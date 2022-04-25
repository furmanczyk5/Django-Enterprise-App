import datetime
import re

import pytz
from django import forms
from django.contrib.admin import widgets
from django.utils.safestring import mark_safe
from django.utils import timezone

from content.forms import StateCountryModelFormMixin, AddFormControlClassMixin, \
    SearchFilterForm, SearchFilterFormKeywordless, DateTimeTimezoneField, \
    ContentAdminAuthorForm, ContentAdminEditorForm
from content.models import TagType, ContentTagType
from content.models.settings import TARGETED_CREDITS_TOPICS
from content.widgets import SelectFacade, DatetimeFacade
from events.models import Event, EventSingle, EventMulti, \
    Activity, Course, Speaker, EventInfo
from myapa.models.contact_role import ContactRole
from submissions.forms import SubmissionBaseForm, SubmissionVerificationForm
from ui.utils import get_selectable_options_tuple_list

RATING_CHOICES = ((None, "--"), (1, 1), (2, 2), (3, 3), (4, 4))


class HorizontalRadioSelect(forms.RadioSelect):
    template_name = 'content/newtheme/widgets/horizontal_select.html'

class EventSubmissionBaseForm(StateCountryModelFormMixin, SubmissionBaseForm):
    """
    Form for creating or updating events, includes fields that are used for every EventType
    """

    event_type = "EVENT_SINGLE"
    submission_category_code = "EVENT"
    tag_type_choices = [
        {
            "code": "SEARCH_TOPIC",
            "required": True,
            "field": forms.MultipleChoiceField,
            "max_tags": 3
        }
    ]
    format_tag = "FORMAT_LIVE_IN_PERSON_EVENT" # default
    default_publish_status = "DRAFT" # CM Providers should be editing draft copies (changed 7/18/2017)

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['title'] = forms.CharField(required=True, label="Event Title")
        self.fields['text'] = forms.CharField(
            required=self.is_strict,
            label="General Description",
            widget=forms.Textarea()
        )

        # contact fields
        self.fields["contact_firstname"] = forms.CharField(label="Contact First Name", required=self.is_strict, max_length=20)
        self.fields["contact_lastname"] = forms.CharField(label="Contact Last Name", required=self.is_strict, max_length=20)
        self.fields["contact_email"] = forms.CharField(label="Contact Email", required=self.is_strict, max_length=1000)

        self.add_form_control_class()

    def init_begin_end_time_fields(self):

        if self.data and "timezone" in self.fields: # when submitting data
            initial_timezone = self.data.get("timezone", "US/Central")
        elif self.instance and getattr(self.instance, "timezone", None): # when viewing existing data
            initial_timezone = getattr(self.instance, "timezone")
        else: # when new
            initial_timezone = self.initial.get("timezone", "US/Central")

        if "timezone" in self.fields:
            self.fields["timezone"] = forms.ChoiceField(
                label="TIME ZONE WHERE EVENT WILL OCCUR",
                required=self.is_strict,
                choices=[(tz, tz) for tz in pytz.all_timezones],
                initial="US/Central",
                widget=forms.Select(attrs={"class": "form-control"})
            )

        self.fields['begin_time'] = DateTimeTimezoneField(
            required=True,
            label="Start",
            widget=forms.TextInput(attrs={"class": "planning-datetime-widget form-control"}),
            timezone_str=initial_timezone
        )

        self.fields['end_time'] = DateTimeTimezoneField(
            required=True,
            label="End",
            widget=forms.TextInput(attrs={"class": "planning-datetime-widget form-control"}),
            timezone_str=initial_timezone
        )

    def init_cm_fields(self):
        credit_number_choices = [
            ("0.00", 0.0)] + [("%.2f" % float(x/4), x/4) for x in list(range(1, 401))
        ]

        credit_number_law_ethics_choices = [
            ("0.00", 0.0)] + [("%.2f" % float(x/4), x/4) for x in list(range(1, 7))
        ]

        self.fields['cm_approved'] = forms.ChoiceField(choices=credit_number_choices, initial=0.0, label="CM Credits")

        self.fields['cm_law_approved'] = forms.ChoiceField(
            choices=credit_number_law_ethics_choices,
            initial=0.0,
            label="CM Law Credits",
#             help_text="""Providers must demonstrate that the content of the activity is related to
#             planning law, such as environmental law, land use law, redevelopment law, administrative law,
# housing law, etc. Activities entered for law credit must be closely related to recently enacted planning
#             laws or recent case decisions or trends in existing planning laws or case decisions. Recent is defined as
#             within the last 10-years.  Activities related to political movements, policy recommendations, and policy initiatives
#             are not eligible for law credit. Training on law must constitute a majority of the content of the activity.""",
            help_text="""CM Law –  Planning practices are dependent upon local legislation and regulatory processes, which change frequently. The law mandatory credit topic ensures planners have a current understanding of case law, regulations, and statutes and their impact on planning practice.  To view full criteria details, click here: <a href='https://www.planning.org/cm/credits/'>Certification Maintenance Credits.</a>"""
        )

        self.fields['cm_ethics_approved'] = forms.ChoiceField(
            choices=credit_number_law_ethics_choices,
            initial=0.0,
            label="CM Ethics Credits",
            # help_text="""For ethics requirement: Providers must demonstrate that the content of the activity
            # focuses on training planners on the standards of ethical behavior according to the AICP Code of Ethics and Professional Conduct.
            # While general ethics courses, local ethics laws, and ethic codes from other professions can introduce relevant issues as well,
            # the AICP Code focuses on a system of moral principles specific to professional planners.""",
            help_text="""CM Ethics – AICP-certified planners pledge to uphold high standards of ethics and professional conduct. The ethics mandatory credit topic ensures that planners maintain an understanding of how the AICP Code of Ethics applies to evolving circumstances and trends in the practice of planning. To view full criteria details, click here: <a href='https://www.planning.org/cm/credits/'>Certification Maintenance Credits.</a>"""
        )

        self.fields['cm_equity_credits'] = forms.ChoiceField(
            choices = [("0.00", 0.0), ("1.00", 1.0)],
            initial=0.0,
            label="CM Equity Credits",
            help_text="""CM Equity – Planners have a special responsibility to serve the public interest, expand choice and opportunity for all persons, and to plan for the needs of the disadvantaged, as asserted in the AICP Code of Ethics and Professional Conduct. The equity mandatory credit provides the opportunity for planners to expand their equity toolkit, leading to more equitable outcomes in communities. To view full criteria details, click here: <a href='https://www.planning.org/cm/credits/'>Certification Maintenance Credits.</a>"""
        )

        self.fields['cm_targeted_credits'] = forms.ChoiceField(
            choices = [("0.00", 0.0), ("1.00", 1.0)],
            initial=0.0,
            label="CM Targeted Credits"
            # help_text="""CM Sustainability & Resilience - Planners must pay special attention to the long-term and interrelated consequences of their actions. Planning actions may have potentially detrimental long-term consequences, especially on their most vulnerable people, places, and systems. The sustainability and resilience credit will help planners better plan for sustainable and resilient outcomes.  To view full criteria details, click here: <a href='https://www.planning.org/cm/credits/'>Certification Maintenance Credits.</a>"""
        )

        self.fields['cm_targeted_credits_topic'] = forms.ChoiceField(
            choices = [(None, "None selected")] + list(TARGETED_CREDITS_TOPICS),
            initial="Sustainability & Resilience",
            label="CM Targeted Credits Topic",
            help_text="""CM Sustainability & Resilience - Planners must pay special attention to the long-term and interrelated consequences of their actions. Planning actions may have potentially detrimental long-term consequences, especially on their most vulnerable people, places, and systems. The sustainability and resilience credit will help planners better plan for sustainable and resilient outcomes.  To view full criteria details, click here: <a href='https://www.planning.org/cm/credits/'>Certification Maintenance Credits.</a>""",
            required=False
        )

        self.fields['cm_approved'].widget.attrs['class'] = 'form-control'
        self.fields['cm_law_approved'].widget.attrs['class'] = 'form-control'
        self.fields['cm_ethics_approved'].widget.attrs['class'] = 'form-control'
        self.fields['cm_equity_credits'].widget.attrs['class'] = 'form-control'
        self.fields['cm_targeted_credits'].widget.attrs['class'] = 'form-control'
        self.fields['cm_targeted_credits_topic'].widget.attrs['class'] = 'form-control'

    def clean_cm_approved(self):
        cm_approved = float(self.cleaned_data.get('cm_approved') or 0.0)
        # using data instead of cleaned_data for law and ethics because those fields have not been cleaned yet
        cm_ethics_approved = float(self.data.get('cm_ethics_approved') or 0.0)
        cm_law_approved = float(self.data.get('cm_law_approved') or 0.0)
        cm_equity_credits = float(self.data.get('cm_equity_credits') or 0.0)
        cm_targeted_credits = float(self.data.get('cm_targeted_credits') or 0.0)
        cm_targeted_credits_topic = self.data.get('cm_targeted_credits_topic') or None

        # FLAGGED FOR REFACTORING: CM PROVIDER CHANGES
        # TEMPORARY LOGIC... MAKE NEW [0,1] RULES PERMANENT ON JAN 1 2022 AND REMOVE LOGIC RELATED TO 1/1/2022
        begin_time = self.data.get('begin_time') or None

        if type(begin_time) == str:
            date_str = begin_time.split(' ')[0] if begin_time else ""
            date_time_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        elif type(begin_time) == datetime.datetime:
            date_time_obj = begin_time
        else:
            date_time_obj = None

        # TEMPORARY LOGIC
        begin_date = datetime.datetime.date(date_time_obj) if date_time_obj else None
        a_date = datetime.datetime.date(timezone.now())
        jan_01_2022 = a_date.replace(year=2022, month=1, day=1)

        if begin_date and begin_date >= jan_01_2022:
            if (cm_ethics_approved not in [0, 1]):
                self.add_error("cm_ethics_approved", "Starting January 2022, Ethics credits must be either 0.0 or 1.0")
            if (cm_law_approved not in [0, 1]):
                self.add_error("cm_law_approved", "Starting January 2022, Law credits must be either 0.0 or 1.0")
            if cm_targeted_credits_topic and not cm_targeted_credits:
                self.add_error("cm_targeted_credits",
                    "If you select a targeted credits topic, you must also select a credit amount "
                    "of 1.0 CM targeted credit hours for the event.")
            if cm_targeted_credits and not cm_targeted_credits_topic:
                self.add_error("cm_targeted_credits_topic",
                    "If you select 1.0 CM targeted credit hours, you must also select a targeted credits topic "
                    "for the event.")

        if begin_date and begin_date < jan_01_2022:
            if cm_equity_credits > 0:
                self.add_error("cm_equity_credits", "Before January 2022, Equity credits cannot be added.")
            if cm_targeted_credits > 0:
                self.add_error("cm_targeted_credits", "Before January 2022, Targeted credits cannot be added.")
            if cm_targeted_credits_topic:
                self.add_error("cm_targeted_credits_topic", "Before January 2022, Targeted credit topics cannot be added.")

        # PERMANENT NEW LOGIC
        if any(cm_approved < x for x in [cm_ethics_approved, cm_law_approved, cm_equity_credits, cm_targeted_credits]):
            self.add_error("cm_approved",
                "You cannot create an event with less general CM credit(s) than the total CM credits "
                "selected for any mandatory topic."
            )

        if (cm_law_approved or cm_ethics_approved or cm_equity_credits or cm_targeted_credits) and not cm_approved:
            raise forms.ValidationError(
                "If you select to add CM credits for law, ethics, equity or targeted, you must first select to "
                "add CM credits for the overall event."
            )

        return cm_approved  #cm_approved value

    def clean_tag_choice_SEARCH_TOPIC(self):
        # Might be better to build into the 'init_tag_choice_fields' method?
        tags = self.cleaned_data.get("tag_choice_SEARCH_TOPIC", "")
        tags_count = len(tags)
        try:
            max_tags = self.tag_type_choices[0].get('max_tags', 3)
        except (IndexError, TypeError):
            max_tags = 3
        if tags_count > max_tags and self.is_strict:
            raise forms.ValidationError(
                "You cannot select more than {} topic tags. You have chosen {}".format(
                    max_tags, tags_count
                )
            )
        return tags

    def presave(self):
        self.instance.event_type = self.event_type

    def save(self, *args, **kwargs):

        content = super().save(*args, **kwargs)
        format_tagtype = TagType.objects.prefetch_related("tags").get(code="FORMAT")

        if self.format_tag and not ContentTagType.objects.filter(
            content=content,
            tag_type=format_tagtype,
            tags__code=self.format_tag
        ).exists():
            format_contenttagtype, _ = ContentTagType.objects.get_or_create(
                content=content,
                tag_type=format_tagtype
            )
            format_contenttagtype.tags.add(*[t for t in format_tagtype.tags.all() if t.code == self.format_tag])

        return content

    def get_save_status(self):
        """ Newly created events get status 'N'
                editing existing events does not change status """
        return self.instance.status if self.instance and self.instance.pk else "N"

    class Meta:
        model = Event
        fields = ["title", "text"]


