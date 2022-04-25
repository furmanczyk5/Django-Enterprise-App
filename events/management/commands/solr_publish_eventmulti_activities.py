from django.core.management.base import BaseCommand
from django.utils import timezone

from content.solr_search import SolrSearch
from events.models import EventMulti, NATIONAL_CONFERENCES


class Command(BaseCommand):
    help = """Mass solr publish EventMulti activities"""

    def add_arguments(self, parser):
        # parser.add_argument('', nargs='+', type=int)
        pass

    def get_event_multis(self, **query_kwargs):
        """
        Get non-archived, non-NPC EventMultis
        :return: :class:`django.db.models.query.QuerySet`
        """
        ems = EventMulti.objects.filter(
            archive_time__gt=timezone.now(),
            publish_status="PUBLISHED",
            status='A',
            **query_kwargs
        ).exclude(
            code__in=[x[0] for x in NATIONAL_CONFERENCES]
        )
        return ems

    def already_published(self, master_id):
        """
        Is this activity already published in Solr?
        :param master_id: the master id of the activity
        :type master_id: int
        :return: bool
        """
        q = SolrSearch(custom_q='id:CONTENT.{}'.format(master_id))
        res = q.get_results()
        return res.get('response', {}).get('numFound', 0) > 0

    def handle(self, *args, **options):
        eventmultis = self.get_event_multis()
        self.stdout.write(
            self.style.NOTICE(
                "Preparing to mass Solr publish activities for {} multi-part events".format(eventmultis.count())
            )
        )
        for event in eventmultis:
            activities = event.get_activities()
            activities = [x for x in activities if not self.already_published(x.master_id)]
            self.stdout.write(
                self.style.NOTICE(
                    "Solr publishing {} Activities for {} | {}".format(len(activities), event.master_id, event.title)
                )
            )
            for activity in activities:
                activity.solr_publish()
