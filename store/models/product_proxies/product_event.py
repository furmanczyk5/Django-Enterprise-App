
# import requests
from django.db import models
# from sentry_sdk import add_breadcrumb

# from conference.models.settings import *
from conference.cadmium_api_utils import CadmiumAPICaller
# from planning.settings import CADMIUMCD_API_KEY, CADMIUMCD_REGISTRATION_TASK_ID
from store.models.product import Product
from store.utils.prevent_delete_purchases_queryset import PreventDeletePurchasesQuerySet


class ProductEventManager(models.Manager):
    """
    manager for querying event products
    """
    def get_queryset(self):
        return super().get_queryset().filter(content__content_type="EVENT") # better than looking at content_type ?


class ProductEvent(Product):

    objects = ProductEventManager.from_queryset(PreventDeletePurchasesQuerySet)()

    def process_purchase(self, purchase_instance, purchase_json, *args, **kwargs):
        """
        function to write to iMIS, etc. that's specific to events
        """

        #warning... NEVER call super().process_purchase here... it will create an infinite loop...
        # TO DO... create specific logic for writing event purchases to iMIS...

        # self.recalculate_current_quantity_taken()

        ## ATTENDEE RECORDS HANDLED IN PURCHASE SAVE METHOD

        contact = purchase_instance.contact

        if contact.external_id:
            cadmium_api_caller = CadmiumAPICaller()
            event = purchase_instance.product.content
            if event.content_type == 'EVENT':
                sync = cadmium_api_caller.django_event_to_cadmium_sync(event)
                if sync and sync.cadmium_event_key:
                    cadmium_api_caller.update_registration_status(contact, sync.cadmium_event_key)

    class Meta:
        proxy = True
