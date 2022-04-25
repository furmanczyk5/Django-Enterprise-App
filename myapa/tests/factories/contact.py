import random

import factory
from django.contrib.auth.models import User
from pytz import utc

from imis.tests.factories.name import TOP_20_TITLES, TOP_20_COMPANIES
from myapa.models.constants import SALARY_CHOICES_ALL
from myapa.models.contact import Contact
from myapa.models.proxies import School


SALARY_CHOICES = [i[0] for i in SALARY_CHOICES_ALL]
TITLE_CHOICES = TOP_20_TITLES + (None,)
COMPANY_CHOICES = [i for i in TOP_20_COMPANIES if i != 'American Planning Association']
COMPANY_CHOICES.append(None)
TOP_20_SCHOOLS = (
    'University of Pennsylvania', 'Arizona State University', 'University of California, Los Angeles',
    'California State Polytechnic University - Pomona', 'Massachusetts Institute of Technology',
    'University of Michigan', 'University of Cincinnati', 'University of Illinois at Chicago',
    'Ohio State University', 'University of Southern California', 'Florida State University',
    'Rutgers, The State University of New Jersey', 'Georgia Institute of Technology',
    'Cornell University', 'University of California, Berkeley', 'University of Colorado Denver',
    'University of Virginia', 'Portland State University', 'Iowa State University'
)


class UserFactory(factory.DjangoModelFactory):
    """A Factory for creating users in Django"""
    username = factory.Sequence(lambda n: n + 10000000)
    password = 'unittest'

    class Meta:
        model = User

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Overriding DjangoModelFactory._create to use the Django contrib auth User
        model manager create_user method so that we can do things like
        pass in a plain-text password and have it hashed on save (which
        will then let us authenticate this user in subsequent tests)"""
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)


class AdminUserFactory(factory.DjangoModelFactory):
    """A Factory for creating admin users in Django. This class uses the
    django_get_or_create pattern in its Meta class, so that it is only
    created once."""
    id = 9999999
    username = 'administrator'
    email = 'it@planning.org'
    password = 'planzizzle'
    is_staff = True
    is_superuser = True

    class Meta:
        model = User
        django_get_or_create = ('username',)


class ContactFactory(factory.DjangoModelFactory):
    """A factory_boy Factory for :class:`myapa.models.Contact`"""

    user = factory.SubFactory(UserFactory)

    class Meta:
        model = Contact


class ContactFactoryAdmin(factory.DjangoModelFactory):
    """A factory_boy Factory for an APA staff/admin Contact"""

    user = factory.SubFactory(AdminUserFactory)

    class Meta:
        model = Contact


class ContactFactoryIndividual(ContactFactory):
    """A Factory for INDIVIDUAL Contacts"""

    contact_type = "INDIVIDUAL"

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    job_title = random.choice(TITLE_CHOICES)
    salary_range = random.choice(SALARY_CHOICES)
    email = factory.Faker('email')
    # this occasionally generates phone numbers > 20 characters
    # phone = factory.Faker('phone_number')
    phone = random.randrange(1000000000, 9999999999)
    birth_date = factory.Faker('date_of_birth', tzinfo=utc, minimum_age=18)
    company = random.choice(COMPANY_CHOICES)
    bio = random.choice((None, factory.Faker('text', max_nb_chars=5000)))


class ContactFactoryOrganization(ContactFactory):
    """A Factory for ORGANIZATION"""

    contact_type = "ORGANIZATION"

    company = random.choice(COMPANY_CHOICES)


class SchoolFactory(ContactFactoryOrganization):

    company = random.choice(TOP_20_SCHOOLS)

    class Meta:
        model = School
