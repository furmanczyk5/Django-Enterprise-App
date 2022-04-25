import datetime
import traceback

from django.apps import apps
from django.core.mail import send_mail
from django.db import models
from django.db.models.aggregates import Sum
from sentry_sdk import capture_exception, capture_message

from content.mail import Mail
from content.models.settings import ContentType, ContentStatus
from imis.enums.relationship_types import ImisRelationshipTypes
from imis.event_tickets import *
from myapa.models.contact import Contact
from myapa.models.contact_relationship import ContactRelationship
from store.models.settings import ProductTypes
from .line_item import LineItem
from ..utils import PurchaseInfo


# TO DO... THIS MODEL IS A HOT MESS!
# TO DO... create a PurchaseManager that always queries related products (will almost always want to show related products with purchases)?
class Purchase(LineItem):
    """
    represents a purchase line item for an order, or an item in a user's cart if order reference not set (before submitting order)
    """
    # the product being purchased:
    product = models.ForeignKey('Product', related_name='purchases', on_delete=models.PROTECT)
    content_master = models.ForeignKey(
        "content.MasterContent",
        related_name="purchases",
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )

    # recipient of the purchase... generally the same as the Purchase.contact unless purchase is transferred to someone else, or (eventually) if purchased on behalf of organization
    contact_recipient = models.ForeignKey(
        Contact,
        related_name="purchases_received",
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL
    )

    # the price that applies for this purchase... updated as needed while item in cart; should not be updated once order submitted:
    # allow null only as a safety measure / for legacy data where there may not be related price records
    product_price = models.ForeignKey('ProductPrice', related_name="purchases", on_delete=models.PROTECT)

    option = models.ForeignKey("ProductOption", related_name="purchases", blank=True, null=True, on_delete=models.SET_NULL)

    # once order for this purchase is submitted/created price value is also set here for historical data (the price of the product at the time of the order submission):
    submitted_product_price_amount = models.DecimalField(
        decimal_places=2,
        max_digits=9,
        verbose_name="amount to be charged"
    )

    quantity = models.DecimalField(decimal_places=2, max_digits=6, default=1)

    question_response_1 = models.CharField(max_length=500, blank=True, null=True)
    question_response_2 = models.CharField(max_length=500, blank=True, null=True)
    question_response_3 = models.CharField(max_length=500, blank=True, null=True)

    agreement_response_1 = models.BooleanField(default=False, verbose_name="response 1")
    agreement_response_2 = models.BooleanField(default=False, verbose_name="response 2")
    agreement_response_3 = models.BooleanField(default=False, verbose_name="response 3")

    first_name = models.CharField(max_length=20, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)

    expiration_time = models.DateTimeField(blank=True, null=True)

    for_someone_else = models.BooleanField(
        default=False,
        help_text="""Will this purchase be redeemed by someone else?
        (used to indicate that a "group license code" should be generated for an LMS purchase
        as opposed to immediate access for purchaser)."""
    )

    def validate(self, *args, **kwargs):
        if self.order:
            return True
        else:
            purchase_list = Purchase.objects.filter(
                product__product_type=ProductTypes.ACTIVITY_TICKET.value
            )
            for purchase in purchase_list:
                if purchase.product.content.content_type == ContentType.EVENT.value:
                    return True

    # TO DO... may want to rethink this:
    @classmethod
    def cart_items(cls, user):

        # should return cart items for both the user and associated company

        # we should be storing logged in user's company on the request, and pass in here
        company = ContactRelationship.get_company_contact(user=user)

        if company is not None:
            cart_query = cls.objects.filter(
                (models.Q(user=user) | models.Q(contact_recipient=company)),
                order__isnull=True
            )
        else:
            cart_query = cls.objects.filter(user=user, order__isnull=True)

        cart_items = cart_query.select_related(
            "product", "product_price"
        ).prefetch_related(
            "product__options",
            "product__prices__required_groups",
            "product__prices__required_product_options"
        ).filter(
            product__status__in=(ContentStatus.ACTIVE.value, ContentStatus.HIDDEN.value)
        ).order_by(
            'product__content__event__begin_time', 'product__product_type', 'product__title'
        )

        try:
            for purchase in cart_items:
                if purchase.product.max_quantity and purchase.product.max_quantity > 0:
                    # TODO: This new PurchaseInfo class is basically always assuming
                    #  an Event/Activity product type by default, which means it queries
                    #  iMIS for things like tickets remaining/standby, etc.
                    if purchase.product.product_type == ProductTypes.ACTIVITY_TICKET.value:
                        purchase_info = PurchaseInfo(purchase.product, user).get()
                        purchase._purchase_info = purchase_info  # for accessing this info afterwards

                        if purchase_info["product_sale_status"] == 'Regular':
                            if purchase_info["regular_remaining"] < purchase.quantity:
                                purchase.quantity = purchase_info["regular_remaining"]
                                purchase.save()
                        elif purchase_info["product_sale_status"] == 'Waitlist':
                            purchase.save()
                        else:
                            # assume sold out - remove product from cart
                            cart_items.exclude(id=purchase.id)
                            purchase.delete()
        except Exception as exc:
            capture_exception(exc)

        return cart_items

    @classmethod
    def cart_total(cls, user, cart_items=None):
        if cart_items:
            return sum([float(getattr(purchase, "amount", 0.0)) for purchase in cart_items])
        else:
            return cls.cart_items(user=user).aggregate(Sum("amount"))["amount__sum"]

    def process(self, *args, **kwargs):
        product_type_class = self.product.get_product_type_class()

        self.status = "A"
        if not self.submitted_time:
            self.submitted_time = timezone.now()
        self.save()

        try:

            is_chapter_admin = kwargs.get("is_chapter_admin", False)

            purchase_json = self.imis_format(is_chapter_admin=is_chapter_admin)

            product_type_instance = product_type_class.objects.get(id=self.product.id)
            product_type_instance.process_purchase(self, purchase_json, *args, **kwargs)

        except Exception as e:
            stack_trace = traceback.format_exc()
            try:
                subject = "ERROR - app: store | model: purchase | method: process.  user id: {0} | order id: {1}".format(self.order.user.username, self.order.id)
                mail_body = "There was an error running purchase.process() <br/><br/>"
                mail_body += "user id: {0} | order id: {1} |  purchase id: {2} | product code: {3}".format(self.order.user.username, self.order.id, self.id, self.product.code)
                mail_body +="<br/><br/>"
                mail_body += "<br/>Exception: <br/>"
                mail_body += str(e)
                mail_body +="<br/><br/>"
                mail_body += stack_trace
            except:
                subject = "STORE CHECKOUT ERROR"
                mail_body = str(e)
                mail_body +="<br/><br/>"
                mail_body += stack_trace
                print(str(stack_trace))
            send_mail(subject, mail_body, 'store@planning.org', ["rwest@planning.org","plowe@planning.org","akrakos@planning.org", "tjohnson@planning.org", "cmollet@planning.org", "msullivan@planning.org"], fail_silently=True, html_message=mail_body)

    def process_pending_check(self, *args, **kwargs):
        """ method called from cart when purchases are not processed immediately,
                but something else needs to be done on submit"""
        product_type_class = self.product.get_product_type_class()
        product_type_instance = product_type_class.objects.get(id=self.product_id)
        is_chapter_admin = kwargs.get("is_chapter_admin", False)
        purchase_json = self.imis_format(is_chapter_admin=is_chapter_admin)
        try:
            product_type_instance.process_pending_check_purchase(self, purchase_json, *args, **kwargs)
        except AttributeError:
            # We're going to assume for now that if a refactored store proxy model does not
            # implement a process_pending_check_purchase method it's because it doesn't need one
            # https://americanplanning.atlassian.net/browse/DEV-5744
            capture_message(
                "Attempted to call process_pending_check_purchase on {}, but "
                "that class does not implement this method".format(product_type_class),
                level='error'
            )

    def imis_format(self, **kwargs):

        # if the batch date matches the current date for any transaction associated with this order, use that trans number.
        # NOTE: need to allow staff to pass a trans number for t3go orders

        is_chapter_admin = kwargs.get("is_chapter_admin", False)

        # have to do this because node/sql issues converting to boolean types
        is_chapter_admin_int = 0

        if is_chapter_admin:
            is_chapter_admin_int = 1

        purchase_option = ''
        conference_code = ''

        if self.option:
            purchase_option = self.option.code
        # move this to the product model?
        if self.product.product_type == ProductTypes.EVENT_REGISTRATION.value:
            conference_code = self.product.imis_code
            product_code = conference_code + "/" + purchase_option
        elif self.product.product_type == ProductTypes.ACTIVITY_TICKET.value:
            conference_code = self.product.content.parent.content_live.product.imis_code
            product_code = conference_code + '/' + self.product.imis_code
        else:
            product_code = self.product.imis_code

        event_quantity = Purchase.objects.filter(
            product=self.product,
            contact=self.contact,
            product_price=self.product_price
        ).aggregate(
            Sum('quantity')
        )['quantity__sum']

        formatted_content = {
            "WebUserID": self.user.username,
            "Amount": self.amount,
            "ProductCode": product_code,
            "ProductOption": purchase_option,
            "DjangoProductCode": self.product.code,
            "ProductPrice": self.submitted_product_price_amount,
            "Option": purchase_option,
            "Quantity": self.quantity,
            "EventQuantity": event_quantity,
            "ProductTypeCode": self.product.product_type,
            "ConferenceCode": conference_code,
            # "EventPurchaseTotal": event_purchase_total,
            # "EventPaymentTotal": event_payment_total,
            # "EventBalanceTotal": event_balance_total,
            "PurchaseID": self.id,
            "InvoiceReferenceNumber": 0,
            "BatchNumber":self.imis_batch,
            "BatchTime":self.imis_batch_date,
            "TransNumber":self.imis_trans_number,
            "IsChapterAdmin":is_chapter_admin_int,
        }

        return formatted_content

    def payment_required_total(self):
        return (self.submitted_product_price_amount * self.quantity)

    def update_attendees(self, checkout_source="CART"):
        """
        Method to correct (create/edit/remove) the user's attendee records within this purchase record
        """

        from store.models.order import Order

        Attendee = apps.get_model(app_label="registrations", model_name="Attendee")
        attendees = self.attendees.all()
        offset = int(self.quantity) - len(attendees)

        # WTF is this for?
        assign_status = "N"
        try:
            if self.status=="A":
                assign_status = "A"
        except Order.DoesNotExist:
            pass

        user = self.user or self.contact.user
        contact = self.contact or self.user.contact

        if int(self.quantity) >= 0:
            if offset > 0:
                # add new attendee records
                added_time = timezone.now()
                new_attendee_records = [
                        Attendee(
                            event=self.product.content.event,
                            purchase=self,
                            contact=contact,
                            added_time=added_time
                        )
                        for _ in range(0, offset)
                ]
                Attendee.objects.bulk_create(new_attendee_records) # save method not called in bulk_create
            elif offset < 0:
                existing_attendee_records = Attendee.objects.filter(
                    event=self.product.content,
                    purchase__product=self.product,
                    purchase__order__user=user
                ) # status also?
                attendees.exclude(
                    pk__in=[a.pk for a in list(existing_attendee_records)[:offset]]
                ).delete()

            update_kwargs = {"status": assign_status}

            ready_to_print = checkout_source == "CONFERENCE_KIOSK" and assign_status == "A"
            if ready_to_print:
                update_kwargs["ready_to_print"] = True

            # Does this make some refunded attendee records active?... ecluding refunded purchases now
            #   NOTE: TO make this correctly assign status based on the state of the order, we need query for all attendee and purchases records on this order
            Attendee.objects.filter(
                purchase=self,
                contact=contact
            ).exclude(
                status="R"
            ).update(**update_kwargs)

        elif int(self.quantity) < 0:

            attendees.delete()

            # TO DO... wonky / not correct. Would be much cleaner to avoid refunds in process purchase altogether (instead just something that
            # happens on an individual attendee record)
            attendees = Attendee.objects.filter(
                event=self.product.content.event,
                contact=contact,
                purchase__product_price=self.product_price
            )

            purchases = Purchase.objects.filter(
                product=self.product,
                contact=self.contact,
                product_price=self.product_price
            ).exclude(
                order__isnull=True
            )

            refund_quantity = abs(sum([p.quantity for p in purchases if p.quantity < 0]))

            active_attendees = [a for a in attendees if a.status != "R"]
            refund_attendees = len([a for a in attendees if a.status == "R"])

            index = 0

            try:
                while refund_quantity != refund_attendees:
                    active_attendees[index].status = "R"
                    active_attendees[index].save()

                    index += 1
                    refund_attendees += 1
            except IndexError:
                pass

    def is_waitlist(self):
        if is_event_ticket(self):
            return is_waitlist_in_imis(self)
        return False

    def is_expired(self):
        # return self.expiration_time and force_utc_datetime(datetime.now()) > self.expiration_time
        return self.expiration_time and timezone.now() > self.expiration_time

    def activate_to_expire(self):
        """
        used when a member agrees to the expiration time of a product
        """
        if self.product.code == "STR_EXAM3":
            self.expiration_time = timezone.now() + datetime.timedelta(days=1095)
        else:
            self.expiration_time = timezone.now() + datetime.timedelta(days=184) # ondemand expires after 184 days (~6months)
        self.save()
        return self.expiration_time

    def send_confirmation(self):
        """
        sends product template for purchases
        """
        if self.product.email_template and self.quantity > 0:
                mail_context = {}
                mail_context["purchase"] = self
                Mail.send(mail_code=self.product.email_template.code, mail_to=self.contact.email, mail_context=mail_context)

    def save(self, *args, **kwargs):
        # TO DO set amount on save....
        # if order not set, then use the current product price to determine the line item amount, otherwise use the historical price
        # ALSO TO DO ... if no order set (still in cart) and no price applies for this purchase, then delete it

        # add provider to contact recipient for CM purchases
        if self.product.product_type in (
            ProductTypes.CM_REGISTRATION.value, ProductTypes.CM_PER_CREDIT.value
        ) and not self.contact_recipient:
            target = self.user.contact.get_imis_source_relationships().filter(
                relation_type__in=(
                    ImisRelationshipTypes.ADMIN_I.value,
                    ImisRelationshipTypes.CM_I.value
                )
            ).first()
            if target is not None:
                try:
                    self.contact_recipient = Contact.objects.get(user__username=target.target_id)
                except Contact.DoesNotExist:
                    # TODO: automatically create the Org record here?
                    capture_message(
                        "{} attempted to purchase a {} but the organization with iMIS ID {} "
                        "does not exist in Django".format(
                            self.user.contact,
                            self.product.code,
                            target.target_id
                        ),
                        level='warning'
                    )

        if not self.contact_recipient:
            self.contact_recipient = self.contact

        super().save(*args, **kwargs)

        if is_event_ticket(self):
            save_tickets_to_imis(self)

    def delete(self, *args, **kwargs):
        if is_event_ticket(self):
            delete_event_tickets(self)
        super().delete(*args, **kwargs)

    # FUTURE TO DO... add first/last name for shipping info
    def __str__(self):
        status = "unknown"
        if self.status == "A":
            status = "[ACTIVE]"
        elif self.status == "P":
            status = "[PENDING]"
        elif self.status == "CA":
            status = "[CANCELLED]"
        if self.product:
            return str(str(self.user) + ' | product: ' + str(self.product) + ' | price: ' + str(self.amount) + ' | qty: ' + str(self.quantity) + ' | total: ' + str(self.amount) + ' | status: ' + status )

