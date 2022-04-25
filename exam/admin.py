import datetime

from pytz import timezone as pytz_timezone

from django.contrib import admin
from django import forms
from django.contrib import messages
from django.utils import timezone

from content.mail import Mail
from content.models.email_template import EmailTemplate
from submissions.models import Answer, AnswerReview
from submissions.admin import CategoryAdmin
from store.admin import OrderAdmin
from exam.prometric import Prometric

from uploads.models import UploadType
from cm.models import Log, Period

from .models import Exam, ExamApplication, ExamRegistration, \
    ApplicationCategory, ExamRegistrationOrder, ExamApplicationOrder, \
    ExamApplicationReview, ExamApplicationRole, ApplicationJobHistory, \
    ApplicationDegree, VerificationDocument, AICPCandidateApplication, \
    ENROLLED_STATUSES, CANDIDATE_REGISTRATION_TYPES, AICPCredentialData
from .forms import ExamApplicationReviewForm, ExamAnswerReviewForm, APPROVAL_CHOICES
from .utils import build_exams_list

central = pytz_timezone('US/Central')

from .settings import *

class ExamAdmin(admin.ModelAdmin):

    list_display = ("code", "title", "start_time", "end_time", "registration_start_time","registration_end_time","application_start_time","application_end_time")

    fieldsets = [

        (None, {
            "fields": (
                "title",
                ("code", "is_advanced"),
                ("start_time", "end_time"),
                ("registration_start_time", "registration_end_time"),
                ("application_start_time", "application_end_time"),
                "application_early_end_time",
                "previous_exams"
            ),
        }),
    ]
    filter_horizontal = ('previous_exams',)

class ExamRegistrationAdmin(admin.ModelAdmin):

    list_display = ("get_author_id", "contact","gee_eligibility_id", "exam",
        "registration_type", "get_email",)
    list_filter =  ["exam","registration_type"]
    search_fields = ["=contact__user__username", "=contact__first_name", "=contact__last_name"]
    show_prometric = True

    fieldsets = [

        (None, {
            "fields":( ("get_author_id"),
                        "contact",
                        "exam",
            			"registration_type",
                        "certificate_name",
                        "ada_requirement",
                        ("code_of_ethics", "release_information", "is_pass"),
                        ("gee_eligibility_id"),
            ),
        }),
    ]

    readonly_fields=["get_author_id", "get_email"]
    change_form_template = "admin/exam/examregistration/change-form.html"

    def get_author_id(self, obj):
        try:
            return obj.contact.user.username
        except:
            return " -- "

    raw_id_fields = ['contact']
    # def get_queryset(self, request):
    #     #test = super().get_queryset(request).select_related("application").prefetch_related(Prefetch("application__contactrole", queryset=ContactRole.objects.filter(role_type="AUTHOR").select_related("contact"), to_attr="authors"))
    #     return super().get_queryset(request).select_related("application").prefetch_related(Prefetch("application__contactrole", queryset=ContactRole.objects.filter(role_type="AUTHOR").select_related("contact"), to_attr="authors"))

    def get_email(self, obj):
        try:
            return obj.contact.email
        except:
            return " -- "
    get_email.short_description = "Email"

    def change_view(self, request, object_id, form_url='', extra_context=None):

        # add check here for webgroup
        extra_context = {}
        extra_context["extra_save_options"] = {
            "show_prometric":self.show_prometric,
        }

        return super().change_view(request, object_id, form_url,
            extra_context=extra_context)

    def add_view(self, request, form_url='', extra_context=None):

        # add check here for webgroup
        extra_context = {}
        extra_context["extra_save_options"] = {
            "show_prometric":self.show_prometric,
        }

        return super().add_view(request, form_url,
            extra_context=extra_context)

    def response_add(self, request, obj):
        return_action = self.publishable_button_actions(request, obj)
        return_super = super().response_change(request, obj)
        return return_action or return_super

    def response_change(self, request, obj):
        return_action = self.publishable_button_actions(request, obj)
        return_super = super().response_change(request, obj)
        return return_action or return_super

    def publishable_button_actions(self, request, obj):
        if "_sync_prometric" in request.POST:

            if obj.gee_eligibility_id:
                messages.error(request,'gee eligibility id already exists and already sent to Prometric. To resend: delete existing id and click send id again.')
            else:
                response = Prometric().submit_xelig(obj)
                if response == "1":
                    messages.success(request,'Successfully sent gee eligibility id %s to Prometric.' % (obj.gee_eligibility_id))
                else:
                    messages.error(request, 'There was a problem sending to Prometric. Check your email for details.')
