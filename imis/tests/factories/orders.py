import random

import factory
from pytz import utc

from imis.models import Orders
from imis.tests.factories.name import MEMBER_TYPES


class ImisOrdersFactory(factory.Factory):

    order_number = factory.Sequence(lambda n: n + 1000000)
    org_code = ''
    order_type_code = ''
    stage = ''
    source_system = ''
    batch_num = ''
    status = ''
    hold_code = ''
    order_date = factory.Faker('date_time_this_decade', tzinfo=utc)
    bt_id = factory.Sequence(lambda n: str(n + 1000000))
    st_id = factory.Sequence(lambda n: str(n + 1000000))
    st_address_num = 0
    entered_date_time = factory.Faker('date_time_this_decade', tzinfo=utc)
    entered_by = 'DJANGO_TEST_FACTORY'
    updated_date_time = factory.Faker('date_time_this_decade', tzinfo=utc)
    updated_by = 'DJANGO_TEST_FACTORY'
    invoice_reference_num = 0
    invoice_number = 0
    invoice_date = factory.Faker('date_time_this_decade', tzinfo=utc)
    number_lines = 0
    full_name = factory.Faker('name')
    title = factory.Faker('job')
    company = factory.Faker('company')
    full_address = factory.Faker('address')
    prefix = ''
    first_name = factory.Faker('first_name')
    middle_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    suffix = ''
    designation = ''
    informal = factory.Faker('first_name')
    last_first = ''
    company_sort = ''
    address_1 = factory.Faker('street_address')
    address_2 = factory.Faker('secondary_address')
    city = factory.Faker('city')
    state_province = factory.Faker('state')
    zip = factory.Faker('postalcode')
    country = factory.Faker('country')
    dpb = ''
    bar_code = ''
    address_format = 0
    phone = random.randrange(1000000000, 9999999999)
    fax = random.randrange(1000000000, 9999999999)
    total_charges = 0
    total_payments = 0
    balance = 0
    line_total = 0
    line_taxable = 0
    freight_1 = 0
    freight_2 = 0
    handling_1 = 0
    handling_2 = 0
    cancellation_fee = 0
    tax_1 = 0
    tax_2 = 0
    tax_3 = 0
    line_pay = 0
    other_pay = 0
    ar_pay = 0
    tax_author_1 = ''
    tax_author_2 = ''
    tax_author_3 = ''
    tax_rate_1 = 0
    tax_rate_2 = 0
    tax_rate_3 = 0
    tax_exempt = ''
    terms_code = ''
    scheduled_date = None
    confirmation_date_time = None
    ship_papers_date_time = None
    shipped_date_time = None
    bo_released_date_time = None
    source_code = ''
    salesman = ''
    commission_rate = 0
    discount_rate = 0
    priority = 0
    hold_comment = ''
    affect_inventory = False
    hold_flag = False
    customer_reference = ''
    valuation_basis = 0
    undiscounted_total = 0
    auto_calc_handling = False
    auto_calc_restocking = False
    backorders = 0
    member_type = random.choice(MEMBER_TYPES)
    pay_type = ''
    pay_number = ''
    credit_card_expires = ''
    authorize = ''
    credit_card_name = ''
    bo_status = 0
    bo_release_date = None
    total_quantity_ordered = 0
    total_quantity_backordered = 0
    ship_method = ''
    total_weight = 0
    cash_gl_acct = ''
    line_pst_taxable = 0
    intent_to_edit = ''
    prepaid_invoice_reference_num = 0
    auto_calc_freight = False
    co_id = ''
    co_member_type = ''
    email = ''
    crrt = ''
    address_status = ''
    recognized_cash_amount = 0
    is_fr_order = 0
    vat_tax_code_fh = ''
    encrypt_pay_number = ''
    encrypt_credit_card_expires = ''
    auto_freight_type = 0
    use_member_price = False
    st_print_company = False
    st_print_title = False
    toll_free = ''
    mail_code = ''
    address_3 = ''
    encrypt_csc = ''
    issue_date = ''
    issue_number = ''
    more_payments = 0
    gateway_ref = ''
    originating_trans_num = 0
    freight_tax = 0
    handling_tax = 0
    tax_rate_fh = 0
    discount_code = ''

    class Meta:
        model = Orders
