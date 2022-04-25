import datetime
import re

import magic
from django import forms
from django.utils import timezone
from sentry_sdk import capture_exception

from content.forms import StateCountryModelFormMixin, AddFormControlClassMixin
from content.widgets import YearMonthDaySelectorWidget, SelectFacade
from imis.models import CustomSchoolaccredited
from myapa.models.constants import RACE_CHOICES, HISPANIC_ORIGIN_CHOICES, GENDER_CHOICES, FUNCTIONAL_TITLE_CHOICES, \
    SALARY_CHOICES, SALARY_CHOICES_ALL, DEGREE_TYPE_CHOICES
from myapa.models.contact import Contact
from myapa.models.educational_degree import EducationalDegree
from myapa.models.job_history import JobHistory
from myapa.models.profile import IndividualProfile
from myapa.models.proxies import Organization, School
from ui.utils import get_selectable_options_tuple_list
from uploads.models import DocumentUpload, ImageUpload, UploadType


PREFIX_NAME_CHOICES = [
    ("Col.", "Col."),
    ("Cpt", "Cpt."),
    ("Dr", "Dr."),
    ("Hon.", "Hon."),
    ("Lt", "Lt."),

    ("Maj", "Maj."),
    ("Mr.", "Mr."),
    ("Mrs.", "Mrs."),
    ("Ms", "Ms."),
    ("Prof", "Prof."),

    ("Rev.", "Rev."),
    ("Sgt", "Sgt.")
]

SUFFIX_NAME_CHOICES = [
    ("II", "II"),
    ("III", "III"),
    ("IV", "IV"),
    ("Jr.", "Jr."),
    ("Sr.", "Sr.")
]

PASSWORD_HINT_CHOICES = [
    ("A", "What is your Mother's Maiden Name?"),
    ("B", "What city were you born in?"),
    ("C", "What is your pet's name?"),
    ("D", "What is your Father's Middle Name?"),
    ("E", "What is your favorite sports team?")
]

CONTACT_PREFERENCES_CHOICES = (
    (
        "CP_INTERACT",
        "I would like to receive Interact (available to APA members only) and other general APA membership information"
    ),
    ("CP_PAS", "Include me in information about the Planning Advisory Service and APA research"),
    ("CP_COMMISSIONER", "Include me in information about The Commissioner"),
    ("CP_JAPA", "Include me in information about the Journal of the American Planning Association"),
    ("CP_PLANNING", "Include me in information about Planning magazine"),
    ("CP_ZP", "Include me in information about Zoning Practice"),
    ("CP_NATLCONF", "Include me in information about the National Planning Conference"),
    ("CP_OTHERCONF", "Include me in information about Other Conferences and In-Person Events"),
    ("CP_PAC", "Include me in information about the Policy and Advocacy Conference"),
    ("CP_PAN", "Include me in information about the Planners Advocacy Network"),
    ("CP_FOUNDATION", "Include me in information about the APA Foundation"),
    ("CP_LEARN", "Include me in information about APA Learn"),
    ("CP_PLANNING_HOME", "Include me in information about Planning Home"),
    ("CP_SURVEY", "Include me in surveys"),
    ("CP_MAIL_LIST", "Include me in information from partners and affiliates"),
)


