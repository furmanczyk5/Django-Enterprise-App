from django import forms

from content.forms import AddFormControlClassMixin
from myapa.models.contact import Contact
from myapa.models.educational_degree import EducationalDegree
from .account import BaseCreateAccountForm, AddressesFormMixin, DemographicsForm
from .join import StudentJoinEnhanceMembershipForm, \
    StudentJoinSchoolInformationForm


class OptionallyRequiredFieldsMixin(object):
    """ will make fields required False if is_strict is False"""

    always_required = []  # list of fields to always require

    def __init__(self, *args, **kwargs):
        self.is_strict = kwargs.pop('is_strict', True)
        super().__init__(*args, **kwargs)

    def optionally_require_fields(self):

        for field_name in self.fields:
            if field_name not in self.always_required:
                field = self.fields[field_name]
                if not field.required:
                    field.widget.attrs.update({"placeholder": "Optional"})
                if not self.is_strict:
                    field.required = False


class FreeStudentAdminAccountForm(AddFormControlClassMixin, OptionallyRequiredFieldsMixin, AddressesFormMixin,
                                  BaseCreateAccountForm):
    always_required = ["first_name", "last_name", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_address_fields()
        self.fields["secondary_email"].label = "Secondary Email"
        self.optionally_require_fields()
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
        fields = ["prefix_name", "first_name", "middle_name", "last_name", "suffix_name", "email", \
                  "secondary_email", "phone", "secondary_phone", "cell_phone", "birth_date", "user_address_num",
                  "address1", "address2", "country", "state", "city", "zip_code", "company"]


class FreeStudentAdminDemographicsForm(AddFormControlClassMixin, OptionallyRequiredFieldsMixin, DemographicsForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.optionally_require_fields()
        self.add_form_control_class()


class FreeStudentAdminSchoolInformationForm(OptionallyRequiredFieldsMixin, StudentJoinSchoolInformationForm):
    verify = None
    hide_school = True

    school = forms.ChoiceField(
        label="School",
        required=True,
        choices=[("OTHER", "Other")],
        widget=forms.HiddenInput())

    other_school = forms.CharField(
        label="Other school if yours is not listed above",
        required=False,
        widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["degree_program"].required = True
        self.optionally_require_fields()

    class Meta:
        model = EducationalDegree
        fields = ["other_school", "level", "level_other", "graduation_date", "student_id"]


class FreeStudentAdminEnhanceMembershipForm(OptionallyRequiredFieldsMixin, StudentJoinEnhanceMembershipForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.optionally_require_fields()

    def save(self, user=None):
        """ user instance may not be defined until the form is being saved 
                so we are allowing to pass user into save method """
        if not self.user:
            self.user = user
            self.contact = user.contact
        return super().save()
