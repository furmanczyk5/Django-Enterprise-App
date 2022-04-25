import random
from datetime import datetime
from datetime import timedelta
import pytz
from decimal import Decimal

from django.db.models.query import *
from django.db.models import Q
from django.contrib.auth.models import User, Group
from django.conf import settings

from conference.models import NationalConferenceActivity
from content.models import Content, ContentRelationship, ContentTagType, TagType, Tag
from events.models import Event, Activity, Course, \
    NATIONAL_CONFERENCE_PROGRAM, EventMulti, NATIONAL_CONFERENCE_NEXT
from store.models import Product, ProductPrice, ProductOption
from pages.models import Page, LandingPageMasterContent
from myapa.models.proxies import Organization
from myapa.models.contact_role import ContactRole
from learn.models import LearnCourse, LearnCourseInfo, LearnCourseBundle
from learn.utils.wcw_api_utils import LMS_TEMPLATE_ID_STAGING, LMS_TEMPLATE_ID_PROD, MULTI_EVENT_CODE, \
    CONFERENCE_PREFIX, TWO_DIGIT_YEAR, LEARN_SESSION_DIGIT, COURSE_CREATE_PREFIX, LEARN_COURSE_PREFIX, \
    RUN_TIME_CM, RUN_TIME

"""
Script to create new on-demand events (courses) that correspond to Conference Sessions and Deep Dives
"""
ALL_TAG_CODES = [
"SESSION",
"POSTER",
"SPECIAL_EVENT",
"ORIENTATION_TOUR",
"MOBILE_WORKSHOP",
"CAREER_ZONE",
"SPECIAL_PROGRAMMING",
"FAST_FUNNY",
"TRAINING_WORKSHOP",
"RECEPTIONS",
"DEEP_DIVE",
"MEETING",
"EXHIBIT_HALL",
]

# Kimberly is saying there are about 170
TAG_CODES = [
"SESSION",
]

MISSING_SESSION_CODES = [
"NPC189001", "NPC189004", "NPC189008", "NPC189009", "NPC189010"
]

missing = Event.objects.filter(code__in=MISSING_SESSION_CODES, publish_status='DRAFT')

# mod = make on-demand
def mod(sessions=None):
    tz = pytz.timezone("US/Central")
    jan1st2018 = tz.localize(datetime(2018, 1, 1), is_dst=None)
    # window of reporting availibility
    first_date_available = tz.localize(datetime(2018, 6, 1), is_dst=None)
    last_date_available = tz.localize(datetime(2021, 6, 1), is_dst=None)
    format_tag_type = TagType.objects.get(title__contains="Format")
    # od_tags = Tag.objects.filter(Q(title__contains="Sessions & Discussions") | Q(title__contains="Deep Dives"))
    od_tags = Tag.objects.filter(code__in=TAG_CODES)
    od_parent_landing_master = LandingPageMasterContent.objects.get(id=9027802)
    on_demand_template = "events/newtheme/ondemand/course-details.html"

    if not sessions:
        sessions = Event.objects.filter(
            contenttagtype__tags__in=od_tags,
            begin_time__gte=jan1st2018,
            parent__content_live__code=NATIONAL_CONFERENCE_PROGRAM[0],
            publish_status='DRAFT'
            ).distinct("id")
        # sesh = sessions.first()
        # print("first session to be copied is ", sesh)
        # digital_product_url=, Ben will have to enter?? ONLY SET ON ORIGINAL LIVE EVENT?
        # resource_url # ben will be add this (media server link?)
        # length_in_minutes, -- Ben: blank What is this for?
    print("**********************************")
    print("Sessions count is ", sessions.count())
    print()

    for sesh in sessions:
        course_code = None
        session_code = sesh.code
        if session_code:
            tokens = session_code.split("NPC18")
            if len(tokens) > 1:
                course_code = "LRN18" + tokens[1]
            elif len(tokens) == 1:
                course_code = "LRN18_NO_NPC_" + tokens[0] + "_" + str(int(random.random()*9999))
        else:
            course_code = "LRN18_NO_CODE_" + str(int(random.random()*9999))
        new_ond, created = Course.objects.get_or_create(
            # For APA Learn make visibility status of new courses "H"
            status="H",
            publish_status="DRAFT",
            text=sesh.text,
            description=sesh.description,
            title=sesh.title,
            featured_image=sesh.featured_image,
            thumbnail=sesh.thumbnail,
            is_free=False,
            is_online=True,
            # ALSO NEED TO PROCESS THE CODE:
            # REPLACE NPC WITH LRN
            code=course_code,
            begin_time=first_date_available,
            end_time=last_date_available,
            cm_status=sesh.cm_status,
            cm_approved=sesh.cm_approved,
            cm_law_approved=sesh.cm_law_approved,
            cm_ethics_approved=sesh.cm_ethics_approved,
            parent_landing_master=od_parent_landing_master,
            template=on_demand_template,
            )
        print("new on demand course is: ", new_ond)
        print("new course publish status is: ", new_ond.publish_status)
        contact_roles = sesh.contactrole.all()
        for cr in contact_roles:
            new_cr, created = ContactRole.objects.get_or_create(
                content=new_ond,
                contact=cr.contact,
                role_type=cr.role_type,
                sort_number=cr.sort_number,
                confirmed=cr.confirmed,
                invitation_sent=cr.invitation_sent,
                special_status=cr.special_status,
                permission_content=cr.permission_content,
                permission_av=cr.permission_av,
                content_rating=cr.content_rating,
                first_name=cr.first_name,
                middle_name=cr.middle_name,
                last_name=cr.last_name,
                bio=cr.bio,
                email=cr.email,
                phone=cr.phone,
                company=cr.company,
                cell_phone=cr.cell_phone
                )

        apa_org=Organization.objects.get(user__username=119523)
        apa_provider_list = [p for p in new_ond.contactrole.all() if p.role_type == "PROVIDER" and p.contact == apa_org]

        if not apa_provider_list:
            apa_provider, created = ContactRole.objects.get_or_create(
                content=new_ond,
                contact=apa_org,
                role_type="PROVIDER",
                sort_number=99,
                )

        content_tag_types = sesh.contenttagtype.all()
        # tags are different from activity to course:
        # course: change live in person tag to on demand education tag
        # course: add "Featured Content " tag type and 2017 National Planning Conference Recordings tag

        for ctt in content_tag_types:
            tag_type = ctt.tag_type
            if tag_type.title != "Format":
                tags = ctt.tags.all()
            else:
                tags = Tag.objects.filter(tag_type=tag_type, title="On-Demand Education")

            new_ctt, created = ContentTagType.objects.get_or_create(
                content=new_ond,
                tag_type=tag_type,
                # tags=tags
                )
            # add the tags in a 2nd step
            # loop thrugh the tags and call new_ctt.tags.add(tag)
            new_ctt.tags.clear()

            for tag in tags:
                new_ctt.tags.add(tag)
                new_ctt.save()

        featured_content_tag_type = TagType.objects.get(title="Featured Content")
        npc18recordings_tag, created = Tag.objects.get_or_create(
            tag_type=featured_content_tag_type,
            title="2018 National Planning Conference Recordings",
            code="EVENTS_NPC18_RECORDINGS"
            )
        new_ctt, created = ContentTagType.objects.get_or_create(
            content=new_ond,
            tag_type=featured_content_tag_type,
            # tags=tags
            )
        new_ctt.tags.add(npc18recordings_tag)
        new_ctt.save()


        # ADD TAXONOMY TAGS
        topic_tags_list = list(sesh.taxo_topics.all())
        new_ond.taxo_topics.set(topic_tags_list)

        # FOR NOW DON'T DO PRICES -- SIGNIFICANT DEVELOPMENT WORK
        # WILL BE REQUIRED FOR THAT

        # organizations_can_purchase=True, ?? needed?
        product, created = Product.objects.get_or_create(
            content=new_ond,
            title=sesh.title,
            description=sesh.description,
            code=course_code,
            product_type="STREAMING",
            imis_code=course_code,
            gl_account="470130-MF1408",
            )

        # product_option_one, created = ProductOption.objects.get_or_create(
        # 	title="Individual Viewing",
        # 	code="STREAMING_INDIVIDUAL",
        # 	description="Individual Viewing",
        # 	product=product,
        # 	sort_number=1,
        # 	)
        # product_option_two, created = ProductOption.objects.get_or_create(
        # 	title="Group Viewing",
        # 	code="STREAMING_GROUP",
        # 	description="Group Viewing",
        # 	product=product,
        # 	sort_number=2,
        # 	)

        # def get_opt_code(i):
        # 	if i in [0,1,3]:
        # 		return "STREAMING_INDIVIDUAL"
        # 	elif i == 2:
        # 		return "STREAMING_GROUP"
        # 	elif i >3:
        # 		raise ValueError("Index exceeded 3 -- should only create six prices.")
        # 	else:
        # 		raise ValueError("Default error.")

        # titles = ["NPC18 attendee", "APA member", "Group viewing", "List Price"]
        # prices =  ['0.00','68.00','300.00','80.00']
        # priorities = [1, 2 ,10 ,99]

        # # titles = ["NPC17 attendee", "AICP member", "APA member", "Group viewing", "Nonmember", "List Price"]
        # # prices = [Decimal(p) for p in ['0.00','60.00','68.00','300.00','80.00','80.00']]
        # # priorities = [1,2,3,10,10,99]
        # # "aicpmember",
        # groups = [Group.objects.get(name=gn) for gn in ["18CONF","member"]]

        # for i in range(0,len(titles)):
        # 	title = titles[i]
        # 	price = prices[i]
        # 	priority = priorities[i]
        # 	# group = groups[i] if i<3 else None
        # 	option_code = get_opt_code(i)

        # 	new_pp, created = ProductPrice.objects.get_or_create(
        # 		title=title,
        # 		product=product,
        # 		price=price,
        # 		priority=priority,
        # 		begin_time=first_date_available,
        # 		# required_groups=groups,
        # 		option_code=option_code,
        # 		include_search_results=True,
        # 		)

        # 	new_pp.required_groups.clear()

        # 	if i < 2:
        # 		new_pp.required_groups.add(groups[i])
        # 		new_pp.save()
    # new_ond.publish()

    print("at end new_ond publish status is ", new_ond.publish_status)
    print()
    return new_ond


