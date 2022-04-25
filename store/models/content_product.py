from django.db import models

from content.models import Content

class ContentProductManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(content_type="PRODUCT").select_related("product")

class ContentProduct(Content):
    """
    Represents content records for products. All products must be linked to a content record. For products
    such as events, activities, APA learn courses, etc. products are linked to the specific event/activity/course/etc.
    for that product.

    For products that don't already have a specific type of content corresponding to the product type, this 
    "ContentProduct" is the catch-all default.

    """
    objects = ContentProductManager()

    def save(self, *args, **kwargs):
        self.content_type = "PRODUCT"
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "Product"
        verbose_name_plural = "Other Products"