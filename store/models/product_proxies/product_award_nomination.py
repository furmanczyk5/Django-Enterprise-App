from django.apps import apps
from django.db import models
from django.utils import timezone

from store.models.product import Product
from store.utils.prevent_delete_purchases_queryset import PreventDeletePurchasesQuerySet


class ProductAwardNominationManager(models.Manager):
    """
    manager for querying registration
    """
    def get_queryset(self):
        return super().get_queryset().filter(product_type="AWARD")


class ProductAwardNomination(Product):
    """
    Awards product proxy class
    """
    objects = ProductAwardNominationManager.from_queryset(PreventDeletePurchasesQuerySet)()

    def process_purchase(self, purchase_instance, purchase_json, *args, **kwargs):
        """
        function to write to iMIS, etc. that's specific to awards
        """
        AwardSubmission = apps.get_model(app_label="awards", model_name="submission")
        award_submission = AwardSubmission.objects.get(master=purchase_instance.content_master, publish_status="SUBMISSION")
        award_submission.status = "A"
        award_submission.submission_time = timezone.now()
        award_submission.save()

    class Meta:
        proxy = True
