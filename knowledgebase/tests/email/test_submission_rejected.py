from django.template.loader import render_to_string

from content.models import Content, ContentRelationship
from myapa.models import Contact, ContactRole
from planning.global_test_case import GlobalTestCase


class TestSubmissionRejected(GlobalTestCase):
    def setUp(self):
        self.title = 'How to Plan'
        self.content = Content.objects.create(title=self.title)

        self.collection_title = 'Automobiles'
        collection = Content.objects.create(
            title=self.collection_title
        )
        collection.publish()

        ContentRelationship.objects.create(
            content=self.content,
            content_master_related=collection.master
        )

        self.email_body = render_to_string(
            'knowledgebase/email/submission_rejected.html',
            {'content': self.content}
        )

    def test_email_contains_generic_greeting_if_contact_first_name_missing(self):
        assert 'Dear member,' in self.email_body

    def test_email_contains_custom_greeting_if_contact_first_name_present(self):
        first_name = 'Steven'
        contact = Contact.objects.create(first_name=first_name)

        ContactRole.objects.create(
            content=self.content,
            contact=contact
        )

        email_body = render_to_string(
            'knowledgebase/email/submission_rejected.html',
            {'content': self.content}
        )

        assert 'Dear {},'.format(first_name) in email_body

    def test_email_contains_content_title(self):
        assert '"{}"'.format(self.title) in self.email_body

    def test_email_contains_knowledgebase_category(self):
        assert '"{}"'.format(self.collection_title) in self.email_body