# class ApplicationDegreeHistoryVerificationDocumentForm(forms.ModelForm):

#     def save(self, commit=True):
#         upload_type = UploadType.objects.filter(code="EXAM_APPLICATION_EDUCATION").first()
#         model_instance = super().save(commit=False)
#         model_instance.upload_type = upload_type

#         return super().save(commit=commit)


#     class Meta:
#         model = VerificationDocument
#         fields = ("uploaded_file",)


# class ApplicationDegreeHistoryVerificationDocumentInline(admin.StackedInline):
#     model = VerificationDocument
#     fields = ["uploaded_file",]
#     max_num = 1
#     extra = 0
#     classes=( "grp-collapse grp-closed",)
#     title = "Degrees"
#     form = ApplicationDegreeHistoryVerificationDocumentForm


# class ApplicationJobHistoryVerificationDocumentForm(forms.ModelForm):

#     def save(self, commit=True):
#         upload_type = UploadType.objects.filter(code="EXAM_APPLICATION_JOB").first()
#         model_instance = super().save(commit=False)
#         model_instance.upload_type = upload_type

#         return super().save(commit=commit)


#     class Meta:
#         model = VerificationDocument
#         fields = ("uploaded_file",)


# class ApplicationJobHistoryVerificationDocumentInline(admin.StackedInline):
#     model = VerificationDocument
#     fields = ["uploaded_file",]
#     max_num = 1
#     extra = 0
#     classes=( "grp-collapse grp-closed",)
#     title = "Jobs"
#     form = ApplicationJobHistoryVerificationDocumentForm


# #upload_type = UploadType.objects.filter(code="EXAM_APPLICATION_EDUCATION").first()

# class ApplicationJobHistoryAdmin(admin.ModelAdmin):
#     model = ApplicationJobHistory
#     fields = ["title","company",("city","state", "zip_code"),"country",("supervisor_name", "contact_employer"),("start_date","end_date","is_planning"),("is_current","is_part_time"),("verification_link")]
#     classes=( "grp-collapse grp-closed",)
#     title = "Jobs"
#     inlines = [ApplicationJobHistoryVerificationDocumentInline]

class ApplicationJobHistoryInlineForm(forms.ModelForm):

    uploaded_file = forms.FileField(required=False, label="Job Verification Document")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_uploaded_file()

    def save(self, commit=True):
        model_instance = super().save(commit=commit)
        if commit==True:
            self.save_verification_doc()
        return model_instance

    def save_verification_doc(self):
        uploaded_file = self.cleaned_data.get("uploaded_file")
        model_instance = self.instance
        if self.cleaned_data.get("uploaded_file", None):# == None:
            upload_type = UploadType.objects.filter(code="EXAM_APPLICATION_JOB").first()
            verif_docum = VerificationDocument.objects.filter(applicationjobhistory=model_instance).first()
            if not verif_docum:
                verif_docum = VerificationDocument(content=model_instance.application, upload_type=upload_type)
            verif_docum.uploaded_file = self.cleaned_data.get("uploaded_file", None)
            verif_docum.save()
            model_instance.verification_document = verif_docum
            model_instance.save()


    def init_uploaded_file(self):
        if self.instance and self.instance.verification_document:
            initial_uploaded_file = self.instance.verification_document.uploaded_file
        else:
            initial_uploaded_file = None
        self.fields["uploaded_file"].initial = initial_uploaded_file


    class Meta:
        model = ApplicationJobHistory
        fields = '__all__'


class ApplicationJobHistoryInline(admin.StackedInline):
    model = ApplicationJobHistory
    fields = ["uploaded_file","title","company",("city","state", "zip_code"),"country",("supervisor_name", "contact_employer"),("start_date","end_date","is_planning"),("is_current","is_part_time"),("verification_link"),]
    extra = 0
    classes=( "grp-collapse grp-closed",)
    title = "Jobs"
    readonly_fields=("verification_link",)
    form = ApplicationJobHistoryInlineForm

    def verification_link(self, obj):
        if obj.verification_document and obj.verification_document.uploaded_file:
            return  '<a href="%s">%s</a>' % (obj.verification_document.uploaded_file.url, obj.verification_document.uploaded_file.url)
        else:
            return None

    verification_link.allow_tags = True
    verification_link.short_description = 'Verification Document'

    # def job_link(self, obj):
    #     if obj:
    #         return '<a href="%s">%s</a>' % (reverse("admin:exam_applicationjobhistory_change", args=[obj.id]), "Go to Job Record")
    #     else:
    #         return None

    # job_link.allow_tags = True
    # job_link.short_description = 'Job Link'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "verification_document"
            )



