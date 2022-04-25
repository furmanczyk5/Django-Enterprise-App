import datetime

from django.db import models
from django.utils import timezone

from component_sites.sites_config import COMPONENT_SITES
from content.models import Content, BaseAddress, ContentManager, TagType, \
    ContentTagType

from content.utils import generate_filter_model_manager

from places.models import CENSUS_REGION_STATE
from myapa.models.contact_role import ContactRole

JOB_TYPES = (
    ("INTERN", "Internship"),
    ("ENTRY_LEVEL", "Entry-level job - 4 weeks online"),
    ("PROFESSIONAL_2_WEEKS", "Professional job - 2 weeks online"),
    ("PROFESSIONAL_4_WEEKS", "Professional job - 4 weeks online"),
    ("PROFESSIONAL_4_WEEKS_100", "Professional (various levels of experience) - 4 weeks online"),
    ("PROFESSIONAL_4_WEEKS_75", "Professional (various levels of experience) - 4 weeks online"),
    ("PROFESSIONAL_4_WEEKS_50", "Professional (various levels of experience) - 4 weeks online"),
    ("PROFESSIONAL_4_WEEKS_25", "Professional (various levels of experience) - 4 weeks online"),
    ("PROFESSIONAL_4_WEEKS_0", "Professional (various levels of experience) - 4 weeks online"),
    ("PROFESSIONAL_2_WEEKS_75", "Professional (various levels of experience) - 2 weeks online"),
    ("PROFESSIONAL_2_WEEKS_50", "Professional (various levels of experience) - 2 weeks online"),
    ("PROFESSIONAL_2_WEEKS_25", "Professional (various levels of experience) - 2 weeks online"),
    ("PROFESSIONAL_2_WEEKS_0", "Professional (various levels of experience) - 2 weeks online"),
    ("ENTRY_LEVEL_50", "Entry Level only (zero to one year of experience; not AICP) - 4 weeks online"),
    ("ENTRY_LEVEL_25", "Entry Level only (zero to one year of experience; not AICP) - 4 weeks online"),
    ("ENTRY_LEVEL_0", "Entry Level only (zero to one year of experience; not AICP) - 4 weeks online"),
    ("INTERN_25", "Internship only (temporary position; no experience required) - 4 weeks online"),
    ("INTERN_0", "Internship only (temporary position; no experience required) - 4 weeks online"),
    ("FEATURED_2_WEEKS", "Featured job - 2 weeks online"),
)

ENTRY_LEVEL_JOB_TYPES = (
    "INTERN",
    "ENTRY_LEVEL",
    "ENTRY_LEVEL_50",
    "ENTRY_LEVEL_25",
    "ENTRY_LEVEL_0",
    "INTERN_25",
    "INTERN_0",
)

JOBS_DEFAULT_PARENT_LANDING_MASTER = 9022686


