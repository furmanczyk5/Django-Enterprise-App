from django.db import models
from django.contrib.auth.models import Group
from content.models import BaseContent
from myapa.models.contact import Contact
from store.models import Product


class Directory(BaseContent):
    subscription_product = models.ForeignKey(
        Product,
        related_name="directories",
        on_delete=models.CASCADE
    )
    permission_groups = models.ManyToManyField(
        Group,
        blank=True,
        null=True,
        help_text="Permission groups for those able to view the directory"
    )
    committees = models.CharField(
        max_length=1000,
        null=True,
        blank=True,
        help_text="Committee codes to include in the directory. Separate multiple values by commas, without spaces."
    )
    directory_group = models.ForeignKey(
        Group,
        related_name="included_in_directories",
        blank=True,
        null=True,
        help_text="Permission group for those to be INCLUDED in the directory (may be depreciated)",
        on_delete=models.SET_NULL
    )

    def get_contacts(self, limit=200, *args, **kwargs):
        # TO DO... update to pull different contact lists based on committee, permissions, etc.
        contacts = Contact.objects

        # TO DO... add ability to pull based on subscription product
        # if self.subscription_product:
        #     contacts = contacts.filter( ... )

        if self.directory_group:
            contacts = contacts.filter(user__groups__name=self.directory_group.name).order_by("last_name")

        if self.committees:
            committee_codes = self.committees.split(",")

            # TO DO... this queries ALL committees for a given contact (not just the applicable one)... why?
            contacts = contacts.filter(committees__code__in=committee_codes).prefetch_related("committees").order_by("committees__rank", "last_name")


        contacts = contacts[:limit]
        return contacts

    class Meta:
        verbose_name_plural = "Directories"
