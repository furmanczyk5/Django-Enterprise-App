import datetime
import json
import logging
import random
import sys
import time
from decimal import Decimal
from pathlib import Path

import pytz
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse_lazy
from django.db import transaction
from django.db.models import Sum, Q, FloatField
from django.http import HttpResponse, Http404, HttpResponseRedirect, \
    JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, FormView, View
from sentry_sdk import capture_exception, capture_message, configure_scope

from content.viewmixins import AppContentMixin
from events.models import Event, NATIONAL_CONFERENCE_CURRENT
from imis import models as imis_models
from imis.db_accessor import DbAccessor
from learn.utils.wcw_api_utils import WCWContactSync
from myapa.models.contact import Contact
from myapa.permissions.utils import update_user_groups
from myapa.viewmixins import AuthenticateLoginMixin
from pages.models import Page
from planning.settings import CSI_GIVING_PAGE
from store.forms import PaymentCallbackForm, FoundationDonationForm, FoundationDonationCartForm
from store.functions import rows_distributed, get_donor_reference, get_merge_code_and_tributee
from store.models import Purchase, Payment, Order, ProductCart, ProductOption
from store.models.payment_processor import BluepayPaymentProcessor
from store.models.settings import DONOR_RANGES, GENERIC_IMIS_PRODUCTS, AutodraftBillPeriod, AutodraftBillFrequency
from store.payment import PaymentClass, PaymentException

logger = logging.getLogger(__name__)


def product_redirect(request, **kwargs):
    # TO DO... include redirect for subscriptions and event registrations....
    # TO DO EVENTUALLY... show a (page has moved screen with link (instead of immediate redirect)
    # ... and then eventually after that remove this completely)
    product_code = request.GET.get("ProductCode", None)
    product = get_object_or_404(ProductCart, code=product_code)
    if product.product_type == "STREAMING":
        return redirect("/events/course/%s/" % product.content.master.id)
    elif product.content.resource_type == "REPORT":
        return redirect("/publications/report/%s/" % product.content.master.id)
    else:
        # TO DO... for now, just add product to cart in all other cases (e.g. subscriptions, chapters, divisions)
        # ... but really each of these should get a content record to give an overview of the subscription/chapter/division ...
        if not request.user.is_authenticated():
            return redirect("/login/?next=/store/product/?ProductCode=" + product.code)
        else:
            product.add_to_cart(request.contact)
            return redirect("/store/cart/")


class CheckoutView(AuthenticateLoginMixin, View):


    def get(self, *args, **kwargs):

        payment_mode = getattr(settings, 'PAYPAL_MODE', "TEST")
        test_mode = True if payment_mode.upper() == "TEST" else False
        payment_user = getattr(settings, 'PAYPAL_USER', "")
        payment_vendor = getattr(settings, 'PAYPAL_VENDOR', "")
        payment_password = getattr(settings, 'PAYPAL_PASSWORD', "")
        payment_partner = getattr(settings, 'PAYPAL_PARTNER', "")
        payment_currency = getattr(settings, 'PAYPAL_CURRENCY', "USD")

        # this should check for the company purchase....
        user = self.request.user

        username = user.username

        customer_name = username + "|" + user.first_name + " " + user.last_name

        pc = PaymentClass(
            vendor=payment_vendor,
            user=payment_user,
            password=payment_password,
            test_mode=test_mode,
            partner=payment_partner,
            currency=payment_currency,
            comment1=customer_name,
            comment2="",
            username=username
        )

        # logger.debug("{}".format(pc.get_test_curl(amount=self.final_amount)))
        # logger.info(
        #     ("User({uid}-{username}) is about to purchase "
        #      "Registration Option ({registration_option_id}) "
        #      "Product Prices ({product_prices})"
        #      "for a Total of ({final_amount})").format(
        #     uid=user.id, username=user.username,
        #     registration_option_id=self.registration_option_id,
        #     product_prices=self.product_prices,
        #     final_amount=self.final_amount))
        try:
            cart_total = Purchase.cart_total(user=self.request.user)
            secure_token_id, secure_token = pc.get_secure_token(
                amount=cart_total
            )
        except PaymentException as e:
            raise Http404("Token lookup failed: {}".format(e))

        return redirect("https://payflowlink.paypal.com?SECURETOKEN=%s&SECURETOKENID=%s&MODE=%s&USER1=%s" % (secure_token, secure_token_id, payment_mode, username))


