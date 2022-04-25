from django.apps import apps
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import models

from content.models import BaseContent, Publishable, Content
from store.models import Purchase
from store.utils.prevent_delete_purchases_queryset import PreventDeletePurchasesQuerySet
from .settings import PRODUCT_TYPES


class Product(BaseContent, Publishable):
    """
    for product/transactional information. ALL products must be associated with a content record.

    """
    content = models.OneToOneField(Content, related_name="product", on_delete=models.PROTECT)

    product_type = models.CharField(max_length=50, choices=PRODUCT_TYPES, blank=True,
        help_text="leave blank to auto-populate")
    imis_code = models.CharField(max_length=50, blank=False, null=True)
    max_quantity = models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True)
    max_quantity_per_person = models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True)
    # max_quantity_standby to be used as boolean for "waitlist enabled": False = 0 or True = 1 (or > 0)?
    max_quantity_standby = models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True)
    current_quantity_taken = models.DecimalField(decimal_places=2, max_digits=6, default=0)

    organizations_can_purchase = models.BooleanField(default=False)
    individuals_can_purchase = models.BooleanField(default=True)

    future_groups = models.ManyToManyField(Group, related_name="products_future", blank=True)

    gl_account = models.CharField(max_length=50)
    shippable = models.BooleanField(default=False)

    question_1 = models.TextField("custom question 1", blank=True, null=True)
    question_2 = models.TextField("custom question 2", blank=True, null=True)
    question_3 = models.TextField("custom question 3", blank=True, null=True)

    agreement_statement_1 = models.TextField("custom agreement checkbox 1", blank=True, null=True)
    agreement_statement_2 = models.TextField("custom agreement checkbox 2", blank=True, null=True)
    agreement_statement_3 = models.TextField("custom agreement checkbox 3", blank=True, null=True)

    email_template = models.ForeignKey(
        "content.EmailTemplate",
        related_name="products",
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )
    confirmation_text = models.TextField("custom confirmation text on receipt", blank=True, null=True)

    refund_cutoff_time = models.DateTimeField(help_text="If users can request refunds for this product online, then this date may be added as a cutoff for refund requests.",
                null=True, blank=True)

    reviews = models.TextField(null=True, blank=True,
        help_text="For APA-curated reviews of the product.")

    objects = PreventDeletePurchasesQuerySet.as_manager()

    # PUBLISHABLE STUFF
    publish_reference_fields = [
        {"name":"options",
            "publish":True,
            "multi":True,
            "replace_field":"product"
        },
        {"name":"prices",
            "publish":True,
            "multi":True,
            "replace_field":"product"
        },
        {"name":"future_groups",
            "publish":False,
            "multi":True
        }
    ]

    def get_product_type_class(self):
        product_type_classes = {
            "EVENT_REGISTRATION": apps.get_model(app_label='store', model_name='ProductEvent'),
            "ACTIVITY_TICKET": apps.get_model(app_label='store', model_name='ProductEvent'),
            "CM_PER_CREDIT": apps.get_model(app_label='store', model_name='ProductCMPerCredit'),
            "CM_REGISTRATION": apps.get_model(app_label='store', model_name='ProductCMRegistration'),
            "DUES": apps.get_model(app_label='store', model_name='ProductDues'),
            "STREAMING": apps.get_model(app_label='store', model_name='ProductStreaming'), # can go away eventually
            "JOB_AD": apps.get_model(app_label='store', model_name='ProductJobAd'),
            "EXAM_REGISTRATION": apps.get_model(app_label='store', model_name='ProductExamRegistration'),
            "EXAM_APPLICATION": apps.get_model(app_label='store', model_name='ProductExamApplication'),
            "AICP_CANDIDATE_ENROLLMENT": apps.get_model(app_label='store', model_name='ProductCandidateEnrollment'),
            "AWARD": apps.get_model(app_label='store', model_name='ProductAwardNomination'),
            "DONATION": apps.get_model(app_label='store', model_name='ProductDonation'),
            "RESEARCH_INQUIRY": apps.get_model(app_label='store', model_name='ProductResearchInquiry'),
            "LEARN_COURSE": apps.get_model(app_label='store', model_name='ProductLearnCourse'),
            }
        return product_type_classes.get(self.product_type, Product)


    def imis_format(self):
        """
        for submitting product data to imis
        """

        formatted_content = {
        "ProductMaxQuantity": self.max_quantity,
        "ProductCode": self.imis_code,
        "ProductTitle": self.title,
        "ProductGLAccount": self.gl_account,
        "ProductStatus": self.status,
        "ProductDescription": self.description,
        }

        # TO DO: this is messy... refactor...
        try:
            # no price exists (possibly hidden status?). automatically set the price to the first one associated with the product.
            if self.prices.all():
                formatted_content.update({"ProductPrice": self.prices.all()[0].price})
        except:
            pass

        return formatted_content

    def get_prices_all(self, user=None, contact=None, option=None, code=None):
        """
        returns a list of all prices that apply for the user
        """
        prices = self.prices.all()

        product_price_list = []

        for p in prices:
            if p.price_applies(user=user, contact=contact, option=option, code=code, ignore_webgroups=True):
                product_price_list.append(p)

        return product_price_list

    @classmethod
    def get_prices(cls, user=None, contact=None, queryset=None, master_id_list=[] , **kwargs):
        """
        Pass in a querset of content records or a list of master ids, reuturns a dictionary of master_id keys, and dictionary values {"product", "purchase_info", "price"}
        Does not support price options
        """
        if queryset:
            master_id_list = [x.master_id for x in queryset]

        if contact is not None:
            user = contact.user

        # need to match up products with activities
        products = cls.objects.filter(publish_status="PUBLISHED", content__master_id__in=master_id_list).select_related("content").prefetch_related("options","prices__required_groups", "prices__required_product_options",
            models.Prefetch("purchases", Purchase.objects.filter( models.Q(user=user) | models.Q(contact__user__username=user.username) ), to_attr="purchases_for_user")

        )

        master_product_dictionary = {}
        for product in products:
            master_product_dictionary[str(product.content.master_id)] = {
                "product":product,
                "price":product.get_price(user=user, contact=contact, option=None ),
                "purchase_info":product.get_purchase_info(user=user, purchases=product.purchases_for_user),
                "content":product.content
            }
        return master_product_dictionary

    def process_purchase(self, purchase_instance, purchase_json, *args, **kwargs):
        """
        function to write to iMIS, etc. that's specific to events
        """
        # NOTE: all products being purchased should have a proxy model for processing
        pass

    def save(self, *args, **kwargs):
        # if product type auto-set product type based on content type
        if self.product_type is None or self.product_type == "":
            if self.content.content_type == "EVENT":
                if self.content.event.event_type == "ACTIVITY":
                    self.product_type = "ACTIVITY_TICKET"
                else:
                    self.product_type = "EVENT_REGISTRATION"
            else:
                self.product_type = "PRODUCT"
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        purchases = self.purchases.all()
        if not purchases:
            super().delete(*args, **kwargs)
        else:
            raise ValidationError("Cannot delete Products that have at least one Purchase")

    def __str__(self):
       return str(self.code)  #"QTY. AVAIL: " + str(self.get_purchase_info().get("user_allowed_to_purchase"))
