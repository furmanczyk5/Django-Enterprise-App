from django.contrib import admin
from django.contrib.staticfiles.templatetags.staticfiles import static
import nested_admin

from reversion.admin import VersionAdmin

from content.admin import MasterContentAdmin, ContentAdmin, \
    ContentTagTypeInline,  TaxoTopicTagInline, JurisdictionInline, \
    CommunityTypeInline, get_FormatInline, CollectionRelationshipInline, \
    SearchTopicInline
from content.models import TagType, ContentTagType
from store.admin import ProductInline

from .forms import UploadMediaAdminForm
from .models import MediaImageMasterContent, Media, Document, Image, Video, \
    Audio


class MediaImageMasterContentAdmin(MasterContentAdmin):

    readonly_fields = ["to_html", "img_thumbnail_html", "content_live", "content_draft", "published_time"]
    list_display = ["img_thumbnail_html", "__str__", "content_type", "publish_status"]

    fieldsets = [
        (None, {
            "fields": (
                "to_html",
                "content_live",
                "content_draft",
                "published_time"
            ),
        }),
    ]

    def content_type(self, obj):
        if obj.content_live is not None:
            return obj.content_live.content_type
        elif obj.content_draft is not None:
            return obj.content_draft.content_type
        else:
            try:
                return obj.content.all()[0].content_type
            except:
                return None

    def publish_status(self, obj):
        if obj.content_live is not None:
            return "Published"
        elif obj.content_draft is not None:
            return "Draft"
        else:
            return "Submission"


class MediaAdmin(ContentAdmin, VersionAdmin):

    list_display = ["img_thumbnail_html_small", "get_master_id", "title", "media_format", "resource_url", "url_source", "is_published"]
    list_display_links = ["get_master_id", "img_thumbnail_html_small"]

    list_filter = ["media_format"]
    search_fields = ["master__id", "title", "resource_url"]
    readonly_fields = ["img_thumbnail_html", "img_thumbnail_html_small"]

    filter_horizontal = ('permission_groups',)
    show_sync_harvester = False

    fieldsets = [
        (None, {
            "fields":(
                "media_format",
                "uploaded_file",
                ("img_thumbnail_html", "image_file"),
                ("resource_url", "url_source"),
                "title",
                "description",
                "text",
                "permission_groups",
                "show_content_without_groups",
            ),
        }),
        ("Taxonomy", {
            "classes":( "grp-collapse grp-closed",),
            "fields":(  "abstract",
                        "resource_type",
                        ("serial_pub","volume_number","issue_number"),
                        "language",
                        "resource_published_date",
                        "copyright_date",
                        "copyright_statement",
                        "isbn",
            )
        })
    ]

    class Media:
        # js = ['/static/content/js/tinymce/tinymce.min.js', '/static/content/js/tinymce/tinymce_setup.js',]
        js = (
            "//ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js",
            static("ckeditor/ckeditor.js"),
            # static("ckeditor/plugins/lite/lite-interface.js")
        )
        css = {
             'all': ( static("ckeditor/plugins/planning_media/admin.css"), )
        }

    inlines = [
        TaxoTopicTagInline, JurisdictionInline, CommunityTypeInline,
        SearchTopicInline, ContentTagTypeInline, ProductInline,
        CollectionRelationshipInline
    ]

    format_tag_defaults = []
    format_tag_choices = []

    actions = []
    form = UploadMediaAdminForm

    def user_has_publish_permission(self, request):
        return True

    def save_model(self, request, obj, form, change):

        super().save_model(request, obj, form, change)

        # for setting default format_tags
        if self.format_tag_defaults:
            format_tagtype = TagType.objects.prefetch_related("tags").get(code="FORMAT")
            format_contenttagtype, is_created = ContentTagType.objects.get_or_create(content=obj, tag_type=format_tagtype)
            format_contenttagtype.tags.add(*[t for t in format_tagtype.tags.all() if t.code in self.format_tag_defaults])

    def get_master_id(self,obj):
        return obj.master_id
    get_master_id.short_description = "Master"
    get_master_id.admin_order_field = "master__id"

media_proxy_list_filter = ["file_type", "url_source"] # figure out way to have relevant filter options for each proxy model

