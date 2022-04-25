import random
from datetime import datetime, timedelta

import factory
import pytz
from django.conf import settings

from imis import models
from myapa.models import constants

# :attr:`imis.models.Name.member_type`
# MEM: Member
# NOM: Non-member
# STU: Student
# RET: Retired
# LIFE: Life
MEMBER_TYPES = (
    'ADMIN', 'AGC', 'CHP', 'DEC', 'EXC', 'FCLTI', 'FCLTS', 'GPBM', 'LIB', 'LIFE',
    'MEDIA', 'MEM', 'MWEB', 'NM', 'NOM', 'PAGC', 'PPRI', 'PRI', 'PRO', 'PSCH', 'PSTU', 'PWEB',
    'RET', 'SCH', 'STF', 'STU', 'SUB', 'SWEB', 'WEB', 'XALUM', 'XDIV', 'XFCLI', 'XFCLS', 'XFCLT',
    'XFSTU', 'XGPBM', 'XLIFE', 'XMEM', 'XMWEB', 'XNOM', 'XNP', 'XPBM', 'XRET',
    'XSTF', 'XSTU', 'XSWEB', 'XXSTF', 'XXSTU'
)

# :attr:`imis.models.Name.category`
CATEGORIES = ('CHAPT', 'NM1', 'NM2')

# :attr:`imis.models.Name.status`
STATUSES = ('A', 'D', 'I')

# :attr:`imis.models.Name.title`
TOP_20_TITLES = (
    'Planner', 'Senior Planner', 'Director', 'President', 'Student',
    'Planning Commissioner', 'Executive Director', 'Project Manager', 'Associate Planner',
    'Planning Director', 'Principal Planner', 'Professor', 'Transportation Planner', 'City Planner',
    'Vice President', 'Assistant Professor', 'Planner II', 'Associate Professor', 'Owner'
)

# :attr:`imis.models.Name.company`
TOP_20_COMPANIES = (
    'AECOM', 'American Planning Association', 'Parsons Brinckerhoff', 'Arizona State University',
    'URS Corporation', 'Cornell University', 'City of Austin', 'City of Los Angeles',
    'City of Portland', 'University of Minnesota', 'University of Washington', 'National Park Service',
    'University of Cincinnati', 'City of San Antonio', 'Columbia University', 'University of Pennsylvania',
    'University of Florida', 'HNTB Corporation', 'JACOBS', 'University of Michigan'
)

ORG_CODES = list(constants.IMIS_ORGANIZATION_TYPES_CODES.values())

MEMBER_STATUSES = ('D', 'R', 'N', 'S')

CO_MEMBER_TYPES = ('AGC', 'PRI', 'SCH', 'PAGC', 'LIB', 'PPRI',
                   'SUB', 'PSCH', 'SPL', 'CHP', 'EXC', 'DVN',
                   )

CHAPTERS = [x[0] for x in constants.CHAPTER_CHOICES]
CHAPTERS.append('')

FUNCTIONAL_TITLES = [x[0] for x in constants.FUNCTIONAL_TITLE_CHOICES]
FUNCTIONAL_TITLES.append('')

SOURCE_CODE_CHOICES = ('', 'WEB', 'WEB-SMM', 'CA CHAP', 'CHAPONLY')


