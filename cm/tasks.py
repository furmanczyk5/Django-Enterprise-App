import datetime
import logging
import pickle
import pytz

from celery import shared_task
from celery.decorators import periodic_task
from celery.task.schedules import crontab
from sentry_sdk import capture_message

from cm.models import Provider
from cm.credly_api_utils import CredlyAPICaller

logger = logging.getLogger(__name__)


@shared_task(name="start_periodic_reviews", bind=True)
def start_periodic_reviews(self, pickled_query=None):
    providers = Provider.objects.none()
    providers.query = pickle.loads(pickled_query.encode())

    for provider in providers:
        provider.start_periodic_review(with_email=True)

# @periodic_task(run_every=(crontab(hour=2, minute=50)))
# def credly_nightly_sync_task():
#     central = pytz.timezone("US/Central")
#     central_start = central.localize(datetime.datetime.now())
#     capture_message("Started Credly Sync at: %s" % central_start)
#     credly_api_caller = CredlyAPICaller()
#     # COMMENTING OUT BECAUSE THIS IS IN CRON NOW. KEEPING THE TASK HERE FOR CELERY TESTING.
#     # credly_api_caller.credly_nightly_sync()
#     central_end = central.localize(datetime.datetime.now())
#     capture_message("Finished Credly Sync at: %s" % central_end)
