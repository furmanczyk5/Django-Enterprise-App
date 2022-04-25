from unittest import TestCase, skip
from ...utils import PurchaseInfo, REGULAR, SOLDOUT


IMIS_CODE = '19CONF/NPC123'


class MockProduct(object):
    imis_code = IMIS_CODE


class MockUser(object):
    username = '12345'


class MockEventFunction(object):
    event_function_id = IMIS_CODE
    regular_capacity = 100
    standby_capacity = 10
    regular_max_quantity_per_registrant = 2
    standby_max_quantity_per_registrant = 1
    total_regular_purchased = 0
    total_standby_purchased = 0
    user_regular_purchased = 0
    user_standby_purchased = 0
    user_regular_in_cart = 0
    user_standby_in_cart = 0


@skip
class TestPurchaseInfo(TestCase):
    def setUp(self):
        self.product = MockProduct()
        self.user = MockUser()
        self.purchase_info = PurchaseInfo(
            MockProduct(), MockUser(), MockEventFunction()
        )

    def test_returns_regular_capacity_of_event(self):
        self.assertEqual(100, self.purchase_info.regular_capacity())

    def test_returns_standby_capacity_of_event(self):
        self.assertEqual(10, self.purchase_info.standby_capacity())

    def test_soldout_is_False_if_regular_tickets_available(self):
        event_function = MockEventFunction()
        event_function.total_standby_purchased = 10
        purchase_info = PurchaseInfo(
            self.product, self.user, event_function
        )
        self.assertFalse(purchase_info.soldout())

    def test_soldout_is_False_if_regular_soldout_but_standby_available(self):
        event_function = MockEventFunction()
        event_function.total_regular_purchased = 100
        purchase_info = PurchaseInfo(
            self.product, self.user, event_function
        )
        self.assertFalse(purchase_info.soldout())

    def test_soldout_is_True_if_no_tickets_available(self):
        event_function = MockEventFunction()
        event_function.total_standby_purchased = 10
        event_function.total_regular_purchased = 100
        purchase_info = PurchaseInfo(
            self.product, self.user, event_function
        )
        self.assertTrue(purchase_info.soldout())

    def test_status_is_SOLDOUT_if_soldout(self):
        event_function = MockEventFunction()
        event_function.total_standby_purchased = 10
        event_function.total_regular_purchased = 100
        purchase_info = PurchaseInfo(
            self.product, self.user, event_function
        )
        self.assertEqual(SOLDOUT, purchase_info.product_sale_status())

    def test_status_is_REGULAR_if_regular_tickets_available(self):
        event_function = MockEventFunction()
        event_function.total_standby_purchased = 10
        purchase_info = PurchaseInfo(
            self.product, self.user, event_function
        )
        self.assertEqual(REGULAR, purchase_info.product_sale_status())

    def test_status_is_STANDBY_if_regular_soldout_but_standby_available(self):
        event_function = MockEventFunction()
        event_function.total_regular_purchased = 100
        purchase_info = PurchaseInfo(
            self.product, self.user, event_function
        )
        self.assertEqual(STANDBY, purchase_info.product_sale_status())

    def test_purchase_quantity_is_regular_max_when_regular_available(self):
        self.assertEqual(2, self.purchase_info.user_allowed_to_purchase())

    def test_purchase_quantity_is_standby_max_if_regular_soldout_but_standby_available(self):
        event_function = MockEventFunction()
        event_function.total_regular_purchased = 100
        purchase_info = PurchaseInfo(
            self.product, self.user, event_function
        )
        self.assertEqual(1, purchase_info.user_allowed_to_purchase())

    def test_purchase_quantity_is_lesser_of_regular_remaining_and_max_remaining(self):
        event_function = MockEventFunction()
        event_function.standby_max_quantity_per_registrant = 0
        event_function.total_regular_purchased = 99
        purchase_info = PurchaseInfo(
            self.product, self.user, event_function
        )
        self.assertEqual(1, purchase_info.user_allowed_to_purchase())

    def test_purchase_quantity_is_remaining_regular_when_limited_regular_available(self):
        event_function = MockEventFunction()
        event_function.total_regular_purchased = 99
        purchase_info = PurchaseInfo(
            self.product, self.user, event_function
        )
        self.assertEqual(1, purchase_info.user_allowed_to_purchase())

    def test_purchase_quantity_is_lesser_of_standby_remaining_and_max_standing(self):
        event_function = MockEventFunction()
        event_function.standby_max_quantity_per_registrant = 4
        event_function.total_regular_purchased = 100
        event_function.total_standby_purchased = 7
        purchase_info = PurchaseInfo(
            self.product, self.user, event_function
        )
        self.assertEqual(3, purchase_info.user_allowed_to_purchase())

    def test_add_quantity_is_regular_max_when_regular_available_and_none_in_cart(self):
        self.assertEqual(2, self.purchase_info.user_allowed_to_add())

    def test_add_quantity_is_regular_max_minus_cart_and_purchased_amount_when_regular_available(self):
        event_function = MockEventFunction()
        event_function.user_regular_purchased = 1
        event_function.user_regular_in_cart = 1
        purchase_info = PurchaseInfo(
            self.product, self.user, event_function
        )
        self.assertEqual(0, purchase_info.user_allowed_to_add())

    def test_add_quantity_is_standby_max_if_regular_soldout_but_standby_available(self):
        event_function = MockEventFunction()
        event_function.total_regular_purchased = 100
        purchase_info = PurchaseInfo(
            self.product, self.user, event_function
        )
        self.assertEqual(1, purchase_info.user_allowed_to_add())

    def test_add_quantity_is_lesser_of_regular_remaining_and_max_remaining_if_no_standby(self):
        event_function = MockEventFunction()
        event_function.standby_max_quantity_per_registrant = 0
        event_function.total_regular_purchased = 99
        purchase_info = PurchaseInfo(
            self.product, self.user, event_function
        )
        self.assertEqual(1, purchase_info.user_allowed_to_add())

    def test_add_quantity_is_zero_when_regular_max_purchased_with_standby_available_only(self):
        event_function = MockEventFunction()
        event_function.user_regular_purchased = 2
        purchase_info = PurchaseInfo(
            self.product, self.user, event_function
        )
        self.assertEqual(0, purchase_info.user_allowed_to_add())

    def test_add_quantity_is_remaining_regular_when_limited_regular_available(self):
        event_function = MockEventFunction()
        event_function.total_regular_purchased = 99
        purchase_info = PurchaseInfo(
            self.product, self.user, event_function
        )
        self.assertEqual(1, purchase_info.user_allowed_to_add())

    def test_add_quantity_is_lesser_of_standby_remaining_and_max_standing(self):
        event_function = MockEventFunction()
        event_function.standby_max_quantity_per_registrant = 4
        event_function.total_regular_purchased = 100
        event_function.total_standby_purchased = 7
        purchase_info = PurchaseInfo(
            self.product, self.user, event_function
        )
        self.assertEqual(3, purchase_info.user_allowed_to_add())
