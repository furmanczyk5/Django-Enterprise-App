import random

import factory

from imis.tests.factories.name import TOP_20_COMPANIES, TOP_20_TITLES
from myapa.models.job_history import JobHistory
from myapa.tests.factories.contact import ContactFactoryIndividual


class JobHistoryFactory(factory.DjangoModelFactory):

    contact = factory.SubFactory(ContactFactoryIndividual)
    title = random.choice(TOP_20_TITLES)
    company = random.choice(TOP_20_COMPANIES)
    city = factory.Faker('city')
    state = factory.Faker('state')
    zip_code = random.choice(
        (
            factory.Faker('postalcode'),
            factory.Faker('postalcode_plus4')
        )
    )
    country = factory.Faker('country')
    start_date = factory.Faker('date_between', start_date='-30y', end_date='-1m')
    end_date = factory.Faker('date_between', start_date='-20y', end_date='-2m')
    is_current = random.choice((True, False))
    is_part_time = random.choice((True, False))
    phone = factory.Faker('phone_number')

    class Meta:
        model = JobHistory
