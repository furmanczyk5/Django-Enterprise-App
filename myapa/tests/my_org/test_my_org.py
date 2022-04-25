import random

from django.test import Client

from imis import models as imis_models
from imis.enums.relationship_types import ImisRelationshipTypes as RelTypes
from imis.tests.factories import name as name_facts
from imis.tests.factories.relationship import RelationshipFactory
from myapa.functional_tests import utils as test_utils
from myapa.models.contact import Contact
from myapa.models.proxies import Organization
from myapa.tests.factories import contact as contact_factory
from planning.global_test_case import GlobalTestCase
from uploads.models import UploadType


class MyOrgTestCase(GlobalTestCase):

    @classmethod
    def setUpTestData(cls):

        super(MyOrgTestCase, cls).setUpTestData()

        UploadType.objects.get_or_create(code="PROFILE_PHOTOS")

    def setUp(self):

        # An administrator for an organization has records correctly set up
        # in the iMIS Name and Relationship tables by the Membership department
        self.org_imis, self.org_imis_admin = test_utils.build_imis_org_and_admin()
        self.org_imis.save()
        self.org_imis_admin.save()

        self.rel_imis = RelationshipFactory(
            id=self.org_imis_admin.id,
            relation_type=RelTypes.ADMIN_I.value,
            target_id=self.org_imis.id,
            target_relation_type=RelTypes.ADMIN_C.value,
        )
        self.rel_imis.save()

        self.client = Client()

    def tearDown(self):
        self.client.logout()

    def test_organization_proxy_model_works_after_syncing_from_imis(self):

        # Membership dept uses the update/create record from iMIS page
        org_contact = Contact.update_or_create_from_imis(self.org_imis.id)

        # smoke test for our proxy model
        self.assertTrue(Organization.objects.filter(user__username=org_contact.user.username).exists())

    def test_relationships_automatically_created_when_org_synced_in_django(self):
        # Membership dept uses the update/create record from iMIS page
        org_contact = Contact.update_or_create_from_imis(self.org_imis.id)
        # Should be automatically created when the Org is synced
        org_admin_contact = Contact.objects.get(user__username=self.org_imis_admin.id)

        self.assertEqual(org_contact.related_contact_sources.first(), org_admin_contact)
        self.assertEqual(org_admin_contact.related_contacts.first(), org_contact)
        self.assertEqual(org_admin_contact.company_fk, org_contact)

    def test_non_org_admin_does_not_see_my_org_dashboard_on_myapa(self):
        rando_mem = name_facts.ImisNameFactoryAmerica()
        rando_mem.save()
        contact = Contact.update_or_create_from_imis(rando_mem.id)

        self.client.force_login(contact.user)
        resp = self.client.get('/myapa/')
        self.assertNotIn("My Organization", resp.content.decode('utf-8'))

    def test_org_admin_sees_my_org_dashboard_on_myapa(self):
        Contact.update_or_create_from_imis(self.org_imis.id)
        org_admin_contact = Contact.objects.get(user__username=self.org_imis_admin.id)

        self.client.force_login(org_admin_contact.user)
        resp = self.client.get('/myapa/')
        self.assertIn("My Organization", resp.content.decode('utf-8'))

    def test_get_relationships_imis(self):
        orgdjango = contact_factory.ContactFactoryOrganization()
        orgimis = name_facts.ImisNameFactoryAmerica(
            id=orgdjango.user.username
        )
        orgimis.save()

        adminimis = name_facts.ImisNameFactoryAmerica(
            co_id=orgdjango.user.username
        )
        adminimis.save()

        imis_models.Relationship.objects.create(
            id=adminimis.id,
            target_id=orgdjango.user.username,
            relation_type=RelTypes.ADMIN_I.value,
            updated_by='DJANGO_TEST_FACTORY',
            seqn=random.randrange(1000000, 2000000)
        )

        self.assertTrue(orgdjango.get_imis_target_relationships().exists())

        employee = name_facts.ImisNameFactoryAmerica(
            co_id=orgdjango.user.username
        )
        employee.save()
        imis_models.Relationship.objects.create(
            id=employee.id,
            target_id=orgdjango.user.username,
            relation_type=RelTypes.ADMIN_I.value,
            updated_by='DJANGO_TEST_FACTORY',
            seqn=random.randrange(1000000, 2000000)
        )

        self.assertEqual(orgdjango.get_imis_target_relationships().count(), 2)

        imis_models.Relationship.objects.filter(id=employee.id).delete()

        self.assertEqual(orgdjango.get_imis_target_relationships().count(), 1)
