import re

from django import forms
from django.core.exceptions import ValidationError

from cm.models import ProviderRegistration, ProviderApplication, Provider, PROVIDER_APPLICATION_YEAR
from content.forms import AddFormControlClassMixin
from content.forms import StateCountryModelFormMixin
from content.widgets import SelectFacade
from events.models import EVENT_TYPES
from uploads.forms import ImageUploadBaseForm
from uploads.models import ImageUpload

# TO DO... remove completely
YEARS_2015=(
    ("2008", "2008"),
    ("2009", "2009"),
    ("2010", "2010"),
    ("2011", "2011"),
    ("2012", "2012"),
    ("2013", "2013"),
    ("2014", "2014"),
    ("2015", "2015"),
)

# TO DO... not needed... instead pull widget values based on PROVIDER_APPLICATION_YEAR and PROVIDER_APPLICATION_YEAR - 1
# and whether provider has already registered for those years.
YEARS = (
    ("2016", "2016"),
    ("2017", "2017"),
    ("2018", "2018")
)


class ProviderEventSearchFilterForm(forms.Form):

    def __init__(self, *args, **kwargs):
        year_options = kwargs.pop("year_options")
        super().__init__(*args, **kwargs)

        self.fields["type"] = forms.ChoiceField(
            widget=SelectFacade(facade_attrs={"data-empty-text":"All"}),
            choices=[("","All")] + [x for x in EVENT_TYPES],
            required=False
        )

        year_tuple_list = []
        for year in year_options:
            year_tuple_list.append( (year,year) )

        self.fields["time"] = forms.ChoiceField(
            widget=SelectFacade(facade_attrs={"data-empty-text":"All"}),
            choices=[("ALL","All"), ("CURRENT", "Current Year and Forward"), ("PAST", "Past"), ("FUTURE", "Future")] + year_tuple_list,
            required=False
        )

        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class RadioSelectWithoutUL(forms.RadioSelect):
    template_name = 'forms/widgets/radio.html'


class ProviderRegistrationForm(forms.ModelForm):
    """
    Form for submitting provider registrations
    """
    years_choices = [PROVIDER_APPLICATION_YEAR, PROVIDER_APPLICATION_YEAR - 1]

    def __init__(self, *args, **kwargs):
        years_choices = kwargs.pop("years_choices", self.years_choices)
        my_registration_choices = kwargs.pop('registration_choices')

        super().__init__(*args, **kwargs)

        registration_choices = self.fields["registration_type"].choices
        self.fields["registration_type"].choices = [
            choice for choice in registration_choices if choice[0] in my_registration_choices
        ]
        self.fields["year"].widget = forms.Select(choices=years_choices)

        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    class Meta:
        model = ProviderRegistration
        fields = ["registration_type", "provider", "year"]
        widgets = {
                "provider": forms.HiddenInput(),
                "registration_type": RadioSelectWithoutUL()
            }


class ProviderRegistration2015Form(ProviderRegistrationForm):
    """
    Form for submitting provider registrations
    """
    years_choices = YEARS_2015
    my_registration_choices = ("CM_UNLIMITED_1",
            "CM_UNLIMITED_INHOUSE", "CM_UNLIMITED_NONPROFIT_1", "CM_UNLIMITED_NONPROFIT_2",
            "CM_UNLIMITED_NONPROFIT_3", "CM_UNLIMITED_NONPROFIT_4", )


