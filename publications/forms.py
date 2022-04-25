from django import forms

from content.models.tagging import Tag#, PlanningMagFeaturedContentTagType
from publications.models import (Publication, PlanningMagFeaturedContentTagType, PlanningMagSectionContentTagType,
    PlanningMagSeriesContentTagType, PlanningMagSlugContentTagType, PlanningMagSponsoredContentTagType)


class PlanningMagFeaturedContentTagTypeAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tags'].queryset = Tag.objects.filter(
            tag_type__code="PLANNING_MAG_FEATURED")

    class Meta:
        model = PlanningMagFeaturedContentTagType
        exclude = ["tag_type", "published_time", "publish_time",
                   "published_by", "publish_status", "publish_uuid"]


class PlanningMagSectionContentTagTypeAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tags'].queryset = Tag.objects.filter(
            tag_type__code="PLANNING_MAG_SECTION")

    class Meta:
        model = PlanningMagSectionContentTagType
        exclude = ["tag_type", "published_time", "publish_time",
                   "published_by", "publish_status", "publish_uuid"]


class PlanningMagSeriesContentTagTypeAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tags'].queryset = Tag.objects.filter(
            tag_type__code="PLANNING_MAG_SERIES")

    class Meta:
        model = PlanningMagSeriesContentTagType
        exclude = ["tag_type", "published_time", "publish_time",
                   "published_by", "publish_status", "publish_uuid"]


class PlanningMagSlugContentTagTypeAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tags'].queryset = Tag.objects.filter(
            tag_type__code="PLANNING_MAG_SLUG")

    class Meta:
        model = PlanningMagSlugContentTagType
        exclude = ["tag_type", "published_time", "publish_time",
                   "published_by", "publish_status", "publish_uuid"]


class PlanningMagSponsoredContentTagTypeAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tags'].queryset = Tag.objects.filter(
            tag_type__code="SPONSORED")

    class Meta:
        model = PlanningMagSponsoredContentTagType
        exclude = ["tag_type", "published_time", "publish_time",
                   "published_by", "publish_status", "publish_uuid"]
