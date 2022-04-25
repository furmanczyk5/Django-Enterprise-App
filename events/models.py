import datetime
import imis
from enum import Enum

import pytz
import requests

from datetime import timedelta
from django.apps import apps
from django.contrib import messages
from django.db import models
from django.db.models import Prefetch
from django.utils import timezone
from sentry_sdk import add_breadcrumb, capture_exception

from content.models.settings import TARGETED_CREDITS_TOPICS, MINIMUM_YEAR
from conference.models.settings import *
# from conference.cadmium_api_utils import CadmiumAPICaller
from content.mail import Mail
from content.models import Content, BaseAddress, ContentManager
from content.models.settings import ContentStatus, PublishStatus
from content.solr_search import SolrUpdate
from content.utils import force_utc_datetime, batch_qs
from content.utils import generate_filter_model_manager
from myapa.models.contact_role import ContactRole
# from planning.settings import CADMIUMCD_API_KEY
from .tasks import provider_event_submit_task


CM_STATUSES = (
    ('A', 'Active'),
    ('I', 'Inactive'),
    ('P', 'Pending'),
    ('C', 'Cancelled')
    # more here...
)


class CMStatus(Enum):
    ACTIVE = "A"
    ACTIVE_LABEL = "Active"

    INACTIVE = "I"
    INACTIVE_LABEL = "Inactive"

    PENDING = "P"
    PENDING_LABEL = "Pending"

    CANCELLED = "C"
    CANCELLED_LABEL = "Cancelled"


EVENT_TYPES = (
    ('EVENT_MULTI', 'Multipart Event'),
    ('EVENT_SINGLE', 'Single Event'),
    ('ACTIVITY', 'Activity'),
    ('COURSE', 'On Demand'),
    ('EVENT_INFO', 'Informational Event'),
    ('LEARN_COURSE', 'APA Learn Course'),
    ('LEARN_COURSE_BUNDLE','APA Learn Course Bundle'),
)


class EventType(Enum):
    EVENT_SINGLE = "EVENT_SINGLE"
    EVENT_SINGLE_LABEL = "Single Event"

    EVENT_MULTI = "EVENT_MULTI"
    EVENT_MULTI_LABEL = "Multipart Event"

    ACTIVITY = "ACTIVITY"
    ACTIVITY_LABEL = "Activity"

    COURSE = "COURSE"
    COURSE_LABEL = "On Demand"

    EVENT_INFO = "EVENT_INFO"
    EVENT_INFO_LABEL = "Informational Event"

    LEARN_COURSE = "LEARN_COURSE"
    LEARN_COURSE_LABEL = "APA Learn Course"

    LEARN_COURSE_BUNDLE = "LEARN_COURSE_BUNDLE"
    LEARN_COURSE_BUNDLE_LABEL = "APA Learn Course Bundle"


EVENTS_DEFAULT_PARENT_LANDING_MASTER = 9026571

# any better way to manage this rather than hardcoding here??
# 9000321 - 2016 National Planning Conference
# 9135594 - 2018
# 2020: 9162593
NATIONAL_CONFERENCE_MASTER_ID = 9207576

NATIONAL_CONFERENCES = [
    ("15CONF", "2015"),
    ("EVENT_16CONF", "2016"),
    ("EVENT_17CONF", "2017"),
    ("EVENT_18CONF", "2018"),
    ('19CONF', '2019'),
    ('20CONF', '2020'),
    ('21CONF', '2021')
] # whichever is last is the current conference...SO ADDING ANOTHER TO THE LIST EFFECTS MANY THINGS!!! (which activities show by default in the admin, which show in the mobile apps)

NATIONAL_CONFERENCE_CURRENT = ("20CONF", "2020")
NATIONAL_CONFERENCE_NEXT    = ("21CONF", "2021")

NATIONAL_CONFERENCE_DEFAULT   = NATIONAL_CONFERENCE_CURRENT # By default, creating new conference activities will assign to this conference
NATIONAL_CONFERENCE_PROGRAM   = NATIONAL_CONFERENCE_CURRENT # The conference used for the program, my schedule, and the mobile app
NATIONAL_CONFERENCE_ADMIN     = NATIONAL_CONFERENCE_DEFAULT # The conference used for the kiosk and as the default in admin filters
NATIONAL_CONFERENCE_PROPOSALS = NATIONAL_CONFERENCE_NEXT    # TO DO: REMOVE