class ApplicationDegreeInlineForm(forms.ModelForm):

    uploaded_file = forms.FileField(required=False, label="Education Verification Document")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_uploaded_file()

    def save(self, commit=True):
        model_instance = super().save(commit=commit)
        if commit==True:
            self.save_verification_doc()
        return model_instance

    def save_verification_doc(self):
        uploaded_file = self.cleaned_data.get("uploaded_file")
        model_instance = self.instance

        if self.cleaned_data.get("uploaded_file", None):
            upload_type = UploadType.objects.filter(code="EXAM_APPLICATION_EDUCATION").first()
            verif_docum = VerificationDocument.objects.filter(applicationdegree=model_instance).first()
            if not verif_docum:
                verif_docum = VerificationDocument(content=model_instance.application, upload_type=upload_type)
            verif_docum.uploaded_file = self.cleaned_data.get("uploaded_file", None)
            verif_docum.save()
            model_instance.verification_document = verif_docum
            model_instance.save()




    def init_uploaded_file(self):
        if self.instance and self.instance.verification_document:
            initial_uploaded_file = self.instance.verification_document.uploaded_file
        else:
            initial_uploaded_file = None
        self.fields["uploaded_file"].initial = initial_uploaded_file

    class Meta:
        model = ApplicationDegree
        fields = '__all__'


class ApplicationDegreeInline(admin.StackedInline):
    model = ApplicationDegree
    fields = ["uploaded_file","school","other_school",("level","graduation_date"),("is_planning","pab_accredited"),("verification_link"),]
    extra = 0
    classes=( "grp-collapse grp-closed",)
    title = "Education"
    readonly_fields=("verification_link",)
    form = ApplicationDegreeInlineForm


    def verification_link(self, obj):
        if obj.verification_document and obj.verification_document.uploaded_file:
            return  '<a href="%s">%s</a>' % (obj.verification_document.uploaded_file.url, obj.verification_document.uploaded_file.url)
        else:
            return None

    verification_link.allow_tags = True
    verification_link.short_description = 'Verification Document'

    # def degree_link(self, obj):
    #     if obj:
    #         return '<a href="%s">%s</a>' % (reverse("admin:exam_applicationdegreehistory_change", args=[obj.id]), "Go to Degree Record")
    #     else:
    #         return None

    # degree_link.allow_tags = True
    # degree_link.short_description = 'Degree Link'
    def formfield_for_foreignkey(self, db_field, *args, **kwargs):
        field = super().formfield_for_foreignkey(db_field, *args, **kwargs)
        if db_field.name == 'school':
            field.queryset = field.queryset.select_related("user")
            field.required = False
        return field

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "verification_document"
            )

# class ApplicationDegreeAdmin(admin.ModelAdmin):
#     model = ApplicationDegree
#     fields = ["school","other_school",("level","graduation_date"),("is_planning","pab_accredited"),("verification_link")]
#     classes=( "grp-collapse grp-closed",)
#     title = "Education"
#     inlines = [ApplicationDegreeHistoryVerificationDocumentInline]


