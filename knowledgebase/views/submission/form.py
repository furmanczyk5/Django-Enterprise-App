from django.conf import settings
from django.http import Http404
from sentry_sdk import capture_exception

from knowledgebase.forms.submission import (
    ResourceSuggestionTypeForm,
    StorySubmissionTypeForm
)
from knowledgebase.models import CollectionRelationship
from knowledgebase.tags import add_member_story_tag
from content.models import MasterContent
from myapa.models import ContactRole
from myapa.viewmixins import AuthenticateMemberMixin
from submissions.views import SubmissionEditFormView
from content.mail import Mail




class SubmissionFormTypeView(AuthenticateMemberMixin, SubmissionEditFormView):
    home_url = '/knowledgebase/dashboard'
    success_url = '/knowledgebase/dashboard'
    body = ''

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['request'] = self.request
        return kw

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['body'] = self.body
        return context

    def set_content(self, request, *args, **kwargs):
        if not getattr(self, 'content', None):
            master_id = kwargs.pop('master_id', None)
            if master_id is not None:
                self.model_class = self.form_class.Meta.model
                self.content = self.model_class.objects.filter(
                    master_id=master_id,
                    publish_status='DRAFT'
                ).first()
                if not self.content:
                    Http404('Submission Record not Found')
            else:
                self.content = None

    def after_save(self, form):
        collection_id = form['collection_choices'].value()
        collection_obj = MasterContent.objects.get(pk=collection_id)
        form_obj = form.save(commit=False)

        self.remove_previous_collection_relationship(form_obj)

        CollectionRelationship.objects.get_or_create(
            content=form_obj,
            content_master_related=collection_obj,
            relationship='RELATED'
        )

        ContactRole.objects.get_or_create(
            contact=self.request.user.contact,
            content=self.content,
            role_type='AUTHOR'
        )

        if self.user_is_submitting():
            self.send_submitted_email(form_obj)

        super().after_save(form)

    def remove_previous_collection_relationship(self, form_obj):
        collection_relationships = CollectionRelationship.objects.filter(
            content=form_obj
        )

        for relationship in collection_relationships:
            relationship.delete()

    def user_is_submitting(self):
        return self.request and 'submitButton' in self.request.POST

    def send_submitted_email(self, form_obj):
        try:
            mail_context = {
                'content': form_obj,
                'SERVER_ADDRESS': settings.SERVER_ADDRESS
            }
            email_template = 'KNOWLEDGEBASE_SUBMISSION_SUBMITTED'
            user_email = self.request.user.contact.email
            Mail.send(email_template, user_email, mail_context)
            Mail.send(
                'KNOWLEDGEBASE_SUBMISSION_STAFF_NOTICE',
                'knowledgebase@planning.org',
                mail_context
            )
        except Exception as e:
            capture_exception(e)


class StorySubmissionFormTypeView(SubmissionFormTypeView):
    title = 'Submit a Story'
    body = (
        'Enter your story below. Please be sure '
        'that it is correct before hitting "Submit."'
    )
    form_class = StorySubmissionTypeForm
    template_name = 'knowledgebase/newtheme/submission/story.html'

    def after_save(self, form):
        super().after_save(form)
        form_obj = form.save(commit=False)
        add_member_story_tag(form_obj)


class ResourceSuggestionFormTypeView(SubmissionFormTypeView):
    title = 'Submit a Resource'
    body = (
        'Please enter the resource name and URL. '
        'Please be sure that both are correct '
        'before hitting "Submit."'
    )
    form_class = ResourceSuggestionTypeForm
    template_name = 'knowledgebase/newtheme/submission/resource.html'
