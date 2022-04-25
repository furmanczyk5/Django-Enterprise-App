from django.contrib import admin
from django.core import urlresolvers
from django.contrib import messages
from django.contrib.admin.views.main import ChangeList

from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.utils.safestring import mark_safe

from reversion.admin import VersionAdmin

from content.models import MenuItem
from content.admin import ContentAdmin, MasterContentAdmin, MenuItemInline, \
    TaxoTopicTagInlineRequired, JurisdictionInline, CommunityTypeInline, \
    ContentTagTypeInline, TagListFilter, ArchivedStatusListFilter, CollectionRelationshipInline, \
    ContentAdminAuthorForm, ContentAdminEditorForm, SearchTopicInline

from .models import Page, UncategorizedPage, LandingPageMasterContent, \
    LandingPage, MembershipPage, KnowledgeCenterPage, ConferencesPage, \
    AICPPage, PolicyPage, CareerPage, OutreachPage, ConnectPage, AboutPage, AudioPage, VideoPage, JotFormPage


# TO DO... hard coding this until we can get models_subclassable working properly here... SHOULD REMOVE ONCE THAT'S WORKING
class PageAdminChangeList(ChangeList):
    """
    Used to create a custom url for admin results in order to link to specific admin subclass
    """
    def url_for_result(self, result):
        if hasattr(result, "landingpage"):
            return urlresolvers.reverse("admin:%s_%s_change" % ("pages", "landingpage"), args=(result.id,))
        else:
            return super().url_for_result(result)


class PageAdmin(ContentAdmin, VersionAdmin):
    list_filter = ("status", TagListFilter,
                   ArchivedStatusListFilter, "workflow_status")  # removes content_type from filters
    list_display = (
        "get_master_id",
        "get_landing_ancestors_admin_links",
        "title", "url", "status",
        "is_published", "is_up_to_date",
        "get_published_time", "workflow_status"
    )
    readonly_fields = ContentAdmin.readonly_fields + ('content_type',)
    inlines = (
        TaxoTopicTagInlineRequired, JurisdictionInline, CommunityTypeInline,
        SearchTopicInline, ContentTagTypeInline, CollectionRelationshipInline)
    change_form_template = "admin/pages/page/change-form.html" # using page change_form because of the checkin/checkout system

    format_tag_defaults = ["FORMAT_WEBPAGE"]

    show_sync_harvester = False

    # TO DO... hard coding this until we can get models_subclassable working properly here... SHOULD REMOVE ONCE THAT'S WORKING
    def get_changelist(self, request, **kwargs):
        return PageAdminChangeList

    def get_queryset(self, request):
        # OMG!!!!
        return super().get_queryset(request).select_related(
            "{0}__{0}__{0}__{0}__{0}".format("parent_landing_master__content_draft__landingpage"),
            "landingpage"
        )

    def response_add(self, request, obj):
        self.update_object_class(obj)
        admin_subsection = self.get_subsection(obj)
        obj.taxo_topic_tags_save()

        if ('/page/' in request.path or
                ('/uncategorizedpage/' and not obj.parent_landing_master)):
           return super().response_add(request, obj)

        if '_continue' in request.POST:
            return HttpResponseRedirect("../../{}/{}".format(admin_subsection, obj.id))

        if '_save' in request.POST or '_publish' in request.POST:
            super().response_add(request, obj)
            self.update_messages(request, obj, admin_subsection)
            return HttpResponseRedirect("../../{}".format(admin_subsection))

        return super().response_add(request, obj)

    def update_object_class(self, obj):
        subclass = Page.subclass_from_code(obj.content_area, obj.content_type)
        obj.__class__ = subclass

    def get_subsection(self, obj):
        return type(obj).__name__.lower()

    def update_messages(self, request, obj, subsection):
        removed_messages = list(messages.get_messages(request))
        if '_publish' in request.POST:
            messages.success(request, "Successfully published.")
        change_message = (
            'The page <a href="/admin/pages/{}/{}/change">"{}"</a> '
            'was successfully changed.'
        ).format(subsection, obj.id, obj.title)
        messages.success(request, mark_safe(change_message))

    class Media:
        js = ContentAdmin.Media.js + ("pages/checkin/js/admin-page-checkin.js",)
        css = {
            'all':ContentAdmin.Media.css.get("all") + ("pages/checkin/css/admin-page-checkin.css",)
        }

class ContentAreaPageAdmin(PageAdmin):
    readonly_fields = PageAdmin.readonly_fields + ("content_area",)