def get_sessions(sessions=None):
    tz = pytz.timezone("US/Central")
    jan1st2017 = tz.localize(datetime(2017, 1, 1), is_dst=None)
    # window of reporting availibility
    first_date_available = tz.localize(datetime(2017, 6, 1), is_dst=None)
    last_date_available = tz.localize(datetime(2020, 6, 1), is_dst=None)
    format_tag_type = TagType.objects.get(title__contains="Format")
    od_tags = Tag.objects.filter(Q(title__contains="Sessions & Discussions") | Q(title__contains="Deep Dives"))
    od_parent_landing_master = LandingPageMasterContent.objects.get(id=9027802)
    on_demand_template = "events/newtheme/ondemand/course-details.html"

    if not sessions:
        sessions = Event.objects.filter(
            contenttagtype__tags__in=od_tags,
            begin_time__gte=jan1st2017,
            parent__content_live__code=NATIONAL_CONFERENCE_PROGRAM[0],
            publish_status='DRAFT'
            ).distinct("id")
    return sessions

def samp_sesh(seshes=None):
    for i in range(0,10):
        n=int(random.random()*350)
        s=seshes[n]
        ss=seshes.filter(master_id=s.master_id)
        print("All sessions with same master")
        print(ss)
        for s in ss:
            print(s.master_id)
            print(s.publish_status)
            print(s.id)
        print()

# PRODUCT EXAMPLE: ON DEMAND HOME GROWN WINERIES DISTILLeries, Marijuana, Master ID 3031109

# TEST LIKE THIS:
# od = mod()

"""
Here are a couple of examples for testing:

Session- https://planning.org/admin/conference/nationalconferenceactivity/475505/change/?_changelist_filters=p%3D2
Master ID: 9109848
Deep Dive- https://planning.org/admin/conference/nationalconferenceactivity/476642/change/?_changelist_filters=p%3D2
Master ID: 9107237

session:
import django
django.setup()
from events.models import *
from _data_tools.on_demand import *
es=Event.objects.filter(master_id=9109848, publish_status="PUBLISHED")
od=mod(es)

import django
django.setup()
from events.models import *
from _data_tools.on_demand import *
es=Event.objects.filter(master_id=9107237, publish_status="PUBLISHED")
od=mod(es)

"""
# dod = delete on demand
def dod(sessions=None):
    tz = pytz.timezone("US/Central")
    jan1st2017 = tz.localize(datetime(2017, 1, 1), is_dst=None)
    # window of reporting availibility
    first_date_available = tz.localize(datetime(2017, 6, 1), is_dst=None)
    last_date_available = tz.localize(datetime(2020, 6, 1), is_dst=None)
    format_tag_type = TagType.objects.get(title__contains="Format")
    od_tags = Tag.objects.filter(Q(title__contains="Sessions & Discussions") | Q(title__contains="Deep Dives"))
    od_parent_landing_master = LandingPageMasterContent.objects.get(id=9027802)
    on_demand_template = "events/newtheme/ondemand/course-details.html"

    if not sessions:
        sessions = Event.objects.filter(
            contenttagtype__tags__in=od_tags,
            begin_time__gte=jan1st2017,
            parent__content_live__code=NATIONAL_CONFERENCE_PROGRAM[0],
            publish_status='DRAFT'
            ).distinct("id")
        # sesh = sessions.first()
        # print("first session to be copied is ", sesh)
        # digital_product_url=, Ben will have to enter?? ONLY SET ON ORIGINAL LIVE EVENT?
        # resource_url # ben will be add this (media server link?)
        # length_in_minutes, -- Ben: blank What is this for?
    print("**********************************")
    print("Sessions count is ", sessions.count())
    print()

    for sesh in sessions:
        new_ond, created = Course.objects.get_or_create(
            publish_status="DRAFT",
            text=sesh.text,
            description=sesh.description,
            title=sesh.title,
            featured_image=sesh.featured_image,
            thumbnail=sesh.thumbnail,
            is_free=False,
            is_online=True,
            code=sesh.code,
            begin_time=first_date_available,
            end_time=last_date_available,
            cm_status=sesh.cm_status,
            cm_approved=sesh.cm_approved,
            cm_law_approved=sesh.cm_law_approved,
            cm_ethics_approved=sesh.cm_ethics_approved,
            parent_landing_master=od_parent_landing_master,
            template=on_demand_template,
            )
        print("new on demand course is: ", new_ond)
        print("new course publish status is: ", new_ond.publish_status)
        print("new on demand was created: ", created)
        new_ond.delete()

# modi = make on demand inactive
def modi(sessions=None):
    tz = pytz.timezone("US/Central")
    jan1st2017 = tz.localize(datetime(2017, 1, 1), is_dst=None)
    # window of reporting availibility
    first_date_available = tz.localize(datetime(2017, 6, 1), is_dst=None)
    last_date_available = tz.localize(datetime(2020, 6, 1), is_dst=None)
    format_tag_type = TagType.objects.get(title__contains="Format")
    od_tags = Tag.objects.filter(Q(title__contains="Sessions & Discussions") | Q(title__contains="Deep Dives"))
    od_parent_landing_master = LandingPageMasterContent.objects.get(id=9027802)
    on_demand_template = "events/newtheme/ondemand/course-details.html"

    if not sessions:
        sessions = Event.objects.filter(
            contenttagtype__tags__in=od_tags,
            begin_time__gte=jan1st2017,
            parent__content_live__code=NATIONAL_CONFERENCE_PROGRAM[0],
            publish_status='DRAFT'
            ).distinct("id")
        # sesh = sessions.first()
        # print("first session to be copied is ", sesh)
        # digital_product_url=, Ben will have to enter?? ONLY SET ON ORIGINAL LIVE EVENT?
        # resource_url # ben will be add this (media server link?)
        # length_in_minutes, -- Ben: blank What is this for?
    print("**********************************")
    print("Sessions count is ", sessions.count())
    print()

    for sesh in sessions:
        new_ond, created = Course.objects.get_or_create(
            publish_status="DRAFT",
            text=sesh.text,
            description=sesh.description,
            title=sesh.title,
            featured_image=sesh.featured_image,
            thumbnail=sesh.thumbnail,
            is_free=False,
            is_online=True,
            code=sesh.code,
            begin_time=first_date_available,
            end_time=last_date_available,
            cm_status=sesh.cm_status,
            cm_approved=sesh.cm_approved,
            cm_law_approved=sesh.cm_law_approved,
            cm_ethics_approved=sesh.cm_ethics_approved,
            parent_landing_master=od_parent_landing_master,
            template=on_demand_template,
            )
        print("new on demand course is: ", new_ond)
        print("new course publish status is: ", new_ond.publish_status)
        print("new on demand was created: ", created)
        new_ond.status = 'I'
        new_ond.save()
        new_ond.publish()

# **********************
# FIX DUPE PRODUCT CODES
# **********************

# query = Product.objects.filter(publish_status='PUBLISHED').query

def get_doops():
    query = Product.objects.all().query
    query.group_by = ['code']
    results = QuerySet(query=query, model=Product)
    s=set()
    for r in results:
        same_code_group = results.filter(code=r.code)
        if same_code_group.count() > 2:
            # print(r)
            s.add(r.code)

    s2 = set()
    for i in s:
        if i.find("ACTIVITY") < 0:
            s2.add(i)
    return s2

def get_slms():
    query = Product.objects.all().query
    query.group_by = ['code']
    results = QuerySet(query=query, model=Product)
    results = results.filter(Q(code="STREAM_LMS") | Q(imis_code="STREAM_LMS"), publish_status="DRAFT")
    return results

def get_doop_slms_codes(results):
    s=set()
    s2=set()
    for r in results:
        same_code_group = results.filter(code=r.code)
        if same_code_group.count() > 1:
            # print(r)
            # s.add((r.code, same_code_group.count()))
            s.add(r.code)
        else:
            s2.add(r.code)
    return (s, s2)

def print_slms(rs):
    print()
    print("-----------------------------------")
    print("START OF STREAMING_LMS PRINT")
    for p in rs:
        print("Title: %s" % p.title)
        print("Product type: %s" % p.product_type)
        print("code:      ", p.code)
        print("imis_code: ", p.imis_code)
        #print("GL Account: %s" % gl_account)
        print()
    print("END OF STREAMING_LMS PRINT")
    print("---------------------------------\n")

def print_doops(s2):
    for c in s2:
        print("PRODUCTS WITH CODE %s" % c)
        print("---------------------------------")
        ps = Product.objects.filter(code=c, publish_status='PUBLISHED')
        for p in ps:
            print("Title: %s" % p.title)
            print("Product type: %s" % p.product_type)
            print("imis_code: ", p.imis_code)
            #print("GL Account: %s" % gl_account)
        print("---------------------------------\n")

# FOR REFERENCE
same_titles = ['STR_TDRO','S513NPC16', 'STR_TGPGC', 'S409NPC16', 'STR_TIP2D1',
    'STR_TIZBAD', 'STR_TSPLRO', 'STR_TIDA', 'STR_TIP1', ]
special_case = 'STR_' # LARGE NUMBER OF PRODUCTS WITH THIS CODE
cs = ['STR_S619']

def showem(code=None):
    if not code:
        code = 'STR_S619'
    results = Product.objects.filter(code=code, publish_status="DRAFT")
    p1 = results.first()
    p2 = results.last()
    print("NEW CODES: ", get_new_codes(p1))

    if results.count() > 1:
        for r in results:
            print(r.title)
            # print(r.id)
            print("Code: ", r.code)
            print("imis code: ", r.imis_code)
            print(r.content)
            # print(r.content.event.parent)
    #		print(r.content.id)
    #		print(r.content.description)
            print(r.content.content_type)
            print(r.publish_status)
            if r.content.content_type == 'EVENT':
                print(r.content.event.event_type) # == 'COURSE' FOR streaming
                # print("EVENT PARENT: ", r.content.event.parent)
            print()

def valid(p1, p2):
    # 0. check that the ids are different on the two products
    # 1. no field value may be null or empty string or None
    # 2. code must start with STR_ but must not be only 'STR_'
    # 3. the products must have titles and they must be different
    # 4. both products must have product.content.event and the
    # product.content.event.event_type must be "COURSE" (STREAMING)
    id_bool = code = title = event = False
    id_bool = p1.id and p2.id and p1.id != p2.id
    code = p1.code and p2.code and p1.code != 'STR_' and p2.code != 'STR_'
    code = code and p1.code.find('STR_') > -1 and p2.code.find('STR_') > -1
    title = p1.title and p2.title and p1.title != p2.title
    try:
        event = p1.content.event and p2.content.event
        p1et = p1.content.event.event_type
        p2et = p2.content.event.event_type
        event = event and p1et == 'COURSE' and p2et == 'COURSE'
    except:
        event = False

    return id_bool and code and title and event

def get_new_codes(p1):
    if p1:
        code_parts = p1.code.split("_")
        code_parts1 = code_parts.copy()
        code_parts2 = code_parts.copy()
        code_parts1.insert(1, "NPC1")
        code_parts2.insert(1, "NPC2")

        new_code1 = "_".join(code_parts1)
        new_code2 = "_".join(code_parts2)
        return (new_code1, new_code2)
    else:
        print("NO PRODUCT\n")