class AddressesFormMixin(StateCountryModelFormMixin):

    def init_address_fields(self, is_individual=True):

        additional_address1 = self.data.get("additional_address1", False)
        has_additional_address = bool(additional_address1)

        self.fields["user_address_num"] = forms.IntegerField(
            required=False,
            widget=forms.HiddenInput()
        )
        self.fields["address1"] = forms.CharField(
            label="Address Line 1",
            required=True,
            help_text="Street Address, P.O. Box, c/o"
        )
        self.fields["address2"] = forms.CharField(
            label="Address Line 2",
            required=False,
            widget=forms.TextInput(attrs={"placeholder": "Optional"}),
            help_text="Apartment, suite, unit, building, floor, etc."
        )
        self.fields["city"] = forms.CharField(label="City",  required=True)
        self.fields["zip_code"] = forms.CharField(label="Zip/Postal Code", required=True)
        self.fields["company"] = forms.CharField(
            label="Company",
            required=False,
            widget=forms.TextInput(attrs={"placeholder": "Optional"})
        )

        # Additional Address Info
        self.fields["additional_user_address_num"] = forms.IntegerField(
            required=False,
            widget=forms.HiddenInput()
        )
        self.fields["additional_address1"] = forms.CharField(
            label="Address Line 1",
            required=has_additional_address,
            help_text="Street Address, P.O. Box, c/o"
        )
        self.fields["additional_address2"] = forms.CharField(
            label="Address Line 2",
            required=False,
            widget=forms.TextInput(attrs={"placeholder": "Optional"}),
            help_text="Apartment, suite, unit, building, floor, etc."
        )
        self.fields["additional_city"] = forms.CharField(
            label="City",
            required=has_additional_address
        )
        self.fields["additional_zip_code"] = forms.CharField(
            label="Zip/Postal Code",
            required=has_additional_address
        )
        self.fields["additional_company"] = forms.CharField(
            label="Company",
            required=False,
            widget=forms.TextInput(attrs={"placeholder": "Optional"})
        )

        # Mailing/Billing Preferences
        if is_individual:
            billing_choices = (('Home Address', 'Set Home as billing address.'),
                       ('Work Address', 'Set Work as billing address.'),
                       # ('Other Address', 'Set Other as billing address.')
                       )
            mailing_choices = (('Home Address', 'Set Home as mailing address.'),
                       ('Work Address', 'Set Work as mailing address.'),
                       # ('Other Address', 'Set Other as mailing address.')
                       )
        else:
            billing_choices = (('Home Address', 'Set Primary as billing address.'),
                       ('Work Address', 'Set Secondary as billing address.'),
                       # ('Other Address', 'Set Other as billing address.')
                       )
            mailing_choices = (('Home Address', 'Set Primary as mailing address.'),
                       ('Work Address', 'Set Secondary as mailing address.'),
                       # ('Other Address', 'Set Other as mailing address.')
                       )
        self.fields["billing_preferences"] = forms.ChoiceField(widget=forms.RadioSelect, required=True,
                                                       label="Billing Address Preferences",
                                          choices=billing_choices, initial='Home Address')
        self.fields["mailing_preferences"] = forms.ChoiceField(widget=forms.RadioSelect, required=True,
                                                       label="Mailing Address Preferences",
                                          choices=mailing_choices, initial='Home Address')

        # these are for display, may be necessary depending on design choices
        self.fields["home_preferred_mail"] = forms.BooleanField(
            label="Preferred Mailing",
            required=False,
            disabled=True,
        )
        self.fields["home_preferred_bill"] = forms.BooleanField(
            label="Preferred Billing",
            required=False,
            disabled=True,
        )
        self.fields["work_preferred_mail"] = forms.BooleanField(
            label="Preferred Mailing",
            required=False,
            disabled=True,
        )
        self.fields["work_preferred_bill"] = forms.BooleanField(
            label="Preferred Billing",
            required=False,
            disabled=True,
        )

        self.init_state_country_fields()
        self.init_state_country_fields(
            prefix="additional_",
            state_required=has_additional_address,
            country_required=has_additional_address
        )

        self.fields["state"].label = "State/Province"
        self.fields["additional_state"].label = "State/Province"
        self.fields["additional_country"].label = "Country"


class BaseCreateAccountForm(forms.ModelForm):

    # Name Information
    prefix_name = forms.ChoiceField(
        label="Prefix",
        required=False,
        choices=[("", "")] + PREFIX_NAME_CHOICES,
    )
    first_name = forms.CharField(label="First Name", required=True)
    middle_name = forms.CharField(
        label="Middle Initial",
        required=False,
        widget=forms.TextInput(
            attrs={'placeholder': 'Optional'}
        ),
    )
    last_name = forms.CharField(label="Last Name", required=True)
    suffix_name = forms.ChoiceField(
        label="Suffix",
        required=False,
        choices=[("", "")] + SUFFIX_NAME_CHOICES,
    )
    informal_name = forms.CharField(
        label="Nickname",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Optional'}),
    )

    birth_date = forms.DateField(
        label="Date of Birth",
        required=True,
        widget=YearMonthDaySelectorWidget(attrs={"style": "width:auto;display:inline-block"}))

    # Email Fields
    email = forms.EmailField(
        label="Email Address",
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'required': ''})
    )

    secondary_email = forms.EmailField(
        label="Email Address",
        required=False,
        widget=forms.EmailInput(attrs={'placeholder': 'Optional'})
    )

    # Phone Fields preferably only digits, js autoformat
    phone = forms.CharField(label="Home Phone Number", required=False)
    secondary_phone = forms.CharField(label="Work Phone Number", required=False)
    cell_phone = forms.CharField(label="Cell Phone Number", required=False)

    def clean(self):

        cleaned_data = super().clean()

        email = cleaned_data.get("email", None)
        phone = cleaned_data.get("phone", None)
        secondary_phone = cleaned_data.get("secondary_phone", None)
        cell_phone = cleaned_data.get("cell_phone", None)

        existing_contact_with_email = email and Contact.objects.filter(email=email).first()

        trying_new_email = not self.instance or (email != self.instance.email)
        if existing_contact_with_email and trying_new_email:
            self.add_error(
                "email",
                "An account already exists with the email address you've entered. "
                "Please try using an alternative email."
            )

        if not (phone or secondary_phone or cell_phone):
            self.add_error("cell_phone", "Please provide at least one phone number.")
            self.add_error("phone", "Please provide at least one phone number.")
            self.add_error("secondary_phone", "Please provide at least one phone number.")

        return cleaned_data

    class Meta:
        model = Contact
        fields = [
            "prefix_name",
            "first_name",
            "middle_name",
            "last_name",
            "suffix_name",
            "email",
            "secondary_email",
            "phone",
            "secondary_phone",
            "cell_phone",
            "birth_date"
        ]


