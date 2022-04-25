from planning.global_test_case import GlobalTestCase

from imis.models import NameAddress, IndDemographics, OrgDemographics
from myapa.tests.factories.organization import OrganizationFactory


class OrganizationTest(GlobalTestCase):

    @classmethod
    def setUpTestData(cls):
        super(OrganizationTest, cls).setUpTestData()

    @classmethod
    def tearDownClass(cls):
        return super().tearDownClass()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_imis_create(self):
        org = OrganizationFactory()
        org_name = org.imis_create()
        self.assertTrue(org_name.company_record)
        self.assertEqual(org.company, org_name.company)
        self.assertEqual(org.phone, org_name.work_phone)
        self.assertEqual(org.city, org_name.city)
        self.assertEqual(org.state, org_name.state_province)
        self.assertEqual(org.country, org_name.country)
        self.assertEqual(org.zip_code, org_name.zip)
        self.assertEqual(org.personal_url, org_name.website)

        name_address = NameAddress.objects.get(id=org_name.id)
        self.assertEqual(name_address.address_1, org.address1)
        self.assertEqual(name_address.address_2, org.address2)
        self.assertEqual(name_address.city, org.city)
        self.assertEqual(name_address.state_province, org.state)
        self.assertEqual(name_address.country, org.country)
        self.assertEqual(name_address.zip, org.zip_code)

        self.assertEqual(org_name.full_address, name_address.full_address)

        self.assertTrue(IndDemographics.objects.filter(id=org_name.id).exists())
        self.assertTrue(OrgDemographics.objects.filter(id=org_name.id).exists())
        self.assertEqual(org_name.company_sort, name_address.get_company_sort())