# TO DO:REMOVE
PROPOSAL_SUBMISSION_CATEGORY_CODES = [
    "EVENTS_NATIONAL_PROPOSAL_GEN",
    "EVENTS_NATIONAL_PROPOSAL_DIVE",
    "EVENTS_NATIONAL_PROPOSAL_DISCUSSION",
    "EVENTS_NATIONAL_PROPOSAL_FUNNY",
    "EVENTS_NATIONAL_PROPOSAL_STUDENT_FUNNY",
    "EVENTS_NATIONAL_PROPOSAL_POSTER",
    "EVENTS_NATIONAL_PROPOSAL_STUDENT_POSTER",
    "EVENTS_NATIONAL_PROPOSAL_EMERGE",
    "EVENTS_NATIONAL_PROPOSAL_MOBILE"]

EVENT_TICKET_TEMPLATES = (
    ("registrations/tickets/layouts/CONFERENCE-BADGE.html", "NPC Conference Badge"),
    ("registrations/tickets/layouts/CONFERENCE-ACTIVITY.html", "NPC Activity Ticket"),
    ("registrations/tickets/layouts/CONFERENCE-PAVILION.html", "NPC18 Pavilion Card"),
    ("registrations/tickets/layouts/CONFERENCE-NPC19.html", "NPC18 Check out NPC19!"),
    ("registrations/tickets/layouts/CONFERENCE-FOUNDATION18.html", "NPC18 Foundation Card"),
    ("registrations/tickets/layouts/EVENT-MULTI.html", "Chapter Conference Badge"),
    ("registrations/tickets/layouts/ACTIVITY.html", "Chapter Conference Activity"),
    ("registrations/tickets/layouts/CONFERENCE-DRINK-TICKET18.html", "Conference Drink Ticket18")
)

# FLAGGED FOR REFACTORING: CADMIUM SYNC
# REPLACE ALL HARDCODED INSTANCES OF "EVENTS_NATIONAL_TRACK..." WITH THIS GLOBAL:
# SPECIAL PROBLEM: Hardcoded Tag Type codes in templates related to solr results
# Note: On the member side, NPC Tracks are now being referred to as "Program Areas"
EVENTS_NATIONAL_TRACK_CURRENT = "EVENTS_NATIONAL_TRACK_21"

class EventManager(ContentManager):
    """
    Model manager for Event
    """
    def with_details(self):

        provider_roles = Prefetch("contactrole", queryset=ContactRole.objects.select_related("contact").filter(role_type="PROVIDER"), to_attr="provider_roles")
        speaker_roles = Prefetch("contactrole", queryset=ContactRole.objects.select_related("contact").filter(
            role_type__in=(
                "SPEAKER", "ORGANIZER&SPEAKER", "MOBILEWORKSHOPGUIDE",
                "MODERATOR", "ORGANIZER&MODERATOR", "LEADPOSTERPRESENTER", "POSTERPRESENTER",
                "MOBILEWORKSHOPCOORDINATOR", "LEADMOBILEWORKSHOPCOORDINATOR", "AUTHOR") ), to_attr="speaker_roles")

        qs = super().with_details().prefetch_related(speaker_roles, provider_roles)
        # maybe other things...product, attendees, children activities

        return qs

    def prefetch_speakers(self):

        provider_roles = Prefetch("contactrole", queryset=ContactRole.objects.select_related("contact").filter(role_type="PROVIDER"), to_attr="provider_roles")
        speaker_roles = Prefetch("contactrole", queryset=ContactRole.objects.select_related("contact").filter(
            role_type__in=(
                "SPEAKER", "ORGANIZER&SPEAKER", "MOBILEWORKSHOPGUIDE",
                "MODERATOR", "ORGANIZER&MODERATOR", "LEADPOSTERPRESENTER", "POSTERPRESENTER",
                "MOBILEWORKSHOPCOORDINATOR", "LEADMOBILEWORKSHOPCOORDINATOR", "AUTHOR")), to_attr="speaker_roles")

        # maybe other things...product, attendees, children activities
        return self.prefetch_related(speaker_roles, provider_roles)


