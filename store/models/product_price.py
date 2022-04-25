from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import models

from content.models import BaseContent, Publishable
from store.utils.prevent_delete_purchases_queryset import PreventDeletePurchasesQuerySet
from .settings import EVENT_PRICING_CUTOFF_TYPES


class ProductPrice(BaseContent, Publishable):
    """
    represents a price for a product... in order to be able to purchase a product,
    at least 1 price must apply
    """
    product = models.ForeignKey('Product', related_name="prices", on_delete=models.CASCADE)
    legacy_id = models.IntegerField(null=True, blank=True)

    # priority for assigning this price if multiple prices apply... lower numbers come first
    priority  = models.IntegerField(default=0)

    price = models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True)

    # sometimes needed for syncing the transaction data to imis:
    imis_reg_class = models.CharField(max_length=50, null=True, blank=True)

    required_groups = models.ManyToManyField(Group, related_name="product_prices_require", blank=True)
    exclude_groups = models.ManyToManyField(Group, related_name="product_prices_exclude", blank=True)

    # TO DO... stale field... REMOVE
    required_product_option = models.ForeignKey(
        "ProductOption",
        verbose_name="Associated Option",
        blank=True,
        null=True,
        help_text="The option required for this product to get this price.",
        on_delete=models.SET_NULL
    )

    option_code = models.CharField(max_length=200, null=True, blank=True,
        help_text="If this price applies to a particular option above, enter the code for that option here")
    other_required_product_code = models.CharField(max_length=200, null=True, blank=True,
        help_text="""If this prices requires that the user have purchased another product in order
            to receive this price for this product, then enter the code for that other product here""")
    other_required_option_code = models.CharField(max_length=200, null=True, blank=True,
        help_text="""If, an "Other required product code" is entered to the left, and for that other product,
            a particular option must have been choosen in order to receive this price, then enter that
            other product's option code here""")

   # means that the product must by in the user's cart AT THE SAME TIME:
    other_required_product_must_be_in_cart = models.BooleanField(default=False,
        help_text="""If, an "Other required product code" is entered to the left, and that other product
            must be purchased at the same time as this product (i.e. purchased in the same order
            as opposed to purchased at any point in the past), then check this box""")

    # TO DO... would be better to name these "other_required_product" and "other_required_product_options"
    required_product = models.ForeignKey(
        "Product",
        verbose_name="Other required product",
        related_name="price_required_by",
        blank=True,
        null=True,
        help_text="If this price requires that another product be purchased in order to receive it, enter that product here.",
        on_delete=models.SET_NULL
    )

    required_product_options = models.ManyToManyField("ProductOption", verbose_name="Other required options", related_name="prices_required_by", blank=True,
        help_text="If this price requires that specific options from another product be purchased in order to receive it, enter those options here."
        )
    comped = models.BooleanField("Comped/auto-included for given required products", default=False)

    begin_time = models.DateTimeField('begin time', null=True, blank=True)
    end_time = models.DateTimeField('end time', null=True, blank=True)
    include_search_results = models.BooleanField(default=False,
        help_text="show this price in the search results list")
    # groups that WILL be assigned once product is purchased... for future use:

    max_quantity = models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True)
    min_quantity = models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True)

    event_pricing_cutoff_type = models.CharField(max_length=20, choices=EVENT_PRICING_CUTOFF_TYPES, null=True, blank=True,
        help_text="For iMIS events to link registrants with early, regular, or late registration pricing.")

    # TO DO... ability to execute this logic for a SET of products/prices all at once... reduce queries

    objects = PreventDeletePurchasesQuerySet.as_manager()

    publish_reference_fields = [
        {"name":"required_groups",
            "publish":False,
            "multi":True,
        },
        {"name":"exclude_groups",
            "publish":False,
            "multi":True,
        }
    ]

    def delete(self, *args, **kwargs):
        if not self.purchases.exists():
            super().delete(*args, **kwargs)
        else:
            raise ValidationError("Cannot delete Product Prices that have at least one Purchase")

    def __str__(self):
        code_string = " | " + str(self.code) if self.code else ""
        option_string = " (" + str(self.option_code) + " option ) " if self.option_code else ""
        return option_string + "$" + str(self.price) + code_string + " | " + str(self.product) + " | " + str(self.status)
