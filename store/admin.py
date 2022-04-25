import nested_admin

from django.contrib import admin, messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from django.forms.models import inlineformset_factory
from django.utils import timezone
from django.db.models import Q, Sum

from myapa.utils import has_webgroup
from content.admin import BaseContentAdmin, ContentAdmin, \
    PublishStatusListFilter, CollectionRelationshipInline
from content.models import EmailTemplate
from registrations.models import Attendee
from learn.utils.wcw_api_utils import WCWContactSync

from store.models import Purchase, Payment, Order, ProductPrice, \
    ProductOption, Product, ContentProduct
from .admin_forms import PaymentAdminForm, PurchaseInlineAdminForm, \
    ProductInlineAdminForm


class PurchaseAdmin(admin.ModelAdmin):
    raw_id_fields = ['user', 'order', 'created_by', 'updated_by',
                     'product', 'product_price']
    autocomplete_lookup_fields = {"fk": [
        'user', 'order', 'created_by', 'updated_by', 'product',
        'product_price']}

    search_fields = [
        "=user__username", "id", "product__code", "product__content__code",
        "product__content__parent__content_live__code",
        "product__content__parent__content_live__product__code"]
    list_filter = ["product__content__event__event_type"]
    fieldsets = [
        (None, {
            "fields": (
                ("user",), ("order",), ("status",), ("amount",),
                ("submitted_product_price_amount",),
                ("product", "option", "code"), ("product_price",), ("quantity",),
                ("imis_trans_number", "imis_batch","imis_batch_date"),
                ("for_someone_else",),
            )
        }),
    ]

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        is_org_store_admin = has_webgroup(
            user=request.user, required_webgroups=["organization-store-admin"])
        if is_org_store_admin:
            return {}
        else:
            return super().get_model_perms(request)

    def save_model(self, request, purchase, form, change):

        purchase.submitted_by_id = request.user
        if not purchase.submitted_time:
            purchase.submitted_time = timezone.now()
        purchase.status = "N"  # status changes to "A" after purchase.
        purchase.save()

    def get_queryset(self, request):

        # TO DO... we need to create this "product-admin" login group...
        #  we're checking for for that instead of staff (because chapter
        #  admins will also be marked as is_staff)
        if request.user.groups.filter(
            name__in=("staff-store-admin", "component-admin", "onsite-conference-admin")
        ).exists() or request.user.is_superuser:
            return super().get_queryset(request)
        else:
            # organization = Organization.objects.get(user__username='050501')
            organization = request.user.contact.contactrelationship_as_target.filter(
                relationship_type="ADMINISTRATOR"
            ).first().source
            return Purchase.objects.filter(
                Q(product__content__contactrole__contact=organization) |
                Q(product__content__parent__content_live__contactrole__contact=organization),
                # TODO: Purchase is not publishable; has no publish_status field???
                publish_status="PUBLISHED")


admin.site.register(Purchase, PurchaseAdmin)