class ExamApplicationAnswerReviewAdminForm(ExamAnswerReviewForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = AnswerReview
        exclude = []


class ExamApplicationAnswerReviewInline(admin.StackedInline):
    model = AnswerReview
    form = ExamApplicationAnswerReviewAdminForm
    # fields = ["answer_text", "rating", "comments", "answered_successfully"]
    extra = 0
    classes=( "grp-collapse grp-closed",)
    title = "Criteria reviews"
    readonly_fields=("answer_text",)

    def answer_text(self, obj):
        return "<h3>%s</h3><p>%s</p>" % (obj.answer.question.title, obj.answer.text)
    answer_text.allow_tags = True
    answer_text.short_description = 'Application Question and Answer'


class ExamApplicationReviewAdminForm(ExamApplicationReviewForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "content" in self.fields:
            self.fields["content"].queryset = ExamApplication.objects.filter(publish_status="DRAFT")
        # self.fields["contact"].label = "Reviewer"
    class Meta:
        model = ExamApplicationReview
        exclude = []

class ExamApplicationReviewAdmin(admin.ModelAdmin):
    model = ExamApplicationReview
    raw_id_fields=['role', 'contact']
    list_display = ['get_applicant', 'get_reviewer', 'get_reviewer_recommendation', 'review_round']
    form = ExamApplicationReviewAdminForm
    inlines = (ExamApplicationAnswerReviewInline, )
    # this hangs the admin:
    # list_filter =  ["contact","content"]
    fieldsets = [
        (None, {
            "fields": ( ("get_application"), ("get_applicant"),
                        ("contact","role"),
                        ("review_round", "assigned_time", "review_time"),
                        ("deadline_time",),
                        ("rating_1",),
                        ("rating_2", "rating_3"),
                        ("comments",),
                        ("custom_text_1",),
                        ("custom_text_2",),
                        ("custom_boolean_1",),
            ),
        }),
    ]
    readonly_fields = ("contact", "assigned_time", "review_time", "get_applicant", "get_application", "get_reviewer_recommendation", "get_reviewer")

    def get_applicant(self, obj):
        return  'Applicant: %s | %s' % (obj.content.examapplication.contact, obj.content.examapplication.contact.user.username)
    get_applicant.short_description = "Applicant"

    def get_application(self, obj):
        return  'Application: %s | %s' % (obj.content.examapplication.submission_category, obj.content.examapplication.application_status)
    get_application.short_description = "Application"

    def get_reviewer_recommendation(self, obj):
        return "Approve" if obj.rating_2 == 1 else "Deny"
    get_reviewer_recommendation.short_description = "Reccomendation"

    def get_reviewer(self, obj):
        return "Reviewer: %s | %s" % (obj.role.contact, obj.role.title)
    get_reviewer.short_description = "Reviewer"


class ExamApplicationReviewInline(admin.StackedInline):
    model = ExamApplicationReview

    fieldsets = [
        (None, {
            "fields": ( ("get_application"), ("get_applicant"),
                        ("contact","role"),
                        ("review_round", "assigned_time", "review_time"),
                        ("deadline_time",),
                        ("rating_1",),
                        ("rating_2", "rating_3"),
                        ("comments",),
                        ("custom_text_1",),
                        ("custom_text_2",),
                        ("custom_boolean_1",),
                        ("review_details_link",),
            ),
        }),
    ]
    # raw_id_fields=["role", "contact"]
    # autocomplete_lookup_fields = {'fk': ["role", "contact"]}
    readonly_fields = ("contact", "assigned_time", "review_time", "review_details_link", "get_applicant", "get_application")
    extra = 0
    classes=( "grp-collapse grp-closed",)
    title = "Review Assignments"
    form = ExamApplicationReviewAdminForm

    def review_details_link(self, obj):
        return  '<a href="%s">VIEW/EDIT DETAILS</a>' % obj.get_admin_url()
    review_details_link.allow_tags = True
    review_details_link.short_description = 'See/edit full review, including comments for each criteria'


    def formfield_for_foreignkey(self, db_field, *args, **kwargs):
        field = super().formfield_for_foreignkey(db_field, *args, **kwargs)
        if db_field.name == 'role':
            field.queryset = field.queryset.filter(review_type="EXAM_REVIEW").select_related("contact__user")
            field.required = True
        return field

    def get_applicant(self, obj):
        return  'Applicant: %s | %s' % (obj.content.examapplication.contact, obj.content.examapplication.contact.user.username)
    get_applicant.short_description = "Applicant"

    def get_application(self, obj):
        return  'Application: %s | %s' % (obj.content.examapplication.submission_category, obj.content.examapplication.application_status)
    get_application.short_description = "Application"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "contact", "content__examapplication__contact__user", "content__examapplication__exam",
            "content__examapplication__submission_category"
            )


class ExamApplicationPublishStatusFilter(admin.SimpleListFilter):

    title = 'Copy of application (publish status)'
    parameter_name = 'publish_status'

    def lookups(self, request, model_admin):
        lookup_list = (
                ("DRAFT", "Submitted Applications - staff editable (DRAFT copy)"),
                ("SUBMISSION", "Original application submissions / in-progress applications (SUBMISSION)"),
                ("EARLY_RESUBMISSION", "Re-submitted copy of an early-bird application (EARLY_RESUBMISSION)"),
                ("_ALL", "All Copies"),
            )
        return lookup_list

    def queryset(self, request, queryset):
        lookup_value = self.value()
        if lookup_value is None: # default to DRAFT
            return queryset.filter(publish_status="DRAFT")
        elif lookup_value == "_ALL":
            return queryset
        else:
            return queryset.filter(publish_status=lookup_value)

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }


