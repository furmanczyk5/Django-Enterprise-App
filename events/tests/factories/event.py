import json
import os
from datetime import datetime, timedelta

import factory
import pytz
from django.conf import settings
from factory import fuzzy

from events.models import Activity, Event, EventMulti
from myapa.tests.factories.contact import AdminUserFactory

NPC19_START = datetime(2019, 4, 13, 8, tzinfo=pytz.timezone("US/Pacific"))
NPC19_END = datetime(2019, 4, 16, 23, tzinfo=pytz.timezone("US/Pacific"))
NPC19_PROD_MASTER_ID = 9162593
YEAR = 2019
MONTH = 4


with open(os.path.join(
        settings.BASE_DIR, "events/fixtures/npc_activities_titles_descriptions.json"
)) as npc_activities_fixutre:
    NPC_ACTIVITIES = json.load(npc_activities_fixutre)


class EventFactory(factory.DjangoModelFactory):

    class Meta:
        model = Event


class EventMultiFactory(factory.DjangoModelFactory):

    class Meta:
        model = EventMulti


class EventMultiFactoryNPC(EventMultiFactory):

    begin_time = NPC19_START
    end_time = NPC19_END
    timezone = "US/Pacific"
    city = "San Francisco"
    code = "EVENT_19CONF"
    country = "United States"
    created_by = factory.SubFactory(AdminUserFactory)
    keywords = "NPC"
    mail_badge = True
    description = "Join APA in {} for the {} National Planning Conference".format(city, begin_time.year)
    title = "{} National Planning Conference".format(begin_time.year)
    og_description = description
    og_title = title
    og_type = 'article'
    state = 'CA'
    template = "events/newtheme/eventmulti-details.html"
    ticket_template = "registrations/tickets/layout/CONFERENCE-BADGE.html"
    updated_by = factory.SubFactory(AdminUserFactory)

    class Meta:
        model = EventMulti
        django_get_or_create = ("title", )


class ActivityFactory(factory.DjangoModelFactory):

    class Meta:
        model = Activity


class ActivityFactoryNPC(ActivityFactory):

    begin_time = fuzzy.FuzzyDateTime(
        start_dt=NPC19_START,
        end_dt=NPC19_END - timedelta(hours=1)
    )
    end_time = factory.LazyAttribute(lambda o: o.begin_time + timedelta(hours=o.duration))
    timezone = "US/Pacific"

    title = fuzzy.FuzzyChoice([i["title"] for i in NPC_ACTIVITIES])
    # see events.models.EVENT_TICKET_TEMPLATES; ticketed activity would use
    # registrations/tickets/layouts/CONFERENCE-ACTIVITY.html
    ticket_template = None

    class Params:
        duration = 1
