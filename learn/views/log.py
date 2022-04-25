from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import Q

from myapa.viewmixins import AuthenticateLoginMixin
from content.viewmixins import AppContentMixin
from content.models.content_relationship import ContentRelationship
from cm.models import Claim#, Log, Period
from cm.forms.claims import EventClaimForm
from cm.views.claims import EventClaimFormView
from exam.models import ExamApplication, ENROLLED_STATUSES
from comments.views import EventEvaluationFormView, EventEvaluationDeleteView, \
    EventEvaluationConfirmationView

from learn.models.learn_evaluation import LearnCourseEvaluation
from learn.forms import LearnCourseEvaluationForm
from learn.utils.wcw_api_utils import WCWContactSync


def hide_learn_course_eval(course_eval):
    if course_eval:
        comm = course_eval.commentary
        comm = '' if not comm else comm
        if comm.find("HIDDEN_LEARN_COURSE") < 0:
            course_eval.commentary = comm + "HIDDEN_LEARN_COURSE"
            course_eval.save()


class LearnCourseCompletedView(AuthenticateLoginMixin, AppContentMixin, TemplateView):
    """
    Lists APA Learn Courses that a contact (user) has finished and can be logged.
    """
    template_name = "learn/newtheme/completed-courses.html"
    content_url = "learn/apa-learn-courses"

    def get(self, request, *args, **kwargs):

        eval_id = self.request.GET.get('hide_course', '')

        try:
            course_eval = LearnCourseEvaluation.objects.get(id=eval_id)
        except:
            course_eval = None

        if course_eval:
            hide_learn_course_eval(course_eval)

        wcw_contact_sync = WCWContactSync(request.user.contact)
        wcw_contact_sync.pull_course_completions_from_wcw()

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        user = self.request.user
        contact = user.contact if not user.is_anonymous() else None

        context["course_evals"] = LearnCourseEvaluation.objects.filter(
            contact=contact, submitted_time__isnull=False
            ).exclude(commentary__contains="HIDDEN_LEARN_COURSE"
                ).order_by('-submitted_time')

        the_log = contact.get_cm_log() if contact else None

        context["log_begin"] = the_log.begin_time if the_log else None
        context["is_candidate"] = contact.is_aicp_candidate() if contact else None
        context["is_aicp_cm"] = self.request.user.groups.filter(name="aicp-cm").exists()
        context["is_reinstatement_cm"] = self.request.user.groups.filter(name="reinstatement-cm").exists()
        # context["is_cm_search_result"] = True

        return context

class LearnCourseHiddenView(AuthenticateLoginMixin, AppContentMixin, TemplateView):
    """
    Django Template View to show APA Learn Courses hidden from pending list
    by users. Allows them to "unhide" these courses.
    """
    template_name = "learn/newtheme/hidden-courses.html"
    content_url = "/learn/hidden-pending-courses/"

    def get(self, request, *args, **kwargs):

        eval_id = self.request.GET.get('unhide_course', '')

        try:
            course_eval = LearnCourseEvaluation.objects.get(id=eval_id)
        except:
            course_eval = None

        if course_eval:
            comm = course_eval.commentary
            comm = '' if not comm else comm
            if comm.find("HIDDEN_LEARN_COURSE") >= 0:
                course_eval.commentary = comm.replace("HIDDEN_LEARN_COURSE", "")
                course_eval.save()

        wcw_contact_sync = WCWContactSync(request.user.contact)
        wcw_contact_sync.pull_course_completions_from_wcw()

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        contact = self.request.user.contact if not self.request.user.is_anonymous() else None

        context["hidden_course_evals"] = LearnCourseEvaluation.objects.filter(
            contact=contact, submitted_time__isnull=False,
            commentary__contains="HIDDEN_LEARN_COURSE"
            ).order_by('-submitted_time')

        return context
