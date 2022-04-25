import django
django.setup()
import json, urllib
import requests
import pytz
import datetime
import logging
import math
import string
import random

from exam.models import *
from cm.models import *
from datetime import date

# YET ANOTHER RANDOM COMMENT
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import is_password_usable
from django.core.mail import send_mail

from datetime import timedelta

from django.db.models import Q

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

from publications.models import Book, EBook
from content.utils import generate_random_string, get_api_key_querystring

def aicp_prorate_import(period_code='JAN2020', begin_date='2017-01-01T00:00:00.000Z', ):
    """
    creates logs for those who have an active prorate status in iMIS
    Pass the period_code that should be used (add 3 years to current year for MAY, 4 years for NOV)
    EXAMPLE: 2016 uses period code JAN2019
    ALSO CHECK THE BEGIN DATE!
    USE THIS AFTER AICP EXAM RESULTS IMPORT
    NOTE: BEGIN TIME WAS CHANGED!!!! 
    """

    code = 'AICP_PRORATE'
    f = '%Y-%m-%d %H:%M:%S'

    url = RESTIFY_SERVER_ADDRESS + '/api/0.2/subscriptions/' + code + get_api_key_querystring() 

    r = requests.get(url)

    aicp_users = r.json()['data']

    # current_date = datetime.now().date()
    # period_begin_time = current_date.replace(month=1, day=1, year=current_date.year+1)
    # period = Period.objects.get(begin_time=period_begin_time)
    period = Period.objects.get(code=period_code)
    logs_created_list = []
    log_begin_time_changes_list = []
    aicp_users_filter_begin_date = [x for x in aicp_users if x['BEGIN_DATE'] == begin_date ]
    print("There are {0} logs to be created in django".format(str(len(aicp_users_filter_begin_date))))
    
    for user_data in aicp_users_filter_begin_date:
        try:
            user_id = user_data['ID']
            # is there a better way to get the last log?
            log = Log.objects.filter(contact__user__username=user_id, period=period).last()

            if not log:
                if not Log.objects.filter(contact__user__username=user_id, is_current=True, end_time__gte=date.today()).exists():
                    # set all other logs for the user to NOT current
                    Log.objects.filter(contact__user__username=user_id).update(is_current=False)

                    contact=Contact.objects.get(user__username=user_id)
                    log = Log.objects.create(contact=contact, period=period)
                    log.is_current = True
                    ###### BEGIN TIME WAS CHANGED - should be period begin_time for MAY exams #######
                    log.begin_time = begin_date[:10] # period.begin_time 
                    log.end_time=period.end_time
                    log.save()
                    logs_created_list.append(user_id)
                    print('log created for: ' + str(user_id))
            else:
                print('log already exists for user:' + str(user_id))

        except Exception as e:
            print('error: ' + str(e))
            continue

    print('aicp prorate check complete.')
    print('logs created for: ' + str(logs_created_list))
    print('log period changes: ' + str(log_begin_time_changes_list))

def drop_exempt_members_fix(period_code):
    # Karl requested members be dropped if in a certain member type vs. comparing paid dates - this is a fix 

    period = Period.objects.get(code=period_code)
    imis_drop_errors = {}
    django_drop_errors = {}
    logs_to_drop = Log.objects.filter(period=period, status__in=("D"), contact__member_type__in=("MEM","LIFE",), is_current=True).annotate(credit_total=Coalesce(Sum("claims__credits"), 0), law_total=Coalesce(Sum("claims__law_credits"), 0), ethics_total=Coalesce(Sum("claims__ethics_credits"), 0)).filter(Q(credits_required__gt=F("credit_total")) | Q(law_credits_required__gt=F("law_total")) | Q(ethics_credits_required__gt=F("ethics_total")))

    logs_count = str(logs_to_drop.count())

    print("NUMBER OF LOGS TO BE DROPPED: " + str(logs_count))
    for log in logs_to_drop:

        log.status = "D"
        log.save()

        try:
            print("dropping log for user:" + str(log.contact.user.username) )
            json_response = log.imis_drop()

            if json_response.get("success") == False:
                imis_drop_errors[log.contact.user.username] = json_response.get("data")
                pass
        except Exception as e:
            print('error dropping log for user: ' + str(log.contact.user.username) + 'ERROR: ' + str(e))
            django_drop_errors[log.contact.user.username] = str(e)
            pass
    print('IMIS DROP ERRORS: ' + str(imis_drop_errors))
    print('DJANGO DROP ERRORS: ' + str(django_drop_errors))

    mail_subject = "Dropped logs for period %s - attempted to drop %s logs" % (period.code, logs_count)
    mail_body = "Period: " + period.code + "<br/>" + "Results" + "<br/>" + "Drop attempt: " + logs_count + "<br/> <br/>" + "iMIS Drop Errors: " + str(imis_drop_errors) + "<br/><br/>" + "Django Drop Errors: " + str(django_drop_errors)

    send_mail(mail_subject, mail_body, "it@planning.org", ["plowe@planning.org"], fail_silently=False, html_message=mail_body)

    return "BAM"

