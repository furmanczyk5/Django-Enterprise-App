from django.test import TestCase

from imis.tests.factories.name_address import ImisNameAddressFactoryAmerica


class NameAddressTestCase(TestCase):

    def test_get_full_address(self):
        apa_office = ImisNameAddressFactoryAmerica(
            id='999999',
            address_1='205 N Michigan Ave',
            address_2='Suite 1200',
            city='Chicago',
            state_province='IL',
            zip='60601',
            country='United States'
        )
        self.assertMultiLineEqual(
            apa_office.get_full_address(),
            '205 N Michigan Ave\rSuite 1200\rChicago, IL 60601\rUNITED STATES'
        )

        no_address_2 = ImisNameAddressFactoryAmerica(
            id='999999',
            address_1='205 N Michigan Ave',
            address_2='',
            city='Chicago',
            state_province='IL',
            zip='60601',
            country='United States'
        )
        self.assertMultiLineEqual(
            no_address_2.get_full_address(),
            '205 N Michigan Ave\rChicago, IL 60601\rUNITED STATES'
        )

    def test_get_company_sort(self):
        company = ImisNameAddressFactoryAmerica(
            company='Lincoln Institute of Land Policy'
        )
        self.assertEqual(
            company.get_company_sort(),
            'LINCOLN INSTITUTE OF LAND POLI'
        )

        the_company = ImisNameAddressFactoryAmerica(
            company='The Pew Charitable Trusts'
        )
        self.assertEqual(
            the_company.get_company_sort(),
            'PEW CHARITABLE TRUSTS'
        )

        startswiththe = ImisNameAddressFactoryAmerica(
            company='Themistocleous And Associates'
        )
        self.assertEqual(
            startswiththe.get_company_sort(),
            'THEMISTOCLEOUS AND ASSOCIATES'
        )
