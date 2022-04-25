import datetime
import string

from django import forms
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q, Prefetch
from django.forms import formset_factory
from django.forms.models import modelformset_factory
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.encoding import force_text
from django.views.generic import FormView, TemplateView

from cm.models import Period, Log
from content.mail import Mail
from content.viewmixins import AppContentMixin
from imis.models import CustomSchoolaccredited
from myapa.models.constants import DEGREE_LEVELS
from myapa.models.contact import Contact
from myapa.models.proxies import School
from myapa.viewmixins import AuthenticateLoginMixin, AuthenticateMemberMixin, \
    AuthenticateWebUserGroupMixin
from store.models import ProductCart, Purchase
from submissions.models import Answer
from submissions.views import SubmissionEditFormView, SubmissionDetailsView
from uploads.models import Upload, UploadType
from .admin import CAND_ENROLL_EMAIL_TEMPLATES, CAND_ENROLL_APP_TYPES, CAND_CERT_APP_TYPES
from .forms import ExamApplicationMCIPSubmitForm, ExamApplicationReviewForm, \
    ExamAnswerReviewForm, ExamApplicationTypeForm, ExamSummaryForm, \
    ExamApplicationCodeOfEthicsForm, ExamCriteriaForm, ExamDegreeHistoryForm, \
    ExamJobHistoryForm, ExamRegistrationForm, ExamCodeOfEthicsForm, \
    ExamRegistrationSearchForm, ASCExamCriteriaForm, ASCExamJobHistoryForm, \
    AICPCandidateBasicInfoForm, AICPCandidateEducationForm
from .models import Exam, ExamApplication, ExamRegistration, \
    ApplicationDegree, ApplicationJobHistory, VerificationDocument, \
    ExamApplicationReview, ApplicationCategory, APPLICATION_TYPES, \
    APPLICATION_STATUSES, APPROVAL_PROCESS_STATUSES, PRE_APPROVED_REG_TYPE_LIST, \
    DENIED_STATUSES_LIST, ADVANCED_APPLICATION_TYPES, HIGHEST_REQUIRED_EXPERIENCE, \
    APP_TYPE_TO_EMAIL_CODE, SKIP_APP_TYPES, REGULAR_APPLICATION_TYPES, \
    CANDIDATE_REGISTRATION_TYPES, APPROVED_STATUSES

CAND_PORTAL_ACCESS_STATUSES = ['N', 'EN']
CAND_REG_TYPES = ["CAND_ENR_A", "CAND_T_0", "CAND_T_100"]


class CandidatePortalAccessMixin(object):
    """
    A current or former AICP Candidate will always have an approved CAND application. In both
    cases they are excluded from the portal.
    """

    def validate_aicp(self):
        is_aicp = self.request.user.groups.filter(name='aicpmember').exists()
        imis_subs = self.contact.get_imis_subscriptions()
        aicp_sub = False
        if imis_subs.exists():
            aicp_sub = imis_subs.filter(product_code="AICP").exists()
        was_aicp = True if aicp_sub else False

        if is_aicp or was_aicp:
            messages.error(self.request, "Current and former AICP members are not eligible for the AICP Candidate Program.")
            self.success_url = "/aicp/candidate/"

    def validate_status(self, app_status):
        # if app_status == 'PE':
        #     messages.warning(self.request, "Your student enrollment application was submitted and is currently under review.")
        #     self.success_url = "/aicp/candidate/"
        if app_status == 'P':
            messages.warning(self.request, "Your enrollment application was submitted/updated and is currently under review.")
            self.success_url = "/aicp/candidate/"
        elif app_status in APPROVED_STATUSES:
            messages.success(self.request, "You have an approved enrollment application on record. You are already eligible to register for the AICP Exam.")
            self.success_url = "/aicp/candidate/"
        elif app_status in CAND_PORTAL_ACCESS_STATUSES or app_status in ['D_C', 'D', 'E', None]:
            pass
        else:
            raise Http404("Error condition: Unable to validate AICP enrollment application.")


class CandidateRegistrationAccessMixin(object):
    """
    A current or former AICP Candidate will always have an approved CAND application. In both
    cases they are excluded from the portal.
    """

    def validate_aicp(self):
        is_aicp = self.request.user.groups.filter(name='aicpmember').exists()
        imis_subs = self.contact.get_imis_subscriptions()
        aicp_sub = imis_subs.filter(product_code="AICP").exists()
        was_aicp = True if aicp_sub else False

        if is_aicp or was_aicp:
            messages.error(
                self.request,
                "Current and former AICP members are not eligible for the AICP Candidate Program."
            )
            self.success_url = "/aicp/candidate/"

    def validate_status(self, app_status):
        # if app_status == 'D':
        #     messages.warning(self.request, "Your student enrollment application was denied. You will need to go through the enrollment process again before registering for the exam.")
        #     self.success_url = "/aicp/candidate/"
        if app_status is None:
            messages.warning(self.request, "You do not have an AICP Candidate enrollment application. You need to go through the enrollment process before registering for the exam.")
            self.success_url = "/aicp/candidate/"
        elif app_status == 'P':
            messages.warning(self.request, "Your enrollment application was submitted/updated and is currently under review. Once approved, you will be able to register.")
            self.success_url = "/aicp/candidate/"
        elif app_status == 'EN':
            messages.success(self.request, "You are enrolled as a student in the AICP Candidate Program. You will be eligible to register for the AICP Exam when you graduate and complete your enrollment.")
            self.success_url = "/aicp/candidate/"
        elif app_status == 'N':
            messages.success(self.request, "Your AICP candidate enrollment has not yet been submitted. You will not be able to register until the enrollment process is complete.")
            self.success_url = "/aicp/candidate/"
        elif app_status in APPROVED_STATUSES:
            pass
        else:
            raise Http404("Error condition: Unable to validate AICP enrollment application.")


class CandidateCertPortalAccessMixin(object):

    def candidate_cert_access(self):
        now = timezone.now()
        cand_log_finished = False

        self.approved_cand_enroll_app = ExamApplication.objects.filter(
            contact=self.contact,
            application_type='CAND_ENR',
            application_status__in=APPROVED_STATUSES
        ).first()

        if not self.approved_cand_enroll_app:
            self.in_process_cand_enroll_app = ExamApplication.objects.filter(
                contact=self.contact,
                application_type='CAND_ENR'
            ).exclude(
                application_status__in=['A', 'A_C', 'D', 'D_C']
            ).order_by(
                'created_time'
            ).last()

        if not self.approved_cand_enroll_app and not self.in_process_cand_enroll_app:
            self.denied_cand_enroll_app = ExamApplication.objects.filter(
                contact=self.contact,
                application_type='CAND_ENR',
                application_status__in=['D', 'D_C']
            ).first()

        period = Period.objects.filter(code='CAND')
        cand_log = Log.objects.filter(contact=self.contact, period=period).first()
        if cand_log is not None:
            credits_overview = cand_log.credits_overview()
            if cand_log \
                    and credits_overview['general_needed'] <= 0 \
                    and credits_overview['ethics_needed'] <= 0 \
                    and credits_overview['law_needed'] <= 0:
                cand_log_finished = True

            self.cand_registration = ExamRegistration.objects.filter(
                contact=self.contact,
                registration_type__in=CAND_REG_TYPES,
                is_pass=True
            ).first()
            if self.cand_registration:
                passed_exam = True
            else:
                passed_exam = False
                self.cand_registration = ExamRegistration.objects.filter(
                    contact=self.contact,
                    registration_type__in=CAND_REG_TYPES
                ).order_by("exam__registration_end_time").last()

            # passed_exam = getattr(self.cand_registration, "is_pass", None)
            cand_no_pass = True if self.approved_cand_enroll_app and not passed_exam else False
            cand_cm_not_done = True if self.approved_cand_enroll_app and not cand_log_finished else False
            cand_log_end = getattr(cand_log, "end_time", None)
            cand_within_5_year_window = now < cand_log_end if cand_log_end else False

            self.cand_no_access = self.in_process_cand_enroll_app or cand_no_pass or cand_cm_not_done
            self.cand_access = self.approved_cand_enroll_app and passed_exam and cand_log_finished and cand_within_5_year_window
            self.ex_cand = (self.approved_cand_enroll_app or self.denied_cand_enroll_app) and not getattr(cand_log, "is_current", True)

            if self.cand_no_access:
                msg_string = ""
                if cand_no_pass and not cand_cm_not_done:
                    msg_string = "You still need to pass the AICP Certification Exam."
                elif cand_cm_not_done and not cand_no_pass:
                    msg_string = "You still need to finish tracking CM credits."
                elif cand_no_pass and cand_cm_not_done:
                    msg_string = "You still need to pass the AICP Certification Exam and finish tracking CM credits."
                messages.error(
                    self.request,
                    "You are not yet eligible to apply for AICP certification through the AICP Candidate Pilot Program. %s "
                    "Please contact customer service with questions." % (msg_string))
                self.success_url = "/aicp/candidate/"
            # FOR NOW SHUT OFF THE CERT PORTAL TO CANDIDATES UNTIL IT'S DONE.
            if self.cand_access:
                pass
                # messages.error(self.request,"The AICP certification portal is temporarily closed to AICP Candidates.")
                # self.success_url = "/aicp/candidate/"


def get_required_experience(obj):

    current_required_experience = HIGHEST_REQUIRED_EXPERIENCE
    lowest_required_experience = HIGHEST_REQUIRED_EXPERIENCE

    if obj.the_degrees:
        for degree in obj.the_degrees:
            current_required_experience = degree.get_experience_requirement()
            if current_required_experience < lowest_required_experience:
                lowest_required_experience = current_required_experience
    return lowest_required_experience


def get_years_experience(obj):
    total_experience = datetime.timedelta(0)

    if obj.the_jobs:
        for job in obj.the_jobs:
            job_planning_experience = job.get_planning_experience()
            if job_planning_experience is not None:
                total_experience += job_planning_experience

    return round(total_experience.days/365, 1)