class ExamApplicationExamFilter(admin.SimpleListFilter):

    title = 'Exam'
    parameter_name = 'exam'
    exams = None

    def lookups(self, request, model_admin):
        self.exams = self.exams or build_exams_list()
        lookup_list = sorted(self.exams, reverse=True)
        # index_of_default = [y[0] for y in lookup_list].index(CURRENT_EXAM[0])
        # index_of_default = [y[0] for y in lookup_list].index("_ALL")
        # lookup_list[index_of_default] = (None, CURRENT_EXAM[1])
        return lookup_list

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        lookup_value = self.value()
        if lookup_value is None: # default to most recent exam
            # return queryset.filter(parent__content_live__code=CURRENT_EXAM[0])
            # return queryset.filter(exam__code=CURRENT_EXAM[0])
            return queryset
        elif lookup_value == "_ALL":
            return queryset
        else:
            # return queryset.filter(parent__content_live__code=self.value())
            return queryset.filter(exam__code=self.value())


class ExamApplicationAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["editorial_comments"].label = "Comments to reviewers"
        self.fields["editorial_comments"].help_text = "Enter comments for reviewers to see on the review form."

    class Meta:
        model = ExamApplication
        exclude = []
        widgets = {
            "editorial_comments":forms.Textarea()
        }

class ExamApplicationAnswerInline(admin.StackedInline):
    model = Answer
    extra = 0
    # clean this up...
    fields = ("question", "text")
    ordering = ("question__sort_number",)
    def formfield_for_foreignkey(self, db_field, *args, **kwargs):
        field = super().formfield_for_foreignkey(db_field, *args, **kwargs)
        if db_field.name == "question":
            field.queryset = field.queryset.filter(categories__content_type="EXAM").distinct("id")
        return field

