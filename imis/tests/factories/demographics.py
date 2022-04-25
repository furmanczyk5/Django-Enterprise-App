import random

import factory

from imis.models import MailingDemographics, OrgDemographics
from myapa.models.constants import PAS_TYPES, ORGANIZATION_TYPES


class MailingDemographicsFactoryBlank(factory.Factory):

    job_mart_bulk = False
    job_mart_address = ''
    excl_mail_list = False
    excl_website = False
    excl_interact = False
    excl_survey = False
    excl_all = False
    excl_natlconf = False
    excl_otherconf = False
    excl_planning = False
    excl_japa = False
    excl_zp = False
    excl_pac = False
    excl_pan = False
    excl_pas = False
    excl_commissioner = False
    excl_foundation = False
    excl_learn = False
    excl_planning_home = False
    excl_planning_print = False
    speaker_address = ''
    leadership_address = ''
    roster_address = ''
    job_mart_invoice = ''

    class Meta:
        model = MailingDemographics


class OrgDemographicsFactoryBlank(factory.Factory):

    pas_code = ''
    org_type = ''
    population = ''
    annual_budget = ''
    staff_size = ''
    parent_id = ''
    top_city = False
    top_county = False
    planning_function = False
    school_program_type = ''

    class Meta:
        model = OrgDemographics


class OrgDemographicsFactory(factory.Factory):

    id = factory.Sequence(lambda n: str(n + 10000000))
    pas_code = random.choice([x[0] for x in PAS_TYPES])
    org_type = random.choice([x[0] for x in ORGANIZATION_TYPES])
    population = random.randrange(1, 10000000)
    annual_budget = random.randrange(1, 10000000)
    staff_size = random.randrange(1, 100000)
    parent_id = 'DJANGO_TE'
    planning_function = random.choice((True, False))
    school_program_type = ''

    class Meta:
        model = OrgDemographics

