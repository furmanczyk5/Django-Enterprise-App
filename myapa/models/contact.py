import datetime
import logging
import re
from calendar import monthrange

import pytz
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import connections, models
from django.utils import timezone
from django.utils.text import Truncator

from content.models import BaseContent, BaseAddress, Content
from content.solr_search import SolrUpdate
from imis.utils import sql as imis_sql
from myapa.models.constants import (
    CONTACT_TYPES, CHAPTER_CHOICES, ADDRESS_TYPES, SALARY_CHOICES_ALL,
    ORGANIZATION_TYPES, PAS_TYPES, COUNTRY_CATEGORY_CODES, DjangoContactTypes
)
from myapa.models.imis_sync_mixin import ImisSyncMixin
from myapa.permissions import conditions

logger = logging.getLogger(__name__)


class Contact(BaseContent, BaseAddress, ImisSyncMixin):
    """
    people or orgs (for the purposes of future my apa info and for connecting them
    with content as authors, publishers, organizers, reviewers, etc.)
    """

    # The number of months after lapsing a member is still allowed to renew with their current account
    LAPSED_MEMBERSHIP_RENEWAL_MONTHS = 3

    contact_type = models.CharField(max_length=50, choices=CONTACT_TYPES, default='INDIVIDUAL')

    # TODO... research / test what happens when contact deleted:
    # - user also auto-deleted? (assume yes, otherwise exception would be thrown)
    # - Store orders / purchases / payments deleted? (assume no, but check)?
    # - other related models?
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)

    # maybe "roles" would have been a better name for this?
    content = models.ManyToManyField(Content, through='myapa.ContactRole', related_name="contacts")

    content_added = models.ManyToManyField(
        Content,
        through='ContactContentAdded',
        related_name="contacts_who_added"
    )

    related_contacts = models.ManyToManyField(
        'self',
        through='ContactRelationship',
        related_name="related_contact_sources",
        symmetrical=False
    )

    # currently used to store the "PresenterID" of Harvester Presenter records
    external_id = models.IntegerField(null=True, blank=True)

    prefix_name = models.CharField("prefix", max_length=25, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    middle_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    suffix_name = models.CharField("suffix", max_length=10, blank=True, null=True)
    designation = models.CharField(max_length=20, blank=True, null=True)

    chapter = models.CharField(max_length=15, choices=CHAPTER_CHOICES, blank=True, null=True)
    # TODO... delete this?
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPES, blank=True, null=True)
    # note, using "job_title" here since "title" is already inherited, and refers to the
    # generic title for the object (which makes more sense as the full name or company name)

    job_title = models.CharField(max_length=80, blank=True, null=True)

    # membership info
    # TODO: Should this have its choices restricted to `imis.tests.factories.name.MEMBER_TYPES`?
    member_type = models.CharField(max_length=5, blank=True, null=True)
    salary_range = models.CharField(max_length=5, choices=SALARY_CHOICES_ALL, blank=True, null=True)

    email = models.CharField(max_length=100, blank=True, null=True, db_index=True)

    # Stored in the Ind_Demographics table in iMIS
    secondary_email = models.CharField(max_length=100, blank=True, null=True)

    phone = models.CharField("Home Phone", max_length=20, blank=True, null=True)
    secondary_phone = models.CharField("Work Phone", max_length=20, blank=True, null=True)
    cell_phone = models.CharField("Cell Phone", max_length=20, blank=True, null=True)

    birth_date = models.DateField(blank=True, null=True)

    company = models.CharField(max_length=80, blank=True, null=True)  # Company text field
    company_fk = models.ForeignKey(
        'Organization',
        verbose_name="linked organization",
        related_name="contacts",
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )  # company foreign key field

    # TODO: could this be a property instead of db column?
    company_is_apa = models.BooleanField(default=False)

    ein_number = models.CharField(max_length=15, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    about_me = models.TextField(blank=True, null=True)
    # for branch offices of Consultant Organizations
    parent_organization = models.ForeignKey(
        'Organization',
        verbose_name="parent organization",
        related_name="branchoffice",
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )

    # TO DO: move to iMIS (Name table? Check with Phil?)
    staff_teams = models.TextField(
        blank=True,
        null=True,
        help_text="""Department/team names for APA staff for granting django admin access.
        Staff may belong to multiple teams if they perform cross-departmental work that requires
        access to specific apps or pages. Enter values in CAPS,
        separated by commas WITH NO SPACES. Possible values:
        AICP,
        CAREERS,
        COMMUNICATIONS,
        COMPONENT_ADMIN,
        COMPONENT_BLACK,
        COMPONENT_CITY,
        COMPONENT_HOUSING,
        COMPONENT_PRIVATE,
        COMPONENT_TRANS,
        COMPONENT_URBAN_DES,
        COMPONENT_WOMEN,
        CONFERENCE,
        EDITOR,
        EDUCATION,
        EVENTS_EDITOR,
        KNOWLEDGEBASE_EDITOR,
        LEADERSHIP,
        MARKETING,
        MEMBERSHIP,
        PUBLICATIONS,
        RESEARCH,
        STORE_ADMIN,
        TEMP_STAFF
        """)

    # for Consultant "Firm Specializations:"
    tag_types = models.ManyToManyField('content.TagType', through="ContactTagType", blank=True)

    # change this to cm_organization type..
    organization_type = models.CharField(
        max_length=20,
        choices=ORGANIZATION_TYPES,
        blank=True,
        null=True
    )

    pas_type = models.CharField(max_length=10, choices=PAS_TYPES, blank=True, null=True)

    personal_url = models.URLField(max_length=255, blank=True, null=True)
    linkedin_url = models.URLField(max_length=255, blank=True, null=True)
    facebook_url = models.URLField(max_length=255, blank=True, null=True)
    twitter_url = models.URLField(max_length=255, blank=True, null=True)
    instagram_url = models.URLField(max_length=255, blank=True, null=True)

    def __str__(self):
        return_string = ""

        if self.user:
            return_string = str(self.user.username) + " | "
        if self.contact_type == 'INDIVIDUAL':
            return_string += str(self.first_name) + " " + str(self.last_name)
            if self.designation:
                return_string += ", " + self.designation
        else:
            return_string += str(self.company)

        return return_string

    @property
    def is_aicp(self):
        return self.get_imis_subscriptions(product_code="AICP", status='A').exists()

    @property
    def is_aicp_prorate(self):
        return self.get_imis_subscriptions(product_code="AICP_PRORATE", status='A').exists()

    @property
    def is_international(self):
        name_address = self.get_imis_name_address(preferred_mail=True).first()
        if name_address is not None:
            country = str(name_address.country).upper().strip()
            return country and country != "UNITED STATES"
        return False

    @property
    def is_new_member(self):
        name = self.get_imis_name()
        if name is not None:
            return name.category in ('NM1', 'NM2')
        return False

    @property
    def informal_name(self):
        name = self.get_imis_name()
        if name is None or name.informal is None or not name.informal.strip():
            return None
        return name.informal

    @property
    def is_new_membership_qualified(self):
        return (self.member_type in ('NOM', 'STU') or self.is_new_member) \
               and not self.is_international

    def get_country_type_code(self):
        return next(
            (country[0] for country in COUNTRY_CATEGORY_CODES if country[1] == self.country),
            "CC"
        )

    # For JotForms
    def get_standard_fields(self):
        name = self.get_imis_name()
        mailing_address = self.get_imis_name_address(preferred_mail=True).first()

        std_fields = {}
        std_fields['id'] = getattr(name,'id', None)
        std_fields['first_name'] = getattr(name, 'first_name', None)
        std_fields['last_name'] = getattr(name, 'last_name', None)
        std_fields['designation'] = getattr(name, 'designation', None)
        std_fields['email'] = getattr(name, 'email', None)
        std_fields['address_1'] = getattr(mailing_address, 'address_1', None)
        std_fields['address_2'] = getattr(mailing_address, 'address_2', None)
        std_fields['city'] = getattr(mailing_address, 'city', None)
        std_fields['state'] = getattr(mailing_address, 'state_province', None)
        std_fields['zip'] = getattr(mailing_address, 'zip', None)
        home_phone = getattr(name, 'home_phone', None)
        if home_phone and home_phone.strip():
            std_fields['phone'] = home_phone
        else:
            std_fields['phone'] = getattr(name, 'work_phone', None)
        std_fields['member_type'] = getattr(name, 'member_type', None)
        std_fields['chapter'] = getattr(name, 'chapter', None)

        return std_fields

    def save(self, *args, **kwargs):
        if self.contact_type == DjangoContactTypes.INDIVIDUAL.value:
            self.title = str(self.first_name) + ' ' + str(self.last_name)
            if self.designation is not None and self.designation.strip() != '':
                self.title += ', ' + self.designation
        else:
            self.title = self.company

        # if self.organization_type == DjangoOrganizationTypes.PR005.value:
        #     tag_type_specialty = TagType.objects.get(code="JOB_CATEGORY")
        #     # TODO: This is attempting to assign an unsaved object (itself) to
        #     # a possibly new, unsaved ContactTagType. Needs refactoring
        #     contact_tag_type_specialty, created = ContactTagType.objects.get_or_create(
        #         contact=self,
        #         tag_type=tag_type_specialty
        #     )

        # TODO: SubclassableModel.__init__ calls its super() before going through
        # the whole get_subclass dance, so fields with default values will have those
        # assigned, in some cases overwriting set values
        super(Contact, self).save(*args, **kwargs)

    def full_title(self):

        if self.contact_type == DjangoContactTypes.INDIVIDUAL.value:
            _full_title = self.first_name or ""

            if self.middle_name and self.middle_name.strip():
                middle_initial = self.middle_name.strip().strip(".")[0].upper()
                _full_title += " %s." % middle_initial

            _full_title += " %s" % self.last_name

            if self.suffix_name and self.suffix_name.strip():
                _full_title += " %s" % self.suffix_name

            if self.designation and self.designation.strip():
                _full_title += ", %s" % self.designation

        else:
            _full_title = self.title

        return _full_title

    @staticmethod
    def update_or_create_from_imis(username):
        """
        Update or create a Contact and Django User from iMIS. Will silently sync
        and return the existing Contact if it does already exist.
        :param username: iMIS id (:attr:`imis.models.Name.id`)
        :type username: str
        :return: `.Contact`
        """

        user, _ = User.objects.get_or_create(username=str(username))
        contact, _ = Contact.objects.get_or_create(user=user)
        contact = contact.sync_from_imis()
        return contact

    @staticmethod
    def autocomplete_search_fields():
        return "user__username__iexact", "title__icontains", "last_name__icontains", \
               "first_name__icontains", "company__icontains", "city__icontains", \
               "state__icontains", "country__icontains"

    def get_branch_offices(self):
        """
        NOT THE SAME AS parent_organization and its reverse "branchoffice" on Contact

        :return: reverse of parent_organization on BranchOffice
        """
        return self.branchoffices.all()

    @property
    def solr_id(self):
        return "CONTACT." + str(self.id)

    def solr_format(self):
        """
        Create a document for indexing in Solr

        :return: dict
        """

        formatted_content = self._init_solr_format()
        formatted_content.update(self.get_individual_solr_fields())
        formatted_content.update(self.get_solr_ctt_tags())

        speaker_events = []
        speaker_dates = []
        for contact_role in self.contactrole.all():

            if contact_role.publish_status == "PUBLISHED" and contact_role.content.status == "A":

                formatted_content.update(contact_role.get_solr_role_types())

                for sctag in contact_role.get_solr_content_tags():
                    formatted_content['tags'].add(sctag)

                if contact_role.role_type == "SPEAKER" \
                        and contact_role.content.content_type == "EVENT" \
                        and contact_role.content.event.begin_time:
                    event = contact_role.content.event
                    speaker_events.append(
                        "{id}|{event_type}|{title}|{date}|{parent_id}".format(
                            id=event.master_id,
                            event_type=event.event_type,
                            title=event.title,
                            date=event.begin_time,
                            parent_id=event.parent_id or ""
                        )
                    )
                    speaker_dates.append(event.begin_time)

                    # sort by most recent event
                    if not formatted_content.get("sort_time") \
                            or formatted_content["sort_time"] < event.begin_time:
                        formatted_content["sort_time"] = event.begin_time

        if speaker_events:
            pipe = re.escape("|")
            pattern = ".*{0}.*{0}.*{0}(?P<date>.*){0}.*".format(pipe)
            formatted_content["speaker_events"] = sorted(
                speaker_events,
                key=lambda e: re.match(pattern, e).group("date"),
                reverse=True
            )
            formatted_content["speaker_dates"] = sorted(speaker_dates, reverse=True)
        formatted_content["tags"] = list(formatted_content["tags"])

        return formatted_content

    def get_solr_ctt_tags(self):
        """
        Get the :class:`myapa.models.contact_tag_type.ContactTagType` tags to use in the Solr document

        :return: dict
        """
        solr_tags = dict()
        tags = set()
        for ctt in self.contacttagtype.all():
            tags = tags | {tag.title for tag in ctt.tags.all()}
        solr_tags["tags"] = tags
        return solr_tags

    def get_individual_solr_fields(self):
        """Get MyAPA profile image, url, and share permissions fields"""
        individual_fields = dict()
        if self.contact_type == "INDIVIDUAL":
            profile = getattr(self, "individualprofile", None)
            if profile and profile.image:
                individual_fields["thumbnail"] = profile.get_thumbnail_url()
                individual_fields["url"] = profile.get_profile_url()
                individual_fields["contact_permission"] = profile.share_contact or "PRIVATE"
        return individual_fields

    def _init_solr_format(self):
        """Initialize a basic document for indexing in Solr"""
        formatted_content = {
            "id": self.solr_id,
            "record_type": "CONTACT",
            "title": self.full_title(),
            "contact_type": self.contact_type,
            "member_type": self.member_type,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "middle_name": self.middle_name,
            "suffix_name": self.suffix_name,
            "designation": self.designation,
            "job_title": self.job_title,
            "company": (self.company or "").strip(),

            # some bios are so long they cannot be published to Solr
            "bio": Truncator(self.bio).words(1000) if self.bio else "",

            "about_me": self.about_me,
            "address1": self.address1,
            "address2": self.address2,
            "address_city": self.city,
            "address_state": self.state,
            "address_zip_code": self.zip_code,
            "address_country": self.country,
            "resource_url": self.personal_url,
            "phone": self.secondary_phone,  # work phone
            "email": self.email
        }
        return formatted_content

    def solr_publish(self, **kwargs):
        """
        method for publishing individual records to solr, will unpublish from solr if status is not "A",
        returns the status code if successful, raises an exception if not
        """
        solr_base = kwargs.pop("solr_base", None)
        if self.status == "A":
            pub_data = [self.solr_format()]
            solr_response = SolrUpdate(pub_data, solr_base=solr_base).publish()

            if solr_response.status_code != 200:
                raise Exception(
                    "An error occured while trying to publish this event to Search. Status Code: %s"
                    % solr_response.status_code
                )
            else:
                return solr_response.status_code
        else:
            # if it shouldn't be on solr, then remove it
            self.solr_unpublish(solr_base=solr_base)

    def solr_unpublish(self, **kwargs):
        """
        method for removing individual records from solr
        returns the status code if successful, raises an exception if not
        """
        solr_base = kwargs.pop("solr_base", None)
        pub_data = {"delete": {"id": self.solr_id}}
        solr_response = SolrUpdate(pub_data, solr_base=solr_base).publish()

        if solr_response.status_code != 200:
            raise Exception(
                "An error occured while trying to remove results from Search. Status Code: %s"
                % solr_response.status_code
            )

        return solr_response.status_code

    def designation_to_badges(self, request=None):
        from imis.models import Name
        from cm.credly_api_utils import CredlyAPICaller
        imis_name = Name.objects.filter(id=self.user.username).first()
        credly_api_caller = CredlyAPICaller()
        credly_api_caller.designation_to_badges(imis_name)

        if request:
            messages.success(request, "Syncing credentials of : \"" + str(self) + "\" from iMIS to Credly.")

    def get_bluepay_customer_information(self):
        query = """SELECT
               a.FIRST_NAME,
               a.LAST_NAME,
               b.ADDRESS_1,
               b.ADDRESS_2,
               b.CITY,
               b.STATE_PROVINCE,
               b.ZIP,
               b.COUNTRY,
               b.PHONE,
               a.EMAIL,
               a.COMPANY
        FROM Name a
            JOIN Name_Address b
                ON b.ID = a.ID
        WHERE a.ID = %s
        AND b.PREFERRED_BILL = 1"""

        keys = [
            'name1',
            'name2',
            'addr1',
            'addr2',
            'city',
            'state',
            'zipcode',
            'country',
            'phone'
        ]
        result = imis_sql.do_select(query, [self.user.username])
        return dict(zip(keys, result[0]))

    def _set_cached_subscription_attributes(self):
        subscriptions_attr = self.CachedAttrNames.IMIS_SUBSCRIPTIONS
        if not hasattr(self, subscriptions_attr):
            setattr(self, subscriptions_attr, [x for x in self.get_imis_subscriptions(status='A')])

        paid_subscriptions_attr = self.CachedAttrNames.IMIS_PAID_SUBSCRIPTIONS
        if not hasattr(self, paid_subscriptions_attr):
            setattr(self, paid_subscriptions_attr, [x for x in getattr(self, subscriptions_attr, [])
                                                    if isinstance(x.paid_thru, timezone.datetime)])

    def _get_membership_expiry_year_and_month(self, expiry_date: datetime.datetime) -> tuple:
        expiry_year = expiry_date.year
        expiry_month = expiry_date.month - self.LAPSED_MEMBERSHIP_RENEWAL_MONTHS
        if expiry_month < 0:
            expiry_year -= 1
            expiry_month = 12 - abs(expiry_month)
        elif expiry_month == 0:
            expiry_year -= 1
            expiry_month = 12
        return expiry_year, expiry_month

    def _get_membership_expiry_day(self, expiry_date: datetime.datetime) -> int:
        expiry_year, expiry_month = self._get_membership_expiry_year_and_month(expiry_date)
        expiry_month_lastday = monthrange(expiry_year, expiry_month)[1]
        if expiry_date.day > expiry_month_lastday:
            return expiry_month_lastday
        return expiry_date.day

    def get_membership_renewal_expiry_date(self, expiry_date: datetime.datetime) -> datetime.datetime:
        """
        Get the "real" expiration date for an APA membership, by subtracting the number of months
        defined by LAPSED_MEMBERSHIP_RENEWAL_MONTHS from the end of the actual iMIS paid_thru date
        (essentially making it seem as if their expiration date was that number of months ago)

        :param expiry_date: iMIS APA Subscription paid_thru date
        :return: The renewal expiration date for comparing with the current date
        """
        year, month = self._get_membership_expiry_year_and_month(expiry_date)
        renewal_date = datetime.datetime(
            year=year,
            month=month,
            day=self._get_membership_expiry_day(expiry_date)
        )
        return pytz.utc.localize(renewal_date)

    def _get_cached_paid_subscription(self, product_code):
        self._set_cached_subscription_attributes()
        return next((x for x in getattr(self, self.CachedAttrNames.IMIS_PAID_SUBSCRIPTIONS)
                     if x.product_code == product_code), None)

    def can_renew(self) -> bool:
        is_member = conditions.IsMember()
        self._set_cached_subscription_attributes()
        if not is_member.has_group(self):
            return False
        apa_subscription = self._get_cached_paid_subscription("APA")
        if apa_subscription is None:
            return False
        current_date = pytz.utc.localize(datetime.datetime.today())
        renewal_date = self.get_membership_renewal_expiry_date(apa_subscription.paid_thru)

        return renewal_date.date() < current_date.date()

    def has_autodraft_payment(self) -> bool:
        with connections['MSSQL'].cursor() as cursor:
            cursor.execute("SELECT Count(*) FROM [dbo].[BDR_Member_Accounts] WHERE MEMBER_ID = %s", [self.user.username])
            count = cursor.fetchone()[0]
            return count > 0

    def most_recent_apa_ptd(self):
        """Get the most recent paid thru date for an APA membership subscription"""
        self._set_cached_subscription_attributes()
        apa_subscription = self._get_cached_paid_subscription("APA")
        if apa_subscription:
            return apa_subscription.paid_thru.date()

    def get_cm_log(self):
        # Here because of circular import errors:
        from cm.models import Period, Log
        cand_period = Period.objects.get(code="CAND")
        cand_log = Log.objects.filter(contact=self, period=cand_period, status='A', is_current=True).first()
        if cand_log is not None:
            return cand_log
        else:
            # including status='A' excludes exempt AICP, this can cause issueq
            return Log.objects.select_related('period').filter(contact=self, status='A', is_current=True).first()

    def is_aicp_candidate(self):
        # Here because of circular import errors:
        from exam.models import ExamApplication, ENROLLED_STATUSES
        from store.models import Purchase

        cand_enroll_purchase = None
        cand_app = ExamApplication.objects.filter(
            contact=self,
            application_type='CAND_ENR',
            application_status__in=ENROLLED_STATUSES
        ).first()
        if cand_app is None:
            cand_enroll_purchase = Purchase.objects.filter(product__code='OW_AICP_CAN_ENR', contact=self).first()
        has_app_or_purchase = cand_app is not None or cand_enroll_purchase is not None
        the_log = self.get_cm_log()
        return has_app_or_purchase and the_log and the_log.period.code == "CAND"

    def set_imis_address_data(self, imis_address_data: dict):
        self.user_address_num = imis_address_data['address_num']
        self.address1 = imis_address_data['address_1']
        self.address2 = imis_address_data['address_2']
        self.city = imis_address_data['city']
        self.state = imis_address_data['state_province']
        self.zip_code = imis_address_data['zip']
        self.country = imis_address_data['country']
        self.company = imis_address_data['company']

    class CachedAttrNames:
        IMIS_SUBSCRIPTIONS = '_cached_imis_subscriptions'
        IMIS_PAID_SUBSCRIPTIONS = '_cached_imis_paid_subscriptions'

    def is_student(self):
        return self.member_type in ("STU", "FSTU")
