from django.db import models
from django.core.exceptions import ValidationError

from content.models import BaseContent, Publishable

from store.utils.prevent_delete_purchases_queryset import PreventDeletePurchasesQuerySet

from .product_price import ProductPrice


class ProductOption(BaseContent, Publishable):
    """
    represents an option that a user can select for a given product
    (a registration type, a product format, etc.)
    """
    product = models.ForeignKey("Product", related_name="options", on_delete=models.CASCADE)
    sort_number = models.PositiveIntegerField(default=999, null=True, blank=True)

    objects = PreventDeletePurchasesQuerySet.as_manager()

    def imis_format(self):
        """
        for syncing product options to iMIS
        """

        # try to get a price for the option first. if none exist, set to $9999
        price = ProductPrice.objects.filter(product=self.product, option_code=self.code).first()
        if price:
            price = price.price
        else:
            price = 1

        formatted_content = {
            "ConferenceCode": self.product.content.product.imis_code,
            "BeginTime": str(self.product.content.begin_time)[:19],
            "EndTime": str(self.product.content.end_time)[:19],
            "Code": self.code,
            "Title": self.title,
            "GLAccount": self.product.gl_account,
            "Status": self.status,
            "Price": price,
        }

        return formatted_content

    def delete(self, *args, **kwargs):
        purchases = self.purchases.all()
        if not purchases:
            super().delete(*args, **kwargs)
        else:
            raise ValidationError("Cannot delete Product Options that have at least one Purchase")

    def __str__(self):
        return str(self.code) + " | " + str(self.title)
