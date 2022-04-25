import datetime
import pytz

from django import forms
from django.template import defaultfilters
from sentry_sdk import capture_exception

from content.models import Tag
from content.forms import SearchFilterForm
from content.widgets import SelectFacade
from events.models import Event, EVENTS_NATIONAL_TRACK_CURRENT


class ConferenceSearchFilterForm(SearchFilterForm):

    keyword = forms.CharField(
        widget = forms.TextInput(attrs = {"placeholder": "Search Program", "class": "form-control"}),
        required = False,
        initial = "*"
    )

    cm = forms.ChoiceField(
        widget=SelectFacade(facade_attrs={"data-empty-text": " "}),
        choices=(
            ("", ""),
            ("cm", "CM Credits"),
            ("cm_law", "Law Credits"),
            ("cm_ethics", "Ethics Credits"),
        ),
        required=False
    )

    # TO DO... update to pull in choices from queries
    topics = forms.ChoiceField(
        widget=SelectFacade(facade_attrs={"data-empty-text": " "}),
        choices=(("", ""), ("TOPIC_HOUSING_POLICY", "Housing Policy"), ),
        required=False
    )

    divisions = forms.ChoiceField(
        widget=SelectFacade(facade_attrs={"data-empty-text": " "}),
        choices=(("", ""), ),
        required=False
    )

    tracks = forms.ChoiceField(
        widget=SelectFacade(facade_attrs={"data-empty-text": " "}),
        choices=(("", ""), (1376, "From Climate Change to Resilience"), ),
        required=False
    )

    activity_types = forms.ChoiceField(
        widget=SelectFacade(facade_attrs={"data-empty-text": " "}),
        choices=(("", ""), ("cm", "CM Credits"), ("cm_law", "Law Credits"), ("cm_ethics", "Ethics Credits"),),
        required=False
    )

    date = forms.ChoiceField(
        widget=SelectFacade(),
        required=False
    )

    tags = forms.CharField(widget=forms.HiddenInput()) # manually handling query conversion
    # tag_types = forms.CharField(widget=forms.HiddenInput()) # manually handling query conversion # DONT THINK WE EVER NEED TO DO THIS
    speakers = forms.CharField(widget=forms.HiddenInput()) # manually handling query conversion

    def __init__(self, *args, conference, **kwargs):
        self.conference = conference
        self.microsite = None
        if self.conference:
            self.microsite = self.conference.master.event_microsite.first()
        super().__init__(*args, **kwargs)

        if self.microsite:
            filters = self.microsite.program_search_filters.all()
            field_list = []

            for i, tt in enumerate(filters):
                self.fields['filter_%s' % tt.code.lower()] = forms.ChoiceField(
                    widget=SelectFacade(facade_attrs={"data-empty-text": " "}),
                    required=False,
                    choices=[("", "")] + [(t.code, t.title) for t in tt.tags.all().filter(
                        status="A"
                    ).order_by(
                        "title"
                    )],
                    label='filter_%s' % tt.code.lower()
                    )
                field_list.append(self.fields['filter_%s' % tt.code.lower()])
            self.filter_field_list = field_list + [self.fields["date"]]
            self.fields["date"].choices = self.get_filter_dates()
        else:
            tags = Tag.objects.select_related("tag_type").filter(
                tag_type__code__in=[
                    EVENTS_NATIONAL_TRACK_CURRENT,
                    "SEARCH_TOPIC",
                    "EVENTS_NATIONAL_TYPE",
                    "DIVISION"
                ],
                status="A"
            ).order_by("sort_number", "title")

            self.fields["topics"].choices = [("", "")] + [(t.code, t.title) for t in tags if t.tag_type.code == "SEARCH_TOPIC"]
            self.fields["tracks"].choices = [("", "")] + [(t.code, t.title) for t in tags if t.tag_type.code == EVENTS_NATIONAL_TRACK_CURRENT]
            self.fields["activity_types"].choices = [("", "")] + [(t.code, t.title) for t in tags if t.tag_type.code == "EVENTS_NATIONAL_TYPE"]
            self.fields["divisions"].choices = [("", "")] + [(t.code, t.title) for t in tags if t.tag_type.code == "DIVISION"]

    def get_filter_dates(self):
        # SHOULD MOVE ALL THESE FILTERS TO A FORM?
        filter_dates = [("", "All")]
        multi_begin_time_as_date = self.conference.begin_time_astimezone().date()
        current_year = multi_begin_time_as_date.year
        multi_end_time_as_date = self.conference.end_time_astimezone().date()
        two_weeks = datetime.timedelta(days=14)
        twbm = two_weeks_before_multi = multi_begin_time_as_date - two_weeks
        twam = two_weeks_after_multi = multi_end_time_as_date + two_weeks

        date_set = set()
        acts = Event.objects.filter(parent=self.conference.master).order_by("begin_time")

        for a in acts:
            try:
                date = a.begin_time_astimezone().date()
                if date.year == current_year and date >= twbm and date <= twam:
                    date_set.add(date)
            except Exception as e:
                capture_exception(e)

        date_list = list(date_set)
        date_list.sort()

        # begin_time_as_date = self.conference.begin_time_astimezone().date()
        # end_time_as_date = self.conference.end_time_astimezone().date()
        # date_difference = end_time_as_date - begin_time_as_date
        # for i in range(date_difference.days + 1):
        #     _date = begin_time_as_date + datetime.timedelta(days=i)
        #     filter_dates.append((_date.strftime("%Y-%m-%d"), defaultfilters.date(_date, "l, F j") ))

        for d in date_list:
            filter_dates.append((d.strftime("%Y-%m-%d"), defaultfilters.date(d, "l, F j")))

        return filter_dates

    def get_query_map(self):
        query_map = super().get_query_map()
        # query_map["date"] = "begin_time:[{0}T00:0:00Z TO {0}T23:59:59Z]"
        query_map["cm"] = "{0}_approved:[0.01 TO *]"
        return query_map

    def to_query_list(self):
        output = super().to_query_list()
        date_string = self.query_params.get("date", None)
        if date_string:
            date_list = [int(d) for d in date_string.split("-")]
            range_begin_time = datetime.datetime(*date_list, tzinfo=self.conference.timezone_object())
            range_end_time = datetime.datetime(*(date_list+[23, 59, 59]), tzinfo=self.conference.timezone_object())
            range_begin_time_string = range_begin_time.astimezone(pytz.timezone("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")
            range_end_time_string = range_end_time.astimezone(pytz.timezone("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")
            output.append("begin_time:[" + range_begin_time_string + " TO " + range_end_time_string + "]")
        return output
