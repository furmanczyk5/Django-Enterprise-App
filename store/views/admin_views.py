from django.shortcuts import render, redirect
from django.views.generic import View, FormView
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseRedirect

from django.utils import timezone

from myapa.viewmixins import AuthenticateStaffMixin
from myapa.utils import has_webgroup

from events.models import Event

from store.models import Purchase, Payment, Order, Product, ProductPrice, \
    ProductOption, ProductCart
from store.payment import PaymentClass, PaymentException
from store.admin_forms import OrderConfirmationAdminEmailForm


def submit_none_payment(request, **kwargs):
    """
    submits the added check payment and processes the purchases
    """

    order_id = kwargs['order_id']

    success_payment_redirect = "/admin/store/order/{0}/".format(str(order_id))
    # process the check payment / submit to iMIS
    order = Order.objects.get(id=order_id)
    order.order_status = "SUBMITTED"
    if not order.submitted_time:
        order.submitted_time = timezone.now()
    order.is_manual = True
    order.submitted_user_id = request.user.username # note: pass staff ID as user3 to paypal
    order.status="A"
    order.save()

    payment = Payment.objects.create(order=order, user=order.user, contact=order.user.contact, amount=0, method="NONE", status="P")

    # for determining which cash gl account the payment should write to
    is_chapter_admin = False

    if request.user.groups.filter(name='organization-store-admin').exists():
        is_chapter_admin = True
    payment.process(is_chapter_admin)
    
    order = Order.objects.get(id=order_id)

    purchases = order.get_purchases()

    for purchase in purchases:
        purchase.process(checkout_source="T3GO")

    for purchase in purchases:
        purchase.send_confirmation()

    order.process()

    order.send_confirmation()

    messages.success(request, "$0 payment has been processed.")
    
    return HttpResponseRedirect(success_payment_redirect)

def submit_payment_refund(request, *args, **kwargs):
    """
    submits the refund payment
    """

    order_id = kwargs['order_id']
    refund_type = request.GET.get('refund_type')

    success_payment_redirect = "/admin/store/order/{0}/".format(str(order_id))
    # process the check payment / submit to iMIS
    order = Order.objects.get(id=order_id)
    order.order_status = 'SUBMITTED'
    order.save()

    balance = order.balance()

    payment = Payment.objects.create(method=refund_type, order=order, user=order.user, contact=order.user.contact, amount=balance, status="P")
    
    # for determining which cash gl account the payment should write to
    is_chapter_admin = False
    if request.user.groups.filter(name='organization-store-admin').exists():
        is_chapter_admin = True
    payment.process(is_chapter_admin)

    purchases = Purchase.objects.filter(order=order, status="P")
    for purchase in purchases:
        purchase.process()
    messages.success(request, "Refund has been processed.")
    
    return HttpResponseRedirect(success_payment_redirect)

def manage_payment_cc(request, **kwargs):
    """
    allows staff/admins to add or view cc payments for existing orders
    """

    context = {}

    # I DON'T THINK THIS IS NEEDED ANYMORE.... WE'LL FIND OUT
    # COMMENTED OUT FOR SEPERATE BATCH TICKET

    # is_staff = False

    # if request.user.groups.filter(name="staff").exists():
    #     is_staff = True

    # context["is_staff"] = is_staff

    order_id = kwargs['order_id']
    submitter_id = request.user.username

    order = Order.objects.get(pk = order_id)
    user = order.user 

    context["order"] = order
    context["user"] = user

    payment_mode = getattr(settings, 'PAYPAL_MODE', "TEST")
    test_mode = True if payment_mode.upper() == "TEST" else False
    payment_user = getattr(settings, 'PAYPAL_USER', "")
    payment_vendor = getattr(settings, 'PAYPAL_VENDOR', "")
    payment_password = getattr(settings, 'PAYPAL_PASSWORD', "")
    payment_partner = getattr(settings, 'PAYPAL_PARTNER', "")
    payment_currency = getattr(settings, 'PAYPAL_CURRENCY', "USD")

    # this probably should have been done where a positive balance is money owed
    # adding abs to bypass negative balances
    balance = abs(order.balance())

 
    username = user.username
    customer_name = user.username + " | " + user.first_name + " " + user.last_name 
    comment2 = "t3go order id: " + str(order_id) + " || "+ "submitter id: " + request.user.username
    orderid = str(order_id)

    pc = PaymentClass(
        vendor=payment_vendor, user=payment_user,
        password=payment_password, test_mode=test_mode,
        partner=payment_partner, currency=payment_currency,
        comment1=customer_name, comment2=comment2, 
        username = username, user2=orderid)

    try:
        secure_token_id, secure_token = pc.get_secure_token(amount=balance)
    except PaymentException as e:
        raise Http404("Token lookup failed: {}".format(e))

    context['final_amount'] = balance
    context['secure_token_id'] = secure_token_id
    context['secure_token'] = secure_token
    context['payment_mode'] = payment_mode
    context['USER1'] = username
    context['USER2'] = orderid
    context['USER3'] = "T3GO"
    context['USER4'] = request.user.username
    
    return render(request, "store/newtheme/admin/manage-payment-cc.html", context) 