class PaymentAdmin(admin.ModelAdmin):
    # CURRENTLY ONLY USED FOR ADDING CHECK PAYMENTS!
    raw_id_fields = ['user', 'created_by', 'updated_by']
    fieldsets = [
        (None, {
            "fields": (
                ("amount"),
                ("billing_name"),
                ("method"),
                ("card_check_number"))
        })
    ]
    form = PaymentAdminForm

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        is_org_store_admin = has_webgroup(
            user=request.user, required_webgroups=["organization-store-admin"])
        if is_org_store_admin:
            return {}
        else:
            return super().get_model_perms(request)

    def get_form(self, request, obj=None, **kwargs):
        # for setting the initial payment amount

        amount = request.GET.get("amount")
        form = super(PaymentAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['amount'].initial = amount
        return form

    def save_model(self, request, payment, form, change):
        # for processing check (and possibly cash) payments ONLY
        order_id = request.GET.get("order")
        method = request.POST.get("method", "CHECK")
        order = Order.objects.get(id=order_id)
        payment.method = method
        payment.order = order
        payment.user = order.user
        payment.contact = order.user.contact
        payment.status = "P"
        payment.save()

        # determines which cash GL account the payment should write to
        is_chapter_admin = False

        is_org_store_admin = has_webgroup(
            user=request.user, required_webgroups=["organization-store-admin"])

        if is_org_store_admin:
            is_chapter_admin = True

        payment.process(is_chapter_admin)

        for purchase in order.get_purchases():
            purchase.process(
                checkout_source="T3GO",
                is_chapter_admin=is_chapter_admin)

        order.process()

        order.send_confirmation()

        messages.success(request, "Check payment has been processed.")

    def response_add(self, request, obj, post_url_continue=None):
        # redirects user after payment is submitted back to the order
        order_id = request.GET.get('order')

        return HttpResponseRedirect("/admin/store/order/%s" % order_id)

    def get_queryset(self, request):

        # TO DO... we need to create this "product-admin" login group... we're
        #  checking for for that instead of staff (because chapter admins will
        #  also be marked as is_staff)
        if request.user.groups.filter(
            name__in=("staff-store-admin", "onsite-conference-admin")
        ).exists() or request.user.is_superuser:
            return super().get_queryset(request)
        else:
            organization = request.user.contact.\
                contactrelationship_as_target.all().filter(
                    relationship_type="ADMINISTRATOR").first().source

            # get all purchase order ids
            organization_order_ids = Purchase.objects.filter(
                Q(product__content__contactrole__contact=organization) |
                Q(product__content__parent__content_live__contactrole__contact=organization)
            ).exclude(
                order__isnull=True
            ).values_list('order__id', flat=True).distinct().order_by(
                'order__id'
            )

            return Payment.objects.filter(
                order__id__in=organization_order_ids
            ).distinct().order_by('id')


admin.site.register(Payment, PaymentAdmin)


# should change shown fields if payment type is changed
#  (hide address for check payments)
# add payments to another screen (when checking out as staff to process)


class PaymentInline(admin.StackedInline):
    model = Payment
    # raw_id_fields = ['user', 'created_by', 'updated_by']
    readonly_fields = (
        "method", "amount", "billing_name", "card_check_number", "pn_ref")
    # max_num = 0
    extra = 0
    fieldsets = [
        (None, {
            "fields": (
                ("method"), ("amount"), ("billing_name"), ("card_check_number"), ("pn_ref"),
                # ("address1"),("address2"), ("city"), ("zip_code"), ("country"),
            )
        })
    ]

    def get_max_num(self, request, obj=None, **kwargs):
        # do not allow anymore purchases to be added to an order after it has been submitted

        # payments = Payment.objects.filter(order=obj)
        # number_of_payments = payments.count()
        # pending_payments = payments.filter(status="P")
        return 0
        # if not obj or ( obj and (obj.balance() == 0 or obj.balance() > 0 or pending_payments)):
        #     return 0
        # else:
        #     number_of_payments = Payment.objects.filter(order=obj).count()
        #     return number_of_payments + 1

    # def formfield_for_choice_field(self, db_field, request=None, **kwargs):
    #     # limit admin choices for payment methods
    #     if db_field.name == 'method':
    #         kwargs['choices'] = (('', '---------'), ('CHECK', 'Check'), ('CASH', 'Cash'), ('CHECK_REFUND', 'Check Refund'), ('CC', 'Credit Card'), ('CC_REFUND', 'CC Refund'),)
    #     return db_field.formfield(**kwargs)

    def get_queryset(self, request):
        # hide $0 payments that are required when processing refund products
        qs = super(PaymentInline, self).get_queryset(request)
        return qs.filter().exclude(method="NONE")


class PurchaseInline(admin.StackedInline):
    model = Purchase
    extra = 0
    raw_id_fields = ['created_by', 'updated_by', 'product', 'product_price', 'option']
    autocomplete_lookup_fields = {"fk": ['created_by', 'updated_by', 'product_price']}
    formset = inlineformset_factory(parent_model=Order, model=Purchase, form=PurchaseInlineAdminForm)
    readonly_fields = ["product", "option", "get_question_1", "get_question_2", "get_question_3",
                       "get_agreement_statement_1", "get_agreement_statement_2", "get_agreement_statement_3",
                       "get_license_code", "get_redemption_date", "get_redemption_contact"]
    # max_num = 0

    fieldsets = [
        (None, {
            "fields": (
                ("product_price"), ("product"), ("option", "code"), ("quantity"), ("submitted_product_price_amount"),
                ("get_license_code", "get_redemption_date", "get_redemption_contact"),
                ("get_question_1"), ("question_response_1"), ("get_question_2"), ("question_response_2"),
                ("get_question_3"), ("question_response_3"),
                ("get_agreement_statement_1"), ("agreement_response_1"), ("get_agreement_statement_2"), ("agreement_response_2"),
                ("get_agreement_statement_3"), ("agreement_response_3"),
            )
        })
    ]

    def get_max_num(self, request, obj=None, **kwargs):
        # do not allow anymore purchases to be added to an order after it has been submitted

        if not obj:
            return 0
        else:
            number_of_purchases = Purchase.objects.filter(order=obj).count()
            return number_of_purchases + 1

    def get_question_1(self, obj):
        return obj.product.question_1
    get_question_1.short_description = 'Question 1:'

    def get_question_2(self, obj):
        return obj.product.question_2
    get_question_2.short_description = 'Question 2:'

    def get_question_3(self, obj):
        return obj.product.question_3
    get_question_3.short_description = 'Question 3:'

    def get_agreement_statement_1(self, obj):
        return obj.product.agreement_statement_1
    get_agreement_statement_1.short_description = 'Agreement Statement 1:'

    def get_agreement_statement_2(self, obj):
        return obj.product.agreement_statement_2
    get_agreement_statement_2.short_description = 'Agreement Statement 2:'

    def get_agreement_statement_3(self, obj):
        return obj.product.agreement_statement_3
    get_agreement_statement_3.short_description = 'Agreement Statement 3:'

    def get_license_code(self, obj):
        return [gl.license_code for gl in obj.purchase.learn_group_licenses.all()]
    get_license_code.short_description = 'License Code:'

    def get_redemption_date(self, obj):
        return [gl.redemption_date for gl in obj.purchase.learn_group_licenses.all()]
    get_redemption_date.short_description = 'Redemption Date:'

    def get_redemption_contact(self, obj):
        return [gl.redemption_contact for gl in obj.purchase.learn_group_licenses.all()]
    get_redemption_contact.short_description = 'Redeemer:'


class OrderAdmin(admin.ModelAdmin):
    """
    purchases and check payments are added with a status = "N" until purchase and payment is processed
    """
    model = Order
    list_display = ["get_id", "user", "get_name", "order_status", "get_products", "submitted_time", "submitted_user_id", "is_manual", ]
    search_fields = ["id", "=user__username", "=submitted_user_id"]
    list_filter = ["order_status", "is_manual", "payment__method"]
    inlines = [PurchaseInline, PaymentInline]
    raw_id_fields = ["user"]
    # autocomplete_lookup_fields = { "fk" : ['user'] }
    readonly_fields = ["get_name", "get_username", "purchase_total", "payment_total", "balance",
                       "payment_process_options",  # "payment_option_credit_card","payment_option_check", "payment_option_none",
                       "order_status", "is_manual", "add_comp_tickets", "email_confirmation_link", ]  # "payment_option_refund_credit_card", "payment_option_refund_check","add_comp_tickets",]
    list_per_page = 20

    fieldsets = [
        (None, {
            "fields": (
                ("user", "get_name", "order_status",),
                ("purchase_total", "payment_total", "balance", "is_manual",),
                ("add_comp_tickets", "payment_process_options"),
                ("email_confirmation_link"),
                # ("payment_option_credit_card", "payment_option_check", "payment_option_none",),
                # ("payment_option_refund_credit_card", "payment_option_refund_check",),
            )}
         ),
    ]

    def email_confirmation_link(self, obj):
        # custom email confirmation that admins can use to send order recap
        return ("""
                <div style='width:225spx;'>
                    <a class='grp-button' href='/store/admin/order/%s/email-confirmation/' style='display:inline; margin-right:10px;'>Send email confirmation for order</a>
                </div>
                """ % (obj.id))
    email_confirmation_link.short_description = "Order Confirmation"
    email_confirmation_link.allow_tags = True

    def get_order_submitter(self, obj):
        # determins who submitted the order (APA STAFF, CHAPTER ADMIN, or USER)
        pass

    def purchase_total(self, obj):
        return "{0:.2f}".format((obj.purchase_total()))
    purchase_total.allow_tags = True

    def payment_total(self, obj):
        return "{0:.2f}".format((obj.payment_total()))
    payment_total.allow_tags = True

    def balance(self, obj):
        return "{0:.2f}".format((abs(obj.balance())))
    balance.allow_tags = True

    def get_name(self, obj):
        if obj.user:
            return obj.user.first_name + " " + obj.user.last_name
        else:
            return ""
    get_name.short_description = "Name"

    def get_username(self, obj):
        if obj.user:
            return obj.user.username
        else:
            return ""
    get_username.short_description = "User ID"

    def payment_process_options(self, obj):
        order_id = obj.id
        balance = obj.balance()
        payment_pending_total = obj.payment_pending_total()
        balance = balance - payment_pending_total
        pending_purchases = obj.purchase_set.all().filter(status="P").exists()
        # pending_check = obj.payment_set.all().filter(method="CHECK", status="P").exists()

        # this is too messy... rethink this logic
        if order_id:
            if balance < 0:
                return ("""
                    <div style='width:575px;'>
                        <a class='grp-button' href='/store/manage/%s/payment/cc/' style='display:inline; margin-right:10px;'>Process Credit Card Payment and Submit</a>
                        <a  class='grp-button'  href='/admin/store/payment/add/?order=%s&amount=%s' style='display:inline'>Add Cash/Check Payment and Submit</a>
                    </div>
                    """ % (order_id, order_id, "{0:.2f}".format(-balance)))
            elif balance == 0 and pending_purchases:
                return ("<a  class='grp-button' href='/store/manage/%s/payment/none/'>Submit Without Payment</a>" % order_id)

            elif balance > 0:
                return ("""
                    <div style='width:575px;'>
                    <a class='grp-button' href='/store/manage/%s/payment/refund/?refund_type=CC_REFUND' style='margin-right:10px'>Process Credit Card Refund and Submit</a>
                    <a  class='grp-button'  href='/store/manage/%s/payment/refund/?refund_type=CHECK_REFUND' style='display:inline;'>Process Check Refund and Submit</a>
                    </div>
                    """ % (order_id, order_id))
            else:
                return("Add purchases and save first in order to submit.")
        else:
            return("Add purchases and save first in order to submit.")
    payment_process_options.allow_tags = True
    payment_process_options.short_description = "Submit this order"
    # complete_order.allow_tags = True

    def save_model(self, request, order, form, change):
        if not order.submitted_user_id:
            order.submitted_user_id = request.user.username
        if not order.submitted_time:
            order.submitted_time = timezone.now()

        order.is_manual = True
        order.save()

    def get_products(self, obj):
        # purchases = obj.get_purchases() # THIS RE-QUERIES EVERY RECORD!

        product_list = ''
        for purchase in obj.purchase_set.all():
            product_list += purchase.product.content.title + ', '

        return product_list

    def get_id(self, obj):
        return obj.id

    get_id.short_description = "Order ID"
    get_products.short_description = "Products"

    def add_comp_tickets(self, obj):
        # auto add comp tickets for events in the order

        order_id = obj.id

        if not order_id:
            return ("Add purchases and save first in order to add complimentary tickets.")
        return ("<a class='grp-button' href='/store/manage/%s/comp-tickets/update/'>Auto add complimentary tickets</a>" % order_id)
    add_comp_tickets.short_description = "Add Complimentary Tickets"
    add_comp_tickets.allow_tags = True

    # NOTE: AFTER SUBMITTING AN ORDER (ORDER STATUS ='SUBMITTED') THESE FIELDS SHOULD NOT BE EDITABLE!
    # SHOULD PRODUCTS HAVE STATUSES TOO? OR... REQUIRE NEW ORDER AND LOOP THROUGH ENTIRE PURCHASE HISTORY FOR REFUNDS
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)

        for obj in formset.deleted_objects:
            try:
                if isinstance(obj, Purchase):
                    if obj.status == "A":  # refund attempt

                        purchases_sum = Purchase.objects.filter(contact=obj.contact, product=obj.product, product_price=obj.product_price).aggregate(number_of_purchases=Sum('quantity')).get("number_of_purchases")
                        print('purchases sum: ' + str(purchases_sum))
                        if obj.quantity < 1:
                            messages.error(request, "This purchase cannot be refunded because it has a negative quantity.")
                        elif purchases_sum <= 0 or purchases_sum < obj.quantity:
                            messages.error(request, "This purchase cannot be refunded. Quantity refund attempt: {0}. Quantity avaiable to refund for this user: {1}".format(str(obj.quantity), str(purchases_sum)))
                        else:
                            imis_invoice_number = None

                            # ??? why isn't this changing? This should also stay as "A".
                            obj.status == "CA"
                            # create and process payment, then immediately process purchase
                            obj.save()

                            attendee = Attendee.objects.filter(purchase=obj).first()
                            if attendee:
                                imis_invoice_number = attendee.imis_invoice_number

                            # create refund object / attendee record if needed
                            obj.pk = None
                            obj.imis_batch = None
                            obj.imis_batch_date = None
                            obj.imis_trans_number = None
                            obj.quantity = -obj.quantity
                            obj.save()

                            # create refund payment
                            payment = Payment.objects.create(user=obj.user, contact=obj.contact, amount=0, order=obj.order, method="NONE", status="P")
                            payment.process()

                            obj = Purchase.objects.get(id=obj.id)
                            obj.process()

                    elif obj.status == "P":
                        obj.delete()
                    elif obj.status == "CA":
                        messages.error(request, "This purchase has already been refunded.")
                    else:
                        messages.error(request, "There was an error removing this product.")

                if isinstance(obj, Payment):
                    if obj.status == "A":
                        messages.error(request, "This payment has already been processed and cannot be deleted.")
                    elif obj.status == "P":
                        obj.delete()
            except Exception as e:
                print("****" + str(e))
        for instance in instances:

            if isinstance(instance, Purchase):

                product = instance.product_price.product

                purchases_sum = Purchase.objects.filter(order=instance.order, product=product, status="A", contact=instance.order.user.contact).aggregate(Sum('quantity'))['quantity__sum']

                edit_questions = Purchase.objects.filter(id=instance.id).first()

                if edit_questions:
                    edit_questions.question_response_1 = instance.question_response_1
                    edit_questions.question_response_2 = instance.question_response_2
                    edit_questions.question_response_3 = instance.question_response_3
                    edit_questions.save()

                if not purchases_sum:
                    purchases_sum = 0
                # do not let user add another event purchase without refunding the existing one first
                if purchases_sum > 0:
                    instance.product = instance.product_price.product
                    messages.error(request, "You must refund this user's existing event purchase before adding another.")
                elif instance.quantity < 1:
                    instance.product = instance.product_price.product
                    messages.error(request, "You cannot manually add a negative quantity to the order.")
                # removed for adjustment purchases
                # elif instance.submitted_product_price_amount < 0:
                #    instance.product = instance.product_price.product
                #    messages.error(request, "Purchases cannot have a negative amount.")
                else:
                    instance.user = instance.order.user
                    instance.contact = instance.order.user.contact
                    instance.amount = instance.submitted_product_price_amount * abs(instance.quantity)

                    instance.product = instance.product_price.product

                    if instance.product_price.option_code:
                        try:
                            instance.option = ProductOption.objects.get(code=instance.product_price.option_code, product=instance.product)
                        except ProductOption.DoesNotExist:
                            messages.error("""WARNING: purchase was saved, but there was a problem determining the option associated with the selected
                                price. The price record was probably created incorrectly. Please verify that any option code
                                '""" + instance.product_price.option_code + """' associated with this price
                                is correct, and then try re-saving this purchase.""")
                    instance.save()
            if isinstance(instance, Payment):
                instance.user = instance.order.user
                instance.contact = instance.order.user.contact
                instance.save()

    def get_queryset(self, request):
        # also only events with parent NPC! or some tag?
        if request.user.groups.filter(
            name__in=("staff-store-admin", "onsite-conference-admin")
        ).exists() or request.user.is_superuser:
            return super().get_queryset(request).select_related(
                "user"
            ).prefetch_related(
                "purchase_set__product__content"
            )
        else:
            organization = request.user.contact.contactrelationship_as_target.all().filter(
                relationship_type="ADMINISTRATOR"
            ).first()

            if organization is None:
                raise PermissionDenied()
            else:
                organization = organization.source
            # purchase to organization

            # get all purchases
            organization_order_ids = Purchase.objects.filter(Q(product__content__contactrole__contact=organization) | Q(product__content__parent__content_live__contactrole__contact=organization)).exclude(order__isnull=True).values_list('order__id', flat=True).distinct().order_by('order__id')
            # limited date because we do not want to display old orders with no products on the admin dashboard
            return Order.objects.filter(Q(id__in=organization_order_ids) | Q(purchase__isnull=True), submitted_time__gte='2016-05-01').select_related("user").prefetch_related("purchase_set__product__content").distinct()

    def change_view(self, request, object_id, form_url='', extra_context=None):
        try:
            order = Order.objects.get(id=object_id)
            wcw_contact_sync = WCWContactSync(order.user.contact)
            wcw_contact_sync.pull_licenses_redeemed_from_wcw(order)
        except:
            pass

        return super(OrderAdmin, self).change_view(
            request, object_id, form_url, extra_context=extra_context)


