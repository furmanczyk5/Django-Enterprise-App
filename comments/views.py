from django.shortcuts import redirect
from django.views.generic import TemplateView, View
from django.forms import modelformset_factory
from django.contrib import messages
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.http import Http404

from content.models import MenuItem
from myapa.models.contact_role import ContactRole
from myapa.viewmixins import AuthenticateLoginMixin
from events.models import Event, NATIONAL_CONFERENCES, NATIONAL_CONFERENCE_CURRENT
from cm.utils import get_eval_status
from conference.models import Microsite
from learn.models.learn_evaluation import LearnCourseEvaluation
from learn.forms import LearnCourseEvaluationForm
from learn.utils.wcw_api_utils import WCWContactSync

from .models import EventComment, ExtendedEventEvaluation
from .forms import ExtendedEventEvaluationForm#EventCommentForm,


class CadmiumEventEvaluationRedirectView(View):

    def get(self, request, *args, **kwargs):
        cadmium_key = self.kwargs.get("cadmium_key", 0)
        event = Event.objects.filter(
            external_key=cadmium_key,
            publish_status="PUBLISHED",
            status__in=("A","H"),
            parent__content_live__code=NATIONAL_CONFERENCE_CURRENT[0],
            ).first()
        if not event:
            raise Http404
        redirect_url = "/events/%s/evaluation/" % event.master.id
        # redirect_url = "/cm/log/claim/event/%s/" % event.master.id
        return redirect(redirect_url)

class EventEvaluationFormView(AuthenticateLoginMixin, TemplateView):

    # need to check that event has started...
    # ...also, need to check for existing claim, or if aicp and falls within reporting period...
    #    ...or sort this out in the routing view?
    template_name = "comments/newtheme/extended-event-evaluation-form.html"
    success_url = "/{app_label}/{model_name}/{master_id}/"
    comment_form_class = ExtendedEventEvaluationForm
    is_apa_learn = False
    course_completed = True
    course_eval = None
    not_complete_url = "/cm/search/"

    def get_restrictions_response(self):
        eval_status = get_eval_status(self.event, self.contact)
        action = eval_status.get("evaluation_action", None)
        if action and action == "EVALUATE":
            return None
        else:
            evaluation_message = eval_status.get("evaluation_message", None)
            evaluation_url = eval_status.get("evaluation_url", "/events/event/%s/" % self.event.master_id) # default to event details?
            if evaluation_message:
                messages.info(self.request, evaluation_message)
            return redirect(evaluation_url)

    # TemplateView methods
    def get(self, request, *args, **kwargs):
        self.setup(*args, **kwargs)
        restrictions_response = self.get_restrictions_response()
        if restrictions_response:
            return restrictions_response
        self.set_forms()

        if not self.course_completed:
            messages.warning(self.request, "You cannot log/evaluate this education until it is complete.")
            return redirect(self.not_complete_url)

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

    def get_template_names(self):
        if self.use_extended_evaluation:
            return "comments/newtheme/extended-event-evaluation-form.html"
        else:
            return super().get_template_names()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            "contact":self.contact,
            "event":self.event,
            "comment_form":self.comment_form,
            "comment":self.comment,
        })
        return context

    # custom methods
    def setup(self, *args, **kwargs):
        """Place to put common setup logic, shared between get and post methods"""
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

    def set_form_classes(self):

        if self.is_apa_learn:
            self.comment_form_class = LearnCourseEvaluationForm
            self.comment_model = LearnCourseEvaluation
        elif self.use_extended_evaluation:
            self.comment_form_class = ExtendedEventEvaluationForm
            self.comment_model = ExtendedEventEvaluation
        else:
            self.comment_form_class = ExtendedEventEvaluationForm
            self.comment_model = ExtendedEventEvaluation

    def set_forms(self, *args, **kwargs):

        self.set_form_classes()
        self.comment = self.comment_model.objects.filter(contact=self.contact, content=self.event).first()
        self.comment_form = self.comment_form_class(self.request.POST or None,
            prefix="commentform",
            instance=self.comment if not self.course_eval else self.course_eval,
            initial=dict(contact=self.contact, content=self.event))

    def is_form_valid(self):
        return self.comment_form.is_valid()

    def form_valid(self):
        """is called when forms are valid"""
        self.comment_form.save()
        self.show_success_message()
        return redirect(self.get_success_url())

    def form_invalid(self):
        """is called when forms are not valid"""
        messages.error(self.request, "Could not submit your evaluation. Please correct the changes below and resubmit.")
        return self.render_to_response(self.get_context_data())

    def show_success_message(self):
        if not self.request.detect_mobile_app.get("is_mobileapp", False):
            if self.event.event_type == "LEARN_COURSE":
                messages.success(self.request, '''You successfully submitted your evaluation.<br/><br/>
                    <a href="https://learn.planning.org/my/"><strong>Return to APA Learn.</strong></a>''')
            else:
                messages.success(self.request, "You successfully submitted your evaluation.")

    def get_success_url(self):
        """returns the url ro redirect to on success"""
        if self.request.detect_mobile_app.get("is_mobileapp", False):
            return reverse("mobile:event_evaluation_confirmation", kwargs=dict(master_id=self.event.master_id))
        elif not self.request.user.groups.filter(name="aicp-cm").exists():
            return "/myapa/"
        else:
            EventClass = self.event.get_proxymodel_class()
            return self.success_url.format(app_label=EventClass._meta.app_label, model_name=EventClass._meta.model_name, master_id=self.event.master_id)

class EventEvaluationDeleteView(AuthenticateLoginMixin, View):

    def get(self, request, *args, **kwargs):
        master_id = kwargs.get("master_id")
        event = Event.objects.filter(master_id=master_id, publish_status="PUBLISHED").first()
        EventClass = event.get_proxymodel_class()
        comment_to_delete = EventComment.objects.filter(is_deleted=False, content=event, contact=request.user.contact) # using EventComment should make sure that this is not a for a claim
        if comment_to_delete:
            comment_to_delete.delete()
            messages.success(request, "Successfully deleted your Rating and Comments for %s" % event)
        else:
            messages.error(request, "Could not delete your rating and comments because they could not be found")
        return redirect("/{0}/{1}/{2}/".format(EventClass._meta.app_label, EventClass._meta.model_name, master_id))


class EventEvaluationConfirmationView(AuthenticateLoginMixin, TemplateView):

    template_name = "comments/newtheme/event-evaluation-confirmation.html"
    title = "Evaluation Complete"
    message = "Thank you for submitting your evaluation!"
    microsite = None
    conf_menu_query = None

    def get(self, request, *args, **kwargs):
        master_id = kwargs.get("master_id")
        self.event = Event.objects.filter(master_id=master_id, publish_status="PUBLISHED").first()
        self.event.__class__ = self.event.get_proxymodel_class()
        self.set_microsite(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["title"] = self.title
        context["event"] = self.event
        context["message"] = self.message

        if self.request.detect_mobile_app.get("is_mobileapp", False):
            context["extends_template"] = "newtheme/templates/mobile-app.html"

        context["conference_menu"] = self.conf_menu_query
        context["microsite"] = self.microsite

        return context

    def set_microsite(self, request, *args, **kwargs):
        microsite = Microsite.get_microsite( self.request.get_full_path() )

        if microsite:
            # means we are in a conf microsite (not incl npc)
            self.conf_menu_query = MenuItem.get_root_menu(landing_code=microsite.home_page_code)
            self.microsite = microsite
        else:
            self.conf_menu_query = None






