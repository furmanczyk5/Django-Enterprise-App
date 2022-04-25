
from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.db.models import Q
from django.http.response import HttpResponseRedirect
from django.utils import timezone
from sentry_sdk import capture_exception, capture_message

from myapa.admin import ContactRoleInlineContact
from .admin_abstract import BaseContentAdmin
from .admin_publishable import AdminPublishableMixin
from .forms import MessageTextAdminForm, EmailTemplateAdminForm, \
    ContentTagTypeAdminForm, JurisdictionContentTagTypeAdminForm, \
    ContentAdminEditorForm, CommunityTypeContentTagTypeAdminForm, \
    ContentAdminAuthorForm, CollectionRelationshipAdminInlineForm, \
    SearchTopicTypeContentTagTypeAdminForm
from .mail import Mail
from .models import Content, TagType, Tag, ContentTagType, \
    FormatContentTagType, JurisdictionContentTagType, \
    CommunityTypeContentTagType, MenuItem, TaxoTopicTag, EmailTemplate, \
    MasterContent, SerialPub, MessageText, CONTENT_TYPES
from .tasks import make_content_public_task, make_content_inactive_task

CKEDITOR_STATIC_PATH = "ckeditor/ckeditor.js"


class TagInline(admin.StackedInline):
    model = Tag
    extra = 0
    fieldsets = BaseContentAdmin.fieldsets[:]
    fieldsets.insert(1, ("", {
        "fields": ("pk", "tag_type", "parent", "related", "sort_number", "taxo_term")
    }))

    readonly_fields = ["pk", "created_by", "created_time", "updated_by", "updated_time"]

    # TO DO: use auto complete for the parent lookup (rather than drop-down)... for some reason this isn't working:
    raw_id_fields = ['parent']
    autocomplete_lookup_fields = {'fk': ['parent']}

    filter_horizontal = ('related',)