class EventSubmissionVerificationForm(SubmissionVerificationForm):

    submission_verified = forms.BooleanField(label="Verify Entry", widget=forms.CheckboxInput(), required=True, initial=False,
        help_text="""Criteria for CM Event: Please ensure that you have read and understand the following content, delivery and administrative criteria.
        Criteria for the content of CM activities: Activities must (a) meet a planning-related objective, (b) be unbiased and non-promotional
        and (c) communicate a clearly identified educational purpose or objective. Criteria for the delivery of CM activities:
        Activities must (a) be led by one or more experts on the subject matter discussed, (b) use learning methodologies and formats
        that are appropriate to the activity's educational purpose, (c) involve the use of materials that do not include proprietary information,
        (d) be timed in a manner consistent with the time for which the activity was registered for CM credit and that only the portion of the activity
        meeting CM criteria is entered for CM credit. Criteria for the administration of CM activities: Activities must
        (a) use mechanisms to record attendance and evaluate the content, (b) have a point of contact that is responsible for the proper
        administration of the CM activity. I have read and understood the above, and agree that the event I am entering meets the CM criteria.""")


class EventMultiForm(EventSubmissionBaseForm):
    """
    Form for creating or updating multi events
    """

    event_type = "EVENT_MULTI"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.init_state_country_fields(state_required=self.is_strict, country_required=self.is_strict)

        self.fields['city'] = forms.CharField(required=self.is_strict)
        self.fields['resource_url'] = forms.URLField(
            required=False,
            widget=forms.TextInput(attrs={'placeholder': 'Optional'})
        )
        self.fields['resource_url'].label = "Resource URL (must start with http:// or https://)"
        self.fields["is_free"].label = "This Event is Free"

        self.add_form_control_class()
        self.init_begin_end_time_fields()

    class Meta:
        model = EventMulti
        fields = EventSubmissionBaseForm.Meta.fields + ["begin_time", "end_time", "timezone", "city", "state", "country", "is_free", "resource_url"]


