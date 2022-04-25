import random

import factory
import pytz

from content.models.tagging import ContentTagType, Tag, TagType
from myapa.tests.factories.contact import AdminUserFactory


# TagType codes and titles for NPC Activities
CODES_TITLES = {
    "POSTER": "Posters",
    "ORIENTATION_TOUR": "Orientation Tours",
    "SPECIAL_PROGRAMMING": "Special Programming",
    "FAST_FUNNY": "Fast, Funny, and Passionate",
    "RECEPTIONS": "Receptions",
    "EXHIBIT_HALL": "Exhibit Hall Presentations",
    "SESSION": "Educational Sessions",
    "DEEP_DIVE": "Deep Dive Sessions",
    "MOBILE_WORKSHOP": "Mobile Workshops",
    "MEETING": "Meetings",
    "CAREER_ZONE": "Career Zone",
    "SPECIAL_EVENT": "Ticketed Events"
}


class TagTypeFactory(factory.DjangoModelFactory):

    created_by = factory.SubFactory(AdminUserFactory)
    updated_by = factory.SubFactory(AdminUserFactory)
    created_time = factory.Faker('date_time_this_decade', tzinfo=pytz.utc)
    updated_time = factory.Faker('date_time_this_decade', tzinfo=pytz.utc)

    class Meta:
        model = TagType


class TagFactory(factory.DjangoModelFactory):

    created_by = factory.SubFactory(AdminUserFactory)
    updated_by = factory.SubFactory(AdminUserFactory)
    created_time = factory.Faker('date_time_this_decade', tzinfo=pytz.utc)
    updated_time = factory.Faker('date_time_this_decade', tzinfo=pytz.utc)

    class Meta:
        model = Tag


class ContentTagTypeFactory(factory.DjangoModelFactory):

    class Meta:
        model = ContentTagType


class TagFactoryNPCActivity(TagFactory):
    """Factory for Tags for NPC Activities"""

    tag_type = TagType.objects.filter(code="EVENTS_NATIONAL_TYPE").first()
    code = random.choice(list(CODES_TITLES.keys()))
    title = CODES_TITLES[code]
