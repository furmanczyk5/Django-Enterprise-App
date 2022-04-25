from datetime import datetime

import pytz
from django.conf import settings
from django.core.management.base import BaseCommand

from content.models import Content
from events.models import Course, EventMulti
from learn.models import LearnCourse

TZ = pytz.timezone("America/Chicago")
END_TIME = TZ.localize(datetime(2018, 11, 14))
NPC17_EVENT_MULTI_MASTER_ID = 9102340
COURSE_PRODUCT_PAGE = "https://{}/local/catalog/view/product.php?globalid=".format(
    settings.LEARN_DOMAIN
)


class Command(BaseCommand):
    help = """Deactivate COURSE event types and their associated ProductPrices"""

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.NOTICE(
                "Deactivating On-Demand courses and associated Products and ProductPrices"
            )
        )
        for course in Course.objects.filter(product__product_type="STREAMING"):
            if course.product.status in ('A', 'H'):
                course.product.status = 'I'
                course.product.save()
            course.product.options.update(status='I')
            course.product.prices.update(status='I', end_time=END_TIME)
            course.solr_publish()
            self.stdout.write(
                self.style.SUCCESS(
                    "Deactivated {}: {}".format(course.master_id, course.title)
                )
            )

        Content.objects.filter(url="/ondemand/", publish_status="PUBLISHED").update(status="I")

        self.stdout.write(
            self.style.SUCCESS(
                "Deactivated content associated with /ondemand/ url"
            )
        )

        self.stdout.write(
            self.style.NOTICE(
                "Deactivating NPC17 Activities with a corresponding APA Learn Course"
            )
        )

        npc17 = EventMulti.objects.get(publish_status="PUBLISHED", master_id=NPC17_EVENT_MULTI_MASTER_ID)
        for npc17act in npc17.get_activities():
            if hasattr(npc17act, "product"):
                lc = LearnCourse.objects.filter(
                    publish_status="PUBLISHED",
                    code="LRN_{}".format(npc17act.product.code)
                ).first()
                if lc is not None:
                    self.stdout.write(
                        self.style.NOTICE(
                            "Deactivating NPC17 Activity {}: {}".format(
                                npc17act.master_id,
                                npc17act.title
                            )
                        )
                    )
                    npc17act.product.status = "I"
                    npc17act.product.save()
                    npc17act.product.options.update(status="I")
                    npc17act.product.prices.update(status="I", end_time=END_TIME)