def exempt_rollover(period_code='JAN2016'):
    # roll over exmpt members for retired (E_01) or foreign practice (E_03) logs if the new log does NOT exist.
    # see Axosoft ticket 1552
    
    #exempt_logs = Log.objects.filter(period__code='JAN2016', contact__user__username='052101')
    exempt_logs = Log.objects.filter(period__code=period_code, status__in=("E_01","E_03"), is_current=True)

    f = '%Y-%m-%d %H:%M:%S'
    period_rollover_to =Period.objects.get(code=period_code).rollover_to

    for log in exempt_logs:
        try:
            # make API call to verify the AICP product is paid and valid
            url = RESTIFY_SERVER_ADDRESS + "/api/0.2/contacts/" + str(log.contact.user.username) + "/subscriptions" + get_api_key_querystring() + "&has_bill_amount=0&product_code=AICP"

            r = requests.get(url)

            aicp_product = r.json()['data'][0]

            if aicp_product:

                paid_thru = aicp_product.get("paid_thru").replace("T", " ").replace(".000Z","")
                paid_thru_converted = datetime.strptime(paid_thru, f)

                if datetime.now() < paid_thru_converted:

                    old_log_status = log.status
                    new_log = log.close_and_rollover()
                    new_log.credits_required = 0
                    new_log.law_credits_required = 0
                    new_log.ethics_credits_required = 0
                    new_log.status = old_log_status
                    new_log.save()
                
                previous_logs = Log.objects.filter(contact=log.contact).exclude(period=log.period.rollover_to)
                for previous_log in previous_logs:
                    previous_log.is_current = False
                    previous_log.status="C"
                    previous_log.save()


                print("User ID: {0} has been rolled over into period: {1}".format(log.contact.user.username, new_log.period.code))
            else:

                print("NOT ACTIVE: user {0} no longer has an active paid AICP product".format(log.contact.user.username))
        except Exception as e:

            print("ERROR: {0}".format(str(e)))
            pass

    print("bam")

def assign_grace_period(period_code='JAN2017'):
    # switches the status and end time to reflect grace periods for active and current logs

    period = Period.objects.get(code=period_code)
    active_logs = Log.objects.filter(period=period, status="A", is_current=True)

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

    # problem: if the prices have become mismatched between draft/published records, and you want to restore
    # some missing prices -- you can't just create new prices on the draft and publish -- because some 
    # prices will probably have uuid mismatches. So to restore you will need to get the uuids from prices
    # that only exist on published and then set the new draft prices to the same uuids. Only then can you 
    # publish without getting a ['Cannot delete records with one or more purchases'] message.   