class BluepayReturnView(View):

    http_method_names = ['get']

    APPROVED = 'APPROVED'
    DECLINED = 'DECLINED'
    MISSING = 'MISSING'
    SENTINEL_STATUS = DECLINED

    def get_transaction_status_function_mapping(self):
        return {
            self.APPROVED: self.handle_approved,
            self.DECLINED: self.handle_declined,
            self.MISSING: self.handle_missing
        }

    @staticmethod
    def get_log_dir():
        if getattr(settings, 'ENVIRONMENT_NAME', 'LOCAL').upper() in ['STAGING', 'PROD']:
            log_dir = Path('/srv/sites/apa/log/bluepay')
        else:
            log_dir = Path(Path.home(), 'bluepay_logs')

        Path.mkdir(log_dir, parents=True, exist_ok=True)

        return log_dir

    @staticmethod
    def get_log_filename():
        return 'bluepay_redirect_response_{}.json'.format(timezone.now().strftime('%Y-%m-%d:%H:%M:%S'))

    def log_request(self, data):
        log_dir = self.get_log_dir()
        fname = self.get_log_filename()
        Path(log_dir, fname).write_text(str(data))

    def create_payment_data(self):
        payment_data = dict(
            bill_frequency=self.kwargs.get('bill_frequency'),
            bill_period=self.kwargs.get('bill_period'),
            CARD_TYPE=self.request.GET.get('CARD_TYPE'),
            PAYMENT_ACCOUNT=self.request.GET.get('PAYMENT_ACCOUNT'),
            RRNO=self.request.GET.get('RRNO'),
            AUTH_CODE=self.request.GET.get('AUTH_CODE'),
            AMOUNT=self.request.GET.get('AMOUNT'),
            CARD_EXPIRE=self.request.GET.get('CARD_EXPIRE')
        )
        logger.debug("payment data: {}".format(payment_data))
        return payment_data

    def validate_url(self):
        try:
            bill_period = int(self.kwargs.get('bill_period'))
            assert AutodraftBillPeriod.is_valid_range(bill_period)
            bill_frequency = int(self.kwargs.get('bill_frequency'))
            assert bill_frequency in AutodraftBillFrequency.__dict__.values()
        except (AssertionError, TypeError, ValueError):
            raise Http404()

    def get_transaction_status(self):
        return self.request.GET.get('Result', self.SENTINEL_STATUS)

    def handle_approved(self):
        processor = BluepayPaymentProcessor(self.kwargs.get('username'), self.create_payment_data())
        processor.run()
        return redirect(processor.get_redirect_url())

    def handle_declined(self):
        messages.error(
            self.request,
            "Your credit card was declined by the payment gateway provider. Please verify the accuracy of "
            "your information and try again."
        )
        return redirect('/store/cart/?recurring={}'.format(self.kwargs.get('bill_frequency')))

    def handle_missing(self):
        messages.error(
            self.request,
            "The payment gateway provider indicated that the following required fields were missing: {}. "
            "Please try again.".format(
                ', '.join(self.request.GET.get("MESSAGE", []))
            )
        )
        return redirect('/store/cart/?recurring={}'.format(self.kwargs.get('bill_frequency')))

    def authenticate(self, request):
        if not request.user.is_authenticated:
            raise Http404()
        username = self.kwargs.get('username')
        if not username or not request.user.username == username:
            raise Http404()

    def get(self, request, *args, **kwargs):
        self.authenticate(request)
        self.validate_url()
        if getattr(settings, 'ENVIRONMENT_NAME', 'LOCAL').upper() != 'PROD':
            self.log_request(json.dumps(self.request.GET, indent=2))
        status = self.get_transaction_status()
        function_mapping = self.get_transaction_status_function_mapping()
        function = function_mapping.get(
            status,
            function_mapping[self.SENTINEL_STATUS]
        )
        return function.__call__()


class PaymentCallbackVeiw(FormView):
    """
    Callback made by PayPal to indicate a successful payment
    USER1 = customer user id
    USER2 = The Order ID (passed if purchase is made in T3go Admin)
    USER3 = Checkout Source
    """
    form_class = PaymentCallbackForm
    http_method_names = ['post']
    checkout_source = "CART" # default source of checkout... if something other than default cart, then passed as USER3 param to payflow (e.g. for conf kiosk)

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        #  TO DO... look into logger... use it?

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):

        if getattr(settings, 'PAYPAL_DEBUG', False):
            debug_data = {k: v for (k, v) in form.cleaned_data.items() if k in [
                'AMT', 'RESULT', 'AUTHCODE', 'RESPMSG', 'TYPE', 'CUSTID',
                'HOSTCODE', 'RESPTEXT', 'USER1', 'USER2'
            ]}
            capture_message('PAYPAL DEBUG: payment callback for user {}:\n{}'.format(
                form.cleaned_data['USER1'],
                json.dumps(debug_data, indent=2)
            ), level='debug')

        if form.cleaned_data.get("RESULT") != '0':

            return HttpResponse("Fail", status=400)

        start_time = time.time()
        with transaction.atomic(): # TO DO... we should understand these db transactions better...
            user = User.objects.get(username=form.cleaned_data["USER1"]) # Purchaser's ID
            order_id = form.cleaned_data.get("USER2") # Order ID
            self.checkout_source = form.cleaned_data.get("USER3", self.checkout_source) # checkout source
            submitted_user_id = form.cleaned_data.get("USER4")

            amount = form.cleaned_data.get("AMT")
            pn_ref = form.cleaned_data.get("PNREF")

            if not self.checkout_source:
                self.checkout_source = "CART"

            # T3GO ADMIN ORDERS
            if self.checkout_source == "T3GO":

                order = Order.objects.get(id=order_id)
                order.order_status="SUBMITTED"
                order.submitted_time=timezone.now()
                order.is_manual = True
                order.submitted_user_id = submitted_user_id
                order.status="A"
                order.save()

                # TRANSACTIONS SPLIT TO DIFFERENT BATCHES DEPENDING ON IF THIS IS A REFUND,
                # AND IF THIS IS A CHAPTER ADMIN
            else:
                order = Order.objects.create(
                    user=user,
                    submitted_user_id=user.username,
                    order_status="SUBMITTED",
                    submitted_time=timezone.now(),
                )

                order.add_from_cart(user)

            # eventually should be processing the payments first.
            payment = Payment.objects.create(
                status="P",
                order=order,
                amount=amount,
                user=user,
                method="CC",
                pn_ref=pn_ref,
                submitted_time=timezone.now(),
                contact=Contact.objects.get(user__username=user.username)
            )

            payment.process()

            purchases = order.get_purchases()

            for purchase in purchases:

                # setup to only change the purchase status and send email for products with an email template
                purchase.process(checkout_source=self.checkout_source)
                purchase.send_confirmation()

            order.process()

            order.send_confirmation()

            # update user groups after purchase
            try:
                user.contact.sync_from_imis()
                update_user_groups(user)
            except Exception as exc:
                with configure_scope() as scope:
                    scope.set_extra("request", self.request)
                capture_exception(exc)

        if getattr(settings, 'PAYPAL_DEBUG', False):
            capture_message('USER: {}; Sending success response to Paypal after {} seconds'.format(
                    user, round((time.time() - start_time), 1)
            ), level='debug')
        return HttpResponse("Success", status=200)