class EventSingleForm(EventSubmissionBaseForm):
    """
    Form for creating or updating single events
    """

    event_type = "EVENT_SINGLE"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.init_state_country_fields(state_required=self.is_strict, country_required=self.is_strict)
        self.init_cm_fields()

        self.fields['city'] = forms.CharField(required=self.is_strict)
        self.fields['resource_url'] = forms.URLField(
            required=False,
            widget=forms.TextInput(attrs={'placeholder': 'Optional'})
        )
        self.fields['resource_url'].label = "Resource URL (must start with http:// or https://)"

        self.fields["is_free"].label = "This Event is Free"

        self.add_form_control_class()
        self.init_begin_end_time_fields()

    class Meta:
        model = EventSingle
        fields = EventSubmissionBaseForm.Meta.fields + [
            "begin_time",
            "end_time",
            "timezone",
            "cm_approved",
            "city",
            "state",
            "country",
            "is_free",
            "resource_url",
            "cm_law_approved",
            "cm_ethics_approved",
            "cm_equity_credits",
            "cm_targeted_credits",
            "cm_targeted_credits_topic"
        ]

class EventSingleOnlineForm(EventSubmissionBaseForm):
    """
    Form for creating or updating single event - live online
    """
    event_type = "EVENT_SINGLE"
    format_tag = "FORMAT_LIVE_ONLINE_EVENT"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.init_cm_fields()

        self.fields['resource_url'] = forms.URLField(
            required=False,
            widget=forms.TextInput(attrs={'placeholder': 'Optional'})
        )
        self.fields['resource_url'].label = "Resource URL (must start with http:// or https://)"
        self.fields["is_free"].label = "This Event is Free"

        self.add_form_control_class()
        self.init_begin_end_time_fields()

    def presave(self):
        self.instance.is_online = True
        super().presave()

    class Meta:
        model = EventSingle
        fields = EventSubmissionBaseForm.Meta.fields + [
        "begin_time", "end_time", "timezone", "cm_approved", "is_free", "resource_url", "cm_law_approved", "cm_ethics_approved",
        "cm_equity_credits", "cm_targeted_credits", "cm_targeted_credits_topic"
        ]


