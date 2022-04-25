import random

import factory
from pytz import utc

from imis import models
from imis.tests.factories.name import TOP_20_COMPANIES
from myapa.models.constants import ADDRESS_TYPES

# :attr:`imis.models.NameAddress.purpose`
PURPOSES = [x[1] for x in ADDRESS_TYPES]


class ImisNameAddressFactory(factory.Factory):
    """An abstract factory_boy Factory for creating :class:`imis.models.NameAddress` models"""

    # start above 10,000,000 to avoid conflicts with existing ids
    id = factory.Sequence(lambda n: str(n + 10000000))
    address_num = factory.Sequence(lambda n: n + 10000000)
    purpose = random.choice(PURPOSES)
    company = random.choice(TOP_20_COMPANIES)
    crrt = ''
    dpb = ''
    bar_code = ''
    country_code = ''
    address_format = 0  # TODO: Investigate this, can be 0, 5, or 7 but almost all are 0

    # XXX ACHTUNG DANGER PELIGRO!
    # WARNING: DO NOT CHANGE THIS UNLESS YOU ARE SURE YOU KNOW WHAT YOU'RE DOING!
    # tearDownClass classmethods of unit tests use this as value to test for deletion
    mail_code = 'DTEST'

    full_address = ''

    county = ''
    us_congress = ''
    state_senate = ''
    state_house = ''
    fax = ''
    toll_free = ''
    company_sort = ''
    note = ''
    status = ''
    last_updated = factory.Faker('date_time_this_decade', tzinfo=utc)
    list_string = ''
    preferred_mail = False
    preferred_bill = False
    last_verified = factory.Faker('date_time_this_decade', tzinfo=utc)
    email = ''
    bad_address = ''
    no_autoverify = False
    last_qas_batch = factory.Faker('date_time_this_decade', tzinfo=utc)
    address_3 = ''
    preferred_ship = random.choice((True, False))
    informal = ''
    title = ''

    class Meta:
        model = models.NameAddress


class ImisNameAddressFactoryAmerica(ImisNameAddressFactory):
    address_1 = factory.Faker('street_address', locale='en_US')
    address_2 = random.choice(('', factory.Faker('secondary_address', locale='en_US')))
    city = factory.Faker('city', locale='en_US')
    state_province = factory.Faker('state_abbr', locale='en_US')
    zip = random.choice((
        factory.Faker('postalcode', locale='en_US'),
        factory.Faker('postalcode_plus4', locale='en_US')
    ))
    country = 'United States'
    phone = factory.Faker('phone_number', locale='en_US')


class ImisNameAddressFactoryCanada(ImisNameAddressFactory):
    address_1 = factory.Faker('street_address', locale='en_CA')
    address_2 = random.choice(('', factory.Faker('secondary_address', locale='en_CA')))
    city = factory.Faker('city', locale='en_CA')
    state_province = factory.Faker('state_abbr', locale='en_CA')
    zip = factory.Faker('postalcode', locale='en_CA')
    country = 'Canada'
    phone = factory.Faker('phone_number', locale='en_CA')


class ImisNameAddressFactoryIndia(ImisNameAddressFactory):
    address_1 = factory.Faker('street_address', locale='hi_IN')
    address_2 = random.choice(('', factory.Faker('secondary_address', locale='hi_IN')))
    city = factory.Faker('city', locale='hi_IN')
    state_province = factory.Faker('state_abbr', locale='hi_IN')
    zip = factory.Faker('postalcode', locale='hi_IN')
    country = 'India'
    phone = factory.Faker('phone_number', locale='hi_IN')


class ImisNameAddressFactoryAustralia(ImisNameAddressFactory):
    address_1 = factory.Faker('street_address', locale='en_AU')
    address_2 = random.choice(('', factory.Faker('secondary_address', locale='en_AU')))
    city = factory.Faker('city', locale='en_AU')
    state_province = factory.Faker('state_abbr', locale='en_AU')
    zip = factory.Faker('postalcode', locale='en_AU')
    country = 'Australia'
    phone = factory.Faker('phone_number', locale='en_AU')


class ImisNameAddressFactoryChina(ImisNameAddressFactory):
    address_1 = factory.Faker('street_address', locale='zh_CN')
    address_2 = random.choice(('', factory.Faker('secondary_address', locale='zh_CN')))
    city = factory.Faker('city', locale='zh_CN')
    state_province = factory.Faker('state_abbr', locale='zh_CN')
    zip = factory.Faker('postalcode', locale='zh_CN')
    country = 'China'
    phone = factory.Faker('phone_number', locale='zh_CN')


class ImisNameAddressFactoryUK(ImisNameAddressFactory):
    address_1 = factory.Faker('street_address', locale='en_GB')
    address_2 = random.choice(('', factory.Faker('secondary_address', locale='en_GB')))
    city = factory.Faker('city', locale='en_GB')
    state_province = factory.Faker('state_abbr', locale='en_GB')
    zip = factory.Faker('postalcode', locale='en_GB')
    country = 'United Kingdom'
    phone = factory.Faker('phone_number', locale='en_GB')


