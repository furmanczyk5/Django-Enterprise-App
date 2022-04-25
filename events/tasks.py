import pytz
import datetime

from celery import shared_task
from celery.schedules import crontab
from celery.task import periodic_task
from sentry_sdk import capture_message

from events import models as event_models


@shared_task(name="provider_event_submit_task")
def provider_event_submit_task(event_id=None, EventClass=None):
    event = EventClass.objects.get(id=event_id)
    event.provider_submit()


@periodic_task(run_every=(crontab(hour=3, minute=0)))
def nightly_solr_speaker_reindex():
    central = pytz.timezone("US/Central")

    central_start = central.localize(datetime.datetime.now())
    capture_message("Started solr speaker reindex at: %s" % central_start)

    event_models.Speaker.solr_reindex_all()

    central_end = central.localize(datetime.datetime.now())
    capture_message("Finished solr speaker reindex at: %s" % central_end)
