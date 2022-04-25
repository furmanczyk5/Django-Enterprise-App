from django.db import models

from events.models import EventSingle, EventMulti, Activity, Course, Event

from store.utils.prevent_delete_purchases_queryset import PreventDeletePurchasesQuerySet
from store.utils.scholarlab import ScholarLab

from store.models.product import Product

class ProductStreamingManager(models.Manager):
    """
    manager for querying streaming products
    """
    def get_queryset(self):
        return super().get_queryset().filter(product_type="STREAMING")

class ProductStreaming(Product):
    """
    Streaming product proxy class. NOTE, in general, streaming (on-demand) products are going away
    09/2018 with the launch of the APA Learn. However, the exam prep product (STR_EXAM3 product code)
    is one exception that will be sold for a while longer.
    """

    objects = ProductStreamingManager.from_queryset(PreventDeletePurchasesQuerySet)()

    def process_purchase(self, purchase_instance, purchase_json, *args, **kwargs):
        """
        function to write to iMIS, etc. that's specific to events
        """
        # grant access to exam prep product
        if self.code == "STR_EXAM3":
            ScholarLab().create_access(purchase_instance.user)
            
    class Meta:
        proxy = True