from django.db import models
from django.utils import timezone

from content.models import STATUSES, BaseAddress
from store.models import Purchase
from events.models import Event, NATIONAL_CONFERENCES, \
    NATIONAL_CONFERENCE_ADMIN
from myapa.models.contact import Contact

ATTENDEE_STATUSES = STATUSES + (("R", "Refund"), )


class Attendee(BaseAddress):
    """
    Stores a relationship between a contact and an event/acivity to indicate that
    the contact is attending (e.g. is registered for) that event/activity.
    Should be used for all event ticketing and non-financial reporting (e.g. activity counts).
    """
    # TBD.... include reg class here?
    status = models.CharField(max_length=5, choices=ATTENDEE_STATUSES, default="A")
    event = models.ForeignKey(Event, related_name="attendees", on_delete=models.CASCADE) # should be master id???
    contact = models.ForeignKey(Contact, related_name="attending", on_delete=models.CASCADE)
    purchase = models.ForeignKey(Purchase, related_name="attendees", null=True, blank=True, on_delete=models.SET_NULL) # default delete behavior is CASCADE, attendee records will be delete d when purchases are deleted
    added_time = models.DateTimeField(editable=False)
    is_standby = models.BooleanField(default=False)

    badge_name = models.CharField(max_length=20, blank=True)
    badge_company = models.CharField(max_length=60, blank=True)
    badge_location = models.CharField(max_length=60, blank=True)

    # change invoice_number to reference_number for matching imis?
    imis_invoice_number = models.IntegerField(null=True, blank=True) # this is actually the INVOICE_REFERENCE_NUMBER
    imis_order_number = models.IntegerField(null=True, blank=True)

    last_printed_time = models.DateTimeField(null=True, blank=True)
    ready_to_print = models.BooleanField(default=False)
    print_count = models.IntegerField(default=0)

    # rating = models.IntegerField(blank=True, null=True) ... assume we won't use this

    def activity_attendance(self, *args, **kwargs):
        """
        returns queryset of all child activity attendee for this contact and this parent event, for any attendee status
        """
        return Attendee.objects.filter(event__parent=self.event.master, event__event_type="ACTIVITY", contact=self.contact).select_related("event", "purchase")


    # is this adding unnecessary db hits??
    def __str__(self):

        return str(self.id) + " | " + str(self.contact) + " | " + str(self.event)

    def save(self, *args, **kwargs):

        if not self.added_time:
            self.added_time = timezone.now()

        return super().save(*args, **kwargs)

    def get_member_type_friendly(self):
        member_type = self.contact.member_type
        if member_type in ["MEM", "FCLTS", "FCLTI", "LIFE", "RET", "GPBM", "NP"]:
            return "MEMBER"
        elif member_type in ["STU", "FSTU"]:
            return "STUDENT"
        else:
            return ""

    def order_overview(self):
        """
        returns a dict with purchase/payment/balance totals
        """

        purchase_total = 0
        payment_total = 0
        balance = 0


        #1. get all distinct orders that are associated with the event for this user
            #a. get the main event product
        if self.event.event_type == "ACTIVITY":
            # if this attendee record is for an activity, then we need to get the parent attendee record for the event as a whole and use that:
            main_product = self.event.parent.content_live.product
            event_attendee_list = Attendee.objects.filter(contact=self.contact, purchase__product=main_product)
        else:
            # otherwise, if this is an event, then use this attendee record
            event_attendee_list = Attendee.objects.filter(contact=self.contact, purchase__product=self.purchase.product)

        for event_attendee in event_attendee_list:
            # TO DO... figure out how to reduce query count...
            activity_attendance = event_attendee.activity_attendance().select_related("purchase__order")

            orders_list = [] #[activity_attendance.purchase.order for x in activity_attendance]
            purchase_list = []

            # # add purchases/payments for orders related to event
            if event_attendee.purchase:
                purchase_list.append(event_attendee.purchase)
                purchase_total += event_attendee.purchase.submitted_product_price_amount * event_attendee.purchase.quantity
                if event_attendee.purchase.order:
                    orders_list.append(event_attendee.purchase.order)

            for attendee in activity_attendance:
                if attendee.purchase:
                    purchase_total += attendee.purchase.submitted_product_price_amount * attendee.purchase.quantity

                    purchase_list.append(attendee.purchase)

                    if attendee.purchase.order and attendee.purchase.order not in orders_list:
                        orders_list.append(attendee.purchase.order)

            # print("activity_attendance: {0}".format(str(activity_attendance)))
            # print("event_attendee_list: {0}".format(str(event_attendee_list)))
            # print("purchase list: {0}".format(str(purchase_list)))
            # print("order list: {0}".format(str(orders_list)))
            for order in orders_list:

                # first add all payments in for related orders
                for payment in order.payment_set.all():
                    payment_total += payment.amount
            #     # now, subtract out purchase amounts from the payment total for any unrelated purchases (we're assuming that unrelated purchases are paid in full)
                for purchase in order.purchase_set.all():
                    if purchase not in purchase_list:
                        payment_total -= purchase.submitted_product_price_amount


            balance += payment_total - purchase_total

        return (purchase_total, payment_total, balance)

        # 2. add purchases/payments for orders related to event
        #  for order in orders_list:
        # 3. add all payments related to the event from orders
        # 4. subtract purchases not related to the event from payments
        # 4. return purchase/payment/balance dict values back

