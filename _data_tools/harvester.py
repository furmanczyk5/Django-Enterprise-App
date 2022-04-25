# CODE RELATED TO INTERFACING WITH CADMIUM
import pytz
import datetime
# import requests
import logging
from decimal import Decimal
from collections import OrderedDict
import csv
# from django.http import HttpResponse, JsonResponse

# from planning.settings import CADMIUMCD_API_KEY, CADMIUMCD_REGISTRATION_TASK_ID

# from conference.models.settings import *
#from conference.utils import HARVESTER_ROOM_TITLE_TO_CODE
from conference.models.cadmium_mapping import CadmiumMapping, SyncMapping, MAPPING_TYPES
from conference.models.cadmium_sync import CadmiumSync
from conference.models.microsite import Microsite
from events.models import Activity, Event
# from myapa.models.constants import ROLE_TYPES
from pages.models import LandingPageMasterContent
# from store.models import Purchase
# from content.models import TaxoTopicTag

logger = logging.getLogger(__name__)

# *******************************
# TAXONOMY TO SEARCH MAPPING ****
# *******************************

# Run this code in the shell to generate a spreadsheet showing how
# taxonomy tags map to search topic tags

# ttts=TaxoTopicTag.objects.exclude(status='I').order_by('related__title')

def vee(queryset):
    fieldnames = OrderedDict([
        ("title", "Taxonomy Tag Title"),
        ("related__title", "Related Search Topics"),
    ])
    fp = open('/Users/tjohnson/code/taxotosearch.csv', 'w')
    writer = csv.DictWriter(fp, fieldnames=fieldnames)
    writer.writerow(fieldnames)
    for tag in queryset.values(*fieldnames):
        writer.writerow(tag)

# *******************************
# CREATE ROOM TAGS ****
# *******************************

# First update the room mapping dictionary then
# run this code in the shell to generate room tags for current conference

def create_npc_room_tags():
	rd = HARVESTER_ROOM_TITLE_TO_CODE

	rtt = TagType.objects.get(code="ROOM")

	for i in rd.items():
		Tag.objects.get_or_create(title=i[0], code=i[1], status="A", tag_type=rtt)

# NOW ON WRAPPER
# # *************************************
# # BULK PUSH COMPLETED REGISTRATION TASK
# # *************************************
#
# def push_completed_reg(speaker_purchases=None):
#     current_npc_code = "19CONF"
#     # get contacts who have external_id and registered for current conference
#     if not speaker_purchases:
#         speaker_purchases = Purchase.objects.filter(product__code=current_npc_code
#             ).exclude(contact__external_id__isnull=True)
#     # for each speaker hit cadmium endpoint
#     count = speaker_purchases.count()
#     i = 0
#     for sp in speaker_purchases:
#         contact = sp.contact
#
#         if contact.external_id:
#             i+=1
#             api_key = CADMIUMCD_API_KEY
#             task_id = CADMIUMCD_REGISTRATION_TASK_ID
#             # url = 'http://www.conferenceharvester.com/conferenceportal3/webservices/HarvesterJsonAPI.asp'
#             url = HARVESTER_API_URL
#             data = {}
#             username = contact.user.username
#             external_id = contact.external_id
#
#             params = {
#             'APIKey': api_key,
#             'Method': 'completeTask',
#             'PresenterID': external_id,
#             'TaskID': task_id}
#
#             r1=requests.post(url, params=params, json=data)
#
#             params = {
#             'APIKey': api_key,
#             'Method': 'presenterReg',
#             'PresenterID': external_id,
#             # 'PresenterRegID': None, # if needed, could be primary key of Attendee model
#             'PresenterRegCode': username,
#             'PresenterRegFlag': 1}
#
#             r2=requests.post(url, params=params, json=data)
#
#             message = "%s NPC19 SPEAKER REGISTRAION" % (username)
#             logger.error(message,
#                 exc_info=True,
#                 extra={
#                     'complete_task_response': r1,
#                     'presenter_reg_response': r2,
#                     'username': username,
#                     'external_id': external_id
#                 })
#             print("%s of %s done." % (i, count))


# *************************************************
# EXPORT PAC EVENTS TO POSTGRES FROM SPREADSHEET
# *************************************************

