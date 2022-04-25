from django.utils import timezone
from functools import reduce

from knowledgebase.admin_content.publishing import PublishPermissionMixin
from knowledgebase.mail import (
    send_resource_rejected_email,
    send_reviewer_email
)
from knowledgebase.models import ResourceSuggestionReview
from content.admin import ContentAdmin
from myapa.models import ContactRole


REJECTED_RESOURCE_STATUSES = [
    'REVIEW_COMPLETE_DUPLICATIVE',
    'REVIEW_COMPLETE_OFF_TOPIC'
]


def get_submission_url(submission_type, content_id, url_title):
    return ("<a href='/admin/knowledgebase/{}/{}' "
            ">{}</a>").format(submission_type, content_id, url_title)


class SubmissionAdmin(PublishPermissionMixin, ContentAdmin):
    list_display = [
        'get_master_id', 'title', 'get_collections',
        'reviewers', 'status'
    ]
    list_display_links = ['get_master_id', 'title']
    readonly_fields = (
        ContentAdmin.readonly_fields
        + ('content_type', 'get_collections')
    )
    search_fields = (
        'master__id', 'title',
        'review_assignments__role__contact__last_name',
        'review_assignments__role__contact__first_name'
    )
    author_form_class = None
    editor_form_class = None
    review_model = None

    def get_collections(self, obj):
        draft_collections = [
            mc.content_draft.title
            for mc in obj.related.all()
            if mc.content_draft.content_type == 'KNOWLEDGEBASE_COLLECTION'
        ]
        return ", ".join(draft_collections)
    get_collections.short_description = 'Collections'

    def reviewers(self, obj):
        return ', '.join(
            [
                "%s (%s)" % (str(r.role.contact), r.role.title)
                for r in obj.review_assignments.all()
            ]
        ) or 'Unassigned'
    reviewers.short_description = 'Staff Reviewer'
    reviewers.admin_order_field = (
        'review_assignments__role__contact__last_name'
    )

    def save_formset(self, request, form, formset, change):
        if (formset.model == self.review_model and
                self.review_model is not None):
            presave_objects = self.get_presave_objects(formset)
            self.save_objects(formset, self.set_review_fields)
            self.send_email_for_reviewer_change(formset, presave_objects)
            if formset.model == ResourceSuggestionReview:
                self.handle_rejected_status(formset, presave_objects)
        elif formset.model == ContactRole:
            self.save_objects(formset, self.set_role_fields)
        else:
            super().save_formset(request, form, formset, change)

    def get_presave_objects(self, formset):
        form_objects = formset.save(commit=False)

        return [
            self.review_model.objects.get(id=obj.id)
            for obj in form_objects
            if obj.id
        ]

    def save_objects(self, formset, field_setter):
        form_objects = formset.save(commit=False)
        for form_object in form_objects:
            field_setter(form_object)
            form_object.save()
        self.delete_objects(formset)
        formset.save_m2m()

    def set_review_fields(self, review):
        review.assigned_time = review.assigned_time or timezone.now()
        review.contact = review.role.contact

    def set_role_fields(self, role):
        role.role_type = 'AUTHOR'

    def delete_objects(self, formset):
        for form_object in formset.deleted_objects:
            form_object.delete()

    def send_email_for_reviewer_change(self, formset, presave_objects):
        form_objects = formset.save(commit=False)
        presave_ids = list(map(lambda obj: obj.id, presave_objects))

        for obj in form_objects:
            if (obj.id not in presave_ids or
                    not self.equals_presave_role(obj, presave_objects)):
                send_reviewer_email(obj)

    def equals_presave_role(self, obj, presave_objects):
        presave_object = list(
            filter(
                lambda x: x.id == obj.id,
                presave_objects
            )
        )[0]
        return obj.role.contact_id == presave_object.role.contact_id

    def handle_rejected_status(self, formset, presave_objects):
        form_objects = formset.save(commit=False)
        presave_ids = list(map(lambda obj: obj.id, presave_objects))
        status_updates = []

        for obj in form_objects:
            if (obj.id not in presave_ids or
                    not self.equals_presave_status(obj, presave_objects)):
                status_updates.append(obj.review_status)

        was_rejected = reduce(
            lambda x, y: bool(y in REJECTED_RESOURCE_STATUSES) or x,
            status_updates,
            False
        )

        if was_rejected:
            obj.content.status = 'I'
            obj.content.save()
            send_resource_rejected_email(form_objects[0])

    def equals_presave_status(self, obj, presave_objects):
        presave_object = list(
            filter(
                lambda x: x.id == obj.id,
                presave_objects
            )
        )[0]
        return obj.review_status == presave_object.review_status
