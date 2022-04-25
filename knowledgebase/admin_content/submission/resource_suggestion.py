from .submission import SubmissionAdmin
from knowledgebase.admin_content.filters import (
    CollectionFilter,
    ReviewStatusFilter
)
from knowledgebase.forms.admin.inlines import ResourceReviewInline
from knowledgebase.forms.admin.forms import (
    ResourceSuggestionAdminAuthorForm,
    ResourceSuggestionAdminEditorForm
)
from knowledgebase.models import ResourceSuggestionReview
from content.admin import CollectionRelationshipInline
from myapa.admin import ContactRoleInlineContact


class ResourceSuggestionAdmin(SubmissionAdmin):
    list_filter = (ReviewStatusFilter, CollectionFilter)
    list_display = [
        'get_master_id', 'title', 'get_collections',
        'reviewers', 'get_status'
    ]
    inlines = (
        ContactRoleInlineContact,
        CollectionRelationshipInline,
        ResourceReviewInline
    )
    author_form_class = ResourceSuggestionAdminAuthorForm
    editor_form_class = ResourceSuggestionAdminEditorForm
    review_model = ResourceSuggestionReview

    def publishable_extra_context(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['extra_save_options'] = {
            'show_publish': False,
            'show_preview': False
        }
        return extra_context

    def get_status(self, obj):
        review_statuses = ', '.join(
            [
                "%s" % (r.get_review_status_display())
                for r in obj.review_assignments.all()
            ]
        )

        if not review_statuses:
            visibility_status = obj.status
            if visibility_status == 'P':
                return 'Pending'
            elif visibility_status == 'CA':
                return obj.get_status_display()
            elif visibility_status == 'N':
                return 'Not Complete'

        return review_statuses
    get_status.short_description = 'Review Status'
    get_status.admin_order_field = (
        'review_assignments__review_status'
    )

    fieldsets = [
        (None, {
            'fields': (
                'title',
                'text',
                'editorial_comments',
                ('url', 'resource_url'),
                'description',
            ),
        })
    ]