class CheckoutDoneView(AuthenticateLoginMixin, TemplateView):

    def get(self, request, **kwargs):
        pn_ref = ""
        try:
            pn_ref = request.GET.get("PNREF", "")
            payment = Payment.objects.get(pn_ref=pn_ref)
            checkout_source = request.GET.get("USER3", "CART")
            order = payment.order
            if order:
                if checkout_source == "CONFERENCE_KIOSK":

                    # need to get the multipart event that this is for...
                    # just getting the master/parent for the first multipart/activity purchase we find
                    conference_master_id = None
                    event_purchase_set = Purchase.objects.filter(
                        order=order,
                        product__content__content_type="EVENT"
                    ).select_related("product__content__event")
                    for event_purchase in event_purchase_set:
                        event = event_purchase.product.content.event
                        if event.event_type == "EVENT_MULTI" and event.master_id:
                            conference_master_id = event.master_id
                            break
                        elif event.event_type == "ACTIVITY" and event.parent_id:
                            conference_master_id = event.parent_id
                            break

                    if not conference_master_id:
                        # default to the current conference, this would happend if someone checks out without any activities or registration
                        conference_master_id = Event.objects.get(
                            publish_status="PUBLISHED",
                            code=NATIONAL_CONFERENCE_CURRENT[0]
                        )

                    return redirect(
                        "kiosk:order_confirmation",
                        order_id=str(order.id),
                        master_id=conference_master_id
                    )

                elif checkout_source == "T3GO":
                    messages.success(request, "Credit card payment has been processed.")
                    return redirect("/admin/store/order/{0}/".format(str(order.id)))

                trans_num = None
                purch = order.purchase_set.first()
                ot = order.submitted_time.date()
                ot_days = [ot.day-1,ot.day]

                if purch:
                    trans_num = purch.imis_trans_number
                    if not trans_num:
                        trans = imis_models.Trans.objects.filter(
                            bt_id=purch.user,
                            product_code__startswith=purch.product.imis_code,
                            transaction_date__year=ot.year,
                            transaction_date__month=ot.month,
                            transaction_date__day__in=ot_days
                        )
                        if trans:
                            trans = trans.first()
                            trans_num = trans.trans_number
                return redirect("/store/order_confirmation/?order_id=" + str(trans_num))
                # return redirect("/store/order_confirmation/?order_id=" + str(order.id))

        except Exception as exc:
            with configure_scope() as scope:
                scope.set_extra("request", self.request)
            capture_exception(exc)
            return redirect("/myapa/orderhistory/?msg=Thank%20you%20for%20your%20order!")
        return super().get(request, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["PNREF"] = self.request.GET.get("PNREF", "")
        return context

class OrderDetailView(AuthenticateLoginMixin, AppContentMixin, TemplateView):
    template_name = "store/newtheme/payment-confirmation.html"
    content_url = "/myapa/orderhistory/"
    contact = None

    @method_decorator(csrf_exempt)
    def get(self, request, *args, **kwargs):
        trans_number = request.GET.get("order_id")
        django_order_id = kwargs.get("order_id", None)
        user = request.user
        self.contact = request.contact
        self.django_purchases = []

        if trans_number:
            if request.user.groups.filter(name="staff").exists():
                self.order = imis_models.Trans.objects.filter(
                    trans_number=trans_number,
                    transaction_type="PAY",
                    )
                if self.order:
                    self.order = self.order.first()
                    self.django_purchases = Purchase.objects.filter(
                        imis_trans_number=self.order.trans_number,
                    )
            else:
                self.order = imis_models.Trans.objects.filter(
                    bt_id=user.username,
                    trans_number=trans_number,
                    transaction_type="PAY",
                )
                if self.order:
                    self.order = self.order.first()

                    # I don't believe this is used for iMIS orders.
                    # Purchase also throws an error if the transaction did not take place in iMIS.
                    # self.django_purchases = Purchase.objects.filter(
                    #     user=user,
                    #     imis_trans_number=self.order.trans_number,
                    # )
        elif django_order_id:
            if request.user.groups.filter(name="staff").exists():
                self.order = Order.objects.filter(
                    id=django_order_id,
                    )
                if self.order:
                    self.order = self.order.first()
                    self.django_purchases = self.order.get_purchases()
            else:
                self.order = Order.objects.filter(
                    user__username=user.username,
                    id=django_order_id,
                    )
                if self.order:
                    self.order = self.order.first()
                    self.django_purchases = self.order.get_purchases()
            if self.order:
                imis_trans_list = []
                django_order = self.order
                django_purchases = django_order.purchase_set.all()
                for dp in django_purchases:
                    imis_trans = imis_models.Trans.objects.filter(
                        trans_number=dp.imis_trans_number,
                        line_number=dp.imis_trans_line_number
                    )
                    if not imis_trans:
                        dp_amount = round(-1 * dp.amount, 4)
                        # Going this direction day can be one-off -- how to accommodate?
                        imis_trans = imis_models.Trans.objects.filter(
                            bt_id=dp.user.username,
                            transaction_date__year=dp.submitted_time.year,
                            transaction_date__month=dp.submitted_time.month,
                            # transaction_date__day=dp.submitted_time.day,
                            gl_account=dp.product.gl_account,
                            product_code__contains=dp.product.imis_code,
                            amount=dp_amount
                        )
                        if imis_trans:
                            imis_trans_list.append(imis_trans.first())
                imis_trans_dist = [it for it in imis_trans_list if it.transaction_type=="DIST"]
                if len(imis_trans_dist) > 0:
                    imis_trans = imis_trans_dist[0]
                elif len(imis_trans_list) > 0:
                    imis_trans = imis_trans_list[0]
                self.order = imis_trans

        # GETTING RID OF THIS BECAUSE WE NEED TO DEAL WITH THE CONFIRMATION MESSAGING MORE GENERALLY... SHOULD RETHINK
        ######## for awards
        # product_codes = [p.code for p in self.order.purchase_set.all()]
        # self.order.has_award_product = "CONTENT_AWARD_PRODUCT" in product_codes
        ########
        try:
            wcw_contact_sync = WCWContactSync(self.contact)
            wcw_contact_sync.pull_licenses_redeemed_from_wcw(self.order)
        except:
            pass

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order"] = self.order
        if self.order:
            # we should be able to figure out from product associated with imis trans
            # if there is a corresponding Django product that is tied to an event or content
            # record that is an APA Learn Course
            learn_purchases = None
            # learn_purchases = [p for p in self.order.purchase_set.all() if p.product.product_type=="LEARN_COURSE"]
            context["learn_order"] = True if learn_purchases else False
        context["user"] = self.request.user
        context["contact"] = self.contact
        context["learn_domain"] = settings.LEARN_DOMAIN
        context["generic_imis_products"] = GENERIC_IMIS_PRODUCTS
        try:
            context["confirmation_text_purchases"] = self.django_purchases.filter(product__confirmation_text__gt=0).select_related('product')
        except AttributeError:
            context["confirmation_text_purchases"] = self.django_purchases
        return context



class AddToCartView(View):
    """
    View that adds or removes an item from the cart
    post accepts:
        - product_id
        - quantity
    implemented return types are
        - None : will redirect to the cart
        - json : will return a json oject indicating success or failure
        - replace : will return new html for the button accounting for soldout, standby, remaining tickets, etc ....
    """

    def post(self, request, *args, **kwargs):
        return_type = kwargs.get("return_type", None)

        if request.user.is_authenticated():
            product = ProductCart.objects.get(id=request.POST.get("product_id"))
            option_id = request.POST.get("option_id", None)
            option = ProductOption.objects.get(id=option_id) if option_id else None
            # for APA Learn courses if someone is buying a code for someone else
            for_someone_else = bool(request.POST.get("for_someone_else", False))

            if request.user.contact.member_type in ["STU", "FSTU"] \
                    and product.product_type == "DIVISION":
                # students should manage their divisions on this page
                return redirect('myapa_student_freedivisions')

            purchases = Purchase.objects.filter(
                Q(status='A') | Q(status='P'),
                user=request.user)

            quantity = self.get_quantity(request, product, purchases)

            product_added = product.add_to_cart(
                contact=request.contact,
                quantity=quantity,
                option=option,
                for_someone_else=for_someone_else,
                purchases=purchases
            )
            # occurs when user does not have a salary range. force user to enter salary info
            if not product_added and product.code in (
                    "CHAPT_CO",
                    "CHAPT_IL",
                    "CHAPT_UT",
                    "CHAPT_NNE",
                    "CHAPT_WA",
                    "CHAPT_NE",
                    "CHAPT_OH"
                    "CHAPT_FL",
                    "CHAPT_PA",
                    "CHAPT_CT",
                    "CHAPT_NJ",
                    "CHAPT_IN",
                    "CHAPT_VA",
                    "CHAPT_NATC",
                    "CHAPT_FL"
            ):
                messages.error(
                    request,
                    "Error: a salary range is needed to assign the appropriate chapter price."
                )
                return HttpResponseRedirect('/myapa/personal-information/')

            return JsonResponse({"success": True}) if return_type == "json" \
                else redirect(request.POST.get('redirect', "store:cart"))

        else:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Log In to add items to your cart"
                }
            ) if return_type == "json" else redirect(request.POST.get('redirect', "store:cart"))

    def get(self, request, *args, **kwargs):

        return_type = None

        product_code = request.GET.get("product_code", None)
        option_id = request.GET.get("option_id", None)
        option = ProductOption.objects.get(id=option_id) if option_id else None

        if request.user.is_authenticated():

            try:
                if product_code:
                    product = ProductCart.objects.get(code=product_code)
                else:
                    product = ProductCart.objects.get(
                        id=request.GET.get("ProductID", 0)
                    ) # WTF... what is this for?
            except (ValueError, ProductCart.DoesNotExist):
                messages.error(request,"Error: Enter a valid Product Code")
                return redirect(request.META.get('HTTP_REFERER', 'store:cart'))

            if request.user.contact.member_type in ["STU", "FSTU"] \
                    and product.product_type == "DIVISION":
                # students should manage their divisions on this page
                return redirect('myapa_student_freedivisions')

            quantity = 1
            product_added = product.add_to_cart(contact=request.contact, quantity=quantity, option=option)

            if product_added and product.code in (
                    "CHAPT_CO",
                    "CHAPT_IL",
                    "CHAPT_UT",
                    "CHAPT_NNE",
                    "CHAPT_WA",
                    "CHAPT_NE",
                    "CHAPT_OH",
                    "CHAPT_FL",
                    "CHAPT_PA",
                    "CHAPT_CT",
                    "CHAPT_NJ",
                    "CHAPT_IN",
                    "CHAPT_VA",
                    "CHAPT_NATC",
                    "CHAPT_FL"
            ):
                messages.error(
                    request,
                    "Error: a salary range is needed to assign the appropriate chapter price."
                )
                return HttpResponseRedirect('/myapa/personal-information/')

            return JsonResponse({"success":True}) if return_type == "json" \
                else redirect("store:cart")
        else:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Log In to add items to your cart"
                }
            ) if return_type == "json" else redirect('/login/?next=%s' % self.request.build_absolute_uri())

    def get_quantity(self, request, product, purchases):
        return request.POST.get("quantity", 1)


