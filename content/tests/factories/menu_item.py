import factory
from pytz import utc

from content.models import MenuItem


class MenuItemFactory(factory.DjangoModelFactory):

    publish_status = "PUBLISHED"
    status = 'A'
    created_time = factory.Faker('date_time_this_decade', tzinfo=utc)
    updated_time = factory.Faker('date_time_this_decade', tzinfo=utc)

    class Meta:
        model = MenuItem
