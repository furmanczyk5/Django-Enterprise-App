import datetime

import pytz
from django import forms
from django.contrib import messages

from content.forms import StateCountryModelFormMixin, AddFormControlClassMixin
from content.widgets import YearMonthDaySelectorWidget, SelectFacade
from imis.db_accessor import DbAccessor
from imis.models import CustomSchoolaccredited
from myapa.models.constants import CHAPTER_CHOICES
from myapa.models.contact import Contact
from myapa.models.proxies import School
from submissions.forms import SubmissionBaseForm
from submissions.models import AnswerReview, REVIEW_ROUNDS
from ui.utils import get_selectable_options_tuple_list
from .models import ADVANCED_APPLICATION_TYPES, Exam, ExamApplication, \
    ExamRegistration, VerificationDocument, ApplicationJobHistory, \
    ApplicationDegree, ExamApplicationReview, \
    make_regular_application_types_list, make_advanced_application_types_list

RATING_CHOICES_NUMS = (('',"Select Overall Rating"),(1,1),(2,2),(3,3),(4,4),(5,5))
DENIAL_LETTER_OPTION_CHOICES = ((0,"Select Denial Letter Option"),(1,1),(2,2),(3,3),(4,4))
ANSWER_REVIEW_CHOICES = (('',"Select Criteria Recommendation"),(1,"Meets Requirements"),(2,"Does Not Meet Requirements"))
APPROVAL_CHOICES = ((0,"Select Recommendation"),(1,"Approval"),(2,"Denial"))
APP_TYPES_NO_SCHOLAR = (
    ("REG","Regular Applicant"),
    ("MCIP","Canadian Institute of Planners (MCIP)"),
    ("NJ","NJ: applying for AICP only, already passed exam"),
    ("NJ_REG","NJ: applying for AICP and will register for the exam"),
    ("NJ_NOAICP", "NJ: Not Applying for AICP – Exam Only"),
    )
CAND_CERT_APP_TYPE = (
    ("CAND_CERT","AICP Candidate AICP Certification"), # $375
    # ("CAND_RESUB","AICP Candidate AICP Certification Resubmission"), # $0
    )
CAND_RESUB_APP_TYPE = (
    # ("CAND_CERT","AICP Candidate AICP Certification"), # $375
    ("CAND_RESUB","AICP Candidate AICP Certification Resubmission"), # $0
    )
# a Temporary fix to link Django Application Degrees to an accredited program in imis
# (This was somehow lost in code changes related to getting rid of node?)
DUMMY_SCHOOL_SEQN = 45


class ExamAnswerReviewForm(forms.ModelForm):
    """
    for the ExamApplicationReview model -- used in the review/approval process.
    """
    def __init__(self, *args, **kwargs):
        self.base_fields['rating'] = forms.ChoiceField(
            choices=ANSWER_REVIEW_CHOICES,
            required=True,
            label="Criterion Recommendation"
        )
        self.base_fields['comments'] = forms.CharField(
            widget=forms.Textarea(attrs={"class": "full-width"}),
            required=True
        )
        self.base_fields['answered_successfully'] = forms.BooleanField(required=False)

        super().__init__(*args, **kwargs)
        self.fields['review'].widget=forms.HiddenInput()
        self.fields['answer'].widget=forms.HiddenInput()

    class Meta:
        model = AnswerReview
        fields = ['rating','comments','answered_successfully','review','answer']