class ImisNameAddressFactoryJapan(ImisNameAddressFactory):
    address_1 = factory.Faker('street_address', locale='ja_JP')
    address_2 = random.choice(('', factory.Faker('secondary_address', locale='ja_JP')))
    city = factory.Faker('city', locale='ja_JP')
    state_province = factory.Faker('state_abbr', locale='ja_JP')
    zip = factory.Faker('postalcode', locale='ja_JP')
    country = 'Japan'
    phone = factory.Faker('phone_number', locale='ja_JP')


class ImisNameAddressFactoryIran(ImisNameAddressFactory):
    address_1 = factory.Faker('street_address', locale='fa_IR')
    address_2 = random.choice(('', factory.Faker('secondary_address', locale='fa_IR')))
    city = factory.Faker('city', locale='fa_IR')
    state_province = factory.Faker('state_abbr', local='fa_IR')
    zip = factory.Faker('postalcode', locale='fa_IR')
    country = 'Iran'
    phone = factory.Faker('phone_number', locale='fa_IR')


class ImisNameAddressFactoryGermany(ImisNameAddressFactory):
    address_1 = factory.Faker('street_address', locale='de_DE')
    address_2 = random.choice(('', factory.Faker('secondary_address', locale='de_DE')))
    city = factory.Faker('city', locale='de_DE')
    state_province = factory.Faker('state_abbr', locale='de_DE')
    zip = factory.Faker('postalcode', locale='de_DE')
    country = 'Germany'
    phone = factory.Faker('phone_number', locale='de_DE')


class ImisNameAddressFactoryArabicGulf(ImisNameAddressFactory):
    address_1 = factory.Faker('street_address', locale='ar_SA')
    address_2 = random.choice(('', factory.Faker('secondary_address', locale='ar_SA')))
    city = factory.Faker('city', locale='ar_SA')
    state_province = factory.Faker('state_abbr', locale='ar_SA')
    zip = factory.Faker('postalcode', locale='ar_SA')
    country = random.choice(('Saudi Arabia', 'United Arab Emirates'))
    phone = factory.Faker('phone_number', locale='ar_SA')


class ImisNameAddressFactoryItaly(ImisNameAddressFactory):
    address_1 = factory.Faker('street_address', locale='it_IT')
    address_2 = random.choice(('', factory.Faker('secondary_address', locale='it_IT')))
    city = factory.Faker('city', locale='it_IT')
    state_province = factory.Faker('state_abbr', locale='it_IT')
    zip = factory.Faker('postalcode', locale='it_IT')
    country = 'Italy'
    phone = factory.Faker('phone_number', locale='it_IT')


class ImisNameAddressFactoryIndonesia(ImisNameAddressFactory):
    address_1 = factory.Faker('street_address', locale='id_ID')
    address_2 = random.choice(('', factory.Faker('secondary_address', locale='id_ID')))
    city = factory.Faker('city', locale='id_ID')
    state_province = factory.Faker('state_abbr', locale='id_ID')
    zip = factory.Faker('postalcode', locale='id_ID')
    country = 'Indonesia'
    phone = factory.Faker('phone_number', locale='id_ID')


class ImisNameAddressFactoryKorea(ImisNameAddressFactory):
    address_1 = factory.Faker('street_address', locale='ko_KR')
    address_2 = random.choice(('', factory.Faker('secondary_address', locale='ko_KR')))
    city = factory.Faker('city', locale='ko_KR')
    state_province = factory.Faker('state_abbr', locale='ko_KR')
    zip = factory.Faker('postalcode', locale='ko_KR')
    country = 'South Korea'
    phone = factory.Faker('phone_number', locale='ko_KR')


class ImisNameAddressFactoryNetherlands(ImisNameAddressFactory):
    address_1 = factory.Faker('street_address', locale='nl_NL')
    address_2 = random.choice(('', factory.Faker('secondary_address', locale='nl_NL')))
    city = factory.Faker('city', locale='nl_NL')
    state_province = factory.Faker('state_abbr', locale='nl_NL')
    zip = factory.Faker('postalcode', locale='nl_NL')
    country = 'Netherlands'
    phone = factory.Faker('phone_number', locale='nl_NL')


class ImisNameAddressFactoryBlank(factory.Factory):

    purpose = ''
    company = ''
    address_1 = ''
    address_2 = ''
    city = ''
    state_province = ''
    zip = ''
    country = ''
    crrt = ''
    dpb = ''
    bar_code = ''
    country_code = ''
    address_format = 0
    full_address = ''
    county = ''
    us_congress = ''
    state_senate = ''
    state_house = ''
    mail_code = ''
    phone = ''
    fax = ''
    toll_free = ''
    company_sort = ''
    status = ''
    list_string = ''
    preferred_mail = True
    preferred_bill = True
    email = ''
    bad_address = ''
    no_autoverify = False
    address_3 = ''
    preferred_ship = True
    informal = ''
    title = ''

    class Meta:
        model = models.NameAddress
