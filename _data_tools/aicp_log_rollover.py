# import django
# django.setup()
# import json, urllib
# import requests
# import pytz
# import datetime
# import logging
# import math
# import string
# import random

from exam.models import *
from cm.models import Log
from cm.models import settings as cm_settings
from datetime import date

# YET ANOTHER RANDOM COMMENT
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import is_password_usable
from django.core.mail import send_mail

from datetime import timedelta

from django.db.models import Q

from cm.models import settings
from content.models import *
from myapa.models import ContactRole
from store.models import *
from events.models import *
from media.models import *

from planning.settings import ENVIRONMENT_NAME, RESTIFY_SERVER_ADDRESS
from urllib.request import urlopen
from urllib import parse
from decimal import *
from xml.dom import minidom

from uploads.models import *

from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from io import BytesIO

from imis.models import Name

"""
The scripts in this file were created to accomodate jira ticket 5712
"""

def exempt_rollover(period_code='JAN2019'):
    """

    NOTE: THERE NEEDS TO BE AN ETHICS AND LAW CREDIT CHECK ADDED TO THE ROLLOVER METHOD IN LOG! DOING THESE CHECKS MANUALLY FOR NOW!

    Rollover into the given passed reporting period with exception status and credit requirements met.
    Retired (E_01) will be given a 0 CM requirement.
    Voluntary Life (E_13) will be given a 16 CM credit requirement.
    Outside US (E_03) will be given a 32 CM requirement and will no longer have the exemption.
    Active (A) will give given a 32 CM requirement.
    """

    logs = Log.objects.filter(period__code=period_code, status__in=("E_01","E_13","E_03","A"), is_current=True)

    for log in logs:
        try:
            # per William - check DESIGNATION for creating new logs. This is change from changing the PAID_THRU date
            designation = Name.objects.get(id=log.user.username).designation

            credits_overview = log.credits_overview()
            credits_needed = credits.overview.get("general_needed")
            law_credits_needed = credits_overview.get("law_needed")
            ethics_credits_needed = credits_overview.get("ethics_needed")

            credits_required = 32
            law_credits_required = 1.5
            ethics_credits_required = 1.5

            # all log status should transfer over for all users who rollover / go into grace period EXCEP for E_03.
            # E_03 gets regular AICP status.
            new_log_status = log.status if log.status != "E_03" else "A"

            if log.status == "E_01":
                credits_required = 0
                law_credits_required = 0
                ethics_credits_required = 0

            elif log.status == "E_13":
                credits_required = 16

            # rollover exempt logs who have met credit requirements
            if "AICP" in designation and general_needed == 0 and law_credits_needed == 0 and ethics_credits_needed == 0 and log.status != "A":

                new_log = log.close_and_rollover()
                new_log.credits_required = credits_required
                new_log.law_credits_required = law_credits_required
                new_log.ethics_credits_required = ethics_credits_required
                new_log.status = new_log_status
                new_log.save()

                print("ID: {0} has been rolled over into period: {1}".format(log.contact.user.username, new_log.period.code))

            # grace period for everyone else
            elif "AICP" in designation:
                log.status = "G"
                log.reinstatement_end_time = log.period.grace_end_time
                log.save()

        except Exception as e:

            print("ERROR: {0}".format(str(e)))
            continue

def grace_period(period_code='JAN2019'):

    period = Period.objects.get(code=period_code)
    active_logs = Log.objects.filter(period=period, status__in=("A","E_13","E_02", "E_14"), is_current=True)

    for log in active_logs:
        try:
            credits_overview = log.credits_overview()
            if credits_overview.get("general_needed") != 0 or credits_overview.get("ethics_needed") != 0 or credits_overview.get("law_needed") != 0 :
                print("Log not complete for {0} - changing status and end time".format(str(log.contact.user.username)))
                log.status = "G"
                log.end_time = period.grace_end_time
                log.save()
        except Exception as e:
            print("error changing log {0}".format(e))
            continue


# *********************************************
# ***** CM CONSOLIDATION EXTENSIONS *****
# *********************************************

