import datetime

import pytz
from django.db import models
from django.utils import timezone

from content.models import Content, BaseAddress, ContentManager, TagType, ContentTagType
from content.utils import force_utc_datetime, generate_filter_model_manager
from myapa.models.proxies import Organization
from myapa.models.constants import DjangoOrganizationTypes, DjangoContactTypes
from places.models import CENSUS_REGION_STATE

RFP_TYPES = (
    ("RFP", "RFP"),
    ("RFQ", "RFQ"),
)


class Consultant(Organization):
    """
    TODO: Consider consolidating this in myapa? It's a proxy model of a Contact proxy model...
    Proxy model for all consultant organizations in the database (whether paying for listing service or not).
    """
    class_query_args = {
        "contact_type": DjangoContactTypes.ORGANIZATION.value,
        "organization_type": DjangoOrganizationTypes.PR005.value
    }

    def solr_format(self):
        profile = self.organizationprofile

        formatted_content = super().solr_format()

        additional_content = {
            "sort_time": force_utc_datetime(profile.consultant_listing_until),
            "archive_time": force_utc_datetime(profile.consultant_listing_until),
        }
        formatted_content.update(additional_content)

        return formatted_content

    class Meta:
        proxy = True


class ConsultantListingManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            organizationprofile__consultant_listing_until__gt=timezone.now()
        )


class ConsultantListing(Consultant):
    """
    Proxy model for subset of consultant organizations who have paid for listing service.
    """
    prevent_auto_class_assignment = True
    objects = ConsultantListingManager()


class BranchOffice(BaseAddress):
    """
    Model for consultant branch offices
    """
    # for branch offices of Consultant Organizations
    parent_organization = models.ForeignKey(
        'Consultant',
        verbose_name="main office",
        related_name="branchoffices",
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )
    email = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    cell_phone = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Branch Office"
        verbose_name_plural = "Branch Offices"


class RFP(Content, BaseAddress):
    """
    Model for RFP/RFQ posts. Used for RFP submissions as well
    Notes:
        The poster is related to the RFP/RFQ through the ContactRole model with role type of "PROVIDER"
    Questions:
        Do we want a format tag for rfp/rfq?
        Do we want special rules for the archive time? Currently 14 days after deadline
    """
    rfp_type = models.CharField("RFP or RFQ", max_length=50, choices=RFP_TYPES)
    deadline = models.DateField(blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    website = models.URLField(max_length=255, blank=True, null=True)
    company = models.CharField(max_length=80, blank=True, null=True)

    objects = generate_filter_model_manager(ParentManager=ContentManager, content_type="RFP")()

    default_template = "consultants/newtheme/rfp/details.html"

    def solr_format(self):
        formatted_content = super().solr_format()
        formatted_content_additional = {
            "content_type": self.rfp_type or self.content_type,
        # In Solr RFP and RFQ will have different content_type (unless we want to add a field), In django, both will have content_type = "RFP"
            "end_time": self.deadline,
            "address_city": self.city,
            "address_state": self.state,
            "address_country": self.country,
            "resource_url": self.website,
            "company": self.company,
            "sort_time": self.submission_time,
        }
        formatted_content.update(formatted_content_additional);
        return formatted_content

    def deadline_chicago(self):
        """
        returns the deadline_time to have with chicago timezone, but does not
        change the time (e.g. 12:00 utc -> 12:00 chicago, and not 12:00 utc -> 7:00 chicago)
        ...UNTIL WE IMPLEMENT TIMEZONES...
        """
        return pytz.timezone("America/Chicago").localize(
            self.deadline_time.replace(tzinfo=None)) if self.deadline_time else None

    def deadline_is_past(self):
        now_chicago = datetime.datetime.now(pytz.timezone("America/Chicago"))
        return self.deadline is None or now_chicago < self.deadline_chicago()

    def save(self, *args, **kwargs):
        self.content_type = 'RFP'
        self.archive_time = self.archive_time or (self.deadline + datetime.timedelta(
            days=1) if self.deadline else None)  # default archive time is 14 days after the deadline
        super().save(*args, **kwargs)

    def census_region_tag_save(self):
        """
        assigns and saves census region tag based on the state field
        """
        # updating contenttagtype records based off of taxo master topics

        if self.state or (self.country and self.country != "United States"):
            census_region_tagtype = TagType.objects.prefetch_related("tags").get(code="CENSUS_REGION")
            contenttagtype, _ = ContentTagType.objects.get_or_create(
                content=self,
                tag_type=census_region_tagtype
            )
            region_code = next((r[0] for r in CENSUS_REGION_STATE if self.state in r[1]), "INTERNATIONAL")
            contenttagtype.tags = [tag for tag in census_region_tagtype.tags.all()
                                   if tag.code == region_code]
            contenttagtype.save()
        else:
            ContentTagType.objects.filter(content=self, tag_type__code="CENSUS_REGION").delete()

        return self

    class Meta:
        verbose_name = "RFP or RFQ"
        verbose_name_plural = "RFPs and RFQs"
