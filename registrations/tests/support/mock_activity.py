from decimal import Decimal


PURCHASE_INFO = {
    'max_quantity': Decimal('300.00'),
    'max_quantity_standby': 0,
    'max_quantity_per_person': 9223372036854775807,
    'total_purchased': Decimal('30.00'),
    'regular_remaining': Decimal('270.00'),
    'standby_remaining': 0,
    'user_total_purchased': 0,
    'user_total_in_cart': 0,
    'user_total': 0,
    'user_allowed_to_add': 100,
    'user_allowed_to_purchase': 100,
    'product_sale_status': 'Regular'
}


class MockActivity():
    product_info = {
            'purchase_info': PURCHASE_INFO
        }
    def get_product(self):
        return MockProduct()


class MockProduct():
    imis_code = '123'