class Job(Content, BaseAddress):
    job_type = models.CharField(max_length=50, choices=JOB_TYPES, default="PROFESSIONAL_4_WEEKS")
    display_contact_info = models.BooleanField(default=False)

    salary_range = models.CharField(max_length=50, blank=True, null=True)
    company = models.CharField(max_length=80, blank=True, null=True)
    post_time = models.DateTimeField(blank=True, null=True)
    # should jobs instead be linked to actual company contacts/records (instead of these fields below)?
    contact_us_first_name = models.CharField(max_length=20, blank=True, null=True)
    contact_us_last_name = models.CharField(max_length=30, blank=True, null=True)
    contact_us_email = models.CharField(max_length=100, blank=True, null=True)
    contact_us_phone = models.CharField(max_length=20, blank=True, null=True)
    contact_us_user_address_num = models.IntegerField(blank=True, null=True)
    contact_us_address1 = models.CharField(max_length=40, blank=True, null=True)
    contact_us_address2 = models.CharField(max_length=40, blank=True, null=True)
    contact_us_city = models.CharField(max_length=40, blank=True, null=True)
    contact_us_state = models.CharField(max_length=15, blank=True, null=True)
    contact_us_zip_code = models.CharField(max_length=10, blank=True, null=True)
    contact_us_country = models.CharField(max_length=100, blank=True, null=True)
    legacy_id = models.IntegerField(null=True, blank=True)  # TO DO: remove?

    objects = generate_filter_model_manager(ParentManager=ContentManager, content_type="JOB")()

    # FLAGGED FOR REFACTORING: FEATURED JOBS
    # URL FIELDS
    # company_url = models.URLField(max_length=255, blank=True, null=True)
    linkedin_url = models.URLField(max_length=255, blank=True, null=True)
    facebook_url = models.URLField(max_length=255, blank=True, null=True)
    twitter_url = models.URLField(max_length=255, blank=True, null=True)
    instagram_url = models.URLField(max_length=255, blank=True, null=True)
    youtube_url = models.URLField(max_length=255, blank=True, null=True)


    def save(self, *args, **kwargs):
        self.content_type = 'JOB'
        if not self.parent_landing_master_id:  # setting default parent_landing_master
            self.parent_landing_master_id = JOBS_DEFAULT_PARENT_LANDING_MASTER
        super().save(*args, **kwargs)

    def ad_publish(self):
        """
        creates a draft copy / changes the status to Active so that staff can verify job updates before publishing
        NOTE: ad_publish is only called when the customer purchases the submission
        """

        self.status = "A"
        published_draft = self.publish(publish_type="DRAFT")

        if self.master.content_live:
            self.master.content_live.status = "P"
            self.master.content_live.save()

        published_draft.workflow_status = 'IS_PUBLISHED'
        published_obj = published_draft.publish() # next publish to published
        latest_job = Job.objects.filter(id=published_obj.id).first()
        if latest_job:
            pub_status = latest_job.solr_publish()
        else:
            pub_status = 0
        return pub_status


    def publish(self, replace=(None, None), publish_type="PUBLISHED", database_alias="default"):
        if not self.make_inactive_time and self.status == "A":
            if self.job_type in ("PROFESSIONAL_2_WEEKS", "PROFESSIONAL_2_WEEKS_75",
                                 "PROFESSIONAL_2_WEEKS_50", "PROFESSIONAL_2_WEEKS_0"):
                self.make_inactive_time = timezone.now() + datetime.timedelta(days=14)
            else:
                self.make_inactive_time = timezone.now() + datetime.timedelta(days=28)
        self.save()

        return_value = super().publish(replace, publish_type, database_alias)

        if publish_type == "PUBLISHED" and self.status == "A":
            type(self).objects.using(database_alias).filter(post_time__isnull=True, publish_uuid=self.publish_uuid)\
                .update(post_time=timezone.now())

        return return_value

    def solr_format(self):
        formatted_content = super().solr_format()
        formatted_content_additional = {
            "company": self.company,
            "address_city": self.city,
            "address_state": self.state,
            "address_country": self.country,
            "begin_time": self.post_time,
            "end_time": self.make_inactive_time,
            "sort_time": self.post_time,
            # FLAGGED FOR REFACTORING: FEATURED JOBS
            "job_type": self.job_type,
            # thumbnail, thumbnail_2, featured_image already published to solr (if we use a preexisting for logo)
        }
        formatted_content.update(formatted_content_additional)
        return formatted_content

    def get_two_crumb_breadcrumb(self):
        provider_roles = ContactRole.objects.filter(content=self, role_type="PROVIDER")
        CHAPTER_PROVIDERS = set([v["username"] for v in COMPONENT_SITES.values()])
        if '119523' in CHAPTER_PROVIDERS:
            CHAPTER_PROVIDERS.remove('119523')
        if not provider_roles:
            # WITHOUT THIS ASSIGNMENT THE METHOD RETURNS NONE (instead of empty list)?!
            val = super().get_two_crumb_breadcrumb()
            return val
            # return super().get_two_crumb_breadcrumb()
        elif provider_roles:
            if not [pr for pr in provider_roles if pr.contact.user.username in CHAPTER_PROVIDERS]:
                # WITHOUT THIS ASSIGNMENT THE METHOD RETURNS NONE (instead of empty list)?!
                val = super().get_two_crumb_breadcrumb()
                return val
                # return super().get_two_crumb_breadcrumb()
            else:
                print("there's a chapt provider")
                return []
                # WTF?
                # raise UserWarning("Please do not edit/publish Chapter Jobs in Django.")

    def census_region_tag_save(self):
        """
        assigns and saves census region tag based on the state field
        """
        # updating contenttagtype records based off of taxo master topics

        if self.state or (self.country and self.country != "United States"):
            census_region_tagtype = TagType.objects.prefetch_related("tags").get(code="CENSUS_REGION")
            contenttagtype, is_created = ContentTagType.objects.get_or_create(content=self,
                                                                              tag_type=census_region_tagtype)
            region_code = next((r[0] for r in CENSUS_REGION_STATE if self.state in r[1]), "INTERNATIONAL")
            contenttagtype.tags = [tag for tag in census_region_tagtype.tags.all() if tag.code == region_code]
            contenttagtype.save()
        else:
            ContentTagType.objects.filter(content=self, tag_type__code="CENSUS_REGION").delete()

        return self

    def editable(self):
        return self.status in ['A', 'P', 'N']


    @staticmethod
    def purchase_info_function(purchase):
        """
        Function to return a dict that conforms with
        :obj:`imis.event_function.EventFunction`,
        for use in
        :meth:`store.models.purchase.Purchase.cart_items`
        :return: dict
        """
        return {
            'product_sale_status': 'Regular',
            'regular_remaining': purchase.quantity + 1  # Buy as many as you'd like!
        }


class WagtailJobManager(models.Manager):
    def get_queryset(self):
        return super(WagtailJobManager, self).get_queryset().exclude(contactrole__contact__user_id=115054)


class WagtailJob(Job):
    objects = WagtailJobManager()

    class Meta:
        proxy = True
        verbose_name = "Wagtail Job"
