import json

from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.utils.html import strip_tags
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from six.moves import html_parser

from .program import MicrositeSearchView
from content.models import ContentTagType
from conference.models import NationalConferenceActivity
from events.models import (
    Activity,
    NATIONAL_CONFERENCES,
    NATIONAL_CONFERENCE_PROGRAM)
from imis.event_tickets import (
    cancel_activity_on_schedule,
    save_activity_to_schedule)
from myapa.models.contact import Contact
from myapa.models.contact_role import ContactRole
from myapa.utils import is_authenticated_check_all
from registrations.models import Attendee


class ConferenceMobileAppVersionMixin(object):
    """
    Convenient Mixin to api versions by year
    For most years, specific logic will not change, only the multipart event
    record for conference will.
    """

    # To add a new conference, match a new version to conference year here,
    # and add the appropriate conference record
    # in events.models NATIONAL_CONFERENCES
    api_versions = [
        dict(version="0.3", year="2018"),
        dict(version="0.2", year="2017"),
        dict(version="0.1", year="2016"),
        dict(version="0.0", year="2015")
    ]

    def get_conference_event_code_from_version(self, version=None):
        year = next(
            (
                v["year"]
                for v in self.api_versions
                if v["version"] == version
            ),
            NATIONAL_CONFERENCE_PROGRAM[1])
        return next(
            (
                conf[0]
                for conf in NATIONAL_CONFERENCES
                if conf[1] == year
            ),
            NATIONAL_CONFERENCE_PROGRAM[0])


class MobileAppMicrositeSearchView(
        ConferenceMobileAppVersionMixin, MicrositeSearchView):

    def get_conference_event_code(self):
        api_version = self.kwargs.get("version", None)
        return self.get_conference_event_code_from_version(api_version)


class ScheduleIdsView(ConferenceMobileAppVersionMixin, View):
    """
    View that returns a list of activity master ids on
    logged in user's schedule for the current national conference
    ONLY returns the JSON of the ids for use with apis
    """
    def get(self, request, *args, **kwargs):

        api_version = self.kwargs.get("version", None)

        is_authenticated, username = is_authenticated_check_all(request)

        context = {"is_authenticated": is_authenticated}

        if is_authenticated:
            schedule_ids = [
                a.get("event__master_id")
                for a in Attendee.objects.filter(
                    event__parent__content_live__code=(
                        self.get_conference_event_code_from_version(
                            api_version)),
                    contact__user__username=username,
                    status="A",
                ).values("event__master_id")
            ]

            context["success"] = True
            context["schedule_ids"] = schedule_ids

        else:
            context["success"] = False
            context["message"] = "Not logged in"
            context["action"] = "LOGOUT"

        return HttpResponse(
            json.dumps(context, cls=DjangoJSONEncoder),
            content_type='application/json')


