import datetime

from django.db import models
from django.utils import timezone

from cm.enums.applications import ProviderApplicationStatus, ProviderApplicationReviewStatus
from content.mail import Mail
from content.models import STATUSES
from myapa.models.contact_relationship import ContactRelationship
from myapa.models.contact_role import ContactRole
from myapa.models.proxies import Organization
from store.models import Purchase, Order

OBJECTIVES_STATUSES = (
    ("ALWAYS", "Always"),
    ("SOMETIMES", "Sometimes"),
    ("NEVER", "Never")
)

PROVIDER_APPLICATION_STATUSES = (
    ('A', 'Approved'),
    ('D', 'Deferred'),
    ('S', 'Submitted'),
    ('I', 'Incomplete'))

PROVIDER_APPLICATION_REVIEW_STATUSES = (
    ('DUE', 'Due for Review'),
    ('REVIEWING', 'Under Review'),
    ('COMPLETE', 'Review Complete'),
    ('LOCKED', 'Coaching') # For locking providers from doing anything
)

PROVIDER_REGISTRATION_TYPES = ( # NOTE: maybe these should tie directly to product codes (or price rule codes?) to help with the checkout process?
    ("CM_PER_CREDIT", "Per-Credit"),

    ("CM_UNLIMITED_1", "Annual Unlimited - Government and University Rate : $1,995 + $95 registration fee"), #legacy 2008-2015 annual reg type... will eventually remove at some TBD date
    ("CM_UNLIMITED_INHOUSE", "In House Annual Unlimited (for employee training only) : $475 + $95 registration fee"), #legacy 2008-2015 annual reg type... will eventually remove at some TBD date
    ("CM_UNLIMITED_NONPROFIT_1", "Annual Unlimited (nonprofit, less than $500,000) : $945 + $95 registration fee"), #legacy 2008-2015 annual reg type... will eventually remove at some TBD date
    ("CM_UNLIMITED_NONPROFIT_2", "Annual Unlimited (nonprofit, $500,000 to $5M) : $1,995 + $95 registration fee"), #legacy 2008-2015 annual reg type... will eventually remove at some TBD date
    ("CM_UNLIMITED_NONPROFIT_3", "Annual Unlimited (nonprofit, $5M to 15M) : $2,995 + $95 registration fee"), #legacy 2008-2015 annual reg type... will eventually remove at some TBD date
    ("CM_UNLIMITED_NONPROFIT_4", "Annual Unlimited (nonprofit, over $15M) : $5,145 + $95 registration fee"), #legacy 2008-2015 annual reg type... will eventually remove at some TBD date

    ("CM_UNLIMITED_PARTNER", "Unlimited registration through partner organization : $95"),
    ("CM_UNLIMITED_SMALL","For-Profit and Not-for-Profit Providers with gross revenue < $500K : $1,254"),
    ("CM_UNLIMITED_MEDIUM","Universities and  Governments - For-Profit and Not-for-Profit Providers with gross revenue $500K−$5M : $2,461 "),
    ("CM_UNLIMITED_LARGE","For-Profit and Not-for-Profit Providers with gross revenue $5M−$15M : $3,611 "),
    ("CM_UNLIMITED_LARGEST","For-Profit and Not-for-Profit Providers with gross revenue > $15M : $6,084 "),
    # ... TO DO... more statuses needed here
)

PROVIDER_APPLICATION_YEAR = 2022 # the year for which applications are being submitted/reviewed (starts a few months early)


def supporting_document_file_path(instance, filename):
    return "uploads/provider/{0}/{1}/{2}".format(instance.provider.user.username, instance.id, filename)


