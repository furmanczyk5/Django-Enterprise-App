from urllib.parse import urlencode

from django.db import models
from sentry_sdk import capture_exception

from content.mail import Mail
from store.utils.prevent_delete_purchases_queryset import PreventDeletePurchasesQuerySet
from store.models.product import Product


class ProductResearchInquiryManager(models.Manager):
    """
    manager for querying research inquiries
    """
    def get_queryset(self):
        return super().get_queryset().filter(product_type="RESEARCH_INQUIRY")


class ProductResearchInquiry(Product):
    """
    Research inquiry product proxy class
    """
    objects = ProductResearchInquiryManager.from_queryset(PreventDeletePurchasesQuerySet)()

    def process_purchase(self, purchase_instance, purchase_json, *args, **kwargs):
        """
        function to write to iMIS, etc. that's specific to events
        """
        try:
            purchase_instance.contact_recipient = purchase_instance.contact.company_fk
            purchase_instance.save()
            
            search_url = ''
            if getattr(purchase_instance.contact, 'company'):
                search_url += "https://www.planning.org/admin/research_inquiries/inquiry/?"
                search_url += urlencode({"q": purchase_instance.contact.company})
            mail_context = {
                'purchase': purchase_instance,
                'search_url': search_url,
                }
            Mail.send('RESEARCH_INQUIRY_ORDER', '', mail_context)
        except Exception as e:
            capture_exception(e)

        # TO DO... add contact_recipient to purchase_instance for the currently logged-in user's organization
            
    class Meta:
        proxy = True