class Event(Content, BaseAddress):
    class_queryset_args = {"content_type": "EVENT"}

    # currently used to store the "PresentationID" of Harvester Presentation records
    # allows us to sync these records into Django
    external_key = models.IntegerField(null=True, blank=True)

    #TO DO... distance learning fields (e.g. period approved)
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPES,
        default='EVENT_SINGLE',
        db_index=True
    )

    begin_time = models.DateTimeField('begin time', null=True, blank=True)
    end_time = models.DateTimeField('end time', null=True, blank=True)
    timezone = models.CharField(max_length=50, null=True, blank=True,
                                help_text="The timezone for the location of the event")
    is_online = models.BooleanField(default=False)

    cm_status = models.CharField(max_length=5, choices=CM_STATUSES, default='A')
    cm_approved = models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True, default=0)
    cm_law_approved = models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True, default=0)
    cm_ethics_approved = models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True, default=0)
    cm_equity_credits = models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True, default=0)
    cm_targeted_credits = models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True, default=0)
    cm_targeted_credits_topic = models.CharField(max_length=100, choices=TARGETED_CREDITS_TOPICS, null=True, blank=True)

    is_free = models.BooleanField(default=False)

    price_default = models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True,
            help_text="TO BE DELETED, DO NOT USE")

    # still used?????
    digital_product_url = models.URLField(max_length=255, blank=True, null=True,
            help_text="link to digital download (e.g. streaming/recording)")

    # still used ????
    always_on_schedule = models.BooleanField(help_text="Use to indicate that an activity should be auto-added to an attendee's schedule",
            default=False)

    # for courses (on-demand e-learning) ONLY... used to specify the
    # length in minutes that displays in the store
    length_in_minutes = models.IntegerField(null=True, blank=True)

    ticket_template = models.CharField(
        'badge/ticket template',
        max_length=100,
        choices=EVENT_TICKET_TEMPLATES,
        null=True,
        blank=True
    )
    mail_badge = models.BooleanField(default=True)
    learning_objectives = models.TextField("Learning Objectives", blank=True, null=True)
    more_details = models.TextField("More Details", blank=True, null=True)
    location = models.TextField("Location", blank=True, null=True, help_text="Room or Venue")
    outside_vendor = models.BooleanField(default=False)

    # pricing dates used for the events and product prices iMIS sync
    price_early_cutoff_time = models.DateTimeField('early pricing cutoff time', null=True, blank=True)
    price_regular_cutoff_time = models.DateTimeField('regular pricing cutoff time', null=True, blank=True)
    price_late_cutoff_time = models.DateTimeField('late pricing cutoff time', null=True, blank=True)

    objects = EventManager()

    def __init__(self, *args, **kwargs):
        super(Event, self).__init__(*args, **kwargs)
        self._meta.get_field('content_type').default = 'EVENT'

    def timezone_object(self):
        if self.timezone:
            return pytz.timezone(self.timezone)
        else:
            return pytz.timezone("America/Chicago")

    def begin_time_astimezone(self):
        if self.begin_time:
            return self.begin_time.astimezone(self.timezone_object())
        else:
            return None

    def end_time_astimezone(self):
        if self.end_time:
            return self.end_time.astimezone(self.timezone_object())
        else:
            return None

    def has_cm_law(self):
        return self.cm_law_approved is not None and self.cm_law_approved != 0
    has_cm_law.boolean = True
    has_cm_law.short_description = 'CM Law?'

    def has_cm_ethics(self):
        return self.cm_ethics_approved is not None and self.cm_ethics_approved != 0
    has_cm_ethics.boolean = True
    has_cm_ethics.short_description = 'CM Ethics?'

    def has_cm_equity(self):
        return self.cm_equity_credits is not None and self.cm_equity_credits != 0
    has_cm_equity.boolean = True
    has_cm_equity.short_description = 'CM Equity?'

    def has_cm_targeted(self):
        return self.cm_targeted_credits is not None and self.cm_targeted_credits != 0
    has_cm_targeted.boolean = True
    has_cm_targeted.short_description = 'CM Sustainability & Resilience?'

    @property
    def is_cancelled(self):
        return self.status == ContentStatus.HIDDEN.value and self.cm_status == CMStatus.CANCELLED.value

    @property
    def has_changes(self):
        return self.publish_status == PublishStatus.DRAFT.value \
               and self.status == ContentStatus.NOT_COMPLETE.value

    @property
    def is_editable(self):
        """Can this event be edited by a CM Provider?"""
        if self.status == ContentStatus.NOT_COMPLETE.value or not self.is_past:
            return True
        return False

    @property
    def is_submitted(self):
        return self.publish_status == PublishStatus.DRAFT.value \
               and self.status == ContentStatus.ACTIVE.value

    @property
    def is_pending_payment(self):
        return self.publish_status == PublishStatus.DRAFT.value \
               and self.status == ContentStatus.PENDING.value

    @property
    def has_registration_product(self):
        return hasattr(self, "product")

    @property
    def is_past(self):
        return self.begin_time and self.begin_time <= timezone.now().replace(tzinfo=pytz.UTC)

    @property
    def avg_rating_tuple(self):
        return self.rating_average, self.rating_count

    @property
    def can_relist(self):
        return self.is_published and self.event_type in \
               (EventType.EVENT_SINGLE.value, EventType.COURSE.value)

    def get_total_cm_credits(self):
        return self.cm_approved or 0

    def is_conference_activity(self):
        """
        returns true if event is an activity for the current conference
        """
        # should make something better
        return self.event_type == "ACTIVITY" and self.parent.content_live and self.parent.content_live.code in [conf[0] for conf in NATIONAL_CONFERENCES]

    def solr_format(self):
        formatted_content = super().solr_format()
        formatted_content_additional = {
            "event_type": self.event_type,
            "begin_time": force_utc_datetime(self.begin_time),
            "end_time": force_utc_datetime(self.end_time),
            "timezone": self.timezone,
            "location": self.location,
            "outside_vendor": self.outside_vendor,
            "address_city": self.city,
            "address_state": self.state,
            "address_country": self.country,
            "cm_status": self.cm_status,
            "cm_approved": self.cm_approved,
            "cm_law_approved": self.cm_law_approved,
            "cm_ethics_approved": self.cm_ethics_approved,
            "cm_equity_credits": self.cm_equity_credits,
            "cm_targeted_credits": self.cm_targeted_credits,
            "cm_targeted_credits_topic": self.cm_targeted_credits_topic,
            "is_free": self.is_free,
            "is_online": self.is_online,
            "sort_time": force_utc_datetime(self.begin_time)

            # "price_default":self.price_default # NOT IN SCHEMA YET
        }
        formatted_content.update(formatted_content_additional);
        return formatted_content

    def save(self, *args, **kwargs):
        if not self.parent_landing_master_id: #setting default parent_landing_master
            self.parent_landing_master_id = EVENTS_DEFAULT_PARENT_LANDING_MASTER
        self.content_type = 'EVENT'

        three_years = datetime.timedelta(days=3*365)

        if not self.pk and self.end_time:
            self.archive_time = self.end_time + three_years
        elif not self.pk and self.begin_time:
            self.archive_time = self.begin_time + three_years
        elif not self.pk:
            self.archive_time = timezone.now() + three_years

        if self.begin_time and self.begin_time.year < MINIMUM_YEAR:
            self.begin_time = self.begin_time.replace(year=MINIMUM_YEAR)
        if self.end_time and self.end_time.year < MINIMUM_YEAR:
            self.end_time = self.end_time.replace(year=MINIMUM_YEAR)

        super(Event, self).save(*args, **kwargs)

    def get_purchase(self, *ards, **kwargs):
        product_model = apps.get_model(app_label="store", model_name="Product")
        purchase_model = apps.get_model(app_label="store", model_name="Purchase")

        product = product_model.objects.get(content=self)
        event_purchase = purchase_model.objects.filter(product=product, order__isnull=False)

        return event_purchase

    def provider_submit(self):

        # make sure it's the SUBMISSION copy
        add_breadcrumb(
            message='Running provider_submit for event {}'.format(self.title),
            data=dict(
                pk=self.pk,
                publish_status=self.publish_status,
                status=self.status
            ),
            level='debug'
        )

        if self.publish_status == "DRAFT":

            if self.status != ContentStatus.MARKED_FOR_DELETION.value:
                self.status = ContentStatus.ACTIVE.value
            self.submission_time = timezone.now()
            self.save()

            # No longer publishing to draft, only prod
            add_breadcrumb(
                message='Calling publish() on event master_id: {}'.format(self.master_id),
                level='debug'
            )
            self.publish()

            # then to solr
            self.solr_publish()

            try:
                provider = self.contactrole.select_related("contact").filter(role_type="PROVIDER").first().contact
                self.send_speaker_emails(provider=provider)
                # instead of this should we publish info events to cm/search?
                # i.e. change cm/search so it pulls in the info events
                if self.event_type != "ACTIVITY" and self.event_type != "EVENT_INFO":
                    self.send_admin_emails(provider=provider)
            except Exception as exc:
                capture_exception(exc)

        else:
            raise ValueError("Cannot submit non-draft records") # shouldn't happen

    def provider_submit_async(self):
        kwargs = dict(event_id=self.id, EventClass=self.__class__)
        provider_event_submit_task.apply_async(kwargs=kwargs)

    def send_speaker_emails(self, provider=None, email_template="PROVIDER_SPEAKER_INVITATION"):

        if provider == None:
            provider = self.contactrole.select_related("contact").filter(role_type="PROVIDER").first().contact

        speaker_roles = self.contactrole.select_related("contact").filter(role_type="SPEAKER", invitation_sent=False)

        for speaker_role in speaker_roles:
            try:
                mail_context = {
                    "speaker":speaker_role.contact,
                    "contact_role":speaker_role,
                    "event":self,
                    "provider":provider
                }
                # only send speak mail if speaker has a contact record in db
                if speaker_role.contact:
                    Mail.send(email_template, mail_context["speaker"].email, mail_context)
            except Exception as exc:
                capture_exception(exc)
        speaker_roles.update(invitation_sent=True)

    def send_admin_emails(self, provider=None, email_template="PROVIDER_EVENT_SUBMIT"):

        if provider == None:
            provider = self.contactrole.select_related("contact").filter(role_type="PROVIDER").first().contact

        for admin in  provider.contactrelationship_as_source.filter(relationship_type="ADMINISTRATOR"):
            try:
                mail_context = {
                    "admin":admin.target,
                    "event":self,
                    "provider":provider
                }
                # Mail.send(email_template, admin.email, mail_context) # TO DO... use this once we have final email text
                Mail.send(email_template, admin.target.email, mail_context)
            except Exception as exc:
                capture_exception(exc)

    def relist(self, replace=dict()):
        """
        Makes a deep copy of this event and related publishable records (tags, contactroles, products, pricing)
        """

        replace_dict = dict(
            title="{0} RELISTED".format(self.title),
            begin_time=None,
            end_time=None,
            status="N",
            publish_status="DRAFT",
            created_time=timezone.now()
        )

        replace_dict.update(replace)

        return self.deep_copy(replace=replace_dict)


    def get_proxymodel_class(self):
        """
        returns the proxy model class that fits this record
        """
        if self.event_type == "EVENT_SINGLE":
            return apps.get_model(app_label="events", model_name="eventsingle")
        elif self.event_type == "EVENT_MULTI":
            return apps.get_model(app_label="events", model_name="eventmulti")
        elif self.event_type == "ACTIVITY":
            if self.is_conference_activity():
                return apps.get_model(app_label="conference", model_name="nationalconferenceactivity")
            else:
                return apps.get_model(app_label="events", model_name="activity")
        elif self.event_type == "COURSE":
            return apps.get_model(app_label="events", model_name="course")
        else:
            return apps.get_model(app_label="events", model_name="event")

    def imis_format(self):

        conference_code = ""
        if self.event_type == "ACTIVITY":
            conference_code = self.parent.content_live.product.imis_code # draft should be ok to use

        formatted_content = {
            "EventType": self.event_type,
            "ConferenceCode":conference_code, # conference code
            "EventCode": self.product.imis_code,
            "EventName":self.title,
            "Description": self.description,
            "BeginTime":str(self.begin_time)[:19],
            "EndTime":str(self.end_time)[:19],
            "Address1": self.address1,
            "Address2": self.address2,
            "City": self.city,
            "State": self.state,
            "Zip": self.zip_code,
            "Country": self.country,
        }

        try:
            formatted_product = self.product.imis_format()
            formatted_content.update(formatted_product)
        except:
            # fails if no product associated with the event
            pass

        return formatted_content

    def events_related(self):
        """
        returns related children of the event (activities) that have an active status
        """

        return Event.objects.filter(parent__content_draft=self, status="A")

    def events_related_live(self):
        """
        returns related children of the event (activities) that have an active status and have publish status as "PUBLISHED"
        """
        return Event.objects.filter(parent__content_live=self, status="A")

    def get_meeting_code(self):
        if self.event_type == 'ACTIVITY':
            try:
                imis_code = self.parent.product.imis_code
            except:
                imis_code = self.parent.content_live.event.product.imis_code
        else:
            imis_code = self.product.imis_code

        return imis_code or ''

    def has_started(self):
        """
        returns true if begin time has passed
        NOTE: until we figure out how timezones are going to work, this always uses chicago timezones
        """
        if self.begin_time:
            begin_time = pytz.timezone("America/Chicago").localize(self.begin_time.replace(tzinfo=None))
            now = timezone.now()
            return now > begin_time
        else:
            return False

    def sync_from_harvester(self, request=None):
        from conference.cadmium_api_utils import CadmiumAPICaller
        cadmium_api_caller = CadmiumAPICaller()
        cadmium_api_caller.sync_from_harvester(self)

        # ABOVE TWO LINES REPLACE ALL BELOW UP TO if request:
        # from conference.views.harvester import get_dummy_json, EVENT_POST

        # from conference.utils import update_presentation
        # data = {}
        # e = ''
        #
        # if self.external_key:
        #     api_key = CADMIUMCD_API_KEY
        #     # url = 'http://www.conferenceharvester.com/conferenceportal3/webservices/HarvesterJsonAPI.asp'
        #     url = HARVESTER_API_URL
        #     params = {
        #     'APIKey': api_key,
        #     'Method': 'getSinglePresentationWithPresenters',
        #     'PresentationID': self.external_key}
        #
        #     r = requests.post(url, params=params, json=data)
        #     json_list = r.json()
        #     if json_list:
        #         e = json_list[0]
        #         # print(json_list)
        #     # else:
        #     #     e = get_dummy_json(EVENT_POST)
        #
        # if e:
        #     context = update_presentation(self, e)
        if request:
            messages.success(request, "syncing event: \"" + str(self) + "\" from Harvester to Django.")

    def sync_to_imis(self):

        """
        publishes an event options to mis

        IF PRODUCT OPTION, AND PRODUCT PRICE IS $0, WE ASSUME THIS IS A COMPED PRODUCT.
        IF NO PRODUCT OPTION, AND PRODUCT PRICE IS $0, WE ASSUME THIS IS A REGULAR PRODUCT WITH $0 PRICE.
        NOTE: CHANGE EVENT CODE TO 19CONF (FROM EVENT_19CONF)

        SOME QUIRKS:
        1. EVENT OPTION PRODUCT CODES ARE CREATED BY COMBINING EVENT IMIS CODE AND OPTION CODE. THIS SHOULD BE A NEW FIELD. (IMIS_CODE ON OPTION)
        2. EVENT ACTIVITY TICKET PRODUCT CODES ARE THE IMIS_CODE ON THE PRODUCT. (SHOULD THIS BE A PRODUCT_IMIS_CODE ON THE EVENT CONTENT?)
        3. EVENT SESSION PRODUCT CODES ARE CREATED BY COMBINING NPC CODE AND THE SESSION EVENT CODE. (SHOULD THIS BE A PRODUCT_IMIS_CODE ON THE EVENT CONTENT?)
        4. COMPLIMENTARY PRODUCT STATUS IS GIVEN IF THE EVENT HAS AN ASSOCIATED PRODUCT WITH A $0 PRICE. SESSIONS ARE NOT COMP. (THIS SHOULD BE A FIELD ON OPTION AND PRODUCT PRICE)
        5. EVENT WITH PRODUCT OPTIONS ARE ASSUMED TO BE REGISTRATION OPTIONS. NO DJANGO ACTIVITIES SHOULD HAVE OPTIONS.
        6. PRINT TICKET OPTION IS SELECTED FOR EVENTS THAT DON'T HAVE PRODUCT OPTIONS AND HAVE PRODUCTS. (THIS SHOULD BE A FIELD ON PRODUCT PRICE)
        """

        # reg start and end dates are not stored as separate fields in django (they're in the product price).
        # registration start date =  -1 year from event start date.
        # registration end date = event end date

        # iMIS expects central time, but pyodbc (or iMIS) doesn't know how to handle time zones. so we do this manually.
        setattr(self, "imis_begin_time", self.begin_time - timedelta(hours=5))
        setattr(self, "imis_end_time", self.end_time - timedelta(hours=5))

        # set the event begin time to 1 year prior
        setattr(self, "registration_begin_time", self.imis_begin_time - timedelta(days=365))

        imis.models.MeetMaster.create_event(self)

        event_product_options = self.product.options.all()

        for option in event_product_options:

            product_major = self.code
            product_minor = option.code
            product_code = product_major + '/' + product_minor

            imis.models.Product.create_event(self, product_major, product_minor, product_code, option)

            imis.models.ProductFunction.create_event(self, product_code, option=option)

            # PRODUCT INVENTORY DOESN'T APPEAR TO BE MUCH BY IMIS FOR EVENTS.
            imis.models.ProductInventory.objects.get_or_create(product_code = product_code)

            # commenting out for chapter conferences (no pricing will be created)
            #imis.models.ProductPrice.create_event(self, product_code, option=option)

            imis.models.MeetResources.create_location(self, product_code)

    class Meta:
        verbose_name="Event/Activity/Course"
        verbose_name_plural="All events, activities, and courses"


