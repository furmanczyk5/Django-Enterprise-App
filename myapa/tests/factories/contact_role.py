import random

import factory

from content.tests.factories.content import ContentFactory
from myapa.models.constants import ROLE_TYPES
from myapa.models.contact_role import ContactRole


class ContactRoleFactory(factory.DjangoModelFactory):

    content = factory.SubFactory(ContentFactory)
    role_type = random.choice([x[0] for x in ROLE_TYPES])

    first_name = factory.Faker('first_name')
    middle_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')
    phone = random.randrange(1000000000, 9999999999)
    company = factory.Faker('company')
    cell_phone = random.randrange(1000000000, 9999999999)


    class Meta:
        model = ContactRole
