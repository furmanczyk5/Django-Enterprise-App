import factory

from imis.enums import members
from imis.models import Name, NameAddress
from imis.tests.factories import name as name_facts
from imis.tests.factories.name_address import ImisNameAddressFactoryBlank
from myapa.models import proxies
from myapa.tests.factories import contact as contact_factory
from myapa.utils import get_contact_class, OrgDupeCheck
from planning.global_test_case import GlobalTestCase


class MyAPAUtilsTest(GlobalTestCase):

    def test_get_contact_class(self):
        contact = contact_factory.ContactFactory()
        imis_name = name_facts.ImisNameFactoryAmerica(id=contact.user.username)
        imis_name.save()

        cc1 = get_contact_class(contact)()
        self.assertIsInstance(cc1, proxies.IndividualContact)

        contact_org = contact_factory.ContactFactoryOrganization()
        imis_name_org = name_facts.ImisNameFactoryAmerica(id=contact_org.user.username)
        imis_name_org.save()

        cc2 = get_contact_class(contact_org)()
        self.assertIsInstance(cc2, proxies.Organization)

        contact_school = contact_factory.ContactFactoryOrganization(
            member_type=members.ImisMemberTypes.SCH.value
        )
        imis_name_school = name_facts.ImisNameFactoryAmerica(
            id=contact_school.user.username
        )
        imis_name_school.save()

        cc3 = get_contact_class(contact_school)()
        self.assertIsInstance(cc3, proxies.School)


class DuplicateCheckTest(GlobalTestCase):

    def setUp(self):
        self.test_orgs = [
            dict(
                id='-1',
                company="Cyberdyne Systems",
                address1="240 N Wolfe Rd #3A",
                city="Sunnyvale",
                state="CA",
                zip_code='94087',
                email="miles.dyson@cyberdynesystems.com,",
                phone='408-830-2890 x31',
                ein_number='55876342',
                company_record=True
            ),
            dict(
                id='-2',
                company="Cyberdyne Systems, Inc.",
                address1="240 North Wolfe Road",
                address2="Ste. 3A",
                city="Sunnyvale",
                state="CA",
                zip_code='94087-4342',
                personal_url="https://cyberdynesystems.com",
                phone='408-830-2893',
                ein_number='55-876342',
                company_record=True
            ),
            dict(
                id='-3',
                company="Cyberdyne",
                address1="240 N. Wolfe Rd.",
                address2="Suite 3A",
                city="Sunnyvale",
                state="CA",
                zip_code='94087',
                country="United States",
                personal_url="http://www.cyberdynesystems.com",
                phone='(408) 830-2894',
                ein_number='55876342',
                company_record=True
            ),
            dict(
                id='-4',
                company="Cybernetics Industries",
                address1="421 Main St",
                city="Clarion",
                state="PA",
                zip_code='16214-1024',
                country="United States",
                personal_url="cyberneticsindustries.com",
                phone='(814) 226-4000x2801',
                company_record=True
            ),
            dict(
                id='-5',
                company='The Galactic Federation of Planets',
                address1='284 N Wolfe Rd',
                address2='Unit Q',
                city='Sunnyvale',
                state='CA',
                zip_code='94085',
                country='United States',
                personal_url='https://starfleet.gov',
                phone='(408) 655-6452',
                company_record=True
            )
        ]
        self.name_records = [self.build_name_record(x) for x in self.test_orgs]
        self.name_address_records = [self.build_name_address_record(x) for x in self.test_orgs]

    @staticmethod
    def build_name_record(org_data):
        name = name_facts.ImisNameFactoryBlank(
            id=org_data.get('id'),
            company=org_data.get('company', ''),
            city=org_data.get('city', ''),
            state_province=org_data.get('state', ''),
            country=org_data.get('country', ''),
            website=org_data.get('personal_url', ''),
            email=org_data.get('email', ''),
            work_phone=org_data.get('phone', ''),
            updated_by='DJANGO_TEST_FACTORY',
            company_record=True
        )
        return name

    @staticmethod
    def build_name_address_record(org_data):
        name_address = ImisNameAddressFactoryBlank(
            id=org_data.get('id'),
            address_num=factory.Sequence(lambda n: str(n + 1000000)),
            purpose='Work Address',
            company=org_data.get('company', ''),
            address_1=org_data.get('address1', ''),
            address_2=org_data.get('address2', ''),
            city=org_data.get('city', ''),
            state_province=org_data.get('state', ''),
            country=org_data.get('country', ''),
            zip=org_data.get('zip_code', ''),
            phone=org_data.get('phone', ''),
            mail_code='DTEST'
        )
        return name_address

    def test_duplicate_check_orgs(self):

        Name.objects.bulk_create(self.name_records)
        NameAddress.objects.bulk_create(self.name_address_records)

        odc = OrgDupeCheck(
            company='Cyberdyne Sys',
            phone='4088302890',
            email='info@cyberdynesystems.com',
            address1='240 n wolfe',
            address2='3A',
            city='Sunnyvale',
            state='CA',
            zip_code='94087',
            country='United States',
            ein_number='55-876342',
            personal_url='https://cyberdynesystems.com'
        )
        self.assertEqual(len(odc.get_candidates()), 2)

    def test_get_string_for_icontains_search(self):
        odc = OrgDupeCheck(
            company='Cyberdyne Systems',
            personal_url='http://cyberdynesystems.com'
        )
        self.assertEqual(
            odc.get_string_for_icontains_search('company'),
            'yberdyne System'
        )
        self.assertEqual(
            odc.get_string_for_icontains_search('personal_url'),
            'ttp://cyberdynesystems.co'
        )

        odc.personal_url = 'http://www.cyberdynesystems.com'
        self.assertEqual(
            odc.get_string_for_icontains_search(
                'personal_url',
                start_idx=odc.personal_url.find('://') + 7
            ),
            'cyberdynesystems.co'
        )

    def test_check_address_does_not_append_to_location_candidates_if_necessary_fields_not_set(self):
        odc = OrgDupeCheck(
            company='American Planning Association',
            address1='205 N Michigan Ave',
            city='Chicago'
        )
        odc.check_company_name()
        odc.check_location()
        self.assertEqual(len(odc.location_candidates), 0)
        odc = OrgDupeCheck(
            company='American Planning Association',
            address1='205 N Michigan Ave',
            city='Chicago',
            state='IL',
            zip_code='60601'
        )
        odc.check_company_name()
        odc.check_location()
        self.assertGreaterEqual(len(odc.location_candidates), 1)