class ContentAreaPageAdminAuthorForm(ContentAdminAuthorForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent_landing_master'].required = True

class ContentAreaPageAdminEditorForm(ContentAdminEditorForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent_landing_master'].required = True

class MembershipPageAdmin(ContentAreaPageAdmin):
    author_form_class = ContentAreaPageAdminAuthorForm
    editor_form_class = ContentAreaPageAdminEditorForm

class KnowledgeCenterPageAdmin(ContentAreaPageAdmin):
    author_form_class = ContentAreaPageAdminAuthorForm
    editor_form_class = ContentAreaPageAdminEditorForm

class ConferencesPageAdmin(ContentAreaPageAdmin):
    author_form_class = ContentAreaPageAdminAuthorForm
    editor_form_class = ContentAreaPageAdminEditorForm

class AICPPageAdmin(ContentAreaPageAdmin):
    author_form_class = ContentAreaPageAdminAuthorForm
    editor_form_class = ContentAreaPageAdminEditorForm

class PolicyPageAdmin(ContentAreaPageAdmin):
    author_form_class = ContentAreaPageAdminAuthorForm
    editor_form_class = ContentAreaPageAdminEditorForm

class CareerPageAdmin(ContentAreaPageAdmin):
    author_form_class = ContentAreaPageAdminAuthorForm
    editor_form_class = ContentAreaPageAdminEditorForm

class OutreachPageAdmin(ContentAreaPageAdmin):
    author_form_class = ContentAreaPageAdminAuthorForm
    editor_form_class = ContentAreaPageAdminEditorForm

class AboutPageAdmin(ContentAreaPageAdmin):
    author_form_class = ContentAreaPageAdminAuthorForm
    editor_form_class = ContentAreaPageAdminEditorForm

class ConnectPageAdmin(ContentAreaPageAdmin):
    author_form_class = ContentAreaPageAdminAuthorForm
    editor_form_class = ContentAreaPageAdminEditorForm

class AudioPageAdmin(ContentAreaPageAdmin):
    author_form_class = ContentAreaPageAdminAuthorForm
    editor_form_class = ContentAreaPageAdminEditorForm

class VideoPageAdmin(ContentAreaPageAdmin):
    author_form_class = ContentAreaPageAdminAuthorForm
    editor_form_class = ContentAreaPageAdminEditorForm

class JotFormPageAdmin(ContentAreaPageAdmin):
    author_form_class = ContentAreaPageAdminAuthorForm
    editor_form_class = ContentAreaPageAdminEditorForm

class UncategorizedPageAdmin(ContentAreaPageAdmin):
    pass


class LandingPageAdmin(PageAdmin):

    fieldsets = [
        (None, {
            "fields":(  "title",
                        "text",
                        ("parent_landing_master", "url"),
                        "description",
                        ("featured_image", "featured_image_display",),
                        ("thumbnail", "thumbnail_html"),
                        # "has_xhtml", # now, everything has xhtml... we should remove this field from the model...
            ),
        }),
        ("Landing Page Search Results", {
            "classes":( "grp-collapse grp-closed",),
            "fields":(
                "show_search_results", "search_query", "sort_field", "search_max"
            )
        }),
        ("Advanced Content Management Settings", {
            "classes":( "grp-collapse grp-closed",),
            "fields":(
                ("content_area",),
                ("template", "status"),
                ("code", "resource_url"),
                ("publish_time", "make_public_time",),
                ("archive_time", "make_inactive_time",),
                ("workflow_status", "editorial_comments"),
                ("parent", "slug"),
                "permission_groups",
                "show_content_without_groups",
                "keywords",
                "structured_data_markup",
                ("og_title", "og_url"),
                ("og_type", "og_image"),
                ("og_description",)
            )
        }),
        ("Publication Data", {
            "classes":( "grp-collapse grp-closed",),
            "fields":(
                        "subtitle",
                        "abstract",
                        # ("resource_type",),
                        ("serial_pub","volume_number","issue_number"),
                        "language",
                        "resource_published_date",
                        "copyright_date",
                        "copyright_statement",
                        "isbn",
                        # "places", # inline?
                        # "related" # inline?
            )
        })
    ]

    inlines = ContentAdmin.inlines + (MenuItemInline,)

    def get_queryset(self, request):
        return super(PageAdmin, self).get_queryset(request).select_related(
            "{0}__{0}__{0}__{0}__{0}".format("parent_landing_master__content_draft__landingpage"),
        )

    # TO DO... hard coding this until we can get models_subclassable working properly here... SHOULD REMOVE ONCE THAT'S WORKING
    def get_changelist(self, request, **kwargs):
        return super(PageAdmin, self).get_changelist(request, **kwargs)


class LandingPageMasterContentAdmin(MasterContentAdmin):
    pass

    # readonly_fields = ["to_html", "img_thumbnail_html", "content_live", "content_draft", "published_time"]
    # list_display = ["img_thumbnail_html", "__str__", "content_type", "publish_status"]

    # fieldsets = [
    #     (None, {
    #         "fields":(
    #             "to_html",
    #             "content_live",
    #             "content_draft",
    #             "published_time"
    #         ),
    #     }),
    # ]

# Register your models here.
admin.site.register(MembershipPage, MembershipPageAdmin)
admin.site.register(KnowledgeCenterPage, KnowledgeCenterPageAdmin)
admin.site.register(ConferencesPage, ConferencesPageAdmin)
admin.site.register(AICPPage, AICPPageAdmin)
admin.site.register(PolicyPage, PolicyPageAdmin)
admin.site.register(CareerPage, CareerPageAdmin)
admin.site.register(OutreachPage, OutreachPageAdmin)
admin.site.register(AboutPage, AboutPageAdmin)
admin.site.register(ConnectPage, ConnectPageAdmin)
admin.site.register(AudioPage, AudioPageAdmin)
admin.site.register(VideoPage, VideoPageAdmin)
admin.site.register(JotFormPage, JotFormPageAdmin)
admin.site.register(UncategorizedPage, UncategorizedPageAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(LandingPage, LandingPageAdmin)
admin.site.register(LandingPageMasterContent, LandingPageMasterContentAdmin)
