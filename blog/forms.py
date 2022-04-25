from django import forms

from content.models import Tag
from content.forms import SearchFilterForm

from .models import BlogCategoryContentTagType


class BlogCategoryContentTagTypeAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tags'].queryset = Tag.objects.filter(
            tag_type__code="BLOG_CATEGORY")

    class Meta:
        model = BlogCategoryContentTagType
        exclude = ["tag_type", "published_time", "publish_time",
                   "published_by", "publish_status", "publish_uuid"]


class BlogSearchFilterForm(SearchFilterForm):

    sort_choices = (
        ("sort_time desc, published_time desc", "Date Posted"),
        ("title_string asc", "Title (A to Z)"),
        ("title_string desc", "Title (Z to A)"),
        ("relevance", "Relevance"),
    )

    # should have better way to set default sort value
    def get_sort(self):
        sort_field = self.query_params.get("sort", None)

        if not sort_field:
            self.data["sort"] = "sort_time desc, published_time desc"
        elif sort_field == "relevance":
            self.query_params["sort"] = "relevance"
            self.data["sort"] = None

        return self.data.get("sort", None)
