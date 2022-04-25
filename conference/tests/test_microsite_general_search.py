import json
import os
from unittest import skip

from django.conf import settings

from content.models.master_content import MasterContent
from content.models.tagging import TagType
from content.solr_search import SolrSearch
from events.models import EVENTS_DEFAULT_PARENT_LANDING_MASTER
from events.tests.factories.event import ActivityFactoryNPC, EventMultiFactoryNPC
from pages.models import LandingPage, LandingPageMasterContent
from pages.tests.factories.landing_page import LandingPageFactory, LandingPageFactoryNPC
from planning.global_test_case import GlobalTestCase


class MicrositeGeneralSearchTestCase(GlobalTestCase):

    @classmethod
    def setUpTestData(cls):

        super(MicrositeGeneralSearchTestCase, cls).setUpTestData()

        # for solr searching
        cls.content_types = (
            'PAGE',
            'RFP',
            'KNOWLEDGEBASE_COLLECTION',
            'IMAGE',
            "PUBLICATION",
            "BLOG",
            "JOB"
        )

        cls.event_types = ("EVENT_SINGLE", "EVENT_MULTI", "COURSE", "ACTIVITY")

        with open(os.path.join(
            settings.BASE_DIR, "content/fixtures/tag_type.json"
        )) as tag_type_fixture:
            tag_types = json.load(tag_type_fixture)

        for tag_type in tag_types:
            TagType.objects.update_or_create(**tag_type["fields"])

        with open(os.path.join(
            settings.BASE_DIR, "events/fixtures/npc_landing_pages.json"
        )) as landing_page_fixture:
            landing_pages = json.load(landing_page_fixture)

        for lp in landing_pages:
            LandingPage.objects.update_or_create(**lp)

    def setUp(self):
        # TODO: replace this by subclassing events.tests.NPCTestCase
        self.events_default_parent_landing_master, _ = LandingPageMasterContent.objects.get_or_create(
            id=EVENTS_DEFAULT_PARENT_LANDING_MASTER
        )

        # NPC landing master
        self.npc_lp = LandingPageFactoryNPC(publish_status="PUBLISHED")
        self.npc_lp_master, _ = LandingPageMasterContent.objects.get_or_create(
            content_live=self.npc_lp.content_ptr
        )
        self.npc_lp.master = self.npc_lp_master
        self.npc_lp.save()

        # we have an NPC Landing Page
        # now make a multievent with this as its parent_landing_master
        self.npc_multi_event = EventMultiFactoryNPC(
            parent_landing_master=self.npc_lp_master,
            publish_status="PUBLISHED",
            title="National Planning Conference"
        )

        # (fake) publish the npc multi event
        self.npc_multi_event_master, _ = MasterContent.objects.get_or_create(
            content_live=self.npc_multi_event.content_ptr
        )

    def tearDown(self):
        pass

    def get_filters(self, event_master, landing_page_ids):
        return [
            "(content_type:({}) OR event_type:({}))".format(" ".join(
                self.content_types), " ".join(self.event_types)
            ),
            "-archive_time:[* TO NOW]",
            "(parent:({}) OR id:({}))".format(
                event_master.pk,
                " ".join(landing_page_ids)
            )
        ]

    def test_activity_factory(self):

        # make some activities with the NPC MultiEvent as their parent
        act = ActivityFactoryNPC(
            parent=self.npc_multi_event_master,
            publish_status="PUBLISHED"
        )
        self.assertIn(act, self.npc_multi_event.get_activities())

    @skip
    def test_npc_activities_returned_in_microsite_search_view(self):
        activities = ActivityFactoryNPC.create_batch(
            size=100,
            parent=self.npc_multi_event_master,
            publish_status="PUBLISHED"
        )

        self.assertEqual(self.npc_multi_event.get_activities().count(), len(activities))

        act = activities[0]

        # tag1, _ = Tag.objects.get_or_create(
        #     tag_type=self.tag_type,
        #     title=""
        # )
        published_act = act.publish()
        published_act.solr_publish()

        searcher = SolrSearch(custom_q="id:CONTENT.{}".format(published_act.id))
        results = searcher.get_results()
        self.assertEqual(results['response']['numFound'], 1)
        self.assertEqual(published_act.solr_id, results['response']['docs'][0]['id'])

        published_act.solr_unpublish()

    def test_npc_activities_and_pages_returned_in_microsite_search_view(self):
        activity = ActivityFactoryNPC(
            parent=self.npc_multi_event_master,
            publish_status="PUBLISHED"
        )
        published_act = activity.publish()
        published_act.solr_publish()

        travel_page = LandingPage.objects.get(url="/conference/travel/")
        travel_page.parent_landing_master = self.npc_lp_master
        travel_page.save()
        travel_page_published = travel_page.publish()
        travel_page_published.solr_publish()

        register_page = LandingPage.objects.get(url="/conference/registration/")
        register_page.parent_landing_master = self.npc_lp_master
        register_page.save()
        register_page_published = register_page.publish()
        register_page_published.solr_publish()

        random_page = LandingPageFactory(
            title='land on me I dare you',
            text='<h1>HURR DURR I AM A LANDING PAGE</h1>'
        )
        random_page_published = random_page.publish()
        random_page_published.solr_publish()

        npc_landing_pages = LandingPage.objects.filter(
            parent_landing_master=self.npc_lp_master,
            publish_status="PUBLISHED"
        )
        landing_page_ids = [i.solr_id for i in npc_landing_pages]
        filters = self.get_filters(
            event_master=self.npc_multi_event_master,
            landing_page_ids=landing_page_ids
        )

        searcher = SolrSearch(filters=filters)
        results = searcher.get_results()
        # should only get the 1 activity, 2 landing pages, and NOT the random landing page
        # that does not have the microsite as its parent_landing_master
        self.assertEqual(results['response']['numFound'], 3)

        travel_page_published.solr_unpublish()
        register_page_published.solr_unpublish()
        random_page_published.solr_unpublish()
        published_act.solr_unpublish()