class EventActivityForm(EventSubmissionBaseForm):
    """
    Form for creating or updating Activities that belong to events events
    """

    event_type = "ACTIVITY"

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.init_cm_fields()
        self.add_form_control_class()
        self.init_begin_end_time_fields()
        self.fields['parent'].widget = forms.HiddenInput()

    class Meta:
        model = Activity
        fields = EventSubmissionBaseForm.Meta.fields + [
        "begin_time", "end_time", "timezone", "cm_approved", "cm_law_approved", "cm_ethics_approved", "parent",
        "cm_equity_credits", "cm_targeted_credits", "cm_targeted_credits_topic"]


class EventCourseForm(EventSubmissionBaseForm):
    """
    Form for creating or updating distance learning / courses
    """

    event_type = "COURSE"
    format_tag = "FORMAT_ON_DEMAND_EDUCATION"

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.init_cm_fields()

        self.fields['resource_url'] = forms.URLField(
            required=False,
            widget=forms.TextInput(attrs={'placeholder': 'Optional'})
        )
        self.fields['resource_url'].label = "Resource URL (must start with http:// or https://)"
        self.fields["is_free"].label = "This Course is Free"

        self.add_form_control_class()
        self.init_begin_end_time_fields() # NEED OTHER BEGIN + END TIME WIDGET (SELECT PERIOD AVAILABLE)
        self.fields['begin_time'].widget.attrs["data-show-time"] = "false"
        self.fields['end_time'].widget.attrs["data-show-time"] = "false"

    class Meta:
        model = Course
        fields = EventSubmissionBaseForm.Meta.fields + [
        "begin_time", "end_time", "cm_approved", "is_free", "resource_url", "cm_law_approved", "cm_ethics_approved",
        "cm_equity_credits", "cm_targeted_credits", "cm_targeted_credits_topic"]