def fix_doops(codes_set=None, no_valid=False):
    # verify that there are exactly two products
    fixed = 0
    soo=set()
    soo.add("STR_")
    cs = codes_set.difference(soo)
    for c in cs:
        results = Product.objects.filter(code=c, publish_status="DRAFT")
        if results.count() == 2:
            p1 = results.first()
            p2 = results.last()
            if valid(p1, p2) or no_valid:
                new_codes = get_new_codes(p1)
                p1.code = new_codes[0]
                p2.code = new_codes[1]
                p1.imis_code = new_codes[0]
                p2.imis_code = new_codes[1]
                p1.save()
                p2.save()
                # publish content or event?
                if p1.content.content_type == "EVENT" and p2.content.content_type == "EVENT":
                    p1.content.event.publish()
                    p2.content.event.publish()
                    p1.content.event.solr_publish()
                    p2.content.event.solr_publish()
                    fixed+=1
                    print("%s set(s) of dupes corrected" % fixed)
                else:
                    p1.content.publish()
                    p2.content.publish()
                    p1.content.solr_publish()
                    p2.content.solr_publish()
                    fixed+=1
                    print("%s set(s) of dupes corrected" % fixed)
            else:
                print("--------------------------------")
                print("INVALID SET OF DUPES: ", (p1, p2))
                print("--------------------------------")
        else:
            print("++++++++++++++++++++++++++++++")
            print("RESULTS SET HAS %s records" % results.count())
            print("++++++++++++++++++++++++++++++")
    print("********")
    print("ALL DONE: %s TOTAL DUPE SETS CORRECTED" % fixed)
    print("********")

def fix46():
    code = "STR_"
    results = Product.objects.filter(code=code, publish_status="DRAFT")
    i = 0
    for p in results:
        i+=1
        new_code = code + "NONE_" + str(i)
        print("new code for %s is %s" % (i, new_code))
        p.code = new_code
        p.imis_code = new_code
        p.save()
        p.content.event.publish()
        p.content.event.solr_publish()

def fix_singles(codes=None, non_singles=None):
    fixed = 0
    codes = codes.difference(non_singles)
    for c in codes:
        try:
            p1 = Product.objects.get(code=c, publish_status="DRAFT")
            print("p1 code is ", p1.code)
            print("p1 imis code is ", p1.imis_code)
            p1.imis_code = p1.code
            p1.save()
            p1.content.event.publish()
            p1.content.event.solr_publish()
            fixed+=1
            print("changed %s draft records" % fixed)
        except:
            print("CODE NOT GETTING FIXED: ", c)
    print("********")
    print("ALL DONE: %s TOTAL DUPE SETS CORRECTED" % fixed)
    print("********")

def get_non_singles(codes):
    s = set()
    for c in codes:
        ps = Product.objects.filter(code=c, publish_status="DRAFT")
        if ps.count() == 2:
            s.add(ps.first().code)
    return s

def make_full_dupes(non_singles, dupe_codes):
    return non_singles.union(dupe_codes)

# list of manual writes to imis
manual = [
'STR_NPC2_S439',
'STR_NPC2_S547',
'STR_NPC2_S538',
'STR_TCCB',
'STR_NPC2_S465',
'STR_NPC1_S540',
'STR_NPC1_S596',
'STR_NPC1_S589',
'STR_NPC2_S499',
'STR_NPC1_S627',
'STR_NPC1_S418',
'STR_NPC1_S514',
'STR_NPC2_S541',
'STR_NPC2_S511',
'STR_NPC1_S547',
'STR_NPC2_S615',
'STR_NPC1_S414',
'STR_NPC2_S512',
'STR_NPC1_S533',
'STR_NPC1_S559'
]

def get_man(manual=None):
    for m in manual:
        p=Product.objects.get(code=m, publish_status="PUBLISHED")
        print("PRODUCT CODE: ", p.code)
        print("PRODUCT TITLE: ", p.title)
        print("PRODUCT DESCTIPTION: ", p.description)
        print()

def change_codes():
    cs=Course.objects.filter(code__startswith="LRN")
    for c in cs:
        print("old code: ", c.code)
        new_code = c.code.replace("LRN", "LRN_NPC")
        print("new code: ", new_code)
        c.code = new_code
        c.save()
        c.product.code = new_code
        c.product.imis_code = new_code
        c.product.save()
        c.save()
        print("Done: ", c)
        print("************************************")

def add_taxo(sessions=None):
    tz = pytz.timezone("US/Central")
    jan1st2018 = tz.localize(datetime(2018, 1, 1), is_dst=None)
    # window of reporting availibility
    first_date_available = tz.localize(datetime(2018, 6, 1), is_dst=None)
    last_date_available = tz.localize(datetime(2021, 6, 1), is_dst=None)
    format_tag_type = TagType.objects.get(title__contains="Format")
    # od_tags = Tag.objects.filter(Q(title__contains="Sessions & Discussions") | Q(title__contains="Deep Dives"))
    od_tags = Tag.objects.filter(code__in=TAG_CODES)
    od_parent_landing_master = LandingPageMasterContent.objects.get(id=9027802)
    on_demand_template = "events/newtheme/ondemand/course-details.html"

    if not sessions:
        sessions = Event.objects.filter(
            contenttagtype__tags__in=od_tags,
            begin_time__gte=jan1st2018,
            parent__content_live__code=NATIONAL_CONFERENCE_PROGRAM[0],
            publish_status='DRAFT'
            ).distinct("id")

    for sesh in sessions:
        course = Course.objects.filter(title=sesh.title, code__contains=sesh.code)
        if course.count() == 1:
            course = course.first()
            topic_tags_list = list(sesh.taxo_topics.all())
            course.taxo_topics.set(topic_tags_list)
            print("sesh: ", sesh)
            print("course: ", course)
            print()

def see_taxo(sessions=None):
    tz = pytz.timezone("US/Central")
    jan1st2018 = tz.localize(datetime(2018, 1, 1), is_dst=None)
    # window of reporting availibility
    first_date_available = tz.localize(datetime(2018, 6, 1), is_dst=None)
    last_date_available = tz.localize(datetime(2021, 6, 1), is_dst=None)
    format_tag_type = TagType.objects.get(title__contains="Format")
    # od_tags = Tag.objects.filter(Q(title__contains="Sessions & Discussions") | Q(title__contains="Deep Dives"))
    od_tags = Tag.objects.filter(code__in=TAG_CODES)
    od_parent_landing_master = LandingPageMasterContent.objects.get(id=9027802)
    on_demand_template = "events/newtheme/ondemand/course-details.html"

    if not sessions:
        sessions = Event.objects.filter(
            contenttagtype__tags__in=od_tags,
            begin_time__gte=jan1st2018,
            parent__content_live__code=NATIONAL_CONFERENCE_PROGRAM[0],
            publish_status='DRAFT'
            ).distinct("id")
    for sesh in sessions:
        c = Course.objects.filter(title=sesh.title, code__contains=sesh.code)
        if c.count() == 1:
            c=c.first()
            print(c)
            print(c.taxo_topics.all())
            print()

# *********************************************************
# ***** MAKE CODE/IMIS CODE SAME FOR SALES PRODUCTS *****
# *********************************************************

"""
*** NEW :
15 character max code on imis_code - because sales products in imis

if product is missing a title, set title to imis code
"""


# psps = print sales products
def psps():
    print("**********************************************")
    print("DIGITAL PUBLICATION CODES AND TITLES IN DJANGO")
    print("**********************************************")
    ps=Product.objects.filter(product_type='DIGITAL_PUBLICATION', publish_status='DRAFT')
    for p in ps:
        print("      Title: ", p.content.title)
        print("  Django id: ",p.id)
        print("Django code: ",p.code)
        print("  Imis code: ",p.imis_code)
        print()

# dctoic = django code to imis code
def dctoic():
    ps_d=Product.objects.filter(product_type='DIGITAL_PUBLICATION', publish_status='DRAFT').distinct("code")
    print("*********** DISTINCT ***************")
    for p in ps_d:
        new_code = get_new_code(p)
        process_codes(p, new_code)
        print(p.code)
        print(p.imis_code)
        print()
    ps=Product.objects.filter(product_type='DIGITAL_PUBLICATION', publish_status='DRAFT')
    ps_dupes = ps.difference(ps_d)
    print("\n*********** DUPES ***************")
    for p in ps_dupes:
        dupes = Product.objects.filter(code=p.code, publish_status='DRAFT')
        for i,d in enumerate(dupes):
            new_code = get_new_code(d) + "_" + str(i)
            process_codes(d, new_code)
            print(d.code)
            print(d.imis_code)
            print()

def get_new_code(p):
    code = p.code
    if code.find("PASQ") == 0:
        code = code.replace("PASQ", "PAS_Q")
        process_codes(p, code)
    elif code.find("PASM") == 0:
        code = code.replace("PASM", "PAS_M")
        process_codes(p, code)
    elif code.find("EIP") == 0:
        code = "PAS_" + code
        process_codes(p, code)
    elif code.find("BOOK_P") == 0:
        code = code.replace("BOOK_P", "PAS_")
        process_codes(p, code)
    elif code.find("BOOK_A") == 0:
        code = code.replace("BOOK", "PAS")
        process_codes(p, code)
    elif code.find("ZP") == 0:
        pass
    else:
        print("\n***************")
        print("CODE DOES NOT MEET ANY CONDITIONS")
        print("product: ", p)
        print("code: ", code)
        print("***************\n")
    return code


"""
CHANGE DJANGO CODE:
PASQ, PASM = PAS_Q, PAS_M
EIP -  PREPEND PAS_
BOOK_P = REPLACE WITH PAS_
THEN WRITE TO IMIS CODE
"""
def digital_publication_code_rehab():
    ps = Product.objects.filter(product_type='DIGITAL_PUBLICATION', publish_status='DRAFT')
    print("\n*********** START digital publication code rehab ***************")
    for p in ps:
        code = p.code
        if code.find("PASQ") == 0:
            code = code.replace("PASQ", "PAS_Q")
            process_codes(p, code)
        elif code.find("PASM") == 0:
            code = code.replace("PASM", "PAS_M")
            process_codes(p, code)
        elif code.find("EIP") == 0:
            code = "PAS_" + code
            process_codes(p, code)
        elif code.find("BOOK_P") == 0:
            code = code.replace("BOOK_P", "PAS_")
            process_codes(p, code)
        elif code.find("BOOK_A") == 0:
            code = code.replace("BOOK", "PAS")
            process_codes(p, code)
        elif code.find("ZP") == 0:
            pass
        else:
            print("\n***************")
            print("CODE DOES NOT MEET ANY CONDITIONS")
            print("product: ", p)
            print("code: ", code)
            print("***************\n")

