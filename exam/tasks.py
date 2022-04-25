import pytz
import datetime

from celery.decorators import periodic_task
from celery.task.schedules import crontab

from django.conf import settings

from exam.open_water_api_utils import OpenWaterAPICaller

from sentry_sdk import capture_message

# COMPLETELY REMOVING THIS UNTIL CELERY IS CONFIGURED ON A SINGLE SERVER
# @periodic_task(run_every=(datetime.timedelta(minutes=15)))
# @periodic_task(enabled=False, run_every=(crontab(hour=23, minute=59)))
# def pull_open_water_invoices_task():
#     central = pytz.timezone("US/Central")
#     central_start = central.localize(datetime.datetime.now())
#     if central_start.hour in range(0,23) and central_start.minute in range(0,59):
#         capture_message("Started Open Water Invoice Pull at: %s" % central_start)
#     if settings.ENVIRONMENT_NAME != "PROD":
#         open_water_test = OpenWaterAPICaller(instance="test_instance")
#         open_water_test.pull_open_water_invoices(window_in_hours=.5)
#     else:
#         # COMMENT THIS BACK IN FOR AWARDS LAUNCH:
#         # open_water_awards = OpenWaterAPICaller(instance="awards_instance")
#         # open_water_awards.pull_open_water_invoices(window_in_hours=.5)
#         # COMMENTING THIS OUT BECAUSE IT'S COPIED 3 TIMES -- but leaving this task in the queue for testing
#         # open_water_aicp = OpenWaterAPICaller(instance="aicp_instance")
#         # open_water_aicp.pull_open_water_invoices(window_in_hours=.5)
#     central_end = central.localize(datetime.datetime.now())
#     # we still want central_start in this logic so we are sure to see the end
#     if central_start.hour in range(0,23) and central_start.minute in range(0,59):
#         capture_message("Finished Open Water Invoice Pull at: %s" % central_end)

# COMPLETELY REMOVING THIS UNTIL CELERY IS CONFIGURED ON A SINGLE SERVER
# @periodic_task(run_every=(crontab(hour=3, minute=20)))
# def sync_open_water_to_myapa_task():
#     central = pytz.timezone("US/Central")
#     central_start = central.localize(datetime.datetime.now())
#     capture_message("Started Open Water MyAPA Sync at: %s" % central_start)

#     if settings.ENVIRONMENT_NAME != "PROD":
#         open_water_test = OpenWaterAPICaller(instance="test_instance")
#         open_water_test.sync_open_water_to_myapa()
#     else:
#         # COMMENT THIS BACK IN FOR AWARDS LAUNCH:
#         # open_water_awards = OpenWaterAPICaller(instance="awards_instance")
#         # open_water_awards.sync_open_water_to_myapa()
#         open_water_aicp = OpenWaterAPICaller(instance="aicp_instance")
#         open_water_aicp.sync_open_water_to_myapa()

#     central_end = central.localize(datetime.datetime.now())
#     capture_message("Finished Open Water MyAPA Sync at: %s" % central_end)

