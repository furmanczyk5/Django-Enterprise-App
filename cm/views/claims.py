from django.contrib import messages
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Q
from django.http.response import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.generic import TemplateView, FormView

from cm.forms import SelfReportClaimForm, AuthorClaimForm, ClaimBaseForm, \
    EventClaimForm, CMOnDemandSearchFilterForm, CMSearchFilterForm
from cm.models import Log, Claim,Period
from cm.utils import get_eval_status
from comments.forms import ExtendedEventEvaluationForm
from comments.models import ExtendedEventEvaluation
from comments.views import EventEvaluationConfirmationView
from conference.models import Microsite
from content.models import MessageText, MenuItem
from content.viewmixins import AppContentMixin
from content.views import LandingSearchView
from events.models import Event, NATIONAL_CONFERENCES
from learn.forms import LearnCourseEvaluationForm
from learn.models.learn_evaluation import LearnCourseEvaluation
from learn.utils.wcw_api_utils import WCWContactSync
from myapa.models.contact import Contact
from myapa.models.contact_role import ContactRole
from myapa.viewmixins import AuthenticateWebUserGroupMixin, \
    AuthenticateLoginMixin


class CMSearchView(LandingSearchView):
    """
    Search View for finding all cm events and ondemand courses
    """
    content_url="/cm/"
    hide_content = True
    title = "CM Search"
    record_template = "content/newtheme/search/record_templates/generic.html"
    template_name = "content/newtheme/search/results-cm.html"
    filters = ["content_type:EVENT",
        "event_type:(EVENT_SINGLE EVENT_MULTI COURSE LEARN_COURSE LEARN_COURSE_BUNDLE)"]
    FilterFormClass = CMSearchFilterForm
    show_content_type = False
    facets = []

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        contact = self.request.user.contact if not self.request.user.is_anonymous() else None
        the_log = contact.get_cm_log() if contact else None
        context["log_begin"] = the_log.begin_time if the_log else None
        context["is_candidate"] = contact.is_aicp_candidate() if contact else None
        context["is_aicp_cm"] = self.request.user.groups.filter(name="aicp-cm").exists()
        if context["is_aicp_cm"] and the_log:
            try:
                period_code = the_log.period.code
                message = MessageText.objects.get(code="CM_LOG_NOTIFICATION", status="A")
            except (Period.DoesNotExist, MessageText.DoesNotExist):
                period_code = None
            if period_code and period_code in ('JAN2021', 'JAN2022'):
                messages.add_message(self.request, message.message_level, message.text)

        context["is_reinstatement_cm"] = self.request.user.groups.filter(name="reinstatement-cm").exists()
        context["is_cm_search_result"] = True
        return context


class CMLiveEventSearchView(CMSearchView):
    """
    Search View for finding single and multi events (cm and non-cm accrdited)
    """
    title = "CM Live Event Search"
    filters = ["content_type:EVENT", "event_type:(EVENT_SINGLE EVENT_MULTI)"]
    content_url="/cm/"


class CMOnDemandSearchView(CMSearchView):
    """
    Search View for finding single and multi events (cm and non-cm accrdited)
    """
    title = "CM On Demand Course Search"
    filters = ["content_type:EVENT", "event_type:COURSE"]
    FilterFormClass = CMOnDemandSearchFilterForm
    content_url="/cm/"


