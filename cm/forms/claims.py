import pytz

from django import forms
from decimal import Decimal

from content.forms import StateCountryModelFormMixin

from cities_light.models import Country, Region

from cm.models.claims import Log, AUTHOR_TYPES
# FLAGGED FOR REFACTORING: CM CONSOLIDATION
# from cm.models import settings as cm_settings

# from comments.forms import EventCommentForm
from content.forms import DateTimeTimezoneField
from events.forms import EventTrainingSearchBaseFilterForm, CalendarSearchForm

from cm.models import Claim, CMComment


class CMSearchFilterForm(CalendarSearchForm):
    pass


class CMOnDemandSearchFilterForm(EventTrainingSearchBaseFilterForm):
    sort_choices = (
        ("relevance", "Relevance"),
        ("begin_time desc, end_time desc, title asc", "Time First Available"),
        ("title_string asc", "Title (A to Z)"),
        ("title_string desc", "Title (Z to A)")
    )

    include_archived = forms.BooleanField(
            label="Include Archive (Events Greater Than Two Years Old)",
            required=False,
        )


class ClaimBaseForm(forms.ModelForm):
    """
    Form for logging events conference session evaluations... and base class for CM logging form.
    """

    def __init__(self, *args, **kwargs):


        super().__init__(*args, **kwargs)

        self.fields["verified"] = forms.BooleanField(required=True) # if CM, then the user must verify
        # self.fields["make_public"] = forms.BooleanField(required=False)

        # self.fields["rating"] = forms.ChoiceField(required=False, choices = RATING_CHOICES )

    class Meta:
        model = Claim
        fields = ["is_speaker", "verified", "log", "contact"]
        widgets = {"log": forms.HiddenInput(), "contact": forms.HiddenInput()}


class EventClaimForm(ClaimBaseForm):
    """
    Form for logging events conference session evaluations... and base class for CM logging form.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        credits = self.initial["event"].cm_approved
        i = Decimal(0.25)
        speaker_range = [(x*i+i, x*i+i) for x in range(0,int((credits+1)/i))] # funny math hack to generate 0.5 to 1 plus approved credits, in increments of 0.25
        self.fields["credits"] = forms.ChoiceField(required=False, choices = speaker_range, initial=self.instance.credits )

        # for field in self.fields:
        #     self.fields[field].widget.attrs['class'] = 'form-control'

        # self.fields["rating"] = forms.ChoiceField(required=False, choices = RATING_CHOICES )

    class Meta:
        model = ClaimBaseForm.Meta.model
        widgets = {"log": forms.HiddenInput(), "contact": forms.HiddenInput(), "event": forms.HiddenInput()}
        fields = ["event", "credits", "is_speaker", "verified", "log", "contact"]


class SelfReportClaimForm(StateCountryModelFormMixin, ClaimBaseForm):
    """
    Form for logging events conference session evaluations... and base class for CM logging form.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.init_state_country_fields()

        self.fields["self_reported"].initial=True
        city = forms.CharField(required=True)
        state = forms.ModelChoiceField(required = False, queryset=Region.objects.filter(country_id=234))
        # state_other = forms.CharField(required = False)
        country = forms.ModelChoiceField(required = True, queryset=Country.objects.all())

        i = Decimal(0.25)
        credits_range =  [(x*i+i, x*i+i) for x in range(0,int(8/i))] # funny math hack to generate 0.25 to 1 plus approved credits, in increments of 0.25
        # FLAGGED FOR REFACTORING: CM CONSOLIDATION
        # law_range=[(0,0)] + [(x*i+i, x*i+i) for x in range(0,int(Decimal(1.5)/i))]
        # ethics_range=[(0,0)] + [(x*i+i, x*i+i) for x in range(0,int(Decimal(1.5)/i))]
        # how do we know the reporting period here? DOES THIS NEED TO CHANGE?

        law_range=[(0,0)] + [(x*i+i, x*i+i) for x in range(0,int(Decimal(1.5)/i))]
        ethics_range=[(0,0)] + [(x*i+i, x*i+i) for x in range(0,int(Decimal(1.5)/i))]
        self.fields["credits"] = forms.ChoiceField(required=False, choices = credits_range, initial=self.instance.credits )
        self.fields["law_credits"] = forms.ChoiceField(required=False, choices = law_range, initial=self.instance.law_credits )
        self.fields["ethics_credits"] = forms.ChoiceField(required=False, choices = ethics_range, initial=self.instance.ethics_credits )
        self.fields["provider_name"] = forms.CharField(label="Organization or Provider name", required=True)
        self.fields["title"] = forms.CharField(required=True)
        self.fields["city"] = forms.CharField(required=True)
        self.fields["is_pro_bono"] = forms.BooleanField(label="This activity is pro bono", required=False)
        self.fields["description"].required = True
        self.fields["learning_objectives"].required = True

        # for field in self.fields:
        #     self.fields[field].widget.attrs['class'] = 'form-control'

        self.init_time_fields()

        #changes that were needed to add the attribute to provider name,

        for field in self.fields:
            if self.fields[field].required:
                self.fields[field].widget.attrs['required'] = ''
        self.fields['country'].widget.attrs['class'] = 'form-control selectchain'

    def init_time_fields(self):

        if self.data: # when submitting data
            # to handle both single forms and formsets:
            timezone_key = self.prefix + ("-" if self.prefix else "") + "timezone"
            initial_timezone = self.data.get(timezone_key) or "US/Central"
        elif self.instance and getattr(self.instance, "timezone", None): # when viewing existing data
            initial_timezone = getattr(self.instance, "timezone")
        else: # when new
            initial_timezone = self.initial.get("timezone", "US/Central")

        self.fields["timezone"] = forms.ChoiceField(
            label="TIME ZONE WHERE EVENT OCCURRED",
            required=True,
            choices=[(tz,tz) for tz in pytz.all_timezones],
            widget=forms.Select(attrs={"class":"form-control"}),
            initial="US/Central")

        self.fields["begin_time"] = DateTimeTimezoneField(label="Service or Event Begin Date and Time", required=True,
            widget=forms.TextInput(attrs={"class":"planning-datetime-widget form-control", "required":""}),
            timezone_str=initial_timezone)
        self.fields["end_time"] = DateTimeTimezoneField(label="Service or Event End Date and Time", required=True,
            widget=forms.TextInput(attrs={"class":"planning-datetime-widget form-control", "required":""}),
            timezone_str=initial_timezone)

    def clean(self):
        cleaned_data = super().clean()
        is_pro_bono = cleaned_data.get("is_pro_bono", False)
        credits = float(cleaned_data.get("credits", 0.0))
        law_credits = float(cleaned_data.get("law_credits", 0.0))
        ethics_credits = float(cleaned_data.get("ethics_credits", 0.0))

        if is_pro_bono:

            if credits and not credits.is_integer():
                self.add_error("credits", "For pro bono services, you may only claim CM credits in whole integer increments (e.g. 1.0, 2.0, 3.0)")
            if law_credits:
                self.add_error("law_credits", "For pro bono services, you cannot include law credit claims")
            if ethics_credits:
                self.add_error("ethics_credits", "For pro bono services, you cannot include ethics credit claims")

        return cleaned_data


    class Meta:
        model = ClaimBaseForm.Meta.model
        widgets = ClaimBaseForm.Meta.widgets
        widgets["self_reported"] = forms.HiddenInput()
        fields = ["provider_name", "title", "begin_time", "end_time", "timezone", "learning_objectives", "description", "credits",
            "law_credits", "ethics_credits", "city", "state", "country", "self_reported", "is_pro_bono"] + ClaimBaseForm.Meta.fields

