from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.utils.safestring import mark_safe

from ..multi_method import multi, method
from ..imis.xml_parser import *


DEFAULT_CHOICE = [('', '--- Select an option ---')]


@multi
def format_field(question):
    return control_type(question['xml']) or question['type']


@method(format_field, 'Boolean')
def format_field(question):
    return forms.BooleanField(
        label=get_label(question),
        required=False)


@method(format_field, 'Decimal')
def format_field(question):
    return forms.DecimalField(
        widget=forms.NumberInput(attrs={'step': 0.25, 'decimal_places': 2}),
        label=get_label(question),
        required=False
    )


@method(format_field, 'Integer')
def format_field(question):
    return forms.IntegerField(
        label=get_label(question),
        required=False)


@method(format_field, 'String')
def format_field(question):
    return forms.CharField(
        label=get_label(question),
        required=False)


@method(format_field, 'TextField')
def format_field(question):
    xml = question['xml']
    length = max_length(xml)
    return forms.CharField(
        label=get_label(question),
        required=False,
        max_length=length,
        help_text='Must be {} characters or less'.format(length))


@method(format_field, 'TextArea')
def format_field(question):
    xml = question['xml']
    length = max_length(xml)
    return forms.CharField(
        widget=forms.Textarea,
        label=get_label(question),
        required=False,
        max_length=length,
        help_text='Must be {} characters or less'.format(length))


@method(format_field, 'DropDownList')
def format_field(question):
    xml = question['xml']
    list_choices = DEFAULT_CHOICE + choices(xml)
    return forms.ChoiceField(
        label=get_label(question),
        required=False,
        choices=list_choices)


def get_label(question):
    label = question['label']
    if required(question['xml']):
        label += ' <span class="text-lowercase text-lighter text-danger"><em>(required)</em></span>'

    return mark_safe(label)
