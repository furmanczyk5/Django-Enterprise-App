from django.template.loader import render_to_string

from knowledgebase.models import (
    ResourceSuggestion,
    ResourceSuggestionReview,
    Story,
    StoryReview
)
from myapa.models import Contact
from planning.global_test_case import GlobalTestCase


class TestReviewAssigned(GlobalTestCase):
    def setUp(self):
        self.href = (
            '<a href="https://planning.org/knowledgebase'
            '/{}/{}/details">user contribution</a>'
        )
        self.contact = Contact.objects.create()

    def test_contains_link_for_story(self):
        content = Story.objects.create()
        review = StoryReview.objects.create(content=content, contact=self.contact)
        email_body = render_to_string(
            'knowledgebase/email/review_assigned.html',
            {'content': content}
        )
        expected_href = self.href.format('story', content.master_id)
        assert expected_href in email_body

    def test_contains_link_for_resource(self):
        content = ResourceSuggestion.objects.create()
        review = ResourceSuggestionReview.objects.create(content=content, contact=self.contact)
        email_body = render_to_string(
            'knowledgebase/email/review_assigned.html',
            {'content': content}
        )
        expected_href = self.href.format('resource', content.master_id)
        assert expected_href in email_body
