from django.db import models
from django.utils import timezone

from jobs.models import Job

from store.utils.prevent_delete_purchases_queryset import PreventDeletePurchasesQuerySet

from store.models.product import Product

class ProductJobAdManager(models.Manager):
    """
    manager for querying job products
    """
    def get_queryset(self):
        return super().get_queryset().filter(product_type="JOB_AD")

class ProductJobAd(Product):
    """
    Job product proxy class
    """

    objects = ProductJobAdManager.from_queryset(PreventDeletePurchasesQuerySet)()

    def process_purchase(self, purchase_instance, purchase_json, *args, **kwargs):
        """
        function to write to iMIS, etc. that's specific to events
        """

        job = Job.objects.get(master = purchase_instance.content_master)
        job.submission_time = timezone.now()
        job.save()
        job.ad_publish()


    class Meta:
        proxy = True