class ExamApplicationReviewForm(forms.ModelForm):
    """
    for the ExamApplicationReview model -- used in the review/approval process.
    """
    def __init__(self, *args, **kwargs):

        self.base_fields['rating_1'] = forms.TypedChoiceField(coerce=lambda r: int(r) if r else None, choices=RATING_CHOICES_NUMS, required=True, label="Overall Rating")
        self.base_fields['rating_2'] = forms.ChoiceField(choices=APPROVAL_CHOICES, required=False, label="Approval/Denial Recommendation")
        self.base_fields['rating_3'] = forms.TypedChoiceField(coerce=lambda r: int(r) if r else None,
            choices=DENIAL_LETTER_OPTION_CHOICES, required=False, label="Denial Letter Option (if applicable)", initial=1)
        self.base_fields['review_round'] = forms.ChoiceField(choices=REVIEW_ROUNDS, required=False)

        super().__init__(*args, **kwargs)

        self.fields['comments'] = forms.CharField(
            widget=forms.Textarea(attrs={"class": "full-width"}),
            required=True,
            label="Overall Comments"
        )
        self.fields['custom_text_1'] = forms.CharField(
            widget=forms.Textarea(attrs={"class": "full-width"}),
            required=False,
            label="Draft Denial Statement (if applicable)"
        )
        self.fields['custom_text_2'] = forms.CharField(
            widget=forms.Textarea(attrs={"class": "full-width"}),
            required=False,
            label="Denial Statement Comments (if applicable)"
        )
        self.fields['custom_boolean_1'] = forms.BooleanField(
            required=False,
            label="I agree with the current denial statement and no edits are needed."
        )
        self.fields['custom_boolean_1'].initial = self.instance.custom_boolean_1
        self.fields['rating_2'].required = True

    class Meta:
        model = ExamApplicationReview
        fields = ['comments','rating_1','rating_2', 'rating_3', 'custom_text_1', 'custom_text_2', 'custom_boolean_1', 'review_round']


# # OLD FORM.. TO DO: will remove
# class ExamApplicationReviewerEditForm(forms.ModelForm):
#     def __init__(self, *args, **kwargs):
#         # self.base_fields['rating_1'] = forms.ChoiceField(choices = RATING_CHOICES)
#         # self.base_fields['rating_2'] = forms.ChoiceField(choices = RATING_CHOICES)
#         # self.base_fields['rating_3'] = forms.ChoiceField(choices = RATING_CHOICES)
#         # self.base_fields['rating_4'] = forms.ChoiceField(choices = RATING_CHOICES)

#         super().__init__(*args, **kwargs)
#         # self.fields['contact'].widget=forms.HiddenInput()
#         # self.fields['content'].widget=forms.HiddenInput()
#         # self.fields['role'].widget=forms.HiddenInput()
#         # self.fields['comments']=forms.CharField(widget=forms.Textarea(attrs={"class":"full-width"}))

#     class Meta:
#         model = AnswerReview
#         fields = ['review','answer','rating','comments','answered_successfully',]


class ExamApplicationMCIPSubmitForm(forms.ModelForm):

    uploaded_file = forms.FileField(required=False)
    code_of_ethics = forms.BooleanField(required=True)

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.fields['verification_document'].required = False
        self.fields['verification_document'].widget = forms.HiddenInput()
        self.fields['application'].required = False
        self.fields['code_of_ethics'].initial = False
        self.fields['code_of_ethics'].label = "I have read the AICP Code of Ethics and Professional Conduct and understand that I am subject to its provisions as of the date of submittal of this application."

        self.init_uploaded_file()

    def init_uploaded_file(self):
        if self.instance and self.instance.verification_document:
            initial_uploaded_file = self.instance.verification_document.uploaded_file
        else:
            initial_uploaded_file = None
        self.fields["uploaded_file"].initial = initial_uploaded_file

    def clean(self):

        cleaned_data = super().clean()

        the_file = cleaned_data.get("uploaded_file", None)
        if  the_file == None:
            self.add_error("uploaded_file", "You must provide a verification document for your MCIP membership.")

        ethics_response = cleaned_data.get("code_of_ethics", None)
        if  ethics_response == False:
            self.add_error("code_of_ethics", "You must certify that you agree to the AICP Code of Ethics to proceed.")

        return cleaned_data

    class Meta:
        model = ApplicationDegree
        fields = [ "verification_document", "application", "code_of_ethics",
            ]
        labels = {
        }


class ExamApplicationCodeOfEthicsForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['code_of_ethics'].required = True

    class Meta:
        model = ExamApplication
        fields = ["code_of_ethics"]
        labels = {
            "code_of_ethics": "I have read the AICP Code of Ethics and Professional Conduct and understand that I am subject to its provisions as of the date of submittal of this application."
        }


class ExamApplicationTypeForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        asc_window_open = kwargs.pop("asc_window_open")
        cand_access = kwargs.pop("cand_access")
        cand_no_access = kwargs.pop("cand_no_access")
        is_aicpmember = kwargs.pop("is_aicpmember")
        has_paid_cert_app = kwargs.pop("has_paid_cert_app")

        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
        self.type_code = kwargs.pop("type", None)
        advanced_types = make_advanced_application_types_list()
        regular_types = make_regular_application_types_list()

        if not cand_access:
            if (self.type_code in regular_types or not is_aicpmember):
                self.fields['application_type'] = forms.ChoiceField(choices=regular_types)
            elif (self.type_code in ADVANCED_APPLICATION_TYPES or is_aicpmember) and asc_window_open:
                self.fields['application_type'] = forms.ChoiceField(choices=advanced_types)
            else:
                self.fields['application_type'] = forms.ChoiceField(choices=APP_TYPES_NO_SCHOLAR)
        else:
            # if no paid cand cert app within window
            if not has_paid_cert_app:
                self.fields['application_type'] = forms.ChoiceField(choices=CAND_CERT_APP_TYPE)
            else:
                self.fields['application_type'] = forms.ChoiceField(choices=CAND_RESUB_APP_TYPE)

        # MUST IMPLEMENT THE DISPLAY OF CAND RESUB APP TYPE OPTION WHEN APPROPRIATE --
        # LOGIC WILL BE IF THEY HAVE A PAID CAND_CERT APP
        # OR should this be assigned on the back end in the view only (not a user choice)?

    class Meta:
        model = ExamApplication
        fields = ["application_type"]


class ExamSummaryForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.application = kwargs.get("instance", None)

    class Meta:
        model = ExamApplication
        fields = ["legacy_id"]


class ExamCriteriaForm(SubmissionBaseForm):
    tag_type_choices = [{"code":"EXAM_PLANNING_PROCESS", "required":False}]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

    class Meta:
        model = ExamApplication
        fields = [  ]


class ASCExamCriteriaForm(SubmissionBaseForm):
    # tag_type_choices = [{"code":"EXAM_PLANNING_PROCESS", "required":False}]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

    class Meta:
        model = ExamApplication
        fields = [  ]


class VerificationDocumentForm(forms.ModelForm):

    class Meta:
        model = VerificationDocument
        fields = ("upload_type", "uploaded_file")


class ExamDegreeHistoryForm(forms.ModelForm):

    uploaded_file = forms.FileField(required=False)
    schools_queryset = None

    def get_schools_queryset(self):
        """
        throwing this logic in a method (to get a queryset of PAB scools) ... so variables can be declared locally
        """

        try:
            query = """
                        SELECT N.ID FROM Name N
                        INNER JOIN Custom_SchoolAccredited SA on SA.ID = N.ID
                        WHERE MEMBER_TYPE = ?
                        """
            school_ids = DbAccessor().get_rows(query, "SCH")
            school_ids_list = [school_id[0] for school_id in school_ids]
            return School.objects.select_related('user').filter(user__username__in=school_ids_list)
        except:
            # just in case there's an error connecting to iMIS, we don't want everything to crash ...!
            return School.objects.none()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['graduation_date'].required = True
        self.fields['level'].required = True
        self.fields['verification_document'].required = False
        self.fields['verification_document'].widget = forms.HiddenInput()
        self.fields['application'].required = False
        self.fields['school_seqn'].required = False

        # gets a list of the valid accredited schools from iMIS
        self.fields["school"].queryset = self.get_schools_queryset()
        self.init_uploaded_file()

    def init_uploaded_file(self):
        if self.instance and self.instance.verification_document:
            initial_uploaded_file = self.instance.verification_document.uploaded_file
        else:
            initial_uploaded_file = None
        self.fields["uploaded_file"] = forms.FileField(required=False, initial=initial_uploaded_file)

    def clean(self):

        cleaned_data = super().clean()

        the_file = cleaned_data.get("uploaded_file", None)
        if  the_file == None:
            self.add_error("uploaded_file", "You must provide a verification document for this degree.")

        the_school = cleaned_data.get("school", None)
        the_other_school = cleaned_data.get("other_school", None)
        if (not the_school) and (not the_other_school):
            self.add_error("school", "You must enter an educational institution in either the 'school' or the 'other school' field.")

        if the_school:
            school_id = the_school.user.username
            degree_date = cleaned_data.get("graduation_date")
            degree_level = cleaned_data.get("level")
            is_planning = cleaned_data.get("is_planning", False)
            if is_planning and degree_date:
                dt = datetime.datetime.combine(degree_date, datetime.datetime.min.time())
                ddo_utc = pytz.utc.localize(dt)
                csa=CustomSchoolaccredited.objects.filter(
                    id=school_id,
                    degree_level=degree_level,
                    start_date__lte=ddo_utc,
                    end_date__gte=ddo_utc
                )
                if csa:
                    cleaned_data["school_seqn"] = DUMMY_SCHOOL_SEQN
                    cleaned_data["pab_accredited"] = True

        return cleaned_data

    class Meta:
        model = ApplicationDegree
        fields = [ "verification_document", "uploaded_file", "school", "other_school", "graduation_date", "level",
            "is_planning", "application", "pab_accredited", "school_seqn"
            ]
        labels = {
            "school": "Accredited College or University",
            "is_planning": "Is this a planning degree? (check box)",
            "other_school": "College or University (if not on the list above)",
            "graduation_date": "Date of Graduation (mm/dd/yyyy)",
            "level": "Educational Level",
        }