class ImisNameFactory(factory.Factory):
    """An abstract factory_boy Factory for creating :class:`imis.models.Name` models"""

    id = factory.Sequence(lambda n: str(n + 1000000))
    org_code = random.choice(ORG_CODES)
    member_type = random.choice(MEMBER_TYPES)
    category = random.choice(CATEGORIES)
    status = random.choice(STATUSES)
    major_key = ''
    co_id = ''
    last_first = ''
    company_sort = ''
    bt_id = ''
    dup_match_key = ''
    full_name = ''
    title = random.choice(TOP_20_TITLES)
    company = random.choice(TOP_20_COMPANIES)
    full_address = ''
    prefix = ''
    first_name = ''
    middle_name = ''
    last_name = ''
    suffix = ''
    designation = ''
    informal = ''
    work_phone = ''
    home_phone = ''
    fax = ''
    toll_free = ''
    city = ''
    state_province = ''
    zip = ''
    country = ''
    mail_code = ''
    crrt = ''
    bar_code = ''
    county = ''
    mail_address_num = 0
    bill_address_num = 0
    gender = ''

    # Passing in a datetime.date, like Faker.date_of_birth, will cause annoying
    # RuntimeWarnings about naive datetimes being used while time zone support
    # is active (assumming because the imis.models.Name field is a
    # DateTimeField, not DateField).
    birth_date = factory.Faker('date_time_this_century', tzinfo=pytz.utc)

    us_congress = ''
    state_senate = ''
    state_house = ''
    sic_code = ''
    chapter = random.choice(CHAPTERS)
    functional_title = random.choice(FUNCTIONAL_TITLES)
    contact_rank = 0
    member_record = random.choice((True, False))
    company_record = random.choice((True, False))
    join_date = factory.Faker('date_time_this_decade', tzinfo=pytz.utc)
    source_code = random.choice(SOURCE_CODE_CHOICES)
    paid_thru = datetime.utcnow() + timedelta(days=365)
    member_status = random.choice(MEMBER_STATUSES)
    member_status_date = factory.Faker('date_time_this_year', tzinfo=pytz.utc)
    previous_mt = random.choice(MEMBER_TYPES)
    mt_change_date = factory.Faker('date_time_this_decade', tzinfo=pytz.utc)
    co_member_type = random.choice(CO_MEMBER_TYPES)
    exclude_mail = random.choice((True, False))
    exclude_directory = random.choice((True, False))
    date_added = factory.Faker('date_time_this_decade', tzinfo=pytz.utc)
    last_updated = factory.Faker('date_time_this_year', tzinfo=pytz.utc)

    # XXX ACHTUNG DANGER PELIGRO!
    # WARNING: DO NOT CHANGE THIS UNLESS YOU ARE SURE YOU KNOW WHAT YOU'RE DOING!
    # tearDownClass classmethods of unit tests use this as value to test for deletion
    updated_by = 'DJANGO_TEST_FACTORY'

    address_num_1 = 0
    address_num_2 = 0
    address_num_3 = 0
    email = factory.Faker('email')
    website = factory.Faker('url')
    ship_address_num = 0
    display_currency = ''
    mobile_phone = ''

    class Meta:
        model = models.Name


class ImisNameFactoryBlank(factory.Factory):
    """
    A factory for creating Name objects with all optional fields as empty strings
    """

    org_code = ''
    member_type = ''
    category = ''
    status = ''
    major_key = ''
    co_id = ''
    last_first = ''
    company_sort = ''
    bt_id = ''
    dup_match_key = ''
    full_name = ''
    title = ''
    company = ''
    full_address = ''
    prefix = ''
    first_name = ''
    middle_name = ''
    last_name = ''
    suffix = ''
    designation = ''
    informal = ''
    work_phone = ''
    home_phone = ''
    fax = ''
    toll_free = ''
    city = ''
    state_province = ''
    zip = ''
    country = ''
    mail_code = ''
    crrt = ''
    bar_code = ''
    county = ''
    mail_address_num = 0
    bill_address_num = 0
    gender = ''
    birth_date = '1900-01-01'
    us_congress = ''
    state_senate = ''
    state_house = ''
    sic_code = ''
    chapter = ''
    functional_title = ''
    contact_rank = 0
    member_record = False
    company_record = False
    join_date = datetime.now(tz=pytz.timezone(settings.TIME_ZONE))
    source_code = ''
    paid_thru = datetime.now(tz=pytz.timezone(settings.TIME_ZONE))
    member_status = ''
    member_status_date = datetime.now(tz=pytz.timezone(settings.TIME_ZONE))
    previous_mt = ''
    mt_change_date = datetime.now(tz=pytz.timezone(settings.TIME_ZONE))
    co_member_type = ''
    exclude_mail = False
    exclude_directory = False
    date_added = datetime.now(tz=pytz.timezone(settings.TIME_ZONE))
    last_updated = datetime.now(tz=pytz.timezone(settings.TIME_ZONE))
    updated_by = 'WEBUSER'
    intent_to_edit = ''
    address_num_1 = 0
    address_num_2 = 0
    address_num_3 = 0
    email = ''
    website = ''
    ship_address_num = 0
    display_currency = ''
    mobile_phone = ''

    class Meta:
        model = models.Name


class ImisNameFactoryMember(ImisNameFactory):
    company_record = False
    member_record = True


class ImisNameFactoryCompany(ImisNameFactory):
    company_record = True
    member_record = False
    company = factory.Faker('company')


class ImisNameFactoryAmerica(ImisNameFactory):
    first_name = factory.Faker('first_name', locale='en_US')
    last_name = factory.Faker('last_name', locale='en_US')
    # iMIS 20-character limit...(╯°□°）╯︵ ┻━┻
    # work_phone = factory.Faker('phone_number', locale='en_US')
    # home_phone = factory.Faker('phone_number', locale='en_US')


class ImisNameFactoryCanada(ImisNameFactory):
    first_name = factory.Faker('first_name', locale='en_CA')
    last_name = factory.Faker('last_name', locale='en_CA')
    work_phone = factory.Faker('phone_number', locale='en_CA')
    home_phone = factory.Faker('phone_number', locale='en_CA')