# ------------------------------------------------------------------------------
# proxy models for specific events-related content types

class Activity(Event):
    """
    Proxy model for "activities", inherits from Event ... activities are components of multipart events
    (individual sessions, workshops, etc. that
    are part of a larger conference or event). Activity records should always have event_type="ACTIVITY" and the
    parent attribute should reference the master record of the event that the activity belongs to.
    """
    class_queryset_args = {"content_type":"EVENT", "event_type":"ACTIVITY"}

    objects = generate_filter_model_manager(ParentManager=EventManager, event_type="ACTIVITY")()

    def __init__(self, *args, **kwargs):
        super(Activity, self).__init__(*args, **kwargs)
        self._meta.get_field('event_type').default = 'ACTIVITY'


    def sync_to_imis(self):

        """
        publishes an event activities to imis

        SOME QUIRKS:
        1. EVENT OPTION PRODUCT CODES ARE CREATED BY COMBINING EVENT IMIS CODE AND OPTION CODE. THIS SHOULD BE A NEW FIELD. (IMIS_CODE ON OPTION)
        2. EVENT ACTIVITY TICKET PRODUCT CODES ARE THE IMIS_CODE ON THE PRODUCT. (SHOULD THIS BE A PRODUCT_IMIS_CODE ON THE EVENT CONTENT?)
        3. EVENT SESSION PRODUCT CODES ARE CREATED BY COMBINING NPC CODE AND THE SESSION EVENT CODE. (SHOULD THIS BE A PRODUCT_IMIS_CODE ON THE EVENT CONTENT?)
        4. COMPLIMENTARY PRODUCT STATUS IS GIVEN IF THE EVENT HAS AN ASSOCIATED PRODUCT WITH A $0 PRICE. SESSIONS ARE NOT COMP. (THIS SHOULD BE A FIELD ON OPTION AND PRODUCT PRICE)
        5. EVENT WITH PRODUCT OPTIONS ARE ASSUMED TO BE REGISTRATION OPTIONS. NO DJANGO ACTIVITIES SHOULD HAVE OPTIONS.
        6. PRINT TICKET OPTION IS SELECTED FOR EVENTS THAT DON'T HAVE PRODUCT OPTIONS AND HAVE PRODUCTS. (THIS SHOULD BE A FIELD ON PRODUCT PRICE)
        """

        # what the heck! needed since we use UTC in django, datetimes (I believe) are automatically converted
        # to UTC no matter what timezone you try to save as. REMEMBER TO CHANGE THIS TO 6 HOURS AFTER
        # daylight savings time starts (3/10)!

        setattr(self, "imis_begin_time", self.begin_time - timedelta(hours=5))
        setattr(self, "imis_end_time", self.end_time - timedelta(hours=5))

        # set the event begin time to 1 year prior
        setattr(self, "registration_begin_time", self.imis_begin_time - timedelta(days=365))


        # TICKETED ACTIVITIES              git
        if hasattr(self, "product") and self.product:
            product_major = self.parent.content_live.code
            product_minor = self.code
            product_code = self.product.imis_code

        # SESSION (NO TICKET), USE EVENT CODE TO CREATE IMIS PRODUCT.
        else:
            product_major = self.parent.content_live.code
            product_minor = self.code
            product_code = self.parent.content_live.code + "/" + self.code


        imis.models.Product.create_event(self, product_major, product_minor, product_code)

        imis.models.ProductFunction.create_event(self, product_code)

        # PRODUCT INVENTORY DOESN'T APPEAR TO BE MUCH BY IMIS FOR EVENTS.
        imis.models.ProductInventory.objects.get_or_create(product_code=product_code)

        imis.models.MeetResources.create_location(self, product_code)


    def save(self, *args, **kwargs):
        self.event_type = 'ACTIVITY'
        if not self.template == "PAGE" and not self.template: #for things currently set to page (2016 conf)... keep them that way
            self.template = "events/newtheme/event-details.html"
        super(Activity, self).save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name_plural="Multipart event activities"