class ContentTagTypeInline(admin.TabularInline):
    model = ContentTagType
    extra = 0
    classes = ("grp-collapse grp-closed",)

    form = ContentTagTypeAdminForm

    filter_horizontal = ('tags',)
    readonly_fields = []

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        to remove the option to add search_topics and taxo_mastertopics through this Inline
        """
        if db_field.name == "tag_type":
            kwargs["queryset"] = TagType.objects.exclude(code__in=["TAXO_MASTERTOPIC", "JURISDICTION", "COMMUNITY_TYPE", "FORMAT", "SEARCH_TOPIC"])
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        return super().get_queryset(request).exclude(tag_type__code__in=["TAXO_MASTERTOPIC", "JURISDICTION", "COMMUNITY_TYPE", "FORMAT", "SEARCH_TOPIC"]).order_by("tag_type__sort_number","tag_type__title")


def get_FormatInline(tag_codes=None):
    """
    function to generate Tabular inline class for Format TagType
    the queryset for tags will be limited to the tag_codes parameter
    """

    class FormatInline(admin.TabularInline):

        model = FormatContentTagType
        extra = 1
        max_num = 1
        filter_horizontal = ('tags',)
        classes = ("grp-collapse grp-closed",)
        fields = ("tags",)

        tag_code_choices = tag_codes

        def formfield_for_manytomany(self, db_field, request, **kwargs):
            if db_field.name == "tags":
                if tag_codes:
                    kwargs["queryset"] = Tag.objects.filter(tag_type__code="FORMAT", code__in=self.tag_code_choices)
                else:
                    kwargs["queryset"] = Tag.objects.filter(tag_type__code="FORMAT")
            return super().formfield_for_manytomany(db_field, request, **kwargs)

    return FormatInline


class JurisdictionInline(admin.TabularInline):
    model = JurisdictionContentTagType
    extra = 1
    max_num = 1
    filter_horizontal = ('tags',)
    form = JurisdictionContentTagTypeAdminForm
    classes = ("grp-collapse grp-closed",)


class CommunityTypeInline(admin.TabularInline):
    model = CommunityTypeContentTagType
    extra = 1
    max_num = 1
    filter_horizontal = ('tags',)
    form = CommunityTypeContentTagTypeAdminForm
    classes = ("grp-collapse grp-closed",)


class TaxoTopicTagInline(admin.TabularInline):
    model = Content.taxo_topics.through
    extra = 0
    raw_id_fields = ['taxotopictag']
    autocomplete_lookup_fields = {'fk': ['taxotopictag']}
    verbose_name = "Taxonomy Topic"
    verbose_name_plural = "Taxonomy Topics"
    min_num = 0

    # after adding this makes it disappear, but does not make it disappear from
    # raw_id_fields search widget queryset
    # def get_queryset(self, request):
    #     return super().get_queryset(request).filter(taxotopictag__status__in=["A"])


class TaxoTopicTagInlineRequired(admin.TabularInline):
    model = Content.taxo_topics.through
    extra = 1
    raw_id_fields = ['taxotopictag']
    autocomplete_lookup_fields = {'fk': ['taxotopictag']}
    verbose_name = "Taxonomy Topic (required)"
    verbose_name_plural = "Taxonomy Topics (required)"
    min_num = 1


class SearchTopicInline(admin.TabularInline):
    model = ContentTagType
    extra = 0
    max_num = 0
    verbose_name = "Search topic tagging"
    verbose_name_plural = "Search topic tagging"
    classes = ("grp-collapse grp-closed",)

    form = SearchTopicTypeContentTagTypeAdminForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "tag_type":
            kwargs["queryset"] = TagType.objects.filter(code="SEARCH_TOPIC")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(tag_type__code="SEARCH_TOPIC").order_by("tag_type__sort_number","tag_type__title")

    def get_readonly_fields(self, request, obj=None):
        return list(set(
            ['tag_type'] + [field.name for field in self.opts.local_many_to_many]
        ))

    def has_delete_permission(self, request, obj=None):
        return False


class TagListFilter(admin.SimpleListFilter):

    title = 'Tag'
    parameter_name = 'tag'

    def lookups(self, request, model_admin):
        tags = Tag.objects.exclude(tag_type__code="TAXO_MASTERTOPIC").order_by("tag_type__title", "title").select_related("tag_type")
        filter_tags = []

        current_tag_type_code = ""
        for tag in tags:
            tag_type_code = tag.tag_type.code
            if tag_type_code != current_tag_type_code:
                current_tag_type_code = tag_type_code
                tag_type_filter = ("TAGTYPE.%s" % tag_type_code, tag.tag_type.title)
                filter_tags.append(tag_type_filter)
            tag_filter = ("TAG.%s" % tag.code, "- - %s" % tag.title)
            filter_tags.append(tag_filter)

        return filter_tags

    def queryset(self, request, queryset):
        if self.value():
            filter_array = self.value().split(".")
            if filter_array[0] == "TAGTYPE":
                return queryset.filter(tag_types__code=filter_array[1])
            else:
                return queryset.filter(contenttagtype__tags__code=filter_array[1])


class PublishStatusListFilter(admin.SimpleListFilter):
    """
    List filter for publish status
    """
    title = 'Publish Status'
    parameter_name = 'publish_status'

    def lookups(self, request, model_admin):
        lookup_tuple = ((None, "Draft"),)

        if request.user.groups.filter(name="staff").exists():
            lookup_tuple += (
                ("SUBMISSION", "Submission"),
                ("PUBLISHED", "Published (For Debugging Purposes Only)")
            )
        return lookup_tuple

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset.filter(publish_status="DRAFT")
        else:
            return queryset.filter(publish_status=self.value())


class ArchivedStatusListFilter(admin.SimpleListFilter):
    """
    List filter for archived status
    """
    title = 'Archived Status'
    parameter_name = 'archive_time'

    def lookups(self, request, model_admin):
        return (
            ("ARCHIVED","Archived"),
            ("NOT_ARCHIVED", "Not Archived")
        )

    def queryset(self, request, queryset):
        datetime_now = timezone.now()
        if self.value() == "ARCHIVED":
            return queryset.filter(archive_time__lt=datetime_now)
        elif self.value() == "NOT_ARCHIVED":
            return queryset.filter(Q(archive_time__gt=datetime_now) | Q(archive_time__isnull=True))
        else:
            return queryset


class MasterContentTypeFilter(admin.SimpleListFilter):

    title = 'Content Type'
    parameter_name = 'search_topic'

    def lookups(self, request, model_admin):
        return CONTENT_TYPES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(content__content_type=self.value())


class MasterContentAdmin(admin.ModelAdmin):

    readonly_fields = ["content_draft", "content_live", "published_time"]
    search_fields = ["=id", "content_draft__title", "content_draft__url", "content_draft__code"]
    list_display = ["id", "content_draft", "get_url", "get_content_type"]
    list_filter = [MasterContentTypeFilter]

    def get_queryset(self, request):
        # ALL CONTENT RECORDS PUBLISHED, DRAFT, AND SUBMISSIONS
        qs = super().get_queryset(request)
        return qs.select_related("content_draft")

    def get_url(self, obj):
        if obj.content_draft is not None:
            return obj.content_draft.url
        else:
            return ""
    get_url.short_description="Url"

    def get_content_type(self, obj):
        if obj.content_draft is not None:
            return obj.content_draft.content_type
        else:
            return ""
    get_content_type.short_description = "Content Type"


    # def publish_status(self, obj):
    #     if obj.content_live is not None:
    #         return "Published"
    #     elif obj.content_draft is not None:
    #         return "Draft"
    #     else:
    #         return "Submission"

class CollectionRelationshipInline(admin.TabularInline):
    # model = CollectionRelationship
    model = Content.related.through
    form = CollectionRelationshipAdminInlineForm
    extra = 0
    fields = ("content_master_related", )
    verbose_name = "Knowledgebase Collection"
    verbose_name_plural = "Knowledgebase Collections"
    # raw_id_fields = ("content_master_related",)
    # autocomplete_lookup_fields = {'fk': ['content_master_related']}

    def get_queryset(self, request):
        return super().get_queryset(request).filter(relationship="KNOWLEDGEBASE_COLLECTION")

    def formfield_for_foreignkey(self, db_field, *args, **kwargs):
        field = super().formfield_for_foreignkey(db_field, *args, **kwargs)
        if db_field.name == "content_master_related":
            field.queryset = field.queryset.filter(
                content_draft__content_type="KNOWLEDGEBASE_COLLECTION"
            ).order_by('content__title').distinct()
        return field

# NOTE... ContactRoleInline stuff is included here (instead of in myapa app)... because both this content admin and myapa admin need it
class ContentAdmin(AdminPublishableMixin, BaseContentAdmin):

    list_display = ("get_master_id", "title", "content_type", "status",
                    "is_published", "is_up_to_date", "workflow_status",
                    "get_published_time")

    list_display_links = ("get_master_id", "title")

    list_filter = ("content_type", "status", TagListFilter,
                   ArchivedStatusListFilter)

    search_fields = ("=master__id", "title", "=code", "url")

    filter_horizontal = ("permission_groups",)

    readonly_fields = BaseContentAdmin.readonly_fields + (
        "master", "featured_image_display", "thumbnail_html", "thumbnail_2_html",
        "publish_status", "get_published_time")

    raw_id_fields = ("parent", "featured_image",  "parent_landing_master", "og_image")

    autocomplete_lookup_fields = {
        "fk": ("parent", "featured_image", "parent_landing_master", "og_image")
    }

    inlines = (TaxoTopicTagInline, JurisdictionInline, CommunityTypeInline,
               SearchTopicInline, ContentTagTypeInline, ContactRoleInlineContact,
               CollectionRelationshipInline)

    format_tag_choices = [] # default: nothing
    format_tag_defaults = [] # default: nothing
    author_form_class = ContentAdminAuthorForm
    editor_form_class = ContentAdminEditorForm

    revision_form_template = "admin/content/content/revision-form.html"
    change_form_template = "admin/content/content/change-form.html"

    fieldsets = [
        (None, {
            "fields": (
                "title",
                "text",
                ("parent_landing_master", "url"),
                "description",
            )
        }),
        ("Advanced Content Management Settings", {
            "classes": ("grp-collapse grp-closed",),
            "fields": (
                ("subtitle",),
                ("overline",),
                ("content_area",),
                ("template", "status"),
                ("resource_url",),
                ("code",),
                ("featured_image", "featured_image_display",),
                "featured_image_caption",
                ("thumbnail", "thumbnail_html"),
                ("thumbnail_2", "thumbnail_2_html"),
                ("publish_time", "make_public_time",),
                ("archive_time", "make_inactive_time",),
                ("workflow_status", "editorial_comments"),
                ("parent", "slug"),
                ("permission_groups",),
                ("show_content_without_groups",),
                "keywords",
                "structured_data_markup",
                ("og_title", "og_url"),
                ("og_type", "og_image"),
                ("og_description",)
            )
        })
    ]

    def get_actions(self, request):
        """
        Built-in django hook that gets the actions for the admin mass action dropdown in lower left...
        for content, we are disabling the mass "delete" action.
        Also, see PublishableAdminMixin for super() actions related to publishing...
        """
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def has_delete_permission(self, request, obj=None):
        return False

    def get_form(self, request, obj=None, **kwargs):
        if request.user.groups.filter(name="staff-editor").exists():
            kwargs['form'] = self.editor_form_class
        else:
            kwargs['form'] = self.author_form_class
        return super(ContentAdmin, self).get_form(request, obj, **kwargs)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            publish_status="DRAFT"
        ).select_related("master", "master__content_live")

    def save_model(self, request, obj, form, change):
        """
        If editor schedules content to be pubished, made public, archived or made inactive,
        appropriate actions are taken and Celery schedules the appropriate cron job.
        if editor changes workflow_status to "needs work" original author
        receives auto email. All editors receive auto-email when workflow_status
        is set to "needs review."
        """
        save_return = super().save_model(request, obj, form, change)

        self.handle_publish_tasks(form, obj)
        self.handle_workflow(form, obj)

        self.assign_default_format_tags(obj)

        return save_return

    @staticmethod
    def handle_workflow(form, obj):
        try:
            if obj.content_type == "PAGE" and "workflow_status" in form.changed_data:
                mail_context = {
                    "content": obj,
                    "SERVER_ADDRESS": settings.SERVER_ADDRESS
                }

                if obj.workflow_status == "NEEDS_REVIEW":
                    editor_list = User.objects.filter(groups__name="staff-cms-editor")
                    editor_email_list = [a_user.email for a_user in editor_list if a_user.email]
                    email_template = "CMS_CONTENT_NEEDS_REVIEW"
                    Mail.send(email_template, editor_email_list, mail_context)
                elif obj.workflow_status == "NEEDS_WORK":
                    author_email_list = [obj.created_by.contact.email]
                    email_template = "CMS_CONTENT_NEEDS_WORK"
                    Mail.send(email_template, author_email_list, mail_context)
        except Exception as e:
            capture_exception(e)

    @staticmethod
    def handle_publish_tasks(form, obj):
        kwargs = {}
        try:
            if "publish_time" in form.changed_data:
                try:
                    kwargs['eta'] = obj.publish_time
                    if obj.is_solr_publishable:
                        kwargs['solr_publish'] = True
                    obj.publish_async(**kwargs)
                except Exception as e:
                    capture_message("Couldn't call publish_content_task: %s" % e)
            elif "make_public_time" in form.changed_data:
                try:
                    make_content_public_task.apply_async((obj.__class__, obj.id), eta=obj.make_public_time)
                except Exception as e:
                    capture_message("Couldn't call make_content_public_task: %s" % e)
            elif "make_inactive_time" in form.changed_data:
                try:
                    make_content_inactive_task.apply_async((obj.__class__, obj.id), eta=obj.make_inactive_time)
                except Exception as e:
                    capture_message("Couldn't call make_content_inactive_task: %s" % e)
        except Exception as e:
            capture_exception(e)

    # response_add and response_change are the only methods called after the form and all formsets have been saved,
    def response_add(self, request, obj):
        obj.taxo_topic_tags_save()
        if "_continue" in request.POST:
            return HttpResponseRedirect("../%s" % obj.id)
        return super().response_add(request, obj)

    def response_change(self, request, obj):
        obj.taxo_topic_tags_save()
        return super().response_change(request, obj)

    def get_master_id(self,obj):
        return obj.master_id
    get_master_id.short_description = "Master"
    get_master_id.admin_order_field = "master__id"

    def get_published_time(self,obj):
        if obj.master.content_live:
            return obj.master.content_live.published_time
    get_published_time.short_description = "Published time"
    get_published_time.admin_order_field = "master__content_live__published_time"

    def featured_image_display(self, obj):
        image = obj.featured_image.content.filter(publish_status=obj.publish_status).first()
        return image.media.to_html() if image else ""
    featured_image_display.allow_tags = True
    featured_image_display.short_description = ""

    def assign_default_format_tags(self, obj):
        """
        method to assign default format tags, in most cases just use the format_tag_defaults attribute,
        but for more complex cases override this method
        """
        if self.format_tag_defaults:
            format_tagtype = TagType.objects.prefetch_related("tags").get(code="FORMAT")
            format_contenttagtype, is_created = ContentTagType.objects.get_or_create(content=obj, tag_type=format_tagtype)
            format_contenttagtype.tags.add(*[t for t in format_tagtype.tags.all() if t.code in self.format_tag_defaults])

    class Media:
        js = (
            "//ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js",
            static("content/js/jquery-ui.min.js"),
            static(CKEDITOR_STATIC_PATH),
            # static("ckeditor/plugins/lite/lite-interface.js"),
            static('content/js/ckeditor-pastefromword.js'),
            static("ui/modal/js/modal.js"),
            static("prettydiff/lib/language.js"),
            static("prettydiff/lib/finalFile.js"),
            static("prettydiff/lib/safeSort.js"),
            static("prettydiff/ace/ace.js"),
            static("prettydiff/api/dom.js"),
            static("prettydiff/lib/csspretty.js"),
            static("prettydiff/lib/csvpretty.js"),
            static("prettydiff/lib/diffview.js"),
            static("prettydiff/lib/jspretty.js"),
            static("prettydiff/lib/markuppretty.js"),
            static("prettydiff/prettydiff.js"),

            static("prettydiff/adminSetup.js")
        )
        css = {
             'all': (
                static("ckeditor/plugins/planning_media/admin.css"),
                static("ui/modal/css/modal.css"),
                static("prettydiff/css/global.css"),
                static("prettydiff/css/reports.css"),
                static("prettydiff/css/color_white.css"),
                static("prettydiff/css/color_canvas.css"),
                static("prettydiff/css/color_shadow.css"),
                static("prettydiff/css/page_specific.css"))
        }


class MenuItemAdmin(admin.ModelAdmin):
    search_fields = ("url", "master__content_draft__url", "title")

    readonly_fields = ["id", "created_by", "created_time", "updated_by", "updated_time"]

    sortable_field_name = "sort_number"

    raw_id_fields = ("master", "parent",)
    autocomplete_lookup_fields = {"fk": ["master", "parent"] }

    list_display = ("title", "get_url", "get_content")
    list_display_links = ("title",)

    fields = (
            ("id", "code"),
            ("title"),
            ("master", "url"),
            ("parent"),
            ("status"),
            ("sort_number"),
            ("created_by", "created_time"),
            ("updated_by", "updated_time"),
        )

    def get_url(self, obj):
        if obj.master and obj.master.content_draft:
            # TO DO... link to the actual page
            return obj.master.content_draft.url
        else:
            return obj.url
    get_url.short_description = "Url"

    def get_content(self, obj):
        if obj.master and obj.master.content_draft:
            # TO DO... link to the actual page
            return obj.master.content_draft.title
        else:
            return ""
    get_content.short_description = "Associated Content"

    def get_landing_ancestors_admin_links(self, obj):
        return obj.parent_landing_page.get_landing_ancestors_admin_links()
    get_landing_ancestors_admin_links.short_description = "Section Heirarchy"
    get_landing_ancestors_admin_links.allow_tags = True


class MenuItemInline(admin.StackedInline):
    model = MenuItem
    extra = 0

    readonly_fields = ["id", "created_by", "created_time", "updated_by", "updated_time"]

    sortable_field_name = "sort_number"

    raw_id_fields = ("master", "parent",)
    autocomplete_lookup_fields = { "fk" : ["master", "parent"] }

    fields = (
            # ("id", "code"),
            ("title"),
            ("master", "url"),
            ("parent", "status", "sort_number"),
            # ("created_by", "created_time"),
            # ("updated_by", "updated_time"),
        )


class TagTypeAdmin(BaseContentAdmin):
    list_display = ("code", "title")
    list_display_links = ("code", "title")

    list_display = ["id", "code", "title", "sort_number"]
    list_display_links = ["title"]
    fieldsets = BaseContentAdmin.fieldsets[:]
    fieldsets.insert(1, ("Tag Type Fields",{
        "fields": ("parent", ("min_allowed", "max_allowed"), "sort_number")
        }))

    ordering = ("sort_number", "title")

    raw_id_fields = ["parent"]
    autocomplete_lookup_fields = {"fk" : ["parent"]}

    inlines = [TagInline]

    # Overriding the default get_queryset to exlude the TaxoTopic Tag Type from the list of
    # clickable options
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("parent").exclude(code__exact="TAXO_MASTERTOPIC")


class TagAdmin(BaseContentAdmin):

    list_display = ("id", "code", "title", "tag_type", "description")
    search_fields = ["=id", "title", "code", "tag_type__code", "tag_type__title", "=tag_type__id"]
    list_filter =  ["status", "tag_type"]
    list_display_links = ("id", "code", "title")

    fieldsets = BaseContentAdmin.fieldsets[:]
    fieldsets.insert(1, ("Tag Fields",{
        "fields": ("tag_type", "parent", "related", "sort_number", "taxo_term")
        }))

    raw_id_fields = ["parent"]
    autocomplete_lookup_fields = {"fk" : ["parent"]}

    filter_horizontal = ["related"]


class SearchTopicListFilter(admin.SimpleListFilter):

    title = 'Search Topic'
    parameter_name = 'search_topic'

    def lookups(self, request, model_admin):
        search_topics = Tag.objects.filter(tag_type__code="SEARCH_TOPIC")
        return [(tag.code, tag.title) for tag in search_topics]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(related__code=self.value())


class TaxoTopicTagAdminForm(forms.ModelForm):

    class Meta:
        model = TaxoTopicTag
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["related"].queryset = Tag.objects.filter(tag_type__code="SEARCH_TOPIC")


# Use this for now to return taxotopictags one page at a time
class TaxoTopicTagFlatAdmin(BaseContentAdmin):
    form = TaxoTopicTagAdminForm

    list_display = ("title", "description", "related_search_topics", "code", "taxo_term")
    search_fields = ["=id", "title", "code", ]
    list_filter = (SearchTopicListFilter,)

    fieldsets = BaseContentAdmin.fieldsets[:]
    fieldsets.insert(1, ("Tag Fields",{
        "fields": ("tag_type", "parent", "related", "sort_number", "taxo_term")
        }))

    raw_id_fields = ["parent"]
    autocomplete_lookup_fields = {"fk" : ["parent"]}
    filter_horizontal = ["related"]

    def related_search_topics(self, obj):
        return ", ".join([o.title for o in obj.related.all()])

    # filter_horizontal = ["related"]

    list_per_page = 50

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("parent").prefetch_related("related").only("id", "title", "code", "taxo_term", "parent", "description")


# Hierarchical Display
class TaxoTopicTagAdmin(BaseContentAdmin):

    list_display = ("qualified_title", "description")
    search_fields = ["=id", "title", "code", ]
    list_filter = (SearchTopicListFilter,)
    change_list_template = "admin/content/taxotopictag/change_list.html"

    fieldsets = BaseContentAdmin.fieldsets[:]
    fieldsets.insert(1, ("Tag Fields",{
        "fields": ("tag_type", "parent", "related", "sort_number", "taxo_term")
        }))

    raw_id_fields = ["parent"]
    autocomplete_lookup_fields = {"fk" : ["parent"]}

    # filter_horizontal = ["related"]

    list_per_page = 1000

    def qualified_title(self, obj):
        return obj.title if obj.status == 'A' else "(Inactive): " + obj.title

    def get_queryset(self, request):
        # TO DO / NOTE: there is a but with .only() and the get_admin_url / subclasssing in planning.models_subclassable ... need to investigate further...
        # (removing .only for now)
        # return super().get_queryset(request).select_related("parent").only("id", "title", "parent", "description")
        return super().get_queryset(request).select_related("parent").filter(status="A").order_by('title')


    class Media:
        js = (
            '//ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js',
            static('content/js/windowshade.js'))
        css = {
            'all': (static('content/css/change_list_tree.css'),)
        }


class SerialPubAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "title")

    fieldsets = [
        (None, {
            "fields":( "code",
                        "title",
                        "status",
                        "description"
            ),
        }),
    ]

class EmailTemplateAdmin(admin.ModelAdmin): #admin.ModelAdmin):
    # ...
    list_display = ('code', 'title', 'status', 'email_from', 'email_to', 'subject', 'body')

    form = EmailTemplateAdminForm

    fieldsets = [
        (None, {
            "fields":("code",
                      "title",
                      "status",
                      "email_from",
                      "email_to",
                      "subject",
                      "body",
                      ),
        }),
    ]


    def save_model(self, request, content, form, change):
        if not change:
            content.created_by = request.user

        content.updated_by = request.user
        super().save_model(request, content, form, change)

    class Media:
        # js = ['/static/content/js/tinymce/tinymce.min.js', '/static/content/js/tinymce/tinymce_setup.js',]
        js = (
            "//ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js",
            static(CKEDITOR_STATIC_PATH),
            # static("ckeditor/plugins/lite/lite-interface.js")
        )
        css = {
             'all': ( static("ckeditor/plugins/planning_media/admin.css"), )
        }


class MessageTextAdmin(BaseContentAdmin):
    # clashes with Content model:
    # readonly_fields = ["created_by", "created_time", "updated_by", "updated_time"]
    form = MessageTextAdminForm
    list_display = ("code", "title", "message_type", "message_level")
    fieldsets = [
        (None, {
            "fields":( ("message_type", "message_level"),
                "title",
                ("code", "status"),
                "text",
            ),
        }),
    ]

    class Media:
        # js = ['/static/content/js/tinymce/tinymce.min.js', '/static/content/js/tinymce/tinymce_setup.js',]
        js = (
            "//ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js",
            static(CKEDITOR_STATIC_PATH),
            # static("ckeditor/plugins/lite/lite-interface.js")
        )
        css = {
             'all': ( static("ckeditor/plugins/planning_media/admin.css"), )
        }

admin.site.register(Content, ContentAdmin)
# admin.site.register(PageContentPublished, PageAdminPublished)

admin.site.register(TagType, TagTypeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(TaxoTopicTag, TaxoTopicTagAdmin)
# admin.site.register(TaxoTopicTagFlat, TaxoTopicTagFlatAdmin)

admin.site.register(EmailTemplate, EmailTemplateAdmin)

admin.site.register(MasterContent, MasterContentAdmin)

# admin.site.register(Section, SectionAdmin)
admin.site.register(MenuItem, MenuItemAdmin)
admin.site.register(SerialPub, SerialPubAdmin)
admin.site.register(MessageText, MessageTextAdmin)