class ProductPriceAdmin(admin.ModelAdmin):

    list_display = ("product", "title", "price", "status", "get_product_type", "code", "option_code")
    search_fields = ("product__code", "product__title", "title")
    readonly_fields = ["created_by", "created_time", "updated_by", "updated_time", "product", "code_explanation"]
    list_filter = ("product__product_type", "status",)
    fieldsets = [
        (None, {
            "fields": (
                ("title", "price", "status"),
                ("min_quantity", "max_quantity"),
                ("priority", "begin_time", "end_time", "event_pricing_cutoff_type"),
                ("required_groups", "exclude_groups"),
                ("option_code",),
                ("other_required_product_code", "other_required_option_code", "other_required_product_must_be_in_cart"),
                ("code_explanation", "code"),
                ("imis_reg_class", "comped"),
                "description"
            )
        }),
    ]

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        if has_webgroup(user=request.user, required_webgroups=["organization-store-admin"]):
            return {}
        else:
            return super().get_model_perms(request)

    def get_queryset(self, request):

        # TO DO... we need to create this "product-admin" login group... we're checking for for that instead of staff (because chapter admins will also be marked as is_staff)
        if request.user.groups.filter(
            name__in=("staff-store-admin", "onsite-conference-admin")
        ).exists() or request.user.is_superuser:
            return super().get_queryset(request).select_related("product").filter(publish_status="PUBLISHED")
        else:
            # organization = Organization.objects.get(user__username='050501')
            organization = request.user.contact.contactrelationship_as_target.all().filter(relationship_type="ADMINISTRATOR").first().source
            return ProductPrice.objects.filter(Q(product__content__contactrole__contact=organization) | Q(product__content__parent__content_live__contactrole__contact=organization), publish_status="PUBLISHED", status__in=("A", "H"), product__status__in=("A", "H")).select_related("product").distinct().order_by('-product__code')

    def code_explanation(self, obj):
        return "Enter code if a comp or discount code is needed in order to receive this price."

    def get_product_type(self, obj):
        return obj.product.product_type
    get_product_type.short_description = 'Product Type'