class EventSingle(Event):
    class_queryset_args = {"content_type":"EVENT", "event_type":"EVENT_SINGLE"}

    objects = generate_filter_model_manager(ParentManager=EventManager, event_type="EVENT_SINGLE")()

    def __init__(self, *args, **kwargs):
        super(EventSingle, self).__init__(*args, **kwargs)
        self._meta.get_field('event_type').default = 'EVENT_SINGLE'

    def save(self, *args, **kwargs):
        self.event_type = 'EVENT_SINGLE'
        self.template = "events/newtheme/event-details.html"
        super(EventSingle, self).save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name="Single event"


class EventMultiManager(EventManager):
    """
    Model manager for Content
    """
    def with_details(self, publish_status="PUBLISHED"):

        activities = Prefetch(
            "master__children",
            queryset=Activity.objects.prefetch_speakers().filter(
                publish_status=publish_status
            ).order_by(
                "begin_time",
                "end_time"
            ),
            to_attr="activities"
        )
        qs = super().with_details().prefetch_related(activities)
        return qs

    def get_queryset(self):
        return super().get_queryset().filter(event_type="EVENT_MULTI")


class EventMulti(Event):

    class_queryset_args = {"content_type": "EVENT", "event_type": "EVENT_MULTI"}
    objects = EventMultiManager()

    def __init__(self, *args, **kwargs):
        super(EventMulti, self).__init__(*args, **kwargs)
        self._meta.get_field('event_type').default = 'EVENT_MULTI'

    def provider_submit(self):
        super().provider_submit()
        activities = self.get_activities()
        # activities.update(status="A")
        for activity in activities:
            activity.provider_submit()

    def get_activities(self):

        return Activity.objects.filter(
            parent__id=self.master_id,
            publish_status=self.publish_status
        ).select_related(
            "product"
        )

    def get_activities_with_product_cart(self):
        # importing here to avoid circular import
        from store.models.product_cart import ProductCart

        activities = self.get_activities().filter(
            status='A',
            product__status='A'
        ).select_related(
            "parent__content_live__product"
        ).order_by(
            "begin_time", "end_time"
        )

        contents = [x.product.content for x in activities]
        product_carts = ProductCart.objects.filter(content__in=contents)

        for activity in activities:
            product_cart = next(
                filter(
                    lambda pc: pc.content.id == activity.product.content.id,
                    product_carts
                ), None
            )
            activity.product_cart = product_cart
        return activities

    def get_total_cm_credits(self):
        total_cm_credits = 0
        for activity in self.get_activities():
            total_cm_credits += activity.get_total_cm_credits()
        return total_cm_credits

    def has_ticketed_activities(self):
        return self.get_activities().filter(status='A', product__status='A').exists()

    def save(self, *args, **kwargs):
        self.event_type = 'EVENT_MULTI'
        self.template = "events/newtheme/eventmulti-details.html"
        super(EventMulti, self).save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "Multipart event"