class CreateAccountForm(AddFormControlClassMixin, BaseCreateAccountForm):
    """
    Adds verify email and password fields to the create account form
    """

    # Email Fields
    email = forms.EmailField(
        label="EMAIL ADDRESS",
        required=True,
        widget=forms.EmailInput(
            attrs={'class': 'form-control validate-field-email', 'required': ''}
        ),
    )
    verify_email = forms.EmailField(
        label="VERIFY EMAIL ADDRESS",
        required=True,
        widget=forms.EmailInput(
            attrs={'class': 'form-control validate-field-email-confirm', 'required': ''}
        ),
    )
    secondary_email = forms.EmailField(
        label="EMAIL ADDRESS",
        required=False,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control validate-field-secondary-email',
                'placeholder': 'Optional'
            }
        ),
    )
    secondary_verify_email = forms.EmailField(
        label="VERIFY EMAIL ADDRESS",
        required=False,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control validate-field-secondary-email-confirm',
                'placeholder': 'Optional'
            }
        ),
    )

    # Password Fields
    password = forms.CharField(
        label="Password",
        required=True,
        help_text="Passwords must be between 8-16 characters in length",
        widget=forms.PasswordInput(
            render_value=True,
            attrs={'class': 'form-control validate-field-password', 'required': ''}
        )
    )
    verify_password = forms.CharField(
        label="Verify Password",
        required=True,
        widget=forms.PasswordInput(
            render_value=True,
            attrs={'class': 'form-control validate-field-password-confirm', 'required': ''}
        )
    )
    password_hint = forms.ChoiceField(
        label="PASSWORD VERIFICATION QUESTION",
        required=True,
        help_text="This will help APA customer service verify your identity if you request assistance.",
        choices=[("", "(Select a password verification question)")] + PASSWORD_HINT_CHOICES,
    )
    password_answer = forms.CharField(
        label="ANSWER TO PASSWORD VERIFICATION QUESTION",
        required=True
    )

    def clean(self):

        cleaned_data = super().clean()

        email = cleaned_data.get("email", None)
        verify_email = cleaned_data.get("verify_email", None)

        secondary_email = cleaned_data.get("secondary_email", None)
        secondary_verify_email = cleaned_data.get("secondary_verify_email", None)

        password = cleaned_data.get("password", None)
        verify_password = cleaned_data.get("verify_password", None)

        if email and verify_email and email != verify_email:
            self.add_error("email", "Email fields do not match")

        if secondary_email:
            if not secondary_verify_email:
                self.add_error("secondary_verify_email", "Please verify your secondary email address.")
            elif secondary_email != secondary_verify_email:
                self.add_error("secondary_email", "Email fields do not match")

        if password is None or verify_password is None:
            pass
        elif len(password) < 8 or len(password) > 16:
            self.add_error("password", "Passwords must be between 8-16 characters in length")
        elif password != verify_password:
            self.add_error("password", "Passwords do not match")

        return cleaned_data


class UpdateAccountForm(CreateAccountForm):
    prefix_name = None
    first_name = None
    middle_name = None
    last_name = None
    suffix_name = None
    password = None
    verify_password = None
    password_hint = None
    password_answer = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_form_control_class()

    class Meta:
        model = Contact
        fields = [
            "email",
            "secondary_email",
            "birth_date",
            "phone",
            "secondary_phone",
            "cell_phone"
        ]


class UpdateOrgAccountForm(forms.ModelForm):

    email = forms.EmailField(
        label="Email Address",
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control validate-field-email', 'required': ''})
    )
    verify_email = forms.EmailField(
        label="VERIFY EMAIL ADDRESS",
        required=True,
        widget=forms.EmailInput(
            attrs={'class': 'form-control validate-field-email-confirm', 'required': ''}
        ),
    )

    secondary_email = forms.EmailField(
        label="Alternate Email Address",
        required=False,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control validate-field-secondary-email',
                'placeholder': 'Optional'
            }
        )
    )
    secondary_verify_email = forms.EmailField(
        label="VERIFY ALTERNATE EMAIL ADDRESS",
        required=False,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control validate-field-secondary-email-confirm',
                'placeholder': 'Optional'
            }
        )
    )

    personal_url = forms.URLField(
        label="Your organization's website (must start with http:// or https://)",
        required=False,
        widget=forms.URLInput(
            attrs={
                "class": "form-control",
                "placeholder": "Optional"
            }
        )
    )

    secondary_phone = forms.CharField(label="Work Phone Number", required=True)

    def clean(self):
        cleaned_data = super().clean()

        email = cleaned_data.get("email", None)
        verify_email = cleaned_data.get("verify_email", None)

        secondary_email = cleaned_data.get("secondary_email", None)
        secondary_verify_email = cleaned_data.get("secondary_verify_email", None)

        if email and verify_email and email != verify_email:
            self.add_error("email", "Email fields do not match")

        if secondary_email and secondary_email != secondary_verify_email:
                self.add_error("secondary_email", "Email fields do not match")

        return cleaned_data

    class Meta:
        model = Organization
        fields = [
            "email",
            "secondary_email",
            "secondary_phone",
            "personal_url"
        ]