class ProductPriceInline(admin.StackedInline):
    model = ProductPrice
    fk_name = "product"
    extra = 0
    can_delete = False

    readonly_fields = ["created_by", "created_time", "updated_by", "updated_time", "code_explanation"]

    filter_horizontal = ["required_product_options", "required_groups", "exclude_groups"]

    fieldsets = [
        (None, {
            "fields": (
                ("title", "price", "status", "event_pricing_cutoff_type"),
                ("min_quantity", "max_quantity"),
                ("priority", "begin_time", "end_time"),
                ("required_groups", "exclude_groups"),
                ("option_code",),
                ("other_required_product_code", "other_required_option_code", "other_required_product_must_be_in_cart"),
                ("code_explanation", "code"),
                ("imis_reg_class", "comped"),
                "include_search_results"
            )
        }),
    ]
    sortable_field_name = "priority"  # grappelli sorting inlines

    def code_explanation(self, obj):
        return "Enter code if a comp or discount code is needed in order to receive this price."

    def save_model(self, request, content, form, change):
        if not change:
            content.created_by = request.user

        content.updated_by = request.user
        content.save()

    def get_queryset(self, request):
        # also only events with parent NPC! or some tag?
        return super().get_queryset(request).order_by("priority")


class ProductOptionInline(admin.StackedInline):
    model = ProductOption
    fk_name = "product"
    extra = 0

    fieldsets = [
        (None, {
            "fields": [
                ("title",),
                ("code", "status", "sort_number",),
                ("description"),
            ]
        })
    ]

    readonly_fields = ["created_by", "created_time", "updated_by", "published_by", "updated_time"]


