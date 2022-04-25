from django import forms
from django.core.validators import RegexValidator
from hcaptcha.fields import hCaptchaField

from content.widgets import SelectFacade
from content.forms import AddFormControlClassMixin
from .models import Ticket, TICKET_CATEGORIES


class ContactUsForm(AddFormControlClassMixin, forms.ModelForm):

    apa_id = forms.CharField(label="APA ID number", required=False,
                             widget=forms.TextInput(attrs={"placeholder":"Optional"}),
                             validators=[RegexValidator(r'^\d{6}$', message="Enter a valid six digit APA ID")])
    full_name = forms.CharField(label="Full Name", required=True)
    email = forms.CharField(label="Email", required=True)
    phone = forms.CharField(label="Phone", required=False,
                            widget=forms.TextInput(attrs={"placeholder":"Optional"}))

    category_choices = [(None, "")]
    category_choices.extend(sorted(TICKET_CATEGORIES, key=lambda x: x[1]))

    category = forms.ChoiceField(label="Category/Topic",
                                 required=True,
                                 choices=category_choices,
                                 widget=SelectFacade(facade_attrs={
                                     "data-empty-text": "Please Select A Topic"
                                 }))
    title = forms.CharField(label="Subject", required=True,
                            widget=forms.TextInput(attrs={"class":"full-width"}))
    description = forms.CharField(label="Your question or comment", required=True,
                                  widget=forms.Textarea(attrs={"class": "full-width"}))
    hcaptcha = hCaptchaField()


    def clean_title(self):
        title = self.cleaned_data['title']
        if len(title) > 100:
            raise forms.ValidationError("Your subject must be less than 100 characters")
        return title

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["contact"].required = False
        self.fields["created_by"].required = False
        self.fields["contact"].widget = forms.HiddenInput()
        self.fields["created_by"].widget = forms.HiddenInput()

        self.add_form_control_class()

    class Meta:
        model = Ticket
        fields = ["apa_id", "full_name", "email", "phone", "category", "title", "description", "contact", "created_by", "hcaptcha"] # I think we need the actual question or comment
