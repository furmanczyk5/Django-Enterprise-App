from django.contrib import admin

from .filters import RoleFilter
from knowledgebase.forms.admin.forms import ReviewForm
from knowledgebase.mail import (
    send_resource_rejected_email,
    send_reviewer_email
)


REJECTED_RESOURCE_STATUSES = [
    'REVIEW_COMPLETE_DUPLICATIVE',
    'REVIEW_COMPLETE_OFF_TOPIC'
]


def get_submission_url(submission_type, content_id, url_title):
    return ("<a href='/admin/knowledgebase/{}/{}' "
            ">{}</a>").format(submission_type, content_id, url_title)


class SubmissionReviewAdmin(admin.ModelAdmin):
    readonly_fields = ['get_title', 'assigned_time', 'review_time']
    list_display = [
        'id', 'get_master_id', 'get_title', 'get_collections',
        'get_submitter', 'reviewer', 'review_status'
    ]
    raw_id_fields = ['content']
    search_fields = (
        'id', 'content__master__id', 'content__title',
        'content__contactrole__contact__last_name',
        'content__contactrole__contact__first_name',
        'role__contact__last_name', 'role__contact__first_name'
    )
    fieldsets = [
        (None, {
            'fields': (
                ('content'),
                ('role', 'review_status'),
                'comments',
                ('deadline_time', 'assigned_time', 'review_time')
            ),
        }),
    ]

    def get_collections(self, obj):
        draft_collections = [
            mc.content_draft.title
            for mc in obj.content.related.all()
            if mc.content_draft.content_type == 'KNOWLEDGEBASE_COLLECTION'
        ]
        return ", ".join(draft_collections)
    get_collections.short_description = 'Collections'

    def get_submitter(self, obj):
        return ', '.join(
            [
                '{}'.format(submitter)
                for submitter in obj.content.contactrole.all()
            ]
        ) or "Unassigned"
    get_submitter.short_description = 'Submitter'
    get_submitter.admin_order_field = (
        'content__contactrole__contact__last_name'
    )

    def reviewer(self, obj):
        return obj.role or "Unassigned"
    reviewer.short_description = "Staff Reviewer"
    reviewer.admin_order_field = "role__contact__last_name"

    def save_model(self, request, obj, form, change):
        obj.contact = obj.role.contact
        obj.save()
        self.update_content_status(obj)

        if 'role' in form.changed_data:
            send_reviewer_email(obj)
        super().save_model(request, obj, form, change)

    def update_content_status(self, obj):
        if (obj.review_status == 'REVIEW_COMPLETE_DUPLICATIVE' or
                obj.review_status == 'REVIEW_COMPLETE_OFF_TOPIC'):
            obj.content.status = 'I'
            obj.content.save()


class StoryReviewAdmin(SubmissionReviewAdmin):
    list_filter = (RoleFilter,)

    autocomplete_lookup_fields = dict(fk=['content'])
    form = ReviewForm

    def get_title(self, obj):
        if obj:
            return get_submission_url(
                'story', obj.content_id, obj.content)
        else:
            return "None"
    get_title.short_description = "Title"
    get_title.allow_tags = True
    get_title.admin_order_field = "content__title"

    def get_master_id(self, obj):
        if obj:
            return get_submission_url(
                'story', obj.content_id, obj.content.master_id
            )
        else:
            return "None"
    get_master_id.short_description = 'Master'
    get_master_id.allow_tags = True
    get_master_id.admin_order_field = 'content__master__id'


class ResourceSuggestionReviewAdmin(SubmissionReviewAdmin):
    list_filter = (RoleFilter,)

    autocomplete_lookup_fields = dict(fk=['content'])
    form = ReviewForm

    def get_title(self, obj):
        if obj:
            return get_submission_url(
                'resourcesuggestion', obj.content_id, obj.content
            )
        else:
            return "None"
    get_title.short_description = "Title"
    get_title.allow_tags = True
    get_title.admin_order_field = "content__title"

    def get_master_id(self, obj):
        if obj:
            return get_submission_url(
                'resourcesuggestion', obj.content_id, obj.content.master_id
            )
        else:
            return "None"
    get_master_id.short_description = 'Master'
    get_master_id.allow_tags = True
    get_master_id.admin_order_field = 'content__master__id'

    def save_model(self, request, obj, form, change):
        if ('review_status' in form.changed_data and
                obj.review_status in REJECTED_RESOURCE_STATUSES):
            send_resource_rejected_email(obj)

        super().save_model(request, obj, form, change)