class DocumentAdmin(nested_admin.NestedModelAdmin, MediaAdmin):

    list_filter = media_proxy_list_filter
    list_display = ["img_thumbnail_html_small", "get_master_id", "title", "media_format", "resource_url", "url_source",
                        "is_published", "status"]

    format_tag_defaults = []
    format_tag_choices = ["FORMAT_ARTICLE", "FORMAT_ON_DEMAND_EDUCATION", "FORMAT_REPORT", "FORMAT_TOOLKIT"]
    inlines = [
        TaxoTopicTagInline, JurisdictionInline, CommunityTypeInline,
        get_FormatInline(tag_codes=format_tag_choices), SearchTopicInline,
        ContentTagTypeInline, ProductInline, CollectionRelationshipInline
    ]

    fieldsets = [
        (None, {
            "fields":(
                "uploaded_file",
                ("img_thumbnail_html", "image_file"),
                ("resource_url", "url_source"),
                "title",
                "status",
                "description",
                "text",
                "permission_groups",
                "show_content_without_groups",
                "template",
            ),
        }),
        ("Taxonomy", {
            "classes":( "grp-collapse grp-closed",),
            "fields":(  "abstract",
                        "resource_type",
                        ("serial_pub","volume_number","issue_number"),
                        "language",
                        "resource_published_date",
                        "copyright_date",
                        "copyright_statement",
                        "isbn",
            )
        })
    ]

    class Media:
        # js = ['/static/content/js/tinymce/tinymce.min.js', '/static/content/js/tinymce/tinymce_setup.js',]
        js = (
            "//ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js",
            static("ckeditor/ckeditor.js"),
            # static("ckeditor/plugins/lite/lite-interface.js")
        )
        css = {
             'all': ( static("ckeditor/plugins/planning_media/admin.css"), )
        }

class ImageAdmin(MediaAdmin):

    list_filter = media_proxy_list_filter

    fieldsets = [
        (None, {
            "fields":(
                ("img_thumbnail_html", "image_file"),
                ("resource_url", "url_source"),
                "title",
                "description",
                "permission_groups"
            ),
        }),
        ("Taxonomy", {
            "classes":( "grp-collapse grp-closed",),
            "fields":(  "abstract",
                        "resource_type",
                        ("serial_pub","volume_number","issue_number"),
                        "language",
                        "resource_published_date",
                        "copyright_date",
                        "copyright_statement",
                        "isbn",
            )
        })
    ]

    # def get_form(self, request, obj=None, **kwargs):
    #     # if request.user.groups.filter(name='staff-editor').exists():
    #     #     kwargs['form'] = ContentAdminEditorForm
    #     # else:
    #     #     kwargs['form'] = ContentAdminAuthorForm
    #     # return super(ContentAdmin, self).get_form(request, obj, **kwargs)
    #     return ImageMediaAdminForm


class VideoAdmin(MediaAdmin):

    list_filter = media_proxy_list_filter
    format_tag_defaults = ["FORMAT_VIDEO"]
    format_tag_choices = ["FORMAT_ON_DEMAND_EDUCATION"]
    inlines = [
        TaxoTopicTagInline, JurisdictionInline, CommunityTypeInline,
        get_FormatInline(tag_codes=format_tag_choices), SearchTopicInline,
        ContentTagTypeInline, CollectionRelationshipInline
    ]

    fieldsets = [
        (None, {
            "fields": (
                "uploaded_file",
                ("img_thumbnail_html", "image_file"),
                ("resource_url", "url_source"),
                "title",
                "status",
                "description",
                "text",
                "permission_groups"
            ),
        }),
        ("Taxonomy", {
            "classes": ("grp-collapse grp-closed",),
            "fields": (
                "abstract",
                "resource_type",
                ("serial_pub","volume_number", "issue_number"),
                "language",
                "resource_published_date",
                "copyright_date",
                "copyright_statement",
                "isbn",
            )
        })
    ]

    class Media:
        # js = ['/static/content/js/tinymce/tinymce.min.js', '/static/content/js/tinymce/tinymce_setup.js',]
        js = (
            "//ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js",
            static("ckeditor/ckeditor.js"),
            # static("ckeditor/plugins/lite/lite-interface.js")
        )
        css = {
             'all': (static("ckeditor/plugins/planning_media/admin.css"), )
        }


class AudioAdmin(MediaAdmin):

    list_filter = media_proxy_list_filter
    format_tag_defaults = ["FORMAT_AUDIO"]
    format_tag_choices = ["FORMAT_ON_DEMAND_EDUCATION"]
    inlines = [
        TaxoTopicTagInline, JurisdictionInline, CommunityTypeInline,
        get_FormatInline(tag_codes=format_tag_choices), SearchTopicInline,
        ContentTagTypeInline, ProductInline,
        CollectionRelationshipInline
    ]

    fieldsets = [
        (None, {
            "fields":(
                "uploaded_file",
                ("img_thumbnail_html", "image_file"),
                ("resource_url", "url_source"),
                "title",
                "status",
                "description",
                "permission_groups"
            ),
        }),
        ("Taxonomy", {
            "classes":( "grp-collapse grp-closed",),
            "fields":(  "abstract",
                        "resource_type",
                        ("serial_pub","volume_number","issue_number"),
                        "language",
                        "resource_published_date",
                        "copyright_date",
                        "copyright_statement",
                        "isbn",
            )
        })
    ]


admin.site.register(Media, MediaAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(Audio, AudioAdmin)
admin.site.register(MediaImageMasterContent, MediaImageMasterContentAdmin)
