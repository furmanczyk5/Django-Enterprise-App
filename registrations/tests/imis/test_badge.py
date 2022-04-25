from unittest import mock, TestCase

from planning.global_test_case import GlobalTestCase
from ...imis import Badge, format_location
from ..support import MockRow


class BadgeTest(GlobalTestCase):

    def setUp(self):
        self.db_patcher = mock.patch('registrations.imis.badge.DbAccessor')
        mock_db = self.db_patcher.start()
        self.db_instance = mock_db.return_value
        self.id = self.administrator.username

        self.badge = Badge()

    def tearDown(self):
        self.db_patcher.stop()

    def test_read_returns_empty_dict_when_row_is_None(self):
        self.db_instance.get_row.return_value = None
        badge = self.badge.get(self.id)
        self.assertEqual({}, badge)

    def test_read_returns_dict_of_row_data(self):
        row = MockRow()
        self.db_instance.get_row.return_value = row
        badge = self.badge.get(self.id)
        expected_badge = {
            'badge_name':  row.FIRST_NAME,
            'badge_company': row.COMPANY,
            'badge_location': '{}, {}'.format(row.CITY, row.STATE_PROVINCE),
            'address1': row.ADDRESS_1,
            'address2': row.ADDRESS_2,
            'city': row.CITY,
            'state': row.STATE_PROVINCE,
            'country': row.COUNTRY,
            'zip_code': row.ZIP,
        }
        self.assertEqual(expected_badge, badge)


class FormatLocationTest(TestCase):

    def test_returns_city_and_state_province_for_US(self):
        row = MockRow()
        self.assertEqual(
            '{}, {}'.format(row.CITY, row.STATE_PROVINCE),
            format_location(row)
        )

    def test_returns_city_and_country_outside_US(self):
        row = MockRow('Germany')
        self.assertEqual(
            '{}, {}'.format(row.CITY, row.COUNTRY),
            format_location(row)
        )
