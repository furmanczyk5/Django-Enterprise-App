import datetime
import re

import pytz
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms.fields import DateTimeField
from django.utils import timezone

from ui.utils import get_selectable_options_tuple_list
from .models import Content, EmailTemplate, MessageText, \
    ContentTagType, Tag, JurisdictionContentTagType, \
    CommunityTypeContentTagType, ContentRelationship
from .widgets import SelectFacade

DESCRIPTION_NOT_REQUIRED = [
    'Submission', 'SubmissionCategory',
    'Job', 'WagtailJob',
    'Exam', 'ApplicationCategory', 'ApplicationCategory',
    'BaseContent', 'ContentImage', 'MenuItem', 'EmailTemplate', 'MessageText',
    'LineItem', 'Purchase', 'Payment', 'ProductPrice', 'ProductOption', 'Product', 'ProductEvent',
    'Event', 'Activity', 'EventSingle', 'EventMulti', 'Course',
    'Image', 'Inquiry'
    ]


class StateCountryModelFormMixin(object):
    """
    Model Form mixin that defines a method to initialize country and state select chain fields
    This uses the select facade widget
    """

    def init_state_country_fields(self, **kwargs):

        prefix = kwargs.get("prefix", "")
        state_required = kwargs.get("state_required", True)
        country_required = kwargs.get("country_required", True)

        form_prefix = self.prefix or ""
        if form_prefix:
            combo_prefix = form_prefix + "-" + prefix
        else:
            combo_prefix = prefix

        country = self.data.get("%scountry" % combo_prefix, None) \
                  or self.initial.get("%scountry" % prefix, None)

        # Leave everything blank if user is joining or updating MyAPA
        # Don't want to create additional addresses of just a country of "United States"
        if country is None:
            if prefix == "additional_":
                country = ""
            else:
                country = "United States"

        state_options = get_selectable_options_tuple_list(mode="region_from_country", value=country)

        self.fields['%sstate' % prefix] = forms.ChoiceField(
            widget=SelectFacade(
                use_required_attribute=False,
                facade_attrs={"data-empty-text": "Select a State/Region"},
                attrs={"id": "%ssubmission-state-select" % combo_prefix}
            ),
            choices=[("", "")] + state_options,
            required=bool(state_options and state_required)
        )

        self.fields['%scountry' % prefix] = forms.ChoiceField(
            widget=SelectFacade(
                facade_attrs={"data-empty-text": "Select a Country"},
                attrs={
                    "class": "selectchain",
                    "data-selectchain-mode": "region_from_country",
                    "data-selectchain-target": "#%ssubmission-state-select" % combo_prefix
                }
            ),
            choices=[("", "")] + get_selectable_options_tuple_list(mode="country"),
            required=country_required,
            initial=country
        )


class AddFormControlClassMixin(object):

    def add_form_control_class(self, fields=None):
        """
        adds the form-control class to all initialized fields in the form
        """
        _fields = set(self.fields) & set(fields) if fields else self.fields
        for field in _fields:
            class_attr = self.fields[field].widget.attrs.get("class", '')
            if not re.search(r'\bform-control\b', class_attr):
                self.fields[field].widget.attrs["class"] = "form-control " + class_attr


class MessageTextAdminForm(forms.ModelForm):

    class Meta:
        model = MessageText
        exclude = []
        widgets = {
            "text": forms.Textarea(attrs={"class": "ckeditor"})
        }


class ContentAdminForm(forms.ModelForm):

    model_instance = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_instance = kwargs.get('instance', None)

        desc_req = True
        if str(self.Meta.model.__name__) in DESCRIPTION_NOT_REQUIRED:
            desc_req = False

        self.fields["description"] = forms.CharField(
            min_length=1, max_length=400, required=desc_req, widget=forms.Textarea,
            help_text="""A brief description of the content (phrase or 1-2 short sentences).
        For searchable content, this will display in the search results list.""")

        if 'text' in self.fields:
            self.fields['text'].widget.attrs.update({'id': 'ckeditor_admin'})

    def clean(self):
        cleaned_data = super().clean()

        if not self.model_instance:
            content_code = cleaned_data.get('code', None)

            if content_code and Content.objects.filter(code=content_code).exists():
                self.add_error(
                    "code",
                    "Error: Attempt to create new Content record with code that already exists: %s" % content_code
                )

        return cleaned_data

    class Meta:
        model = Content
        exclude = []
        widgets = {
            "text": forms.Textarea(attrs={"class": "ckeditor"})
        }


