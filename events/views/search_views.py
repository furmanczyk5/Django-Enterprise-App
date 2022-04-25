import datetime
import pytz

from django.shortcuts import redirect
from django.views.generic import View
from django.contrib import messages
from django.utils import timezone
from django.db.utils import ProgrammingError
from django.http import Http404

from myapa.viewmixins import AuthenticateLoginMixin
from content.views import LandingSearchView

from store.models import Purchase

from events.forms import CalendarSearchForm, OnDemandSearchFilterForm, EventMultiSearchForm
from events.models import Event, EventMulti, NATIONAL_CONFERENCE_MASTER_ID

# from exam.models import ExamApplication, ENROLLED_STATUSES
# from cm.models import Log, Period


class ProfessionalDevelopmentSearchView(LandingSearchView):
    title = "Start Exploring the APA Learning Subscription"
    content_url = "/access/"
    filters = ["tags_FORMAT:1916*",]
    facets = ["tags_SEARCH_TOPIC"]
    record_template = "content/newtheme/search/record_templates/professional-development.html"
    rows = 20


class CalendarSearchView(LandingSearchView):
    title = "APA Events"
    content_url = "/events/"
    filters = ["content_type:EVENT", "event_type:(EVENT_SINGLE EVENT_MULTI)", "end_time:[NOW TO *]", "is_apa:true"]
    FilterFormClass = CalendarSearchForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        contact = self.request.user.contact if not self.request.user.is_anonymous() else None
        the_log = contact.get_cm_log() if contact else None
        context["log_begin"] = the_log.begin_time if the_log else None
        context["is_candidate"] = contact.is_aicp_candidate() if contact else None
        context["is_aicp_cm"] = self.request.user.groups.filter(name="aicp-cm").exists()
        context["is_reinstatement_cm"] = self.request.user.groups.filter(name="reinstatement-cm").exists()
        context["is_cm_search_result"] = True
        return context


class OnDemandSearchView(LandingSearchView):
    now = timezone.now()
    current_conference_year = now.year
    try:
        current_conference = Event.objects.filter(master_id=NATIONAL_CONFERENCE_MASTER_ID, publish_status="DRAFT").first()
        if current_conference:
            current_conference_year = current_conference.begin_time.year
    # The query for the NPC Event above gets evaluated at runtime, which raises
    # a django.db.utils.ProgrammingError if migrations have not been run (e.g., when
    # creating a fresh test database)
    except ProgrammingError:
        pass
    year_before_conference = current_conference_year - 1
    tz = pytz.timezone("US/Central")
    jan1_of_year_before_conference = tz.localize(datetime.datetime(year_before_conference, 1, 1), is_dst=None)
    jan1_of_year_before_conference_json = jan1_of_year_before_conference.strftime('%Y-%m-%dT%H:%M:%SZ')

    show_content_type = False
    title = "Search On-demand Education"
    content_url = "/ondemand/"
    filters = ["event_type:(COURSE LEARN_COURSE LEARN_COURSE_BUNDLE) AND has_product:true AND begin_time:[%s TO *]" % jan1_of_year_before_conference_json]
    hide_content = False
    FilterFormClass = OnDemandSearchFilterForm


class OnDemandSaleSearchView(LandingSearchView):
    show_content_type = False
    title = "Search On Demand Education Sale Sessions"
    content_url = "/ondemand/sale/"
    filters = ["event_type:COURSE AND has_product:true AND (tags_CONTENT_FEATURED:1394.* OR tags_CONTENT_FEATURED:1392.*)"]
    hide_content = False
    FilterFormClass = OnDemandSearchFilterForm


class OnDemandNPC17SearchView(LandingSearchView):
    show_content_type = False
    title = "Search NPC17 On Demand Education"
    content_url = "/ondemand/npc17/"
    filters = ["event_type:COURSE AND has_product:true AND tags_CONTENT_FEATURED:1766.*"]
    hide_content = False
    FilterFormClass = OnDemandSearchFilterForm


class OnDemandActivateView(AuthenticateLoginMixin, View):

    def get(self, request, *args, **kwargs):
        master_id = kwargs.get("master_id", None)
        return redirect("ondemand_details", master_id=master_id)

    def post(self, request, *args, **kwargs):
        master_id = kwargs.get("master_id", None)
        purchase = Purchase.objects.select_related("product__content").exclude(order__isnull=True).filter(product__content__master_id=master_id, contact__user__username=self.username, status="A").order_by("-expiration_time").first()

        if not purchase:
            messages.error(request, "Could not find any records of your purchase for this product")
        if purchase.is_expired():
            messages.info(request, "Your viewing period for this purchase has already expired")
        elif purchase.expiration_time:
            messages.info(request, "Your purchase has already been activated. Your viewing period will expire %s" % purchase.expiration_time.strftime("%b %d, %Y"))
        else:
            expiration_time = purchase.activate_to_expire()
            messages.success(request, "Successfully activated this product. Your viewing period will expire %s" % expiration_time.strftime("%b %d, %Y"))

        return redirect("ondemand_details", master_id=master_id)


class EventMultiDetailsView(LandingSearchView):

    template_name = "events/newtheme/eventmulti-details.html"
    record_template = "content/newtheme/search/record_templates/event.html"
    event_multi = None
    master_id = None
    FilterFormClass = EventMultiSearchForm

    def get(self, request, *args, **kwargs):
        self.master_id = kwargs.get('master_id', None)
        self.event_multi = EventMulti.objects.with_details().filter(
            status__in=('A', 'H'),
            publish_status='PUBLISHED',
            master_id=self.master_id
        ).first()
        if self.event_multi is None:
            raise Http404("Event not found")
        return super().get(request, *args, **kwargs)

    def get_filters(self):
        filters = [
            "(parent:{} AND event_type:ACTIVITY)".format(self.master_id)
        ]
        return filters

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['content'] = self.event_multi
        context['event'] = self.event_multi
        context["is_aicp_cm"] = self.request.user.groups.filter(name="aicp-cm").exists()
        context["is_reinstatement_cm"] = self.request.user.groups.filter(name="reinstatement-cm").exists()

        contact = None
        if self.request.user.is_authenticated:
            contact = getattr(self.request.user, "contact", None)

        the_log = contact.get_cm_log() if contact else None
        context["log_begin"] = the_log.begin_time if the_log else None
        context['ancestors'] = self.event_multi.get_landing_ancestors()
        return context
