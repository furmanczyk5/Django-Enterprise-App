from django.db import models

from content.mail import Mail

from store.utils.prevent_delete_purchases_queryset import PreventDeletePurchasesQuerySet
from store.models.product import Product

# NOTE / TO DO: currently these proxies are not needed... but likely that they will be needed
# soon with LMS development... if not, then they should be deleted

class ProductLearnCourseManager(models.Manager):
    """
    manager for querying streaming products
    """
    def get_queryset(self):
        return super().get_queryset().filter(product_type="LEARN_COURSE")

class ProductLearnCourse(Product):
    """
    APA Learn product proxy class
    """

    objects = ProductLearnCourseManager.from_queryset(PreventDeletePurchasesQuerySet)()

    def process_purchase(self, purchase_instance, purchase_json, *args, **kwargs):
        pass

    class Meta:
        proxy = True