import factory

from imis.models import Product


class ImisProductFactory(factory.Factory):

    product_code = factory.Sequence(lambda n: str(n + 1000000))
    product_major = ''
    product_minor = ''
    prod_type = ''
    category = ''
    title_key = ''
    title = ''
    description = ''
    status = ''
    note = None
    group_1 = ''
    group_2 = ''
    group_3 = ''
    price_rules_exist = False
    lot_serial_exist = False
    payment_priority = 0
    renew_months = 0
    prorate = ''
    stock_item = False
    unit_of_measure = ''
    weight = 0
    taxable = False
    commisionable = False
    commision_percent = 0
    decimal_points = 0
    income_account = ''
    deferred_income_account = ''
    inventory_account = ''
    adjustment_account = ''
    cog_account = ''
    intent_to_edit = 'DJANGO_TEST_FACTORY'
    price_1 = 0
    price_2 = 0
    price_3 = 0
    complimentary = False
    attributes = ''
    pst_taxable = False
    taxable_value = 0
    org_code = ''
    tax_authority = ''
    web_option = 0
    image_url = ''
    apply_image = False
    is_kit = False
    info_url = ''
    apply_info = False
    plp_code = ''
    promote = False
    thumbnail_url = ''
    apply_thumbnail = False
    catalog_desc = None
    web_desc = None
    other_desc = None
    location = ''
    premium = False
    fair_market_value = 0
    is_fr_item = False
    appeal_code = ''
    campaign_code = ''
    price_from_components = False
    publish_start_date = None
    publish_end_date = None
    tax_by_location = False
    taxcategory_code = ''
    related_content_message = None

    class Meta:
        model = Product