def create_aicp_prorate_prices():

    nov_quarters = ['JAN','ARL','JULY','OCT']
    may_quarters = ['OCT','JAN','ARL','JULY']
    salary_codes = ['A','B','C','D','E','F','G','H','I','P','J','AA','BB','CC','K','KK','LL','L','N','O']
    salary_code_titles = [
    "Under $42,000","Under $42,000","$42,000 - $49,999","$50,000 - $59,999","$60,000 - $69,999",
    "$70,000 - $79,999","$80,000 - $89,999","$90,000 - $99,999","$100,000 - $119,999","$120,000 and above",
    "Undisclosed","INT AA","INT BB","INT CC","US Student Member","INT Student Member","INT New Professional",
    "US New Professional","US Retired Member","US Life Member"
    ]

    prices = [100,100,115,125,135,145,155,165,175,185,190,35,60,110,25,25,25,25,25,15]

    prorate_percentage = 0

    # THIS GET THE PUBLISHED PRODUCT
    product = Product.objects.get(code='MEMBERSHIP_AICP_PRORATE', content__publish_status='DRAFT')
    pub_product = Product.objects.get(code='MEMBERSHIP_AICP_PRORATE', content__publish_status='PUBLISHED')
    # THIS DOES NOT WORK?
    # don't do this -- the get_or_create takes care of not duplicating prices
    # we don't want to delete draft prices because then the uuid won't match prod
    # product.prices.delete()

    for x in nov_quarters:
    # for i,x in enumerate(nov_quarters)

        if x == 'JAN':
            prorate_percentage = 1
        elif x == 'ARL':
            prorate_percentage = .25
        elif x == 'JULY':
            prorate_percentage = .5
        elif x == 'OCT':
            prorate_percentage = .75
            
        for i,y in enumerate(salary_codes):
            price = prices[i]*prorate_percentage
            code = y + "_" + x + "_FALL"
            title = y + "_" + salary_code_titles[i] + "_" + str(int(prorate_percentage*100))
            print(price)

            draft_price, created = ProductPrice.objects.get_or_create(title=title, code=code, product=product, price=price)
            pub_price = ProductPrice.objects.filter(title=title, code=code, product=pub_product, price=price).first()
            if pub_price:
                draft_price.publish_uuid = pub_price.publish_uuid
                draft_price.save()

    for x in may_quarters:
    # for i,x in enumerate(nov_quarters)

        if x == 'OCT':
            prorate_percentage = .25
        elif x == 'JAN':
            prorate_percentage = .5
        elif x == 'ARL':
            prorate_percentage = .75
        elif x == 'JULY':
            prorate_percentage = 1

        for i,y in enumerate(salary_codes):
            price = prices[i]*prorate_percentage
            code = y + "_" + x + "_SPRING"
            title = y + "_" + salary_code_titles[i] + "_" + str(int(prorate_percentage*100))
            print(price)

            draft_price, created = ProductPrice.objects.get_or_create(title=title, code=code, product=product, price=price)
            pub_price = ProductPrice.objects.filter(title=title, code=code, product=pub_product, price=price).first()
            if pub_price:
                draft_price.publish_uuid = pub_price.publish_uuid
                draft_price.save()


"""
# TEST CODE FOR ABOVE
products = Product.objects.filter(code='MEMBERSHIP_AICP_PRORATE')

for p in products:
    print(p.publish_status)
    print(p.prices.count())
    print()

from _data_tools.aicp import *

create_aicp_prorate_prices()

# check that uuids are same from draft to published

product = Product.objects.get(code='MEMBERSHIP_AICP_PRORATE', content__publish_status='DRAFT')
pub_product = Product.objects.get(code='MEMBERSHIP_AICP_PRORATE', content__publish_status='PUBLISHED')

for p in product.prices.all():
    pub_p = ProductPrice.objects.filter(title=p.title, code=p.code, product=pub_product, price=p.price).first()
#   print("draft uuid: ", p.publish_uuid)
#   print("published uuid: ", pub_p.publish_uuid)
    if pub_p:
        if p.publish_uuid != pub_p.publish_uuid:
            print("UUIDS NOT EQUAL FOR: ", p)
            print("published: ", pub_p)
            print()
    else:
        print("NO CORRESPONDING PUBLISHED PRICE TO: ", p)
"""

