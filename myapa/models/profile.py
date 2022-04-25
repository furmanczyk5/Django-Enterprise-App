from django.db import models
from django.urls import reverse
from sentry_sdk import capture_message

from myapa.models.constants import SHARE_CHOICES, DjangoOrganizationTypes
from myapa.models.contact import Contact
from uploads.models import ImageUpload, DocumentUpload


class Profile(models.Model):
    # TODO... eventually it would make sense to move more of the My APA profile fields to this model (or the
    # Individual/Oganization inherited models if specific to an individual or organization)
    contact = models.OneToOneField(Contact, on_delete=models.CASCADE)
    image = models.ForeignKey(ImageUpload, null=True, blank=True, on_delete=models.SET_NULL)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class IndividualProfile(Profile):
    image = models.ForeignKey(
        ImageUpload,
        null=True,
        blank=True,
        related_name="individual_profile",
        on_delete=models.SET_NULL
    )
    resume = models.ForeignKey(DocumentUpload, null=True, blank=True, on_delete=models.SET_NULL)
    slug = models.SlugField(blank=True, null=True)
    statement = models.TextField(blank=True, null=True, help_text="FAICP induction statement")
    experience = models.TextField(blank=True, null=True, help_text="ASC Experience")

    # determines whether profile as a whole is shared... if share profile is PRIVATE, then the profile is not shared at all,
    # regardless of the other share fields below
    share_profile = models.CharField(
        max_length=50,
        choices=SHARE_CHOICES,
        default="MEMBER",
        help_text="""If you choose “Private,” your profile is not included in the APA Member Directory.
                Only you may view your profile, even if someone else knows your profile’s URL.
                <br/><br/>
                If you choose “Visible only to other members,” your profile is included in the APA Member Directory,
                which is accessible only to APA members. Any APA member may view your profile by searching the APA member
                directory or by using your profile’s URL.
                <br/><br/>
                If you choose “Public,” your profile is included in the APA Member Directory.
                Additionally, anyone who has your profile’s URL - APA member or not - may view your profile."""
    )

    share_contact = models.CharField(max_length=50, choices=SHARE_CHOICES, default="MEMBER")
    share_bio = models.CharField(max_length=50, choices=SHARE_CHOICES, default="MEMBER")
    share_social = models.CharField(max_length=50, choices=SHARE_CHOICES, default="MEMBER")
    share_leadership = models.CharField(max_length=50, choices=SHARE_CHOICES, default="MEMBER")
    share_education = models.CharField(max_length=50, choices=SHARE_CHOICES, default="MEMBER")
    share_jobs = models.CharField(max_length=50, choices=SHARE_CHOICES, default="MEMBER")
    share_events = models.CharField(max_length=50, choices=SHARE_CHOICES, default="MEMBER")
    share_resume = models.CharField(max_length=50, choices=SHARE_CHOICES, default="MEMBER")
    share_conference = models.CharField(max_length=50, choices=SHARE_CHOICES, default="MEMBER")
    share_advocacy = models.CharField(max_length=50, choices=SHARE_CHOICES, default="MEMBER")

    speaker_opt_out = models.BooleanField(default=False)

    def get_profile_url(self):
        if self.slug:
            return reverse("public_profile", kwargs=dict(slug=self.slug))
        else:
            return None

    def get_thumbnail_url(self):
        try:
            return self.image.image_thumbnail.url
        except:
            # sometimes accessing this fails
            return ""

    def img_thumbnail(self):
        return u'<img style="max-height:229px" src="%s" />' % (self.get_thumbnail_url())

    img_thumbnail.short_description = 'Profile Image'
    img_thumbnail.allow_tags = True

    def __str__(self):
        return self.slug or "PROFILE"


class OrganizationProfile(Profile):
    principals = models.CharField(max_length=1000, null=True, blank=True)
    number_of_staff = models.IntegerField(null=True, blank=True)
    number_of_planners = models.IntegerField(null=True, blank=True)

    number_of_aicp_members = models.IntegerField(null=True, blank=True)
    date_founded = models.DateField(null=True, blank=True)
    consultant_listing_until = models.DateTimeField(null=True, blank=True)
    research_inquiry_hours = models.IntegerField(
        help_text="Total inquiry hours purchased",
        null=True,
        blank=True
    )
    employer_bio = models.TextField(null=True, blank=True)

    def set_consultant_listing_until(self):
        """
        If this a :class:`consultants.models.Consultant`, get or create its
        :class:`myapa.models.profile.OrganizationProfile` and update its
        consultant_listing_until value.
        :return: None
        """
        if self.contact.organization_type != DjangoOrganizationTypes.PR005.value:
            raise AttributeError(
                "This method should only be called on a Organization with a "
                "contact.organization_type of PR005; this Organization's "
                "contact.organization_type is {}".format(self.contact.organization_type)
            )

        last_paid_thru = self.contact.get_imis_subscriptions(
            product_code="CSCC"
        ).order_by(
            '-paid_thru'
        ).first()

        if last_paid_thru is not None:
            self.consultant_listing_until = last_paid_thru.paid_thru
            self.save()
        else:
            capture_message(
                "No Subscriptions found in iMIS for Consultant {}".format(self.contact),
                level='warning'
            )

    def img_thumbnail(self):
        return u'<img style="max-height:229px" src="%s" />' % self.image.image_thumbnail.url

    img_thumbnail.short_description = 'Organization Profile Image'
    img_thumbnail.allow_tags = True
