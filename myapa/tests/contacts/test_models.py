import datetime

import pytz

from content.models import TagType, Tag, ContentTagType
from content.solr_search import SolrSearch
from events.models import Event
from myapa.models.contact import Contact
from myapa.models.contact_role import ContactRole
from myapa.tests.factories.contact import ContactFactoryIndividual
from pages.models import LandingPage
from planning.global_test_case import GlobalTestCase


class ContactModelsTestCase(GlobalTestCase):

    @classmethod
    def setUpTestData(cls):
        """
        :meth:`events.models.Event.save` sets a default parent landing page
        which will cause errors here if it doesn't exist (i.e. in a fresh test database)
        """

        super().setUpTestData()

        cls.event_landing_page, event_landing_page_exists = LandingPage.objects.get_or_create(
            title='Test Page for Conferences & Meetings'
        )
        if not event_landing_page_exists:
            cls.event_landing_page.publish()
        cls.parent_landing_master_id = cls.event_landing_page.master_id

    @classmethod
    def tearDownClass(cls):
        cls.event_landing_page.solr_unpublish()
        super(ContactModelsTestCase, cls).tearDownClass()

    def test_solr_publish(self):
        """ Tests solr publishing and unpublishing for contacts/speakers """

        contact = ContactFactoryIndividual(bio="This is a test bio.")

        tagtype = TagType.objects.create(title="Tag Type 1")

        tags = [
            Tag.objects.create(title="Tag 1", tag_type=tagtype),
            Tag.objects.create(title="Tag 2", tag_type=tagtype),
            Tag.objects.create(title="Tag 3", tag_type=tagtype)
        ]

        # create event
        event = Event.objects.create(
            title="Test Single Event",
            event_type="EVENT_SINGLE",
            begin_time=pytz.utc.localize(datetime.datetime(year=2017, month=1, day=1, hour=12)),
            end_time=pytz.utc.localize(datetime.datetime(year=2017, month=1, day=1, hour=13)),
            timezone="UTC",
            status="A",
            publish_status="PUBLISHED",
            parent_landing_master_id=self.parent_landing_master_id
        )

        ctt = ContentTagType.objects.create(
            content=event,
            tag_type=tagtype,
            publish_status="PUBLISHED"
        )

        ctt.tags.add(*tags)

        ContactRole.objects.create(
            role_type="SPEAKER",
            contact=contact,
            content=event,
            publish_status="PUBLISHED"
        )

        # requery (to capture relationships) and publish contact to solr
        speaker = Contact.objects.prefetch_related(
            "contactrole__content__event__contenttagtype__tags"
        ).get(id=contact.id)

        speaker.solr_publish()

        solr_results1 = SolrSearch(custom_q="id:{0}".format(speaker.solr_id)).get_results()

        # should be the first and only result
        self.assertEqual(solr_results1["response"]["numFound"], 1)
        testaccount_result1 = solr_results1["response"]["docs"][0]

        self.assertEqual(testaccount_result1["first_name"], speaker.first_name)
        self.assertEqual(testaccount_result1["last_name"], speaker.last_name)
        self.assertEqual(testaccount_result1["bio"], speaker.bio)
        self.assertEqual(
            testaccount_result1.get("speaker_events")[0],  # should be the first and only event
            "{0}|{1}|{2}|{3}|{4}".format(
                event.master_id, event.event_type, event.title, event.begin_time,
                event.parent_id or ""
            )
        )

        solr_tags = testaccount_result1.get("tags")
        for t in tags:
            self.assertTrue(t.title in solr_tags)

        # remove contact from solr
        speaker.solr_unpublish()

        solr_results2 = SolrSearch(custom_q="id:{0}".format(speaker.solr_id)).get_results()

        # check if speaker was removed from solr
        self.assertEqual(solr_results2["response"]["numFound"], 0)