class LogView(AuthenticateLoginMixin, AppContentMixin, TemplateView):
    # authenticate_group = "aicp_cm" # NOTE: no longer using this group to check for access... instead we're looking for the existence of the log records (below)
    content_url="/cm/log/"
    template_name = "cm/newtheme/log.html"
    contact = None
    log = None
    overview = None
    all_logs = None
    claims = None
    microsite = None
    conf_menu_query = None

    def setup(self, request, *args, **kwargs):
        self.contact = Contact.objects.get(user__username=self.username)
        self.all_logs = Log.objects.filter(contact=self.contact).select_related("period").order_by("period__begin_time")

        if "period_code" in kwargs:
            self.log = self.all_logs.filter(period__code=kwargs["period_code"]).first()
        else:
            self.log = self.all_logs.filter(is_current=True).first()

        if self.log:
            self.overview = self.log.credits_overview()
            self.claims = Claim.objects.filter(
                log=self.log,
                is_deleted=False
            ).select_related(
                "comment"
            ).order_by(
                "-is_carryover",
                "-begin_time"
            )

    def get(self, request, *args, **kwargs):
        self.setup(request, *args, **kwargs)
        self.set_microsite(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):

        contact = self.contact
        context = super().get_context_data(**kwargs)
        context["contact"] = contact
        context["is_candidate"] = contact.is_aicp_candidate() if contact else None

        # if self.log.status == "G":
        #     MessageText.add_message(self.request, "GRACE_PERIOD_MESSAGE")

        # TO DO... this should be refactored so that all these messages simply run through MesageText.set_content_messages

        if self.log:
            if self.log.status == "G":
                MessageText.add_message(self.request, "GRACE_PERIOD_MESSAGE")

            context["log"] = self.log
            context['is_closed_dt'] = self.log.period.end_time.replace(microsecond=0, second=0, tzinfo=None) \
                < timezone.now().replace(microsecond=0, second=0, tzinfo=None)
            context["all_logs"] = self.all_logs
            context["log_overview"] = self.overview
            context["claims"] = self.claims

        elif len(self.all_logs) == 0:
            MessageText.set_content_messages(context, ("NO_ACTIVE_CM_LOG",))


        if self.request.detect_mobile_app.get("is_mobileapp", False):
            context["extends_template"] = "newtheme/templates/mobile-app.html"

        MessageText.set_content_messages(context, ("CM_LOG_INTRO",) )

        context["conference_menu"] = self.conf_menu_query
        context["microsite"] = self.microsite
        # FLAGGED FOR REFACTORING: CM CONSOLIDATION
        # need logic here to set the correct phase of cm consolidation
        # these won't be need once transitional phase is over
        # the logic here should depend, at least partly, on the CM reporting period.
        # transitional (coming soon) will show on logs with reporting period jan2024 and beyond
        # at time of launch (Dec 2020 or June 2021)
        # COMMENT THIS IN FOR PROD DEPLOY:
        # if self.log.period.code == 'JAN2024':
        #     context["transitional_period"] = True
        #     context["future_period"] = False
        # for local testing without period condition -- REMOVE THIS FOR PROD DEPLOY:
        context["transitional_period"] = True
        context["future_period"] = False

        return context

    def post(self, request, *args, **kwargs):
        self.setup(request, *args, **kwargs)
        if "close" in request.POST:
            new_log = self.log.close_and_rollover(contact=self.contact, overview=self.overview)
            messages.success(request, "Your " + self.log.period.title + " period has been successfully completed and closed.")

            return HttpResponseRedirect(reverse('cm:log_view', kwargs={'period_code': new_log.period.code}))
        return super().get(request, *args, **kwargs)

    def set_microsite(self, request, *args, **kwargs):
        microsite = Microsite.get_microsite( self.request.get_full_path() )

        if microsite:
            # means we are in a conf microsite (not incl npc)
            self.conf_menu_query = MenuItem.get_root_menu(landing_code=microsite.home_page_code)
            self.microsite = microsite
        else:
            self.conf_menu_query = None


class ClaimDeleteView(AuthenticateWebUserGroupMixin, FormView):
    authenticate_groups = ["aicp-cm", "reinstatement-cm", "candidate-cm"]
    authenticate_groups_message_code = "NO_ACTIVE_CM_LOG"

    def get(self, request, *args, **kwargs):
        claim = Claim.objects.select_related("log").get(contact=request.user.contact, id=kwargs["claim_id"])
        event = claim.event

        if event:
            eval_status = get_eval_status(event, request.user.contact)
            log = eval_status.get("current_log")
            can_delete = eval_status.get("evaluation_action") == "CLAIM_CM" # If you can edit the claim, you can delete it

            if can_delete:
                pass
        else:
            log = claim.log
            can_delete = log.is_active() # if the log tied to the claim is active, you can delete the claim

        if can_delete:
            if claim.comment:
                claim.comment.is_deleted = True
                claim.comment.save()
            claim.is_deleted = True
            claim.save()
            # log.post_cm_log()
            messages.success(request, "Claim deleted.")

            if event:
                event.recalculate_rating()

        else:
            messages.info(request, "You cannot edit or delete claims that are outside of your current logging period")

        return redirect("cm:log")