class ExamJobHistoryForm(StateCountryModelFormMixin, forms.ModelForm):

    uploaded_file = forms.FileField(required=False)#, help_text="(pdf format only)")

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['company'].required = True
        self.fields['start_date'].required = True

        self.init_uploaded_file()

        self.fields['is_current'].initial = False
        self.fields['end_date'].help_text = 'If job is current, leave end date blank and check "is current" box. \
                                            Job experience will be calculated based on application date.'

    def init_uploaded_file(self):
        if self.instance and self.instance.verification_document:
            initial_uploaded_file = self.instance.verification_document.uploaded_file
        else:
            initial_uploaded_file = None
        self.fields["uploaded_file"] = forms.FileField(required=False, initial=initial_uploaded_file)#, help_text="(pdf format only)")


    def clean(self):
        cleaned_data = super().clean()
        the_file = cleaned_data.get("uploaded_file", None)
        # can't get the instance for this?
        if  the_file == None: # and self.app_type not in ['CUD', 'CTP', 'CEP']:
            self.add_error("uploaded_file", "You must provide a verification document for this job.")

        end_date = cleaned_data.get("end_date", None)
        is_current = cleaned_data.get("is_current", None)
        if (not end_date) and (not is_current):
            self.add_error("end_date", "You must either enter an end date or check the 'is current' checkbox.")

        return cleaned_data


    class Meta:
        model = ApplicationJobHistory
        fields = ["id", "title", "company", "phone",
            "start_date", "end_date", "is_current", "is_part_time",
            "supervisor_name", "legacy_id",
            ]
        labels = {
            "company": "Employer",
            "is_part_time": "Is this a part-time job? (Part-time planning jobs will count as half the experience.)",
            "supervisor_name": "What is the name of your supervisor?",
        }
        widgets = {
            'start_date' : YearMonthDaySelectorWidget(include_day=False),
            'end_date' : YearMonthDaySelectorWidget(include_day=False),
            'id' : forms.HiddenInput()
            }