def consolidation_extensions(logs=None, period_code=None):
    """
    Extend JAN2021 Members by changing their end_time to 12/31/21.
    These members will not be able to close their own JAN2021 reporting period.
    They will not see the 2 new credit topics nor the 1.0 credit hours;
    rather they will only log Law and Ethics and will log 1.5 hours for each. (about 3570 of these)

    Extend JAN2023 members by changing their end_time to 12/31/23.
    They will see all 4 mandatory credit topics as well as 1.0 required hours in their CM log. (about 120 of these)
    """
    if not logs:
        logs = Log.objects.filter(period__code=period_code, is_current=True)

    count = logs.count()
    print("logs count is ", count)

    for i, log in enumerate(logs):
    # try:
        current_period_code = log.period.code

        if current_period_code == "JAN2021":
            # Could have sworn this worked before, but now the dates are wrong again
            # log.end_time = log.end_time.replace(year=2022)
            # so running again with this:
            log.end_time = log.end_time.replace(year=2022, month=1, day=1, hour=5, minute=59, second=59)
            # log.law_credits_required = cm_settings.OLD_CREDITS_REQUIRED
            # log.ethics_credits_required = cm_settings.OLD_CREDITS_REQUIRED
            log.equity_credits_required = 0
            log.targeted_credits_required = 0
        # FROM JIRA 7626 -- THESE MEMBERS SHOULD BE LOGGING 1.0 FOR EVERYTHING
        if current_period_code == "JAN2023":
            # THIS ONE IS NOT CURRENTLY A PROBLEM
            log.end_time = log.end_time.replace(year=2024)
            log.law_credits_required = cm_settings.LAW_CREDITS_REQUIRED
            log.ethics_credits_required = cm_settings.ETHICS_CREDITS_REQUIRED
            log.equity_credits_required = cm_settings.EQUITY_CREDITS_REQUIRED
            log.targeted_credits_required = cm_settings.TARGETED_CREDITS_REQUIRED
            log.targeted_credits_topic = cm_settings.TARGETED_CREDITS_TOPIC

        log.save()

        print("User: {0} has had log extended by one year".format(log.contact.user.username))
        print("%s of %s done." % (i+1, count))

# WE ALSO NEED A NEW SCRIPT TO UPDATE ALL CREDITS REQUIRED ON JAN2024 LOGS TO 1.0
def jan2024_credits_update(logs=None, period_code=None):
    if not logs:
        logs = Log.objects.filter(period__code="JAN2024", is_current=True)

    count = logs.count()

    for i, log in enumerate(logs):
        current_period_code = log.period.code

        if current_period_code == "JAN2024":
            log.law_credits_required = cm_settings.LAW_CREDITS_REQUIRED
            log.ethics_credits_required = cm_settings.ETHICS_CREDITS_REQUIRED
            log.equity_credits_required = cm_settings.EQUITY_CREDITS_REQUIRED
            log.targeted_credits_required = cm_settings.TARGETED_CREDITS_REQUIRED
            log.targeted_credits_topic = cm_settings.TARGETED_CREDITS_TOPIC
            log.save()
            print("User: {0} has had log credits updated to 1.0".format(log.contact.user.username))
            print("%s of %s done." % (i+1, count))


def fix_log_end_times(logs=None, period_code=None):
    """
    Fix JAN2021 Members by changing their end_time to 12/31/21 CST
    Fix JAN2023 members by changing their end_time to 12/31/23 CST
    """
    if not logs:
        logs = Log.objects.filter(period__code=period_code, is_current=True)

    count = logs.count()
    print("logs count is ", count)
    jan2021_end_time = logs.last().end_time.replace(year=2022, month=1, day=1, hour=5, minute=59, second=59)
    jan2023_end_time = logs.last().end_time.replace(year=2024, month=1, day=1, hour=5, minute=59, second=59)
    for i, log in enumerate(logs):
        flag = False
        current_period_code = log.period.code
        if current_period_code == "JAN2021":
            if log.end_time != jan2021_end_time:
                print(log)
                print("END TIME BEFORE: ", log.end_time)
                log.end_time = log.end_time.replace(year=2022, month=1, day=1, hour=5, minute=59, second=59)
                print("END TIME AFTER: ", log.end_time)
                flag = True
        if current_period_code == "JAN2023":
            if log.end_time != jan2023_end_time:
                print(log)
                print("END TIME BEFORE: ", log.end_time)
                log.end_time = log.end_time.replace(year=2024, month=1, day=1, hour=5, minute=59, second=59)
                print("END TIME AFTER: ", log.end_time)
                flag = True
        log.save()
        if flag:
            print("User: {0} has had end time corrected".format(log.contact.user.username))
            print("%s of %s done." % (i+1, count))
