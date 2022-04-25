import factory

from imis.models import OrderLines


class ImisOrderLinesFactory(factory.Factory):

    order_number = factory.Sequence(lambda n: n + 1000000)
    line_number = 0
    product_code = ''
    location = ''
    lot_serial = ''
    description = ''
    quantity_ordered = 0
    quantity_shipped = 0
    quantity_backordered = 0
    quantity_reserved = 0
    quantity_committed = 0
    number_days = 0
    taxable = False
    taxable_2 = False
    unit_price = 0
    unit_cost = 0
    undiscounted_price = 0
    extended_amount = 0
    extended_cost = 0
    undiscounted_extended_amount = 0
    cancel_code = ''
    cancel_quantity = 0
    commission_rate = 0
    commission_amount = 0
    ceu_type = ''
    ceu_awarded = 0
    pass_fail = ''
    date_confirmed = None
    tickets_printed = 0
    booth_numbers = ''
    note = 'DJANGO_TEST_FACTORY'
    income_account = ''
    unit_weight = 0
    extended_weight = 0
    pst_taxable = False
    is_gst_taxable = False
    added_to_wait_list = None
    bin = ''
    tax_authority = ''
    tax_rate = 0
    tax_1 = 0
    kit_item_type = 0
    discount = 0
    uf_1 = ''
    uf_2 = ''
    uf_3 = ''
    uf_4 = ''
    extended_square_feet = 0
    square_feet = 0
    meet_appeal = ''
    meet_campaign = ''
    fair_market_value = 0
    org_code = ''
    is_fr_item = False
    manual_price = 0
    is_manual_price = False
    unit_tax_amount = 0
    price_from_components = False
    quantity_per_kit = 0

    class Meta:
        model = OrderLines