class ExamApplicationAdmin(admin.ModelAdmin):
    list_display=[
        "get_author_id","get_author","application_type", "application_status","submission_time",
        "publish_status","exam", "current_review_round", "get_overall_recommendation", "get_email"
        ]
    list_filter =  [ExamApplicationPublishStatusFilter,"application_status","application_type",ExamApplicationExamFilter]
    list_display_links = ["get_author", "get_author_id"]
    search_fields = ["=contact__user__username", "=contact__first_name", "=contact__last_name"]
    form = ExamApplicationAdminForm
    fieldsets = [

        (None, {
            "fields":(  ("contact","publish_status"),
                        ("exam", "get_previous_denial"),
                        ("submission_category", "current_review_round"),
                        ("application_type", "application_status"),
                        ("submission_time","submission_approved_time"),
                        ("editorial_comments"),
                        ("get_overall_recommendation"),
                        ("get_total_experience"),
            ),
        }),
    ]

    # change_form_template = "admin/exam/examapplication/change-form.html"

    # for reviewers?
    #inlines = [ProposalAnswerInline, ApplicationJobHistoryInlineAdmin, ApplicationDegreeAdmin]
    inlines = [ApplicationJobHistoryInline, ApplicationDegreeInline, ExamApplicationAnswerInline, ExamApplicationReviewInline] #
    raw_id_fields=['contact']
    readonly_fields=["get_author_id","get_author", "publish_status",
        "get_previous_denial", "get_email", "get_overall_recommendation", "get_total_experience"]

    def get_email(self, obj):
        try:
            return obj.contact.email
        except:
            return " -- "
    get_email.short_description = "Email"

    def get_author(self, obj):
        try:
            return obj.contact
        except:
            return None
    get_author.short_description = "Name"

    def get_previous_denial(self, obj):
        return obj.previous_denial_application()

    def get_author_id(self, obj):
        try:
            return obj.contact.user.username
        except:
            return None

    get_author_id.short_description = "User ID"

    def get_overall_recommendation(self, obj):
        reviews = obj.review_assignments.all().order_by("review_round")
        recs = [APPROVAL_CHOICES[r.rating_2 if r.rating_2 else 0][1] for r in reviews]
        all_recs = ""
        for i,rec in enumerate(recs):
            round_rec = "Round %s: %s\n" % (i+1, rec)
            all_recs+=round_rec
        return all_recs

    get_overall_recommendation.short_description = "Overall Recommendations"

    def get_total_experience(self, obj):
        try:
            js=obj.applicationjobhistory_set.all()
            exp = datetime.timedelta(days=0)

            for j in js:
                exp = exp + j.get_planning_experience()

            return "%s years" % (round((exp.days / 365.0),2))
        except:
            return None
    get_total_experience.short_description = "Total Job Experience"

    def get_actions(self, request):
        """
        Built-in django hook that gets the actions for the admin mass action dropdown in lower left...
        for content, we are disabling the mass "delete" action.
        Also, see PublishableAdminMixin for super() actions related to publishing...
        """
        actions = super().get_actions(request)
        # TO DO... add multiple mass assignments
        reviewroles = ExamApplicationRole.objects.filter(status="A")
        for i in range(1,7):
            for e in reviewroles:
                actions["mass_assign_%s_%s" % (e.id, i) ] = self.get_mass_assign_method(e, i)

        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def get_mass_assign_method(self, reviewrole, round):
        """
        Admin action to mass publish content to the staging server and staging solr search.
        """
        def mass_to_person(modeladmin, request, queryset):
            # try:
            # assigned_time = datetime.datetime.now(pytz.timezone("Etc/UTC"))
            assigned_time = timezone.now()
            for x in queryset:
                x.current_review_round = round
                x.save()
                if round not in [rev.review_round for rev in x.review_assignments.all()]:
                    exam_app_review, created = ExamApplicationReview.objects.get_or_create(
                                content=x,
                                role=reviewrole,
                                contact=reviewrole.contact,
                                review_round=round,
                                review_type='EXAM_REVIEW')
                    if exam_app_review:
                        exam_app_review.assigned_time = assigned_time
                        exam_app_review.save()
                else:
                    messages.error(request,"Error assgning %s: cannot duplicate review round" % x)
            # except:
            #     messages.error(request,"Error assgning")

        return (mass_to_person, "mass_assign_%s_%s" % (reviewrole.id, round), "ROUND %s ASSIGN: %s" % (round, reviewrole) )


    def save_formset(self, request, form, formset, change):
        # TO DO... we do this exact same thing on other inlines for Review proxy models... maybe make an admin mixin so as not to repeat the code

        # Seemingly the only way to have on-save events for the review inline,
        # Could also use a method on the ModelForm class, but this has the benefit of also detecting changes on the inquiry form
        if formset.model == ExamApplicationReview:
            # review_status doesn't exist on a Review record:
            # review_status = form.cleaned_data.get("review_status")
            # review_status_changed = "review_status" in form.changed_data
            # datetime_now = datetime.datetime.now(pytz.timezone("Etc/UTC"))
            datetime_now = timezone.now()

            reviews = formset.save(commit=False)
            for review in reviews:
                review.assigned_time = review.assigned_time or datetime_now
                review.contact = review.role.contact
            # review_status doesn't exist on a Review record:
                # if review_status_changed and review_status == "COMPLETED":
                #     review.review_time = datetime_now
                review.save()
            formset.save_m2m()
            # as of django 1.7, deletions need to be handled manually when you use formset.save(commit=False)
            for obj in formset.deleted_objects:
                obj.delete()

        elif formset.model == ApplicationJobHistory or formset.model == ApplicationDegree:
            contact = form.cleaned_data.get("contact")
            instances = formset.save(commit=False)


            for instance in instances:
                instance.contact = contact
                instance.save()

            for form in formset:
                form.save_verification_doc()

            # formset.save()
            # only if commit=False:
            formset.save_m2m()

            # as of django 1.7, deletions need to be handled manually when you use formset.save(commit=False)
            for obj in formset.deleted_objects:
                obj.delete()
        else:
            super().save_formset(request, form, formset, change)


    def get_queryset(self, request):
        exclude_types = CAND_ENROLL_APP_TYPES
        return self.model.objects.filter(content_type="EXAM").select_related(
            "submission_category").select_related("exam").select_related(
            "contact").select_related("contact__user").exclude(
            application_type__in=exclude_types)


    # def submission_time_central(self, obj):
    #     fmt = '%Y-%m-%d %H:%M:%S %Z%z'
    #     if obj.submission_time:
    #         dt = obj.submission_time.astimezone(central)
    #         return  dt.strftime(fmt)
    #     else:
    #         return None
    # submission_time_central.short_description = "Submitted On (U.S. Central Time)"


    def save_model(self, request, obj, form, change):
        """
        If staff changes application_status of exam application, an appropriate email is generated.
        """
        mail_context = {
            'application':obj,
        }

        app_status = obj.application_status
        app_type = obj.application_type

        if "application_status" in form.changed_data and app_status not in APP_STATUS_IGNORE_LIST:
            # if app_type in CAND_ENROLL_APP_TYPES:
            #     email_template_code = CAND_ENROLL_EMAIL_TEMPLATES[app_status]
            if app_type in CAND_CERT_APP_TYPES:
                email_template_code = CAND_CERT_EMAIL_TEMPLATES[app_status]
            else:
                email_template_code = EXAM_APP_EMAIL_TEMPLATES[app_status]
            try:
                email_template = EmailTemplate.objects.get(code=email_template_code)
            except Exception as e:
                email_template = None
                print("No Email Template Error: " + str(e))

            if email_template and email_template.status == 'A':
                mail_to = obj.contact.email
                Mail.send(email_template_code, mail_to, mail_context)
        return super().save_model(request, obj, form, change)

    # response_add and response_change are the only methods called after the form and all formsets have been saved,
    def response_add(self, request, obj):
        max_review_round = 0
        reviews = obj.review_assignments.all()
        if reviews:
            for r in reviews:
                max_review_round = max(max_review_round, r.review_round)
        obj.current_review_round = max_review_round if max_review_round > 0 else None
        obj.save()

        return_super = super().response_change(request, obj)
        return return_super

    def response_change(self, request, obj):
        max_review_round = 0
        reviews = obj.review_assignments.all()
        if reviews:
            for r in reviews:
                max_review_round = max(max_review_round, r.review_round)
        obj.current_review_round = max_review_round if max_review_round > 0 else None
        obj.save()

        return_super = super().response_change(request, obj)
        return return_super