# hex character is big endian marker
COLUMNS_OLD = ['\ufeffSession Number (Code)', 'Session Type ', 'Title/Event Name',
           'Date', 'Start', 'End', 'Timezone', 'Room/Location', 'Description',
           'Short Description ', 'CM? - Y/N', 'Learning  Outcome 1',
           'Learning  Outcome 2', 'Learning  Outcome 3', 'CM Hours',
           'Session Outline', 'CM approved?', 'Parent Landing Page ', 'Template',
           'Visibility Status', 'Parent', 'Keywords']


COLUMNS = ['Master Django ID', 'Session Number (Code)', 'Title/Event Name',
               'Date', 'Start', 'End', 'Timezone', 'Room/Location', 'Description',
               'Short Description ', 'CM? - Y/N', 'Learning  Outcome 1',
               'Learning  Outcome 2', 'Learning  Outcome 3', 'CM Hours',
               'Session Outline', 'CM approved?', 'Parent Landing Page ', 'Template',
               'Visibility Status', 'Parent', 'Keywords']

FIELDS = ['', 'code', 'title',
          'date', 'start', 'end', 'timezone', 'location', 'text',
          'description', 'has_cm', 'learning_objectives_1',
          'learning_objectives_2', 'learning_objectives_3', 'cm_approved',
          'session_outline', 'has_cm_approved', 'parent_landing_master', 'template_title',
          'status', 'parent_id', 'keywords']

# pse_init = pac_special_export_init
def pse_init():
    # sstf = spreadsheet to fields
    sstf = {}
    for i in range(0,len(FIELDS)):
        sstf[COLUMNS[i]] = FIELDS[i]
    return sstf

def pac_special_export():
    csv_file_path = '/tmp/pac_events.csv'
    skip_header = False
    ctf = columns_to_fields = pse_init()

    # FOR ALL ACTIVITIES:
    template = 'events/newtheme/conference-details.html'

    parent_master_id = '9175090'
    pac = Event.objects.get(master_id=parent_master_id, publish_status="DRAFT")
    print("parent is ", pac)

    parent_landing_master_id = '9153014'
    lpmc = LandingPageMasterContent.objects.get(id=parent_landing_master_id)
    print("landing master is ", lpmc)

    timezone = 'US/Eastern'
    conference_timezone = pytz.timezone(timezone)
    keywords = 'PAC, PAC19, PAC 2019, Policy and Advocacy, Policy & Advocacy'
    cm_status = 'A'

    with open(csv_file_path) as csvfile:
        reader = csv.reader(csvfile)
        if skip_header:
            next(reader)
        for j,row in enumerate(reader):
            if j==0:
                print(row)
            d = {}
            if row[1].find("PAC") >= 0:# and j<8:
                for i in range(0,len(ctf)):
                    field = ctf[COLUMNS[i]]
                    d[field] = row[i]
                d.pop('')
                d = {k:(v if v != 'N/A' else None) for k,v in d.items()}
                print("\nSTART OF ROW------------------------------------")
                print("Attributes Dict for Row %s:" % j)
                print(d)

                # CONSTRUCT BEGIN_TIME/END_TIME
                date = d.get('date',None)
                start = d.get('start',None) or '12:00 AM'
                end = d.get('end',None) or '12:00 AM'
                print("date is ", date)
                print("start is ", start)
                print("end is ", end)
                begin_str = date + " " + start
                end_str = date + " " + end
                print("begin str is ", begin_str)
                print("end str is ", end_str)
                if begin_str:
                    begin = datetime.datetime.strptime(begin_str, '%A, %B %d, %Y %I:%M %p')
                    begin_time = conference_timezone.localize(begin)
                else:
                    begin_time = None
                if end_str:
                    end = datetime.datetime.strptime(end_str, '%A, %B %d, %Y %I:%M %p')
                    end_time = conference_timezone.localize(end)
                else:
                    end_time = None
                print("begin time is ", begin_time)
                print("end time is ", end_time)

                # BUILD LEARNING OBJECTIVES
                lo1 = d.get('learning_objectives_1',None)
                lo2 = d.get('learning_objectives_2', None)
                lo3 = d.get('learning_objectives_3', None)
                lo1_html = '<li>' + lo1 + '</li>' if lo1 else ''
                lo2_html = '<li>' + lo2 + '</li>' if lo2 else ''
                lo3_html = '<li>' + lo3 + '</li>' if lo3 else ''
                print("lo1 html is ", lo1_html)
                if lo1_html or lo2_html or lo3_html:
                    learning_objectives = '<ul>' + lo1_html + lo2_html + lo3_html + '</ul>'
                else:
                    learning_objectives = None
                print("learning objectives is ", learning_objectives)

                # DECIMALIZE CM VAL
                cm_approved = d.get('cm_approved', None)
                print("cm approved BEFORE is ", cm_approved)
                if cm_approved and cm_approved != 'N/A':
                    cm_approved = Decimal(cm_approved)
                else:
                    cm_approved = None
                print("cm_approved AFTER is ", cm_approved)
                print("DONE WITH ROW -------------------------------------\n")

                # GET STATUS
                status_string = d.get('date', None)
                status = 'A' if status_string == 'Active' else 'H'

                activity, created = Activity.objects.get_or_create(
                    publish_status='DRAFT',
                    code=d.get('code', None))
                activity.title=d.get('title', None)
                activity.begin_time=begin_time
                activity.end_time=end_time
                activity.timezone=timezone
                activity.location=d.get('location', None)
                activity.text=d.get('text', None)
                activity.description=d.get('description', None)
                activity.learning_objectives=learning_objectives
                activity.cm_status=cm_status
                activity.cm_approved=cm_approved
                activity.parent_landing_master=lpmc
                activity.template=template
                activity.status=status
                activity.parent=pac.master
                activity.keywords=keywords

                activity.save()
                activity.publish()
                activity.solr_publish()

