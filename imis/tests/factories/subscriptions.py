import random
from datetime import datetime
from decimal import Decimal

import factory
from pytz import utc

from imis.models import Subscriptions


TOP_20_PRODUCT_CODES = ('APA', 'FREE_APA', 'AICP', 'JOUR', 'FREE_JAPA', 'CHAPT/FL',
                        'EJOUR', 'CHAPT/TX', 'ZONING', 'TRANS', 'CHAPT/CAN', 'CHAPT/CAL',
                        'CHAPT/IL', 'CHAPT/NYM', 'CITY_PLAN', 'CHAPT/VA', 'ENVIRON'
                        'URBAN_DES', 'PLANNING', 'CHAPT/WA')

PRODUCT_TYPES = ('DUES', 'CHAPT', 'SUB', 'SEC', 'MISC')

STATUSES = ('I', 'A', 'IW', 'S', 'D')

TOP_20_SOURCE_CODES = ('', 'WEB', 'STUDENT', 'FREESTUDENT_UPLOAD', 'MREN', 'NAMECHANGE',
                       'LATE', 'Renewal', 'MREG', 'COMP', 'NOCODE', 'CONF', 'M8IY',
                       'M7IY', 'MPI', 'JRG_CONVERT', 'AICP', 'TELE', 'AUTODRAFT', 'Conversion')

TOP_10_CAMPAIGN_CODES = ('', 'WEB', 'MREN', 'LATE', 'NOCODE', 'AICP', 'M7IY', 'NAMECHANGE',
                         'EARLY', 'M6IY')


class ImisSubscriptionFactory(factory.Factory):

    id = factory.Sequence(lambda n: str(n + 10000000))
    product_code = random.choice(TOP_20_PRODUCT_CODES)
    bt_id = ''
    prod_type = random.choice(PRODUCT_TYPES)
    begin_date = factory.Faker('date_time_this_decade', tzinfo=utc)
    paid_thru = factory.Faker('future_date', tzinfo=utc)
    copies = random.choice((0, 1, 2, 3))
    source_code = random.choice(TOP_20_SOURCE_CODES)  # foreign key to SourceCodes ?
    first_subscribed = factory.Faker('date_time_this_decade', tzinfo=utc)
    continuous_since = factory.Faker('date_time_this_decade', tzinfo=utc)
    prior_years = 0
    future_copies = 0
    future_copies_date = factory.Faker('future_date', tzinfo=utc)
    pref_mail = 0
    pref_bill = 0
    renew_months = random.choice((0, 12))
    mail_code = ''
    previous_balance = Decimal(0)
    bill_date = factory.Faker('date_time_this_decade', tzinfo=utc)
    reminder_date = factory.Faker('date_time_this_decade', tzinfo=utc)
    reminder_count = random.choice((0, 1))
    bill_begin = factory.Faker('date_time_this_year', tzinfo=utc, after_now=180)
    bill_thru = datetime((datetime.today().year + 1), 9, 30)
    bill_amount = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    bill_copies = random.choice((0, 1))
    payment_amount = factory.Faker('pydecimal', left_digits=random.choice((2, 3)),
                                   right_digits=2, positive=True)
    payment_date = factory.Faker('date_time_this_year', tzinfo=utc)
    paid_begin = datetime(datetime.today().year, 10, 1)
    last_paid_thru = datetime((datetime.today().year + 1), 9, 30)
    copies_paid = random.choice((0, 1))
    adjustment_amount = random.choice((Decimal(0), Decimal(75), Decimal(130)))
    ltd_payments = random.choice([Decimal(x) for x in range(0, 75, 5)])
    issues_printed = ''
    balance = random.choice([Decimal(x) for x in range(0, 200, 5)])
    cancel_reason = ''
    years_active_string = ''
    last_issue = ''
    last_issue_date = factory.Faker('date_time_this_decade', tzinfo=utc)
    date_added = factory.Faker('date_time_this_decade', tzinfo=utc)
    last_updated = factory.Faker('date_time_this_decade', tzinfo=utc)

    # XXX ACHTUNG DANGER PELIGRO!
    # WARNING: DO NOT CHANGE THIS UNLESS YOU ARE SURE YOU KNOW WHAT YOU'RE DOING!
    # tearDownClass classmethods of unit tests use this as value to test for deletion
    updated_by = 'DJANGO_TEST_FACTORY'

    intent_to_edit = ''
    flag = ''
    bill_type = random.choice(('', '0', 'A'))
    complimentary = random.choice((True, False))
    future_credits = Decimal(0)
    invoice_reference_num = 0
    invoice_line_num = 0
    campaign_code = random.choice(TOP_10_CAMPAIGN_CODES)
    appeal_code = random.choice(('', 'Renewal'))
    org_code = random.choice(('', 'APA'))
    is_fr_item = False
    fair_market_value = Decimal(0)
    is_group_admin = False

    class Meta:
        model = Subscriptions