class EventInfoForm(EventSubmissionBaseForm):
    """
    Form for creating or updating single events
    """

    event_type = "EVENT_INFO"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.init_state_country_fields(state_required=self.is_strict, country_required=self.is_strict)
        # self.init_cm_fields()

        self.fields['city'] = forms.CharField(required=self.is_strict)
        self.fields['resource_url'] = forms.URLField(
            required=False,
            widget=forms.TextInput(attrs={'placeholder': 'Optional'})
        )
        self.fields['resource_url'].label = "Resource URL (must start with http:// or https://)"
        self.fields["is_free"].label = "This Event is Free"

        self.fields["country"].required = False
        self.fields["state"].required = False
        self.fields["city"].required = False

        self.add_form_control_class()
        self.init_begin_end_time_fields()

    class Meta:
        model = EventInfo
        fields = EventSubmissionBaseForm.Meta.fields + ["begin_time", "end_time", "timezone", "city", "state", "country", "is_free", "resource_url"]


class SpeakerForm(forms.ModelForm):

    id = forms.CharField(required=False, widget=forms.HiddenInput())
    default_publish_status = "DRAFT"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        has_contact = self.has_contact()
        self.init_fields_required(has_contact)
        self.fields["contact"].widget = widget=forms.HiddenInput()
        self.fields["content"].widget = widget=forms.HiddenInput()
        self.add_form_control_class()

    def save(self, commit=True):
        contactrole = super().save(commit=False)
        contactrole.publish_status = self.default_publish_status # CM Providers should be editing draft copies (changed 7/18/2017)
        if commit:
            contactrole.save()
        return contactrole

    def init_fields_required(self, has_contact):
        self.fields["first_name"].required = not has_contact
        self.fields["last_name"].required = not has_contact
        self.fields["bio"].required = not has_contact
        self.fields["email"].required = not has_contact

    def has_contact(self):
        prefix = self.prefix + "-" if self.prefix else "" # for formsets
        return (self.instance and self.instance.contact) or self.data.get(prefix+"contact", None)


    def add_form_control_class(self):
        """
        adds the form-control class to all initialized fields in the form
        """
        for field in self.fields:
            class_attr = self.fields[field].widget.attrs.get("class", '')
            if not re.search(r'\bform-control\b', class_attr):
                self.fields[field].widget.attrs["class"] = "form-control " + class_attr

    class Meta:
        model = Speaker
        fields = ("id", "contact", "content", "first_name", "last_name", "email", "bio")


class ProposalSpeakerForm(SpeakerForm):

    default_publish_status = "SUBMISSION"

    def init_fields_required(self, has_contact):
        super().init_fields_required(has_contact)
        self.fields["bio"].required = False # Bio not required for manually entered speakers
        self.fields["bio"].widget.attrs["placeholder"] = "Optional"


class ProviderSpeakerForm(SpeakerForm):

    def init_fields_required(self, has_contact):
        super().init_fields_required(has_contact)
        self.fields["email"].required = False  # Email not required for manually entered speakers
        self.fields["email"].widget.attrs["placeholder"] = "Optional"


class AdditionalSpeakerForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    def clean(self):

        cleaned_data = super().clean()

        first_name = cleaned_data.get("first_name", None)
        last_name = cleaned_data.get("last_name", None)
        bio = cleaned_data.get("bio", None)

        if self.is_populated():
            if not first_name:
                self.add_error("first_name", "Please provide your speaker's first name")
            if not last_name:
                self.add_error("last_name", "Please provide your speaker's last name")
            if not bio:
                self.add_error("bio", "Please provide a bio for your additional speaker")

        return cleaned_data

    def is_populated(self):
        """
        call after clean() to tell if you need to process anything
        """
        first = self.cleaned_data.get("first_name", None)
        last = self.cleaned_data.get("last_name", None)
        bio = self.cleaned_data.get("bio", None)
        if first or last or bio:
            return True
        else:
            return False

    class Meta:
        model = ContactRole
        fields = ("first_name", "last_name", "bio")


