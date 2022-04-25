import django
django.setup()
import json, urllib
import requests
import pytz
import datetime
import logging
import math

# YET ANOTHER RANDOM COMMENT
from django.contrib.auth.models import User
from django.core.mail import send_mail

from datetime import timedelta

from django.db.models import Q

from cm.models import Log, Period, Claim, CMComment, ProviderRegistration, ProviderApplication
from content.models import MasterContent, TagType, Tag, ContentTagType, TaxoTopicTag
from pages.models import Page
from events.models import EventMulti, EventSingle, Activity, Course, NationalConferenceActivity, Event

from planning.settings import ENVIRONMENT_NAME, RESTIFY_SERVER_ADDRESS
from urllib.request import urlopen
from urllib import parse
from xml.dom import minidom

from content.utils import generate_random_string

def load_json(url):
    with urllib.request.urlopen(url) as response:
        json_string = response.readall().decode('utf-8')
    return json.loads(json_string)

def get_cm_period_all(period_code):
    """
    returns all logs that contain an effective start and end date based on period code passed
    """
    credit_period_all = load_json(RESTIFY_SERVER_ADDRESS + '/cm/dates/' + period_code)

    for credit_period in credit_period_all['data']:

        try:

        	username = credit_period['ID']

        	begin_time = credit_period['PERIOD_EFFECTIVE_START']
        	end_time = credit_period['PERIOD_EFFECTIVE_END']
        	period_code = credit_period['CREDIT_PERIOD']
            # do we need grace period ?? 
            # grace_end_time = sql_to_utc(credit_period['GraceEndDateTime']) 
 			
        	log = Log.objects.get(period__code=period_code, contact__user__username=username)


        	log.begin_time = begin_time
        	log.end_time = end_time
        	log.save()
        	
        	print ("dates imported for user id: " + str(username))

        except Exception as e:
            print(e)
            continue

# Update "Grace Period" Status' End Time to 5/2/2018
# Please update the logs end time for members with the "Grace Period" status' 
# from 4/30/2018 to 5/2/2018 for each member's CM log in the 2016-2017 period.
def update_log_end_time(ls=None):
    zone=pytz.timezone(zone="America/Chicago")
    j18 = Period.objects.get(code="JAN2018")
    # actually 11:59:59pm on may 2
    may_2_2018_23_59_59 = datetime.datetime(2018, 5, 2, 23, 59, 59)
    may_2_2018_23_59_59_chicago = zone.localize(may_2_2018_23_59_59)
    may2 = may_2_2018_23_59_59_chicago
    # but we should be storing data in utc
    may2utc = may2.astimezone(pytz.utc)
    # this query is working, even though outside of this the utc/local thing
    # makes the date numbers look wrong -- this returns 4/30 local and 5/1 utc
    if not ls:
        ls=Log.objects.filter(end_time__year=2018, end_time__month=4, end_time__day=30,
            period=j18, status='G')
    # need to change the end_time to 5/2 midnight Chicago which will be 
    # 5/3 5am utc
    count = ls.count() * 1.0
    for i, log in enumerate(ls):
        log.end_time = may2utc
        log.save()
        print("%s%% complete" % ((i/count)*100))
    print("DONE\n")



