from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import FormView
from sentry_sdk import capture_exception, configure_scope

from myapa.models.contact_relationship import ContactRelationship
from myapa.permissions.utils import update_user_groups
from myapa.utils import get_primary_chapter_code_from_zip_code
from myapa.viewmixins import AuthenticateLoginMixin
from store.forms import CartForm
from store.models import Purchase, Payment, Order, ProductCart, PRODUCT_TYPE_PRIORITY, BluepayMembershipPaymentDispatcher
from store.models.settings import AutodraftBillFrequency, AutodraftBillPeriod
from store.utils import PurchaseInfo


class CartView(AuthenticateLoginMixin, FormView):
    form_class = CartForm
    purchases = None
    template_name = "store/newtheme/cart.html"
    allow_checks_products = ("CM_REGISTRATION", "CM_PER_CREDIT")
    process_check_order_immediately = False
    contact = None
    company_contact = None
    url_namespace = "store"
    checkout_source = "CART"
    credit_balance = 0.0 # for NPC20 credit balance messages

    def get_purchases(self, **kwargs):
        self.contact = self.request.contact

        if self.is_recurring_membership_cart():
            # should remove non-membership items from cart
            self.payment_dispatcher = BluepayMembershipPaymentDispatcher(self.contact)
            self.payment_dispatcher.bill_frequency = self.get_recurring_frequency()

            # Hardcode 12 for bill period if annual auto renewal
            if str(self.request.GET.get('recurring')) == str(AutodraftBillPeriod.ANNUAL):
                self.payment_dispatcher.bill_period = AutodraftBillPeriod.ANNUAL

        self.company_contact = ContactRelationship.get_company_contact(user=self.request.user)
        self.purchases = Purchase.cart_items(user=self.request.user)


        self.has_donation_purchase = next((True for p in self.purchases
                                           if p.product.product_type == "DONATION"), False)

        self.my_purchases = self.contact.purchase_set.all()

        self.has_learn_purchase = next((True for p in self.purchases
                                           if p.product.product_type == "LEARN_COURSE"), False)
        for purchase in self.purchases:

            # TODO: Refactor the shopping cart so we can knock it off with all these hacks!
            #  https://americanplanning.atlassian.net/browse/DEV-5445
            if purchase.product_price.code == "PRODUCT_CM_PER_CREDIT_COMPLIMENTARY":
                continue

            my_product = ProductCart.objects.get(id=purchase.product.id)

            if my_product.product_type != 'DONATION':
                new_price = my_product.get_price(
                    contact=self.contact,
                    option=purchase.option,
                    code=purchase.code,
                    purchases=self.my_purchases,
                )

                if new_price:
                    purchase.product_price = new_price

                    purchase.submitted_product_price_amount = new_price.price
                    purchase.amount = new_price.price * purchase.quantity
                    purchase.save()
                else:
                    print("deleting purchase!", purchase)
                    purchase.delete()

    def allow_checks(self, **kwargs):
        return next((False for p in self.purchases
                     if p.product.product_type not in self.allow_checks_products), True)

    def get_credit_balance(self, **kwargs):
        """
        a temporary credit msg, currently used for NPC20 credits

        """
        try:
            my_orders = self.contact.get_imis_orders()
            self.credit_balance = 0 - next(
                (o.BALANCE for o in my_orders
                    if o.BALANCE<0
                        and o.STATUS=='C'
                        and o.SOURCE_SYSTEM=='MEETING'
                        ),
                0.0
                )
        except:
            pass

    def setup(self):
        self.get_purchases(**self.kwargs)
        self.get_credit_balance(**self.kwargs)

    def get(self, request, *args, **kwargs):

        request.session['staff_checkout'] = False

        self.setup()

        if "delete" in self.request.GET:
            delete_id = self.request.GET["delete"]

            purchase_to_remove = Purchase.objects.filter(
                Q(user=self.request.user) | Q(contact=self.company_contact),
                id=delete_id,
                order__isnull=True
            ).first()

            if purchase_to_remove:
                self.handle_purchase_to_remove(purchase_to_remove, request)

            # this should update the purchases
            self.get_purchases(**kwargs)

        return super().get(request, *args, **kwargs)

    def handle_purchase_to_remove(self, purchase_to_remove, request):
        product_type = purchase_to_remove.product.product_type
        if product_type == "CHAPTER":
            primary_chapter_code = get_primary_chapter_code_from_zip_code(
                zip_code=request.user.contact.zip_code
            )
            primary_chapter = 'CHAPT_{}'.format(primary_chapter_code)
            if primary_chapter == purchase_to_remove.product.code:
                Purchase.objects.filter(
                    user=self.request.user,
                    order__isnull=True
                ).delete()
                messages.success(request, "You must select a chapter for APA membership. Your cart has been cleared")

        elif product_type == "DUES":
            Purchase.objects.filter(
                user=self.request.user,
                order__isnull=True
            ).delete()
            messages.success(request, "Additional item prices may vary based on APA membership. Your cart has been cleared")

        elif product_type == "CM_REGISTRATION":
            Purchase.objects.filter(
                user=self.request.user,
                order__isnull=True,
                product__product_type="CM_PER_CREDIT"
            ).delete()

        elif product_type == "EVENT_REGISTRATION":
            self.remove_related_activity_tickets(purchase_to_remove)

        purchase_to_remove.delete()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        purchases = self.purchases

        self.add_purchase_context_detail()

        context["contact"] = self.contact
        context["credit_balance"] = self.credit_balance
        context["purchases"] = purchases
        context["purchase_total"] = Purchase.cart_total(self.request.user, cart_items=self.purchases)
        context["has_donation_purchase"] = self.has_donation_purchase
        context["has_learn_purchase"] = self.has_learn_purchase
        context["allow_checks"] = len(self.purchases) > 0 and self.allow_checks(**kwargs)
        context["recurring_frequency"] = self.request.GET.get('recurring')

        return context

    def post(self, request, *args, **kwargs):
        self.setup()

        self.add_activity_checkout_errors(request)

        if list(messages.get_messages(request)):
            return super().get(request, *args, **kwargs)

        return super().post(request, *args, **kwargs)

    def is_recurring_membership_cart(self):
        return bool(self.request.GET.get('recurring'))

    def get_recurring_frequency(self):
        value = self.request.GET.get('recurring', '').replace('/', '')
        try:
            value = int(value)
            assert value in AutodraftBillFrequency.__dict__.values()
            return value
        except (AssertionError, TypeError, ValueError):
            raise Http404()

    def form_invalid(self, form):
        messages.error(self.request, form.errors)
        return super().form_invalid(form)

    def form_valid(self, form):
        # UPDATING QUANTITIES IN THE CART CHECK:
        cart_is_updated = False
        for purchase in self.purchases:
            purchase_quantity_field = purchase.product.code + '_quantity'
            form_purchase_quantity = float(self.request.POST.get(purchase_quantity_field, 1))

            # TO DO... move to standard "update purchase in cart" method
            if form_purchase_quantity != purchase.quantity:
                purchase.quantity = form_purchase_quantity
                # TO DO... this is nasty having to re-query... refactor
                this_product = ProductCart.objects.get(id=purchase.product.id)
                # TO DO... would "code" ever need to be passed back in here?
                this_price = this_product.get_price(
                    contact=self.request.contact,
                    option=purchase.option,
                    purchases=self.my_purchases)
                if this_price:
                    purchase.product_price = this_price
                    purchase.submitted_product_price_amount = this_price.price
                    purchase.amount=float(this_price.price) * float(form_purchase_quantity) # TO DO... double check is this the best way to convert float/decimal for currency data?
                    purchase.save()

                cart_is_updated = True
                messages.success(
                    self.request,
                    "Quantity updated to {0} for {1}.".format(
                        int(form_purchase_quantity),
                        purchase.product.content.title
                    )
                )

        if cart_is_updated:
            # then we should requery
            self.get_purchases()
            return self.form_invalid(form)

        cart_total = Purchase.cart_total(user=self.request.user, cart_items=self.purchases)
        payment_method = self.request.POST.get("payment_method", "CC")

        if cart_total == 0.00:
            return self.handle_zero_cost_cart()

        elif payment_method == "CC":
            return redirect(self.get_checkout_url())

        elif payment_method == "CHECK" and self.allow_checks(**self.kwargs):
            return self.handle_check_payment_method(cart_total)
        else:
            return self.form_invalid(form)

    def handle_check_payment_method(self, cart_total):
        order = Order.objects.create(
            user=self.request.user,
            submitted_user_id=self.request.user.username,
            submitted_time=timezone.now(),
            order_status="SUBMITTED",
            expected_payment_method="CHECK"
        )

        Payment.objects.create(
            status="P",
            order=order,
            amount=cart_total,
            user=self.request.user,
            method="CHECK",
            submitted_time=timezone.now(),
            contact=self.request.user.contact
        )

        order.add_from_cart(self.request.user)

        order_purchases = sorted(Purchase.objects.filter(order=order),
                                 key=lambda p: PRODUCT_TYPE_PRIORITY.index(p.product.product_type))
        if self.process_check_order_immediately:
            for purchase in order_purchases:
                purchase.process(checkout_source=self.checkout_source)

            order.process()

        else:
            for purchase in order_purchases:
                purchase.process_pending_check(checkout_source=self.checkout_source)
        return redirect(self.get_order_confirmation_url(order.id))

    def handle_zero_cost_cart(self):
        order = Order.objects.create(
            user=self.request.user,
            submitted_user_id=self.request.user.username,
            submitted_time=timezone.now(),
            order_status="SUBMITTED"
        )
        order.add_from_cart(self.request.user)
        payment = Payment.objects.create(
            method='NONE',
            order=order,
            user=self.request.user,
            submitted_time=timezone.now(),
            amount=0
        )
        payment.process()

        order_purchases = sorted(
            Purchase.objects.filter(order=order),
            key=lambda p: PRODUCT_TYPE_PRIORITY.index(p.product.product_type)
        )
        for purchase in order_purchases:
            purchase.process(checkout_source=self.checkout_source)
            purchase.send_confirmation()
        order.process()
        try:
            update_user_groups(self.request.user)
        except Exception as exc:
            with configure_scope() as scope:
                # TODO: Necessary?
                scope.set_extra("request", self.request)
            capture_exception(exc)
        return redirect(self.get_order_confirmation_url(order.id))

    def get_order_confirmation_url(self, order_id):
        return reverse("{0}:order_confirmation".format(
            self.url_namespace),
            kwargs=dict(order_id=order_id)
        )

    def get_checkout_url(self, name="checkout"):
        if self.is_recurring_membership_cart():
            return self.payment_dispatcher.get_dispatch_url()
        return reverse("{0}:{1}".format(self.url_namespace, name))

    def registration_message(self, event):
        messages.info(
            self.request,
            ("To purchase additional tickets you must first register for %s" %
             event.title)
        )
        return redirect(
            "registrations:select_registration",
            master_id=event.master_id
        )

    def checkout_error(self, purchase):
        return (
            purchase.total_remaining == 0 or
            self.purchase_total_reached(purchase))

    def purchase_total_reached(self, purchase):
        if hasattr(purchase, 'user_total_purchased'):
            return purchase.user_total_purchased >= purchase.user_allowed_to_purchase

        return False

    def get_checkout_error_message(self, purchase):
        if self.purchase_total_reached(purchase):
            return (
                'Maximun quantity of tickets for {} have been purchased.<br>'
                'Please remove from cart before checking out.'
            ).format(purchase.product.content.title)

        return (
            'Tickets for {} are sold out.<br>'
            'Please remove from cart before checking out.'
        ).format(purchase.product.content.title)

    def remove_related_activity_tickets(self, purchase_to_remove):
        for purchase in self.purchases:
            if (is_activity(purchase) and
                    parent_event_is_deleted(purchase, purchase_to_remove)):
                purchase.delete()

    def add_activity_checkout_errors(self, request):
        for purchase in self.purchases:
            if purchase.product.product_type == "ACTIVITY_TICKET":
                purchase_info = PurchaseInfo(purchase.product, self.request.user).get()
                setattr(purchase, 'total_remaining', purchase_info['total_remaining'])
                setattr(purchase, 'user_allowed_to_add', purchase_info['user_allowed_to_add'])

                if self.checkout_error(purchase):
                    messages.error(request, self.get_checkout_error_message(purchase))

    def add_purchase_context_detail(self):
        for purchase in self.purchases:
            quantity_dropdown = 100

            if is_activity(purchase):
                purchase_info = PurchaseInfo(purchase.product, self.request.user).get()
                quantity_dropdown = int(
                    purchase_info['user_allowed_to_purchase'] -
                    purchase_info['user_total_purchased']
                )

                for key, value in purchase_info.items():
                    setattr(purchase, key, value)

            setattr(purchase, "quantity_dropdown", range(1, quantity_dropdown + 1))


def is_activity(purchase):
    return purchase.product.product_type == 'ACTIVITY_TICKET'


def parent_event_is_deleted(purchase, purchase_to_remove):
    purchase_imis_code = purchase.product.imis_code
    purchase_to_remove_imis_code = purchase_to_remove.product.imis_code
    return purchase_to_remove_imis_code in purchase_imis_code