# search form for BOTH events and training...
class EventTrainingSearchBaseFilterForm(SearchFilterFormKeywordless):
    """
    Includes fields that are common to all cm event searches
    """

    def __init__(self, foo_choices, *args, **kwargs):
        super().__init__(foo_choices, *args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    keyword = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"keyword"}), required=False, initial="*")

    cm = forms.ChoiceField(
        widget=HorizontalRadioSelect(),
        choices=(("","Any"), ("cm", "CM (General)"), ("cm_law", "Law"), ("cm_ethics", "Ethics"),
            ("cm_equity", "Equity"),
            ("cm_targeted", "Sustainability & Resilience"),
            ),
        required=False
    )

    is_free = forms.BooleanField(
            label="Free",
            required=False,
        )

    is_apa = forms.BooleanField(
            label="APA",
            required=False,
        )

    def to_query_list(self):
        output = super().to_query_list()
        if not self.data.get("include_archived", False):
            output.append("-archive_time:[* TO NOW]")
        return output

    # FLAGGED FOR REFACTORING: CM SEARCH CHANGES
    # REMOVE AFTER CM EVENT FIELD POSTGRES/SOLR SCHEMA CHANGES
    def clean(self):
        cleaned_data = super().clean()
        cm = cleaned_data.get("cm", None)

        if cm in ["cm", "cm_law", "cm_ethics"]:
            self.query_map_string = "{0}_approved:[0.01 TO *]"
        elif cm in ["cm_equity", "cm_targeted"]:
            self.query_map_string = "{0}_credits:[0.01 TO *]"
        else:
            self.query_map_string = "{0}_approved:[0.01 TO *]"

        return cleaned_data

    def get_query_map(self):
        query_map = super().get_query_map()
        # FLAGGED FOR REFACTORING: CM SEARCH CHANGES
        query_map["cm"] = self.query_map_string
        # query_map["cm"] = "{0}_approved:[0.01 TO *]"
        query_map["is_free"] = "is_free:true"
        query_map["is_apa"] = "is_apa:true"
        return query_map

    def get_sort(self):
        sort_field = self.query_params.get("sort", None)
        keyword = self.query_params["keyword"]

        if not sort_field and not keyword:
            self.data["sort"] = "begin_time desc, end_time desc"
        elif not sort_field or sort_field == "relevance":
            self.query_params["sort"] = "relevance"
            self.data["sort"] = None
        return self.data.get("sort", None)


class CalendarSearchForm(EventTrainingSearchBaseFilterForm):
    sort_choices = (
        ("relevance", "Relevance"),
        ("begin_time desc, end_time desc","Time (newest to oldest)"),
        ("begin_time asc, end_time asc","Time (oldest to newest)"),
        ("title_string asc", "Title (A to Z)"),
        ("title_string desc", "Title (Z to A)")
    )

    def __init__(self, foo_choices, *args, **kwargs):
        super().__init__(foo_choices, *args, **kwargs)
        self.fields['state'].choices = [("", "Choose One")] + get_selectable_options_tuple_list(mode="region_from_country", value="United States" )
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    event_type = forms.ChoiceField(
            widget=SelectFacade(facade_attrs={"data-empty-text":"Event Type"}),
            choices=(("","Choose One"), ("LEARN_COURSE", "APA Learn"), ("ONLINE","Live Online"),
                ("EVENT_MULTI", "Multipart Event"), ("COURSE", "On Demand"), ("EVENT_SINGLE","Single Event")),
            required=False
        )

    is_apa = forms.BooleanField(
            label="APA",
            required=False,
            initial=True,
        )

    state = forms.ChoiceField(
            widget=SelectFacade(facade_attrs={"data-empty-text":"State"}),
            choices=[],
            required=False
        )

    range_after = forms.DateTimeField(
            widget=DatetimeFacade(attrs={"data-show-time":"false", "placeholder":"After"}),
            label="RANGE STARTS",
            required=False
        )

    range_before = forms.DateTimeField(
            widget=DatetimeFacade(attrs={"data-show-time":"false", "placeholder":"Before"}),
            label="RANGE ENDS",
            required=False
        )

    include_archived = forms.BooleanField(
            label="Include Archive (Events Greater Than Two Years Old)",
            required=False,
        )

    def to_query_list(self):
        output = super().to_query_list()
        event_type = self.data.get("event_type", None)
        if event_type:
            if event_type == "ONLINE":
                output.append("is_online:true")
            else:
                output.append("event_type:{0}".format(event_type))
        return output

    def get_query_map(self):
        query_map = super().get_query_map()
        query_map["state"] = "address_state:\"{0}\""
        query_map["range_after"] = "begin_time:[{0}T00:0:00Z TO *]"
        query_map["range_before"] = "begin_time:[* TO {0}T23:59:59Z]"
        return query_map