def update_comp_tickets(request, **kwargs):
    
    order_id = kwargs["order_id"]
    success_comp_redirect = "/admin/store/order/{0}/".format(str(order_id))

    order = Order.objects.get(id=order_id)
    purchases = Purchase.objects.filter(order=order, 
        # status="P", # QUESTION... we had originally filtered by status here... why? (admins want ability to add comp tickets regardless of status)
        quantity__gte=1, 
        product__product_type="EVENT_REGISTRATION")

    for purchase in purchases:
        activities_related = Event.objects.filter(parent=purchase.product.content.master, publish_status="PUBLISHED").select_related("product")

        for activity in activities_related:
            if hasattr(activity, "product"):
                # this should be automatically adding the comp tickets for each activity it is looping through
                activity.product.get_price(user=order.user, contact=order.user.contact, order=order)

    messages.success(request, "Complimentary tickets have been added to the order")
    
    return HttpResponseRedirect(success_comp_redirect)



# # IS THIS BEING USED? 
def get_price(request, **kwargs):
    """
    gets the user assigned price based on the product option passed
    NOTES: refactor ... does this need its own view?
    """

    # takes a product and product option
    # filters productprices based on options
    # returns product price assigned

    # try:
    order_id = kwargs.get("order_id", "")
    product_id = kwargs.get("product_id", "")
    option_id = kwargs.get("option_id", "")

    order = Order.objects.get(id = order_id)

    user = order.user

    product = ProductCart.objects.get(id=product_id)
    option = None
    try:
        option = ProductOption.objects.get(product=product, id=option_id)
        prices = option.prices_required_by.filter(product=product_id)

    except:
        option = None
        prices = ProductPrice.objects.filter(product=product)


    #return_price = None
    #return_price_priority = None
    
    product_price = product.get_price(user=user.contact, option=option)
    if product_price:
        return_price = product_price.id
    else:
        return_price = "None"
 
    return HttpResponse(return_price)


class OrderConfirmationAdminEmailView(FormView):

    form_class = OrderConfirmationAdminEmailForm
    template_name = "store/newtheme/admin/send-order-confirmation-email-form.html"
    success_url = '/admin/'
    is_admin = False
    order = None

    def get_order_confirmation_initial(self, request, *args, **kwargs):
        
        order_id = kwargs.get("order_id")
        print("this is the order id: " + str(order_id))
        self.order = Order.objects.get(id=order_id)
        self.is_admin = has_webgroup(
            user=request.user,
            required_webgroups=[
                "organization-store-admin",
                "staff",
                "component-admin",
                "onsite-conference-admin"
            ]
        )


    def dispatch(self, request, *args, **kwargs):
        self.get_order_confirmation_initial(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return "/admin/store/order/{0}/".format(self.order.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_admin"] =  self.is_admin 
        context["order"] = self.order
        return context


    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        email = self.request.POST.get('email','')
        self.order.send_admin_confirmation(email=email)
        messages.success(self.request, "An order email confirmation has been sent to {0}".format(email))

        return super().form_valid(form)


class CMOrderProviderSubmitView(AuthenticateStaffMixin, View):
    """ submits all pending provider events for this order """

    def get(self, request, *args, **kwargs):
        order_id = kwargs.get("order_id")
        self.order = Order.objects.get(id=order_id)
        purchases = self.order.purchase_set.filter(product__product_type="CM_PER_CREDIT").prefetch_related("content_master__content__event")
        published_submissions = []
        for purchase in purchases:
            submission = next((c.event for c in purchase.content_master.content.all() if c.publish_status == "SUBMISSION"), None)
            if submission and submission.status == "P":
                submission.__class__ = submission.get_proxymodel_class()
                submission.provider_submit_async()
                published_submissions.append(submission.title)

        if published_submissions:
            messages.success(request, "Queued the following events for submission: %s" % ", ".join(published_submissions))
        else:
            messages.success(request, "There are no events pending payment for this order.")

        return redirect("admin:cm_cmorder_change", order_id)