# NOT CURRENTLY USED:
def update_aicp_prorate_prices():

    nov_quarters = ['JAN','ARL','JULY','OCT']
    may_quarters = ['OCT','JAN','ARL','JULY']
    salary_codes = ['A','B','C','D','E','F','G','H','I','P','J','AA','BB','CC','K','KK','LL','L','N','O']
    salary_code_titles = [
    "Under $42,000","Under $42,000","$42,000 - $49,999","$50,000 - $59,999","$60,000 - $69,999",
    "$70,000 - $79,999","$80,000 - $89,999","$90,000 - $99,999","$100,000 - $119,999","$120,000 and above",
    "Undisclosed","INT AA","INT BB","INT CC","US Student Member","INT Student Member","INT New Professional",
    "US New Professional","US Retired Member","US Life Member"
    ]

    prices = [100,100,115,125,135,145,155,165,175,185,190,35,60,110,25,25,25,25,25,15]

    prorate_percentage = 0

    product = Product.objects.get(code='MEMBERSHIP_AICP_PRORATE', content__publish_status='DRAFT')
    # THIS DOES NOT WORK:
    # product.prices.delete()

    for x in nov_quarters:
    # for i,x in enumerate(nov_quarters)

        if x == 'JAN':
            prorate_percentage = 1
        elif x == 'ARL':
            prorate_percentage = .25
        elif x == 'JULY':
            prorate_percentage = .5
        elif x == 'OCT':
            prorate_percentage = .75
            
        for i,y in enumerate(salary_codes):
            price = prices[i]*prorate_percentage
            code = y + "_" + x + "_FALL"
            title = y + "_" + salary_code_titles[i] + "_" + str(int(prorate_percentage*100))
            print(price)

            pps = ProductPrice.objects.filter(title=title, code=code, product=product)
            print("before loop")
            print("pps.count() ", pps.count())

            # for pp in pps:
            #     price_str = str(price)
            #     pp.price = Decimal(price_str)
            #     print("before save")
            #     pp.save()
            #     print("after save")

    for x in may_quarters:
    # for i,x in enumerate(nov_quarters)

        if x == 'OCT':
            prorate_percentage = .25
        elif x == 'JAN':
            prorate_percentage = .5
        elif x == 'ARL':
            prorate_percentage = .75
        elif x == 'JULY':
            prorate_percentage = 1

        for i,y in enumerate(salary_codes):
            price = prices[i]*prorate_percentage
            code = y + "_" + x + "_SPRING"
            title = y + "_" + salary_code_titles[i] + "_" + str(int(prorate_percentage*100))
            print(price)

            pps = ProductPrice.objects.filter(title=title, code=code, product=product)
            print("pps.count() ", pps.count())
            # for pp in pps:
            #     price_str = str(price)
            #     pp.price = Decimal(price_str)
            #     pp.save()

    # for x in may_quarters:
    #     for y in salary_codes:
    #         codes.append(y + "_" + x + "_SPRING")


# UPDATE PRORATE PRICES

# upps = update prorate prices
def upps():
    products = Product.objects.filter(code='MEMBERSHIP_AICP_PRORATE')
    salary_codes = ['A','B','C','D','E','F','G','H','I','P','J','AA','BB','CC','K','KK','LL','L','N','O']
    prices = [100,100,115,125,135,145,155,165,175,185,190,35,60,110,25,25,25,25,25,15]
    nov="_ARL_FALL"

    for i,sc in enumerate(salary_codes):
        code = sc + nov
        pps = ProductPrice.objects.filter(code=code)
        for pp in pps:
            nuprice = prices[i] * 1.25
            pp.price = nuprice
            print(code, nuprice)
            print(pp)
            print(pp.price)
            print()
            pp.save()

    print()
    print()
    octo="_OCT_FALL"

    for i,sc in enumerate(salary_codes):
        code = sc + octo
        pps = ProductPrice.objects.filter(code=code)
        for pp in pps:
            nuprice = prices[i] * 1.25
            pp.price = nuprice
            print(code, nuprice)
            print(pp)
            print(pp.price)
            print()
            pp.save()

    for p in products:
        p.save()


