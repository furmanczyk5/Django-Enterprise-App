import random

import factory
from django.utils import timezone
from pytz import utc

from imis import models
from myapa.models import constants


# TODO are we missing "B"? See note above myapa.models.constants.SALARY_CHOICES
SALARY_RANGES = [x[0] for x in constants.SALARY_CHOICES_ALL]
SALARY_RANGES.append('')


FACULTY_POSITIONS = ('', 'F01', 'F02', 'F03', 'F04', 'F05', 'F06', 'F07', 'F08', 'F09',
                     'F10', 'F11',)

ADMIN_POSITIONS = ('', 'A01', 'A02', 'A03', 'A06', 'A07', 'A08', 'A10', 'A11', 'A12',
                   'A13', 'A14',)

TOP_20_PROMOTION_CODES = ('', 'WEB_ANONYMOUS', 'MPI', 'M0IY', 'M1XY', 'MREN', 'LATE',
                          'CONF', 'M2IY', 'M9IY', 'M9IZ', 'AICP', 'LTR', 'MCONF',
                          'CHAP', 'M0VZ', 'M7IZ', 'TELE', 'M8IZ', 'M9VA')


TOP_20_SPECIALTIES = ('', 'S006', 'S003', 'S999', 'S005', 'S013', 'S010', 'S004',
                      'A', 'D', 'B', 'F', 'Z', 'Y', 'S008', 'W', 'S003,S010,S013',
                      'S003,S004,S008', 'S007', 'G')


TOP_20_SUB_SPECIALTIES = ('', '2', '42', '4', '45', '67', '8901', '37', '15', '44',
                          '49', '21', '16', '52', '10', '6400', '46', '65', '68', '35')

COUNTRY_CODES = list(set([x[0] for x in constants.COUNTRY_CATEGORY_CODES]))
COUNTRY_CODES.append('')

CONF_CODES = ('', 'A', 'H', 'D', 'C', 'F', 'B', 'G', 'E', 'CC')

# TODO: Reconcile the "and" and "&" departments
TOP_20_DEPARTMENTS = ('', 'Planning', 'Planning Department', 'Community Development',
                      'Planning Commission', 'Human Resources', 'Planning and Development',
                      'Planning and Zoning', 'Community Development Department',
                      'Development Services', 'Planning Division', 'Transportation',
                      'Administration', 'Urban Planning', 'Planning & Zoning',
                      'Planning & Development', 'Planning and Community Development',
                      'Public Works', 'Urban and Regional Planning', 'Planning Board')


JOIN_TYPES = ('', 'RENEW', 'NEW', 'REJOIN', 'NM', 'STU', 'GPBM', 'NEW MEM', 'FSTU')


class ImisIndDemographicsFactory(factory.Factory):

    apa_life_date = factory.Faker('date_time_this_decade', tzinfo=utc)
    aicp_life_member = random.choice((True, False))
    aicp_life_date = factory.Faker('date_time_this_decade', tzinfo=utc)
    faculty_position = random.choice(FACULTY_POSITIONS)
    admin_position = random.choice(ADMIN_POSITIONS)
    salary_range = random.choice(SALARY_RANGES)
    promotion_codes = random.choice(TOP_20_PROMOTION_CODES)
    date_of_birth = factory.Faker('date_time_this_century', tzinfo=utc)
    sub_specialty = random.choice(TOP_20_SUB_SPECIALTIES)
    usa_citizen = random.choice((True, False))
    aicp_start = factory.Faker('date_time_this_decade', tzinfo=utc)
    aicp_cert_no = random.choice(('', str(random.randrange(1, 10000)).zfill(6)))
    perpetuity = random.choice((True, False))
    aicp_promo_1 = ''

    # TODO: iMIS stores these in plain text!? Not actual passwords, but yikes...
    hint_password = ''

    # XXX ACHTUNG DANGER PELIGRO!
    # WARNING: DO NOT CHANGE THIS UNLESS YOU ARE SURE YOU KNOW WHAT YOU'RE DOING!
    # tearDownClass classmethods of unit tests use this as value to test for deletion
    hint_answer = 'DJANGO_TEST_FACTORY'

    country_codes = random.choice(COUNTRY_CODES)
    specialty = random.choice(TOP_20_SPECIALTIES)
    apa_life_member = random.choice((True, False))
    conf_code = random.choice(CONF_CODES)
    mentor_signup = random.choice((True, False))
    department = random.choice(TOP_20_DEPARTMENTS)
    conv_np = random.choice((True, False))
    invoice_num = ''
    prev_mt = random.choice(('', 'FSTU'))
    conv_freestu = random.choice((True, False))
    conv_stu = random.choice((True, False))
    chapt_only = random.choice((True, False))
    asla = random.choice((True, False))
    salary_verifydate = factory.Faker('date_time_this_decade', tzinfo=utc)
    functional_title_verifydate = factory.Faker('date_time_this_decade', tzinfo=utc)
    previous_aicp_cert_no = random.choice(('', str(random.randrange(1, 10000)).zfill(6)))
    previous_aicp_start = factory.Faker('date_time_this_decade', tzinfo=utc)
    email_secondary = factory.Faker('email')
    new_member_start_date = factory.Faker('date_time_this_decade', tzinfo=utc)
    conv_ecp5 = random.choice((True, False))
    exclude_from_drop = random.choice((True, False))
    student_start_date = factory.Faker('date_time_this_decade', tzinfo=utc)
    is_current_student = random.choice((True, False))
    join_type = random.choice(JOIN_TYPES)
    join_source = random.choice(('', 'SCHOOL_ADMIN'))
    gender = random.choice(constants.GENDER_CHOICES)
    gender_other = ''

    class Meta:
        model = models.IndDemographics


class ImisIndDemographicsFactoryBlank(factory.Factory):

    aicp_life_member = False
    faculty_position = ''
    admin_position = ''
    salary_range = ''
    promotion_codes = ''
    sub_specialty = ''
    usa_citizen = False
    aicp_cert_no = ''
    perpetuity = False
    aicp_promo_1 = ''
    hint_password = ''
    hint_answer = ''
    country_codes = ''
    specialty = ''
    apa_life_member = False
    conf_code = ''
    mentor_signup = False
    department = ''
    conv_np = False
    invoice_num = ''
    prev_mt = ''
    conv_freestu = False
    conv_stu = False
    chapt_only = False
    asla = False
    previous_aicp_cert_no = ''
    email_secondary = ''
    conv_ecp5 = False
    exclude_from_drop = False
    is_current_student = False
    gender=''
    gender_other = ''

    class Meta:
        model = models.IndDemographics
