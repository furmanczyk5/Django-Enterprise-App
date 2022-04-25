from content.tests.factories.content import ContentFactory
from content.tests.factories.tagging import ContentTagTypeFactory, TagTypeFactory, TagFactory
from myapa.tests.factories import contact as contact_factory, contact_role as contact_role_factory
from planning.global_test_case import GlobalTestCase


class ContactRoleTestCase(GlobalTestCase):

    def setUp(self):
        self.brendanaquits = contact_factory.ContactFactoryIndividual(
            first_name='Mark',
            last_name='Brendanawicz',
            job_title='City Planner',
            company='City of Pawnee',
            email="mbrendanawicz@cityofpawnee.us"
        )

    def test_get_contact_name_and_email(self):
        role = contact_role_factory.ContactRoleFactory(
            contact=self.brendanaquits
        )

        self.assertEqual(role.get_contact_name(), self.brendanaquits.title)
        self.assertEqual(role.get_contact_email(), self.brendanaquits.email)

        role_no_contact = contact_role_factory.ContactRoleFactory()
        self.assertEqual(
            role_no_contact.get_contact_name(),
            "{} {}".format(role_no_contact.first_name, role_no_contact.last_name)
        )
        self.assertEqual(
            role_no_contact.get_contact_email(),
            role_no_contact.email
        )

    def test_role_type_friendly(self):
        role_author = contact_role_factory.ContactRoleFactory(
            role_type="AUTHOR"
        )
        self.assertEqual(role_author.role_type_friendly(), "Author")

        role_speaker = contact_role_factory.ContactRoleFactory(
            role_type="SPEAKER"
        )
        self.assertEqual(role_speaker.role_type_friendly(), "Speaker")

        role_proposer = contact_role_factory.ContactRoleFactory(
            role_type="PROPOSER"
        )
        self.assertEqual(role_proposer.role_type_friendly(), "Proposer / Nominator")

        role_none = contact_role_factory.ContactRoleFactory(
            role_type=""
        )
        self.assertEqual(role_none.role_type_friendly(), "")

    def test_get_solr_role_types(self):
        role_speaker = contact_role_factory.ContactRoleFactory(
            role_type="SPEAKER"
        )
        role_speaker.content.title = "Test Title"
        role_speaker.content.save()

        self.assertDictEqual(
            role_speaker.get_solr_role_types(),
            dict(contact_roles_SPEAKER=["{}|Test Title".format(role_speaker.content.master_id)])
        )

    def test_get_solr_content_tags(self):
        content = ContentFactory(title="Climate Change is Bad")
        tag_type_taxo = TagTypeFactory(title="Taxonomy Master Topics")
        ctt1 = ContentTagTypeFactory(content=content, tag_type=tag_type_taxo)
        tag1 = TagFactory(
            title="Climate Change Policy",
            tag_type=tag_type_taxo,
            taxo_term="PolicyClimateChange"
        )
        ctt1.tags.add(tag1)
        self.assertTrue(ctt1.tags.exists())

        author = contact_factory.ContactFactoryIndividual()
        role = contact_role_factory.ContactRoleFactory(
            content=content,
            contact=author,
            role_type="AUTHOR"
        )

        self.assertEqual(role.content.contenttagtype.first(), ctt1)

        solr_tags = role.get_solr_content_tags()
        self.assertSetEqual(solr_tags, {'Climate Change Policy'})

        tag2 = TagFactory(
            title="Energy Policy",
            tag_type=tag_type_taxo,
            taxo_term="PolicyEnergy"
        )
        ctt1.tags.add(tag2)
        self.assertSetEqual(
            role.get_solr_content_tags(),
            {'Climate Change Policy', 'Energy Policy'}
        )
