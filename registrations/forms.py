from django import forms
from django.core.exceptions import ValidationError

from content.forms import AddFormControlClassMixin
from .models import Attendee


class ModelChoiceField_w_LabelDictionary(forms.ModelChoiceField):
    """
    ModelChoiceField with extra kwarg "label_dict" (id keys matching to label values)
    """
    def __init__(self, *args, **kwargs):
        self.label_dict= kwargs.pop("label_dict",{})
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        return self.label_dict.get(obj.id, None) or super().label_from_instance()


class AttendeeBadgeForm(AddFormControlClassMixin, forms.ModelForm):

    badge_name = forms.CharField(
        required=True,
        label="First Name")

    badge_company = forms.CharField(
        required=False,
        label="Organization",
        )

    badge_location = forms.CharField(
        required=True,
        label="Location (City, State)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_form_control_class()

    def clean_badge_name(self):
        badge_name = self.cleaned_data.get('badge_name', None) or ''
        cleaned_badge_name = badge_name.strip()
        if not cleaned_badge_name:
            raise ValidationError("This field is required")
        if (len(cleaned_badge_name) > 14):
            raise ValidationError("Please keep your badge name to 14 characters or fewer.")
        return cleaned_badge_name

    class Meta:
        model = Attendee
        fields = ["badge_name", "badge_company", "badge_location"]

