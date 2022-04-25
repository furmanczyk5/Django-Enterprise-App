import nested_admin
from django import forms
from django.contrib import admin
from reversion.admin import VersionAdmin

from content.admin import ContentAdmin, ArchivedStatusListFilter, TagListFilter, CollectionRelationshipInline
from content.models.content_relationship import ContentRelationship
from store.admin import ProductInline

from .forms import (PlanningMagFeaturedContentTagTypeAdminForm, PlanningMagSectionContentTagTypeAdminForm,
    PlanningMagSeriesContentTagTypeAdminForm, PlanningMagSlugContentTagTypeAdminForm, PlanningMagSponsoredContentTagTypeAdminForm)
from .models import (Publication, PublicationDocument, Report, PlanningMagArticle, PlanningMagFeaturedContentTagType,
    PlanningMagSectionContentTagType, PlanningMagSeriesContentTagType, PlanningMagSlugContentTagType,
    PlanningMagSponsoredContentTagType)


class LinkedPublicationInline(admin.StackedInline):
    model = ContentRelationship
    verbose_name = "Linked Publication"
    verbose_name_plural = "Linked Publications"
    fk_name = "content"
    extra = 0
    can_delete = True

    raw_id_fields = ["content", "content_master_related"]

    readonly_fields = ["get_publication_title", "get_related_publication_format"]

    fieldsets = [
        (None, {
            "fields": (
                ("content"),
                ("content_master_related", "get_publication_title"),
                ("relationship", "get_related_publication_format"),
            )
        }),
    ]

    def get_publication_title(self, obj):
        return obj.content_master_related.content_draft.title
    get_publication_title.short_description = "Publication Title"

    def get_related_publication_format(self, obj):
        return obj.content_master_related.content_draft.publication.publication_format
    get_related_publication_format.short_description = "Related Publication Format"


class FeaturedZoneInline(admin.TabularInline):
    model = PlanningMagFeaturedContentTagType
    extra = 1
    max_num = 1
    filter_horizontal = ('tags',)
    form = PlanningMagFeaturedContentTagTypeAdminForm
    classes = ("grp-collapse grp-closed",)

class SectionInline(admin.TabularInline):
    model = PlanningMagSectionContentTagType
    extra = 1
    max_num = 1
    filter_horizontal = ('tags',)
    form = PlanningMagSectionContentTagTypeAdminForm
    classes = ("grp-collapse grp-closed",)

class SeriesInline(admin.TabularInline):
    model = PlanningMagSeriesContentTagType
    extra = 1
    max_num = 1
    filter_horizontal = ('tags',)
    form = PlanningMagSeriesContentTagTypeAdminForm
    classes = ("grp-collapse grp-closed",)

class SlugInline(admin.TabularInline):
    model = PlanningMagSlugContentTagType
    extra = 1
    max_num = 1
    filter_horizontal = ('tags',)
    form = PlanningMagSlugContentTagTypeAdminForm
    classes = ("grp-collapse grp-closed",)

class SponsoredInline(admin.TabularInline):
    model = PlanningMagSponsoredContentTagType
    extra = 1
    max_num = 1
    filter_horizontal = ('tags',)
    form = PlanningMagSponsoredContentTagTypeAdminForm
    classes = ("grp-collapse grp-closed",)


class PublicationAdmin(nested_admin.NestedModelAdmin, ContentAdmin, VersionAdmin):
    list_filter = ("status", TagListFilter, ArchivedStatusListFilter, "workflow_status")  # removes content_type from filters
    list_display = (
        "get_master_id",
        "get_landing_ancestors_admin_links",
        "title", "url", "status",
        "is_published", "is_up_to_date",
        "get_published_time", "workflow_status"
    )
    readonly_fields = ContentAdmin.readonly_fields + ('content_type',)
    change_form_template = "admin/pages/page/change-form.html" # using page change_form because of the checkin/checkout system
    format_tag_defaults = ["FORMAT_WEBPAGE"]
    show_sync_harvester = False

    fieldsets = ContentAdmin.fieldsets + [
        ("Publication Data", {
            "classes": ("grp-collapse grp-closed",),
            "fields": (
                        "author_bios",
                        "abstract",
                        ("publication_format", "resource_type",),
                        ("publication_download"),
                        ("serial_pub","volume_number","issue_number"),
                        ("isbn", "edition", "language"),
                        ("resource_published_date", "copyright_date", "sort_time"),
                        "date_text",
                        ("copyright_statement", "page_count",),
                        "table_of_contents"
                        # "places", # inline?
                        # "related" # inline?
            )
        })
    ]
    inlines = ContentAdmin.inlines + (FeaturedZoneInline, SectionInline, SeriesInline, SlugInline, SponsoredInline,
        ProductInline, CollectionRelationshipInline, LinkedPublicationInline)

    def get_queryset(self, request):
        # OMG!!!!
        return super().get_queryset(request).select_related(
            "{0}__{0}__{0}__{0}__{0}".format("parent_landing_master__content_draft__landingpage")
        )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['table_of_contents'].widget = forms.Textarea(
            attrs={"class": "ckeditor"})
        form.base_fields['author_bios'].widget = forms.Textarea(
            attrs={"class": "ckeditor"})
        return form

    class Media:
        js = ContentAdmin.Media.js + ("pages/checkin/js/admin-page-checkin.js",)
        css = {
            'all':ContentAdmin.Media.css.get("all") + ("pages/checkin/css/admin-page-checkin.css",)
        }

        # from EmailTemplateAdmin
        # js = (
        #     "//ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js",
        #     static(CKEDITOR_STATIC_PATH),
        #     # static("ckeditor/plugins/lite/lite-interface.js")
        # )
        # css = {
        #      'all': ( static("ckeditor/plugins/planning_media/admin.css"), )
        # }


class PlanningMagArticleAdmin(PublicationAdmin):
    format_tag_defaults = ["FORMAT_ARTICLE"]
    readonly_fields = PublicationAdmin.readonly_fields + ('serial_pub',)



class ReportAdmin(PublicationAdmin):
    format_tag_defaults = ["FORMAT_REPORT"]
    list_display = ["get_master_id", "get_landing_ancestors_admin_links", "title", "code", "url", "status", "is_published", "is_up_to_date", "get_published_time"
    # "published_to_solr" # COULD BE USED FOR DEBUGGING
    ]


class PublicationDocumentAdmin(PublicationAdmin):
    format_tag_defaults = ["DOWNLOAD_PDF"]
    list_display = ["get_master_id", "get_landing_ancestors_admin_links", "title", "code", "url", "status", "is_published", "is_up_to_date", "get_published_time"
    # "published_to_solr" # COULD BE USED FOR DEBUGGING
    ]

admin.site.register(Publication, PublicationAdmin)
admin.site.register(PlanningMagArticle, PlanningMagArticleAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(PublicationDocument, PublicationDocumentAdmin)