class UpdateAddressesForm(AddressesFormMixin, AddFormControlClassMixin, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        is_individual = kwargs.pop("is_individual")
        super().__init__(*args, **kwargs)
        self.init_address_fields(is_individual)
        self.add_form_control_class()

    def clean(self):
        cleaned_data = super().clean()
        additional_address1 = cleaned_data.get("additional_address1", None)
        has_additional_address = bool(additional_address1)

        mailing_preferences = cleaned_data.get("mailing_preferences", None)
        billing_preferences = cleaned_data.get("billing_preferences", None)

        if mailing_preferences == 'Work Address' and not has_additional_address:
            self.add_error("mailing_preferences", "Cannot set mailing preferences on a nonexistent work address")

        if billing_preferences == 'Work Address' and not has_additional_address:
            self.add_error("billing_preferences", "Cannot set billing preferences on a nonexistent work address")

        return cleaned_data

    class Meta:
        model = Contact
        fields = [
            "user_address_num",
            "address1",
            "address2",
            "country",
            "state",
            "city",
            "zip_code",
            "company"
        ]


class UpdateOrgAddressesForm(AddressesFormMixin, AddFormControlClassMixin, forms.ModelForm):
    """Same as UpdateAddressesForm, just without the company field"""

    def __init__(self, *args, **kwargs):
        is_individual = kwargs.pop("is_individual")
        super().__init__(*args, **kwargs)
        self.init_address_fields(is_individual)
        self.fields.pop('company')
        self.add_form_control_class()

    def clean(self):
        cleaned_data = super().clean()
        additional_address1 = cleaned_data.get("additional_address1", None)
        has_additional_address = bool(additional_address1)

        mailing_preferences = cleaned_data.get("mailing_preferences", None)
        billing_preferences = cleaned_data.get("billing_preferences", None)

        if mailing_preferences == 'Work Address' and not has_additional_address:
            self.add_error("mailing_preferences", "Cannot set mailing preferences on a nonexistent work address")

        if billing_preferences == 'Work Address' and not has_additional_address:
            self.add_error("billing_preferences", "Cannot set billing preferences on a nonexistent work address")

        return cleaned_data

    class Meta:
        model = Contact
        fields = [
            "user_address_num",
            "address1",
            "address2",
            "country",
            "state",
            "city",
            "zip_code",
        ]


class DemographicsForm(forms.Form):

    race = forms.MultipleChoiceField(
        label="Race",
        required=True,
        help_text="Please complete the sections for Hispanic Origin and Race. APA uses this data to better understand the diversity of our members. The information we collect correlates with U.S. Census Bureau reports.",
        choices=list(RACE_CHOICES) + [("NO_ANSWER", "I prefer not to answer")],
        widget=forms.CheckboxSelectMultiple()
    )
    hispanic_origin = forms.ChoiceField(
        label="Hispanic Origin",
        required=True,
        help_text="Please select one below",
        choices=list(HISPANIC_ORIGIN_CHOICES),
        widget=forms.RadioSelect()
    )

    gender = forms.ChoiceField(
        label="Gender",
        required=True,
        choices=[(None, "- select -")] + list(GENDER_CHOICES),
        widget=forms.Select(attrs={"style": "width:auto"}),
    )

    gender_other = forms.CharField(label="How You Self-Describe", required=False, max_length=25)

    ai_an = forms.CharField(required=False)
    asian_pacific = forms.CharField(required=False)
    other = forms.CharField(required=False)
    span_hisp_latino = forms.CharField(required=False)

    race_option_other = {
        "E003": "ai_an",
        "E100": "asian_pacific",
        "E999": "other"
    }
    hispanic_origin_option_other = {
        "O999": "span_hisp_latino"
    }

    def clean(self):
        cleaned_data = super().clean()

        gender = cleaned_data.get("gender", None)

        if gender != "N":
            cleaned_data["gender_other"] = ""

        return cleaned_data


class PersonalInformationForm(AddFormControlClassMixin, forms.ModelForm):
    """
    Form for entering personal information
    """
    functional_title = forms.ChoiceField(
        label="Planning Functional Title",
        required=False,
        help_text="Choose the functional title that most closely matches your position.",
        choices=[(None, "Optional")] + list(FUNCTIONAL_TITLE_CHOICES)
    )

    job_title = forms.CharField(
        label="Current Job Title",
        required=False,
        help_text="What is your current, actual job title?"
    )

    salary_range = forms.ChoiceField(
        label="Salary",
        required=True,
        help_text="To ensure equity for all members, APA dues are based on your current total annual income. Please select your range.",
        choices=[(None, "- select -")] + list(SALARY_CHOICES)
    )

    race = forms.MultipleChoiceField(
        label="Race",
        required=True,
        help_text="Please complete the sections for Hispanic Origin and Race. APA uses this data to better understand the diversity of our members. The information we collect correlates with U.S. Census Bureau reports.",
        choices=list(RACE_CHOICES) + [("NO_ANSWER", "I prefer not to answer")],
        widget=forms.CheckboxSelectMultiple()
    )

    hispanic_origin = forms.ChoiceField(
        label="Hispanic Origin",
        required=True,
        help_text="Please select one below",
        choices=list(HISPANIC_ORIGIN_CHOICES),
        widget=forms.RadioSelect()
    )

    gender = forms.ChoiceField(
        label="Gender",
        required=True,
        choices=[(None, "- select -")] + list(GENDER_CHOICES),
        widget=forms.Select(attrs={"style": "width:auto"}),
    )

    gender_other = forms.CharField(label="How You Self-Describe", required=False, max_length=25)

    ai_an = forms.CharField(required=False)
    asian_pacific = forms.CharField(required=False)
    other = forms.CharField(required=False)
    span_hisp_latino = forms.CharField(required=False)

    race_option_other = {
        "E003": "ai_an",
        "E100": "asian_pacific",
        "E999": "other"
    }
    hispanic_origin_option_other = {
        "O999": "span_hisp_latino"
    }

    def __init__(self, *args, **kwargs):

        self.member_type = kwargs.pop("member_type")  # This is required kwarg
        self.is_student = kwargs.pop("is_student", False)
        self.is_international = kwargs.pop("is_international", False)
        self.is_new_membership_qualified = kwargs.pop("is_new_membership_qualified", False)

        super().__init__(*args, **kwargs)

        self.fix_salary_range_field()

        for field_name in self.fields:
            field = self.fields[field_name]
            if not field.required:
                field.widget.attrs.update({"placeholder": "Optional"})

        self.add_form_control_class()

    def fix_salary_range_field(self):
        """ This is necessary because of special salary ranges logic for retired, international, students, etc.
            This value determines the price of membership, chapter, subscriptions, divisions, etc
            We don't want users to choose their salary range under special circumstances. Instead it is assigned """

        hide_salary = self.is_student \
                      or self.is_new_membership_qualified \
                      or self.is_international \
                      or self.member_type in ('RET', 'LIFE')
        if hide_salary:
            self.fields["salary_range"].widget = forms.HiddenInput()
            self.fields["salary_range"].choices = list(SALARY_CHOICES_ALL)
            self.fields["salary_range"].required = False

    def clean(self):
        cleaned_data = super().clean()

        gender = cleaned_data.get("gender", None)

        if gender != "S":
            cleaned_data["gender_other"] = ""

        return cleaned_data

    class Meta:
        model = Contact
        fields = ["salary_range"]


class ContactPreferencesUpdateForm(AddFormControlClassMixin, forms.Form):
    # fields for planning magazine
    exclude_planning_print = forms.BooleanField(
        label="I would like to receive only the digital edition of Planning. I do not want to receive the print edition.",
        required=False
    )

    preferences = forms.MultipleChoiceField(
        required=False,
        choices=sorted(CONTACT_PREFERENCES_CHOICES, key=lambda x: x[1]),
        widget=forms.CheckboxSelectMultiple(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_form_control_class()


class ResumeUploadForm(AddFormControlClassMixin, forms.ModelForm):

    MAX_FILE_SIZE = 30000000  # Maximum file size of uploaded resumes in bytes
    ACCEPTABLE_FILE_EXTENSIONS = ['pdf']
    ACCEPTABLE_MIME_TYPES = ['application/pdf']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["uploaded_file"].widget = forms.FileInput()
        self.add_form_control_class()

    def clean(self):
        cleaned_data = super().clean()
        uploaded_file = cleaned_data.get("uploaded_file", None)
        uploaded_file_size = getattr(uploaded_file, "size", None)
        uploaded_file_name = getattr(uploaded_file, "name", '')
        uploaded_file_extension = uploaded_file_name.split('.')[-1]

        file_is_valid = True

        if not uploaded_file:
            self.add_error("uploaded_file", "Please select a document to upload.")

        if uploaded_file and uploaded_file_size is not None and uploaded_file_size > self.MAX_FILE_SIZE:
            self.add_error("uploaded_file", "Please ensure your document is not larger than 30MB")
            file_is_valid = False

        # Do the security theater method first
        if file_is_valid \
            and uploaded_file \
            and uploaded_file_extension.lower() not in self.ACCEPTABLE_FILE_EXTENSIONS:
            self.add_error("uploaded_file", "Please ensure that your document is a pdf")
            file_is_valid = False

        # Do the slightly better libmagic method last
        if file_is_valid and uploaded_file:
            the_file = getattr(uploaded_file, 'file', None)
            if the_file is not None:
                try:
                    content_type = magic.from_buffer(the_file.getvalue(), mime=True)
                except (AttributeError, TypeError):
                    try:
                        content_type = magic.from_buffer(the_file.file.read(1024), mime=True)
                    except Exception as exc:
                        content_type = None
                        capture_exception(exc)
                        self.add_error(
                            "uploaded_file",
                            "Something went wrong trying to upload your document. "
                            "Please try re-exporting to UTF-8 encoded PDF."
                        )
                if content_type not in self.ACCEPTABLE_MIME_TYPES:
                    self.add_error(
                        "uploaded_file",
                        "Please ensure that your document is a pdf"
                    )

        return cleaned_data

    def save(self, commit=True):
        resume = super().save(commit=False)
        resume.upload_type = UploadType.objects.get(code="RESUMES")
        if commit:
            resume.save()
        return resume

    class Meta:
        model = DocumentUpload
        fields = ["uploaded_file"]


class EducationDegreeForm(AddFormControlClassMixin, forms.ModelForm):

    school = forms.ChoiceField(
        label="School",
        required=True,
        choices=[("OTHER", "Other")]
    )

    other_school = forms.CharField(
        label="Other school if yours is not listed above",
        required=False
    )

    degree_program = forms.ChoiceField(
        label="Program",
        choices=[(None, ""), ],
        help_text="(Optional if School is 'Other')",
        required=False
        )

    degree_type_choice = forms.ChoiceField(
        label="Degree Type",
        choices=((None, "Select a Degree Type"), ) + DEGREE_TYPE_CHOICES + (("OTHER", "Other"), ),
        required=False
    )

    degree_type_other = forms.CharField(
        label="Other Degree Type",
        required=False
    )

    level = forms.ChoiceField(
        label="Degree Level",
        required=False,
        choices=(
            (None, "Select a Degree Level"),
            ("B", "Undergraduate"),
            ("M", "Graduate"),
            ("P", "Post-Graduate (PhD, J.D., etc.)"),
            ("N", "Other")
        )
    )

    level_other = forms.CharField(
        label="Other Degree Level",
        required=False
    )

    graduation_date = forms.DateField(
        label="Graduation Date",
        help_text="If you have not graduated, enter an expected graduation date or the date you were last enrolled.",
        required=False,
        widget=YearMonthDaySelectorWidget(
            max_year=datetime.datetime.today().year+20,
            min_year=1900,
            include_day=False,
            attrs={"style": "width:auto;display:inline-block"}
        )
    )

    is_current = forms.BooleanField(
        label="I am currently enrolled in this program",
        required=False
    )

    complete = forms.BooleanField(
        label="I have completed this degree",
        required=False
    )

    student_id = forms.CharField(
        label="Student ID",
        widget=forms.TextInput(attrs={"placeholder": "Optional"}),
        required=False
    )

    def __init__(self, *args, **kwargs):

        initial = kwargs.pop("initial", {})
        instance = kwargs.get("instance", None)
        if instance:
            self.alter_initial_from_instance(initial, instance)
        kwargs["initial"] = initial

        self.accredited_school_choices = kwargs.pop("accredited_school_choices", None)

        super().__init__(*args, **kwargs)

        self.init_school_and_degree_fields(*args, **kwargs)
        self.add_form_control_class()

    def alter_initial_from_instance(self, initial, instance):
        """
        Method for setting initial values given only the instance passed in.
            Sets initial values for fields that are not directly linked to model fields.
            Returns the new initial values dictionary, must be passed into super().__init__
        """
        if instance.school_seqn:
            initial_degree_program = instance.school_seqn
            initial_degree_type_choice = None
            initial_degree_type_other = None
        elif instance.program in [dt[0] for dt in DEGREE_TYPE_CHOICES]:
            initial_degree_program = "OTHER"
            initial_degree_type_choice = instance.program
            initial_degree_type_other = None
        else:
            initial_degree_program = "OTHER"
            initial_degree_type_choice = "OTHER"
            initial_degree_type_other = instance.program

        initial.update({
            "school": instance.school.user.username if instance.school else "OTHER",
            "other_school": instance.other_school if not instance.school else None,  # DON'T INCLUDE IN INITIAL?
            "degree_program": initial_degree_program,
            "degree_type_choice": initial_degree_type_choice,
            "degree_type_other": initial_degree_type_other,
            "level": instance.level,  # DON'T INCLUDE IN INITIAL?
            "level_other": instance.level_other,  # DON'T INCLUDE IN INITIAL?
            "graduation_date": instance.graduation_date,  # DON'T INCLUDE IN INITIAL?
            "is_current": instance.is_current,  # DON'T INCLUDE IN INITIAL?
            "student_id": instance.student_id,  # DON'T INCLUDE IN INITIAL?
            "complete": instance.complete  # DON'T INCLUDE IN INITIAL?
        })
        return initial

    def get_accredited_school_choices(self, *args, **kwargs):
        if not self.accredited_school_choices:
            self.accredited_school_choices = CustomSchoolaccredited.get_current_schools()
        return [(None, ""), ("OTHER", "Other")] + self.accredited_school_choices

    def init_school_and_degree_fields(self, *args, **kwargs):

        data_prefix = "{}-".format(self.prefix) if self.prefix else ""

        school = self.data.get("%sschool" % data_prefix, None) or self.initial.get("school", None) or None
        degree_program_choices = [(None, "")] + get_selectable_options_tuple_list(
            mode="current_programs_from_school",
            value=school
        )

        self.fields["school"].widget = SelectFacade(
            attrs={
                "class": "selectchain",
                "data-selectchain-mode": "current_programs_from_school",
                "data-selectchain-target": "#%sdegree-program-select" % self.prefix
            }
        )
        self.fields["school"].choices = self.get_accredited_school_choices()

        self.fields["degree_program"].widget = SelectFacade(attrs={"id": "%sdegree-program-select" % self.prefix})
        self.fields["degree_program"].choices = degree_program_choices

    def clean(self):

        school = self.cleaned_data.get("school")
        other_school = self.cleaned_data.get("other_school")
        degree_program = self.cleaned_data.get("degree_program")
        degree_type_choice = self.cleaned_data.get("degree_type_choice")
        degree_type_other = self.cleaned_data.get("degree_type_other")
        level = self.cleaned_data.get("level")
        level_other = self.cleaned_data.get("level_other")
        is_current = self.cleaned_data.get("is_current")
        is_complete = self.cleaned_data.get("complete")
        graduation_date = self.cleaned_data.get("graduation_date")

        if school == "OTHER":
            if not other_school:
                self.add_error("other_school", "Please provide an other value")
        else:
            self.cleaned_data["other_school"] = next((s[1] for s in self.fields["school"].choices if s[0] == school), None)

            if not degree_program:
                self.add_error("degree_program", "This field is required")
            elif degree_program == "OTHER":
                if not degree_type_choice:
                    self.add_error("degree_type_choice", "This field is required")
                elif degree_type_choice == "OTHER" and not degree_type_other:
                    self.add_error("degree_type_other", "Please provide an other value")
            elif graduation_date and not CustomSchoolaccredited.is_valid_program_date(degree_program, graduation_date):
                # if school and program are selected, check that the program was offered at the time of graduation
                self.add_error("degree_program", "The program that you have selected is not valid for the given graduation date.")

        if level == "N":
            if not level_other:
                self.add_error("level_other", "Please provide an other value")
        else:
            self.cleaned_data["level_other"] = None

        if is_complete and is_current:
            self.add_error("is_current", "You cannot be currently enrolled in a program you have completed")

        if not is_current and is_complete and not graduation_date:
            self.add_error("graduation_date", "You must provide a graduation date for completed degrees.")

        if graduation_date:
            now = timezone.now()
            grad_year = graduation_date.year
            grad_month = graduation_date.month
            now_year = now.year
            now_month = now.month
            is_graduation_date_past = grad_year < now_year or (grad_year == now_year and grad_month < now_month)
            is_graduation_date_future = grad_year > now_year or (grad_year == now_year and grad_month > now_month)

            if is_current and is_graduation_date_past:
                self.add_error("is_current", "Current degrees cannot have a past graduation date")

            if is_complete and is_graduation_date_future:
                self.add_error("complete", "Completed degrees cannot have a future graduation date")

        return self.cleaned_data

    def save(self, commit=True):

        degree = super().save(commit=False)

        school = self.cleaned_data.get("school")
        degree_program = self.cleaned_data.get("degree_program")
        degree_type_choice = self.cleaned_data.get("degree_type_choice")
        degree_type_other = self.cleaned_data.get("degree_type_other")

        if school != "OTHER":
            # choices are usernames so we need to query for actual record
            degree.school = School.objects.only("id").get(user__username=school)
        else:
            degree.school = None

        if school == "OTHER" or degree_program == "OTHER":
            degree.school_seqn = None
            degree.program = degree_type_choice if degree_type_choice != "OTHER" else degree_type_other
        else:
            # TODO pass accredited schools into init so we don't have to query here?
            imis_school = CustomSchoolaccredited.objects.only("degree_level", "degree_program").get(id=school, seqn=degree_program)
            degree.school_seqn = degree_program
            degree.program = imis_school.degree_program
            degree.level = imis_school.degree_level
            degree.level_other = None
            degree.is_planning = True

        if commit:
            degree.save()

        return degree

    class Meta:
        model = EducationalDegree
        fields = ["other_school", "level", "level_other", "graduation_date", "is_current", "complete", "student_id"]


class JobHistoryUpdateForm(StateCountryModelFormMixin, forms.ModelForm):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.init_state_country_fields(state_required=False, country_required=False)

        self.fields['is_current'].label = "Currently working"
        self.fields['is_part_time'].label = "Part time"
        self.fields['zip_code'].label = "Zip/Postal Code"
        self.fields['state'].label = "State/Prov"

        self.fields['start_date'].widget.attrs['class'] = 'form-control form-control-2-col'
        self.fields['end_date'].widget.attrs['class'] = 'form-control form-control-2-col'

        self.add_form_control_class()

    def add_form_control_class(self):
        """
        adds the form-control class to all initialized fields in the form
        """

        for field in self.fields:
            class_attr = self.fields[field].widget.attrs.get("class", '')
            if not re.search(r'\bform-control\b', class_attr):
                self.fields[field].widget.attrs["class"] = "form-control " + class_attr

    class Meta:
        model = JobHistory
        fields = ["title", "company", "is_current", "is_part_time", "start_date", "end_date", "country", "city", "state", "zip_code", "id"]
        widgets = {
            'start_date': YearMonthDaySelectorWidget(include_day=False),
            'end_date': YearMonthDaySelectorWidget(include_day=False)
            }


class AboutMeAndBioUpdateForm(forms.ModelForm):

    bio = forms.CharField(
        label="Professional Biography",
        help_text="Tell about your key accomplishments, past assignments, and education. Write in third person (“he” or “she”).",
        required=False
    )
    about_me = forms.CharField(
        label="About Me",
        help_text="Let other members get to know you. Share a brief description of yourself.",
        required=False
    )

    def __init__(self, *args, **kwargs):
        super(AboutMeAndBioUpdateForm, self).__init__(*args, **kwargs)
        self.fields["bio"].widget = forms.Textarea(attrs={'rows': 5, 'cols': 15, "class": "form-control"})
        self.fields["about_me"].widget = forms.Textarea(attrs={'rows': 5, 'cols': 15, "class": "form-control"})

    class Meta:
        model = Contact
        fields = ["bio", "about_me"]


class UpdateSocialLinksForm(forms.ModelForm):
    personal_url = forms.CharField(
        label="Personal (or company)",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: http://www.example.com'})
    )
    linkedin_url = forms.CharField(
        label="LinkedIn",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: https://www.linkedin.com/in/username'})
    )
    facebook_url = forms.CharField(
        label="Facebook",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: https://www.facebook.com/username'})
    )
    twitter_url = forms.CharField(
        label="Twitter",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: https://twitter.com/username'})
    )
    instagram_url = forms.CharField(
        label="Instagram",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: https://www.instagram.com/username'})
    )

    class Meta:
        model = Contact
        fields = ["personal_url", "linkedin_url", "facebook_url", "twitter_url", "instagram_url"]


class AdvocacyNetworkForm(forms.Form):
    # field to opt in to network
    grassroots_member = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    # TO DO... how to incorporate advocacy interests and address selection?


class ImageUploadForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ImageUploadForm, self).__init__(*args, **kwargs)
        images = UploadType.objects.get(code="PROFILE_PHOTOS")
        self.fields['upload_type'].initial = images.id

    def clean(self):

        cleaned_data = super().clean()
        image_file = cleaned_data.get("image_file", None)
        if not image_file:
            self.add_error("image_file", "Please select an image to upload.")

        return cleaned_data

    class Meta:
        model = ImageUpload
        fields = ["image_file", "upload_type"]


class ProfileShareForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    class Meta:
        model = IndividualProfile
        fields = ["share_profile", "share_contact", "share_bio", "share_social",
                  "share_leadership", "share_education", "share_jobs", "share_events",
                  "share_resume", "share_conference", "share_advocacy", "speaker_opt_out"]
        labels = {
            "share_profile": "Share Your Profile",
            "share_contact": "Share Your Contact Information",
            "share_bio": "Share Your Professional Biography",
            "share_social": "Share Your Social Links",
            "share_leadership": "Share Your Leadership",
            "share_education": "Share Your Education",
            "share_jobs": "Share Your Job History",
            "share_events": "Share Events You Attended",
            "share_resume": " Share Your Resume",
            "share_conference": "Share Conferences You Attended",
            "share_advocacy": "Share Issues You Advocate For",
            "speaker_opt_out": """Exclude Me from the APA Speaker Directory
                (if you were a speaker at the National Planning Conference after 2014)""",
        }