class UpdateCartView(AddToCartView):
    def get_quantity(self, request, product, purchases):
        quantity = request.POST.get("quantity", 1)
        additional_tickets = 0

        if purchases:
            purchase = next(filter(
                lambda purchase: purchase.product.id == product.id,
                purchases), None)
            additional_tickets = getattr(purchase, 'quantity', 0)

        return int(quantity) + additional_tickets


class RemoveFromCartView(View):
    """
    View that adds or removes an item from the cart
    post accepts:
        - purchase_id
    """

    def post(self, request, *args, **kwargs):

        return_type = kwargs.get("return_type", None)

        if request.user.is_authenticated():
            purchase_id=request.POST["purchase_id"]
            purchase = Purchase.objects.get(id=purchase_id)
            event_qset = Event.objects.filter(id=purchase.product.content.id)
            if event_qset:
                if event_qset[0].event_type != "ACTIVITY":
                    cart_items = Purchase.cart_items(
                        user=request.user
                    ).select_related("product__content__master", "product_price")
                    for item in cart_items:
                        item.delete()
                else:
                    parent_event = event_qset[0].parent
                    if Purchase.objects.filter(
                            Q(user=request.user) | Q(contact__user__username=request.user.username),
                            product__content__master_id=parent_event.id
                    ):
                        Purchase.objects.get(id=purchase_id).delete()
                    else:
                        cart_items = Purchase.cart_items(
                            user=request.user
                        ).select_related("product__content__master", "product_price")
                        for item in cart_items:
                            item.delete()
                return JsonResponse({"success": True}) if return_type == "json" \
                    else redirect("store:cart")
            else:
                purchase.delete()  # Deleting the purchase alone if no event found too
                return JsonResponse({"success": True}) if return_type == "json" \
                    else redirect("store:cart")
        else:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Log In to remove items from your cart"
                }
            ) if return_type == "json" else redirect("store:cart")



