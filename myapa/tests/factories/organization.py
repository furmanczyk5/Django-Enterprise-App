import random

import factory

from myapa.models.constants import ORGANIZATION_TYPES, DjangoContactTypes
from myapa.models.proxies import Organization
from ui.utils import NORTH_AMERICAN_GEONAME_CODES


class OrganizationFactory(factory.DjangoModelFactory):

    contact_type = DjangoContactTypes.ORGANIZATION.value
    company = factory.Faker('company')
    organization_type = random.choice(
        [x[0] for x in ORGANIZATION_TYPES if x[0] != "CONSULTANT"]
    )  # TODO: Fix when we revisit consultants
    address1 = factory.Faker('street_address')
    address2 = random.choice((factory.Faker('secondary_address'), ''))
    # country = factory.Faker('country')
    country = "United States"
    city = factory.Faker('city')
    # state = random.choice([x for x in NORTH_AMERICAN_GEONAME_CODES.values()])
    state = "IL"
    zip_code = random.choice((factory.Faker('postalcode'), factory.Faker('postalcode_plus4')))
    phone = str(random.randrange(1111111111, 9999999999))
    bio = factory.Faker('paragraphs', nb=5)
    ein_number = str(random.randrange(111111111, 999999999))
    personal_url = random.choice((factory.Faker('uri'), ''))

    class Meta:
        model = Organization

    @factory.post_generation
    def post(obj, create, extracted, **kwargs):
        obj.bio = '\n'.join(obj.bio)