def process_codes(p, code):
    p.code = code
    p.imis_code = code
    if not p.title:
        p.title = p.imis_code
    print(p.code)
    print(p.imis_code)
    print()
    p.save()
    p.content.publish()

dpcr = digital_publication_code_rehab

def code_cleanup_title(ps=None):
    if not ps:
        ps = Product.objects.filter(product_type='DIGITAL_PUBLICATION', publish_status='DRAFT')
    for p in ps:
        if p.code.find("_D") > 0:
            new_code = p.code.replace("_D", "")
            p.code = new_code
            p.imis_code = new_code
        if not p.title:
            p.title = p.imis_code
        print(p.code)
        print(p.imis_code)
        print(p.title)
        print()
        p.save()
        p.content.publish()

cct = code_cleanup_title

def cleanup_title_again(ps=None):
    if not ps:
        ps = Product.objects.filter(product_type='DIGITAL_PUBLICATION', publish_status='DRAFT')
    for p in ps:
        if not p.title or (p.title == p.imis_code):
            p.title = p.content.title
        print(p.code)
        print(p.imis_code)
        print(p.title)
        print()
        p.save()
        p.content.publish()

cta = cleanup_title_again

# *********************************************************
# ***** MAKE APA LEARN COURSES FROM ON-DEMAND COURSES *****
# *********************************************************

ON_DEMAND_ID_LIST = [
# for Kerry
9126606,
9126530,
9126460,
9126621
]
# real final groups:
# '9111224',
# '9111225',
# '9111226',
# '9111313',
# '9111314',
# '9111315',
# '9111316',
# '9111317',
# '9111319',

# final group:
# '9112838',
# '9027090',
# '3028198',
# '9002710',
# '9154940',
# '9154941',
# '9109264',
# '9130408',

# original test:
# '9126482',
# '9126428',
# '9126490',
# '9126339'
# final test of three on staging:
# '9152450',
# '9152449',
# '9152453'

# NPC17
# '9126482',
# '9126428',
# '9126490',
# '9126441',
# '9126456',
# '9126531',
# '9126393',
# '9126505',
# '9126446',
# '9126553',
# '9126542',
# '9126360',
# '9126335',
# '9126491',
# '9126485',
# '9126541',
# '9126506',
# '9126411',
# '9126310',
# '9126420',
# '9126337',
# '9126443',
# '9126365',
# '9126522',
# '9126527',
# '9126303',
# '9126445',
# '9126489',
# '9126480',
# '9126548',
# '9126390',
# '9126334',
# '9126395',
# '9126345',
# '9126304',
# '9126458',
# '9126406',
# '9126364',
# '9126450',
# '9126501',
# '9126328',
# '9126477',
# '9126326',
# '9126417',
# '9126354',
# '9126301',
# '9126375',
# '9126377',
# '9126630',
# '9126405',
# '9126457',
# '9126537',
# '9126538',
# '9126517',
# '9126455',
# '9126557',
# '9126322',
# '9126324',
# '9126368',
# '9126494',
# '9126415',
# '9126421',
# '9126430',
# '9126338',
# '9126346',
# '9126496',
# '9126507',
# '9126431',
# '9126478',
# '9126481',
# '9126387',
# '9126373',
# '9126378',
# '9126447',
# '9126331',
# '9126426',
# '9126521',
# '9126533',
# '9126376',
# '9126410',
# '9126424',
# '9126429',
# '9126386',
# '9126584',
# '9126547',
# '9126532',
# '9126412',
# '9126347',
# '9126625',
# '9126384',
# '9126471',
# '9126359',
# '9126434',
# '9126561',
# '9126495',
# '9126344',
# '9126413',
# '9126590',
# '9126436',
# '9126508',
# '9126563',
# '9126472',
# '9126336',
# '9126560',
# '9126333',
# '9126546',
# '9126372',
# '9126484',
# '9126409',
# '9126528',
# '9126498',
# '9126340',
# '9126513',
# '9126385',
# '9126529',
# '9126473',
# '9126382',
# '9126451',
# '9126486',
# '9126363',
# '9126479',
# '9126349',
# '9126398',
# '9126369',
# '9126454',
# '9126397',
# '9126416',
# '9126329',
# '9126307',
# '9126452',
# '9126543',
# '9126325',
# '9126401',
# '9126350',
# '9126465',
# '9126524',
# '9126453',
# '9126544',
# '9126305',
# '9126500',
# '9126419',
# '9126404',
# '9126351',
# '9126520',
# '9126523',
# '9126361',
# '9126499',
# '9126315',
# '9126352',
# '9126362',
# '9126442',
# '9126422',
# '9126355',
# '9126503',
# '9126464',
# '9126432',
# '9126371',
# '9126423',
# '9126463',
# '9126462',
# '9126466',
# '9126468',

# # NPC18
# '9152378',
# '9152424',
# '9152457',
# '9152398',
# '9152474',
# '9152384',
# '9152238',
# '9152309',
# '9152335',
# '9152445',
# '9152336',
# '9152306',
# '9152287',
# '9152400',
# '9152295',
# '9152240',
# '9152392',
# '9152395',
# '9152452',
# '9152316',
# '9152420',
# '9152314',
# '9152468',
# '9152307',
# '9152387',
# '9152254',
# '9152412',
# '9152461',
# '9152257',
# '9152469',
# '9152472',
# '9152410',
# '9152340',
# '9152397',
# '9152459',
# '9152466',
# '9152245',
# '9152367',
# '9152329',
# '9152389',
# '9152442',
# '9152404',
# '9152323',
# '9152437',
# '9152381',
# '9152304',
# '9152281',
# '9152358',
# '9152330',
# '9152417',
# '9152463',
# '9152236',
# '9152299',
# '9152242',
# '9152421',
# '9152305',
# '9152264',
# '9152253',
# '9152416',
# '9152427',
# '9152364',
# '9152377',
# '9152454',
# '9152290',
# '9152250',
# '9152394',
# '9152428',
# '9152279',
# '9152344',
# '9152422',
# '9152244',
# '9152361',
# '9152465',
# '9152446',
# '9152369',
# '9152308',
# '9152320',
# '9152312',
# '9152359',
# '9152288',
# '9152278',
# '9152337',
# '9152368',
# '9152450',
# '9152274',
# '9152371',
# '9152366',
# '9152403',
# '9152272',
# '9152239',
# '9152415',
# '9152414',
# '9152391',
# '9152436',
# '9152409',
# '9152248',
# '9152385',
# '9152441',
# '9152283',
# '9152449',
# '9152348',
# '9152432',
# '9152406',
# '9152322',
# '9152370',
# '9152277',
# '9152343',
# '9152382',
# '9152319',
# '9152439',
# '9152379',
# '9152301',
# '9152317',
# '9152373',
# '9152426',
# '9152401',
# '9152481',
# '9152324',
# '9152443',
# '9152347',
# '9152413',
# '9152345',
# '9152234',
# '9152241',
# '9152339',
# '9152332',
# '9152429',
# '9152354',
# '9152405',
# '9152246',
# '9152334',
# '9152431',
# '9152407',
# '9152321',
# '9152243',
# '9152296',
# '9152269',
# '9152363',
# '9152485',
# '9152346',
# '9152294',
# '9152448',
# '9152291',
# '9152350',
# '9152267',
# '9152433',
# '9152418',
# '9152302',
# '9152271',
# '9152298',
# '9152286',
# '9152488',
# '9152423',
# '9152251',
# '9152311',
# '9152276',
# '9152447',
# '9152365',
# '9152399',
# '9152462',
# '9152388',
# '9152360',
# '9152376',
# '9152258',
# '9152438',
# '9152455',
# '9152425',
# '9152470',
# '9152310',
# '9152487',
# '9152352',
# '9152480',
# '9152482',
# '9152517',
# '9152520',
# '9152521',
# '9152522',
# '9152523',
# '9152525',
# '9152526',
# '9152528',
# '9152529',
# '9152531',
# '9152534',
# '9152536',
# '9152540',
# '9152539',
# '9152458',
# '9154175',
# '9154174',
# '9154176',
# '9154177',
# '9154626',

# ]

# most recent conversion group is from planning & advocacy conference
# and does not have codes -- adding codes to draft:
def add_codes(es=None):
    if not es:
        es=Activity.objects.filter(master_id__in=ON_DEMAND_ID_LIST, publish_status="DRAFT")
    for i,e in enumerate(es):
        e.code="PAC18" + str(i).zfill(4)
        e.save()

# CURRENT CODE FORMAT: “LRN_18xxxx”
def get_or_convert_code(on_demand_code):
    if on_demand_code:
        if on_demand_code.find("LRN_NPC") > -1:
            return on_demand_code.replace("NPC", "")
        elif on_demand_code.find("LRN") > -1:
            return on_demand_code
        else:
            return "LRN_" + on_demand_code
    else:
        return "LRN_" + "NO_CODE_" + str(int(random.random()*9999))

