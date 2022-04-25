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


class ModelChoiceField_w_LabelDictionary(forms.ModelChoiceField):
    """
    ModelChoiceField with extra kwarg "label_dict" (id keys matching to label values)
    """
    def __init__(self, *args, **kwargs):
        self.label_dict= kwargs.pop("label_dict",{})
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        return self.label_dict.get(obj.id, None) or super().label_from_instance()
