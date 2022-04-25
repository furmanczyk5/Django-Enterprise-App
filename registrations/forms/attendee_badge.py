from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.contrib.admin import widgets as admin_widgets

from content.forms import StateCountryModelFormMixin, AddFormControlClassMixin
from events.models import EVENT_TICKET_TEMPLATES
from myapa.models.contact import Contact
from store.models import Purchase, ProductOption
from ..models import Attendee
from imis.models import CustomEventRegistration


BADGE_PRINT_LENGTH = 14


def check_field_length(form, field, length):
    cleaned_value = form.cleaned_data.get(field, '').strip()
    value_length = len(cleaned_value)
    if (value_length > length):
        raise ValidationError(
            'Ensure this value has at most {} characters (it has {}).'.format(length, value_length)
        )
    return cleaned_value


class AttendeeBadgeForm(AddFormControlClassMixin, forms.ModelForm):

    badge_name = forms.CharField(
        required=True,
        label="Preferred Name"
    )

    badge_company = forms.CharField(
        required=False,
        label="Organization",
        help_text="Initial capitalized, e.g. American Planning Association"
    )

    badge_location = forms.CharField(
        required=True,
        label="Location (City, State)",
        help_text="City, ST; e.g. Chicago, IL"
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.add_form_control_class()

    def clean_badge_name(self):
        return check_field_length(self, 'badge_name', BADGE_PRINT_LENGTH)

    class Meta:
        model = CustomEventRegistration
        fields = ["badge_name", "badge_company", "badge_location"]


class AttendeeBadgeShippingForm(StateCountryModelFormMixin, AttendeeBadgeForm):

    address1 = forms.CharField(
        required=True,
        label="Address 1")

    address2 = forms.CharField(
        required=False,
        label="Address 2")

    city = forms.CharField(
        required=True,
        label="City")

    zip_code = forms.CharField(
        required=True,
        label="Zip/Postal Code")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_state_country_fields()
        self.add_form_control_class(fields=["address1", "address2", "city", "state", "country", "zip_code"])

    def clean_state(self):
        return self.truncate_field("state")

    def clean_country(self):
        return self.truncate_field("country")

    def truncate_field(self, field):
        field_value = self.cleaned_data.get(field, "")
        max_length = CustomEventRegistration._meta.get_field(field).max_length
        if len(field_value) > max_length:
            field_value = field_value[:max_length]

        return field_value

    class Meta:
        model = CustomEventRegistration
        fields = ["badge_name", "badge_company", "badge_location", "address1", "address2", "city", "state", "country", "zip_code"]