# mlfod = make learn from on-demand
def mlfod(courses=None):
    tz = pytz.timezone("US/Central")
    first_date_available = tz.localize(datetime(2018, 7, 1), is_dst=None)
    last_date_available = tz.localize(datetime(2021, 9, 5), is_dst=None)
    launch_date = tz.localize(datetime(2018, 9, 4), is_dst=None)

    learn_parent_landing_master = LandingPageMasterContent.objects.filter(
        content_live__url="/learn/purchase/").first()

    if settings.ENVIRONMENT_NAME == 'PROD':
        # Only prod has the page with this id:
        # learn_parent_landing_master = LandingPageMasterContent.objects.get(id=9154303)
        begin_time = launch_date
    else:
        begin_time = first_date_available

    # get the courses that will be copied into new Learn records
    # next year convert this to a query for conference activities
    # (on-demand courses will not be involved)
    if not courses:
        courses = Course.objects.filter(
            master_id__in=ON_DEMAND_ID_LIST,
            publish_status='DRAFT'
            ).distinct("id")

    # for NPC19 only this: ??
    if not courses:
        courses = Activity.objects.filter(
            master_id__in=ON_DEMAND_ID_LIST,
            publish_status='DRAFT'
            ).distinct("id")

    for sesh in courses:
        # in this case the sesh code has already been converted for the newer NPC18 batch
        # but not for the earlier on-demand
        print("sesh is ", sesh)
        course_code = get_or_convert_code(sesh.code)
        print("course_code is ", course_code)
        if settings.ENVIRONMENT_NAME == 'PROD':
            status = "H"
        else:
            status = "A"

        learn, created = LearnCourse.objects.get_or_create(
            status=status,
            publish_status="DRAFT",
            text=sesh.text,
            description=sesh.description,
            title=sesh.title,
            featured_image=sesh.featured_image,
            thumbnail=sesh.thumbnail,
            is_free=False,
            is_online=True,
            code=course_code,
            begin_time=begin_time,
            end_time=last_date_available,
            timezone=tz.zone,
            cm_status=sesh.cm_status,
            cm_approved=sesh.cm_approved,
            cm_law_approved=sesh.cm_law_approved,
            cm_ethics_approved=sesh.cm_ethics_approved,
            parent_landing_master=learn_parent_landing_master,
            keywords="webinar, webinars, on demand, on-demand, apa learn, npc, npc18, npc2018, npc 18, npc 2018",
            )
        print("new learn course is: ", learn.title)
        contact_roles = sesh.contactrole.all()
        for cr in contact_roles:
            learn_contact_role, created = ContactRole.objects.get_or_create(
                content=learn,
                contact=cr.contact,
                role_type=cr.role_type,
                sort_number=cr.sort_number,
                confirmed=cr.confirmed,
                invitation_sent=cr.invitation_sent,
                special_status=cr.special_status,
                permission_content=cr.permission_content,
                permission_av=cr.permission_av,
                content_rating=cr.content_rating,
                first_name=cr.first_name,
                middle_name=cr.middle_name,
                last_name=cr.last_name,
                bio=cr.bio,
                email=cr.email,
                phone=cr.phone,
                company=cr.company,
                cell_phone=cr.cell_phone
                )

        apa_org=Organization.objects.get(user__username=119523)
        apa_provider_list = [p for p in learn.contactrole.all() if p.role_type == "PROVIDER" and p.contact == apa_org]

        if not apa_provider_list:
            apa_provider, created = ContactRole.objects.get_or_create(
                content=learn,
                contact=apa_org,
                role_type="PROVIDER",
                sort_number=99,
                )

        content_tag_types = sesh.contenttagtype.all()

        for ctt in content_tag_types:
            tag_type = ctt.tag_type

            if tag_type.title != "Format":
                tags_list = [t for t in ctt.tags.all()]
            else:
                tags = Tag.objects.filter(tag_type=tag_type).filter(
                    Q(code="FORMAT_APA_LEARN") | Q(code="FORMAT_ON_DEMAND_EDUCATION"))
                tags_list = list(tags)

            learn_content_tag_type, created = ContentTagType.objects.get_or_create(
                content=learn,
                tag_type=tag_type,
                )
            learn_content_tag_type.tags.clear()
            learn_content_tag_type.tags.set(tags_list)

        if not content_tag_types.filter(tag_type__title="Format"):
            format_tag_type = TagType.objects.get(title="Format")
            tags = Tag.objects.filter(tag_type=format_tag_type).filter(
                Q(code="FORMAT_APA_LEARN") | Q(code="FORMAT_ON_DEMAND_EDUCATION"))
            tags_list = list(tags)
            learn_content_tag_type, created = ContentTagType.objects.get_or_create(
                content=learn,
                tag_type=format_tag_type,
                )
            learn_content_tag_type.tags.clear()
            learn_content_tag_type.tags.set(tags_list)

        ContentRelationship.objects.get_or_create(
            content=sesh,
            content_master_related=learn.master,
            relationship="LEARN_COURSE")

        topic_tags_list = list(sesh.taxo_topics.all())
        learn.taxo_topics.set(topic_tags_list)

        # LOOK AT ANDY'S EXAMPLE LEARN RECORD FOR GUIDANCE (9153085)
        product, created = Product.objects.get_or_create(
            content=learn,
            title=sesh.title,
            description=sesh.description,
            code=course_code,
            product_type="LEARN_COURSE",
            imis_code=course_code,
            gl_account="470130-AF6301",
            )

        option_titles = [
            "1-4 Learners Pricing",
            "5-25 Learners Group Pricing",
            "26+ Learners Group Pricing"
        ]
        option_codes = ["INDIVIDUAL", "GROUP525", "GROUP26PLUS"]
        for i in range(0,3):
            ProductOption.objects.get_or_create(
                product=product,
                title=option_titles[i],
                code=option_codes[i],
                status='A',
                sort_number=i)

        # titles = ["Member", "Member Group License", "Member Group License",
        # 			"Non-Member", "Non-Member Group License", "Non-Member Group License"]
        titles = ["Member", "Nonmember", "Member Group License",
                    "Nonmember Group License", "Member Group License", "Nonmember Group License"]
        member_group = Group.objects.get(name="member")
        cm = learn.cm_approved
        discounts = [1.0, 1.0, .85, .85, .75, .75]
        mins = [1, 1, 5, 5, 26, 26]
        maxes = [4, 4, 25, 25, 100, 100]
        option_codes = ["INDIVIDUAL", "INDIVIDUAL", "GROUP525", "GROUP525", "GROUP26PLUS", "GROUP26PLUS"]

        """
        Member pricing per quantity (licenses) and price code:
        1-4: $20 * cm 			MEMBER_1_TO_4
        5-25: $20 * cm * .85	MEMBER_5_TO_25
        26+:  $20 * cm * .75	MEMBER_26_AND_UP

        NonMember pricing per quantity (licenses):

        1-4: $40 * cm 			NONMEMBER_1_TO_4
        5-25: $40 * cm * .85	NONMEMBER_5_TO_25
        26+:  $40 * cm * .75	NONMEMBER_26_AND_UP
        """

        for i in range(0,len(titles)):
            title = titles[i]
            # base_price = 20 if i<3 else 40
            base_price = 20 if i%2 == 0 else 40
            discount = discounts[i]
            option_code = option_codes[i]
            price = Decimal(base_price * float(cm) * discount)
            priority = i
            min_quantity = mins[i]
            max_quantity = maxes[i]
            # print("title is ", title)
            # print("base_price is ", base_price)
            # print("discount is ", discount)
            # print("price is ", price)
            # print("priority is ", priority)
            # print("min_quantity is ", min_quantity)
            # print("max_quantity is ", max_quantity)

            learn_product_price, created = ProductPrice.objects.get_or_create(
                title=title,
                product=product,
                price=price,
                priority=priority,
                begin_time=begin_time,
                include_search_results=True,
                min_quantity=min_quantity,
                max_quantity=max_quantity,
                option_code=option_code
                )

            learn_product_price.required_groups.clear()

            if i%2 == 0:
                learn_product_price.required_groups.set([member_group])
        print()
    published_learn = learn.publish()
    solr_response = published_learn.solr_publish()
    print("solr publish response is ", solr_response)
    print("at end learn course publish status is ", learn.publish_status)
    print()
    return learn


def delete_learn(courses):
    if not courses:
        courses = Course.objects.filter(
            master_id__in=ON_DEMAND_ID_LIST,
            publish_status='DRAFT'
            ).distinct("id")

    lurnz = LearnCourse.objects.filter(related_from__in=courses)
    for el in lurnz:
        print(el)
    # UNCOMMENT WHEN READY
    # lurnz.delete()

# FIX FORMAT TAGS -- MAKE SURE ALL LEARN COURSES HAVE ON-DEMAND AND APA LEARN
# vafots = view all format tags
def vafota():
    lcs =LearnCourse.objects.all()
    ftt=TagType.objects.filter(title="Format").first()
    for lc in lcs:
        print(lc)
        print([ctt.tags.all() for ctt in ContentTagType.objects.filter(content=lc, tag_type=ftt)])
        print()

# vabrofots = view all broken format tags
def vabrofota():
    lcs =LearnCourse.objects.all()
    ftt=TagType.objects.filter(title="Format").first()
    lt = Tag.objects.filter(code="FORMAT_APA_LEARN").first()
    odt = Tag.objects.filter(code="FORMAT_ON_DEMAND_EDUCATION").first()
    tlist = [lt, odt]
    for lc in lcs:
        ctt=ContentTagType.objects.filter(content=lc, tag_type=ftt).first()
        if not ctt:
            print(lc)
            print("has no format content tag type\n")
        elif not set(ctt.tags.all()) == set(tlist):
            print(lc)
            print(ctt.tags.all())
            print()

# fifota = fix format tags
def fifota():
    lcs =LearnCourse.objects.all()
    ftt=TagType.objects.filter(title="Format").first()
    lt = Tag.objects.filter(code="FORMAT_APA_LEARN").first()
    odt = Tag.objects.filter(code="FORMAT_ON_DEMAND_EDUCATION").first()
    tlist = [lt, odt]
    for lc in lcs:
        ctt=ContentTagType.objects.filter(content=lc, tag_type=ftt).first()
        if ctt:
            if not set(ctt.tags.all()) == set(tlist):
                ctt.tags.set(tlist)
                print("fixed tags for %s\n" % (lc))
        else:
            new_ctt, created = ContentTagType.objects.get_or_create(content=lc, tag_type=ftt)
            new_ctt.tags.set(tlist)
            print("created format tag type for %s\n" % (lc))

# apa learn post go live script
# nood = no on demand (take on demand off line)
"""
Each product price associated with each event will need to be end dated and
have the visibility status be set to 'inactive.'

Every product associated with each event will need to have the
visibility status set to 'inactive.'
"""
def nood():
    now = django.timezone.now()
    # ods = Course.objects.all()
    ods=Course.objects.filter(product__isnull=False)
    for od in ods:
        product = od.product
        if product:
            product.status = "I"
            # product.save()
            prices = product.prices.all()
            for p in prices:
                p.end_time = now
                p.status = "I"
                # p.save()
            # product.publish()
            # product.solr_publish()

"""
Can be done right away on Stg and Prod

Update Parent Landing Page on all APA Learn records to: Master ID: 9022738

Update keywords:

all:
webinar, webinars, on demand, on-demand, apa learn

npc also get:
npc, npc18, npc2018, npc 18, npc 2018

active ethics also get:
ethics

active law also get:
law
"""

# ulrs = update learn records
def ulrs():
    parent_landing_master = LandingPageMasterContent.objects.get(id=9022738)
    # query for all then just use logic tests
    lrs = LearnCourse.objects.filter(
        publish_status="DRAFT")

    for lr in lrs:
        lr.parent_landing_master = parent_landing_master
        lr.keywords = "webinar, webinars, on demand, on-demand, apa learn, "
        if lr.code.find("LRN_18") >= 0:
            lr.keywords = lr.keywords + "npc, npc18, npc2018, npc 18, npc 2018, "
        if lr.cm_ethics_approved:
            lr.keywords = lr.keywords + "ethics, "
        if lr.cm_law_approved:
            lr.keywords = lr.keywords + "law, "
        print(lr)
        print(lr.parent_landing_master)
        print(lr.keywords)
        print()
        lr.save()
        lr.publish()
        lr.solr_publish()