# class FoundationDonationView(AuthenticateLoginMixin, FormView):
class FoundationDonationView(FormView):
    """ View for adding a donation to the cart """

    template_name = "store/newtheme/foundation/donation.html"
    form_class = FoundationDonationForm
    success_url = reverse_lazy("store:cart")

    # Hack for sorting donation categories,
    #   anything not in this list will be appended to the end
    PRODUCT_SORT_ORDER = (
        "DONATION_GENERAL",
        "DONATION_COMMUNITY",
        "DONATION_SCHOLARSHIP",
        "DONATION_RESEARCH"
        )

    def setup(self):
        self.content = Page.objects.get(code="FOUNDATION_DONATION_PAGE", publish_status="PUBLISHED")
        self.donation_products = sorted(
            ProductCart.objects.filter(
                product_type="DONATION"
                ),
            key=lambda dp: (
                self.PRODUCT_SORT_ORDER.index(dp.code) if (dp.code in self.PRODUCT_SORT_ORDER)
                else sys.maxsize
            )
        )

    def get(self, request, *args, **kwargs):
        self.setup()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.setup()
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)

        # update purchase in the cart if it's for the same product
        #   NOTE: Remove the instance kwarg altogether to prevent ability to edit existing cart donations
        posted_product_id = self.request.POST.get("product_id")
        product_kwargs = dict(purchase__product__content__master_id=posted_product_id) \
            if posted_product_id else dict()

        # form_kwargs["instance"] = Donation.objects.filter(
        #     purchase__contact=self.request.user.contact,
        #     purchase__order=None,
        #     **product_kwargs
        # ).first()

        form_kwargs["products"] = self.donation_products

        return form_kwargs

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial()
        initial["product_id"] = next((dp.content.master_id for dp in self.donation_products), None)
        contact = getattr(self.request.user, 'contact', None)
        if contact:
            initial["name"] = contact.title
        return initial

    def form_valid(self, form):

        donation_amount = form.cleaned_data.get("amount")
        donation_other_amount = form.cleaned_data.get("other_amount")
        donation_product_id = form.cleaned_data.get("product_id")

        purchase_product = next((p for p in self.donation_products
                                 if p.content.master_id == donation_product_id), None)
        purchase_amount = donation_amount if donation_amount != "OTHER" else donation_other_amount

        # adding or updating this donation item in the cart
        purchase, is_created = Purchase.objects.update_or_create(
            order=None,
            contact=self.request.contact,
            product=purchase_product,
            defaults=dict(
                user=self.request.user,
                submitted_product_price_amount=purchase_amount,
                amount=purchase_amount,
                product_price=purchase_product.get_price(contact=self.request.contact),
                quantity=1,
            )
        )

        # is_anonymous = form.cleaned_data.get("is_anonymous")
        #
        # if purchase:
        #     purchase.agreement_response_1 = is_anonymous
        #     purchase.save()

        # saving the donation record
        # donation = form.save(commit=False)
        # donation.purchase = purchase
        # donation.save()

        return super().form_valid(form)

    def form_invalid(self, form):
        amount = form.cleaned_data.get("amount", "")
        other_amount = form.cleaned_data.get("other_amount", None)

        if amount == "OTHER" and other_amount and other_amount >= 10000.00:
            messages.info(
                self.request,
                """Thank you for your generosity. APA
                wants to handle your gift—and all gifts of $10,000 or
                more—with special care. Please contact APA Chief Executive
                Officer <a href='mailto:jdrinan@planning.org'>James Drinan</a>
                at your earliest convenience to finalize your gift.""")
        else:
            messages.error(
                self.request,
                """Could not add donation to your cart.
                Please make the corrections below and try again."""
            )

        return super().form_invalid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(dict(
            content=self.content,
            title=self.content.title,
            ancestors=self.content.get_landing_ancestors(),
            donation_products=self.donation_products
            )
        )
        context["csi_giving_page"] = CSI_GIVING_PAGE
        guid = None
        username = self.request.user.username if self.request.user else None
        if username:
            contact_main = imis_models.Contactmain.objects.filter(id=username).first()
            guid = contact_main.contactkey_id if contact_main else None
        context["guid"] = guid
        return context


