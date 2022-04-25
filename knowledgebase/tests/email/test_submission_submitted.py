from django.template.loader import render_to_string

from knowledgebase.models import Story, ResourceSuggestion
from planning.global_test_case import GlobalTestCase


class TestSubmissionAccepted(GlobalTestCase):
    def setUp(self):
        self.href = (
            '<a href="https://planning.org/knowledgebase'
            '/{}/{}/details">user contribution</a>'
        )

    def test_contains_link_for_story(self):
        content = Story.objects.create()
        email_body = render_to_string(
            'knowledgebase/email/submission_submitted.html',
            {'content': content}
        )
        expected_href = self.href.format('story', content.master_id)
        assert expected_href in email_body

    def test_contains_link_for_resource_suggestion(self):
        content = ResourceSuggestion.objects.create()
        email_body = render_to_string(
            'knowledgebase/email/submission_submitted.html',
            {'content': content}
        )
        expected_href = self.href.format('resource', content.master_id)
        assert expected_href in email_body
