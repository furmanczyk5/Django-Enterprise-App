import pytz
import datetime

from celery.decorators import periodic_task
from celery.task.schedules import crontab

from django.conf import settings
from sentry_sdk import capture_message

from component_sites.models import NewsPage
from _data_tools.solr_reindex import reindex_wagtail


@periodic_task(run_every=(crontab(hour=3, minute=5)))
def nightly_solr_wt_events_reindex():
    central = pytz.timezone("US/Central")
    central_start = central.localize(datetime.datetime.now())

    capture_message("Started solr wagtail events reindex at: %s" % central_start, level='info')

    env = 'staging' if settings.ENVIRONMENT_NAME != 'PROD' else 'PROD'

    reindex_wagtail(
        Class=NewsPage,
        environment=env,
        delete_kwargs={"query": "record_type:WAGTAIL_PAGE AND content_type:newspage"},
    )

    central_end = central.localize(datetime.datetime.now())
    capture_message("Finished solr wagtail events reindex at: %s" % central_end, level='info')