def fix_exam_app_data(exam_code="2016NOV", user_id=None):
    """
    this guy will attempt to fix the link between exam applications, registrations, and degrees
    """

    exam = Exam.objects.get(code=exam_code)

    registration_list = []
    no_exam_app_list = []
    no_degrees_list = []
    added_application_list = []
    if user_id:
        try:
            registration_list.append(ExamRegistration.objects.get(exam=exam, contact__user__username=user_id))
        except Exception as e:
            print("ERROR: " +str(e))
    else:
        registration_list = ExamRegistration.objects.filter(exam=exam).exclude(purchase__order__isnull=True)

    for x in registration_list:
        try:
            # make sure the registration has an application linked to it
            if not x.application:
                print("User does not have an application....finding the last approved and linking...")
                approved_app = ExamApplication.objects.filter(publish_status="DRAFT", contact=x.contact, application_status="A", exam__in=exam.previous_exams.all()).last()
                added_application_list.append(x.contact.user.username)
                if not approved_app:
                    print("No previous approved exam application has been found. Moving onto the next user.")
                    no_exam_app_list.append(x.contact.user.username)
                    continue
                else:
                    x.application = approved_app
                    x.save()

            if not x.application.applicationdegree_set.all():
                print("user does not have any degrees listed on the app 'draft' -  attempting to add degrees from other publish statuses.")

                app_with_degree = ExamApplication.objects.filter(master=x.application.master).exclude(applicationdegree__isnull=True).last()
                if app_with_degree:
                    for d in app_with_degree.applicationdegree_set.all():
                        d.pk = None
                        d.application = x.application
                        d.save()
                    
                    print("success! found a degree. added.")
                else:
                    print("no degrees found for other apps.")
                    no_degrees_list.append(x.contact.user.username)
        except Exception as e:
            print("ERROR: " + str(e))
    print("completed")
    print("------------------------------")
    print("no exam apps:" + str(no_exam_app_list))
    print("------------------------------")
    print("no degrees on app: " + str(no_degrees_list))
    print("------------------------------")
    print("application added to registration: " + str(added_application_list))



# def create_missing_logs():
#   """
#   simple method to create missing credit logs for those who have purchased AICP membership
#   """

#   aicp_purchases = Purchase.objects.filter(product__code="MEMBERSHIP_AICP").exclude(order__isnull=True)

#   create_missing_log_errors = {}
#   new_logs_created = {}
#   for purchase in aicp_purchases:
#       try:
#           contact = purchase.contact

#           purchase_date_time = purchase.submitted_time
#           credit_period_year = purchase_date_time.replace(year = purchase_date_time.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

#           period = Period.objects.get(begin_time=credit_period_year)
#           log, created = Log.objects.get_or_create(contact=contact, period=period)

#           # do we want to change this automatically?
#           if not log.begin_time and not log.end_time:
#               log.begin_time = purchase.submitted_time
#               log.end_time = period.end_time
#               log.save()
#           if created:
#               print('Log was created for ' + str(purchase.contact.user.username) + ' | ' + 'period code: ' + period.code)
#               new_logs_created[purchase.contact.user.username] = period.code
#           else:
#               print('log already exists..')
#       except Exception as e:
#           create_missing_log_errors[purchase.contact.user.username] = str(e)
#           print('error: ' + str(e))
#           continue

# def aicp_log_check(code='AICP_PRORATE'):
#     """
#     creates logs for those who have an active prorate status in iMIS
#     code = AICP or AICP_PRORATE
#     1. get current period based on today's date
#     2. if the code AICP_PRORATE is passed in, look fo an exisitng log equal to the current date log returned
#     3. If this log exists and the payment date jumps the period, change the period code to match.
#     """

#     f = '%Y-%m-%d %H:%M:%S'

#     url = RESTIFY_SERVER_ADDRESS + '/api/0.2/subscriptions/' + code + get_api_key_querystring() 

#     r = requests.get(url)

#     aicp_users = r.json()['data']

#     # current_date = datetime.now().date()
#     # period_begin_time = current_date.replace(month=1, day=1, year=current_date.year+1)
#     # period = Period.objects.get(begin_time=period_begin_time)