# update learn course price priorities = ulcpp
def ulcpp(lcs=None):
    option_codes = ["INDIVIDUAL", "INDIVIDUAL", "INDIVIDUAL", "GROUP525",
    "GROUP525", "GROUP26PLUS", "GROUP26PLUS"]
    titles = ["APA Staff", "Member", "Nonmember", "Member Group License",
                "Nonmember Group License", "Member Group License", "Nonmember Group License"]
    statuses = ['H' if i == 0 else 'A' for i in range(0,7)]

    if not lcs:
        lcs = LearnCourse.objects.filter(status='A')

    for lc in lcs:
        print("START ***************************\n")
        product = getattr(lc, "product", None)

        if product:
            original_prices = product.prices.all()
            print("original_prices are ", original_prices.count())
            print()
            changed_prices = set()

            for i in range(0,len(titles)):
                title = titles[i]
                option_code = option_codes[i]
                priority = i
                status = statuses[i]

                if i == 0:
                    try:
                        # print("in try")
                        # print("title is ", title)
                        # print("option_code is ", option_code)
                        # print("status is ", status)
                        # print("product is ", lc.product)
                        draft_product_price = pp = ProductPrice.objects.get(title=title,option_code=option_code,
                            status=status, price=Decimal('0.00'), publish_status="DRAFT", product=lc.product)
                        # print("draft_product_price is ", draft_product_price)
                        changed_prices.add(draft_product_price.id)
                        # print("changed_prices in here is ", changed_prices)
                    except:
                        draft_product_price = None
                    try:
                        published_product_price = pp = ProductPrice.objects.get(title=title,option_code=option_code,
                            status=status, price=Decimal('0.00'), publish_status="PUBLISHED", product=lc.product)
                        changed_prices.add(published_product_price.id)
                    except:
                        published_product_price = None
                else:
                    # we're only checking price on the staff price above
                    try:
                        draft_product_price = pp = ProductPrice.objects.get(title=title,option_code=option_code,
                            status=status, publish_status="DRAFT", product=lc.product)
                        changed_prices.add(draft_product_price.id)
                    except:
                        draft_product_price = None
                    try:
                        published_product_price = pp = ProductPrice.objects.get(title=title,option_code=option_code,
                            status=status, publish_status="PUBLISHED", product=lc.product)
                        changed_prices.add(published_product_price.id)
                    except:
                        published_product_price = None

                if draft_product_price:
                    print("\ndraft_product_price is ", draft_product_price)
                    print("old priority is ", draft_product_price.priority)
                    draft_product_price.priority = i
                    print("new priority is ", draft_product_price.priority)
                    draft_product_price.save()

                if published_product_price:
                    published_product_price.priority = i
                    published_product_price.save()

            print("changed_prices is ", changed_prices)
            fake_prices = original_prices.exclude(id__in=changed_prices)
            print("fake_prices are ", fake_prices)

            for i, fp in enumerate(fake_prices):
                print("\nfake price is ", fp)
                print("old priority is ", fp.priority)
                fp.priority = i+7
                print("new priority is ", fp.priority)
                fp.save()
            print("END ***************************\n")


# **************************
# CREATE ContentRelationship records tying NPC18 live sessions
# to APA Learn Courses -- Currently they only exist for
# on_demand to APA Learn ...(?)
# **************************

# mcrs = make content relationship records
def mcrs(activities=None):
    # to pass a queryset of limited number of activities
    # you must query Content
    npc18_draft = Event.objects.get(
        master_id=9135594, code="EVENT_18CONF",
        publish_status="DRAFT")
    print("npc18 is ", npc18_draft)

    if not activities:
        npc18_activities = Content.objects.filter(
            parent=npc18_draft.master,
            publish_status="DRAFT",
            event__event_type="ACTIVITY"
            ).distinct("id")
    else:
        npc18_activities = activities.filter(
            parent=npc18_draft.master,
            publish_status="DRAFT",
            event__event_type="ACTIVITY"
            ).distinct("id")
    print("we have %s activities" % (npc18_activities.count()))
    print()
    i = 0
    for sesh in npc18_activities:
        try:
            i+=1
            print("\n^^^^^^^       START       ^^^^^^^^^")
            print("activity %s is %s" % (i,sesh))
            learn_draft = LearnCourse.objects.get(publish_status="DRAFT",
                title=sesh.title)
            print("***************************************************")
            print("the corresponding learn course is ", learn_draft)
            print("***************************************************")
            # cr = None
            cr, created = ContentRelationship.objects.get_or_create(
                content=sesh,
                content_master_related=learn_draft.master,
                relationship="LEARN_COURSE",
                publish_status="DRAFT")
            if cr:
                print("we have a ContentRelationship record.")
                sesh.publish()
            print()
        except Exception as e:
            print("---------------------------------------------------")
            print("Exception: ", e)
            print("---------------------------------------------------")
            print()

# *****************************************************
# CONVERT MULTI-EVENT ACTIVITIES INTO APA LEARN COURSES
# *****************************************************

# COURSE CREATE SETUP:
# 1. SET THESE GLOBALS in wcw_api_utils.py
# 2. SET THE THREE DATES BELOW IN mlfs()

# MULTI_EVENT_CODE = "21CONF"

# CONFERENCE_PREFIX = "NPC"
# TWO_DIGIT_YEAR = "21"
# LEARN_SESSION_DIGIT = "1"
# COURSE_CREATE_PREFIX = CONFERENCE_PREFIX + TWO_DIGIT_YEAR + LEARN_SESSION_DIGIT
# LEARN_COURSE_PREFIX = "LRN_" + COURSE_CREATE_PREFIX

# RUN_TIME_CM = Decimal('0.75')
# RUN_TIME = timedelta(0,45*60)

def get_learn_code(activity_code):
    """
    CURRENT CODING CONVENTIONS: POL – Policy & Advocacy Conference (formerly PAC):
     2-digit year (20)
     1-digit session type code (1)
     3-digit unique session number (001 through 999)
     (PAC20: all activites that start with POL201 should be included in course create)
    """
    if activity_code.find(COURSE_CREATE_PREFIX) > -1:
        return activity_code.replace(COURSE_CREATE_PREFIX, LEARN_COURSE_PREFIX)
    else:
        raise Exception("INCORRECT Activity CODE: %s" % activity_code)

def make_learn_course_info(activities=None):
    # FOR TESTING ONLY:
    # MULTI_EVENT_CODE = "EVENT_POL16"
    # multi_event=EventMulti.objects.get(
    #     master_id=9103288,
    #     publish_status="DRAFT")

    # PUT BACK AFTER TESTING:
    multi_event=EventMulti.objects.get(
        publish_status="DRAFT",
        code=MULTI_EVENT_CODE)
    tag = Tag.objects.get(code="APA_LEARN")

    if activities:
        activities = activities.filter(
            parent=multi_event.master,
            publish_status='DRAFT'#,
            # contenttagtype__tags=tag
            ).distinct("id")
    else:
        activities = Activity.objects.filter(
            parent=multi_event.master,
            publish_status='DRAFT'#,
            # contenttagtype__tags=tag
            ).distinct("id")

    for sesh in activities:
        print("sesh is ", sesh)
        lci, created = LearnCourseInfo.objects.get_or_create(activity=sesh)

        if settings.ENVIRONMENT_NAME == 'PROD':
            template_id = LMS_TEMPLATE_ID_PROD
        else:
            template_id = LMS_TEMPLATE_ID_STAGING
        lci.run_time = RUN_TIME
        lci.run_time_cm = RUN_TIME_CM
        lci.lms_template = template_id
        lci.save()
mlci=make_learn_course_info