class AuthorClaimForm(ClaimBaseForm):
    """
    Form for logging events conference session evaluations... and base class for CM logging form.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["credits"] = forms.CharField()
        self.fields["credits"].widget = forms.HiddenInput()
        self.fields["credits"].initial=8
        self.fields["is_author"].initial=True
        self.fields["provider_name"].required = False
        self.fields["provider_name"].label="Journal Title or Book Publisher"
        self.fields["provider_name"].widget = forms.TextInput(attrs={"placeholder": "Optional"})
        self.fields["title"].label="Article Name or Book Title"
        self.fields["title"].required = True
        self.fields["provider_name"].widget.attrs['class'] = 'form-control'
        self.fields["title"].widget.attrs['class'] = 'form-control'

        self.fields["begin_time"] = forms.DateTimeField(required = True, label="Published Date",
            widget=forms.TextInput(attrs={"class":"planning-datetime-widget form-control"}))
        self.fields["author_type"] = forms.ChoiceField(choices=AUTHOR_TYPES, required=True,
                                                       label="Criterion Recommendation")

        # Eliminating this due to only one field required in this view
        #for field in self.fields:
        #   if self.fields[field].required:
        #       self.fields[field].widget.attrs['required'] = ''

    def clean(self):
        cleaned_data = super().clean()
        author_type = cleaned_data.get("author_type", "PLANNING_ARTICLE")
        contact = cleaned_data["contact"]
        log = Log.objects.filter(contact=contact, is_current=True).first()
        overview = log.credits_overview()

        if overview:
            current_auth_creds = overview["is_author"]
            creds_available_to_fill = 16 - current_auth_creds

        if creds_available_to_fill > 0:
            if author_type == "PLANNING_ARTICLE":
                potential_creds = 4
            elif author_type == "PLANNING_JOURNAL_ARTICLE":
                potential_creds = 8
            elif author_type == "PLANNING_BOOK":
                potential_creds = 16

            if potential_creds <= creds_available_to_fill:
                creds_to_apply = potential_creds
            else:
                creds_to_apply = creds_available_to_fill
            cleaned_data["credits"] = Decimal("{:.1f}".format(creds_to_apply))
        else:
            self.add_error("credits", "You are limited to 16 authoring credits per reporting period.")

        return cleaned_data

    class Meta:
        model = ClaimBaseForm.Meta.model
        widgets = ClaimBaseForm.Meta.widgets
        widgets["is_author"] = forms.HiddenInput()
        fields = ["provider_name", "begin_time", "title", "description", "credits", "is_author",
                "author_type"] + ClaimBaseForm.Meta.fields