class FoundationDonationCartView(FoundationDonationView):
    template_name = "store/newtheme/foundation/donation-cart.html"
    form_class = FoundationDonationCartForm
    http_method_names = ['post']

    def form_invalid(self, form):
        return redirect(self.success_url)  # FIXME: uhh...


class DonorListView(AppContentMixin, TemplateView):
    """
    Django Template View to list donors to APA Foundation
    """

    template_name = "store/newtheme/donors.html"
    content_url = "/foundation/donors/"
    sorted_donations = []
    donor_list = []
    current_donation_year = None

    def get_all_donors_limited_by_year(self, current_donation_cutoff):
        try:
            query = """
                        SELECT G.ID, G.AMOUNT, N.FULL_NAME, N.COMPANY,
                        G.TRANSACTIONDATE,
                        A.NOTE, G.LISTAS, G.MEMORIALID, G.MEMORIALNAMETEXT,
                        N2.FULL_NAME
                        FROM Name N
                        INNER JOIN Giftreport G
                        ON G.ID = N.ID
                        INNER JOIN Activity A
                        ON A.originating_trans_num = G.originaltransaction
                        AND A.other_id = G.id
                        LEFT JOIN Name N2
                        ON N2.ID = G.MEMORIALID
                        ORDER BY N.ID
                        """
            donor_data = DbAccessor().get_rows(query, [])
            all_donors = []
            ks = ["id", "amount", "full_name", "company", "transactiondate",
                  "note", "listas", "memorialid", "memorialnametext",
                  "tributee_name"]
            for t in donor_data:
                d = {}
                for i in range(0,len(t)):
                    d[ks[i]] = "" if t[i] is None else t[i]
                if d["transactiondate"] >= current_donation_cutoff:
                    all_donors.append(d)
        except:
            all_donors = None

        return all_donors


    def get_aggregate_and_tributes(self, current_donation_cutoff):
        all_donor_names = self.get_all_donors_limited_by_year(current_donation_cutoff)
        sdl = single_donor_list = []
        fdl = full_donors_list = []
        has_non_anonymous = False
        all_donors_count = len(all_donor_names)

        for i,n in enumerate(all_donor_names):
            if i < all_donors_count - 1:
                if n["listas"] != "Anonymous":
                    has_non_anonymous = True

                if all_donor_names[i + 1]["id"] == n["id"]:
                    name_difference = False
                    sdl.append(n)
                    if i == all_donors_count - 2:
                        sdl.append(all_donor_names[i+1])
                else:
                    name_difference = True
                    sdl.append(n)

                if name_difference and not has_non_anonymous:
                    sdl = []

                if name_difference and sdl and has_non_anonymous:
                    total = 0
                    if len(sdl) == 1:
                        donation = sdl[0]
                        merge_and_tributee = get_merge_code_and_tributee(donation)
                        tributee = merge_and_tributee[1]
                        if tributee:
                            donation["tributee_name"] = tributee
                        donation["merge_code"] = merge_and_tributee[0]
                        fdl.append(donation)
                    elif len(sdl) > 1:
                        for donation in sdl:
                            merge_and_tributee = get_merge_code_and_tributee(donation)
                            tributee = merge_and_tributee[1]
                            donation["merge_code"] = merge_and_tributee[0]

                            if tributee:
                                donation["tributee_name"] = tributee
                                fdl.append(donation)
                            total = total + Decimal(donation["amount"])
                        aggregate = {}
                        aggregate["id"] = donation["id"]
                        aggregate["amount"] = total
                        aggregate["full_name"] = donation["full_name"]
                        aggregate["company"] = donation["company"]
                        aggregate["transactiondate"] = ""
                        aggregate["note"] = ""
                        aggregate["listas"] = ""
                        aggregate["memorialid"] = ""
                        aggregate["memorialnametext"] = ""
                        aggregate["tributee_name"] = ""
                        aggregate["merge_code"] = ""
                        fdl.append(aggregate)
                    sdl = []
                    has_non_anonymous = False
        return fdl

    def get_level_donors(self, aggregate_and_tributes, giving_level):
        level_list = []
        for d in aggregate_and_tributes:
            if d["amount"] >= giving_level[0] and d["amount"] < giving_level[1]:
                level_list.append(d)
        return level_list

    def categorize_donations(self):

        now = timezone.now()
        current_year = now.year
        current_month = now.month
        current_day = now.day
        donation_cutoff_month = 1
        donation_cutoff_day = 1

        if (current_month < donation_cutoff_month) or (current_month == donation_cutoff_month and current_day <= donation_cutoff_day):
            self.current_donation_year = current_year - 1
        else:
            self.current_donation_year = current_year

        current_donation_cutoff = datetime.datetime(
            year=self.current_donation_year,
            month=1,
            day=1
        )

        aggregate_and_tributes = self.get_aggregate_and_tributes(
            current_donation_cutoff)

        self.grouped_donor_list = []
        for i, donor_level in enumerate(DONOR_RANGES):
            this_donor_list = {'level': donor_level[2]}

            level_aggregate_and_tributes = self.get_level_donors(
                aggregate_and_tributes, donor_level)

            donor_refs = list(map(
                lambda x: get_donor_reference(x),
                level_aggregate_and_tributes))

            donor_refs_clean = [x for x in donor_refs if x is not None]
            this_donor_list['donors'] = rows_distributed(sorted(donor_refs_clean), 2)

            if i == 0:
                range_description = " $" + str(donor_level[0]) + " and above"
            elif i == len(DONOR_RANGES)-1:
                range_description = "Up to $" + str(donor_level[1])
            else:
                range_description = " $" + str(donor_level[0]) + " - $" + str(donor_level[1])

            this_donor_list['range'] = range_description
            self.grouped_donor_list.append(this_donor_list)
            # if donor_level[2] == "Supporter":
            #     print(self.grouped_donor_list)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        self.categorize_donations()
        context["current_donation_year"] = self.current_donation_year
        context["grouped_donor_list"] = self.grouped_donor_list

        return context