class OnDemandSearchFilterForm(EventTrainingSearchBaseFilterForm):
    sort_choices = (
        ("relevance", "Relevance"),
        ("begin_time desc, end_time desc, title asc", "Time First Available"),
        ("title_string asc", "Title (A to Z)"),
        ("title_string desc", "Title (Z to A)")
    )

    event_type = forms.ChoiceField(
            widget=SelectFacade(facade_attrs={"data-empty-text":"Event Type"}),
            choices=(("","Choose One"), ("LEARN_COURSE", "APA Learn"),
                ("COURSE", "On Demand") ),
            required=False
        )


class EventTimeFieldsMixin(object):
    def init_begin_end_time_fields(self):

        if self.data: # when submitting data
            initial_timezone = self.data.get("timezone", "US/Central")
        elif self.instance and getattr(self.instance, "timezone", None): # when viewing existing data
            initial_timezone = getattr(self.instance, "timezone")
        else: # when new
            initial_timezone = self.initial.get("timezone", None) or "US/Central"


        if self.instance and self.instance.event_type == 'COURSE':
            self.fields["timezone"] = forms.ChoiceField(
                label="Time Zone",
                choices= [(None, "")] + [(tz,tz) for tz in pytz.all_timezones],
                initial="US/Central",
                required=False
                )
        else:
            self.fields["timezone"] = forms.ChoiceField(
                label="Time Zone",
                choices= [(None, "")] + [(tz,tz) for tz in pytz.all_timezones],
                initial="US/Central",
                required=True
                )

        self.fields['begin_time'] = DateTimeTimezoneField(required=True, label="Start",
            widget=widgets.AdminSplitDateTime(),
                        timezone_str=initial_timezone)

        self.fields['end_time'] = DateTimeTimezoneField(required=True, label="End",
            widget=widgets.AdminSplitDateTime(),
            timezone_str=initial_timezone)