class ImisNameFactoryIndia(ImisNameFactory):
    first_name = factory.Faker('first_name', locale='hi_IN')
    last_name = factory.Faker('last_name', locale='hi_IN')
    work_phone = factory.Faker('phone_number', locale='hi_IN')
    home_phone = factory.Faker('phone_number', locale='hi_IN')


class ImisNameFactoryAustralia(ImisNameFactory):
    first_name = factory.Faker('first_name', locale='en_AU')
    last_name = factory.Faker('last_name', locale='en_AU')
    work_phone = factory.Faker('phone_number', locale='en_AU')
    home_phone = factory.Faker('phone_number', locale='en_AU')


class ImisNameFactoryChina(ImisNameFactory):
    first_name = factory.Faker('first_name', locale='zh_CN')
    last_name = factory.Faker('last_name', locale='zh_CN')
    work_phone = factory.Faker('phone_number', locale='zh_CN')
    home_phone = factory.Faker('phone_number', locale='zh_CN')


class ImisNameFactoryUK(ImisNameFactory):
    first_name = factory.Faker('first_name', locale='en_GB')
    last_name = factory.Faker('last_name', locale='en_GB')
    work_phone = factory.Faker('phone_number', locale='en_GB')
    home_phone = factory.Faker('phone_number', locale='en_GB')


class ImisNameFactoryJapan(ImisNameFactory):
    first_name = factory.Faker('first_name', locale='ja_JP')
    last_name = factory.Faker('last_name', locale='ja_JP')
    work_phone = factory.Faker('phone_number', locale='ja_JP')
    home_phone = factory.Faker('phone_number', locale='ja_JP')


class ImisNameFactoryIran(ImisNameFactory):
    first_name = factory.Faker('first_name', locale='fa_IR')
    last_name = factory.Faker('last_name', locale='fa_IR')
    work_phone = factory.Faker('phone_number', local='fa_IR')
    home_phone = factory.Faker('phone_number', locale='fa_IR')


class ImisNameFactoryGermany(ImisNameFactory):
    first_name = factory.Faker('first_name', locale='de_DE')
    last_name = factory.Faker('last_name', locale='de_DE')
    work_phone = factory.Faker('phone_number', locale='de_DE')
    home_phone = factory.Faker('phone_number', locale='de_DE')


class ImisNameFactoryArabicGulf(ImisNameFactory):
    first_name = factory.Faker('first_name', locale='ar_SA')
    last_name = factory.Faker('last_name', locale='ar_SA')
    work_phone = factory.Faker('phone_number', locale='ar_SA')
    home_phone = factory.Faker('phone_number', locale='ar_SA')


class ImisNameFactoryItaly(ImisNameFactory):
    first_name = factory.Faker('first_name', locale='it_IT')
    last_name = factory.Faker('last_name', locale='it_IT')
    work_phone = factory.Faker('phone_number', locale='it_IT')
    home_phone = factory.Faker('phone_number', locale='it_IT')


class ImisNameFactoryIndonesia(ImisNameFactory):
    first_name = factory.Faker('first_name', locale='id_ID')
    last_name = factory.Faker('last_name', locale='id_ID')
    work_phone = factory.Faker('phone_number', locale='id_ID')
    home_phone = factory.Faker('phone_number', locale='id_ID')


class ImisNameFactoryKorea(ImisNameFactory):
    first_name = factory.Faker('first_name', locale='ko_KR')
    last_name = factory.Faker('last_name', locale='ko_KR')
    work_phone = factory.Faker('phone_number', locale='ko_KR')
    home_phone = factory.Faker('phone_number', locale='ko_KR')


class ImisNameFactoryNetherlands(ImisNameFactory):
    first_name = factory.Faker('first_name', locale='nl_NL')
    last_name = factory.Faker('last_name', locale='nl_NL')
    work_phone = factory.Faker('phone_number', locale='nl_NL')
    home_phone = factory.Faker('phone_number', locale='nl_NL')


class ImisNameFinFactoryBlank(factory.Factory):
    tax_exempt = ''
    credit_limit = 0
    no_statements = False
    terms_code = ''
    backorders = 0
    renew_months = 0
    bt_id = ''
    tax_author_default = ''
    use_vat_taxation = False
    vat_reg_number = ''
    vat_country = ''

    class Meta:
        model = models.NameFin


class ImisNamePictureFactoryBlank(factory.Factory):
    purpose = ''
    description = ''
    date_added = datetime.now(tz=pytz.timezone(settings.TIME_ZONE))
    last_updated = datetime.now(tz=pytz.timezone(settings.TIME_ZONE))
    updated_by = 'WEBUSER'

    class Meta:
        model = models.NamePicture


class ImisNameSecurityFactoryBlank(factory.Factory):
    login_disabled = False
    web_login = ''
    password = ''
    updated_by = 'WEBUSER'

    class Meta:
        model = models.NameSecurity
