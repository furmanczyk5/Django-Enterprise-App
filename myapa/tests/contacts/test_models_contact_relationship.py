from imis.enums.relationship_types import ImisRelationshipTypes
from myapa.models.contact_relationship import ContactRelationship
from myapa.tests.factories import contact as contact_factory
from planning.global_test_case import GlobalTestCase


class ContactRelationshipTestCase(GlobalTestCase):

    def setUp(self):
        self.org_contact = contact_factory.ContactFactoryOrganization()

        self.employee_contact = contact_factory.ContactFactoryIndividual()

        self.rel1 = ContactRelationship(
            source=self.employee_contact,
            target=self.org_contact,
            relationship_type="ADMINISTRATOR"
        )
        self.rel1.save()

    def test_relationships_must_be_explicitly_created(self):

        org = contact_factory.ContactFactoryOrganization()
        ind = contact_factory.ContactFactoryIndividual()
        self.assertFalse(org.related_contacts.exists())
        self.assertFalse(org.related_contact_sources.exists())
        self.assertFalse(ind.related_contacts.exists())
        self.assertFalse(ind.related_contact_sources.exists())

    def test_relationships_exist(self):
        self.assertEqual(self.org_contact.related_contact_sources.count(), 1)
        self.assertFalse(self.org_contact.related_contacts.exists())
        self.assertEqual(self.employee_contact.related_contacts.count(), 1)
        self.assertFalse(self.employee_contact.related_contact_sources.exists())

        self.assertEqual(self.employee_contact.related_contacts.first(), self.org_contact)
        self.assertEqual(self.org_contact.related_contact_sources.first(), self.employee_contact)

        rel2 = ContactRelationship(
            source=self.employee_contact,
            target=self.org_contact,
            relationship_type="ADMINISTRATOR"
        )
        rel2.save()

        self.assertTrue(self.org_contact.related_contact_sources.count() == 2)
        self.assertTrue(self.employee_contact.related_contacts.count() == 2)

        ContactRelationship.objects.get(pk=rel2.pk).delete()

    def test_get_company_contact(self):
        contact = ContactRelationship.get_company_contact(user=self.employee_contact.user)
        self.assertEqual(self.org_contact, contact)

        contact2 = ContactRelationship.get_company_contact(user=self.org_contact.user)
        self.assertEqual(self.employee_contact, contact2)

        billing_admin = contact_factory.ContactFactoryIndividual()
        rel3 = ContactRelationship(
            source=self.org_contact,
            target=billing_admin,
            relationship_type=ImisRelationshipTypes.BILLING_I.value
        )
        rel3.save()

        contact3 = ContactRelationship.get_company_contact(user=billing_admin.user)
        self.assertNotEqual(self.org_contact, contact3)

        # Change the relationship_type such that there are no more ADMINISTRATOR ContactRelationships
        self.rel1.relationship_type = "FSMA"
        self.rel1.save()
        contact4 = ContactRelationship.get_company_contact(user=self.employee_contact.user)
        self.assertIsNone(contact4)

    def test_get_company_admin(self):
        contact = ContactRelationship.get_company_admin(contact=self.org_contact)
        self.assertEqual(self.employee_contact, contact)

        contact2 = ContactRelationship.get_company_admin(contact=self.employee_contact)
        self.assertEqual(self.org_contact, contact2)
