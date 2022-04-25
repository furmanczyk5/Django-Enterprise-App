from django.utils import timezone

from content.models.master_content import MasterContent
from events.tests.factories.event import EventMultiFactoryNPC
from pages.models import LandingPageMasterContent
from pages.tests.factories.landing_page import LandingPageFactoryNPC
from planning.global_test_case import GlobalTestCase
from store.models.product import Product

THIS_YEAR = timezone.now().year


class NPCTestCase(GlobalTestCase):
    """
    Subclass of :class:`planning.global_test_case.GlobalTestCase` that
    boilerplates the landing page / master content / product
    Rube Goldberg machine
    """

    @classmethod
    def setUpTestData(cls):
        super(NPCTestCase, cls).setUpTestData()

        cls.npc_lp = LandingPageFactoryNPC(publish_status="PUBLISHED")
        cls.npc_lp_master, _ = LandingPageMasterContent.objects.get_or_create(
            content_live=cls.npc_lp.content_ptr
        )
        cls.npc_lp.master = cls.npc_lp_master
        cls.npc_lp.save()

        # we have an NPC Landing Page
        # now make a multievent with this as its parent_landing_master
        cls.npc_multi_event = EventMultiFactoryNPC(
            parent_landing_master=cls.npc_lp_master,
            publish_status="PUBLISHED",
            title="National Planning Conference",
        )

        # (fake) publish the npc multi event
        cls.npc_multi_event_master, _ = MasterContent.objects.get_or_create(
            content_live=cls.npc_multi_event.content_ptr
        )

        # buy this thing
        cls.npc_product = Product.objects.create(
            code="{}CONF".format(str(THIS_YEAR)[-2:]),
            product_type="EVENT_REGISTRATION",
            publish_status="PUBLISHED",
            content=cls.npc_multi_event
        )