# TO DO.. consider creating a separate app for on-demand e-learning ...
# on-demand e-learning would inherit directly from content...
# CM-specific attributes would move to abstract model that both events and on-demand e-learning
# would inerhit from
# (EVENTUALLY... would mean MAJOR refactoring!!!!!!!)
class Course(Event):
    class_queryset_args = {"content_type":"EVENT", "event_type":"COURSE"}
    objects = generate_filter_model_manager(ParentManager=EventManager, event_type="COURSE")()

    def __init__(self, *args, **kwargs):
        super(Course, self).__init__(*args, **kwargs)
        self._meta.get_field('event_type').default = "COURSE"

    def save(self, *args, **kwargs):
        self.event_type = "COURSE"
        if hasattr(self, "product"):
            self.template = "store/newtheme/product/details.html"
        else:
            self.template = "events/newtheme/ondemand/course-details.html"
        super(Course, self).save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "On-demand education"
        verbose_name_plural = "On-demand education"


class EventInfo(Event):
    class_queryset_args = {"content_type":"EVENT", "event_type":"EVENT_INFO"}

    objects = generate_filter_model_manager(ParentManager=EventManager, event_type="EVENT_INFO")()

    def __init__(self, *args, **kwargs):
        super(EventInfo, self).__init__(*args, **kwargs)
        self._meta.get_field('event_type').default = 'EVENT_INFO'

    def save(self, *args, **kwargs):
        self.event_type = 'EVENT_INFO'
        self.template = "events/newtheme/eventinfo-details.html"
        super(EventInfo, self).save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name="Info event"



class SpeakerManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role_type="SPEAKER")

class Speaker(ContactRole):
    # saving as this is the same as saving a Contact Role. The only difference is the queryset
    objects = SpeakerManager()

    def save(self, *args, **kwargs):
        self.role_type="SPEAKER"
        return super().save(*args, **kwargs)

    @classmethod
    def solr_reindex_contact(self, contact):
        if next((True for cr in contact.contactrole.all() if
            cr.role_type in (
                "SPEAKER","ORGANIZER&SPEAKER","MOBILEWORKSHOPGUIDE",
                "MODERATOR", "ORGANIZER&MODERATOR", "LEADPOSTERPRESENTER", "POSTERPRESENTER",
                "MOBILEWORKSHOPCOORDINATOR", "LEADMOBILEWORKSHOPCOORDINATOR", "AUTHOR") and
            cr.publish_status == "PUBLISHED"), False) and not contact.individualprofile.speaker_opt_out:

            contact.solr_publish()
        else:
            contact.solr_unpublish()

    @classmethod
    def solr_reindex_all(cls):
        """ reindex all speakers """

        GROUP_SIZE = 100

        print("starting solr reindex")

        # deleting all speakers from solr
        #   This is how we are recognizing speakers,
        #   until we start publishing other contact records this is OK,
        #   need better way to remove records that are no longer speakers
        #   (or just update those records if they belong in solr there for something else)
        delete_kwargs = dict(query="id:CONTACT.*, speaker_events:*")
        print("Removing old solr results matching query:")
        print(delete_kwargs)
        delete_query_kwargs = dict(delete=delete_kwargs)
        SolrUpdate(delete_query_kwargs).publish()

        base_query = cls.objects.filter(content__publish_status="PUBLISHED").exclude(contact__isnull=True).order_by("contact_id").distinct("contact_id")
        optimized_query = base_query.prefetch_related("contact__contactrole__content__event__contenttagtype__tags")
        total_records = base_query.count()

        total_count = 0
        group_count = 0
        pub_data = []

        print("starting publishing for {0} total records".format(total_records))

        # batching the queryset so that this doesn't take too long/require too much memory
        for batch_tuple in batch_qs(optimized_query, 500):

            for record in batch_tuple[3]:

                pub_data.append(record.contact.solr_format())
                group_count += 1
                total_count += 1

                if group_count >= GROUP_SIZE or total_count >= total_records:

                    solr_response = SolrUpdate(pub_data).publish()

                    if solr_response.status_code == 200:
                        group_count = 0
                        pub_data = []
                        print("published {0} of {1}, {2}".format(total_count, total_records, "%.2f%%" % (float(total_count/total_records)*100.0)))
                    else:
                        raise ValueError("Publish to solr failed")

        print("complete")

    class Meta:
        proxy = True