class ASCExamJobHistoryForm(StateCountryModelFormMixin, forms.ModelForm):

    uploaded_file = forms.FileField(required=False)

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['company'].required = True
        self.fields['start_date'].required = True

        self.init_uploaded_file()

        self.fields['is_current'].initial = False
        self.fields['end_date'].help_text = 'If job is current, leave end date blank and check "is current" box. \
                                            Job experience will be calculated based on application date. \
                                            All job experience calculated on save.'

    def init_uploaded_file(self):
        if self.instance and self.instance.verification_document:
            initial_uploaded_file = self.instance.verification_document.uploaded_file
        else:
            initial_uploaded_file = None
        self.fields["uploaded_file"] = forms.FileField(required=False, initial=initial_uploaded_file)#, help_text="(pdf format only)")


    def clean(self):
        cleaned_data = super().clean()
        the_file = cleaned_data.get("uploaded_file", None)

        end_date = cleaned_data.get("end_date", None)
        is_current = cleaned_data.get("is_current", None)
        if (not end_date) and (not is_current):
            self.add_error("end_date", "You must either enter an end date or check the 'is current' checkbox.")

        return cleaned_data


    class Meta:
        model = ApplicationJobHistory
        fields = ["id", "title", "company", "phone",
            "start_date", "end_date", "is_current", "is_part_time",
            "supervisor_name", "legacy_id"
            ]
        labels = {
            "company": "Employer",
            "is_part_time": "Is this a part-time job? (Part-time planning jobs will count as half the experience.)",
            "supervisor_name": "What is the name of your supervisor?",
        }
        widgets = {
            'start_date' : YearMonthDaySelectorWidget(include_day=False),
            'end_date' : YearMonthDaySelectorWidget(include_day=False),
            'id' : forms.HiddenInput()
            }


class ExamRegistrationForm(forms.ModelForm):

    class Meta:
        model = ExamRegistration
        fields = ["release_information", "certificate_name", "ada_requirement"]
        labels = {
            "release_information": "Yes, release my information" ,
            "code_of_ethics": "I have read the AICP Code of Ethics and Professional Conduct and understand that I am subject to its provisions as of the date of submittal of this application."
        }


class ExamCodeOfEthicsForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['code_of_ethics'].required = True

    class Meta:
        model = ExamRegistration
        fields = ["code_of_ethics"]
        labels = {
            "code_of_ethics": "I have read the AICP Code of Ethics and Professional Conduct and understand that I am subject to its provisions as of the date of submittal of this application."
        }

class ExamRegistrationSearchForm(forms.Form):

    exam = forms.ModelChoiceField(queryset=Exam.objects.all().order_by("-code"), required=False)
    chapter = forms.ChoiceField(choices=((None,"-----------"),) + (CHAPTER_CHOICES), required=False)
    first_name = forms.CharField(required = False)
    last_name = forms.CharField(required = False)
    pass_only = forms.BooleanField(label="Only Include Members Who Have Passed the Exam", required = False)
    show_rates = forms.BooleanField(label="Show Cumulative Pass Rates For Selected Exam", required = False)

    username = forms.CharField(required=False, label="Member ID Number")
    #status = forms.ChoiceField(choices = (REGISTRATION_TYPES))

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.query_params = args[0].copy()
        self.data = self.query_params

    def get_query_map(self):

        filter_kwargs = {}

        filter_kwargs["exam"] = self.data.get("exam", None)
        filter_kwargs["pass_only"] = self.data.get("pass_only", None)
        filter_kwargs["chapter"] = self.data.get("chapter", None)
        filter_kwargs["first_name"] = self.data.get("first_name", None)
        filter_kwargs["last_name"] = self.data.get("last_name", None)
        filter_kwargs["username"] = self.data.get("username", None)
        filter_kwargs["show_rates"] = self.data.get("show_rates", None)

        return filter_kwargs

###############################################
# AICP Candidate Program
###############################################

class AICPCandidateBasicInfoForm(forms.ModelForm):

    # mentor_enroll = forms.BooleanField(label="Check here to join the mentoring program.", required = False)

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
        # self.init_mentor_enroll()
        # self.fields["email"].required = True
        # self.fields["chapter"].required = False
        # self.fields["email"].disabled = False
        # self.fields["chapter"].disabled = True
        self.request = request

    # def init_mentor_enroll():
    #     self.fields["uploaded_file"].initial = True

    # def clean(self):

    #     cleaned_data = super().clean()
    #     mentor_choice = cleaned_data.get("mentor_enroll", None)
    #     modifier = "" if mentor_choice else "not"
    #     messages.warning(self.request,"You have elected " + modifier + " to join the mentor program.")

    #     return cleaned_data

    class Meta:
        model = Contact
        # "mentor_enroll"
        # fields = ["email", "chapter"]
        fields = []