class ScheduleUpdate(View):
    """
    makes bulk updates to logged in user's
    conference schedule, returns json response
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(ScheduleUpdate, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):

        is_authenticated, username = is_authenticated_check_all(request)

        context = {}

        add_string_ids = request.POST.get("add", "").split(",")
        remove_string_ids = request.POST.get("remove", "").split(",")

        add_ids = [int(i) for i in add_string_ids if i != ""]
        remove_ids = [int(i) for i in remove_string_ids if i != ""]

        if is_authenticated:
            # remove anything on schedule that matches
            # the master ids in the "remove" parameter
            Attendee.objects.filter(
                event__master__id__in=remove_ids,
                contact__user__username=username,
                event__product__isnull=True
            ).delete()

            # Need the actual activity and contact records to do "create"
            activities_to_add = NationalConferenceActivity.objects.filter(
                master__id__in=add_ids,
                publish_status='PUBLISHED',
                product__isnull=True)
            contact = Contact.objects.get(user__username=username)

            for activity in activities_to_add:
                Attendee.objects.get_or_create(event=activity, contact=contact)

            context["success"] = True
            context["message"] = "Successfully updated your schedule"
        else:
            context["success"] = False
            context["action"] = "LOGOUT"
            context["message"] = (
                'Invalid Authentication. '
                'Log in and try again.')

        return HttpResponse(
            json.dumps(context), content_type='application/json')


# GET RID OF THIS ONCE REMOVED FROM APP
#   Use ScheduleUpdate instead
class ScheduleAdd(View):

    def get(self, request, *args, **kwargs):
        is_authenticated, username = is_authenticated_check_all(request)

        context = {}

        if is_authenticated:

            master_id = kwargs.get("master_id")
            activity = Activity.objects.get(
                master__id=master_id,
                publish_status="PUBLISHED",
                product__isnull=True
            )
            contact = Contact.objects.get(user__username=username)

            save_activity_to_schedule(activity, username)

            # TODO: SMT REMOVE THIS
            Attendee.objects.get_or_create(event=activity, contact=contact)

            context["success"] = True
            context["message"] = "Successfully updated your schedule"
        else:
            context["success"] = False
            context["action"] = "LOGOUT"
            context["message"] = (
                'Invalid Authentication. '
                'Log in and try again.')

        return HttpResponse(
            json.dumps(context), content_type='application/json')


# GET RID OF THIS ONCE REMOVED FROM APP
#   Use ScheduleUpdate instead
class ScheduleRemove(View):

    def get(self, request, *args, **kwargs):
        print('remove called')
        is_authenticated, username = is_authenticated_check_all(request)

        context = {}

        if is_authenticated:

            master_id = kwargs.get("master_id")

            activity = Activity.objects.get(
                master__id=master_id,
                publish_status="PUBLISHED",
                product__isnull=True
            )

            cancel_activity_on_schedule(activity, username)

            # TODO: SMT REMOVE THIS
            Attendee.objects.filter(
                event__master__id=master_id,
                contact__user__username=username,
                event__product__isnull=True
            ).delete()

            context["success"] = True
            context["message"] = "Successfully updated your schedule"

        else:
            context["success"] = False
            context["action"] = "LOGOUT"
            context["message"] = (
                'Invalid Authentication. '
                'Log in and try again.')

        return HttpResponse(
            json.dumps(context), content_type='application/json')


class ConferenceAttendeesJsonView(ConferenceMobileAppVersionMixin, View):
    """
    Returns a json response of all attendees at NPC
        (version determines which npc year)
    """

    def get(self, request, *args, **kwargs):

        api_version = self.kwargs.get("version", None)
        is_authenticated, username = is_authenticated_check_all(request)

        if is_authenticated:

            attendees = Attendee.objects.filter(
                status="A",
                event__code=self.get_conference_event_code_from_version(
                    api_version),
                purchase__agreement_response_2=True
            ).values(
                "contact__title",
                "contact__last_name",
                "contact__company",
                "contact__city",
                "contact__state",
                "contact__email",
                "contact__phone"
            ).order_by('contact__last_name')

            context = {
                "success": True,
                "data": [{
                    "title": a["contact__title"],
                    "last_name":a["contact__last_name"],
                    "company": a["contact__company"],
                    "city": a["contact__city"],
                    "state": a["contact__state"],
                    "email": a["contact__email"],
                    "phone": a["contact__phone"],
                } for a in attendees]
            }

        else:
            context = {
                "success": False,
                "message": "You are not logged in",
                "action": "LOGOUT"
            }

        return HttpResponse(
            json.dumps(context),
            content_type='application/json')


# DONT THINK WE ARE USING THIS, SWITCHED TO
# ACTIVITY DETAILS WEBVIEW FOR THE APP
def activity_details_json(request, **kwargs):
    """
    returns activity details in json form
    for the published activity with master_id
    """
    is_authenticated, username = is_authenticated_check_all(request)
    context = {}
    master_id = kwargs['master_id']

    try:
        activity = Activity.objects.get(
            master__id=master_id,
            publish_status="PUBLISHED")
    except Activity.DoesNotExist:
        context = {
            "success": False,
            "message": "Error: Could not find any record for this Actvity"
        }
        return HttpResponse(
            json.dumps(context, cls=DjangoJSONEncoder),
            content_type='application/json')

    speaker_roles = ContactRole.objects.filter(
        content__master__id=master_id,
        confirmed=True,
        role_type="SPEAKER",
        content__publish_status="PUBLISHED")
    contenttagtypes = ContentTagType.objects.filter(
        content__master__id=master_id,
        content__publish_status="PUBLISHED")
    transit_contenttagtypes = contenttagtypes.filter(tag_type__code="TRANSIT")
    location_contenttagtypes = contenttagtypes.filter(tag_type__code="ROOM")

    speakers = [
        speaker_role.contact
        for speaker_role in speaker_roles
    ]
    tags = [
        tag
        for contenttagtype in contenttagtypes
        for tag in contenttagtype.tags.all()
    ]
    transit_codes = [
        tag.code
        for tag in transit_contenttagtypes[0].tags.all()
    ] if transit_contenttagtypes.exists() else []
    location_tags = [
        tag.code
        for tag in location_contenttagtypes[0].tags.all()
    ] if location_contenttagtypes.exists() else []

    # check if activity is on user's schedule
    if is_authenticated:
        user_contact = Contact.objects.get(user__username=username)
        activity_is_on_schedule = Attendee.objects.filter(
            contact=user_contact,
            event=activity,
            added_type='SCHEDULE').exists()
    else:
        activity_is_on_schedule = False

    # check if activity requires a ticket
    if ContentTagType.objects.filter(
            content__id=activity.id,
            tags__code__in=[
                "TRAINING_WORKSHOP",
                "INSTITUTE",
                "MOBILE_WORKSHOP",
                "ORIENTATION_TOUR",
                "SPECIAL_EVENT"
            ]).exists():
        activity_requires_ticket = True
    else:
        activity_requires_ticket = False

    context["success"] = True
    context["user_is_authenticated"] = is_authenticated
    context["activity"] = model_to_dict(
        activity,
        fields=[
            "title",
            "subtitle",
            "code",
            "begin_time",
            "end_time",
            "text",
            "cm_status",
            "cm_approved",
            "cm_law_approved",
            "cm_ethics_approved"
        ]
    )
    context["activity"]["speakers"] = [
        model_to_dict(speaker, fields=["title", "company", "bio"])
        for speaker in speakers
    ]
    context["activity"]["tags"] = [
        model_to_dict(tag, fields=["code", "title"])
        for tag in tags
    ]
    context["activity"]["is_on_schedule"] = activity_is_on_schedule
    context["activity"]["requires_ticket"] = activity_requires_ticket
    context["activity"]["location_tags"] = [
        model_to_dict(tag, fields=["code", "title"])
        for tag in location_tags
    ]
    context["activity"]["mobile_workshop_transit_codes"] = transit_codes

    # only want text. Not html tags.
    parser = html_parser.HTMLParser()
    context["activity"]["text"] = parser.unescape(
        strip_tags(context["activity"]["text"]))

    return HttpResponse(
        json.dumps(context, cls=DjangoJSONEncoder),
        content_type='application/json')
