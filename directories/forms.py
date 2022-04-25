from django import forms
from content.forms import StateCountryModelFormMixin
from myapa.models.constants import FUNCTIONAL_TITLE_CHOICES


class DirectoryForm(StateCountryModelFormMixin, forms.Form):

    keyword = forms.CharField(label="Keyword", widget=forms.TextInput(attrs={'placeholder': 'first name, last name or organization', 'size': 60}), required=False)
    school = forms.CharField(label="University", required=False, widget=forms.TextInput(attrs={'size': 60}))
    city = forms.CharField(label="City", required=False, widget=forms.TextInput(attrs={'size': 60}))
    profile_only = forms.BooleanField(label="Members with profiles only", required=False)
    aicp_only = forms.BooleanField(label="AICP Members only", required=False)

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.init_state_country_fields(state_required=False, country_required=False)
        self.query_params = args[0].copy()
        self.data = self.query_params

    def get_query_map(self):

        filter_kwargs = {}

        keyword = self.data.get("keyword", None)
        school = self.data.get("school", None)
        city = self.data.get("city", None)
        profile_only = self.data.get("profile_only", None)
        aicp_only = self.data.get("aicp_only", None)
        state = self.data.get("state", None)
        country = self.data.get("country", None)

        if keyword:
            filter_kwargs["keyword"] = keyword

        if school:
            filter_kwargs["school"] = school
            if profile_only: #???? TO DO: What does this have to do with the school????
                filter_kwargs["contact__individualprofile__slug__isnull"] = False

        if city:
            filter_kwargs["contact__city__icontains"] = city

        if state:
            filter_kwargs["contact__state__contains"] = state

        if country:
            filter_kwargs["contact__country__contains"] = country

        if profile_only and not school: #???? TO DO: What does this have to do with the school????
            filter_kwargs["slug__isnull"] = False

        if aicp_only:
            filter_kwargs["contact__user__groups__name"] = "aicpmember"

        return filter_kwargs


class PASDirectoryForm(StateCountryModelFormMixin, forms.Form):

    company = forms.CharField(label="Organization", widget=forms.TextInput(attrs={'size': 60}), required=False)
    city = forms.CharField(label="City", required=False, widget=forms.TextInput(attrs={'size': 60}))

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.init_state_country_fields(state_required=False, country_required=False)
        self.query_params = args[0].copy()
        self.data = self.query_params

    def get_query_map(self):

        filter_kwargs = {}

        company = self.data.get("company", None)
        city = self.data.get("city", None)
        state = self.data.get("state", None)
        country = self.data.get("country", None)

        if company:
            filter_kwargs["contact__company__icontains"] = company

        if city:
            filter_kwargs["contact__city__icontains"] = city

        if state:
            filter_kwargs["contact__state__contains"] = state

        if country:
            filter_kwargs["contact__country__contains"] = country

        return filter_kwargs


class ResumeSearchForm(StateCountryModelFormMixin, forms.Form):

    keyword = forms.CharField(label="Keyword", widget=forms.TextInput(attrs={'placeholder': 'first name, last name or organization', 'size': 60}), required=False)
    school = forms.CharField(label="University", required=False, widget=forms.TextInput(attrs={'size': 60}))
    functional_title = forms.ChoiceField(label="Functional Title", required=False, choices=[(None, "Optional")] +  list(FUNCTIONAL_TITLE_CHOICES))
    city = forms.CharField(label="City", required=False, widget=forms.TextInput(attrs={'size': 60}))
    aicp_only = forms.BooleanField(label="AICP Members only", required=False)
    faicp_only = forms.BooleanField(label="FAICP Members only", required=False)

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.init_state_country_fields(state_required=False, country_required=False)
        self.query_params = args[0].copy()
        self.data = self.query_params

    def get_query_map(self):

        filter_kwargs = {}

        keyword = self.data.get("keyword", None)
        school = self.data.get("school", None)
        functional_title = self.data.get("functional_title", None)
        city = self.data.get("city", None)
        faicp_only = self.data.get("faicp_only", None)
        aicp_only = self.data.get("aicp_only", None)
        state = self.data.get("state", None)
        country = self.data.get("country", None)

        if keyword:
            filter_kwargs["keyword"] = keyword

        if school:
            filter_kwargs["school"] = school

        if city:
            filter_kwargs["contact__city__icontains"] = city

        if state:
            filter_kwargs["contact__state__contains"] = state

        if country:
            filter_kwargs["contact__country__contains"] = country

        if faicp_only:
            filter_kwargs["contact__user__groups__name"] = "FAICP"

        if aicp_only:
            filter_kwargs["contact__user__groups__name"] = "aicpmember"

        return filter_kwargs
