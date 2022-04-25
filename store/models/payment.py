from decimal import Decimal

from django.db import models

from .line_item import LineItem
from .purchase import Purchase
from .settings import PAYMENT_METHODS


class Payment(LineItem):
    """
    represents a payment line item
    """
    method = models.CharField(max_length=50, choices=PAYMENT_METHODS)
    billing_name = models.CharField(max_length=60, null=True, blank=True)  # e.g. name as it appears on the card
    card_check_number = models.CharField(max_length=50, null=True, blank=True,
                                         verbose_name="Check number / credit card ending digits",
                                         help_text="""For check or credit card payments: enter check number or credit card ending digits
                for payments processed manually.
                DO NOT enter full credit card numbers in this field.""")
    card_expires_time = models.CharField(max_length=50, null=True, blank=True,
                                         verbose_name="Credit Card expiration date")  # encrypted representation of the card expiration
    pn_ref = models.CharField(max_length=50, null=True, blank=True)  # pay pal transaction ID

    def imis_format(self, is_chapter_admin=False):

        # convert since tedious doesn't work well with passing boolean types
        if is_chapter_admin:
            is_chapter_admin = 1
        else:
            is_chapter_admin = 0

        formatted_content = {
            "OrderID": self.order.id,
            "Method": self.method,
            "Amount": self.amount,
            "PNRef": self.pn_ref,
            "WebUserID": self.user.username,
            "PaymentID": self.id,
            "InvoiceReferenceNumber": 0,
            "IsChapterAdmin": is_chapter_admin
        }

        return formatted_content

    def process(self):
        self.status = "A"
        self.save()

    def imis_ar_balance(self):
        # returns the balance amount for purchases and payments linked to the payment trans number
        purchase_sum = 0
        purchases = Purchase.objects.filter(imis_trans_number=self.imis_trans_number, contact=self.contact)

        payment_sum = self.amount

        for purchase in purchases:
            purchase_sum += purchase.quantity * purchase.submitted_product_price_amount

        if self.method in ("CC_REFUND", "CHECK_REFUND"):
            # amount added back to A/R is the refunded payment amount + any additional purchases that are added to this transaction (so that A/R balances)
            return Decimal(-self.amount) + Decimal(-purchase_sum)

        return Decimal(purchase_sum) - Decimal(payment_sum)

    def method_string(self):
        return next((pm[1] for pm in PAYMENT_METHODS if pm[0] == self.method), "No Payment")

    def get_payment_amount(self):
        """
        will return a negative amount if the payment is a refund
        """
        payment_amount = self.amount
        if self.method in ("CC_REFUND", "CHECK_REFUND", "REFUND", "REFUND_MAIL"):
            payment_amount *= -1
        return payment_amount

    def __str__(self):
        status = "unknown"
        if self.status == "A":
            status = "[ACTIVE]"
        elif self.status == "P":
            status = "[PENDING]"
        elif self.status == "CA":
            status = "[CANCELLED]"
        return str(str(self.method) + ' | amount: ' + str(self.amount) + ' | status: ' + status)