class ClaimFormBaseView(AuthenticateWebUserGroupMixin, TemplateView):
    """
    base view for the form for logging CM credits... used for events/on-demand, author, or self-report
        Note: Using TemplateView because models inheriting from this will use multiple forms
            This view mocs the generic FormView, allows for multiple forms
        Another Note: Consider creating inheritable class based view, MultiFormView, for multi-form views.
            This seems to come up often
    """
    content_url = "/cm/log/"
    authenticate_groups = ["aicp-cm", "reinstatement-cm", "candidate-cm"]
    authenticate_groups_message_code = "NO_ACTIVE_CM_LOG"
    claim_form_class = ClaimBaseForm
    template_name = None  # defined on inherited views
    success_url = reverse_lazy("cm:log")
    microsite = None
    conf_menu_query = None

    def get_restrictions_response(self):
        """
        method for catching claims outside of current logging period,
        If user is clear to edit or create claim, returns None
            else this returns a response
        """
        contact = self.request.contact
        is_candidate = contact.is_aicp_candidate() if contact else None

        if self.claim and not self.claim.log.is_active():
            messages.info(self.request, "You cannot edit this claim, it is outside of your current logging window")
            return redirect("cm:log")
        elif is_candidate:
            messages.info(self.request, "AICP Candidates are not eligible for self-reporting or authoring credits.")
            return redirect("cm:log") # should direct to readonly view of claim
        else:
            return None

    # TemplateView methods
    def get(self, request, *args, **kwargs):
        self.setup(*args, **kwargs)
        self.set_microsite(request, *args, **kwargs)
        restrictions_response = self.get_restrictions_response()
        if restrictions_response:
            return restrictions_response
        self.set_forms()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.setup(*args, **kwargs)
        restrictions_response = self.get_restrictions_response()
        if restrictions_response:
            return restrictions_response
        self.set_forms()

        if self.is_form_valid():
            return self.form_valid()
        else:
            return self.form_invalid()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            "contact":self.contact,
            "log":self.log,
            "log_overview":self.log.credits_overview if self.log else None,
            "claim":self.claim,
            "claim_form":self.claim_form
        })
        context["conference_menu"] = self.conf_menu_query
        context["microsite"] = self.microsite
        return context

    # Custom methods
    def get_claim(self, *args, **kwargs):
        """Hook method to override how the claim is queried"""
        claim_id = self.kwargs.get("claim_id", None)
        claim = Claim.objects.filter(contact=self.request.user.contact, id=claim_id, is_deleted=False).first() if claim_id else None
        return claim

    def setup(self, *args, **kwargs):
        """Place to put common setup logic, shared between get and post methods"""
        self.contact = self.request.user.contact
        self.log = Log.objects.filter(contact=self.contact, is_current=True).select_related("period").first()
        self.claim = self.get_claim()

    def set_forms(self, *args, **kwargs):
        """Similar to FormView's get_form method, but sets the forms on properties of view, does not return the form instance"""
        self.claim_form = self.claim_form_class(self.request.POST or None,
            prefix="claimform",
            instance=self.claim,
            initial=self.get_claim_form_initial())

    def get_claim_form_initial(self):
        """returns initial values for the claim_form"""
        return dict(log=self.log, contact=self.contact)

    def is_form_valid(self):
        """determines if forms are valid, returns true if valid"""
        return self.claim_form.is_valid()

    def form_valid(self):
        """is called when forms are valid"""
        self.claim_form.save()
        messages.success(self.request, 'Successfully submitted your claim.')
        return redirect(self.get_success_url())

    def form_invalid(self):
        """is called when forms are not valid"""
        messages.error(self.request, "Could not submit your claim. Please correct the changes below and resubmit.")
        return self.render_to_response(self.get_context_data())

    def get_success_url(self):
        """returns the url ro redirect to on success"""
        return self.success_url

    def set_microsite(self, request, *args, **kwargs):
        microsite = Microsite.get_microsite( self.request.get_full_path() )

        if microsite:
            # means we are in a conf microsite (not incl npc)
            self.conf_menu_query = MenuItem.get_root_menu(landing_code=microsite.home_page_code)
            self.microsite = microsite
        else:
            self.conf_menu_query = None


