from .submission import SubmissionAdmin
from knowledgebase.admin_content.filters import (
    CollectionFilter
)
from knowledgebase.admin_content.publishing import publishing_for_first_time
from knowledgebase.forms.admin.inlines import StoryReviewInline
from knowledgebase.forms.admin.forms import (
    SubmissionAdminAuthorForm,
    SubmissionAdminEditorForm
)
from knowledgebase.mail import (
    send_story_published_email,
    send_story_rejected_email
)
from knowledgebase.models import StoryReview
from knowledgebase.tags import add_member_story_tag
from content.admin import (
    TaxoTopicTagInline,
    JurisdictionInline,
    CommunityTypeInline,
    ContentTagTypeInline,
    CollectionRelationshipInline,
    SearchTopicInline
)
from myapa.admin import ContactRoleInlineContact
from places.admin import ContentPlaceInline


REJECTED_RESOURCE_STATUSES = [
    'REVIEW_COMPLETE_DUPLICATIVE',
    'REVIEW_COMPLETE_OFF_TOPIC'
]


class StoryAdmin(SubmissionAdmin):
    list_filter = ('status', CollectionFilter)
    inlines = (
        TaxoTopicTagInline, JurisdictionInline, CommunityTypeInline,
        SearchTopicInline, ContentTagTypeInline, ContentPlaceInline,
        ContactRoleInlineContact, CollectionRelationshipInline, StoryReviewInline
    )
    author_form_class = SubmissionAdminAuthorForm
    editor_form_class = SubmissionAdminEditorForm
    review_model = StoryReview

    fieldsets = [
        (None, {
            'fields': (
                ('title', 'status'),
                'text',
                'editorial_comments',
                ('parent_landing_master', 'url'),
                'description',
            )
        }),
        ('Advanced Content Management Settings', {
            'classes': ('grp-collapse grp-closed',),
            'fields': (
                ('subtitle', ),
                ('overline', ),
                ('content_area',),
                ('template',),
                ('resource_url',),
                ('code',),
                ('featured_image', 'featured_image_display',),
                ('thumbnail', 'thumbnail_html'),
                ('publish_time', 'make_public_time',),
                ('archive_time', 'make_inactive_time',),
                ('workflow_status',),
                ('parent', 'slug'),
                ('permission_groups',),
                ('show_content_without_groups',),
                'keywords',
                ('og_title', 'og_url'),
                ('og_type', 'og_image'),
                ('og_description',)
            )
        })
    ]

    def save_model(self, request, obj, form, change):
        save_return = super().save_model(request, obj, form, change)
        add_member_story_tag(obj)

        if publishing_for_first_time(request, obj):
            send_story_published_email(obj)

        if self.changing_to_inactive(form, obj):
            send_story_rejected_email(obj)

        return save_return

    def changing_to_inactive(self, form, obj):
        return 'status' in form.changed_data and obj.status == 'I'