# MAKE THE UPDATES TO THIS TO ADD A NEW PRICE ASSOCIATED WITH NEW WEB GROUP "PROF_DEV_ACCESS"
# BUT DO NOT RUN UNTIL RAN SAYS THE GROUP IS CREATED
def mlfs(activities=None):
    """
    mlfs = make learn from npc sessions
    :param activities: NPC Activities to be converted to Learn Courses
    :return learn: Last Learn Course Created
    """
    tz = pytz.timezone("US/Central")
    first_date_available = tz.localize(datetime(2021, 4, 27), is_dst=None)
    last_date_available = tz.localize(datetime(2022, 5, 16), is_dst=None)
    launch_date = tz.localize(datetime(2021, 5, 17), is_dst=None)
    learn_parent_landing_master = LandingPageMasterContent.objects.filter(
        content_live__url="/events/").first()
    # FOR TESTING ONLY:
    # MULTI_EVENT_CODE = "EVENT_POL16"
    # multi_event=EventMulti.objects.get(
    #     master_id=9103288,
    #     publish_status="DRAFT")
    learn = None
    # PUT BACK AFTER TESTING:
    multi_event=EventMulti.objects.get(
        publish_status="DRAFT",
        code=MULTI_EVENT_CODE)
    tag = Tag.objects.get(code="APA_LEARN")

    if settings.ENVIRONMENT_NAME == 'PROD':
        begin_time = launch_date
    else:
        begin_time = first_date_available

    if activities:
        activities = activities.filter(
            parent=multi_event.master,
            publish_status='DRAFT'#,
            # contenttagtype__tags=tag
            ).distinct("id")
    else:
        activities = Activity.objects.filter(
            parent=multi_event.master,
            publish_status='DRAFT'#,
            # contenttagtype__tags=tag
            ).distinct("id")

    for sesh in activities:
        print("sesh is ", sesh)
        course_code = get_learn_code(sesh.code)
        print("course_code is ", course_code)
        if settings.ENVIRONMENT_NAME == 'PROD':
            status = "H"
        else:
            status = "A"
        lci = LearnCourseInfo.objects.values("run_time_cm").get(activity=sesh)
        rt = lci["run_time_cm"]
        zero = Decimal('0.00')
        cm = rt if sesh.cm_approved and sesh.cm_approved > 0 else zero
        law = rt if sesh.cm_law_approved and sesh.cm_law_approved > 0 else zero
        ethics = rt if sesh.cm_ethics_approved and sesh.cm_ethics_approved > 0 else zero

        learn, created = LearnCourse.objects.get_or_create(
            status=status,
            publish_status="DRAFT",
            text=sesh.text,
            description=sesh.description,
            title=sesh.title,
            learning_objectives=sesh.learning_objectives,
            featured_image=sesh.featured_image,
            thumbnail=sesh.thumbnail,
            is_free=False,
            is_online=True,
            code=course_code,
            begin_time=begin_time,
            end_time=last_date_available,
            timezone=tz.zone,
            cm_status=sesh.cm_status,
            cm_approved=cm,
            cm_law_approved=law,
            cm_ethics_approved=ethics,
            parent_landing_master=learn_parent_landing_master,
            keywords="webinar, webinars, on demand, on-demand, apa learn, npc, npc21, npc2021, npc 21, npc 2021, virtual conference, live online courses"
            )
        print("new learn course is: ", learn.title)
        sesh.course_info_from.learncourse = learn
        sesh.course_info_from.save()
        contact_roles = sesh.contactrole.all()
        for cr in contact_roles:
            learn_contact_role, created = ContactRole.objects.get_or_create(
                content=learn,
                contact=cr.contact,
                role_type=cr.role_type,
                sort_number=cr.sort_number,
                confirmed=cr.confirmed,
                invitation_sent=cr.invitation_sent,
                special_status=cr.special_status,
                permission_content=cr.permission_content,
                permission_av=cr.permission_av,
                content_rating=cr.content_rating,
                first_name=cr.first_name,
                middle_name=cr.middle_name,
                last_name=cr.last_name,
                bio=cr.bio,
                email=cr.email,
                phone=cr.phone,
                company=cr.company,
                cell_phone=cr.cell_phone
                )

        apa_org=Organization.objects.get(user__username=119523)
        apa_provider_list = [p for p in learn.contactrole.all() if p.role_type == "PROVIDER" and p.contact == apa_org]

        if not apa_provider_list:
            apa_provider, created = ContactRole.objects.get_or_create(
                content=learn,
                contact=apa_org,
                role_type="PROVIDER",
                sort_number=99,
                )

        content_tag_types = sesh.contenttagtype.all()

        for ctt in content_tag_types:
            tag_type = ctt.tag_type

            if tag_type.title != "Format":
                tags_list = [t for t in ctt.tags.all()]
            else:
                tags = Tag.objects.filter(tag_type=tag_type).filter(
                    Q(code="FORMAT_APA_LEARN") | Q(code="FORMAT_ON_DEMAND_EDUCATION"))
                tags_list = list(tags)

            learn_content_tag_type, created = ContentTagType.objects.get_or_create(
                content=learn,
                tag_type=tag_type,
                )
            learn_content_tag_type.tags.clear()
            learn_content_tag_type.tags.set(tags_list)

        if not content_tag_types.filter(tag_type__title="Format"):
            format_tag_type = TagType.objects.get(title="Format")
            tags = Tag.objects.filter(tag_type=format_tag_type).filter(
                Q(code="FORMAT_APA_LEARN") | Q(code="FORMAT_ON_DEMAND_EDUCATION"))
            tags_list = list(tags)
            learn_content_tag_type, created = ContentTagType.objects.get_or_create(
                content=learn,
                tag_type=format_tag_type,
                )
            learn_content_tag_type.tags.clear()
            learn_content_tag_type.tags.set(tags_list)

        ContentRelationship.objects.get_or_create(
            content=sesh,
            content_master_related=learn.master,
            relationship="LEARN_COURSE")

        topic_tags_list = list(sesh.taxo_topics.all())
        learn.taxo_topics.set(topic_tags_list)

        product, created = Product.objects.get_or_create(
            content=learn,
            status=status,
            title=sesh.title,
            description=sesh.description,
            code=course_code,
            product_type="LEARN_COURSE",
            imis_code=course_code,
            gl_account="470130-AF6301",
            )

        option_titles = [
            "1-4 Learners Pricing",
            "5-25 Learners Group Pricing",
            "26+ Learners Group Pricing"
        ]
        option_codes = ["INDIVIDUAL", "GROUP525", "GROUP26PLUS"]
        for i in range(0,3):
            ProductOption.objects.get_or_create(
                product=product,
                title=option_titles[i],
                code=option_codes[i],
                status='A',
                sort_number=i)

        # FLAGGED FOR REFACTORING: LEARN COURSE PUSH - NEED TO TEST THESE CHANGES for new PROF_DEV_ACCESS price
        titles = ["APA Staff", "Professional development subscription",
                    "Member", "Nonmember",
                    "Member Group License", "Nonmember Group License",
                    "Member Group License", "Nonmember Group License"]
        member_group = Group.objects.get(name="member")
        staff_group = Group.objects.get(name="staff")
        pds_group = Group.objects.get(name="PROF_DEV_ACCESS")
        cm = learn.cm_approved
        discounts = [0, 0, 1.0, 1.0, .85, .85, .75, .75]
        mins = [1, 1, 1, 1, 5, 5, 26, 26]
        maxes = [1, 1, 4, 4, 25, 25, 100, 100]
        option_codes = ["INDIVIDUAL", "INDIVIDUAL", "INDIVIDUAL", "INDIVIDUAL", "GROUP525",
                        "GROUP525", "GROUP26PLUS", "GROUP26PLUS"]

        """
        Member pricing per quantity (licenses) and price code:
        1-4: $20 * cm 			MEMBER_1_TO_4
        5-25: $20 * cm * .85	MEMBER_5_TO_25
        26+:  $20 * cm * .75	MEMBER_26_AND_UP

        NonMember pricing per quantity (licenses):

        1-4: $40 * cm 			NONMEMBER_1_TO_4
        5-25: $40 * cm * .85	NONMEMBER_5_TO_25
        26+:  $40 * cm * .75	NONMEMBER_26_AND_UP
        """

        for i in range(0, len(titles)):
            title = titles[i]
            base_price = 20 if i % 2 == 0 else 40
            discount = discounts[i]
            option_code = option_codes[i]
            price = Decimal(base_price * float(cm) * discount)
            priority = i
            min_quantity = mins[i]
            max_quantity = maxes[i]
            # print("title is ", title)
            # print("base_price is ", base_price)
            # print("discount is ", discount)
            # print("price is ", price)
            # print("priority is ", priority)
            # print("min_quantity is ", min_quantity)
            # print("max_quantity is ", max_quantity)

            learn_product_price, created = ProductPrice.objects.get_or_create(
                title=title,
                status='H' if i == 0 else 'A',#status,
                product=product,
                price=price,
                priority=priority,
                begin_time=begin_time,
                include_search_results=True,
                min_quantity=min_quantity,
                max_quantity=max_quantity,
                option_code=option_code
                )

            learn_product_price.required_groups.clear()
            if i % 2 == 0 and i > 1:
                learn_product_price.required_groups.set([member_group])
            elif i == 0:
                learn_product_price.required_groups.set([staff_group])
            elif i == 1:
                learn_product_price.required_groups.set([pds_group])

        print()
        # SHOULDN'T THIS LAST BLOCK BE INDENTED HERE???
        # WHEN RUNNING ON PROD DON'T PUBLISH -- PUBLISH LATER?
        # published_learn = learn.publish()
        # solr_response = published_learn.solr_publish()
        # print("solr publish response is ", solr_response)
        # print("at end learn course publish status is ", learn.publish_status)
        # print()
    return learn

# ***************************
# ADD NPC19 COURSES TO BUNDLE
# ***************************
def add_courses_to_bundle(courses=None, test=True):
    """
    Script to add all NPC APA Learn courses
    to the NPC Collection Bundle  (for NPC19 this was 9182252)
    :param courses:
    :return: None
    """
    i = 0

    if not courses and not test:
        courses = LearnCourse.objects.filter(
            code__contains="LRN_H20",
            publish_status="DRAFT"
        )
    # bundle doesn't exist on local yet so...
    # test_bundle = LearnCourseBundle.objects.get(
    #     code='LRN_NPCI_COL', publish_status="DRAFT")
    # THE ACTUAL CODE FOR NPC DIGITAL THAT WAS USED: LRN_NPC20_COL
    bundle = LearnCourseBundle.objects.get(
        code='LRN_NPCH20_COL', publish_status="DRAFT")

    for course in courses:
        ContentRelationship.objects.get_or_create(
            content=bundle,
            # content=test_bundle,
            content_master_related=course.master,
            relationship="LEARN_COURSE"
        )
        i += 1
        print("%s done" % i)

    bundle.publish()
    bundle.solr_publish()
    # test_bundle.publish()
    # test_bundle.solr_publish()
acs=add_courses_to_bundle


def bump_begin_time_on_courses(courses=None):
    """
    Script to move begin time ahead for all NPC19 Learn Courses
    :param courses:
    :return: None
    """
    i = 0
    month = 11
    day = 1

    if not courses:
        courses = LearnCourse.objects.filter(
            code__contains="LRN_19",
            publish_status="DRAFT"
        )
    for course in courses:
        old_begin = course.begin_time
        new_begin = old_begin.replace(month=month, day=day)
        course.begin_time = new_begin
        i += 1
        course.save()
        course.publish()
        course.solr_publish()
        print("%s done" % i)
bbt=bump_begin_time_on_courses


def unhide_conf_courses(courses=None, code_id=None):
    """
    Script to unhide all Learn Courses for a given conference
    :param courses:
    :return: None
    """
    i = 0

    if not courses:
        courses = LearnCourse.objects.filter(
            code__contains=code_id,
            publish_status="DRAFT"
        ).exclude(status='A')
    for course in courses:
        print("COURSE: ", course.code)
        course.status = 'A'
        i += 1
        course.save()
        course.publish()
        course.solr_publish()
        print("%s done" % i)
uncc=unhide_conf_courses
# FOR NPC AT HOME LIKE THIS:
CURRENT_CONF_CODE_ID = "LRN_H20"
# uncc(None, CURRENT_CONF_CODE_ID)

def hide_staff_prices(courses=None):
    """
    Script to hide all staff prices on NPC19 Learn Courses
    (set their priority to 0 in separate script)
    :param courses:
    :return: None
    """
    i = 0

    if not courses:
        courses = LearnCourse.objects.filter(
            code__contains="LRN_19",
            publish_status="DRAFT"
        )
    # get all Product Prices with 'staff' group
    # on NPC19 Course Products. change status to 'H'
    products = Product.objects.filter(
        content__in=courses
    )
    # only with 'staff' group
    stf_grp = Group.objects.get(name='staff')
    product_prices = ProductPrice.objects.filter(
        product__in=products,
        required_groups=stf_grp
    ).exclude(status='H')
    for pp in product_prices:
        pp.status = 'H'
        i += 1
        pp.save()
        pp.product.save()
        pp.product.content.save()
        published_record = pp.product.content.publish()
        published_record.solr_publish()
        print("%s done" % i)
hsp=hide_staff_prices

# 0. query for all relevant records (draft and published)
# 1. make staff price priority 10
# 2. add 1 to all other price priorities
# 3. make staff price priority 0
# 4. save (don't publish)