class ProviderApplication(models.Model):
    """
    stores applications that CM providers submit each year in order to become
    approved providers.
    """
    status = models.CharField(max_length=50, choices=PROVIDER_APPLICATION_STATUSES, default="S")
    provider = models.ForeignKey("myapa.contact", related_name="applications", on_delete=models.CASCADE)
    year = models.IntegerField(default=None) # this may not be needed... since we're using begin_date and end_date
    begin_date = models.DateField("Approval window begin", blank=True, null=True)
    end_date = models.DateField("Approval window end", blank=True, null=True)
    explain_topics = models.TextField(blank=True, null=True)
    objectives_status = models.CharField(max_length=50, choices=OBJECTIVES_STATUSES, blank=True, null=True)
    objectives_example_1 = models.TextField(blank=True, null=True)
    objectives_example_2 = models.TextField(blank=True, null=True)
    objectives_example_3 = models.TextField(blank=True, null=True)
    how_determines_speakers = models.TextField(blank=True, null=True)
    evaluates_activities = models.BooleanField(default=False)
    evaluation_procedures = models.TextField(blank=True, null=True)
    agree_keep_records = models.BooleanField(default=False)
    submitted_time = models.DateTimeField("Submitted date", editable=False, blank=True, null=True)

    review_status = models.CharField(
        max_length=50,
        choices=PROVIDER_APPLICATION_REVIEW_STATUSES,
        blank=True,
        null=True,
        default=None
    )
    review_notes = models.TextField(blank=True, null=True)
    review_notification_time = models.DateTimeField(null=True, blank=True) # datetime for when provider was notified about review period

    provider_notes = models.TextField("Notes to Provider", blank=True, null=True)

    supporting_upload_1 = models.FileField(upload_to=supporting_document_file_path, null=True, blank=True, max_length=255)
    supporting_upload_2 = models.FileField(upload_to=supporting_document_file_path, null=True, blank=True, max_length=255)
    supporting_upload_3 = models.FileField(upload_to=supporting_document_file_path, null=True, blank=True, max_length=255)

    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    def send_status_update_email(self):
        email_template = None
        if self.review_status:
            email_template = "CM_PROVIDER_PERIODIC_REVIEW_STATUS_CHANGE"
        elif self.status == ProviderApplicationStatus.APPROVED.value:
            email_template = "CM_PROVIDER_APPLICATION_APPROVED"
        elif self.status == ProviderApplicationStatus.DEFERRED.value:
            email_template = "CM_PROVIDER_APPLICATION_DEFERRED"

        if email_template:
            mail_context = dict(
                app=self,
                provider=self.provider,
                application_status=next(pas[1] for pas in PROVIDER_APPLICATION_STATUSES if pas[0] == self.status))

            for admininistrator in self.provider.get_admin_contacts():
                mail_context["admin"] = admininistrator
                Mail.send(email_template, admininistrator.email, mail_context)

    def save(self, **kwargs):
        if not self.year:
            self.year = PROVIDER_APPLICATION_YEAR
        super().save()

    @property
    def status_userfriendly(self):
        return next((s[1] for s in PROVIDER_APPLICATION_STATUSES if s[0] == self.status), "")

    def __str__(self):
        return str(self.year) # TO DO... more here


class ProviderRegistration(models.Model):
    """
    stores annual registrations that providers can purchase for each calendar year
    """
    status = models.CharField(max_length=50, choices=STATUSES, default="N")
    is_unlimited = models.BooleanField(default=False)
    registration_type = models.CharField(
        max_length=50,
        choices=PROVIDER_REGISTRATION_TYPES,
        default="CM_PER_CREDIT"
    )
    provider = models.ForeignKey("myapa.contact", related_name="registrations", on_delete=models.CASCADE)
    shared_from_partner_registration = models.ForeignKey(
        "self",
        related_name="shared_to_partner_registration",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    year = models.IntegerField(default=None)
    # TO DO... maybe this should be one-to-one, foriegn key
    purchase = models.ForeignKey(
        Purchase,
        null=True,
        blank=True,
        related_name="provider_registration",
        on_delete=models.SET_NULL
    )

    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.year) + " | " + self.registration_type


class ProviderManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(contact_type="ORGANIZATION", applications__isnull=False).distinct() # CHANGE THIS LATER WHEN WE ACTUALLY HAVE SOMETHING