class EventClaimFormView(ClaimFormBaseView):
    template_name="cm/newtheme/extended-event-claim-form.html"
    comment_form_class = ExtendedEventEvaluationForm
    claim_form_class = EventClaimForm
    is_apa_learn = False
    not_complete_url = "/cm/search/"
    course_completed = True
    course_eval = None

    def get_restrictions_response(self):
        eval_status = get_eval_status(self.event, self.contact)
        action = eval_status.get("evaluation_action", None)
        if action and action == "CLAIM_CM":
            # case where user is AICP member, and event or existing claim is within reporting period...
            return None
        else:
            # case where user is not AICP, or event falls outside of reporting period, or event already logged in another reporting period...
            # then redirect with message (see util.get_eval_status for logic for determining msg and redirect)
            current_log_is_active = eval_status.get("log_is_active", None)
            evaluation_message = eval_status.get("evaluation_message", None)
            evaluation_url = eval_status.get("evaluation_url", "/events/event/%s/" % self.event.master_id) # default to event details?
            evaluation_html = eval_status.get("evaluation_html", None)

            if evaluation_message:
                messages.info(self.request, evaluation_message)

            if not current_log_is_active and evaluation_html:
                # IF you are on this page and you don't have an active log,
                # then you should see special restriction page before evaluating event
                return render(self.request, "cm/newtheme/claim-restricted-access.html", context=dict(evaluation_url=evaluation_url, message=evaluation_html))
            else:
                return redirect(evaluation_url)

    def get_claim(self, *args, **kwargs):
        claim = Claim.objects.filter(contact=self.request.user.contact, event=self.event, is_deleted=False).first() if self.event else None
        return claim

    def get(self, request, *args, **kwargs):
        # kwargs = kwargs.update({"learn_log_url": "EVENT"})
        return_val = super().get(request, *args, **kwargs)

        if self.is_apa_learn and not self.course_completed:
            messages.warning(self.request, "You cannot log/evaluate this education until it is complete.")
            return redirect(self.not_complete_url)

        return return_val

    def setup(self, *args, **kwargs):
        self.contact = self.request.user.contact
        master_id = self.kwargs.get("master_id", None)
        self.event = Event.objects.prefetch_related("contactrole__contact").get(master__id = master_id, publish_status="PUBLISHED")

        if self.event and self.event.event_type in ("LEARN_COURSE", "LEARN_COURSE_BUNDLE"):
            self.course_completed = False
            self.is_apa_learn = True
            wcw_contact_sync = WCWContactSync(self.contact)
            # product_code = str(self.event.code)
            wcw_contact_sync.pull_course_completions_from_wcw() # TO DO: able to pull by product code?

            self.course_eval = LearnCourseEvaluation.objects.filter(contact=self.contact, content__master_id=master_id).first()
            if self.course_eval:
                self.course_completed = True

        self.use_extended_evaluation = ContactRole.objects.filter(role_type="PROVIDER", contact__user__username='119523').filter(
            Q(content_id=self.event.id) | Q(content__master__children__id=self.event.id)).exists() or \
            (self.event.parent and self.event.parent.content_live and self.event.parent.content_live.code in [conf[0] for conf in NATIONAL_CONFERENCES])
        super().setup(*args, **kwargs)

    def set_form_classes(self):

        if self.is_apa_learn:
            self.comment_form_class = LearnCourseEvaluationForm
            self.comment_model = LearnCourseEvaluation
            self.claim_form_class = EventClaimForm
        elif self.use_extended_evaluation:
            self.comment_form_class = ExtendedEventEvaluationForm
            self.comment_model = ExtendedEventEvaluation
        else:
            self.comment_form_class = ExtendedEventEvaluationForm
            self.comment_model = ExtendedEventEvaluation

    def set_forms(self, *args, **kwargs):

        self.set_form_classes()

        if self.claim:
            self.claim.comment = self.comment_model.objects.filter(contact=self.contact, content=self.event).first()
        super().set_forms(*args, **kwargs)

        self.comment_form = self.comment_form_class(self.request.POST or None,
            prefix="commentform",
            instance=self.course_eval or (self.claim.comment if self.claim else None),
            initial=dict(contact=self.contact, content=self.event))

    def get_claim_form_initial(self):
        initial = super().get_claim_form_initial()
        initial["event"] = self.event
        return initial

    def is_form_valid(self):
        return super().is_form_valid() and self.comment_form.is_valid()

    def form_valid(self):
        claim = self.claim_form.save(commit=False)
        comment = self.comment_form.save()
        claim.comment = comment
        claim.save()
        self.show_success_message()
        return redirect(self.get_success_url())

    def show_success_message(self):
        if self.request.detect_mobile_app.get("is_mobileapp", False):
            pass # Dont need this on mobile app
        elif self.event.event_type == "ACTIVITY":
            parent_event_master = self.event.parent
            # parent_event = parent_event_master.content_live
            parent_event = Event.objects.filter(master=self.event.parent, publish_status='PUBLISHED').first()
            messages.success(self.request, '''Successfully submitted your claim.<br/><br/>
                <a href="/events/eventmulti/%s/"><strong>LOG MORE ACTIVITIES FROM: %s</strong></a>''' % (parent_event_master.id, parent_event.title))
        elif self.event.event_type == "LEARN_COURSE":
            messages.success(self.request, '''You successfully logged your CM credits.<br/><br/>
                <a href="https://learn.planning.org/my/"><strong>Return to APA Learn.</strong></a>''')
        else:
            messages.success(self.request, 'Successfully submitted your claim.</a>')

    def get_template_names(self):
        if self.is_apa_learn:
            return "learn/newtheme/learn-course-claim-form.html"
        elif self.use_extended_evaluation:
            return "cm/newtheme/extended-event-claim-form.html"
        else:
            return super().get_template_names()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            "event":self.event,
            "comment_form":self.comment_form,
        })

        if self.request.detect_mobile_app.get("is_mobileapp", False):
            context["extends_template"] = "newtheme/templates/mobile-app.html"

        return context

    def get_success_url(self):
        if self.request.detect_mobile_app.get("is_mobileapp", False):
            return reverse("mobile:cm:event_claim_confirmation", kwargs=dict(master_id=self.event.master_id))
        else:
            return super().get_success_url()