def degree_delete(request, **kwargs):

    edu_id = request.GET.get("edu_id", False)

    if edu_id:
        edu = ApplicationDegree.objects.get(id=edu_id)
        edu.delete()
        messages.success(request,"Your Education details have been removed")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if not edu_id:
        messages.error(request,"You can't remove an empty degree.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def job_delete(request, **kwargs):

    job_id = request.GET.get("job_id", False)

    if job_id:
        job = ApplicationJobHistory.objects.get(id=job_id)
        job.delete()
        messages.success(request,"Your Job details has been removed")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if not job_id:
        messages.error(request,"You can't remove an empty degree.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class ExamApplicationMCIPSubmitView(AuthenticateLoginMixin, FormView):
    """
For MCIP applicants: they must:
1. upload verification of MCIP membership
2. confirm code of ethics
3. submit without paying fee
    """
    title = "AICP EXAM APPLICATION SUBMISSION: MCIP"
    template_name = 'exam/newtheme/application/mcip-submit.html'
    form_class = ExamApplicationMCIPSubmitForm
    application_category = None
    product = None
    form_obj = None

    def dispatch(self, request, *args, **kwargs):
        self.master_id = kwargs.get("master_id", None)
        self.get_exam_initial()

        dispatch = super().dispatch(request, *args, **kwargs)
        return dispatch

    def get_initial(self):
        initial = super().get_initial()
        initial["publish_status"] = self.application.publish_status  # "SUBMISSION"

        return initial

    def get_success_url(self):
        """
        Returns the supplied success URL.
        """
        if self.request.POST.get('submit'):
            messages.success(self.request, "Your MCIP exam application has been successfully submitted.")
            self.success_url = "/store/cart/"
        else:
            messages.error(self.request, "An error occured. Could not submit your MCIP exam application.")
            self.success_url = reverse_lazy("mcip_submit", kwargs={"master_id": self.application.master_id})
        url = force_text(self.success_url)
        return url

    def get(self, request, *args, **kwargs):

        return super().get(request, *args, **kwargs)

    def get_exam_initial(self):
        """
        get initial exam data
        """
        try:
            self.application = ExamApplication.objects.filter(
                Q(publish_status='SUBMISSION') | Q(publish_status='EARLY_RESUBMISSION')
            ).get(
                master__id=self.master_id,
                application_status='N'
            )
            # TO DO... double check... are these two categories the same?
            self.application_category = self.application.submission_category
            content_live_product = self.application_category.product_master.content_live.product
            self.product = ProductCart.objects.get(id=content_live_product.id)
        except ExamApplication.DoesNotExist:
            messages.error(
                self.request,
                "I'm sorry, you don't have an application record yet. Please start at the beginning."
            )

    def get_context_data(self, *args, **kwargs):

        self.get_exam_initial()
        context = super().get_context_data(**kwargs)

        context['code'] = self.application_category.code
        context['contact'] = self.application.contact
        context['exam'] = self.application.exam

        app_type_dict = dict(APPLICATION_TYPES)
        app_type = self.application.application_type
        app_type_verbose = app_type_dict[app_type]

        context['application_type'] = app_type_verbose

        app_status_dict = dict(APPLICATION_STATUSES)
        app_status = self.application.application_status
        app_status_verbose = app_status_dict[app_status]

        context['application_status'] = app_status_verbose
        context['code_of_ethics'] = self.application.code_of_ethics

        context['product'] = self.product
        context['submitted'] = False if (self.application.application_status == "N") else True

        return context

    def get_form_kwargs(self):

        self.get_exam_initial()

        kwargs = super().get_form_kwargs()
        self.degree = self.application.applicationdegree_set.first()
        kwargs["instance"] = getattr(self, "degree", None)

        return kwargs

    def form_valid(self, form):

        form_obj = form.save(commit=False)
        form_obj.exam = self.application.exam
        form_obj.application = self.application
        form_obj.contact = self.request.user.contact

        cleaned_data = form.cleaned_data
        if cleaned_data.get("uploaded_file", None):
            upload_type = UploadType.objects.get(code="EXAM_APPLICATION_EDUCATION")

            verif_docum = VerificationDocument.objects.filter(applicationdegree=form_obj).first()
            if not verif_docum:
                verif_docum = VerificationDocument(
                    content=self.application,
                    upload_type=upload_type,
                    publish_status=self.application.publish_status
                )
            verif_docum.uploaded_file = cleaned_data.get("uploaded_file", None)
            verif_docum.save()
            form_obj.verification_document = verif_docum

        self.purchase = self.product.add_to_cart(
            contact=self.request.contact,
            quantity=1,
            code=self.application.application_type,
            content_master=self.application.master,
        )
        form_obj.purchase = self.purchase
        form_obj.save()
        self.form_obj = form_obj

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "An error occurred. Please see below for any instructions.")
        return super().form_invalid(form)


class ExamApplicationReviewerEditView(AuthenticateLoginMixin, SubmissionDetailsView):
    title = "Exam Application Reviewer Edit"
    template_name = 'exam/newtheme/review/edit.html'
    application_review_form_class = ExamApplicationReviewForm
    application_answer_review_form_class = ExamAnswerReviewForm

    application_review_form = None

    application_answer_review_form_1 = None
    application_answer_review_form_2 = None
    application_answer_review_form_3 = None

    most_recently_denied = None
    is_advanced = False
    exam = None

    modelClass = ExamApplication
    application_category = None
    master_id = None
    contact = None
    product = None
    answer_review_formset = None
    review = None
    reviews = None

    answer_1 = None
    answer_2 = None
    answer_3 = None
    answer_1_old = None
    answer_2_old = None
    answer_3_old = None

    application = None
    the_degrees = None
    the_jobs = None
    years_experience = 0
    required_experience = 0

    review_form_1 = None
    review_form_2 = None
    review_form_3 = None
    review_form_4 = None
    review_form_5 = None
    review_form_6 = None

    round_1_answer_review_form_1 = None
    round_1_answer_review_form_2 = None
    round_1_answer_review_form_3 = None
    round_2_answer_review_form_1 = None
    round_2_answer_review_form_2 = None
    round_2_answer_review_form_3 = None
    round_3_answer_review_form_1 = None
    round_3_answer_review_form_2 = None
    round_3_answer_review_form_3 = None
    round_4_answer_review_form_1 = None
    round_4_answer_review_form_2 = None
    round_4_answer_review_form_3 = None
    round_5_answer_review_form_1 = None
    round_5_answer_review_form_2 = None
    round_5_answer_review_form_3 = None

    round_1_review = None
    round_2_review = None
    round_3_review = None
    round_4_review = None
    round_5_review = None
    round_6_review = None

    current_review_round = 0

    round_1_contact = None
    round_2_contact = None
    round_3_contact = None
    round_4_contact = None
    round_5_contact = None

    def dispatch(self, request, *args, **kwargs):
        self.master_id = kwargs.get("master_id", None)
        self.current_review_round = kwargs.get("review_round", None)
        self.contact = self.request.contact
        self.set_content(request, *args, **kwargs)
        self.get_exam_initial()

        dispatch = super().dispatch(request, *args, **kwargs)
        return dispatch

    def query_content(self, master_id):
        query = self.modelClass.objects.filter(
            master__id=master_id, publish_status="DRAFT"
        ).select_related(
            "submission_category"
        )
        return query

    def setup(self, request, *args, **kwargs):

        # TODO: Refactor this gigantic method

        self.review = ExamApplicationReview.objects.get(
            contact=self.contact,
            content=self.content,
            review_round=self.current_review_round
        )
        self.answer_1 = self.application.submission_answer.filter(question__code="EXAM_PLANNING_SITUATION").first()
        self.answer_2 = self.application.submission_answer.filter(question__code="EXAM_COMPREHENSIVE_POV").first()
        self.answer_3 = self.application.submission_answer.filter(question__code="EXAM_PUBLIC_DECISION_MAKING").first()
        if self.most_recently_denied:
            self.answer_1_old = self.most_recently_denied.submission_answer.filter(question__code="EXAM_PLANNING_SITUATION").first()
            self.answer_2_old = self.most_recently_denied.submission_answer.filter(question__code="EXAM_COMPREHENSIVE_POV").first()
            self.answer_3_old = self.most_recently_denied.submission_answer.filter(question__code="EXAM_PUBLIC_DECISION_MAKING").first()

        self.application_review_form = self.application_review_form_class(
            request.POST or None,
            instance=self.review,
            prefix='application_review'
        )
        if self.answer_1:
            answer1_ans_review = self.answer_1.answer_reviews.filter(
                review__contact=self.contact,
                review__review_round=self.current_review_round
            ).first()
        else:
            answer1_ans_review = None

        if self.answer_2:
            answer2_ans_review = self.answer_2.answer_reviews.filter(
                review__contact=self.contact,
                review__review_round=self.current_review_round
            ).first()
        else:
            answer2_ans_review = None

        if self.answer_3:
            answer3_ans_review = self.answer_3.answer_reviews.filter(
                review__contact=self.contact,
                review__review_round=self.current_review_round
            ).first()
        else:
            answer3_ans_review = None

        self.application_answer_review_form_1 = self.application_answer_review_form_class(
            request.POST or None,
            instance=answer1_ans_review,
            initial={"review": self.review, "answer": self.answer_1},
            prefix='answer_review_1'
        )
        self.application_answer_review_form_2 = self.application_answer_review_form_class(
            request.POST or None,
            instance=answer2_ans_review,
            initial={"review": self.review, "answer": self.answer_2},
            prefix='answer_review_2'
        )
        self.application_answer_review_form_3 = self.application_answer_review_form_class(
            request.POST or None,
            instance=answer3_ans_review,
            initial={"review": self.review, "answer": self.answer_3},
            prefix='answer_review_3'
        )
        # DO TO: IS THIS NEEDED SINCE NO ONE IS ACTUALLY UPLOADING?
        upload_type_codes = ["AWARD_LETTER_OF_SUPPORT", "AWARD_IMAGE", "AWARD_SUPLEMENTAL_MATERIALS"]
        self.upload_types = UploadType.objects.filter(
            code__in=upload_type_codes
        ).prefetch_related(
            Prefetch(
                "uploads",
                queryset=Upload.objects.filter(content=self.content),
                to_attr="the_uploads"
            )
        )
        self.reviews = self.application.review_assignments.all()
        self.review_dict = {}
        self.contact_dict = {}

        for i, r in enumerate(self.reviews):
            if r.review_round == 1:
                self.review_form_1 = self.application_review_form_class(
                    request.POST or None,
                    instance=r,
                    prefix='review_1'
                )
                self.review_dict["round_" + str(r.review_round) + "_review"] = r
                self.contact_dict["round_" + str(r.review_round) + "_contact"] = r.contact

            elif r.review_round == 2:
                self.review_form_2 = self.application_review_form_class(
                    request.POST or None,
                    instance=r,
                    prefix='review_2'
                )
                self.review_dict["round_" + str(r.review_round) + "_review"] = r
                self.contact_dict["round_" + str(r.review_round) + "_contact"] = r.contact

            elif r.review_round == 3:
                self.review_form_3 = self.application_review_form_class(
                    request.POST or None,
                    instance=r,
                    prefix='review_3'
                )
                self.review_dict["round_" + str(r.review_round) + "_review"] = r
                self.contact_dict["round_" + str(r.review_round) + "_contact"] = r.contact

            elif r.review_round == 4:
                self.review_form_4 = self.application_review_form_class(
                    request.POST or None,
                    instance=r,
                    prefix='review_4'
                )
                self.review_dict["round_" + str(r.review_round) + "_review"] = r
                self.contact_dict["round_" + str(r.review_round) + "_contact"] = r.contact

            elif r.review_round == 5:
                self.review_form_5 = self.application_review_form_class(
                    request.POST or None,
                    instance=r,
                    prefix='review_5'
                )
                self.review_dict["round_" + str(r.review_round) + "_review"] = r
                self.contact_dict["round_" + str(r.review_round) + "_contact"] = r.contact

            elif r.review_round == 6:
                self.review_form_6 = self.application_review_form_class(
                    request.POST or None,
                    instance=r,
                    prefix='review_6'
                )
                self.review_dict["round_" + str(r.review_round) + "_review"] = r
                self.contact_dict["round_" + str(r.review_round) + "_contact"] = r.contact

        self.answer_review_dict = {}

        for i in range(2, self.review.review_round+1):
            if self.answer_1:
                self.answer_review_dict["answer1_ans_review_round_" + str(i-1)] = self.answer_1.answer_reviews.filter(
                    review__contact=self.contact_dict["round_" + str(i-1) + "_contact"],
                    review__review_round=(i-1)
                ).first()
            else:
                self.answer_review_dict["answer1_ans_review_round_" + str(i-1)] = None

            if self.answer_2:
                self.answer_review_dict["answer2_ans_review_round_" + str(i-1)] = self.answer_2.answer_reviews.filter(
                    review__contact=self.contact_dict["round_" + str(i-1) + "_contact"],
                    review__review_round=(i-1)
                ).first()
            else:
                self.answer_review_dict["answer2_ans_review_round_" + str(i-1)] = None

            if self.answer_3:
                self.answer_review_dict["answer3_ans_review_round_" + str(i-1)] = self.answer_3.answer_reviews.filter(
                    review__contact=self.contact_dict["round_" + str(i-1) + "_contact"],
                    review__review_round=(i-1)
                ).first()
            else:
                self.answer_review_dict["answer3_ans_review_round_" + str(i-1)] = None

        self.answer_review_form_dict = {}

        if self.review:
            for i in range(2, self.review.review_round+1):
                self.answer_review_form_dict["round_" + str(i-1) + "_answer_review_form_1"] = self.application_answer_review_form_class(
                    request.POST or None,
                    instance=self.answer_review_dict["answer1_ans_review_round_" + str(i-1)],
                    initial={"review": self.review_dict["round_" + str(i-1) + "_review"], "answer": self.answer_1},
                    prefix='round_' + str(i-1) + '_answer_review_1'
                )
                self.answer_review_form_dict["round_" + str(i-1) + "_answer_review_form_2"] = self.application_answer_review_form_class(
                    request.POST or None,
                    instance=self.answer_review_dict["answer2_ans_review_round_" + str(i-1)],
                    initial={"review": self.review_dict["round_" + str(i-1) + "_review"], "answer": self.answer_2},
                    prefix='round_' + str(i-1) + '_answer_review_2'
                )
                self.answer_review_form_dict["round_" + str(i-1) + "_answer_review_form_3"] = self.application_answer_review_form_class(
                    request.POST or None,
                    instance=self.answer_review_dict["answer3_ans_review_round_" + str(i-1)],
                    initial={"review": self.review_dict["round_" + str(i-1) + "_review"], "answer": self.answer_3},
                    prefix='round_' + str(i-1) + '_answer_review_3'
                )

        return super().setup(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.the_degrees = self.application.applicationdegree_set.select_related("verification_document").all()
        self.the_jobs = self.application.applicationjobhistory_set.select_related("verification_document").all()
        self.required_experience = get_required_experience(self)
        self.years_experience = get_years_experience(self)

        if self.review is None:
            return render(
                request,
                "myapa/newtheme/restricted-access.html",
                {"message": "<h2>You have not been assigned to this exam application</h2>"}
            )

        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        """
        Returns the supplied success URL.
        """
        if self.request.POST.get('submit_review'):
            messages.success(self.request, "Your review has been submitted.")
            self.success_url = reverse_lazy("exam_application_reviewer")
        elif self.request.POST.get('save_and_continue'):
            messages.success(self.request, "Your review has been saved. You may continue editing.")
            self.success_url = reverse_lazy(
                "exam_application_reviewer_edit",
                kwargs={"master_id": self.application.master_id, "review_round": self.current_review_round}
            )
        else:
            messages.error(self.request, "An error has occurred. See below for any instructions.")
            self.success_url = reverse_lazy(
                "exam_application_reviewer_edit",
                kwargs={"master_id": self.application.master_id}
            )
        url = force_text(self.success_url)

        return url

    def get_exam_initial(self):
        """
        get the application, review, and most recently denied app (to get old criteria responses)
        """
        self.application = self.content.examapplication
        self.exam = self.application.exam
        previous_exams = self.exam.previous_exams.all()
        applicant_contact = self.application.contact

        current_submission_app = self.application.get_versions()['SUBMISSION']
        if current_submission_app.application_status in ['EB_D', 'EB_D_C']:
            if ExamApplication.objects.filter(
                contact=applicant_contact,
                publish_status='EARLY_RESUBMISSION',
                exam=self.exam
            ).exclude(application_status='N',).exists():
                self.most_recently_denied = ExamApplication.objects.get(master__id=self.master_id, publish_status='SUBMISSION')
            else:
                self.most_recently_denied = ExamApplication.objects.filter(
                    contact=applicant_contact,
                    application_status__in=DENIED_STATUSES_LIST,
                    publish_status='DRAFT',
                    exam__in=previous_exams
                ).order_by('created_time').last()

        # else if not an early bird denial case, get most recently denied app from previous exams
        else:
            self.most_recently_denied = ExamApplication.objects.filter(
                contact=applicant_contact,
                application_status__in=DENIED_STATUSES_LIST,
                publish_status='DRAFT',
                exam__in=previous_exams
            ).order_by('created_time').last()

        self.application_category = self.application.submission_category
        self.submission_category = self.application.submission_category
        content_live_product = self.application_category.product_master.content_live.product
        self.product = ProductCart.objects.get(id=content_live_product.id)

    def get_context_data(self, *args, **kwargs):

        context = super().get_context_data(*args, **kwargs)
        context["application_review_form"] = self.application_review_form
        context["application_answer_review_form_1"] = self.application_answer_review_form_1
        context["application_answer_review_form_2"] = self.application_answer_review_form_2
        context["application_answer_review_form_3"] = self.application_answer_review_form_3

        context["is_proposal"] = False
        context["upload_types"] = self.upload_types

        context['code'] = self.application_category.code
        context['degrees'] = self.application.applicationdegree_set.all()
        context['jobs'] = self.application.applicationjobhistory_set.all()
        context['contact'] = self.application.contact
        context['exam'] = self.application.exam

        degree_levels_dict = dict(DEGREE_LEVELS)
        context['bachelor'] = degree_levels_dict['B']
        context['master'] = degree_levels_dict['M']
        context['doctorate'] = degree_levels_dict['P']
        context['other_degree'] = degree_levels_dict['N']

        app_type_dict = dict(APPLICATION_TYPES)
        app_type = self.application.application_type
        app_type_verbose = app_type_dict[app_type]

        context['application_type'] = app_type_verbose

        app_status_dict = dict(APPLICATION_STATUSES)
        app_status = self.application.application_status
        app_status_verbose = app_status_dict[app_status]

        context['application_status'] = app_status_verbose
        context['code_of_ethics'] = self.application.code_of_ethics

        context["answer_1"] = self.answer_1
        context["answer_2"] = self.answer_2
        context["answer_3"] = self.answer_3
        context["answer_1_old"] = self.answer_1_old
        context["answer_2_old"] = self.answer_2_old
        context["answer_3_old"] = self.answer_3_old

        answer_list = [self.answer_1, self.answer_2, self.answer_3]

        for i, answer in enumerate(answer_list):
            if answer:
                if answer.text:
                    context['answer_word_count_%s' % (i+1)] = len(answer.text.split())
                else:
                    context['answer_word_count_%s' % (i+1)] = 0
            else:
                context['answer_word_count_%s' % (i+1)] = 0

        context['product'] = self.product
        context['submitted'] = False if (self.application.application_status == "N") else True
        context["is_staff"] = self.request.user.groups.filter(name="staff").exists() or self.request.user.is_staff
        context["is_staff_reviewer"] = self.request.user.groups.filter(name="staff-reviewer").exists()

        # this gets the record that relates the content (application in this case) with the EXAM_PLANNING_PROCESS tag type
        criteria_1_contenttagtype = self.application.contenttagtype.filter(tag_type__code="EXAM_PLANNING_PROCESS").first()

        if criteria_1_contenttagtype:
            context["criteria_1_tag"] = criteria_1_contenttagtype.tags.all().first()

        context['answer_reviews'] = self.review.answer_reviews.all()
        context['review_time'] = self.review.review_time
        context['planning_experience'] = self.years_experience
        context['required_planning_experience'] = self.required_experience
        context['current_review_round'] = self.review.review_round
        context['reviews'] = self.reviews

        review_forms = []
        for i in range(1, int(self.current_review_round)):
            r = eval("self.review_form_" + str(i))
            if r is not None:
                review_forms.append(r)

        context['review_forms'] = review_forms

        cri1_answer_review_forms = []
        cri2_answer_review_forms = []
        cri3_answer_review_forms = []

        for i in range(1, int(self.current_review_round)):
            r = self.answer_review_form_dict["round_" + str(i) + "_answer_review_form_1"]
            if r is not None:
                cri1_answer_review_forms.append(r)
            r = self.answer_review_form_dict["round_" + str(i) + "_answer_review_form_2"]
            if r is not None:
                cri2_answer_review_forms.append(r)
            r = self.answer_review_form_dict["round_" + str(i) + "_answer_review_form_3"]
            if r is not None:
                cri3_answer_review_forms.append(r)

        context['cri1_answer_review_forms'] = cri1_answer_review_forms
        context['cri2_answer_review_forms'] = cri2_answer_review_forms
        context['cri3_answer_review_forms'] = cri3_answer_review_forms

        return context

    def post(self, request, *args, **kwargs):

        self.the_degrees = self.application.applicationdegree_set.select_related("verification_document").all()
        self.the_jobs = self.application.applicationjobhistory_set.select_related("verification_document").all()
        self.required_experience = get_required_experience(self)
        self.years_experience = get_years_experience(self)
        # if reviewer clicks 'submit' button review time is set and review is considered "complete"
        if self.request.POST.get('submit_review'):
            self.review.review_time = timezone.now()

        form0 = self.application_review_form.is_valid()
        form1 = self.application_answer_review_form_1.is_valid()
        form2 = self.application_answer_review_form_2.is_valid()
        form3 = self.application_answer_review_form_3.is_valid()

        if form0:
            self.application_review_form.save()
        if form1:
            self.application_answer_review_form_1.save()
        if form2:
            self.application_answer_review_form_2.save()
        if form3:
            self.application_answer_review_form_3.save()

        if form0 and form1 and form2 and form3:
            messages.success(request, "Successfully updated your review")

            return HttpResponseRedirect(self.get_success_url())
        else:
            messages.error(request, "An error occurred. Please see below for any instructions.")

            return super().get(request, *args, **kwargs)


class ExamApplicationReviewerView(AuthenticateLoginMixin, TemplateView):
    """
    Entry point for the Exam Application reviewer portal.
    To allow reviewers to see their new or in-progress exam application reviews.
    """
    template_name="exam/newtheme/review/assigned-list.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        now = timezone.now()
        context["reviews"] = ExamApplicationReview.objects.filter(
            content__examapplication__exam__application_start_time__lte=now,
            content__examapplication__exam__end_time__gte=now,
            contact=self.request.contact,
            content__publish_status="DRAFT"
        ).select_related(
            "contact__user",
            "role__contact__user",
            "content__submission_category",
            "content__examapplication"
        ).order_by(
            "content__submission_category",
            "content__title"
        )

        context["is_staff"] = self.request.user.groups.filter(name="staff").exists()

        return context

    def render_template(self, request):
        return render(request, self.template_name, self.context)


class ExamApplicationReviewerCompleteView(AuthenticateLoginMixin, TemplateView):
    """
    To allow reviewers to see their completed exam application reviews.
    """
    template_name="exam/newtheme/review/completed-list.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        now = timezone.now()
        context["reviews"] = ExamApplicationReview.objects.filter(
            content__examapplication__exam__application_start_time__lte=now,
            content__examapplication__exam__end_time__gte=now,
            contact=self.request.contact,
            content__publish_status="DRAFT",
            review_time__isnull=False
        ).select_related(
            "contact__user",
            "role__contact__user",
            "content__submission_category",
            "content__examapplication"
        ).order_by(
            "content__submission_category",
            "content__title"
        )
        context["is_staff"] = self.request.user.groups.filter(name="staff").exists()

        return context

    def render_template(self, request):

        return render(request, self.template_name, self.context)


class ExamApplicationTypeView(AuthenticateMemberMixin, CandidateCertPortalAccessMixin, FormView):
    """
    Entry point for the Exam Application portal
    """
    title = "Application Type"
    template_name = 'exam/newtheme/application/application-type.html'
    form_class = ExamApplicationTypeForm

    exam = None
    contact = None
    application = None
    application_category = None
    application_type = None
    is_advanced = False
    is_aicpmember = False
    product = None
    registration = None
    blocked = False
    denied_application = None
    early_bird = False
    closed = False
    early_bird_deadline = None
    asc_window_open = False

    approved_cand_enroll_app = None
    in_process_cand_enroll_app = None
    denied_cand_enroll_app = None
    cand_log = None
    cand_registration = None
    cand_no_access = False
    cand_access = False
    ex_cand = False
    has_paid_cert_app = False
    allowed_application_exams = []

    def get_success_url(self):

        app_type = self.request.POST.get('application_type')
        app_status = self.application.application_status
        reg_type = self.registration.registration_type if self.registration else None

        if self.closed:
            messages.error(self.request, "The application process is now closed to all applicants.")
            self.success_url = reverse_lazy("exam_application_type")

        elif (self.application_type in ADVANCED_APPLICATION_TYPES) and not self.is_aicpmember:
            messages.error(self.request, "You must be an aicp member to apply for advanced specialty certification")
            self.success_url = reverse_lazy("exam_application_type")

        elif not self.exam:
            messages.error(self.request, "We're sorry, there is no exam application window currently open.")
            self.success_url = reverse_lazy("exam_application_type")

        elif self.blocked:
            messages.error(
                self.request,
                "The application process is temporarily unavailable to previously denied applicants."
            )
            self.success_url = reverse_lazy("exam_application_type_edit", kwargs={"master_id": self.application.master_id})

        elif app_status in APPROVAL_PROCESS_STATUSES:
            messages.error(
                self.request,
                "You already have a submitted application on record. Contact customer service if this seems incorrect."
            )
            self.success_url = reverse_lazy("exam_application_type_edit", kwargs={"master_id": self.application.master_id})

        elif app_status in APPROVED_STATUSES:
            messages.success(
                self.request,
                "Good news! Your previously submitted AICP exam application is already approved. "
                "Please use the form below to start the registration process for the AICP exam."
            )
            self.success_url = reverse_lazy("exam_registration")

        elif self.registration:
            if reg_type in PRE_APPROVED_REG_TYPE_LIST:
                messages.success(
                    self.request,
                    "Good news! Your previously submitted AICP exam application is already approved. "
                    "Please use the form below to start the registration process for the AICP exam."
                )
                self.success_url = reverse_lazy("exam_registration")

        elif not self.early_bird and timezone.now() > self.application.exam.application_end_time:
            messages.error(
                self.request,
                "The application process is currently only available to early bird denied re-applicants."
            )
            self.success_url = reverse_lazy("exam_application_type")

        elif (app_status == 'N') and self.request.POST.get('submit') and (not self.registration):
            if (app_type == 'REG' or app_type == 'NJ' or app_type == 'NJ_REG') and not self.is_advanced:
                messages.success(self.request, "You may continue your application.")
                self.success_url = reverse_lazy("exam_degree_history", kwargs={"master_id": self.application.master_id})
            elif app_type == 'MCIP' and not self.is_advanced:
                messages.success(
                    self.request,
                    "You've selected the MCIP application type. Please contact us at aicpexam@planning.org for "
                    "instructions on how to complete your application. Thank you."
                )
                self.success_url = reverse_lazy("exam_application_type")
            elif app_type == 'NJ_NOAICP' and not self.is_advanced:
                messages.success(
                    self.request,
                    "You've selected the NJ Not Applying for AICP-Exam Only application type. Please contact us "
                    "at aicpexam@planning.org for instructions on how to complete your application. Thank you."
                )
                self.success_url = reverse_lazy("exam_application_type")
            elif app_type in ['CUD', 'CTP', 'CEP'] and self.is_advanced:
                messages.success(self.request, "You may continue your advanced specialty exam application.")
                self.success_url = reverse_lazy("exam_job_history", kwargs={"master_id": self.application.master_id})
            elif app_type in ['CUD', 'CTP', 'CEP'] and not self.is_advanced:
                messages.error(
                    self.request,
                    "You need to be an AICP member to apply for the advanced specialty exam. Please contact "
                    "customer service if there has been an error."
                )
                self.success_url = reverse_lazy("exam_application_type")
            elif app_type in REGULAR_APPLICATION_TYPES and self.is_advanced:
                messages.error(
                    self.request,
                    "As an AICP member you are only eligible to apply for the advanced specialty exam. "
                    "Please visit <a href='https://planning.org/asc/'>https://planning.org/asc/ for more information.</a>"
                )
                self.success_url = reverse_lazy("exam_application_type")
            elif self.cand_access:
                # messages.error(self.request,"The AICP certification portal is temporarily closed to AICP Candidates.")
                # self.success_url = "/aicp/candidate/"
                messages.success(
                    self.request,
                    "You are eligibile to apply for AICP certification as part of the AICP Candidate Pilot Program."
                )
                self.success_url = reverse_lazy("exam_job_history", kwargs={"master_id": self.application.master_id})
        else:
            messages.error(self.request, "An error occured. Could not proceed with your application. Please contact customer service.")
            self.success_url = reverse_lazy("exam_application_type")

        url = force_text(self.success_url)

        return url

    def get_exam_initial(self):
        self.allowed_application_exams = []
        exam_product = ProductCart.objects.get(code='EXAMAPPLICATION_AICP')
        early_bird_price = exam_product.prices.get(code="EB_D")
        self.early_bird_deadline = early_bird_price.end_time
        # if the current date is later than the last possible application deadline, completely close the portal
        if timezone.now() > self.early_bird_deadline:
            self.closed = True

        if self.exam:
            self.allowed_application_exams = list(self.exam.previous_exams.all()) + [self.exam]
            # .exclude(application_type__in=CAND_ENROLL_APP_TYPES)
            self.application = ExamApplication.objects.filter(
                contact=self.contact,
                application_status__in=APPROVED_STATUSES,
                exam__in=self.allowed_application_exams
            ).exclude(
                application_type__in=CAND_ENROLL_APP_TYPES
            ).order_by(
                'created_time'
            ).last()

            # try to get an exam app that was submitted
            if not self.application:
                try:
                    self.application = ExamApplication.objects.filter(
                        contact=self.contact,
                        exam__in=self.allowed_application_exams,
                        application_status__in=APPROVAL_PROCESS_STATUSES
                    ).exclude(
                        application_type__in=CAND_ENROLL_APP_TYPES
                    ).first()
                except:
                    # TODO: NO MORE BARE EXCEPTS!!!
                    self.application = None
            # try to get a previously denied app to test for early bird, and later to populate data in new app
            if not self.application:
                try:
                    self.denied_application = ExamApplication.objects.filter(
                        contact=self.contact,
                        application_status__in=DENIED_STATUSES_LIST,
                        exam__in=self.allowed_application_exams
                    ).filter(
                        Q(publish_status='EARLY_RESUBMISSION') | Q(publish_status='SUBMISSION')
                    ).exclude(
                        application_type__in=CAND_ENROLL_APP_TYPES
                    ).order_by('created_time').last()

                    if self.denied_application:
                        self.blocked = False
                        exam = self.denied_application.exam
                        exam_is_current = (exam.registration_start_time <= timezone.now()) \
                                          and (exam.registration_end_time >= timezone.now())

                        if (self.denied_application.application_status in ["EB_D", "EB_D_C"]) \
                                and exam_is_current \
                                and (timezone.now() < self.early_bird_deadline):
                            self.early_bird = True
                except:
                    # TODO: NO MORE BARE EXCEPTS!!!
                    pass
            # a non-candidate registration will preclude them from continuing
            self.registration = ExamRegistration.objects.filter(
                exam=self.exam,
                contact=self.contact
            ).exclude(
                registration_type__in=CANDIDATE_REGISTRATION_TYPES
            ).last()
            if self.registration:
                self.purchase = self.registration.purchase
            else:
                self.purchase = None
        # if no current/available exam, set app to None
        else:
            self.application = None
        # if app is still None try to get an unfinished SUBMISSION (they are returning to finish)
        if self.application == None:
            try:
                self.application = ExamApplication.objects.get(
                    ~Q(application_type__in=CAND_ENROLL_APP_TYPES),
                    contact=self.request.contact,
                    exam__application_start_time__lt=timezone.now(),
                    exam__application_end_time__gt=timezone.now(),
                    exam__is_advanced=self.is_advanced,
                    publish_status="SUBMISSION",
                    application_status="N"
                )
            except ExamApplication.DoesNotExist:
                pass  # Fail silently... a new exam record will be created when the form is submitted

    def get(self, request, *args, **kwargs):
        kwargs['type'] = request.GET.get("type", "REG")
        self.contact = request.user.contact

        self.candidate_cert_access()
        url = force_text(self.success_url)
        if url == "/aicp/candidate/":
            return redirect(url)

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.contact = request.user.contact

        self.candidate_cert_access()
        url = force_text(self.success_url)
        if url == "/aicp/candidate/":
            return redirect(url)

        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        most_recent_asc_exam = Exam.objects.filter(code__contains='ASC').order_by('application_start_time').last()
        start = most_recent_asc_exam.application_start_time
        end = most_recent_asc_exam.application_end_time
        self.asc_window_open = start <= now <= end
        context["asc_window_open"] = self.asc_window_open
        return context

    def get_form_kwargs(self):

        kwargs = super().get_form_kwargs()
        if self.application:
            kwargs['initial']['application_type'] = self.application.application_type
        kwargs["asc_window_open"] = self.asc_window_open
        kwargs["cand_no_access"] = self.cand_no_access
        kwargs["cand_access"] = self.cand_access
        kwargs["is_aicpmember"] = self.is_aicpmember
        kwargs["has_paid_cert_app"] = self.has_paid_cert_app
        return kwargs

    def get_form(self, *args, **kwargs):
        self.contact = self.request.user.contact
        self.application_type = self.request.GET.get("type", "REG")
        self.is_aicpmember = self.request.user.groups.filter(name='aicpmember').exists()

        if self.is_aicpmember:
            self.is_advanced = True

        self.exam = Exam.objects.filter(
            is_advanced=self.is_advanced,
            application_start_time__lt=timezone.now(),
            application_end_time__gt=timezone.now()
        ).first()

        self.get_exam_initial()

        # To handle Candidates $0 Resub (not early resub):
        cert_apps = ExamApplication.objects.filter(
            contact=self.contact,
            application_type="CAND_CERT",
            exam__in=self.allowed_application_exams
        )

        purchases = [Purchase.objects.filter(content_master=capp.master).first() for capp in cert_apps]
        filtered_purchases = list(filter(None.__ne__, purchases))
        self.has_paid_cert_app = True if filtered_purchases else False

        return super().get_form(*args, **kwargs)

    def form_valid(self, form):
        if self.early_bird == True:
            messages.success(self.request, "You have been cleared for early bird resubmission.")

        self.application_type = form.cleaned_data.get("application_type", "REG")

        if self.application_type not in ADVANCED_APPLICATION_TYPES:
            self.submission_category_code = "EXAM_APPLICATION_AICP"
        elif self.application_type in ADVANCED_APPLICATION_TYPES:
            self.submission_category_code = "EXAM_APPLICATION_" + self.application_type

        self.application_category = ApplicationCategory.objects.filter(code=self.submission_category_code).first()
        publish_status = "EARLY_RESUBMISSION" if self.early_bird else "SUBMISSION"

        if not self.application:
            if self.early_bird:
                # first query for a pre-existing early resubmission record
                try:
                    self.application = ExamApplication.objects.filter(
                        contact=self.request.contact,
                        exam__is_advanced=self.is_advanced,
                        application_status="N"
                    ).exclude(application_type__in=CAND_ENROLL_APP_TYPES).get(
                        publish_status="EARLY_RESUBMISSION"
                    )
                # if does not exist, set to None, if more than one throw errror
                except ExamApplication.DoesNotExist:
                    self.application = None

                if not self.application:
                    self.application, created = ExamApplication.objects.get_or_create(
                        master=self.denied_application.master,
                        publish_uuid=self.denied_application.publish_uuid,
                        contact=self.request.user.contact,
                        exam=self.exam,
                        application_type=self.application_type,
                        publish_status=publish_status,
                        application_status="N",
                        submission_category=self.application_category
                    )
            else:
                self.application, created = ExamApplication.objects.get_or_create(
                    contact=self.request.user.contact,
                    exam=self.exam,
                    application_type=self.application_type,
                    publish_status=publish_status,
                    application_status="N",
                    submission_category=self.application_category
                )

            if self.denied_application and self.application_type not in CAND_CERT_APP_TYPES:
                if self.application.applicationdegree_set.all().count() == 0:
                    for denied_degree in self.denied_application.applicationdegree_set.all():
                        if self.early_bird:
                            verification_document = denied_degree.verification_document
                            verification_document.id = None
                            verification_document.publish_uuid = denied_degree.verification_document.publish_uuid
                            verification_document.publish_status = publish_status
                            verification_document.save()
                        else:
                            verification_document = None

                        degree_obj = ApplicationDegree.objects.create(
                            publish_status=publish_status,
                            contact=self.request.user.contact,
                            application=self.application,
                            verification_document=verification_document,
                            pab_accredited=denied_degree.pab_accredited,
                            school=denied_degree.school,
                            other_school=denied_degree.other_school,
                            graduation_date=denied_degree.graduation_date,
                            level=denied_degree.level,
                            is_planning=denied_degree.is_planning
                        )
                        # self.application.applicationdegree_set.add(degree_obj)
                        if self.early_bird:
                            degree_obj.publish_uuid = denied_degree.publish_uuid

                        degree_obj.application = self.application

                if self.application.applicationjobhistory_set.all().count() == 0:

                    for denied_job in self.denied_application.applicationjobhistory_set.all():

                        if self.early_bird:
                            verification_document = denied_job.verification_document
                            verification_document.id = None
                            verification_document.publish_uuid = denied_job.verification_document.publish_uuid
                            verification_document.publish_status = publish_status
                            verification_document.save()
                        else:
                            verification_document = None

                        job_obj = ApplicationJobHistory.objects.create(
                            publish_status=publish_status,
                            contact=self.request.user.contact,
                            application=self.application,
                            # pull verific. doc.: yes for early bird, no for previously denied
                            verification_document=verification_document,
                            is_planning=denied_job.is_planning,
                            contact_employer=denied_job.contact_employer,
                            supervisor_name=denied_job.supervisor_name,
                            title=denied_job.title,
                            company=denied_job.company,
                            city=denied_job.city,
                            state=denied_job.state,
                            zip_code=denied_job.zip_code,
                            country=denied_job.country,
                            start_date=denied_job.start_date,
                            end_date=denied_job.end_date,
                            is_current=denied_job.is_current,
                            is_part_time=denied_job.is_part_time,
                            phone=denied_job.phone
                        )
                        # self.application.applicationjobhistory_set.add(job_obj)
                        if self.early_bird:
                            job_obj.publish_uuid=denied_job.publish_uuid

                        job_obj.application = self.application

                # copy criteria answers from denied app to new app
                # HERE WE SHOULD NOT SET THE PUBLISH STATUS???
                if self.application.submission_answer.count() == 0:
                    for dc_answer in self.denied_application.submission_answer.all():
                        ans_obj, created = Answer.objects.get_or_create(
                            # publish_uuid=dc_answer.publish_uuid,
                            publish_status=publish_status,
                            content=self.application,
                            question=dc_answer.question)

                        if self.early_bird:
                            ans_obj.publish_uuid=dc_answer.publish_uuid

                        if created:
                            ans_obj.text = dc_answer.text
                            ans_obj.tag = dc_answer.tag
                            ans_obj.save()

                self.application.save()
        else:
            # If the application exists but the user selects a different type:
            # but only if the application is unsubmitted
            if self.application.application_status == 'N':
                self.application.application_type = self.application_type
                self.application.submission_category = self.application_category
                self.application.save()

        # don't get this from the application, it could be stale
        # self.submission_category = self.application.submission_category
        # get it based on the current application type:
        self.submission_category = self.application_category
        content_live_product = self.application_category.product_master.content_live.product
        self.product = ProductCart.objects.get(id=content_live_product.id)

        # put auto email code for MCIP and NJ_NOAICP here??
        if self.application.application_status == 'N':
            if self.application.application_type in SKIP_APP_TYPES:
                mail_context = {'application': self.application}
                email_template_code = APP_TYPE_TO_EMAIL_CODE[self.application.application_type]
                mail_to = self.application.contact.email
                Mail.send(email_template_code, mail_to, mail_context)

        return super().form_valid(form)


class ExamSummaryView(AuthenticateMemberMixin, FormView):
    """
    The summary step for those applying to take the AICP exam. Links to go back and edit or submit.
    """
    title = "Summary"
    template_name = 'exam/newtheme/application/summary.html'
    form_class = ExamSummaryForm
    application_category = None
    product = None
    years_experience = -1
    required_experience = -1
    is_advanced = False
    the_degrees = None
    the_jobs = None

    def dispatch(self, request, *args, **kwargs):
        self.master_id = kwargs.get("master_id", None)
        self.get_exam_initial()
        self.assemble_application_summary(self.request)

        dispatch = super().dispatch(request, *args, **kwargs)
        return dispatch

    def assemble_application_summary(self, request):
        JobFormSet = formset_factory(ExamJobHistoryForm)
        EthicsFormSet = formset_factory(ExamCodeOfEthicsForm)

        if request.method == 'POST':
            self.job_formset = JobFormSet(request.POST, request.FILES, prefix='jobs')
            self.criteria_form = ExamCriteriaForm(request.POST, request.FILES, instance=self.application, prefix='questions')
            self.ethics_formset = EthicsFormSet(request.POST, request.FILES, prefix='ethics')
        else:
            # self.degree_formset = DegreeFormSet(prefix='degrees')
            self.job_formset = JobFormSet(prefix='jobs')
            # self.criteria_formset = CriteriaFormSet(prefix='questions')
            self.criteria_form = ExamCriteriaForm(request.POST, request.FILES, instance=self.application, prefix='questions')
            self.ethics_formset = EthicsFormSet(prefix='ethics')

    def get_success_url(self):
        """
        Returns the supplied success URL.
        """
        if self.request.POST.get('submit'):
            self.success_url = "/store/cart/"
        else:
            messages.error(self.request, "An error occured. Could not submit your exam application.")
            self.success_url = reverse_lazy("exam_application_summary", kwargs={"master_id": self.application.master_id})
        url = force_text(self.success_url)
        return url

    def get(self, request, *args, **kwargs):

        self.the_degrees = self.application.applicationdegree_set.select_related("verification_document").all()
        self.the_jobs = self.application.applicationjobhistory_set.select_related("verification_document").all()

        self.required_experience = get_required_experience(self)
        self.years_experience = get_years_experience(self)

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        self.the_degrees = self.application.applicationdegree_set.select_related("verification_document").all()
        self.the_jobs = self.application.applicationjobhistory_set.select_related("verification_document").all()

        self.required_experience = get_required_experience(self)
        self.years_experience = get_years_experience(self)

        if self.years_experience >= self.required_experience:
            return super().post(request, *args, **kwargs)
        else:
            experience_defecit = round(self.required_experience - self.years_experience, 1)
            messages.error(
                request,
                "You have not entered enough professional planning experience to apply for the exam. "
                "You need %s more years experience." % experience_defecit
            )
            context = self.get_context_data(**kwargs)

            return render(request, self.template_name, context)

    def get_exam_initial(self):
        """
        get initial exam data
        """
        self.is_advanced = False
        if self.request.user.groups.filter(name='aicpmember'):
            self.is_advanced = True
        # get last created unsubmitted application
        self.application = ExamApplication.objects.filter(
            master__id=self.master_id,
            application_status='N'
        ).filter(
            Q(publish_status='SUBMISSION') | Q(publish_status='EARLY_RESUBMISSION')
        ).order_by(
            "created_time"
        ).exclude(
            application_type__in=CAND_ENROLL_APP_TYPES
        ).last()

        # when coming from APA to view a submitted application the above query will fail, so if unsubmitted doesn't exist get latest submission:
        if not self.application:
            self.application = ExamApplication.objects.filter(
                master__id=self.master_id
            ).filter(
                Q(publish_status='SUBMISSION') | Q(publish_status='EARLY_RESUBMISSION')
            ).order_by(
                "submission_time"
            ).exclude(
                application_type__in=CAND_ENROLL_APP_TYPES
            ).last()

        self.application_category = self.application.submission_category
        self.submission_category = self.application.submission_category
        content_live_product = self.application_category.product_master.content_live.product
        self.product = ProductCart.objects.get(id=content_live_product.id)

    def get_context_data(self, *args, **kwargs):

        context = super().get_context_data(**kwargs)

        context['code'] = self.application_category.code
        context['degrees'] = self.the_degrees
        context['jobs'] = self.the_jobs
        context['contact'] = self.application.contact
        context['exam'] = self.application.exam

        degree_levels_dict = dict(DEGREE_LEVELS)
        context['bachelor'] = degree_levels_dict['B']
        context['master'] = degree_levels_dict['M']
        context['doctorate'] = degree_levels_dict['P']
        context['other_degree'] = degree_levels_dict['N']

        app_type_dict = dict(APPLICATION_TYPES)
        app_type = self.application.application_type
        app_type_verbose = app_type_dict[app_type]

        context['application_type'] = app_type_verbose

        app_status_dict = dict(APPLICATION_STATUSES)
        app_status = self.application.application_status
        app_status_verbose = app_status_dict[app_status]

        context['application_status'] = app_status_verbose
        context['code_of_ethics'] = self.application.code_of_ethics

        criteria = self.application.submission_category.questions.all().exclude(
            question_type='TAG'
        ).order_by(
            "sort_number"
        )
        context['questions'] = criteria

        answer_list = []
        for question in criteria:
            answer_list.append(question.answers.filter(content=self.application).first())

        context['answers'] = answer_list

        qa_dict = dict(zip(criteria, answer_list))
        context['qa_dict'] = qa_dict

        context['planning_experience'] = self.years_experience
        context['required_planning_experience'] = self.required_experience

        # CAN'T DO degree_formset - CAUSES BROWSER TO HANG:
        # this may be circular because of duplicate names:
        # context['review_degree_formset'] = self.degree_formset

        context['job_formset'] = self.job_formset
        context['criteria_form'] = self.criteria_form
        context['ethics_formset'] = self.ethics_formset

        context['product'] = self.product
        context['submitted'] = False if (self.application.application_status == "N") else True
        context['submission_time'] = self.application.submission_time
        context['is_advanced'] = self.is_advanced

        return context

    def get_form_kwargs(self):

        kwargs = super().get_form_kwargs()
        kwargs["instance"] = getattr(self, "application", None)
        return kwargs

    def form_valid(self, form):

        form_obj = form.save(commit=False)

        form_obj.exam = self.application.exam
        form_obj.application = self.application
        form_obj.contact = self.request.user.contact

        if self.application.publish_status == 'EARLY_RESUBMISSION':
            if self.application.application_type in CAND_CERT_APP_TYPES:
                price_code = 'CAND_EB_D'
            else:
                price_code = 'EB_D'
        else:
            price_code = self.application.application_type

        # price_code = 'EB_D' if self.application.publish_status == 'EARLY_RESUBMISSION' else self.application.application_type

        self.purchase = self.product.add_to_cart(
            contact=self.request.contact,
            quantity=1,
            code=price_code
        )

        if self.purchase:
            self.purchase.content_master = self.application.master
            self.purchase.save()
        else:
            self.purchase = None

        form_obj.purchase = self.purchase
        form_obj.save()

        return super().form_valid(form)


class ExamApplicationCodeOfEthicsView(AuthenticateLoginMixin, FormView):
    title = "Ethics"
    template_name = 'exam/newtheme/application/code-of-ethics.html'
    form_class = ExamApplicationCodeOfEthicsForm
    master_id = None

    def dispatch(self, request, *args, **kwargs):
        self.master_id = kwargs.get("master_id", None)
        self.application = ExamApplication.objects.filter(
            master__id=self.master_id,
            application_status='N'
        ).exclude(
            application_type__in=CAND_ENROLL_APP_TYPES
        ).get(
            Q(publish_status='SUBMISSION') | Q(publish_status='EARLY_RESUBMISSION')
        )

        dispatch = super().dispatch(request, *args, **kwargs)

        return dispatch

    def get_success_url(self):
        """
        Returns the supplied success URL.
        """
        if self.request.POST.get('submit'):
            messages.success(self.request, "Please review your application and make any necessary changes.")
            self.success_url = reverse_lazy("exam_application_summary", kwargs={"master_id": self.application.master_id})
        else:
            messages.error(self.request, "An error occured. Could not proceed to summary step.")
            self.success_url = reverse_lazy("exam_app_code_of_ethics", kwargs={"master_id": self.application.master_id})

        url = force_text(self.success_url)

        return url

    def get_form_kwargs(self):

        kwargs = super().get_form_kwargs()
        kwargs['initial']['code_of_ethics'] = self.application.code_of_ethics

        return kwargs

    def get_form(self, form_class=None):

        if not form_class:
            form_class = self.form_class

        if self.application:
            return form_class(instance=self.application, **self.get_form_kwargs())
        else:
            return form_class(**self.get_form_kwargs())

    def form_valid(self, form):

        form_obj = form.save(commit=False)
        form_obj.exam = self.application.exam
        form_obj.application = self.application
        form_obj.contact = self.request.user.contact
        form_obj.save()

        return super().form_valid(form)


class ExamCriteriaView(SubmissionEditFormView):
    title = "Questions"
    template_name = 'exam/newtheme/application/criteria.html'
    form_class = ExamCriteriaForm

    submission_category = None
    submission_category_code = None
    product = None
    application_category = None
    extra_form_kwargs = {}

    home_url = "/certification/exam/application/{master_id}/criteria/"
    success_url = "/certification/exam/application/{master_id}/code-of-ethics/"
    home_path = home_url
    is_advanced = False
    guidelines_dict = {
        'CUD': 'https://www.planning.org/asc/urbandesign/',
        'CTP': 'https://www.planning.org/asc/transportation/',
        'CEP': 'https://www.planning.org/asc/environment/',
    }

    def query_content(self, master_id):
        query = self.modelClass.objects.filter(
            master__id=master_id,
            application_status='N'
        ).filter(
            Q(publish_status="SUBMISSION") | Q(publish_status="EARLY_RESUBMISSION")
        ).select_related(
            "submission_category"
        )
        return query

    def dispatch(self, request, *args, **kwargs):
        self.master_id = kwargs.get("master_id", None)
        self.get_exam_initial()
        self.application_category = self.application.submission_category
        self.submission_category = self.application.submission_category

        dispatch = super().dispatch(request, *args, **kwargs)

        return dispatch

    def setup(self, request, *args, **kwargs):
        upload_type_codes = ["AWARD_LETTER_OF_SUPPORT", "AWARD_IMAGE", "AWARD_SUPLEMENTAL_MATERIALS"]
        self.upload_types = UploadType.objects.filter(
            code__in=upload_type_codes
        ).prefetch_related(
            Prefetch(
                "uploads",
                queryset=Upload.objects.filter(content=self.content),
                to_attr="the_uploads"
            )
        )

        super().setup(request, *args, **kwargs)

    def get_exam_initial(self):
        """
        get initial exam data
        """
        if self.request.user.groups.filter(name='aicpmember'):
            self.is_advanced = True

        if self.is_advanced:
            self.form_class = ASCExamCriteriaForm
        else:
            self.form_class = ExamCriteriaForm

        try:
            self.application = ExamApplication.objects.filter(
                master__id=self.master_id,
                application_status='N'
            ).filter(
                Q(publish_status='SUBMISSION') | Q(publish_status='EARLY_RESUBMISSION')
            ).exclude(application_type__in=CAND_ENROLL_APP_TYPES).first()

        except ExamApplication.DoesNotExist:
            messages.error(self.request, "You don't have an application record yet. Please start from the beginning.")
            self.application = None

    def get_context_data(self, *args, **kwargs):

        context = super().get_context_data(**kwargs)
        context['is_advanced'] = self.is_advanced
        if self.is_advanced:
            for i in range(1, 4):
                identifier = "criterion_" + str(i) + "_subtitle"
                context[identifier] = "ASC " + self.application.application_type + " Exam Criterion " + str(i)
            context['criteria_guidelines_url'] = self.guidelines_dict[self.application.application_type]

        criteria = self.application.submission_category.questions.all().order_by("sort_number")
        context['questions'] = criteria

        answer_list = []
        for question in criteria:
            answer_list.append(question.answers.filter(content=self.application).first())
        context['answers'] = answer_list

        qa_dict = dict(zip(criteria, answer_list))
        context['qa_dict'] = qa_dict

        for i, answer in enumerate(answer_list):
            if answer:
                if answer.text:
                    context['answer_word_count_%s' % (i+1)] = len(answer.text.split())
                else:
                    context['answer_word_count_%s' % (i+1)] = 0
            else:
                context['answer_word_count_%s' % (i+1)] = 0

        return context

    def get_form_kwargs(self):

        form_kwargs = super().get_form_kwargs()
        form_kwargs['publish_status'] = self.application.publish_status

        return form_kwargs

    def form_invalid(self, form):
        messages.error(self.request, "An error occurred. Please see below for any instructions.")

        return super().form_invalid(form)

    def form_valid(self, form):

        self.get_exam_initial()

        form_obj = form.save()
        form_obj.exam = self.application.exam
        form_obj.application = self.application
        form_obj.contact = self.request.user.contact
        form_obj.save()

        return super().form_valid(form)


class ExamDegreeHistoryView(AuthenticateLoginMixin, FormView):
    title = "Degrees"
    template_name = 'exam/newtheme/application/degree-history.html'
    form_class = ExamDegreeHistoryForm
    application_category = None
    product = None
    the_degrees = None
    required_experience = None

    def get_initial(self):
        initial = super().get_initial()
        initial["publish_status"] = self.application.publish_status
        formset_initial = [initial for i in range(self.the_degrees.count() + 1)]

        return formset_initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["queryset"] = self.the_degrees

        return kwargs

    def get_form_class(self):

        return modelformset_factory(ApplicationDegree, self.form_class, extra=1)

    def get(self, request, *args, **kwargs):
        self.master_id = kwargs.get("master_id", None)
        self.get_exam_initial()
        self.application_category = self.application.submission_category
        self.the_degrees = self.application.applicationdegree_set.select_related("verification_document").all()
        self.required_experience = get_required_experience(self)

        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        """
        Returns the supplied success URL.
        """
        if self.request.POST.get('save_and_add_another'):
            messages.success(self.request, "Your school was added successfully. You may add another.")
            self.success_url = reverse_lazy("exam_degree_history", kwargs={"master_id": self.application.master_id})
        elif self.request.POST.get('save_and_continue'):
            messages.success(self.request, "Your education history has been updated successfully!")
            self.success_url = reverse_lazy("exam_job_history", kwargs={"master_id": self.application.master_id})
        else:
            messages.error(self.request, "An error has occurred. Could not update degree history.")
            self.success_url = reverse_lazy("exam_degree_history", kwargs={"master_id": self.application.master_id})
        url = force_text(self.success_url)
        return url

    def get_exam_initial(self):
        """
        get initial exam data
        """
        self.application = ExamApplication.objects.filter(
            Q(publish_status='SUBMISSION') | Q(publish_status='EARLY_RESUBMISSION')
        ).get(
            master__id=self.master_id,
            application_status='N'
        )

        if not self.application:
            messages.error(self.request, "We could not locate an unsubmitted application.")

    def get_context_data(self, *args, **kwargs):

        context = super().get_context_data(**kwargs)

        context["form_set"] = context["form"]

        return context

    def post(self, request, *args, **kwargs):

        self.master_id = kwargs.get("master_id", None)
        self.get_exam_initial()
        self.the_degrees = self.application.applicationdegree_set.select_related("verification_document").all()
        self.required_experience = get_required_experience(self)

        return super().post(request, *args, **kwargs)

    def form_valid(self, form):

        upload_type = UploadType.objects.filter(code="EXAM_APPLICATION_EDUCATION").first()

        for degree_form in form:
            degree = degree_form.save(commit=False)

            if degree.school or degree.other_school:

                degree.exam = self.application.exam
                degree.application = self.application
                degree.contact = self.request.user.contact

                cleaned_data = degree_form.cleaned_data

                if cleaned_data.get("uploaded_file", None):

                    verif_docum = VerificationDocument.objects.filter(applicationdegree=degree).first()
                    if not verif_docum:
                        verif_docum = VerificationDocument(
                            content=self.application,
                            upload_type=upload_type,
                            publish_status=self.application.publish_status
                        )
                    verif_docum.uploaded_file = cleaned_data.get("uploaded_file", None)
                    verif_docum.save()

                    degree.verification_document = verif_docum
                degree.publish_status = self.application.publish_status
                degree.save()

        self.the_degrees = self.application.applicationdegree_set.select_related("verification_document").all()
        self.required_experience = get_required_experience(self)
        messages.success(
            self.request,
            "Based on your education history your required years of professional planning experience is: %s years." % self.required_experience
        )

        return super().form_valid(form)


class ExamJobHistoryView(AuthenticateLoginMixin, FormView):
    title = "Jobs"
    template_name = 'exam/newtheme/application/job-history.html'
    form_class = ExamJobHistoryForm
    years_experience = -1
    required_experience = -1
    is_advanced = False
    application = None
    # product = None
    the_degrees = None
    the_jobs = None

    approved_cand_enroll_app = None

    def get(self, request, *args, **kwargs):
        self.master_id = kwargs.get("master_id", None)
        self.get_exam_initial()
        self.the_degrees = self.application.applicationdegree_set.select_related("verification_document").all()
        self.the_jobs = self.application.applicationjobhistory_set.select_related("verification_document").all()
        self.required_experience = get_required_experience(self)
        self.years_experience = get_years_experience(self)

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        upload_type = UploadType.objects.filter(code="EXAM_APPLICATION_JOB").first()

        for job_form in form:

            job = job_form.save(commit=False)

            if job.title or job.company:

                job.exam = self.application.exam
                job.application = self.application
                job.contact = self.request.user.contact

                cleaned_data = job_form.cleaned_data

                if cleaned_data.get("uploaded_file", None):

                    verif_docum = VerificationDocument.objects.filter(applicationjobhistory=job).first()
                    if not verif_docum:
                        verif_docum = VerificationDocument(
                            content=self.application,
                            upload_type=upload_type,
                            publish_status=self.application.publish_status
                        )
                    verif_docum.uploaded_file = cleaned_data.get("uploaded_file", None)
                    verif_docum.save()

                    job.verification_document = verif_docum
                job.publish_status = self.application.publish_status
                job.save()

        self.the_degrees = self.application.applicationdegree_set.select_related("verification_document").all()
        self.the_jobs = self.application.applicationjobhistory_set.select_related("verification_document").all()
        self.required_experience = get_required_experience(self)
        self.years_experience = get_years_experience(self)

        return super().form_valid(form)

    def form_invalid(self, form):

        self.required_experience = get_required_experience(self)
        self.years_experience = get_years_experience(self)
        messages.error(self.request, "An error occurred. Please see below for any instructions.")

        return super().form_invalid(form)

    def post(self, request, *args, **kwargs):
        self.master_id = kwargs.get("master_id", None)
        self.get_exam_initial()
        self.the_degrees = self.application.applicationdegree_set.select_related("verification_document").all()
        self.the_jobs = self.application.applicationjobhistory_set.select_related("verification_document").all()
        self.required_experience = get_required_experience(self)
        self.years_experience = get_years_experience(self)

        return super().post(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial["publish_status"] = self.application.publish_status  # "SUBMISSION"
        formset_initial = [initial for i in range(self.the_jobs.count() + 1)]

        return formset_initial

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["queryset"] = self.the_jobs
        return form_kwargs

    def get_form_class(self):

        return modelformset_factory(ApplicationJobHistory, self.form_class, extra=1)

    def get_success_url(self):
        """
        Returns the supplied success URL.
        """
        if self.request.POST.get('save_and_add_another'):
            messages.success(self.request, "Your Job was added successfully. You may add another.")
            self.success_url = reverse_lazy("exam_job_history", kwargs={"master_id": self.application.master_id})
        elif self.years_experience < self.required_experience and self.request.POST.get('save_and_continue'):
            messages.error(
                self.request,
                "You have not entered enough planning job experience to be able to submit application."
                "\n %s more years experience required."
                % round((self.required_experience - self.years_experience), 1)
            )
            self.success_url = reverse_lazy("exam_job_history", kwargs={"master_id": self.application.master_id})
        elif self.request.POST.get('save_and_continue'):
            self.success_url = reverse_lazy("exam_criteria", kwargs={"master_id": self.application.master_id})
        else:
            messages.error(self.request, "Your Job could not be added. An error occured.")
            # TODO: This is pretty shitty UX...
            raise Http404("Incorrect submit.")

        url = force_text(self.success_url)

        return url

    def get_exam_initial(self):

        self.is_advanced = False

        if self.request.user.groups.filter(name='aicpmember'):
            self.is_advanced = True

        if self.is_advanced:
            self.form_class = ASCExamJobHistoryForm
        else:
            self.form_class = ExamJobHistoryForm

        self.application = ExamApplication.objects.filter(
            master__id=self.master_id,
            application_status='N'
        ).exclude(
            application_type__in=CAND_ENROLL_APP_TYPES
        ).get(
            Q(publish_status='SUBMISSION') | Q(publish_status='EARLY_RESUBMISSION')
        )

        if self.application and self.application.application_type in CAND_CERT_APP_TYPES:
            self.approved_cand_enroll_app = ExamApplication.objects.filter(
                contact=self.request.user.contact,
                application_type='CAND_ENR',
                application_status__in=APPROVED_STATUSES
            ).first()

            if self.approved_cand_enroll_app is not None:
                # make publish status of new objects agree with record they're copied onto:
                publish_status = self.application.publish_status

                if self.application.applicationdegree_set.all().count() == 0:
                    for cand_enr_degree in self.approved_cand_enroll_app.applicationdegree_set.all():
                        # TODO: What is going on here?
                        if True: # they do not have to upload verif doc again
                            verification_document = cand_enr_degree.verification_document
                            verification_document.id = None
                            # no this is only for regular early bird exam applicants:
                            # verification_document.publish_uuid=self.approved_cand_enroll_app.verification_document.publish_uuid
                            verification_document.publish_status=publish_status
                            verification_document.save()
                        else: # they do have to upload verif doc again
                            verification_document = None

                        level = "B"
                        is_planning = False
                        is_pab = False
                        csa = CustomSchoolaccredited.objects.filter(seqn=cand_enr_degree.school_seqn).first()

                        if csa:
                            level = csa.degree_level or cand_enr_degree.level
                            is_planning = True
                            is_pab = csa.school_program_type in ['PAB','ACSP'] or cand_enr_degree.pab_accredited
                        else:
                            level = cand_enr_degree.level
                            is_planning = cand_enr_degree.is_planning
                            is_pab = cand_enr_degree.pab_accredited

                        degree_obj = ApplicationDegree.objects.create(
                            # do not tie this record to the enroll app record:
                            # publish_uuid=denied_degree.publish_uuid,
                            application=self.application,
                            complete = cand_enr_degree.complete,
                            contact=self.request.user.contact,
                            graduation_date = cand_enr_degree.graduation_date,
                            is_current = cand_enr_degree.is_current,
                            is_planning = is_planning,
                            level = level,
                            level_other = cand_enr_degree.level_other,
                            other_school = cand_enr_degree.other_school,
                            pab_accredited = is_pab,
                            program = cand_enr_degree.program,
                            publish_status=publish_status,
                            school = cand_enr_degree.school,
                            school_id = cand_enr_degree.school_id,
                            school_seqn = cand_enr_degree.school_seqn,
                            student_id = cand_enr_degree.student_id,
                            verification_document = verification_document,
                            year_in_program = cand_enr_degree.year_in_program,
                            )
                        # self.application.applicationdegree_set.add(degree_obj)
                        # do not tie this record to the enroll app record:
                        # if self.early_bird:
                        #     degree_obj.publish_uuid = denied_degree.publish_uuid

                        degree_obj.application = self.application

    def get_context_data(self, *args, **kwargs):

        context = super().get_context_data(**kwargs)

        context["form_set"] = context["form"]
        context["planning_experience"] = self.years_experience
        context["required_planning_experience"] = self.required_experience
        context["is_advanced"] = self.is_advanced

        return context


class ExamRegistrationView(AuthenticateMemberMixin, FormView):
    exam = None
    application = None
    template_name = 'exam/newtheme/registration/form.html'
    form_class = ExamRegistrationForm
    success_url = reverse_lazy("exam_code_of_ethics")
    is_advanced = False
    no_approval = False
    expired_approval = False

    def get_exam_initial(self):
        """
        get initial exam data
        """
        if self.request.user.groups.filter(name='aicpmember'):
            self.is_advanced = True

        self.exam = Exam.objects.filter(
            is_advanced=self.is_advanced,
            registration_start_time__lt=timezone.now(),
            registration_end_time__gt=timezone.now()
        ).first()

        if self.exam is not None:
            allowed_application_exams = list(self.exam.previous_exams.all()) + [self.exam]
            self.application = ExamApplication.objects.filter(
                contact=self.request.contact,
                application_status="A",
                exam__in=allowed_application_exams
            ).exclude(
                application_type__contains="CAND"
            ).first()
            if self.application is None:
                self.expired_approval = ExamApplication.objects.filter(
                    contact=self.request.contact,
                    application_status="A"
                ).exists()
                if not self.expired_approval:
                    self.no_approval = True
        else:
            self.application = None

        self.registration = ExamRegistration.objects.filter(exam=self.exam, contact=self.request.contact).last()
        if self.registration is not None:
            self.purchase = self.registration.purchase
        else:
            self.purchase = None

    def get_form(self, *args, **kwargs):
        """
        Check if the user already saved registration. If so, then show
        the form populated with those details, to let user change them.
        """

        self.get_exam_initial()

        if self.registration:
            return self.form_class(instance=self.registration, **self.get_form_kwargs())
        else:
            return self.form_class(**self.get_form_kwargs())

    def get_context_data(self, *args, **kwargs):
        # TO DO... is get_context_data the best place for this logic?

        self.get_exam_initial()

        if self.purchase and self.purchase.order:
            kwargs['error'] = 'registered'
        elif self.no_approval:
            kwargs['error'] = 'no_application'
        elif self.expired_approval:
            kwargs['error'] = 'expired_approval'
        elif not self.exam:
            kwargs['error'] = 'registration_ended'

        context = super().get_context_data(**kwargs)
        context["is_advanced"] = self.is_advanced

        return context


    # def dispatch(self, request, *args, **kwargs):
    #     try:
    #         # must determine if they are taking the regular or advanced exam...
    #         is_advanced = False

    #         if request.user.groups.filter(name='aicp_cm'):
    #             is_advanced = True

    #         self.exam = Exam.objects.get(is_advanced = is_advanced, registration_start_time__lt=datetime.datetime.now(), registration_end_time__gt=datetime.datetime.now())
    #         allowed_application_exams = list(self.exam.previous_exams.all()) + [self.exam]

    #         try:
    #             # TO DO... replace with appropriate MessageText object
    #             self.application = ExamApplication.objects.filter(contact=self.request.contact, status="A", exam__in=allowed_application_exams).first()
    #         except ExamApplication.DoesNotExist:
    #             messages.error(self.request, "Our records indicate that you are currently not approved to sit for the exam.")

    #     except Exam.DoesNotExist:
    #         # TO DO... replace with appropriate MessageText object
    #         messages.error(self.request, "The exam registration window has passed.")

    #     return super().dispatch(request, *args, **kwargs)


    def form_valid(self, form):
        # TO DO... get associate application here!
        form_obj = form.save(commit=False)
        form_obj.exam = self.exam
        form_obj.application = self.application
        form_obj.contact = self.request.user.contact

        form_obj.save()
        return super().form_valid(form)


class ExamCodeOfEthicsView(AuthenticateLoginMixin, FormView):

    template_name = 'exam/newtheme/registration/code-of-ethics.html'
    form_class = ExamCodeOfEthicsForm
    success_url = "/store/cart/"

    product = None

    def get_exam_initial(self):
        """
        get initial exam data
        """

        self.is_advanced = False
        if self.request.user.groups.filter(name='aicpmember'):
            self.is_advanced = True

        # TODO: This is assuming only one will get returned with these query parameters and needlessly checking
        # for so below.
        self.exam = Exam.objects.get(
            is_advanced=self.is_advanced,
            registration_start_time__lt=timezone.now(),
            registration_end_time__gt=timezone.now()
        )
        if self.exam:
            allowed_application_exams = list(self.exam.previous_exams.all()) + [self.exam]

        # try:
            self.application = ExamApplication.objects.filter(
                contact=self.request.contact, application_status="A", exam__in=allowed_application_exams
                ).exclude(application_type__contains="CAND").first()
        # except ExamApplication.DoesNotExist:
        #     self.application = None
        # else:
        #     self.application = None
            # print("SELF.APPLICATION IS ----------------", self.application)
        self.registration = ExamRegistration.objects.filter(exam=self.exam, contact=self.request.contact).last()
        if self.registration:
            self.purchase = self.registration.purchase
        else:
            self.purchase = None

        if not self.registration.exam.is_advanced:
            self.product = ProductCart.objects.get(code='EXAM_REGISTRATION_AICP')
        elif self.registration.application.application_type == 'CEP':
            self.product = ProductCart.objects.get(code='EXAM_REGISTRATION_CEP')
        elif self.registration.application.application_type == "CTP":
            self.product = ProductCart.objects.get(code='EXAM_REGISTRATION_CTP')
        elif self.registration.application.application_type == "CUD":
            self.product = ProductCart.objects.get(code='EXAM_REGISTRATION_CUD')

    def get_context_data(self, *args, **kwargs):
        # TO DO... is get_context_data the best place for this logic?

        self.get_exam_initial()
        context = super().get_context_data(**kwargs)
        if self.purchase and self.purchase.order:
            context['error'] = 'registered'
        elif not self.application:
            context['error'] = 'no_application'
        elif not self.exam:
            context['error'] = 'registration_ended'

        return context

    def get_form(self, *args, **kwargs):
        """
        Check if the user already saved registration. If so, then show
        the form populated with those details, to let user change them.
        """

        self.get_exam_initial()

        if self.registration:
            return self.form_class(instance=self.registration, **self.get_form_kwargs())
        else:
            return self.form_class(**self.get_form_kwargs())

    def form_valid(self, form):

        self.get_exam_initial()
        form_obj = form.save(commit=False)

        self.purchase = self.product.add_to_cart(
            contact=self.request.contact,
            quantity=1,
            code=self.registration.registration_type
        )
        form_obj.purchase = self.purchase

        if self.registration.registration_type == '':
            form_obj.registration_type =  self.registration.application.application_type + "_A"
        form_obj.save()

        return super().form_valid(form)


class ExamRegistrationSearch(AuthenticateWebUserGroupMixin, AppContentMixin, TemplateView):

    template_name = 'exam/newtheme/pdo/exam-registration-search.html'
    form_class = ExamRegistrationSearchForm
    filter_kwargs = {}
    results = None
    model_class = ExamRegistration
    authenticate_groups = ["PDO"]
    show_rates = None
    chapter = None
    exam = None

    def get(self, request, *args, **kwargs):
        page = request.GET.get('page', None)
        if not page:
            request.session["search_query"] = request.GET # NOT CRAZY about using session here.. rework/refactor?
        self.create_pagination(request)
        return super().get(request, *args, **kwargs)

    def create_pagination(self, request):
        self.form = self.form_class(request.session.get("search_query"))
        if request.GET.get('submit') == "Search" or int(request.GET.get('page', 0)) > 1:
            filter_kwargs = self.form.get_query_map()

            first_name = filter_kwargs.get("first_name", None)
            last_name = filter_kwargs.get("last_name", None)
            username = filter_kwargs.get("username", None)
            pass_only = filter_kwargs.get("pass_only", None)
            self.chapter = filter_kwargs.get("chapter", None)
            self.show_rates = filter_kwargs.get("show_rates", None)
            self.exam = filter_kwargs.get("exam", None)

            search_results = self.model_class.objects.select_related(
                "contact"
            ).select_related(
                "contact__user"
            ).select_related(
                "exam"
            ).select_related(
                "purchase__order"
            ).filter(
                exam=self.exam,
                release_information=True,
                purchase__order__isnull=False,
            ).order_by(
                "contact__last_name"
            )
            if self.chapter:
                search_results = search_results.filter(contact__chapter=self.chapter)
            if first_name:
                search_results = search_results.filter(contact__first_name__icontains=first_name)
            if last_name:
                search_results = search_results.filter(contact__last_name__icontains=last_name)
            if username:
                search_results = search_results.filter(contact__username__icontains=username)
            if pass_only:
                search_results = search_results.filter(is_pass=True)

            page = request.GET.get('page', 1)
            paginator = Paginator(search_results or [], 100) # Shows only 10 records per page
            try:
                self.results = paginator.page(page)
            except PageNotAnInteger: # If page is not an integer, deliver first page
                self.results = paginator.page(1)
            except EmptyPage:  # If page is out of range, deliver last page of results
                self.results = paginator.page(paginator.num_pages)
            except Exception as e:
                print("ERROR: " + str(e))


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.show_rates and self.exam:
            cumulative_results = self.model_class.objects.select_related("contact")\
                        .filter(
                                exam=self.exam,
                                is_pass__isnull=False,
                                )
            exam_list = [c.is_pass for c in cumulative_results.all()]
            context["pass_count"] = exam_list.count(True)
            context["fail_count"] = exam_list.count(False)
            context["pass_rate"] = round(context["pass_count"] / (context["pass_count"] + context["fail_count"]) * 100)

            if self.chapter:
                cumulative_results_chapter = cumulative_results.filter(contact__chapter=self.chapter)
                exam_list_chapter = [c.is_pass for c in cumulative_results_chapter.all()]
                context["pass_count_chapter"] = exam_list_chapter.count(True)
                context["fail_count_chapter"] = exam_list_chapter.count(False)
                context["pass_rate_chapter"] = round(context["pass_count_chapter"] / (context["pass_count_chapter"] + context["fail_count_chapter"] ) * 100)

        context["form"] = self.form
        context["results"] = self.results
        context["search"] = self.request.GET.get('submit', None)
        context["page"] = self.request.GET.get('page', None)
        return context


class AicpProratedDuesProductView(AuthenticateLoginMixin, FormView):
    template_name = "exam/newtheme/aicp-prorated-dues-product.html"
    form_class = forms.Form
    purchase = None
    success_url = None

    prorate_balance = None
    aicp_balance = None
    member_balance = None

    prorate_bill_thru = None
    prorate_bill_begin = None
    prorate_paid_thru = None

    aicp_bill_thru = None
    aicp_paid_thru = None
    member_sub = None

    def setup(self):
        contact = self.request.user.contact
        self.contact = contact

        subs = contact.get_imis_subscriptions()

        member_sub = subs.filter(product_code="APA", status='A').first()
        aicp_sub = subs.filter(product_code="AICP", status='A').first()
        self.member_sub = member_sub

        prorate_sub = subs.filter(product_code="AICP_PRORATE", status='A').first()

        if prorate_sub is not None:
            self.prorate_bill_thru = getattr(prorate_sub, "bill_thru", None)
            self.prorate_bill_begin = getattr(prorate_sub, "bill_begin", None)
            self.prorate_paid_thru = getattr(prorate_sub, "paid_thru", None)
            self.prorate_balance = getattr(prorate_sub, "balance", 0)

        if aicp_sub is not None:
            self.aicp_balance = getattr(aicp_sub, "balance", 0)
            self.aicp_bill_thru = getattr(aicp_sub, "bill_thru", None)
            self.aicp_paid_thru = getattr(aicp_sub, "paid_thru", None)

        if member_sub is not None:
            self.member_balance = getattr(member_sub, "balance", 0)

        if prorate_sub and not self.prorate_bill_begin:
            messages.error(
                self.request,
                "Sorry, this page is temporarily unavailable. Please check back later or contact AICPexam@planning.org."
            )

        elif prorate_sub and not member_sub:
            messages.error(
                self.request,
                "Sorry, this page is accessible only to APA members who recently passed the AICP Certification Exam. "
                "Learn more about joining APA "
                "<a href='https://www.planning.org/membership/' target='_blank'>here.</a>"
            )

        elif (self.prorate_balance == 0 and contact.member_type != 'STU')\
                or (contact.member_type == "STU" and self.prorate_paid_thru is not None):
            date = ''
            if self.prorate_paid_thru:
                date = self.prorate_paid_thru.date().isoformat()
            messages.success(
                self.request,
                "Your AICP Initial Dues are paid. Your membership period expires %s. Thank you for your payment." % date
            )

        elif self.aicp_balance == 0:
            date = ''
            if self.aicp_paid_thru:
                date = self.aicp_paid_thru.date().isoformat()
            messages.success(
                self.request,
                "Your AICP Dues are paid. Your membership period expires %s. Thank you for your payment." % date
            )

        elif member_sub and not prorate_sub and not aicp_sub:
            messages.error(
                self.request,
                "Sorry, this page is accessible only to APA members who recently passed the AICP Certification Exam. "
                "If you are a former AICP member interested in reinstating your membership, learn more "
                "<a href='https://www.planning.org/membership/renewal/' target='_blank'>here.</a>"
            )

        elif not member_sub and contact.member_type != "STU":
            messages.error(
                self.request,
                "Sorry, this page is accessible only to APA members who recently passed the AICP Certification Exam. "
                "If you are a former AICP member interested in reinstating your membership, learn more "
                "<a href='https://www.planning.org/membership/renewal/' target='_blank'>here.</a>"
            )

        elif member_sub and aicp_sub and not prorate_sub:
            bal = self.aicp_balance
            date = datetime.datetime.strftime(self.aicp_paid_thru, '%Y-%m-%d')
            messages.success(
                self.request,
                "You do not have an AICP Initial Dues balance. Your regular AICP membership balance is $%s. "
                "Your AICP membership period expires %s." % (bal, date))

    def get(self, request, *args, **kwargs):
        self.setup()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.setup()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        if self.prorate_balance \
                or (self.contact.member_type == "STU" and self.prorate_paid_thru is None):
            product = ProductCart.objects.get(code='MEMBERSHIP_AICP_PRORATE')
            self.purchase = product.add_to_cart(
                contact=self.request.contact,
            )

        elif (not self.prorate_balance and not self.member_balance and self.contact.member_type != "STU") \
                or (self.contact.member_type == "STU" and self.prorate_paid_thru is not None):
            self.success_url = reverse_lazy("aicp_dues_prorated")
            messages.success(
                self.request,
                "Your APA membership and AICP initial subscription dues are paid. No further action is necessary."
            )

        else:
            self.success_url = reverse_lazy("aicp_dues_prorated")
            messages.error(self.request, "An error occurred. Please contact customer service for assistance.")

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['prorate_balance'] = getattr(self, "prorate_balance", 0)
        context['aicp_balance'] = getattr(self, "aicp_balance", 0)
        context["member_balance"] = getattr(self, "member_balance", 0)
        context['prorate_bill_thru'] = getattr(self, "prorate_bill_thru", '')
        context['aicp_bill_thru'] = getattr(self, "aicp_bill_thru", '')
        context['member_sub'] = self.member_sub
        context['member_type'] = self.contact.member_type
        context['prorate_paid_thru'] = getattr(self, "prorate_paid_thru", '')

        return context

    def get_success_url(self):
        """
        Returns the supplied success URL.
        """
        if not self.success_url:
            if self.request.POST.get('join_renew'):
                messages.success(self.request, "Join or renew APA membership and pay initial AICP dues.")
                self.success_url = "/join/account/"
            elif self.request.POST.get('add_to_cart'):
                messages.success(self.request, "Added AICP initial dues to cart.")
                self.success_url = reverse_lazy("store:cart")
            else:
                messages.error(self.request, "An error occurred. Please contact customer service.")
                raise Http404("No match to available options.")
        return super().get_success_url()


# *****
# FAICP
# *****
class FAICPListView(AppContentMixin, TemplateView):
    template_name = "exam/newtheme/faicp/faicp.html"
    content_url = "/faicp/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fellows = Contact.objects.filter(designation__contains='FAICP').select_related("individualprofile", "user"
            ).prefetch_related("user__groups").order_by("last_name")

        caps = string.ascii_uppercase
        sorted_fellows = []
        for let in caps:
            key = let
            val = [f for f in fellows if f.last_name[0] == let]
            sorted_fellows.append((key, val))

        let1 = caps.index('G')
        let2 = caps.index('O')
        end = len(caps)

        context["fellows1"] = [t for t in sorted_fellows if t[0] in caps[0:let1]]
        context["fellows2"] = [t for t in sorted_fellows if t[0] in caps[let1:let2]]
        context["fellows3"] = [t for t in sorted_fellows if t[0] in caps[let2:end]]

        logged_in_user = self.request.user if self.request.user.is_authenticated() else None
        context["logged_in_user"] = logged_in_user

        return context


class FAICPStatementView(TemplateView):
    template_name = "exam/newtheme/faicp/faicp_statement.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        username = kwargs.pop("username", None)

        fellow = Contact.objects.get(user__username=username)

        context["fellow"] = fellow

        return context


# *****
# ASC
# *****
class ASCListView(AppContentMixin, TemplateView):
    template_name = "exam/newtheme/asc/asc.html"
    content_url = "/asc/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cep_group = Contact.objects.filter(designation__contains='CEP'
            ).select_related("individualprofile", "user"
            ).prefetch_related("user__groups").order_by("last_name")
        ctp_group = Contact.objects.filter(designation__contains='CTP'
            ).select_related("individualprofile", "user"
            ).prefetch_related("user__groups").order_by("last_name")
        cud_group = Contact.objects.filter(designation__contains='CUD'
            ).select_related("individualprofile", "user"
            ).prefetch_related("user__groups").order_by("last_name")

        context["cep_group"] = cep_group
        context["ctp_group"] = ctp_group
        context["cud_group"] = cud_group

        logged_in_user = self.request.user if self.request.user.is_authenticated() else None
        context["logged_in_user"] = logged_in_user

        return context


class ASCExperienceView(TemplateView):
    template_name = "exam/newtheme/asc/asc_experience.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        username = kwargs.pop("username", None)

        asc_holder = Contact.objects.get(user__username=username)

        context["asc_holder"] = asc_holder
        return context

###############################################
# AICP Candidate Program
###############################################

class AICPCandidateBasicInfoView(AuthenticateMemberMixin, CandidatePortalAccessMixin, FormView):
    title = "AICP Candidate Basic Info"
    template_name = 'exam/newtheme/candidate/basic.html'
    form_class = AICPCandidateBasicInfoForm
    success_url = None
    application = None
    application_category = None
    submission_category = None
    contact = None
    current_exam = None
    app_status = None

    def get(self, request, *args, **kwargs):
        self.get_candidate_app()

        url = force_text(self.success_url)
        if url == "/aicp/candidate/":
            return redirect(url)

        return super().get(request, *args, **kwargs)

    def get_candidate_app(self):
        self.contact = self.request.user.contact
        now=timezone.now()
        self.current_exam = Exam.objects.filter(registration_end_time__gte=now).order_by("registration_end_time").first()
        # first query for all unsubmitted or "enrolled" apps -- any exam period
        self.application = ExamApplication.objects.filter(
            contact=self.contact, application_status__in=CAND_PORTAL_ACCESS_STATUSES, publish_status='DRAFT', application_type='CAND_ENR')

        if self.application and self.application.count() > 1:
            raise Http404("An error has occured -- duplicate Candidate Enrollment Applications.\nPlease contact customer service.")
        elif self.application and self.application.count() == 1:
            self.application = self.application.first()

        # if no unsubmitted, then query for most recent and validate status (for the sake of redirecting)
        if not self.application:
            self.application = ExamApplication.objects.filter(
                contact=self.contact, publish_status='DRAFT', application_type='CAND_ENR'
                ).exclude(application_status__in=['D','D_C']).order_by("created_time").first()

        self.app_status = getattr(self.application, "application_status", None)
        self.validate_aicp()
        if self.app_status:
            self.validate_status(self.app_status)

        self.application_category = getattr(self.application, "submission_category", None)

    def get_context_data(self, *args, **kwargs):

        kwargs['app_status'] = self.app_status
        kwargs['contact'] = self.contact
        context = super().get_context_data(**kwargs)

        return context

    def post(self, request, *args, **kwargs):
        self.get_or_create_candidate_app()

        self.application_category = self.application.submission_category

        return super().post(request, *args, **kwargs)

    def get_or_create_candidate_app(self):
        self.contact = self.request.user.contact
        now=timezone.now()
        self.current_exam = Exam.objects.filter(registration_end_time__gte=now).order_by("registration_end_time").first()

        queryset = ExamApplication.objects.filter(
            contact=self.contact, publish_status='DRAFT', application_type='CAND_ENR',
            application_status__in=CAND_PORTAL_ACCESS_STATUSES)

        if queryset.count() == 1:
            self.application = queryset.first()
        elif queryset.count() == 0:
            self.application = None
        elif queryset.count() > 1:
            raise Http404("Error: More than one active enrollment application was found.")

        if not self.application:
            self.application = ExamApplication.objects.create(
                contact=self.contact, publish_status='DRAFT', application_type='CAND_ENR',
                application_status='N', exam=self.current_exam)

        self.application_category = getattr(self.application, "submission_category", None)

    def get_success_url(self):
        """
        Returns the supplied success URL.
        """
        if self.request.POST.get('student_enroll'):
            self.success_url = reverse_lazy("candidate_education", kwargs={"enroll_type":"student_enroll"})
            messages.success(self.request,"You have selected to enroll in the AICP Candidate Program as a student.")
        elif self.request.POST.get('full_enroll'):
            self.success_url = reverse_lazy("candidate_education", kwargs={"enroll_type":"full_enroll"})
            messages.success(self.request,"You have selected to enroll in the AICP Candidate Program as a graduate.")

        self.app_status = getattr(self.application, "application_status", None)
        self.validate_aicp()
        if self.app_status:
            self.validate_status(self.app_status)
        else:
            raise Http404("Error condition: AICP enrollment application not found.")

        url = force_text(self.success_url)

        return url

    def get_form_kwargs(self):
        kwargs = super(AICPCandidateBasicInfoView, self).get_form_kwargs()
        kwargs.update({
         'request' : self.request
        })
        kwargs['initial']['email'] = self.contact.email
        kwargs['initial']['chapter'] = self.contact.chapter

        return kwargs

    def form_valid(self, form):

        # ONLY ALLOW "CAND_ENR" HERE?
        # self.application_type = self.application.get("application_type", "CAND_ENR")
        self.submission_category_code = "CAND_ENR"
        self.application_category = ApplicationCategory.objects.filter(code=self.submission_category_code)[0]
        # self.submission_category = self.application_category
        self.application.submission_category = self.application_category
        self.application.save()

        form_obj = form.save(commit=False)
        form_obj.application = self.application
        form_obj.contact = self.contact

        form_obj.save()

        return super().form_valid(form)


class AICPCandidateEducationView(AuthenticateMemberMixin, CandidatePortalAccessMixin, FormView):
    title = "AICP Candidate Education"
    template_name = 'exam/newtheme/candidate/education.html'
    form_class = AICPCandidateEducationForm
    success_url = '/certification/candidate/enrollment/ethics/'
    degree = None
    application = None
    enroll_type = None
    app_status = None

    def get(self, request, *args, **kwargs):
        self.enroll_type = kwargs.get("enroll_type", None)
        self.get_candidate_app()

        url = force_text(self.success_url)
        if url == "/aicp/candidate/":
            return redirect(url)

        self.application_category = getattr(self.application, "submission_category", None)

        self.app_status = getattr(self.application, "application_status", None)
        self.validate_aicp()
        if self.app_status:
            self.validate_status(self.app_status)
        else:
            raise Http404("Error condition: AICP enrollment application not found.")

        url = force_text(self.success_url)
        if url == "/aicp/candidate/":
            return redirect(url)

        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        """
        Returns the supplied success URL.
        """
        if self.request.POST.get('save_and_exit'):
            self.success_url = "/aicp/candidate/"
            messages.success(self.request,"Your enrollment application has been saved.")
        elif self.request.POST.get('save_and_continue'):
            self.success_url = "/certification/candidate/enrollment/ethics/"
            messages.success(self.request,"You may continue your enrollment in the AICP Candidate Program.")

        self.app_status = getattr(self.application, "application_status", None)
        self.validate_aicp()
        if self.app_status:
            self.validate_status(self.app_status)
        else:
            raise Http404("Error condition: AICP enrollment application not found.")

        url = force_text(self.success_url)

        return url

    def get_candidate_app(self):
        self.contact = self.request.user.contact
        try:
            self.application = ExamApplication.objects.get(
                contact=self.contact, application_status__in=CAND_PORTAL_ACCESS_STATUSES, publish_status='DRAFT', application_type='CAND_ENR')
        except:
            messages.error(self.request, "Update Graduation Status is only accessible to members with an in-process AICP Candidate enrollment application. We were unable to locate an in-process application for you. If you feel this to be in error, please contact customer service.")
            self.success_url = "/aicp/candidate/"
            return None
        self.degree = self.application.applicationdegree_set.first()

    def post(self, request, *args, **kwargs):
        self.enroll_type = kwargs.get("enroll_type", None)
        self.get_candidate_app()
        self.application_category = getattr(self.application, "submission_category", None)
        # self.app_status = getattr(self.application, "application_status", None)
        # self.validate_aicp()
        # if self.app_status:
        #     self.validate_status(self.app_status)
        # else:
        #     raise Http404("Error condition: AICP enrollment application not found.")

        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(AICPCandidateEducationView, self).get_form_kwargs()
        kwargs.update({
         'request' : self.request,
         'enroll_type' : self.enroll_type
        })
        school_seqn = getattr(self.degree, "school_seqn", None)
        cust_school_accred = CustomSchoolaccredited.objects.filter(seqn=school_seqn).first()
        verif_doc = getattr(self.degree, "verification_document", None)
        CustomSchoolaccredited_id = getattr(cust_school_accred, "id", None)
        kwargs['initial']['degree_school'] = str(CustomSchoolaccredited_id)
        kwargs['initial']['degree_program'] = getattr(cust_school_accred, "seqn", None)
        kwargs['initial']['graduation_date'] = getattr(self.degree, "graduation_date", None)
        kwargs['initial']['uploaded_file'] = getattr(verif_doc, "uploaded_file", None)

        return kwargs

    def get_form(self, form_class=None):

        if not form_class:
            form_class = self.form_class

        if self.degree:
            return form_class(instance=self.degree, **self.get_form_kwargs())
        else:
            return form_class(**self.get_form_kwargs())

    def get_context_data(self, *args, **kwargs):

        kwargs['enroll_type'] = self.enroll_type
        context = super().get_context_data(**kwargs)

        return context

    def form_valid(self, form):

        upload_type = UploadType.objects.filter(code="EXAM_APPLICATION_EDUCATION").first()
        degree = form.save(commit=False)
        cleaned_data = form.cleaned_data
        school_imis_id = cleaned_data.get("degree_school", None)
        school = School.objects.filter(user__username=school_imis_id).first()
        if school:
            degree.school = school
            if self.enroll_type == 'student_enroll':
                degree.is_current = True
                degree.complete = False
            elif self.enroll_type == 'full_enroll':
                degree.is_current = False
                degree.complete = True
            else:
                raise Http404("Error condition: Enrollment path not found.")

            program_seqn = cleaned_data.get("degree_program", None)
            program = CustomSchoolaccredited.objects.filter(seqn=program_seqn).first()

            if program:
                degree.program = str(program)
                degree.school_seqn = program.seqn
                if program.degree_level and program.degree_level in [level[0] for level in DEGREE_LEVELS]:
                    degree.level = program.degree_level

            degree.application = self.application
            degree.contact = self.request.user.contact

            if cleaned_data.get("uploaded_file", None):

                verif_docum = VerificationDocument.objects.filter(applicationdegree=degree).first()
                if not verif_docum:
                    verif_docum = VerificationDocument(content=self.application, upload_type=upload_type, publish_status=self.application.publish_status)
                verif_docum.uploaded_file = cleaned_data.get("uploaded_file", None)
                verif_docum.save()

                degree.verification_document = verif_docum
            degree.publish_status = self.application.publish_status
            degree.save()

        return super().form_valid(form)


class AICPCandidateCodeOfEthicsView(AuthenticateMemberMixin, CandidatePortalAccessMixin, FormView):
    title = "Code of Ethics"
    template_name = 'exam/newtheme/candidate/code-of-ethics.html'
    form_class = ExamApplicationCodeOfEthicsForm
    master_id = None
    success_url = '/store/cart/'
    contact = None
    application = None
    application_category = None
    submission_category = None
    product = None
    app_status = None

    def get_candidate_app(self):
        self.contact = self.request.user.contact
        self.application = ExamApplication.objects.get(
            contact=self.contact, application_status__in=CAND_PORTAL_ACCESS_STATUSES, publish_status='DRAFT', application_type='CAND_ENR')

    def get_success_url(self):
        """
        Returns the supplied success URL.
        """
        if self.request.POST.get('purchase'):
            self.success_url = "/store/cart/"
        elif self.request.POST.get('update'):
            # messages.success(self.request,"Submitting your updated AICP Candidate Program Enrollment.")
            # self.success_url = reverse_lazy("update_success_page")
            self.success_url = "/aicp/candidate/"

        url = force_text(self.success_url)

        return url

    def get(self, request, *args, **kwargs):
        self.get_candidate_app()

        self.app_status = getattr(self.application, "application_status", None)
        self.validate_aicp()
        if self.app_status:
            self.validate_status(self.app_status)
        else:
            raise Http404("Error condition: AICP enrollment application not found.")

        url = force_text(self.success_url)
        if url == "/aicp/candidate/":
            return redirect(url)

        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial']['code_of_ethics'] = self.application.code_of_ethics
        return kwargs

    def get_form(self, form_class=None):

        if not form_class:
            form_class = self.form_class

        if self.application:
            return form_class(instance=self.application, **self.get_form_kwargs())
        else:
            return form_class(**self.get_form_kwargs())

    def post(self, request, *args, **kwargs):
        self.get_candidate_app()

        return super().post(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):

        kwargs['app_status'] = self.application.application_status

        context = super().get_context_data(**kwargs)

        return context

    def form_valid(self, form):

        form_obj = form.save(commit=False)
        form_obj.exam = self.application.exam
        form_obj.application = self.application
        form_obj.contact = self.contact

        self.application_category = getattr(self.application, "submission_category", None)
        # self.submission_category = self.application.submission_category
        content_live_product = self.application_category.product_master.content_live.product
        self.product = ProductCart(id=content_live_product.id)
        price_code = 'CAND_ENR'

        if self.application.application_status != 'EN':

            self.purchase = self.product.add_to_cart(
                contact = self.contact,
                quantity = 1,
                code = price_code
            )

            if self.purchase:
                self.purchase.content_master = self.application.master
                self.purchase.save()
            else:
                self.purchase = None

            form_obj.purchase = self.purchase

        else:
            self.purchase = Purchase.objects.filter(
                user = self.request.user,
                contact = self.contact,
                quantity = 1,
                product=self.product,
                content_master=self.application.master
                ).order_by('created_time').first()

            if not self.purchase:
                raise Http404("An error has occured: could not find a matching AICP enrollment purchase.\nPlease contact customer service.")

            self.application.application_status = 'P'
            self.application.save()
            messages.success(self.request,"Your updated AICP Candidate Program application has been submitted.")

            mail_context = dict(
                contact=self.contact,
            )
            email_template_code = CAND_ENROLL_EMAIL_TEMPLATES.get(self.application.application_status)
            mail_to = self.contact.email
            Mail.send(email_template_code, mail_to, mail_context)

        form_obj.save()

        return super().form_valid(form)

#****************************
# AICP CANDIDATE REGISTRATION
#****************************


class AICPCandidateRegistrationInfoView(AuthenticateMemberMixin, CandidateRegistrationAccessMixin, FormView):
    current_exam = None
    application = None
    template_name = 'exam/newtheme/candidate/reg-info.html'
    form_class = ExamRegistrationForm
    success_url = reverse_lazy("candidate_registration_ethics")
    no_approval = False
    expired_approval = False
    purchase = None

    def get(self, request, *args, **kwargs):
        self.get_candidate_app()

        url = force_text(self.success_url)
        if url == "/aicp/candidate/":
            return redirect(url)

        self.get_registration()

        return super().get(request, *args, **kwargs)

    def get_candidate_app(self):
        self.contact = self.request.user.contact
        now =timezone.now()
        # this can be different from the exam on the candidate enrollment app
        self.current_exam = Exam.objects.get(is_advanced=False, registration_start_time__lte=now, registration_end_time__gte=now)
        # then query for the approved candidate Draft app (there can only be one).
        # self.application = ExamApplication.objects.get(
            # contact=self.contact, application_status='A', publish_status='DRAFT', application_type='CAND_ENR')
        self.application = ExamApplication.objects.filter(
            contact=self.contact, publish_status='DRAFT', application_type='CAND_ENR'
            ).exclude(application_status__in=['D','D_C']).order_by("created_time")

        if self.application and self.application.count() > 1:
            raise Http404("An error has occured -- duplicate Candidate Enrollment Applications.\nPlease contact customer service.")
        elif self.application and self.application.count() == 1:
            self.application = self.application.first()

        self.app_status = getattr(self.application, "application_status", None)
        self.validate_aicp()
        self.validate_status(self.app_status)

        if self.application:
            self.degree = self.application.applicationdegree_set.first()
        # THIS IS THE LOGIC FROM REGULAR REG THAT SETS THE "AUTHENTICATION" VIEW VARS -- ADAPT:
        # AND PUT AUTHENTICATION STUFF IN SEPARATE METHODS ?? MAY NOT USE THIS--MAY DO DIFFERENTLY
            enrollment_approved_time = getattr(self.application, "submission_approved_time", None)
            if enrollment_approved_time and enrollment_approved_time > now:
                self.expired_approval = True
        else:
            self.no_approval = True

    def get_registration(self):
        self.registration = ExamRegistration.objects.filter(
            contact=self.contact,
            registration_type__contains='CAND',
            exam=self.current_exam)

        if self.registration and self.registration.count() > 1:
            raise Http404("An error has occured -- duplicate Exam Registrations.\nPlease contact customer service.")
        elif self.registration and self.registration.count() == 1:
            self.registration = self.registration.first()

        if self.registration:
            self.purchase = self.registration.purchase

    def post(self, request, *args, **kwargs):
        self.get_candidate_app()
        self.get_registration()
        self.get_or_create_registration()

        return super().post(request, *args, **kwargs)

    def get_or_create_registration(self):
        # self.contact = self.request.user.contact
        now =timezone.now()
        self.current_exam = Exam.objects.get(is_advanced=False, registration_start_time__lte=now, registration_end_time__gte=now)
        # to prevent erroneous duplication of registrations:
        if not self.registration:
            self.registration, created = ExamRegistration.objects.get_or_create(
                contact=self.contact,
                registration_type='CAND_ENR_A',
                exam=self.current_exam,
                code_of_ethics=self.application.code_of_ethics)
        # this is used in conjunction with get_context_data as a kind of authentication --
        # to prevent double registration, etc. -- This needs to happen on the get and post
        if self.registration:
            self.purchase = self.registration.purchase

    def get_form(self, form_class=None):

        if not form_class:
            form_class = self.form_class

        if self.registration:
            return form_class(instance=self.registration, **self.get_form_kwargs())
        else:
            return form_class(**self.get_form_kwargs())

    def get_context_data(self, *args, **kwargs):

        # PUT THIS IN AUTHENTICATION METHODS -- MIXIN??
        # OR MAY NOT GO THIS DIRECTION?
        if self.purchase and self.purchase.order:
            kwargs['error'] = 'registered'
        elif self.no_approval:
            kwargs['error'] = 'no_application'
        elif self.expired_approval:
            kwargs['error'] = 'expired_approval'
        elif not self.current_exam:
            kwargs['error'] = 'registration_ended'

        context = super().get_context_data(**kwargs)

        return context

    def form_valid(self, form):
        form_obj = form.save(commit=False)
        form_obj.exam = self.current_exam
        form_obj.application = self.application
        form_obj.contact = self.request.user.contact

        form_obj.save()
        return super().form_valid(form)


class AICPCandidateRegistrationCodeOfEthicsView(AuthenticateMemberMixin, CandidateRegistrationAccessMixin, FormView):

    template_name = 'exam/newtheme/candidate/reg-ethics.html'
    form_class = ExamCodeOfEthicsForm
    success_url = "/store/cart/"
    contact = None
    product = None
    no_approval = False
    expired_approval = False

    def get(self, request, *args, **kwargs):
        self.get_candidate_app()

        url = force_text(self.success_url)
        if url == "/aicp/candidate/":
            return redirect(url)

        self.get_registration()

        return super().get(request, *args, **kwargs)

    def get_candidate_app(self):
        self.contact = self.request.user.contact
        now =timezone.now()
        # this can be different from the exam on the candidate enrollment app
        self.current_exam = Exam.objects.get(is_advanced=False, registration_start_time__lte=now, registration_end_time__gte=now)
        # then query for the approved candidate Draft app (there can only be one).
        # self.application = ExamApplication.objects.get(
            # contact=self.contact, application_status='A', publish_status='DRAFT', application_type='CAND_ENR')

        self.application = ExamApplication.objects.filter(
            contact=self.contact, publish_status='DRAFT', application_type='CAND_ENR'
            ).exclude(application_status__in=['D','D_C']).order_by("created_time")

        if self.application and self.application.count() > 1:
            raise Http404("An error has occured -- duplicate Candidate Enrollment Applications.\nPlease contact customer service.")
        elif self.application and self.application.count() == 1:
            self.application = self.application.first()

        self.app_status = getattr(self.application, "application_status", None)
        self.validate_aicp()
        self.validate_status(self.app_status)

        if self.application:
        # THIS IS THE LOGIC FROM REGULAR REG THAT SETS THE "AUTHENTICATION" VIEW VARS -- ADAPT:
        # AND PUT AUTHENTICATION STUFF IN SEPARATE METHODS ?? MAY NOT USE THIS--MAY DO DIFFERENTLY
            enrollment_approved_time = getattr(self.application, "submission_approved_time", None)
            if enrollment_approved_time and enrollment_approved_time > now:
                self.expired_approval = True
        else:
            self.no_approval = True

    def get_registration(self):
        self.registration = ExamRegistration.objects.get(
            contact=self.contact,
            registration_type__contains='CAND',
            exam=self.current_exam)
        if self.registration:
            self.purchase = self.registration.purchase

    def post(self, request, *args, **kwargs):
        self.get_candidate_app()
        self.get_registration()

        return super().post(request, *args, **kwargs)

    def get_form(self, form_class=None):

        if not form_class:
            form_class = self.form_class

        if self.registration:
            return form_class(instance=self.registration, **self.get_form_kwargs())
        else:
            return form_class(**self.get_form_kwargs())

    def get_context_data(self, *args, **kwargs):

        # PUT THIS IN AUTHENTICATION METHODS -- MIXIN??
        # OR MAY NOT GO THIS DIRECTION?
        if self.purchase and self.purchase.order:
            kwargs['error'] = 'registered'
        elif self.no_approval:
            kwargs['error'] = 'no_application'
        elif self.expired_approval:
            kwargs['error'] = 'expired_approval'
        elif not self.current_exam:
            kwargs['error'] = 'registration_ended'

        context = super().get_context_data(**kwargs)

        return context

    def form_valid(self, form):

        form_obj = form.save(commit=False)

        form_obj.exam = self.current_exam
        form_obj.application = self.application
        form_obj.contact = self.contact

        self.product = ProductCart.objects.get(code='EXAM_REGISTRATION_AICP')

        self.purchase = self.product.add_to_cart(
            contact = self.request.contact,
            quantity = 1,
            code = self.registration.registration_type
        )
        form_obj.purchase = self.purchase

        # I THINK THIS IS FOR MANUAL REGISTRATIONS WITH NO APPLICATION??:
        # or something else?? -- must look at regular reg process -- views and forms --
        # to see what this is doing...
        if self.registration.registration_type == '':
            form_obj.registration_type =  self.registration.application.application_type + "_A"

        form_obj.save()

        return super().form_valid(form)