# TO DO: maybe better to inherit from CompanyContact here?
class Provider(Organization):
    prevent_auto_class_assignment = True

    objects = ProviderManager()

    def start_periodic_review(self, with_email=False):

        review_application = ProviderApplication.objects.filter(
            provider=self,
            review_status__in=[
                ProviderApplicationReviewStatus.DUE.value,
                ProviderApplicationReviewStatus.REVIEWING.value
            ]
        ).first()

        if not review_application:
            review_application = ProviderApplication(
                provider=self,
                year=timezone.now().year
            )

        review_application.review_status = ProviderApplicationReviewStatus.DUE.value
        review_application.status = ProviderApplicationStatus.INCOMPLETE.value

        if with_email:
            # send email notification to all admins

            provider_admins = self.get_admin_contacts()

            mail_context = {
                "provider": self,
                "approved_thru": self.application_approved_through_date
            }

            for provider_admin in provider_admins:
                mail_context["admin"] = provider_admin
                Mail.send('PROVIDER_PERIODIC_REVIEW_NOTIFICATION', provider_admin.email, mail_context)

            # notification time is the first time admins were notified of review
            review_application.review_notification_time = review_application.review_notification_time or timezone.now()

        review_application.save()

    @staticmethod
    def get_ein_query(ein_number):
        if not isinstance(ein_number, str):
            return []
        ein_query = [ein_number, ein_number.replace('-', '')]
        if '-' not in ein_number:
            ein_query.append('{}-{}'.format(ein_number[:2], ein_number[2:]))
        return ein_query

    def partner_providers(self):
        if self.ein_number:
            ein_query = self.get_ein_query(self.ein_number)
            return Provider.objects.filter(ein_number__in=ein_query).exclude(id=self.id)

    def partner_registration_eligible(self):
        """
        If this org is linked to another org (by ein_number) and if that linked org
        has an active, valid unlimited registration, this org can purchase the
        reduced-rate partner unlimited registration
        :return: bool
        """
        partners = self.partner_providers()
        if not partners:
            return False
        return any(x.has_unlimited_applicationyear_registration() for x in partners)

    def has_approved_application(self):
        """ returns true if the provider has ANY approved application """
        return self.applications.filter(status="A").exists()

    def submitted_applicationyear(self):
        """ returns true if the provider is registered for the the current year"""
        return self.applications.filter(end_date__gte=datetime.date(PROVIDER_APPLICATION_YEAR,1,1) ).exists()

    def get_application_in_progress(self):
        """
        returns the providers application that is not aproved
            there should only ever be one of these
        """
        return next((a for a in self.applications.all() if a.status in ["D", "S", "I"]), None)

    def get_latest_approved_application(self):
        """ returns the provider's approved application with the latest end_date"""
        approved_applications = sorted([a for a in self.applications.all() if a.status == "A" and a.end_date], key=lambda x: (x.end_date, x.id), reverse=True)
        return next((ap for ap in approved_applications), None)

    def application_approved_through_date(self):
        """ returns the latest end_date YEAR for this provider's approved applicatons """
        approved_application = self.get_latest_approved_application()
        return approved_application.end_date if approved_application else None

    def application_approved_through_year(self):
        """ returns the latest end_date YEAR for this provider's approved applicatons """
        enddate = self.application_approved_through_date()
        return enddate.year if enddate else None

    def available_registration_years(self):
        """ Returns the years that are still available for this provider to register as unlimited """
        applications = [a.end_date.year for a in self.applications.all()
                        if a.status == "A" and a.end_date]
        if applications:
            latest_application_year = max(applications)
            purchased_registration_years = [
                r.year for r in self.registrations.all()
                if (r.status in ["A", "P"] and r.is_unlimited)
            ]
            return [
                y for y in [PROVIDER_APPLICATION_YEAR - 1, PROVIDER_APPLICATION_YEAR]
                if y <= latest_application_year and y not in purchased_registration_years
            ]
        return []

    def has_unlimited_prior_applicationyear_registration(self):
        """ returns the True if provider has registered for the PREVIOUS application year"""
        return next((True for r in self.registrations.all() if r.year == (PROVIDER_APPLICATION_YEAR - 1) and r.is_unlimited ), False)

    def has_unlimited_applicationyear_registration(self):
        """ returns the True if provider has registered for the CURRENT application year"""
        return next((True for r in self.registrations.all() if r.year == PROVIDER_APPLICATION_YEAR and r.is_unlimited), False)

    def get_rating_stats(self):
        roles = ContactRole.objects.filter(
            contact=self,
            role_type="PROVIDER",
            content__rating_count__isnull=False
        ).values(
            "content__rating_average", "content__rating_count"
        )

        sum_of_products = 0.00
        total_ratings = 0

        for role in roles:
            sum_of_products += float(role["content__rating_average"] or 0.00) * role["content__rating_count"]
            total_ratings += role["content__rating_count"]
        return {
            "rating_avg": sum_of_products/(total_ratings or 1),
            "rating_count": total_ratings
        }

    @classmethod
    def get_by_username(cls, username):

        provider_relationships = ContactRelationship.objects.select_related("source").filter(target__user__username=username, relationship_type='ADMINISTRATOR') # All of user's provider relationships

        # TO DO... try to prevent another query here
        return cls.objects.filter(id=provider_relationships.first().source.id).first()

    class Meta:
        verbose_name = "CM Provider"
        proxy = True

    def __str__(self):
        if getattr(self, 'user', None) is not None:
            return '<Provider: {} | {}>'.format(self.user.username, self.company)
        else:
            return ''


class CMOrderManager(models.Manager):
    def get_queryset(self):
        # TO DO... may be better to query by product type code instead of product code...
        # .select_related("purchase_set")
        return super().get_queryset().filter(purchase__product__code__in=["PRODUCT_CM_PER_CREDIT","CM_PROVIDER_REGISTRATION","CM_PROVIDER_BUNDLE100_2015","CM_PROVIDER_BUNDLE50_2015","CM_PROVIDER_DISTANCE_2015","PRODUCT_CM_PER_CREDIT_2015","CM_PROVIDER_REGISTRATION_2015","CM_PROVIDER_ANNUAL_2015","CM_PROVIDER_DAY_2015","CM_PROVIDER_WEEK_2015","CM_PROVIDER_MISC","PRODUCT_CM_PER_CREDIT"]).distinct()


class CMOrder(Order):
    objects = CMOrderManager()

    class Meta:
        verbose_name = "CM Order"
        proxy = True