class EventClaimConfirmationView(EventEvaluationConfirmationView):
    title = "CM Claim Submitted"
    message = "Thank you for submitting your CM Claim!"


class AuthorClaimFormView(ClaimFormBaseView):#render the other view for new template_
    template_name="cm/newtheme/author-claim-form.html"
    claim_form_class = AuthorClaimForm


class SelfReportClaimFormView(ClaimFormBaseView):#render the other view for new template_
    template_name="cm/newtheme/selfreport-claim-form.html"
    claim_form_class = SelfReportClaimForm


class ClaimDetailsView(AuthenticateLoginMixin, TemplateView):
    """
    View for submitted claims that can no longer be edited
    """
    template_name = "cm/newtheme/claim-details.html"

    def get(self, request, *args, **kwargs):
        claim_id = kwargs.get("claim_id")
        self.claim = Claim.objects.select_related("comment", "event", "log__period").filter(id=claim_id).first()
        if self.claim.event:
            self.provider_roles = ContactRole.objects.filter(content=self.claim.event, role_type="PROVIDER")
        else:
            self.provider_roles = None

        if self.claim.contact_id == request.user.contact.id:
            return super().get(request, *args, **kwargs)
        else:
            messages.error(request, "You do not have permissions to view this claim")
            return redirect("cm:log")

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["claim"] = self.claim
        context["provider_roles"] = self.provider_roles
        return context