# set staff learn course price priorities = sspp
# IDEMPOTENT as long as no changes occur outside of this process
def sspp(lcs=None):
    i = 0

    if not lcs:
        lcs = LearnCourse.objects.filter(code__contains="LRN_19")

    count = float(lcs.count())

    for lc in lcs:
        print("START ***************************\n")
        product = getattr(lc, "product", None)
        if product:
            stf_grp = Group.objects.get(name='staff')
            prices = product.prices.all()
            # test for highest priority, if > 6 do nothing or if staff price is already 0 do nothing
            print("num prices total: ", prices.count())
            print("OLD PRIORITIES-----------")
            for pp in prices:
                print(pp)
                print(pp.required_groups.all())
                print(pp.priority)
            try:
                staff_price = prices.get(required_groups=stf_grp)
            except:
                staff_price = None
            # IF STAFF PRICE IS ALREADY 0 DO NOTHING
            if staff_price and staff_price.priority > 0:
                staff_price.priority = 10
                staff_price.save()
                prices_no_staff = prices.exclude(id=staff_price.id).order_by("-priority")
                print(prices_no_staff)
                print("num prices minus staff: ", prices_no_staff.count())

                for pp in prices_no_staff:
                    pp.priority += 1
                    pp.save()

                staff_price.priority = 0
                print("staff price priority: ", staff_price.priority)
                print("NEW PRIORITIES non staff-----------")
                for pp in prices_no_staff:
                    print(pp)
                    print(pp.required_groups.all())
                    print(pp.priority)
                staff_price.save()
                product.save()
                lc.save()
                i += 1
                print("%s%% done." % ((i/count) * 100.0))
        print("END ***************************\n")


def add_zero_price_to_npc19_courses(courses=None):
    """
    Script to add a zero dollar price to all NPC19 Learn Courses
    available to NPC19 attendees
    :param courses:
    :return: None
    """
    i = 0
    if not courses:
        courses = LearnCourse.objects.filter(
            code__contains="LRN_19",
            publish_status="DRAFT"
        )
    for course in courses:
        product = course.product
        product_option = ProductOption.objects.get(
            product=product,
            code="INDIVIDUAL",
        )
        print("product option is ", product_option)
        npc19_group = Group.objects.get(name='19CONF')
        tz = pytz.timezone("US/Central")
        sep_01_2019 = tz.localize(datetime(year=2019, month=9, day=1))

        new_zero_dollar_price, created = ProductPrice.objects.get_or_create(
            product=product,
            price=Decimal("0.00"),
            title="NPC19 Attendee",
            min_quantity=Decimal("1.00"),
            max_quantity=Decimal("1.00"),
            begin_time=sep_01_2019,
            priority=100,
            option_code="INDIVIDUAL"
        )
        new_zero_dollar_price.required_groups.clear()
        new_zero_dollar_price.required_groups.set([npc19_group])

        prices_to_bump_priorities = product.prices.filter(priority__gt=0).filter(priority__lt=10)
        for pri in prices_to_bump_priorities:
            pri.priority += 1
            pri.save()
        new_zero_dollar_price.priority = 1
        new_zero_dollar_price.save()
        product.save()
        i += 1
        if created:
            course.save()
            course.publish()
            course.solr_publish()
        print("%s done" % i)
azp=add_zero_price_to_npc19_courses

# FIX EN DASH IN DJANGO PRODUCT GL CODES ************************
# problem: i was given bad gl_account value (with en-dash) that was used in script
# to create the learn courses
# THESE ARE THE OFFENDING PRODUCTS:
def convert_en_dash_to_hyphen():
    from store.models import Product
    prods=Product.objects.filter(gl_account__contains=chr(8211))
    print(prods.count())
    for p in prods:
        print(p)
        print(p.publish_status)
        p.gl_account = p.gl_account.replace(chr(8211), chr(45))
        p.save()
ceth=convert_en_dash_to_hyphen


# pdsp = professional development subscription price
def add_professional_development_subscription_price_to_all_learn_courses(courses):
    """
    Script to add a zero dollar professional_development_subscription price to ALL APA Learn Courses
    available to NPC21 attendees?
    Must explicitly pass None to run the full version
    """
    i = 0
    if not courses:
        courses = LearnCourse.objects.filter(
            publish_status="DRAFT",
         ).exclude(Q(product__isnull=True) | Q(product__prices__isnull=True) | Q(product__prices__option_code__isnull=True))
    count = courses.count()
    for course in courses:
        print("START ------------------------ Learn Course is: ")
        print(course.master)
        product = course.product
        product_option = ProductOption.objects.get(
            product=product,
            code="INDIVIDUAL",
        )
        print("product option is ", product_option)
        npc21_access_group = Group.objects.get(name='NPC21-access')
        tz = pytz.timezone("US/Central")
        # sep_01_2019 = tz.localize(datetime(year=2019, month=9, day=1))

        new_zero_dollar_price, created = ProductPrice.objects.get_or_create(
            product=product,
            price=Decimal("0.00"),
            title="Professional development subscription",
            min_quantity=Decimal("1.00"),
            max_quantity=Decimal("1.00"),
            # begin_time=sep_01_2019,
            priority=100,
            option_code="INDIVIDUAL"
        )
        new_zero_dollar_price.required_groups.clear()
        new_zero_dollar_price.required_groups.set([npc21_access_group])

        # MAKE NEW PRICE 0 PRIORITY BUMP ALL OTHERS UP 1
        prices_to_bump_priorities = product.prices.filter(priority__lt=50)
        for pri in prices_to_bump_priorities:
            pri.priority += 1
            pri.save()
        new_zero_dollar_price.priority = 0
        new_zero_dollar_price.save()
        product.save()
        i += 1
        if created:
            course.save()
            course.publish()
            course.solr_publish()
        print("%s done of %s" % (i, count))
pdsp=add_professional_development_subscription_price_to_all_learn_courses

def make_trial_prof_dev_subscription_price_inactive(courses):
    """
    Script to make trial professional_development_subscription price inactive on ALL APA Learn Courses
    Must explicitly pass None to run the full version
    """
    i = 0
    if not courses:
        courses = LearnCourse.objects.filter(
            publish_status="DRAFT",
         ).exclude(Q(product__isnull=True) | Q(product__prices__isnull=True) | Q(product__prices__option_code__isnull=True))
    count = courses.count()
    for course in courses:
        print("START ------------------------ Learn Course is: ")
        print(course.master)
        product = course.product
        # change this to query for those prices tied to npc21-access group
        trial_price_queryset = product.prices.filter(
            publish_status="DRAFT",
            # title="Professional development subscription",
            required_groups__name="NPC21-access",
            price=Decimal("0.00"))
        if trial_price_queryset:
            for trial_price in trial_price_queryset:
                print("trial prof dev sub price is ", trial_price)
                trial_price.status = 'I'
                trial_price.save()
            product.save()
            course.save()
            course.publish()
            course.solr_publish()
        i += 1
        print("%s done of %s" % (i, count), "\n")

def reset_npc_activity_templates(activities=None, conf_code=None):
    """
    Script to switch NPC templates from conference template
    events/newtheme/conference-details.html to
    standard activity template used in CM search
    events/newtheme/event-details.html
    """
    i = 0
    npc = Event.objects.get(code=conf_code, publish_status="DRAFT")

    if not activities:
        activities = NationalConferenceActivity.objects.filter(
            parent = npc.master,
            publish_status="DRAFT"
        )
    for a in activities:
        print("ACTIVITY: ", a.code)
        print("Activity template before: ")
        print(a.template)
        a.template = "events/newtheme/event-details.html"
        i += 1
        a.save()
        published_instance = a.publish()
        published_instance.solr_publish()
        print("Activity template after: ")
        print(published_instance.template)
        print("%s done" % i)
rnpcat=reset_npc_activity_templates
# rnpcat(None, NATIONAL_CONFERENCE_NEXT[0])

def add_prof_dev_access_prices(courses):
    """
    Script to add a zero dollar professional_development_subscription price to ALL APA Learn Courses
    Must explicitly pass None to run the full version
    This is for the regular subsciption (the above script was for the trial subscription)
    """
    i = 0
    if not courses:
        courses = LearnCourse.objects.filter(
            publish_status="DRAFT",
         ).exclude(Q(product__isnull=True) | Q(product__prices__isnull=True) | Q(product__prices__option_code__isnull=True))
    count = courses.count()
    for course in courses:
        print("START ------------------------ Learn Course is: ")
        print(course.master)
        product = course.product
        product_option = ProductOption.objects.get(
            product=product,
            code="INDIVIDUAL",
        )
        print("product option is ", product_option)
        # npc21_access_group = Group.objects.get(name='NPC21-access')
        prof_dev_access_group = Group.objects.get(name='PROF_DEV_ACCESS')
        tz = pytz.timezone("US/Central")
        # sep_01_2019 = tz.localize(datetime(year=2019, month=9, day=1))

        new_zero_dollar_price, created = ProductPrice.objects.get_or_create(
            product=product,
            price=Decimal("0.00"),
            # "full" as opposed to "trial"
            title="APA Learning Subscription (Pilot)",
            min_quantity=Decimal("1.00"),
            max_quantity=Decimal("1.00"),
            # begin_time=sep_01_2019,
            priority=100,
            option_code="INDIVIDUAL"
        )
        new_zero_dollar_price.required_groups.clear()
        new_zero_dollar_price.required_groups.set([prof_dev_access_group])

        # MAKE NEW PRICE 0 PRIORITY BUMP ALL OTHERS UP 1
        prices_to_bump_priorities = product.prices.filter(priority__lt=50)
        for pri in prices_to_bump_priorities:
            pri.priority += 1
            pri.save()
        new_zero_dollar_price.priority = 0
        new_zero_dollar_price.save()
        product.save()
        i += 1
        if created:
            course.save()
            course.publish()
            course.solr_publish()
        print("%s done of %s" % (i, count))


# for now run on staging only -- may need this for prod later
def change_prof_dev_access_prices(courses):
    """
    Script to change title of a zero dollar professional_development_subscription price on ALL APA Learn Courses
    """
    i = 0
    old_title = "Professional development subscription (full)"
    new_title = "APA Learning Subscription (Pilot)"
    if not courses:
        courses = LearnCourse.objects.filter(
            publish_status="DRAFT",
         ).exclude(Q(product__isnull=True) | Q(product__prices__isnull=True) | Q(product__prices__option_code__isnull=True))
    count = courses.count()
    for course in courses:
        print("START ------------------------ Learn Course is: ")
        print(course.master)
        product = course.product
        prof_dev_access_prices = ProductPrice.objects.filter(
            product=product,
            price=Decimal("0.00"),
            title=old_title,
            required_groups__name="PROF_DEV_ACCESS"
        )
        prof_dev_access_prices.update(title=new_title)
        product.save()
        i += 1
        course.save()
        course.publish()
        course.solr_publish()
        print("%s done of %s" % (i, count))
