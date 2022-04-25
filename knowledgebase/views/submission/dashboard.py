from django.views.generic import TemplateView

from knowledgebase.models import ResourceSuggestionReview
from content.models import MasterContent, Content, ContentRelationship
from myapa.models import ContactRole
from myapa.viewmixins import AuthenticateMemberMixin
from content.viewmixins import AppContentMixin


class SubmissionAdminDashboard(AuthenticateMemberMixin, AppContentMixin, TemplateView):
    title = 'Knowledgebase Submission Dashboard'
    template_name = 'knowledgebase/newtheme/submission/dashboard.html'
    # FLAGGED FOR REFACTORING: COMMENT THIS OUT TO RUN CONTENT MIGRATIONS
    content = Content.objects.filter(url='/knowledgebase/dashboard/').first()


    def get(self, request, *args, **kwargs):
        self.contact = self.request.user.contact
        submissions = []
        roles = ContactRole.objects.filter(contact_id=self.contact.id)

        for role in roles:
            content = Content.objects.filter(id=role.content_id).first()
            content_type = getattr(content, 'content_type', None)
            if (content_type == 'KNOWLEDGEBASE_STORY' or
                    content_type == 'KNOWLEDGEBASE_SUGGESTION'):
                submissions.append(content)

        self.remove_duplicate_content(submissions)
        self.add_resource_url_if_published(submissions)
        self.get_resource_status(submissions)

        self.submissions = sorted(
            submissions,
            key=lambda s: s.updated_time,
            reverse=True
        )

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contact'] = self.contact
        context['submissions'] = self.submissions
        return context

    def remove_duplicate_content(self, submissions):
        for submission in submissions:
            if submission.publish_status != 'DRAFT':
                submissions.remove(submission)

    def get_master_id_counts(self, submissions):
        id_counts = {}

        for submission in submissions:
            if submission.master_id in id_counts:
                id_counts[submission.master_id] += 1
            else:
                id_counts[submission.master_id] = 1

        return id_counts

    def get_resource_status(self, submissions):
        for submission in submissions:
            if submission.content_type == 'KNOWLEDGEBASE_SUGGESTION':
                reviews = ResourceSuggestionReview.objects.filter(
                    content=submission
                ).all()

                review_statuses = list(set([
                    review.review_status
                    for review in reviews
                ]))

                statuses_in_increasing_relevance = [
                    'REVIEW_RECEIVED',
                    'REVIEW_UNDERWAY',
                    'REVIEW_COMPLETE_DUPLICATIVE',
                    'REVIEW_COMPLETE_OFF_TOPIC',
                    'REVIEW_COMPLETE_ADDED'
                ]

                for status in statuses_in_increasing_relevance:
                    if status in review_statuses:
                        submission.review_status = status

    def add_resource_url_if_published(self, submissions):
        for submission in submissions:
            if submission.content_type == 'KNOWLEDGEBASE_SUGGESTION':
                master = MasterContent.objects.get(id=submission.master_id)
                relationships = ContentRelationship.objects.filter(
                    content_master_related=master,
                    relationship='KNOWLEDGEBASE_SUGGESTION'
                ).all()

                check_if_published = []

                for relationship in relationships:
                    check_if_published.append(
                        Content.objects.get(id=relationship.content_id)
                    )

                for resource in check_if_published:
                    if resource.publish_status == 'PUBLISHED':
                        submission.url = resource.url
                        submission.publish_status = 'PUBLISHED'
                        submission.status = 'A'
