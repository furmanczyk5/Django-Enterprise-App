from django import forms
from django.contrib import admin

from knowledgebase.mail import send_resource_published_email
from knowledgebase.models import (
    ResourceSuggestionReview,
    StoryReview
)
from myapa.admin import ContactRoleInlineContact
from research_inquiries.forms import ReviewInlineForm
from content.models import Content, ContentRelationship


class ResourceRelationshipAdminInlineForm(forms.ModelForm):
    def save(self, commit=True):
        contentrelationship = super().save(commit=False)
        contentrelationship.relationship = 'KNOWLEDGEBASE_SUGGESTION'
        if commit:
            contentrelationship.save()

        if self.is_published(contentrelationship.content):
            master_suggestion = contentrelationship.content_master_related
            resource_suggestion = Content.objects.get(
                master_id=master_suggestion.id
            )
            send_resource_published_email(
                contentrelationship.content,
                resource_suggestion
            )

        return contentrelationship

    def is_published(self, content):
        return (
            content.status == 'A' and
            content.workflow_status == 'IS_PUBLISHED'
        )

    class Meta:
        model = ContentRelationship
        fields = ['content_master_related']


class ResourceRelationshipInline(admin.TabularInline):
    model = Content.related.through
    form = ResourceRelationshipAdminInlineForm
    extra = 0
    fields = ('content_master_related', )
    verbose_name = 'Suggestion Submission ID'
    verbose_name_plural = 'Suggestion Submission ID'

    def get_queryset(self, request):
        return super().get_queryset(
            request
        ).filter(
            relationship='KNOWLEDGEBASE_SUGGESTION'
        )

    def formfield_for_foreignkey(self, db_field, *args, **kwargs):
        field = super().formfield_for_foreignkey(db_field, *args, **kwargs)
        if db_field.name == 'content_master_related':
            field.queryset = field.queryset.filter(
                content_draft__content_type='KNOWLEDGEBASE_SUGGESTION'
            )
        return field


class SubmissionInline(admin.StackedInline):
    extra = 0
    readonly_fields = ['assigned_time', 'review_time']
    form = ReviewInlineForm
    fieldsets = [
        (None, {
            'fields': (
                ('role', 'review_status'),
                'comments',
                ('assigned_time', 'review_time'),
                'deadline_time'
            )
        })
    ]


class ReviewInline(SubmissionInline):
    def formfield_for_foreignkey(self, db_field, *args, **kwargs):
        field = super().formfield_for_foreignkey(
            db_field, *args, **kwargs
        )
        if db_field.name == 'role':
            field.queryset = field.queryset.filter(
                review_type='KNOWLEDGEBASE_REVIEW'
            )
            field.required = True
        return field


class StoryReviewInline(ReviewInline):
    model = StoryReview


class ResourceReviewInline(ReviewInline):
    model = ResourceSuggestionReview


class SubmissionRoleInline(ContactRoleInlineContact):
    fields = [
        f for f in ContactRoleInlineContact.fields if f is not 'role_type'
    ]