class DonorMixin(object):
    """
    Mixin for common Donor-related needs
    """

    @staticmethod
    def get_current_donation_year(cutoff_month=1, cutoff_day=1):
        now = timezone.now()

        if (now.month < cutoff_month) \
                or (now.month == cutoff_month and now.day <= cutoff_day):
            return now.year - 1
        else:
            return now.year

    def get_current_donation_cutoff(self, tzstring="US/Central"):
        tz = pytz.timezone(tzstring)
        current_donation_cutoff = tz.localize(
            datetime.datetime(
                year=self.get_current_donation_year(),
                month=1,
                day=1
            )
        )
        return current_donation_cutoff


class OnsiteDonorView(DonorMixin, TemplateView):

    template_name = "store/newtheme/donors-onsite-apa.html"

    def get_donations(self):
        donations = Donation.objects.filter(
            status='A',
            purchase__order__submitted_time__gt=self.get_current_donation_cutoff(),
            is_anonymous=False
        ).distinct(
            'name'
        ).only(
            'name'
        )
        return donations

    def get_donor_names(self):
        donors = [x.name for x in self.get_donations()]
        # since this is meant to be displayed on a rotating grid
        # on a large display, we don't want several screens of
        # just "Anonymous Person." So we exclude them in the query
        # and append one here.
        donors.append('Anonymous Person')
        return sorted(donors)

    def get_context_data(self, **kwargs):
        donors = self.get_donor_names()
        paginator = Paginator(donors, per_page=20)
        page = self.request.GET.get('page', 1)
        try:
            donors_to_display = paginator.page(page)
        except PageNotAnInteger:
            donors_to_display = paginator.page(1)
        except EmptyPage:
            donors_to_display = paginator.page(paginator.num_pages)

        context = dict(
            donors=donors_to_display,
            num_pages=paginator.num_pages
        )
        return context


class OnsiteDonorViewSwitcher(OnsiteDonorView):
    """
    View for the simple template that has some JavaScript that cycles
    iframes back and forth between our donor view and txt2give thermometer
    """

    template_name = "store/newtheme/donors-onsite.html"