pse=pac_special_export


# if __name__ == "__main__":
#     pac_special_export()


# **************************************************
# SETUP CADMIUM MAPPING IN POSTGRES FROM SPREADSHEET
# **************************************************

COLUMNS = [
    'Mapping Type', 'FROM Field or Datum', 'TO Field or Datum',
    'Microsite Identifier', 'Cadmium Event Key', 'Registration Task ID',
    # DO NOT PUT ENDPOINT IN HERE
    # 'API URL',
    'Activity Landing Page Master ID', 'Track Tag Type Code',
    'Activity Tag Type Code', 'Division Tag Type Code', 'NPC Category Tag Type Code'
]

# THIS IS A MAPPING TO THE MAPPING FIELDS
FIELDS = [
    'mapping_type', 'from_string', 'to_string',
    'url_path_stem', 'cadmium_event_key', 'registration_task_id',
    # 'endpoint',
    'parent_landing_master_id', 'track_tag_type_code',
    'activity_tag_type_code', 'division_tag_type_code', 'npc_category_tag_type_code',
]

# (ROW 0 is column headings) will hold sync data only, no mapping
ROW_1 = [
    '', '', '',
    'water', 'event_key_water19', 'REG_TASK_ID_WATER19',
    '9152660', 'EVENTS_WATER_TRACK_19',
    'EVENTS_WATER_ACTIVITY_19', 'EVENTS_WATER_DIVISION_19', 'EVENTS_WATER_CATEGORY_19'
]

ROW_2 = [
    'Harvester Speaker Role to Django Role Type', 'Speaker', 'SPEAKER',
    '','','',
    '','',
    '','',''
]

ROW_3 = [
    'Harvester Speaker Role to Django Role Type', 'Mobile Workshop Coordinator', 'MOBILEWORKSHOPCOORDINATOR',
    '','','',
    '','',
    '','',''
]

# I will create cadmium_mapping.csv from Kerry's spreadsheet
default_spreadsheet_path = '/tmp/default_spreadsheet.csv'
# real_spreadsheet_path = '/tmp/cadmium_mapping.csv'
real_spreadsheet_path = '/tmp/mappingspreadsheet.csv'


def make_default_spreadsheet():
    default_spreadsheet_csv_path = default_spreadsheet_path
    COLUMN1_VALS = []
    d = dict(MAPPING_TYPES)
    dv = d.values()
    l = list(dv)
    for s in l:
        for i in range(0,3):
            COLUMN1_VALS.append([s])
    with open(default_spreadsheet_csv_path, 'w') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(COLUMNS)
        writer.writerow(ROW_1)
        writer.writerow(ROW_2)
        writer.writerow(ROW_3)
        writer.writerows(COLUMN1_VALS)
mds=make_default_spreadsheet

def make_columns_to_fields_dict():
    # sstf = spreadsheet to fields
    sstf = {}
    for i in range(0,len(FIELDS)):
        sstf[COLUMNS[i]] = FIELDS[i]
    return sstf

