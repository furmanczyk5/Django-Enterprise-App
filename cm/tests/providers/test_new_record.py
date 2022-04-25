from django.test import Client
from django.urls import reverse

from cm.forms.providers import ProviderNewRegistrationForm
from imis.enums.relationship_types import ImisRelationshipTypes
from imis.models import Relationship, Name
from imis.tests.factories.name import ImisNameFactoryAmerica
from myapa.models.contact import Contact
from myapa.models.proxies import Organization, IndividualContact
from myapa.tests.factories.organization import OrganizationFactory
from planning.global_test_case import GlobalTestCase


class ProviderNewRecordViewTest(GlobalTestCase):

    @classmethod
    def setUpTestData(cls):
        super(ProviderNewRecordViewTest, cls).setUpTestData()

    @classmethod
    def tearDownClass(cls):
        return super(ProviderNewRecordViewTest, cls).tearDownClass()

    def setUp(self):
        self.client = Client()

    def tearDown(self):
        self.client.logout()


class ProviderNewRegistrationFormTest(GlobalTestCase):

    fixtures = [
        "cities_light_country",
        "cities_light_region"
    ]

    @classmethod
    def setUpTestData(cls):
        super(ProviderNewRegistrationFormTest, cls).setUpTestData()
        cls.org_form_fields = ProviderNewRegistrationForm().fields.keys()

    def setUp(self):
        self.org_data = OrganizationFactory.build().__dict__
        self.org_data = {k: v or '' for (k, v) in self.org_data.items() if k in self.org_form_fields}

    def test_organization_factory_yields_valid_form_data_by_default(self):
        form = ProviderNewRegistrationForm(data=self.org_data)
        self.assertTrue(form.is_valid())

    def test_ein_validator(self):
        data = self.org_data
        data['ein_number'] = 'AHAAAHGH'
        form = ProviderNewRegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['ein_number'],
            ["Only numeric characters are allowed."]
        )

        data['ein_number'] = '14-454322'
        form = ProviderNewRegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['ein_number'],
            ["Only numeric characters are allowed."]
        )

        data['ein_number'] = '111111111'
        form = ProviderNewRegistrationForm(data=data)
        self.assertTrue(form.is_valid())

        data['ein_number'] = '456789876543456789'
        form = ProviderNewRegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['ein_number'],
            ["Ensure this value has at most 9 characters (it has {}).".format(
                len(data['ein_number'])
            )]
        )

    def test_save(self):
        # create a bunch of dummy orgs
        OrganizationFactory.create_batch(size=100)
        self.assertEqual(Organization.objects.count(), 100)

        form = ProviderNewRegistrationForm(data=self.org_data)
        form.save()
        self.assertEqual(Organization.objects.count(), 101)
        # Should only be one that exactly matches all the required form fields
        org = Organization.objects.filter(**self.org_data)
        self.assertEqual(org.count(), 1)

    def test_relationships_created_on_new_org_record_save(self):
        org_admin = ImisNameFactoryAmerica(
            company_record=False,
            member_record=True,
            co_id='',
            company=''
        )
        org_admin.save()
        contact = Contact.update_or_create_from_imis(org_admin.id)
        self.assertIsInstance(contact, IndividualContact)
        self.client.force_login(contact.user)
        self.client.post(
            reverse('cm:provider_newrecord'),
            data=self.org_data
        )

        # admin should now have co_id field set in Name...
        org_admin = Name.objects.get(id=org_admin.id)
        # ...and a company_record with that as its id should exist
        org = Name.objects.get(id=org_admin.co_id)

        relationship = Relationship.objects.filter(
            id=contact.user.username,
            target_id=org.id,
            relation_type=ImisRelationshipTypes.ADMIN_I.value,
            target_relation_type=ImisRelationshipTypes.ADMIN_C.value
        )
        self.assertEqual(relationship.count(), 1)

