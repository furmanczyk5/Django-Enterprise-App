from django.db import models

from content.mail import Mail

from store.utils.prevent_delete_purchases_queryset import PreventDeletePurchasesQuerySet
from store.models.product import Product

class ProductDonationManager(models.Manager):
    """
    manager for querying donations product records
    """
    def get_queryset(self):
        return super().get_queryset().filter(product_type="DONATION")


class ProductDonation(Product):

    objects = ProductDonationManager.from_queryset(PreventDeletePurchasesQuerySet)()

    def process_purchase(self, purchase_instance, purchase_json, *args, **kwargs):

        # make donation active
        # purchase_instance.donation_set.filter(status__in=["A","N"]).update(status="A")

        contact = purchase_instance.contact
        # donation = purchase_instance.donation_set.first()
        product = purchase_instance.product

        mail_context = dict(
            contact=contact,
            # donation=donation,
            product=product,
            purchase=purchase_instance
        )

        # refunds do NOT have a donation record associated. We should add an update_deonations (like attendees) AFTER conference.
        # if donation:
        if product:
            Mail.send(mail_code="FOUNDATION_STAFF_NOTIFICATION", mail_context=mail_context)

            # if donation.is_tribute and donation.tribute_email:
            #     Mail.send(mail_code="FOUNDATION_TRIBUTE_NOTIFICATION", mail_to=donation.tribute_email, mail_context=mail_context)

    class Meta:
        proxy = True