class AICPCandidateEducationForm(AddFormControlClassMixin, forms.ModelForm):

    uploaded_file = forms.FileField(required=False)
    schools_queryset = None
    request = None
    enroll_type = None
    school_ids_list = []

    # override this to prevent init of visible school field widget
    hide_school = False

    degree_school = forms.ChoiceField(
        label="School",
        required = True,)
        # choices=[("OTHER","Other")])

    degree_program = forms.ChoiceField(
        label="Program",
        choices=[(None, "")],
        required=True
        )

    def __init__(self, request=None, enroll_type=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['graduation_date'].required = False
        self.fields['verification_document'].required = False
        self.fields['verification_document'].widget = forms.HiddenInput()
        self.fields['application'].required = False

        self.init_uploaded_file()
        self.init_school_and_degree_fields(*args, **kwargs)
        self.add_form_control_class()
        self.request = request
        self.enroll_type = enroll_type

    def init_uploaded_file(self):
        if self.instance and self.instance.verification_document:
            initial_uploaded_file = self.instance.verification_document.uploaded_file
        else:
            initial_uploaded_file = None
        self.fields["uploaded_file"] = forms.FileField(required=False, initial=initial_uploaded_file)

    def get_school_choices(self, *args, **kwargs):
        return [(None, "")] + CustomSchoolaccredited.get_all_schools(['PAB'])

    def init_school_and_degree_fields(self, *args, **kwargs):

        school = self.data.get("degree_school") or self.initial.get("degree_school") or None
        degree_program_choices = [(None, "")] + get_selectable_options_tuple_list(mode="all_programs_from_school_no_other", value=school)
        if ("OTHER", "Other") in degree_program_choices:
            degree_program_choices.remove(("OTHER", "Other"))

        if not self.hide_school:
            self.fields["degree_school"].widget = SelectFacade(attrs={
                "class":"selectchain",
                "data-selectchain-mode":"all_programs_from_school_no_other",
                "data-selectchain-target":"#degree-program-select"})

        self.fields["degree_school"].choices = self.get_school_choices()
        self.fields["degree_program"].widget = SelectFacade(attrs={ "id":"degree-program-select"})
        self.fields["degree_program"].choices = degree_program_choices

    def clean(self):

        cleaned_data = super().clean()
        errors_occurred = False
        the_file = cleaned_data.get("uploaded_file", None)

        # this is the seqn (primary key) of the imis CustomSchoolaccredited record
        degree_program = cleaned_data.get("degree_program", None)

        the_school = CustomSchoolaccredited.objects.filter(seqn=degree_program).first()
        if not the_school:
            self.add_error("degree_school", "You must select an accredited educational institution.")
            errors_occurred = True

        if not degree_program:
            self.add_error("degree_program", "You must select an accredited program.")
            errors_occurred = True

        graduation_date = cleaned_data.get("graduation_date", None)
        if graduation_date:
            if graduation_date < the_school.start_date.date() or graduation_date > the_school.end_date.date():
                self.add_error("graduation_date", "Your graduation date falls outside of the accredited period.")
                errors_occurred = True

        is_planning = cleaned_data.get("is_planning", False)

        if self.enroll_type == 'full_enroll' and not graduation_date:
            self.add_error("graduation_date", "You must enter your graduation date if you are enrolling as a graduate.")
            errors_occurred = True

        if self.enroll_type == 'full_enroll' and the_file is None:
                self.add_error("verification_document", "You must provide a verification document for this degree.")
                errors_occurred = True

        if the_school:
            degree_valid = CustomSchoolaccredited.is_valid_program_date(the_school.seqn, graduation_date)

            if degree_valid and is_planning:
                cleaned_data["pab_accredited"] = True
            else:
                cleaned_data["pab_accredited"] = False
        if errors_occurred:
            messages.error(self.request,"Errors detected -- see below.")

        return cleaned_data

    class Meta:
        model = ApplicationDegree
        # "program", "school", "accredited_program", "is_current",
        fields = ["application", "pab_accredited", "graduation_date",
                    "verification_document", "uploaded_file",
            ]
        labels = {
            "graduation_date": "Date of graduation (mm/dd/yyyy)",
        }


