import random

import factory
from pytz import utc

from myapa.models.profile import IndividualProfile, OrganizationProfile
from myapa.models.constants import SHARE_CHOICES
from myapa.tests.factories.contact import ContactFactoryIndividual, ContactFactoryOrganization

SHARE_CHOICE_CODES = [x[0] for x in SHARE_CHOICES]


class IndividualProfileFactory(factory.DjangoModelFactory):

    contact = factory.SubFactory(ContactFactoryIndividual)
    share_profile = random.choice(SHARE_CHOICE_CODES)
    share_contact = random.choice(SHARE_CHOICE_CODES)
    share_bio = random.choice(SHARE_CHOICE_CODES)
    share_social = random.choice(SHARE_CHOICE_CODES)
    share_leadership = random.choice(SHARE_CHOICE_CODES)
    share_education = random.choice(SHARE_CHOICE_CODES)
    share_jobs = random.choice(SHARE_CHOICE_CODES)
    share_events = random.choice(SHARE_CHOICE_CODES)
    share_resume = random.choice(SHARE_CHOICE_CODES)
    share_conference = random.choice(SHARE_CHOICE_CODES)
    share_advocacy = random.choice(SHARE_CHOICE_CODES)
    speaker_opt_out = random.choice((True, False))

    class Meta:
        model = IndividualProfile


class OrganizationProfileFactory(factory.DjangoModelFactory):

    contact = factory.SubFactory(ContactFactoryOrganization)

    principals = factory.Faker('name')
    number_of_staff = random.randrange(1, 50000)
    number_of_planners = random.randrange(0, 1000)
    number_of_aicp_members = random.randrange(0, 1000)
    date_founded = factory.Faker('date_this_century')
    consultant_listing_until = factory.Faker('future_date', end_date='+365d', tzinfo=utc)
    research_inquiry_hours = random.randrange(0, 500)

    class Meta:
        model = OrganizationProfile