class ProviderApplicationForm(AddFormControlClassMixin, forms.ModelForm):

    explain_topics = forms.CharField(
        required=True,
        widget=forms.Textarea(),
        label="""Briefly explain how your organization ensures that the topics selected enhance
        and expand the skills, knowledge, and abilities of practicing planners."""
    )

    objectives_example_1 = forms.CharField(
        required=True,
        widget=forms.Textarea(),
        label="Example 1: Activity Name and Objectives"
    )
    objectives_example_2 = forms.CharField(
        required=True,
        widget=forms.Textarea(),
        label="Example 2: Activity Name and Objectives"
    )
    objectives_example_3 = forms.CharField(
        required=True,
        widget=forms.Textarea(),
        label="Example 3: Activity Name and Objectives"
    )

    how_determines_speakers = forms.CharField(
        required=True,
        widget=forms.Textarea(),
        label="""How does your organization determine and evaluate the appropriate qualifications for speakers?"""
    )

    def __init__(self, *args, **kwargs):

        self.is_strict = kwargs.pop("is_strict", True)

        super().__init__(*args, **kwargs)

        self.fields["explain_topics"].required = self.is_strict
        self.fields["objectives_example_1"].required = self.is_strict
        self.fields["objectives_example_2"].required = self.is_strict
        self.fields["objectives_example_3"].required = self.is_strict
        self.fields["how_determines_speakers"].required = self.is_strict
        self.fields["objectives_status"].required = self.is_strict

        self.fields["objectives_status"].label = "Does your organization develop written learning/training objectives?"

        self.add_form_control_class()

    class Meta:
        model = ProviderApplication
        fields = [
            "explain_topics",
            "objectives_example_1",
            "objectives_example_2",
            "objectives_example_3",
            "how_determines_speakers",
            "objectives_status"
        ]


class ProviderApplicationReturningForm(ProviderApplicationForm):

    class Meta:
        model = ProviderApplication
        fields = ["explain_topics", "objectives_example_1", "objectives_example_2", "objectives_example_3",
            "how_determines_speakers", "objectives_status"]


class ProviderApplicationReviewForm(forms.Form):
    agree = forms.BooleanField(label="Agree", required=True)


class ProviderNewRegistrationForm(StateCountryModelFormMixin, forms.ModelForm):

    EIN_PATTERN = re.compile(r'^\d{2}-?\d{7}$')
    INVALID_EIN_MESSAGE = "This does not appear to be a valid EIN. Please ensure the value you enter is 9 digits, with or without the dash."

    ein_number = forms.CharField(required=True)
    address2 = forms.CharField(max_length=80, required=False)
    personal_url = forms.CharField(max_length=80, required=False)
    bio = forms.CharField(widget=forms.Textarea(attrs={"class": "full-width"}))

    def __init__(self, *args, **kwargs):
        super(ProviderNewRegistrationForm, self).__init__(*args, **kwargs)

        self.init_state_country_fields()

        self.fields['company'].required = True
        self.fields['organization_type'].required = True
        self.fields['address1'].required = True
        self.fields['city'].required = True
        self.fields['zip_code'].required = True
        self.fields['phone'].required = True
        self.fields['address2'] = forms.CharField(
            required=False,
            widget=forms.TextInput(attrs={'placeholder': 'Optional'})
        )
        self.fields['personal_url'] = forms.URLField(
            required=False,
            widget=forms.URLInput(attrs={'placeholder': 'Optional'}),
            label="Website (must start with http:// or https://)"
        )
        self.fields['company'].label = "Name of the Organization"
        self.fields['organization_type'].label = "Organization Type"
        self.fields['ein_number'].label = "Tax ID (EIN)"
        self.fields['address1'].label = "Street address"
        self.fields['city'].label = "City"
        self.fields['zip_code'].label = "Zip code"
        self.fields['country'].label = "Country"
        self.fields['state'].label = "State/Province"
        self.fields['phone'].label = 'Phone Number'

        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
            if self.fields[field].required:
                self.fields[field].widget.attrs['required'] = ''
        self.fields['country'].widget.attrs['class'] = 'form-control selectchain'

    def clean_ein_number(self):
        ein_number = self.cleaned_data.get('ein_number', '')

        # prevent people from entering all same digits
        if all(x == ein_number[0] for x in ein_number.replace('-', '')):
            raise ValidationError(self.INVALID_EIN_MESSAGE, code='invalid')

        if not self.EIN_PATTERN.search(ein_number):
            raise ValidationError(self.INVALID_EIN_MESSAGE, code='invalid')

        return ein_number

    class Meta:
        model = Provider
        fields = [
            "company",
            "organization_type",
            "ein_number",
            "address1",
            "address2",
            "city",
            "state",
            "country",
            "zip_code",
            "phone",
            "personal_url",
            "bio"
        ]


class ProviderLogoUploadForm(ImageUploadBaseForm):

    upload_type_code = "PROFILE_PHOTOS"

    class Meta:
        model = ImageUpload
        fields = ["image_file"]