def get_descriptions(code_description_tuple):
    md = dict(code_description_tuple)
    vals = md.values()
    descrips = list(vals)
    return descrips

def mapping_export():
    # csv_file_path = real_spreadsheet_path
    # set up the default spreadsheet to create a new test_sync with a few old/new mappings
    # csv_file_path = default_spreadsheet_path
    csv_file_path = real_spreadsheet_path
    skip_header = False
    ctf = make_columns_to_fields_dict()
    mapping_type_descrips = get_descriptions(MAPPING_TYPES)
    # role_type_descrips = get_descriptions(ROLE_TYPES)

    with open(csv_file_path) as csvfile:
        reader = csv.reader(csvfile)

        if skip_header:
            next(reader)
        sync = None

        for j,row in enumerate(reader):

            if len(row) < 11:
                row = row + ['' for i in range(0,11-len(row))]

            d = {}
            for i in range(0,len(ctf)):
                field = ctf[COLUMNS[i]]
                d[field] = row[i]
            d = {k:(v if v != 'N/A' else None) for k,v in d.items()}

            if j == 1:
                event_key = d.get('cadmium_event_key')
                sync, created = CadmiumSync.objects.get_or_create(cadmium_event_key=event_key)
                if sync:
                    microsite = Microsite.objects.get(url_path_stem=d.get("url_path_stem"))
                    sync.microsite = microsite
                    sync.registration_task_id = d.get("registration_task_id")
                    # sync.endpoint = d.get("endpoint")
                    sync.parent_landing_master_id = d.get("parent_landing_master_id") or None
                    sync.track_tag_type_code = d.get("track_tag_type_code")
                    sync.activity_tag_type_code = d.get("activity_tag_type_code")
                    sync.division_tag_type_code = d.get("division_tag_type_code")
                    sync.npc_category_tag_type_code = d.get("npc_category_tag_type_code")
                    sync.save()
            if sync:
                if d.get("mapping_type") and d.get("from_string") and d.get("to_string"):
                    tuple_index = mapping_type_descrips.index(d.get("mapping_type"))
                    mapping_type = MAPPING_TYPES[tuple_index][0]

                    # if mapping_type == 'HARVESTER_ROLE_TO_DJANGO_ROLE':
                    #     role_type_code_index = mapping_type_descrips.index(d.get("to_string"))
                    #     role_type = ROLE_TYPES[role_type_code_index][0]

                    mapping, created = CadmiumMapping.objects.get_or_create(
                        mapping_type=mapping_type,
                        from_string=d.get("from_string"),
                        to_string=d.get("to_string")
                    )
                    sync_mapping, created = SyncMapping.objects.get_or_create(sync=sync, mapping=mapping)

mex=mapping_export


# if __name__ == "__main__":
#     mex()

def make_activities_active(test=True):
    i = 1
    npc20 = Event.objects.get(code="20CONF", publish_status="DRAFT")
    acts = Activity.objects.filter(
        code__contains="NPC20", parent=npc20.master,
        publish_status="DRAFT")
    total = float(acts.count())
    if test:
        acts = acts[0:2]
        total = float(len(acts))
    for a in acts:
        a.status = 'A'
        a.save()
        published_obj = a.publish()
        published_obj.solr_publish()
        print(a)
        print("%s%% done." % ((i / total) * 100))
        i += 1
    print("------------------- ALL DONE -------------------")
maa=make_activities_active

# DISCONNECT SYNC FROM NPC20
# ERASE External_key on NPC20 Activities
# every Activity with this parent:
# <MasterContent: 9182407 | 2020 National Planning Conference>

from conference.models import NationalConferenceActivity

def disconnect_npc20_sync(test=True):

    # npc20_parent = MasterContent.objects.get(id=9182407)
    npc20_activities = NationalConferenceActivity.objects.filter(
        parent__content_live__code="20CONF")
    # npc20_draft = npc20_activities.filter(publish_status="DRAFT")
    # print("DRAFT count is ", npc20_draft.count())
    # npc20_pub = npc20_activities.filter(publish_status="PUBLISHED")
    # print("PUB count is ", npc20_draft.count())
    # print("FULL npc20 activity count is ", npc20_activities.count())
    # foo=[]
    for a in npc20_activities:
        if a.external_key:
            # foo.append((a.master_id,a.external_key))
            # print(a.master_id, " ", a.external_key)
            a.external_key = None
            a.save()
    # print(foo)
dis20=disconnect_npc20_sync
