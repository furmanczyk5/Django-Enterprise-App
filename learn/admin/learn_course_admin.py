from django.contrib import admin

from content.models.content_relationship import ContentRelationship
from content.models.tagging import ContentTagType
from content.admin import TaxoTopicTagInline, JurisdictionInline, CommunityTypeInline, \
    ContentTagTypeInline, get_FormatInline, ContactRoleInlineContact, \
    CollectionRelationshipInline
from events.admin import EventAdmin
from events.utils.exports import national_export_xlsx
from store.admin import ProductInline
from comments.admin import CommentAdmin
from learn.models.learn_course import LearnCourse, LearnCourseBundle
from learn.models.group_license import GroupLicense
from learn.models.learn_evaluation import LearnCourseEvaluation
from learn.models.learn_course_info import LearnCourseInfo

class LearnCourseInfoInline(admin.StackedInline):
    model = LearnCourseInfo
    extra = 0
    can_delete = True

    raw_id_fields = ["activity", "learncourse"]

    fieldsets = [
        (None, {
            "fields": (
                ("learncourse"),
                ("run_time", "run_time_cm", "vimeo_id"),
                ("lms_course_id", "lms_template", "lms_product_page_url"),
            )
        }),
    ]

    verbose_name = "LMS Integration Information"
    verbose_name_plural = "LMS Integration Information"


class LearnCourseAdmin(EventAdmin):
    """
    Admin for APA Learn Records
    """
    readonly_fields = EventAdmin.readonly_fields + ('event_type',)
    list_filter = [x for x in EventAdmin.list_filter if x not in ["event_type"]] # removes event_type from filters
    format_tag_defaults = ["FORMAT_APA_LEARN"]
    list_display = EventAdmin.list_display + (
        "get_featured_content", "get_track", "get_vimeo")
    actions = [national_export_xlsx]


    def get_featured_content(self, obj):
        ctt=ContentTagType.objects.filter(content=obj, tag_type__title__contains="Featured").first()
        featured = ctt.tags.first() if ctt else None
        return featured if featured else "None"
    get_featured_content.short_description = "Featured"

    def get_track(self, obj):
        ctt=ContentTagType.objects.filter(content=obj, tag_type__code__contains="TRACK").first()
        track = ctt.tags.first() if ctt else None
        return track if track else "None"
    get_track.short_description = "Program Area (formerly Track)"

    def get_vimeo(self, obj):
        lci = LearnCourseInfo.objects.filter(learncourse=obj).first()
        vimeo_id = lci.vimeo_id if lci else None
        return vimeo_id if vimeo_id else "None"
    get_vimeo.short_description = "Vimeo ID"

class ContentRelationshipInline(admin.StackedInline):
    model = ContentRelationship
    fk_name = "content"
    extra = 0
    can_delete = True

    raw_id_fields = ["content", "content_master_related"]

    readonly_fields = ["get_course_title", "get_related_event_type"]

    fieldsets = [
        (None, {
            "fields": (
                ("content"),
                ("content_master_related", "get_course_title"),
                ("relationship", "get_related_event_type"),
            )
        }),
    ]

    def get_course_title(self, obj):
        return obj.content_master_related.content_draft.title
    get_course_title.short_description = "Course Title"

    def get_related_event_type(self, obj):
        return obj.content_master_related.content_draft.event.event_type
    get_related_event_type.short_description = "Related Event Type"


class LearnCourseBundleAdmin(EventAdmin):
    """
    Admin for APA Learn Bundles
    """
    readonly_fields = EventAdmin.readonly_fields + ('event_type',)
    list_filter = [x for x in EventAdmin.list_filter if x not in ["event_type"]] # removes event_type from filters
    format_tag_defaults = ["FORMAT_APA_LEARN"]

    inlines = EventAdmin.inlines + [ContentRelationshipInline,]


class LearnCourseEvaluationAdmin(CommentAdmin):
    # including content in search fields breaks Django
    search_fields = [
    "=id",
    "=contact__user__username",
    # "=content__master_id",
    # "=contactrole__content__master_id",
    "=contactrole__contact__user__username"
    ]


admin.site.register(LearnCourse, LearnCourseAdmin)
admin.site.register(LearnCourseBundle, LearnCourseBundleAdmin)
admin.site.register(LearnCourseEvaluation, LearnCourseEvaluationAdmin)
