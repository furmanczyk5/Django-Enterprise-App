from content.models import Content, ContentRelationship, MasterContent
from content.models.tagging import TaxoTopicTag
from knowledgebase.management.commands.add_proceedings import Command, COLLECTION_CODE
from myapa.models import Contact, ContactRole
from planning.global_test_case import GlobalTestCase


class TransformCVSTest(GlobalTestCase):

    @classmethod
    def setUpTestData(cls):
        super(TransformCVSTest, cls).setUpTestData()
        TaxoTopicTag.objects.get_or_create(code="SKILLSETHISTORY")

    def setUp(self):
        self.page = '58'
        self.resource_url = 'https://fake-url.com'
        self.title = 'LETTER TO THE PEOPLE, HON. BACON PANCAKE, 1909'
        self.modified_title = "{} (p. {})".format(self.title, self.page)
        self.subtitle = 'Proceedings of a Conference'
        self.text = (
            'This resource is on page %s of %s, '
            'an electronic text contained in the APA '
            'Library E-book Collection. This text is '
            'available to APA members as a benefit of '
            'membership.' %(self.page, self.subtitle,)
        )

        self.row = {
            'Year': '1909',
            'Volume': self.subtitle,
            'Author': 'Pancake, IX, The Reverend Bacon Griddle',
            'Title': self.title,
            'Starting Page': self.page,
            'Link': self.resource_url
        }
        self.rows = [self.row]
        self.collection = Content.objects.create(code=COLLECTION_CODE)
        self.collection.publish()

    def test_does_not_include_rows_without_titles(self):
        resources = Command().transform_csv([{'Title': ''}, {'Title': '   '}, {}], self.collection)
        self.assertEqual(resources, [])

    def test_creates_published_resource(self):
        self.assertFalse(Content.objects.filter(title=self.modified_title).exists())
        Command().transform_csv(self.rows, self.collection)
        self.assertTrue(Content.objects.filter(title=self.modified_title).exists())

    def test_creates_resource_with_correct_fields(self):
        Command().transform_csv(self.rows, self.collection)
        resource = Content.objects.filter(title=self.modified_title).first()
        self.assertEqual(resource.title, self.modified_title)
        self.assertEqual(resource.subtitle, self.subtitle)
        self.assertEqual(resource.text, self.text)
        self.assertEqual(resource.resource_url, self.resource_url)
        self.assertEqual(resource.url, '/knowledgebase/resource/{}'.format(resource.master_id))

    def test_does_not_create_duplicate_resources(self):
        Command().transform_csv([self.row, self.row], self.collection)
        self.assertEqual(len(Content.objects.filter(title=self.modified_title)), 2)

    def test_creates_contact(self):
        self.assertFalse(Contact.objects.filter(first_name='Bacon', last_name='Pancake').exists())
        Command().transform_csv(self.rows, self.collection)
        self.assertTrue(Contact.objects.get(first_name='Bacon', last_name='Pancake'))

    def test_creates_contact_with_correct_fields(self):
        Command().transform_csv(self.rows, self.collection)
        contact = Contact.objects.get(first_name='Bacon', last_name='Pancake')
        self.assertEqual(contact.first_name, 'Bacon')
        self.assertEqual(contact.middle_name, 'Griddle')
        self.assertEqual(contact.last_name, 'Pancake')
        self.assertEqual(contact.prefix_name, 'The Reverend')
        self.assertEqual(contact.suffix_name, "IX")
        self.assertEqual(contact.contact_type, 'INDIVIDUAL')

    def test_does_not_create_duplicate_contacts(self):
        Command().transform_csv([self.row, self.row], self.collection)
        self.assertEqual(len(Contact.objects.filter(first_name='Bacon', last_name='Pancake')), 1)

    def test_creates_contactrole(self):
        self.assertFalse(ContactRole.objects.all().exists())
        Command().transform_csv(self.rows, self.collection)
        resource = Content.objects.filter(title=self.modified_title).first()
        contact = Contact.objects.get(first_name='Bacon', last_name='Pancake')
        contact_role = ContactRole.objects.all().first()
        self.assertEqual(contact_role.content, resource)
        self.assertEqual(contact_role.contact, contact)

    def test_creates_content_relationship(self):
        self.assertFalse(ContentRelationship.objects.all().exists())
        Command().transform_csv(self.rows, self.collection)
        resource = Content.objects.filter(title=self.modified_title).first()
        master_collection = MasterContent.objects.get(id=self.collection.master_id)
        content_relationship = ContentRelationship.objects.all().first()
        self.assertEqual(content_relationship.content, resource)
        self.assertEqual(content_relationship.content_master_related, master_collection)
