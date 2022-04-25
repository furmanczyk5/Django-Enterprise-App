import random

import factory
from pytz import utc

from imis.models import Activity as ImisActivity
from imis.tests.factories.name import MEMBER_TYPES
from imis.tests.factories.subscriptions import TOP_20_PRODUCT_CODES


TOP_20_ACTIVITY_TYPES = (
    'DUES', 'MEETFUNC', 'MEETING', 'APA_JOIN', 'CUSTOMER',
    'SALES', 'CONV_MT', 'MEETING_AN', 'ARC_ECP_ST', 'EMAIL',
    'INFO_RECVD', 'REFUND', 'STU_SEC', 'ORDER', 'ARC_CATE',
    'COMMITTEE', 'AICP', 'INFO_SENT', 'STU_RENEW', 'STU_PAN'
)

TOP_20_OTHER_CODES = (
    'DUES', '', 'CHAPT', 'SUB', 'SEC', 'SALES',
    'MEETING', 'STU', 'MEET', 'Chapter Conference', 'P900',
    'MAIN', 'M001', 'P901', 'R01', 'L01',
    'FULL', 'MEM', 'M002', 'DISC', 'MAIN1'
)


class ImisActivityFactory(factory.Factory):

    seqn = factory.Sequence(lambda n: str(n + 1000000))
    id = factory.Sequence(lambda n: str(n + 1000000))
    activity_type = random.choice(TOP_20_ACTIVITY_TYPES)
    transaction_date = factory.Faker('date_time_this_decade', tzinfo=utc)
    effective_date = factory.Faker('date_time_this_decade', tzinfo=utc)
    product_code = random.choice(TOP_20_PRODUCT_CODES)
    other_code = random.choice(TOP_20_OTHER_CODES)
    description = random.choice(('APA Membership', 'AICP Membership', '', 'Journal Subscription'))
    source_system = random.choice((
        'DUES', 'MEETING', '', 'DJANGO', 'AR', 'ORDER', 'SALES', 'LETTER', 'OUTLOOK', 'AUTODRAFT'
    ))
    source_code = 'DJANGO_TEST_FACTORY'
    quantity = random.choice((0, 1))
    amount = random.choice(range(0, 150, 5))
    category = ''
    units = 0
    member_type = random.choice(MEMBER_TYPES)
    action_codes = random.choice((
        'A', '', 'MEM', 'STU', 'ADD', 'SPKM', 'FULL', 'FMEM', 'NOM', 'PBM'
    ))

    class Meta:
        model = ImisActivity