class ProductInline(nested_admin.NestedStackedInline):
    model = Product
    extra = 1
    classes = ("grp-collapse grp-closed",)
    inline_classes = ("grp-open",)
    verbose_name_plural = "Product"
    verbose_name = "product details"
    form = ProductInlineAdminForm
    # filter_horizontal = ["future_groups"] # NEEDED?

    # readonly_fields = BaseContentAdmin.readonly_fields + ("get_regular_remaining", "get_standby_remaining", "current_quantity_taken")
    readonly_fields = BaseContentAdmin.readonly_fields + ("get_regular_remaining", "current_quantity_taken")

    inlines = [ProductOptionInline, ProductPriceInline]

    fieldsets = [
        (None, {
            "fields": [
                ("code", "status", "product_type",),
                ("imis_code", "gl_account", "shippable",),
                ("max_quantity", "max_quantity_per_person"),
                ("get_regular_remaining",),
                "email_template",
            ]
        }),
        ("Advanced product info", {
            "classes": ("collapse", "grp-collapse grp-closed",),
            "fields": ("title", "description", "future_groups",
                       "confirmation_text",
                       "reviews",
                       "question_1", "question_2", "question_3",
                       "agreement_statement_1", "agreement_statement_2", "agreement_statement_3"
                       )
        }),
    ]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "email_template":
            kwargs["queryset"] = EmailTemplate.objects.all().order_by('title')
        return super(ProductInline, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        if has_webgroup(user=request.user, required_webgroups=["organization-store-admin"]):
            return {}
        else:
            return super().get_model_perms(request)

    def get_regular_remaining(self, obj, *args, **kwargs):
        try:
            product_info = obj.content.master.content_live.product.get_purchase_info()
        except:
            product_info = None

        if product_info:
            return product_info['regular_remaining']
        else:
            return None
    get_regular_remaining.short_description = 'Regular remaining'

    def get_master(self, obj, *args, **kwargs):
        return obj.content.master

    def get_queryset(self, request):
        # also only events with parent NPC! or some tag?
        return super().get_queryset(request).select_related("content__master")

    def save_model(self, request, obj, form, change):
        if not obj:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# NOTE: CIRCULAR IMPORT ERROR WHEN ADDING TO CONTENT ADMIN WITH PRODUCT INLINE .FORCED TO ADD THIS IN THE STORE ADMIN?
class ContentProductAdmin(nested_admin.NestedModelAdmin, ContentAdmin):
    # fieldsets = (
    #     ("General Information", ("title", "code", "status", "description"), ),
    #         )
    list_filter = ("product__product_type", PublishStatusListFilter)
    list_display = ContentAdmin.list_display + ("publish_status",)

    # Consider rethinking now that books / on-demand no longer sold
    format_tag_choices = ["FORMAT_BOOK", "FORMAT_EBOOK", "FORMAT_LIVE_IN_PERSON_EVENT", "FORMAT_LIVE_ONLINE_EVENT", "FORMAT_ON_DEMAND_EDUCATION"]
    inlines = [ProductInline, CollectionRelationshipInline]

    publish_to_staging_on_save = True
    show_sync_harvester = False

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        if has_webgroup(user=request.user, required_webgroups=["organization-store-admin"]):
            return {}
        else:
            return super().get_model_perms(request)

    def get_product_type(self, obj):
        return obj.product.product_type

    def save_model(self, request, obj, form, change):
        super(ContentAdmin, self).save_model(request, obj, form, change)


admin.site.register(Order, OrderAdmin)
admin.site.register(ContentProduct, ContentProductAdmin)
admin.site.register(ProductPrice, ProductPriceAdmin)