#     logs_created_list = []
#     log_begin_time_changes_list = []
#     for user_data in aicp_users:
#         try:
#             user_id = user_data['ID']
#             payment_date = user_data['PAYMENT_DATE']
#             period_code = user_data['CREDIT_PERIOD']
#             # is there a better way to get the last log?
#             log = Log.objects.filter(contact__user__username=user_id).order_by('period__code').last()

#             period = Period.objects.get(code=period_code)
#             if not log:

#                 contact=Contact.objects.get(user__username=user_id)
#                 log = Log.objects.create(contact=contact, period=period)

#                 if payment_date:
#                     payment_date = pytz.utc.localize(datetime.strptime(payment_date, f))
#                     if payment_date < log.begin_time:
#                         print('payment date is less than the log begin time... assinging payment date as log begin time')
#                         log_begin_time_changes_list.append(user_id)
#                         log.begin_time = payment_date
#                     else:        
#                         log.begin_time = period.begin_time
#                 log.end_time=period.end_time
#                 log.save()
#                 logs_created_list.append(user_id)
#                 print('log created for: ' + str(user_id))
#             else:
#                 print('log already exists for user:' + str(user_id))

#             # ONLY POSSIBILITY OF CHANGING THE PERIOD IS FOR AICP_PRORATE PRODUCTS

#             # if payment_date and code=='AICP_PRORATE':
#             #     payment_date = pytz.utc.localize(datetime.strptime(payment_date, f))
#             #     if payment_date > log.begin_time:
#             #         print('payment date is greater than the log begin time... changing periods')
#             #         user_log_begin_time = payment_date
#             #         user_period_begin_time = payment_date.replace(month=1,day=1,year=payment_date.year+1)
#             #         user_period = Period.objects.get(begin_time=user_period_begin_time)
#             #         user_period_end_time = user_period.end_time
                    
#             #         log.period = user_period
#             #         log.begin_time = user_log_begin_time
#             #         log.end_time = user_period_end_time
#             #         log.save()
#             #         log_period_changes_list.append(user_id)

#         except Exception as e:
#             print('error: ' + str(e))
#             continue

#     print('aicp prorate check complete.')
#     print('logs created for: ' + str(logs_created_list))
#     print('log period changes: ' + str(log_begin_time_changes_list))


# ********************************
# AICP PRORATE PRICES VERIFICATION and REPAIR
# ********************************

# THIS METHOD VERIFIES AND FIXES ALL PRORATE PRICES
# BASED ON 2018 WORD DOCUMENT
def verify_prorate_prices():
    SEASONS = ["FALL", "SPRING"]
    MONTHS = ["JAN", "ARL", "JULY", "OCT", "JAN", "ARL", "JULY", "OCT"]
    SCALARS = [1,1.25,.5,.75,.5,.75,1,1.25]
    products = Product.objects.filter(code='MEMBERSHIP_AICP_PRORATE')
    salary_codes = ['A','B','C','D','E','F','G','H','I','P','J','AA','BB','CC','K','KK','LL','L','N','O']
    prices = [100,100,115,125,135,145,155,165,175,185,190,35,60,110,0,0,70,70,25,15]

    for mon in range(0,len(MONTHS)):
        month = MONTHS[mon]
        scalar = SCALARS[mon]
        seas_index = math.floor(mon / 4.0)
        seas = SEASONS[seas_index]
        for i in range(0,len(prices)):
            sal_code = salary_codes[i]
            base_price = prices[i]
            calc_price = base_price*scalar
            # print("calc_price is", calc_price)
            ppr_code = sal_code + "_" + month + "_" + seas
            # print("ppr code is ", ppr_code)
            pprs = ProductPrice.objects.filter(code=ppr_code)
            for ppr in pprs:
                actual_price = ppr.price
                # print("actual_price is ", actual_price)
                if calc_price == actual_price:
                    # print("prices match")
                    pass
                else:
                    print("***** NO MATCH FOR %s" % (ppr))
                    ppr.price = calc_price
                    ppr.save()

    for p in products:
        p.save()

vpp = verify_prorate_prices