class EventAdminAuthorForm(EventTimeFieldsMixin, ContentAdminAuthorForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_begin_end_time_fields()

    class Meta:
        model = Event
        exclude = []
        widgets = {
            "text":forms.Textarea(attrs={"class":"ckeditor"})
        }


class EventAdminEditorForm(EventTimeFieldsMixin, ContentAdminEditorForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_begin_end_time_fields()

    class Meta:
        model = Event
        exclude = []
        widgets = {
            "text":forms.Textarea(attrs={"class":"ckeditor"}),
            "learning_objectives":forms.Textarea(attrs={"class":"ckeditor"})
        }


class SpeakerSearchFilterForm(AddFormControlClassMixin, SearchFilterForm):

    city = forms.CharField(
        widget=forms.TextInput(),
        required=False)

    state = forms.ChoiceField(
        choices=[],
        required=False)

    # range_after = forms.DateTimeField(
    #     widget=DatetimeFacade(attrs={"data-show-time":"false", "placeholder":"After"}),
    #     label="Range Starts",
    #     required=False)

    # range_before = forms.DateTimeField(
    #     widget=DatetimeFacade(attrs={"data-show-time":"false", "placeholder":"Before"}),
    #     label="Range Ends",
    #     required=False)

    is_member = forms.BooleanField(
        label="Include Members Only",
        required=False)

    designation = forms.ChoiceField(
        label="Designation",
        choices=[(None, ""), ("FAICP AICP", "AICP"), ("FAICP", "FAICP")],
        required=False)

    npc = forms.ChoiceField(
        label="Event",
        choices=[(None, ""),
            ("9135594", "NPC18"),
            ("9102340", "NPC17"),
            ("9000321", "NPC16"),
            ("3027311", "NPC15")], # hardcoded npc years, note: figure out way to store npc alt names like this, so we don't need to add every year
        required=False)

    sort_choices = (
        ("relevance", "Relevance"),
        ("sort_time desc", "Date (Newest)"),
        ("last_name asc, first_name asc", "Speaker Name (A to Z)")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["state"].choices = [(None,"")] + get_selectable_options_tuple_list(mode="region_from_country", value="United States")
        self.fields["keyword"].widget.attrs["placeholder"] = "Speaker name, company, or bio; session title or topic"

        self.add_form_control_class()

    def get_query_map(self):
        keyword_query_map = "(title:\"{0}\")^10 (title:({0}))^4"

        keyword_query_map += " (speaker_events:\"{0}\")^2.4 (speaker_events:(*|*|*{0}*|*|*))^1.4"
        keyword_query_map += " (tags:\"{0}\")^2.3 (tags:({0}))^1.3"
        keyword_query_map += " (company:\"{0}\")^2.2 (company:({0}))^1.2"
        keyword_query_map += " (bio:\"{0}\")^2.1 (bio:({0}))^1.1"
        keyword_query_map += " (last_name:\"{0}\")^2.1 (last_name:({0}))^1.1" # last_name matches should be better than first name

        keyword_query_map += " (text_search:({0}) OR id:(*.{0}) OR id:(*.30{0}) OR id:(*.4{0}))" # IMPORTANT: THIS HAS TO GO LAST!!

        return {
            "keyword":keyword_query_map,
            "city":"address_city:({0})",
            "state":"address_state:{0}",
            # "range_after":"speaker_dates:[{0}T00:0:00Z TO *]",
            # "range_before":"speaker_dates:[* TO {0}T23:59:59Z]",
            "is_member":"member_type:(MEM STU)",
            "designation":"designation:({0})",
            "npc":"speaker_events:(*|*|*|*|{0})"
        }

    def get_sort(self):
        sort = self.query_params.get("sort", None)
        keyword = self.query_params.get("keyword", None)

        if not sort and not keyword:
            self.query_params["sort"] = "last_name asc, first_name asc"
            self.data["sort"] = "last_name asc, first_name asc"
        elif not sort or sort == "relevance":
            self.query_params["sort"] = "relevance"
            self.data["sort"] = None

        return self.data.get("sort", None)


class EventMultiSearchForm(SearchFilterForm):
    """
    Search form for a multi event details page with activities
    """

    sort_choices = (
        ("begin_time asc, end_time asc", "Time (oldest to newest)"),
        ("begin_time desc, end_time desc", "Time (newest to oldest)"),
        ("relevance", "Relevance"),
        ("title_string asc", "Title (A to Z)"),
        ("title_string desc", "Title (Z to A)")
    )
    cm = forms.ChoiceField(
        widget=HorizontalRadioSelect(),
        choices=(("","Any"), ("cm", "CM (General)"), ("cm_law", "Law"), ("cm_ethics", "Ethics"),
            ("cm_equity", "Equity"),
            ("cm_targeted", "Sustainability & Resilience"),
            ),
        required=False
    )

    # Whether or not to show the "CM Meeting Type" form in
    # content/templates/content/newtheme/search/includes/filters.html
    has_meeting_type = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sort"] = forms.ChoiceField(
            widget=SelectFacade(facade_attrs={"class": "goooold"}, pretext="Sort By: "),
            choices=self.sort_choices,
            required=False,
            initial=("begin_time asc, end_time asc", "Time (oldest to newest)")
        )

    # FLAGGED FOR REFACTORING: CM SEARCH CHANGES
    # REMOVE AFTER CM EVENT FIELD POSTGRES/SOLR SCHEMA CHANGES
    def clean(self):
        cleaned_data = super().clean()
        cm = cleaned_data.get("cm", None)

        if cm in ["cm", "cm_law", "cm_ethics"]:
            self.query_map_string = "{0}_approved:[0.01 TO *]"
        elif cm in ["cm_equity", "cm_targeted"]:
            self.query_map_string = "{0}_credits:[0.01 TO *]"
        else:
            self.query_map_string = "{0}_approved:[0.01 TO *]"

        return cleaned_data

    def get_query_map(self):
        query_map = super().get_query_map()
        # FLAGGED FOR REFACTORING: CM SEARCH CHANGES
        query_map["cm"] = self.query_map_string
        # query_map = super().get_query_map()
        # query_map["cm"] = "{0}_approved:[0.01 TO *]"
        return query_map

    def get_sort(self):
        sort_field = self.query_params.get('sort')
        keyword = self.query_params['keyword']

        if not sort_field and not keyword:
            self.data['sort'] = "begin_time asc, end_time asc"
        elif not sort_field or sort_field == "relevance":
            self.query_params["sort"] = "relevance"
            self.data["sort"] = None
        return self.data.get('sort')