class ContentAdminEditorForm(ContentAdminForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.fields.get("workflow_status", None):
            self.fields["workflow_status"].choices = (
                    ('DRAFT_IN_PROGRESS', 'Draft in progress'),
                    ('NEEDS_REVIEW', 'Needs review'),
                    ('NEEDS_WORK', 'Needs work'),
                    ('APPROVED_TO_PUBLISH', 'Approved to publish'),
                    ('IS_PUBLISHED', 'Published'),
                    ('UNPUBLISHED', 'Unpublished'),
                )


class ContentAdminAuthorForm(ContentAdminForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.fields.get("workflow_status", None):
            self.fields["workflow_status"].choices = (
                ('DRAFT_IN_PROGRESS', 'Draft in progress'),
                ('NEEDS_REVIEW', 'Needs review'),
                        #('NEEDS_WORK','Needs work'),
                        #('APPROVED_TO_PUBLISH','Approved to publish'),
                        # ('IS_PUBLISHED', 'Published'),
                        # ('UNPUBLISHED', 'Unpublished'),
                    )


class EmailTemplateAdminForm(forms.ModelForm):

    class Meta:
        model = EmailTemplate
        exclude = []
        widgets = {
            "body": forms.Textarea(attrs={"class": "ckeditor"})
        }


class JurisdictionContentTagTypeAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tags'].queryset = Tag.objects.filter(tag_type__code="JURISDICTION")

    class Meta:
        model = JurisdictionContentTagType
        # fields=[]
        exclude = ["tag_type", "published_time", "publish_time", "published_by", "publish_status", "publish_uuid"]


class CommunityTypeContentTagTypeAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tags'].queryset = Tag.objects.filter(tag_type__code="COMMUNITY_TYPE")

    class Meta:
        model = CommunityTypeContentTagType
        # fields=[]
        exclude = ["tag_type", "published_time", "publish_time", "published_by", "publish_status", "publish_uuid"]


class SearchTopicTypeContentTagTypeAdminForm(forms.ModelForm):
    class Meta:
        model = ContentTagType
        exclude = [
            "published_time", "publish_time", "published_by",
            "publish_status", "publish_uuid"
        ]


class ContentTagTypeAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'instance' in kwargs:
            instance = kwargs['instance']
            self.fields['tags'].queryset = Tag.objects.filter(tag_type=instance.tag_type)
        else:
            self.fields['tags'].queryset = Tag.objects.none()

    class Meta:
        model = ContentTagType
        # fields=[]
        exclude = ["published_time", "publish_time", "published_by", "publish_status", "publish_uuid"]


class SearchFilterForm(forms.Form):
    """
    Form for filtering search results
    NOTE:facets not included!
    """

    keyword = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "keyword", "class": "form-control"}),
        required=False,
        initial="*"
    )

    sort_choices = (
        ("relevance", "Relevance"),
        ("sort_time desc", "Date (newest)"),
        ("title_string asc", "Title (A to Z)"),
        ("title_string desc", "Title (Z to A)")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.query_params = args[0].copy()
        self.data = self.query_params
        self.query_params["keyword"] = self.query_params.get("keyword", None) or ""

        # this will always be last!
        self.fields["sort"] = forms.ChoiceField(
            widget=SelectFacade(facade_attrs={"class": "goooold"}, pretext="Sort By: "),
            choices=self.sort_choices,
            required=False
        )

    # TO DO: remove/refactor this??
    def to_query_list(self):

        output = []
        query_map = self.get_query_map()
        for key, field in self.fields.items():

            query_param = self.query_params.get(key, None)
            query_map_format_string = query_map.get(key, None)

            if query_param and key in query_map:
                query_args = [query_param]
                output.append( query_map_format_string.format(*query_args) )

        return output

    def get_query_map(self):
        return {}

    def get_sort(self):
        sort_field = self.query_params.get("sort", None)

        if not sort_field or sort_field == "relevance":
            self.query_params["sort"] = "relevance"
            self.data["sort"] = None

        return self.data.get("sort", None)


class SearchFilterFormKeywordless(SearchFilterForm):
    """
    Same as Search Filter Form but with keywordField hidden
    """
    keyword = forms.CharField(widget=forms.HiddenInput(), required=False, initial="*")


class DateTimeTimezoneField(DateTimeField):

    def __init__(self, *args, **kwargs):
        self.timezone_str = kwargs.pop("timezone_str")
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        if isinstance(value, datetime.datetime):
            value = self.to_timezone(value)
        return value

    def to_python(self, value):
        """
        Validates that the input can be converted to a datetime. Returns a
        Python datetime.datetime object.
        """
        if value in self.empty_values:
            return None
        if isinstance(value, datetime.datetime):
            return self.from_timezone(value)
        if isinstance(value, datetime.date):
            result = datetime.datetime(value.year, value.month, value.day)
            return self.from_timezone(result)
        if isinstance(value, list):
            # Input comes from a SplitDateTimeWidget, for example. So, it's two
            # components: date and time.

            # warnings.warn(
            #     'Using SplitDateTimeWidget with DateTimeField is deprecated. '
            #     'Use SplitDateTimeField instead.',
            #    RemovedInDjango19Warning, stacklevel=2)
            if len(value) != 2:
                raise ValidationError(self.error_messages['invalid'], code='invalid')
            if value[0] in self.empty_values and value[1] in self.empty_values:
                return None
            value = '%s %s' % tuple(value)
        result = super(DateTimeField, self).to_python(value)
        return self.from_timezone(result)

    def from_timezone(self, value):
        if settings.USE_TZ and value is not None and timezone.is_naive(value):
            try:
                the_timezone = pytz.timezone(self.timezone_str)
            except:
                the_timezone = None
            try:
                return timezone.make_aware(value, the_timezone)
            except Exception:
                message = _(
                    '%(datetime)s couldn\'t be interpreted '
                    'in time zone %(the_timezone)s; it '
                    'may be ambiguous or it may not exist.'
                )
                params = {'datetime': value, 'current_timezone': the_timezone}
                six.reraise(ValidationError, ValidationError(
                    message,
                    code='ambiguous_timezone',
                    params=params,
                ), sys.exc_info()[2])
        return value

    def to_timezone(self, value):
        """
        When time zone support is enabled, convert aware datetimes
        to naive datetimes in the current time zone for display.
        """
        if settings.USE_TZ and value is not None and timezone.is_aware(value):
            the_timezone = pytz.timezone(self.timezone_str)
            return timezone.make_naive(value, the_timezone)
        return value


class CollectionRelationshipAdminInlineForm(forms.ModelForm):

    def save(self, commit=True):
        contentrelationship = super().save(commit=False)
        contentrelationship.relationship = "KNOWLEDGEBASE_COLLECTION"
        if commit:
            contentrelationship.save()
        return contentrelationship

    class Meta:
        model = ContentRelationship
        fields = ["content_master_related"]
