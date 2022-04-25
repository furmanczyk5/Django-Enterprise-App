from django.db import models
from django.utils import timezone

from events.models import EventSingle, EventMulti, Activity, Course, Event

from store.utils.prevent_delete_purchases_queryset import PreventDeletePurchasesQuerySet

from store.models.product import Product


class ProductCMRegistrationManager(models.Manager):
    """
    manager for querying event products
    """
    def get_queryset(self):
        return super().get_queryset().filter(product_type="CM_REGISTRATION")

# TO CONSIDER... maybe this should move to the "cm" app...?
class ProductCMRegistration(Product):
    objects = ProductCMRegistrationManager.from_queryset(PreventDeletePurchasesQuerySet)()

    def process_purchase(self, purchase_instance, purchase_json, *args, **kwargs):
        """
        function to write to iMIS, etc. that's specific to purchasing CM registrations
        """
        if self.code=="CM_PROVIDER_REGISTRATION" or self.code=="CM_PROVIDER_REGISTRATION_2015" or self.code=="CM_PROVIDER_ANNUAL_2015" :
            try:
                # TO DO.. this should be in process purchases
                provider_registration = purchase_instance.provider_registration.first()
                provider_registration.status="A"
                # TO DO... send registration email here to all admins....
                provider_registration.save()

            except:
                pass
        elif self.code=="CM_PARTNER_REGISTRATION":
            pass

    class Meta:
        proxy = True