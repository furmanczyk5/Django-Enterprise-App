from django.db import models

from myapa.models.contact import Contact


class GroupLicense(models.Model):
    """
    Represents a single group license code allowing some user to enroll in a course, including redemption status.
    """
    purchase = models.ForeignKey("store.Purchase", related_name="learn_group_licenses", on_delete=models.PROTECT)
    license_code = models.CharField(max_length=100, blank=True, null=True)
    redemption_date = models.DateTimeField(null=True, blank=True)
    redemption_contact = models.ForeignKey(Contact, related_name="learn_group_licenses", null=True, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