class FoundationDonationVisualJsonDataView(View):
    """
    returns x-axis bins, for specified time range, for donation counts and amounts
    """

    def setup(self):
        self.TIME_ZONE = pytz.timezone("US/Eastern")
        self.BEGIN_TIME_THRESHOLD = self.TIME_ZONE.localize(datetime.datetime(year=2017, month=4, day=27, hour=12, minute=0))
        self.END_TIME_THRESHOLD = self.TIME_ZONE.localize(datetime.datetime(year=2017, month=5, day=1, hour=12, minute=0))
        # MINUTE_INCREMENT = datetime.timedelta(minutes=1)
        self.MINUTE_INCREMENT = 1
        self.DATETIME_CATEGORY_FORMATTER = "%B %d %I:%M %p"

    def get(self, request, *args, **kwargs):

        self.setup()

        now = timezone.now()

        live_donations = Donation.objects.exclude(
            purchase__submitted_time__isnull=True
        ).filter(
            status__in=["A", "H"]
        ).order_by(
            "purchase__submitted_time"
        ).values(
            "purchase__amount", "purchase__submitted_time"
        )

        # self.donations = []
        self.donations_by_minute = []

        cumulative_count = 0
        cumulative_total = 0.0

        sb_tm_rounded = None
        curr_datetime = self.BEGIN_TIME_THRESHOLD
        curr_count = 0
        curr_total = 0.0
        current_bin = {"time":curr_datetime.strftime(self.DATETIME_CATEGORY_FORMATTER)}

        for ld in live_donations:
            amount = float(ld["purchase__amount"])
            sb_tm = ld["purchase__submitted_time"]

            sb_tm_rounded = datetime.datetime(year=sb_tm.year, month=sb_tm.month, day=sb_tm.day, hour=sb_tm.hour, minute=int(sb_tm.minute/self.MINUTE_INCREMENT), tzinfo=pytz.utc).astimezone(self.TIME_ZONE)

            if sb_tm_rounded >= self.BEGIN_TIME_THRESHOLD and curr_datetime <= self.END_TIME_THRESHOLD:
                if sb_tm_rounded == curr_datetime:
                    curr_count += 1
                    curr_total += amount
                else:
                    current_bin.update({
                        "count":curr_count,
                        "total":curr_total,
                        "cumulative_count":cumulative_count,
                        "cumulative_total":cumulative_total
                    })
                    self.donations_by_minute.append(current_bin)
                    curr_datetime += datetime.timedelta(minutes=self.MINUTE_INCREMENT)

                    while curr_datetime < sb_tm_rounded and curr_datetime <= self.END_TIME_THRESHOLD:
                        self.donations_by_minute.append({
                            "time":curr_datetime.strftime(self.DATETIME_CATEGORY_FORMATTER),
                            "count":0,
                            "total":0.0,
                            "cumulative_count":cumulative_count,
                            "cumulative_total":cumulative_total})
                        curr_datetime += datetime.timedelta(minutes=self.MINUTE_INCREMENT)

                    curr_count = 1
                    curr_total = amount
                    current_bin = {"time":curr_datetime.strftime(self.DATETIME_CATEGORY_FORMATTER)}

            cumulative_count += 1
            cumulative_total += amount

        if sb_tm_rounded and sb_tm_rounded <= self.END_TIME_THRESHOLD:
            current_bin.update({
                "count":curr_count,
                "total":curr_total,
                "cumulative_count":cumulative_count,
                "cumulative_total":cumulative_total
            })
            self.donations_by_minute.append(current_bin)
            curr_datetime += datetime.timedelta(minutes=self.MINUTE_INCREMENT)

        if curr_datetime <= self.END_TIME_THRESHOLD:
            while curr_datetime < now and curr_datetime <= self.END_TIME_THRESHOLD:
                self.donations_by_minute.append({
                    "time":curr_datetime.strftime(self.DATETIME_CATEGORY_FORMATTER),
                    "count":0,
                    "total":0.0,
                    "cumulative_count":cumulative_count,
                    "cumulative_total":cumulative_total})
                curr_datetime += datetime.timedelta(minutes=self.MINUTE_INCREMENT)

        return self.render_to_response()

    def render_to_response(self):
        return JsonResponse({"donations": self.donations_by_minute})
        # entered_donations = [] # collect from spreadsheet


class FoundationDonationVisualJsonDataView2(View):

    def get(self, request, *args, **kwargs):

        donations_query = Donation.objects.exclude(
            purchase__submitted_time__isnull=True
        ).filter(
            status__in=["A", "H"]
        )

        self.donation_count = donations_query.count()

        self.donation_amount = donations_query.aggregate(
            donation_amount=Sum('purchase__amount', output_field=FloatField())
        ).get("donation_amount")

        self.donors = []

        return self.render_to_response()

    def get_context_data(self, *args, **kwargs):
        data = dict(
            donation_count=self.donation_count,
            donation_amount=self.donation_amount)
        return dict(success=True, data=data)

    def render_to_response(self):
        return JsonResponse(self.get_context_data())


class FoundationDonationDonorsJsonDataView(View):

    def get(self, request, *args, **kwargs):

        # RANGE OF DATETIMES TO EXCLUDE FROM RETURNED DONORS. SO NEW
        DATETIME_FORMATTER = "%Y-%m-%dT%H:%M:%S.%fZ"
        exclude_begintime = request.GET.get("exclude_begintime")
        exclude_endtime = request.GET.get("exclude_endtime")

        donations_query = Donation.objects.exclude(
            purchase__submitted_time__isnull=True
        ).exclude(
            is_anonymous=True
        ).filter(
            status__in=["A", "H"]
        ).distinct("name")

        if exclude_begintime and exclude_endtime:
            begintime = pytz.utc.localize(datetime.datetime.strptime(exclude_begintime, DATETIME_FORMATTER))
            endtime = pytz.utc.localize(datetime.datetime.strptime(exclude_endtime, DATETIME_FORMATTER))
            donations_query = donations_query.exclude(purchase__submitted_time__range=[begintime, endtime])
        else:
            begintime = None
            endtime = None

        # SORT BY SUBMITTED TIME
        # sorted_donor_query = sorted(donations_query.values("name", "purchase__submitted_time"), key=lambda d: d.get("purchase__submitted_time"), reverse=True)

        # SORT BY RANDOM!
        sorted_donor_query = sorted(donations_query.values("name", "purchase__submitted_time"), key=lambda d: random.random())

        if sorted_donor_query:
            # new date range to exclude next time query is made, the client should store this somewhere and use it in subsequent queries
            query_min_time = sorted_donor_query[-1].get("purchase__submitted_time")
            query_max_time = sorted_donor_query[0].get("purchase__submitted_time")
            begintime = query_min_time if (begintime is None or query_min_time < begintime) else begintime
            endtime = query_max_time if (endtime is None or query_max_time > endtime) else endtime

        self.exclude_begintime = begintime.strftime(DATETIME_FORMATTER) if begintime else None
        self.exclude_endtime = endtime.strftime(DATETIME_FORMATTER) if endtime else None
        self.donors = [d.get("name") for d in sorted_donor_query]

        return self.render_to_response()

    def get_context_data(self, *args, **kwargs):
        data = dict(
            donors=self.donors,
            exclude_begintime=self.exclude_begintime,
            exclude_endtime=self.exclude_endtime)
        return dict(success=True, data=data)

    def render_to_response(self):
        return JsonResponse(self.get_context_data())


class FoundationDonationVisualView(TemplateView):
    template_name = "store/newtheme/foundation/conference-visualization.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.kwargs.get("webpage_type", "") == "web":
            context["body_class"] = 'foundation-webpage'
        return context