class ApplicationCategoryAdmin(CategoryAdmin):
    pass


class ExamRegistrationOrderAdmin(OrderAdmin):
    model = ExamRegistrationOrder
    list_display = OrderAdmin.list_display
    list_filter = ("expected_payment_method",)


class ExamApplicationOrderAdmin(OrderAdmin):
    model = ExamApplicationOrder
    list_display = OrderAdmin.list_display
    list_filter = ("expected_payment_method",)


class ExamApplicationRoleAdmin(admin.ModelAdmin):
    model = ExamApplicationRole
    list_display = ["contact", "title"]

    fields = ["contact", "title"]
    raw_id_fields=["contact"]
    autocomplete_lookup_fields = {'fk': ["contact"]}

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("contact").select_related("contact__user")


class CandidateApplicationDegreeInline(ApplicationDegreeInline):
    fields = ["uploaded_file","school",("level","graduation_date"),("verification_link"),]

class AICPCandidateApplicationAdmin(admin.ModelAdmin):
    model = AICPCandidateApplication
    list_filter = ["application_status","application_type"]
    # list_filter =  [ExamApplicationPublishStatusFilter,"application_status","application_type",ExamApplicationExamFilter]

    list_display=[
        "get_author_id","get_author","application_type", "application_status","submission_time",
        "exam", "publish_status", "get_registration_status", "five_year_deadline", "get_graduation_status"
        ]
    list_display_links = ["get_author", "get_author_id"]
    search_fields = ["=contact__user__username", "=contact__first_name", "=contact__last_name"]
    # form = ExamApplicationAdminForm
    fieldsets = [
        (None, {
            "fields":(  ("contact","publish_status"),
                        ("exam"),
                        ("submission_category"),
                        ("application_type", "application_status"),
                        ("submission_time","submission_approved_time", "created_time"),
                        # ("editorial_comments"),
            ),
        }),
    ]

    inlines = [CandidateApplicationDegreeInline]
    raw_id_fields=['contact']
    readonly_fields=["get_author_id","get_author", "publish_status", "created_time"]

    def get_author(self, obj):
        try:
            return obj.contact
        except:
            return None
    get_author.short_description = "Name"

    def get_author_id(self, obj):
        try:
            return obj.contact.user.username
        except:
            return None
    get_author_id.short_description = "User ID"

    def get_registration_status(self, obj):
        try:
            now = timezone.now()
            current_exam = Exam.objects.filter(registration_end_time__gte=now).order_by("registration_end_time").first()
            registered = ExamRegistration.objects.filter(contact=obj.contact, exam=current_exam).exists()
            if registered:
                return "Yes"
            else:
                return "No"
        except:
            return None
    get_registration_status.short_description = "Registered?"

    def five_year_deadline(self, obj):
        try:
            contact=obj.contact
            cand_period = Period.objects.get(code="CAND")
            cand_log = Log.objects.filter(contact=contact, period=cand_period, status='A', is_current = True)

            if cand_log and cand_log.count() == 1:
                return cand_log.first().end_time
            else:
                return None
        except:
            return None
    five_year_deadline.short_description = "Deadline"

    def get_graduation_status(self, obj):
        try:
            d=obj.applicationdegree_set.first()
            if d and d.graduation_date:
                return "Yes"
            else:
                return "No"
        except:
            return None
    get_graduation_status.short_description = "Graduated?"

    def save_formset(self, request, form, formset, change):
        if formset.model == ApplicationDegree:
            contact = form.cleaned_data.get("contact")
            instances = formset.save(commit=False)

            for instance in instances:
                instance.contact = contact
                instance.save()

            for form in formset:
                form.save_verification_doc()

            # only if commit=False:
            formset.save_m2m()

            # as of django 1.7, deletions need to be handled manually when you use formset.save(commit=False)
            for obj in formset.deleted_objects:
                obj.delete()
        else:
            super().save_formset(request, form, formset, change)

    def get_queryset(self, request):
        qs = super(AICPCandidateApplicationAdmin, self).get_queryset(request)
        return qs.filter(application_type='CAND_ENR')

    def save_model(self, request, obj, form, change):
        now=timezone.now()
        contact = obj.contact

        if 'application_status' in form.changed_data and obj.application_status in ['D']:
            period = Period.objects.get(code="CAND")
            log = Log.objects.filter(contact=contact, period=period)
            if log.count() == 1:
                log = log.first()
                if log:
                    log.status = 'I'
                    log.is_current = False
                    log.end_time = now
                    log.save()
                    messages.info(request, "Shutting down AICP Candidate Log for this denied applicant.")
            elif log.count() > 1:
                messages.error(request, "ERROR: More than one AICP Candidate Log detected.")
            else:
                messages.error(request, "ERROR: No AICP Candidate Log detected for this enrollee.")

        elif 'application_status' in form.changed_data \
            and obj.application_status in ENROLLED_STATUSES + ['I']:
            if obj.application_status == 'A' or obj.application_status == 'I':
                if obj.application_status == 'A':
                    if not obj.submission_approved_time:
                        obj.submission_approved_time = now

                mail_context = dict(
                    contact=contact,
                )
                email_template_code = CAND_ENROLL_EMAIL_TEMPLATES.get(obj.application_status)
                mail_to = obj.contact.email
                Mail.send(email_template_code, mail_to, mail_context)

            period = Period.objects.get(code="CAND")
            log = Log.objects.filter(contact=contact, period=period)
            if log.count() == 1:
                log = log.first()
                if log.status != 'A':
                    log.status = 'A'
                    log.is_current = True
                    # now=timezone.now()
                    five_years = datetime.timedelta(days=365*5)
                    # log.begin_time = now
                    log.end_time = log.begin_time + five_years
                    log.save()
                    messages.info(request, "Updating status of AICP Candidate Log to 'A' 'Active'.\nThe five-year window is open.")
            elif log.count() > 1:
                messages.error(request, "ERROR: More than one active AICP Candidate Log detected.")
            else:
                messages.error(request, "ERROR: No active AICP Candidate Log detected for this enrollee.")

        super(AICPCandidateApplicationAdmin, self).save_model(request, obj, form, change)


class AICPCredentialDataAdmin(admin.ModelAdmin):
    model = AICPCredentialData


admin.site.register(Exam,ExamAdmin)
admin.site.register(ExamRegistration, ExamRegistrationAdmin)
admin.site.register(ExamApplication, ExamApplicationAdmin)

admin.site.register(ApplicationCategory, ApplicationCategoryAdmin)

admin.site.register(ExamRegistrationOrder, ExamRegistrationOrderAdmin)
admin.site.register(ExamApplicationOrder, ExamApplicationOrderAdmin)
admin.site.register(ExamApplicationReview, ExamApplicationReviewAdmin)
admin.site.register(ExamApplicationRole, ExamApplicationRoleAdmin)
admin.site.register(AICPCandidateApplication, AICPCandidateApplicationAdmin)
admin.site.register(AICPCredentialData, AICPCredentialDataAdmin)



