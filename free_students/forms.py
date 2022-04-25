import re

from django import forms

from content.forms import StateCountryModelFormMixin
from content.widgets import YearMonthDaySelectorWidget
from myapa.utils import get_primary_chapter_code_from_zip_code

from .models import Student


class StudentForm(StateCountryModelFormMixin, forms.ModelForm):

    def __init__(self, *args, **kwargs):

        self.is_strict = kwargs.pop("is_strict", True)
        self.degree_types = kwargs.pop("degree_types", [])
        super().__init__(*args, **kwargs)

        self.init_state_country_fields(state_required=False, country_required=False)
        self.init_state_country_fields(prefix="secondary_", state_required=False, country_required=False)

        self.fields["first_name"] = forms.CharField(required=True)
        self.fields["last_name"] = forms.CharField(required=True)
        # self.fields["address1"] = forms.CharField(required=True)
        # self.fields["city"] = forms.CharField(required=True)
        # self.fields["zip_code"] = forms.CharField(required=True)
        self.fields['address1'] = forms.CharField(label="Address 1", required=True)
        self.fields['address2'] = forms.CharField(label="Address 2", required=False)

        self.fields['middle_name'] = forms.CharField(label="Middle Initial", required=False)
        self.fields['expected_graduation_date'] = forms.DateField(label="Expected Graduation Date (optional)", widget=YearMonthDaySelectorWidget(numbered_months = True, include_day=False, max_year=2025, us_notation=True), required=False)
        self.fields["degree_type"] = forms.ChoiceField(required=False, widget=forms.Select(), choices=self.degree_types)
        self.fields['phone'] = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'xxx-xxx-xxxx'}), required=False)
        self.fields["birth_date"] = forms.DateField(label="Birth Date", widget=YearMonthDaySelectorWidget(us_notation=True, numbered_months=True), required=False)
        self.fields['zip_code'] = forms.CharField(label="Zip", required=False)

        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
            if not self.fields[field].required and field not in ["address1", "city","state","zip_code","phone","email",]:
                self.fields[field].widget.attrs["placeholder"] = "Optional"

            class_attr = self.fields[field].widget.attrs.get("class", '')
            if not re.search(r'\bform-control\b', class_attr):
                self.fields[field].widget.attrs["class"] = "form-control " + class_attr

        self.fields['country'].widget.attrs['class'] = 'form-control selectchain'
        self.fields['secondary_country'].widget.attrs['class'] = 'form-control selectchain'

        self.fields["expected_graduation_date"].widget.attrs["class"] = 'form-control form-control-3-col'
        self.fields["birth_date"].widget.attrs["class"] = 'form-control form-control-3-col'

    def clean(self):

        cleaned_data = super().clean()

        if not self.is_strict:
            return cleaned_data # DON'T OD extra validation if self.is_strict is False

        # fields that need to be cleaned before submission
        address1 = self.cleaned_data.get("address1", None)
        city = self.cleaned_data.get("city", None)
        state = self.cleaned_data.get("state", None)
        country = self.cleaned_data.get("country", None)
        zip_code = self.cleaned_data.get("zip_code", None)
        phone = self.cleaned_data.get("phone", None)
        first_name = self.cleaned_data.get("first_name", None)
        last_name = self.cleaned_data.get("last_name", None)
        birth_date = self.cleaned_data.get("birth_date", None)
        email = self.cleaned_data.get("email", None)
        degree_type = self.cleaned_data.get("degree_type", None)

        if not address1:
            self.add_error("address1", "The address 1 field is required. ")

        if not city:
            self.add_error("city", "The city field is required. ")

        if not state:
            self.add_error("state", "The state field is required. ")

        if not country:
            self.add_error("country", "The country field is required. ")

        if not zip_code:
            self.add_error("zip_code", "The zip code field is required. ")

        if not phone:
            self.add_error("phone", "The phone field is required. ")

        if not first_name:
            self.add_error("first_name", "The first name field is required. ")

        if not last_name:
            self.add_error("last_name", "The last name field is required. ")

        if not birth_date:
            self.add_error("birth_date", "The birth date field is required. ")

        if not email:
            self.add_error("email", "The email field is required")

        if not degree_type:
            self.add_error("degree_type", "The degree type field is required")

        if country == 'United States' and (len(phone) != 12 or phone[3] != '-' or phone[7] != '-'):
            self.add_error("phone", "The phone number must be in the format xxx-xxx-xxxx. ")

        chapter = get_primary_chapter_code_from_zip_code(zip_code)

        if not chapter and country == 'United States':
            self.add_error("zip_code",
                """A valid chapter could not be found with the zip code entered.
                Please verify the zip code is 5 digits only and try again.
                If you continue to experience issues please contact APA at customerservice@planning.org. """
                )

        return cleaned_data

    class Meta:
        model = Student
        fields = ["school","first_name","middle_name","last_name","expected_graduation_date","degree_type","email","phone","secondary_address1","secondary_address2","secondary_city","secondary_state","secondary_zip_code","secondary_country","secondary_phone","secondary_email","address1","address2","city","state","zip_code","country","student_id","birth_date",]
        labels = dict(middle_name="Middle Initial", secondary_address1="Address 1", secondary_address2="Address 2",
            secondary_city="City", secondary_state="State/Province", secondary_zip_code="Zip", secondary_country="Country", state="State/Province",)


class StudentAdminForm(StateCountryModelFormMixin, forms.ModelForm):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.init_state_country_fields(state_required=False, country_required=False)
        self.fields['country'].widget.attrs['class'] = 'form-control selectchain'

    class Meta:
        model = Student
        fields = ["contact","school","first_name","middle_name","last_name","expected_graduation_date","degree_type","email","phone","secondary_address1","secondary_address2","secondary_city","secondary_state","secondary_zip_code","secondary_country","secondary_phone","secondary_email","address1","address2","city","state","zip_code","country","student_id","birth_date","uploaded_on","registration_period","registration_year"]
