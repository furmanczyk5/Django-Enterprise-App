from unittest import mock

from planning.global_test_case import GlobalTestCase
from ..views import CustomizeBadgeView
from .support import MockRow
from ..imis import Badge


class CustomizeBadgeViewTest(GlobalTestCase):
    def setUp(self):
        self.view = CustomizeBadgeView()
        self.view.user = self.administrator

    @mock.patch('registrations.imis.badge.DbAccessor')
    def test_initial_data(self, mock_db):
        instance = mock_db.return_value
        instance.get_row.return_value = MockRow()
        self.view.badge = Badge().get(self.view.user.username)
        initial = self.view.get_initial()
        self.assertEqual(initial['badge_name'], 'Robert')
        self.assertEqual(initial['badge_company'], 'Acme')
        self.assertEqual(initial['badge_location'], 'Phoenix, AZ')
        self.assertEqual(initial['address1'], '123 Lane')
        self.assertEqual(initial['address2'], 'Apt 123')
        self.assertEqual(initial['city'], 'Phoenix')
        self.assertEqual(initial['state'], 'AZ')
        self.assertEqual(initial['country'], 'United States')
        self.assertEqual(initial['zip_code'], '54321')
