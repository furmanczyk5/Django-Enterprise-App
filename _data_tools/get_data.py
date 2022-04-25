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
from django.contrib.auth.hashers import is_password_usable
from django.core.mail import send_mail

from datetime import timedelta

from django.db.models import Q

from cm.models import Log, Period, Claim, CMComment, ProviderRegistration, ProviderApplication
from content.models import MasterContent, TagType, Tag, ContentTagType, TaxoTopicTag
from pages import Page
from events.models import EventMulti, EventSingle, Activity, Course, NationalConferenceActivity, Event
from myapa.models.contact import Contact
from myapa.models.contact_role import ContactRole
from myapa.models.contact_relationship import ContactRelationship
from store.models import Purchase, Payment, Order, Product, ProductOption, ProductPrice

from planning.settings import ENVIRONMENT_NAME, RESTIFY_SERVER_ADDRESS
from urllib.request import urlopen
from urllib import parse
from decimal import * 
from xml.dom import minidom


from content.utils import generate_random_string

logger = logging.getLogger(__name__)

json_server='http://localhost:8081/dataimport';

###### TO IMPORT.....

###### FIRST START NODE SERVER ON LOCAL HOST FROM COMMAND PROMPT... e.g. :
# $cd [path_to_planning_project]/node_api
# $node restify_dataImport_server.js

###### THEN (FROM ANOTHER PROMPT), ACTIVIVATE DJANGO VIRTUAL ENVIRONMENT, START PYTHON, AND RUN IMPORTS FROM PYTHON COMMAND PROMPT... e.g.:
# $python manage.py shell 
# >>>from _data_tools import get_data
# >>>get_data.import_event_activities(27311)


def load_json(url):
    with urllib.request.urlopen(url) as response:
        json_string = response.readall().decode('utf-8')
    return json.loads(json_string)


def get_user_password_length():
    """
    writes to WebUser table whether the password length is too short
    """

    number_of_groups = 64

    for x in range(0, number_of_groups):
    
        if ENVIRONMENT_NAME == 'LOCAL':
            url = "https://staging.planning.org/xml/api/APA.api.decrypt.ashx?"
            contacts_list = load_json('http://localhost:8080/contact/' + str(x) + '/all')
            restify_url = "http://localhost:8080/"
        else:
            url = "https://planning.org/xml/api/APA.api.decrypt.ashx?"
            contacts_list = load_json('https://conference.planning.org:8080/contact/' + str(x) + '/all')
            restify_url = "https://conference.planning.org:8080/"
        for contact in contacts_list['data']:
            try:

                login = contact['Login']

                username = contact['WebUserID']

                contact_dict = {'AuthToken' : 'ericsatie', 'EncryptedString': login}

                url_query = urllib.parse.urlencode(contact_dict)
                url_string = url + url_query
                xml_str = urlopen(url_string).read()
                xmldoc = minidom.parseString(xml_str)


                password_object = xmldoc.getElementsByTagName('success') 
                password = password_object[0].childNodes[0].nodeValue

                is_password_short = 0

                if len(password) < 5:
                    is_password_short = 1

                payload = {'WebUserID': username,
                        'IsPasswordShort': is_password_short}

                r = requests.post(restify_url + "contact/passwordlength", data=payload)

                print('password length checked for user id: ' + str(username) )
            except Exception as e:

                print(str(e))
                print('issue with username: ' + username)

                continue

def import_national_conference():
    #id
    master_id = 3027311
    master, master_created = MasterContent.objects.get_or_create(id=master_id)

    try:
        national_conference = EventMulti.objects.get(master=master, publish_status='DRAFT')
    except EventMulti.DoesNotExist:
        national_conference = EventMulti(master=master, publish_status='DRAFT')
        pass
    national_conference.begin_time = '2015-04-18'
    national_conference.end_time = '2015-04-21'
    national_conference.title = '2015 APA National Planning Conference'
    
    national_conference.save()
    
    print("Imported 2015 National Conference")


def get_event_activities(event_id):
    """
    Imports activities for a particular event
    """
    activity_list = load_json(json_server + '/activity/list/' + str(event_id))['data']
    print("Importing {0} Activities...".format(len(activity_list)))

    try:
        conference_event_master = MasterContent.objects.get(id=3027311)
    except:
        conference_event_master = None

    for activity_listed in activity_list:
        activity_id = activity_listed['ActivityID']
        activity_data = load_json(json_server + '/activity/' + str(activity_id))['data'][0]
        master_id = activity_id + 4000000
        master, master_created = MasterContent.objects.get_or_create(id=master_id)
        try:
            activity = Activity.objects.get(master=master, publish_status='DRAFT')
        except Activity.DoesNotExist:
            activity = Activity(master=master, publish_status='DRAFT')
            pass
        
        activity.parent = conference_event_master
        activity.title = activity_data['ProgramTitle']
        activity.status = activity_data['ActivityStatus']
        if 'ProgramDescription' in activity_data:
            activity.content = activity_data['ProgramDescription']
        
        # NEED TO COME BACK TO THIS!!!
        activity.begin_time = None
        activity.end_time = None

        if 'BeginDateTime' in activity_data:
            activity.begin_time = activity_data['BeginDateTime']
        if 'EndDateTime' in activity_data:
            activity.end_time = activity_data['EndDateTime']
        
        if 'FunctionCode' in activity_data:
            activity.code = activity_data['FunctionCode']
        
        if 'CreditStatus ' in activity_data:
            activity.cm_status = activity_data['CreditStatus']
        if 'CreditRequestedNumber' in activity_data:
            activity.cm_requested = activity_data['CreditRequestedNumber']
        if 'CreditApprovedNumber' in activity_data:
            activity.cm_approved = activity_data['CreditApprovedNumber']

        # # not in model... should it be??
        # if 'CreditLawStatus' in activity_data:
        #      = activity_data['CreditLawStatus']
        if 'CreditLawRequestedNumber ' in activity_data:
            activity.cm_law_requested = activity_data['CreditLawRequestedNumber ']
        if 'CreditLawApprovedNumber' in activity_data:
            activity.cm_law_approved = activity_data['CreditLawApprovedNumber']

        # # not in model... should it be??
        # if 'CreditEthicsStatus' in activity_data:
        #      = activity_data['CreditEthicsStatus']
        if 'CreditEthicsRequestedNumber' in activity_data:
            activity.cm_ethics_requested = activity_data['CreditEthicsRequestedNumber']
        if 'CreditEthicsApprovedNumber' in activity_data:
            activity.cm_ethics_approved = activity_data['CreditEthicsApprovedNumber']


        activity.save()
        print("Imported Activity #{0}".format(activity_id))

def get_event_activity_tagtypes(event_id):
    """
    Creates and imports tag types for a given event... corresponding to the activity types in the old events db
    """

    national_conference = EventMulti.objects.get(master_id=3027311, publish_status='DRAFT')
    events_national_tag_type = TagType.objects.get(code='EVENTS_NATIONAL_TYPE')

    # activities created in t3go are given a 9000000 id - do not loop through these

    for activity in NationalConferenceActivity.objects.filter(parent=national_conference.master):
        activity_tag_type, activity_tag_type_created = ContentTagType.objects.get_or_create(content=activity, tag_type=events_national_tag_type)
        

        print("tag type attach attempt to activity #{0}".format(activity.master_id))

        if activity.master_id < 5000000 and activity.master_id > 4000000:

            activity_data = load_json(json_server + '/activity/' + str(activity.master_id-4000000))['data'][0]
            
            old_activity_type_id = activity_data['ActivityTypeID']

            activity_type_tag_code = None

            if old_activity_type_id == 3:
                activity_type_tag_code = 'SPECIAL_EVENT'
            elif old_activity_type_id == 4:
                activity_type_tag_code = 'ORIENTATION_TOUR'
            elif old_activity_type_id == 12:
                activity_type_tag_code = 'SESSION'
            elif old_activity_type_id == 13:
                activity_type_tag_code = 'POSTER'
            elif old_activity_type_id == 18:
                activity_type_tag_code = 'MOBILE_WORKSHOP'
            elif old_activity_type_id == 19:
                activity_type_tag_code = 'TRAINING_WORKSHOP'
            elif old_activity_type_id == 20:
                activity_type_tag_code = 'MEETING'
            elif old_activity_type_id == 26:
                activity_type_tag_code = 'FACILITATED_DISCUSSION'

            if activity_type_tag_code is not None:

                print("tag for " + activity_type_tag_code + " added to activity #" + str(activity.master_id))

                activity_tag = Tag.objects.get(code=activity_type_tag_code)
                
                activity_tag_type.tags.clear()

                activity_tag_type.tags.add(activity_tag)

                activity_tag_type.save()

    # ... TO DO loop through activities and add the tag types... 


def get_event_contacts(event_id):
    """
    Imports contacts for a particular event
    """
    contact_list = load_json(json_server + '/contact/list/' + str(event_id))['data']
    print("Importing {0} contacts...".format(len(contact_list)))

    for contact_listed in contact_list:
        contact_id = contact_listed['ParticipantID']

        print("Importing ParticipantID {0}..".format(contact_id))

        contact_data = load_json(json_server + '/contact/' + str(contact_id))['data'][0]


        username = contact_data['WebUserID']

        # for testing, anonymous users will have the username = 'A' + ParticipantID.
        # we could then update the username fields to 'ANONYMOUS' for those that contain the letter 'A'

        try:
            if username != 'ANONYMOUS':
                contact = Contact.objects.get(user__username=username)
            # how to check for duplicate anonymous records??
            else: 
                contact = Contact()

        except Contact.DoesNotExist:
            contact = Contact()
            pass

        contact.contact_type = 'INDIVIDUAL'
        contact.status = 'A'

        contact.user.username = contact_data['WebUserID']
        contact.prefix_name = contact_data['Prefix']
        contact.first_name = contact_data['FirstName']
        contact.middle_name = contact_data['MiddleName']
        contact.last_name = contact_data['LastName']
        contact.suffix_name = contact_data['Suffix']
        contact.designation = contact_data['Designation']
        contact.job_title = contact_data['Title']
        contact.email = contact_data['Email']
        contact.phone = contact_data['Phone']
        contact.cell_phone = contact_data['CellPhone']
        contact.company = contact_data['Company']
        contact.bio = contact_data['Bio']
        contact.about_me = contact_data['AboutMe']
        contact.personal_url = contact_data['PersonalUrl']
        contact.linkedin_url = contact_data['LinkedInUrl']
        contact.facebook_url = contact_data['FacebookUrl']
        contact.twitter_url = contact_data['TwitterUrl']

        contact.user_address_num = contact_data['AddressNum']
        contact.address1 = contact_data['Address1']
        contact.address2 = contact_data['Address2']
        contact.city = contact_data['City']
        contact.state = contact_data['StateProvince']
        contact.country = contact_data['Country']

        contact.save()

        print("Imported Contact {0}".format(username))


# def get_participant_contact_roles(event_id):
#     """
#     Imports participant contact roles for a particular event
#     This function is specific to the national conference event contact roles due to sql data structure!
#     """
#     contact_list = load_json(json_server + '/contact/list/' + str(event_id))['data']

#     for contact_listed in contact_list:

#         contact_id = contact_listed['ParticipantID']

#         print("Importing Participant ID: {0}".format(contact_id))
#         contact_data = load_json(json_server + '/contact/' + str(contact_id))['data'][0]

#         username = contact_data['WebUserID']


#         activity_id = contact_data['ActivityID']

#         master_id = contact_data['ActivityID'] + 4000000


#         try:
#             activity = Activity.objects.get(master=master_id, publish_status='DRAFT')
#             contact = Contact.objects.get(user__username=username)


#             if contact_data['Proposer'] == 1:
#                 try:
#                     contactrole = ContactRole.objects.get(contact_id=contact_id, content_id=activity_id)
#                 except ContactRole.DoesNotExist:
#                     contactrole = ContactRole()
#                     pass

#                 contactrole.role_type = 'PROPOSER'
#                 contactrole.contact = contact
#                 contactrole.content = activity

#                 contactrole.save()
#                 print("Saved as proposer.")

#             if contact_data['CoAuthor'] == 1:
#                 try:
#                     contactrole = ContactRole.objects.get(contact_id=contact_id, content_id=activity_id)
#                 except ContactRole.DoesNotExist:
#                     contactrole = ContactRole()
#                     pass

#                 contactrole.role_type = 'COAUTHOR'
#                 contactrole.contact = contact
#                 contactrole.content = activity

#                 contactrole.save()            
#                 print("Saved as coauthor.")

#             if contact_data['Organizer'] == 1:
#                 try:
#                     contactrole = ContactRole.objects.get(contact_id=contact_id, content_id=activity_id)
#                 except ContactRole.DoesNotExist:
#                     contactrole = ContactRole()
#                     pass
 
#                 contactrole.role_type = 'ORGANIZER'
#                 contactrole.contact = contact
#                 contactrole.content = activity

#                 contactrole.save()            
#                 print("Saved as organizer.")

#             if contact_data['Speaker'] == 1:
#                 try:
#                     contactrole = ContactRole.objects.get(contact_id=contact_id, content_id=activity_id)
#                 except ContactRole.DoesNotExist:
#                     contactrole = ContactRole()
#                     pass

#                 contactrole.role_type = 'SPEAKER'
#                 contactrole.contact = contact
#                 contactrole.content = activity

#                 contactrole.save()            
#                 print("Saved as speaker.")

#             if contact_data['Moderator'] == 1:
#                 try:
#                     contactrole = ContactRole.objects.get(contact_id=contact_id, content_id=activity_id)
#                 except ContactRole.DoesNotExist:
#                     contactrole = ContactRole()
#                     pass
  
#                 contactrole.role_type = 'MODERATOR'
#                 contactrole.contact = contact
#                 contactrole.content = activity

#                 contactrole.save()            
#                 print("Saved as moderator.")

#         except Activity.DoesNotExist:
#             print("Error: Activity {0} does not exist. Run get_event_activities.".format(activity_id))
#             pass
#         except Contact.DoesNotExist:
#             print("Error: Contact {0} does not exist. Run get_event_contacts.".format(username))
#             pass

def get_taxotopictags():
    """
    Imports Taxonomy Topic Tags, Search Topic Tags, and the relationships between them.

    IMPORTANT:
        1. Assume that the tag types for code=SEARCH_TOPIC and code=TAXO_MASTERTOPIC have been created already
    """

    print("Importing Taxo Master Topic Tags...")
    taxo_master_topic_tags_json    = load_json("%s/tag/list/TAXO_MASTERTOPIC" % json_server)['data']
    print("Importing Search Topic Tags...")
    search_topic_tags_json  = load_json("%s/tag/list/SEARCH_TOPIC" % json_server)['data']
    print("Importing Tag Relationships...")
    tag_relationships_json  = load_json("%s/tagrelationship/list/TAXO_MASTERTOPIC" % json_server)['data']

    tag_type_taxo_mastertopic = TagType.objects.get(code="TAXO_MASTERTOPIC")
    tag_type_search_topic = TagType.objects.get(code="SEARCH_TOPIC")

    tag_id_code_dict = {}

    TaxoTopicTag.objects.all().delete()
    Tag.objects.filter(tag_type__code="SEARCH_TOPIC").delete()

    # first create tags
    print("Initializing Search Topic Tags in Django...")    
    for tag_json in search_topic_tags_json:
        tag = Tag(
            code=tag_json["TagCode"],
            tag_type=tag_type_search_topic,
            status=tag_json["TagStatus"],
            title=tag_json["TagName"],
            sort_number=tag_json["SortNumber"],
            taxo_term=tag_json["Taxo_Term"],
            description=tag_json["Taxo_Definition"],
        )
        tag.save()

    print("Initializing Taxo Master Topic Tags in Django...")
    for tag_json in taxo_master_topic_tags_json:
        tag_id_code_dict[tag_json["TagID"]] = tag_json["TagCode"]
        tag_code = tag_json["TagCode"]
        if tag_code is None:
            tag_code = tag_json["TagName"].upper().replace(" ","_")
        tag = TaxoTopicTag(
            code=tag_code,
            tag_type=tag_type_taxo_mastertopic,
            status=tag_json["TagStatus"],
            title=tag_json["TagName"],
            sort_number=tag_json["SortNumber"],
            taxo_term=tag_json["Taxo_Term"],
            description=tag_json["Taxo_Definition"],
        )
        tag.save()


    # then loop over again to assign parent tags
    print("Assigning Parent Relationships for Taxo Master Topic Tags...")
    for tag_json in taxo_master_topic_tags_json:
        tag = TaxoTopicTag.objects.filter(code=tag_json["TagCode"]).first()
        parent_id = tag_json["ParentTagID"]
        if parent_id is not None and parent_id in tag_id_code_dict and tag is not None:
            parent = TaxoTopicTag.objects.filter(code=tag_id_code_dict[parent_id]).first()
            tag.parent = parent
            tag.save()



    print("Assigning Relationships between Taxo Master Topic Tags and Search Topic Tags...")
    for relationship_json in tag_relationships_json:
        tag = TaxoTopicTag.objects.filter(code=relationship_json["TagCode1"]).first()
        tag_related = Tag.objects.filter(tag_type__code="SEARCH_TOPIC", code=relationship_json["TagCode2"]).first()
        if tag_related is not None:
            tag.related.add(tag_related)
            tag.save()


    print("Complete")

def get_provider_relationships():
    """
    creates provider contact records and adds relationships between admins and providers
    """

    error_provider_ids = []
    error_all = []
    
    provider_relationships = load_json(RESTIFY_SERVER_ADDRESS + '/provider/relationships')

    for provider_relationship in provider_relationships['data']:
        try:

            admin_id = provider_relationship['AdminID']

            contact_admin, created = Contact.objects.get_or_create(user__username = admin_id)

            contact_admin.save()



            provider_id = provider_relationship['ProviderID']
            member_type = provider_relationship['MemberType']
            company = provider_relationship['Company']
            address1 = provider_relationship['Address1']
            address2 = provider_relationship['Address2']
            city = provider_relationship['City']
            zip_code = provider_relationship['ZipCode']
            state = provider_relationship['State']
            country = provider_relationship['Country']
            phone = provider_relationship['Phone']
            email = provider_relationship['Email']
            provider_type_code = provider_relationship.get('ProviderTypeCode', '')
            bio = provider_relationship.get('ProviderDescription', '')
            ein = provider_relationship.get('ProviderEIN', '')
            is_affiliate = provider_relationship.get('IsAffiliate', '')


            if address1 != None:
                address1 = address1[:40]
            if address2 != None:
                address2 = address2[:40]
            if city != None:
                city = city[:40]
            if state != None:
                state = state[:15]
            if zip_code != None:
                zip_code = zip_code[:10]
            if country != None:
                country = country[:20]
            if phone != None:
                phone = phone[:20]
            if email != None:
                email = email[:100]
            # create contact record
            if ein != None:
                ein = ein[:15]
            if provider_type_code != None:
                provider_type_code[:20]

            contact, created = Contact.objects.get_or_create(user__username = provider_id)

            contact.address1 = address1
            contact.address2 = address2
            contact.city = city
            contact.state = state
            contact.zip_code = zip_code
            contact.country = country
            contact.phone = phone
            contact.company = company
            contact.email = email
            contact.contact_type = 'ORGANIZATION'
            contact.ein_number = ein
            contact.is_affiliate = is_affiliate
            contact.bio = bio
            contact.organization_type = provider_type_code
            contact.save()

            #contact.related_contacts.add(contact_admin)  # IS THIS ALL THAT NEEDS TO BE DONE FOR THE CONTACT / ORGANIZATION RELATIONSHIP?
            #contact.save()

            related_contacts, created = ContactRelationship.objects.get_or_create(source = contact, target = contact_admin)
            related_contacts.relationship_type = 'ADMINISTRATOR'
            related_contacts.save()

            print('contact organization added: ' + str(provider_id))

        except Exception as e:
            print('error adding contact record for provider_id: ' + str(provider_id))
            error_provider_ids.append(provider_id)
            error_all.append(str(e))
            continue

    error_body_complete = "issue importing the following provider relationships: " + str(error_provider_ids)

    error_body_complete += "\n" + "\n" + "***** exceptions ***** " + "\n"

    for error in error_all:
        error_body_complete += error + "\n" + "\n"

    send_mail("Error importing events in get_event_providers()", error_body_complete, 'it@planning.org', ['plowe@planning.org'], fail_silently=True)

    # add relationship
    print('done')


def update_user_data(username):

    """
    updates user and contact records from imis data (currently used when logging in)
    """

    try:

        url = RESTIFY_SERVER_ADDRESS + '/contact/' + username
        user_json = load_json(url)

        user = User.objects.get(username = username)


        user.first_name = user_json['data'][0]['FIRST_NAME']
        user.last_name = user_json['data'][0]['LAST_NAME']
        user.email = user_json['data'][0]['EMAIL']
        user.save()

        contact, created = Contact.objects.get_or_create(user = user)

        contact.first_name = user_json['data'][0]['FIRST_NAME']
        contact.middle_name = user_json['data'][0]['MIDDLE_NAME']
        contact.last_name = user_json['data'][0]['LAST_NAME']
        contact.suffix_name = user_json['data'][0]['SUFFIX'] 
        contact.email = user_json['data'][0]['EMAIL']
        contact.job_title = user_json['data'][0]['TITLE']
        contact.company = user_json['data'][0]['COMPANY']
        contact.phone = user_json['data'][0]['PHONE']
        contact.cell_phone = user_json['data'][0]['CELL_PHONE']
        contact.designation = user_json['data'][0]['DESIGNATION']
        contact.prefix_name = user_json['data'][0]['PREFIX']
        contact.address1 = user_json['data'][0]['ADDRESS_1']
        contact.address2 = user_json['data'][0]['ADDRESS_2']
        contact.city = user_json['data'][0]['CITY']
        contact.state = user_json['data'][0]['STATE_PROVINCE']
        contact.zip_code = user_json['data'][0]['ZIP']
        contact.user_address_num = user_json['data'][0]['ADDRESS_NUM']
        contact.country = user_json['data'][0]['COUNTRY']
        contact.address_type = user_json['data'][0]['ADDRESS_PURPOSE']
        contact.save()
    except Exception as e:
        print(str(e))
        pass


# var postImisPurchaseTransaction = db.makeProcedureCaller({  
#     "procedure_name":"web.dbo.Tedious_iMIS_Transaction_Purchase_Submit", 
#     "parameters":[  
#         {"name":"WebUserID","type":TYPES.VarChar},
#         {"name":"OrderID","type":TYPES.NVarChar},
#         {"name":"Product","type":TYPES.NVarChar},
#         {"name":"Quantity","type":TYPES.NVarChar},
#         {"name":"ProductPrice","type":TYPES.Decimal, options:{"precision":6,"scale":2} }, 
# ]});

# var postImisPaymentTransaction = db.makeProcedureCaller({   
#     "procedure_name":"web.dbo.Tedious_iMIS_Transaction_Payment_Submit", 
#     "parameters":[  
#         {"name":"WebUserID","type":TYPES.VarChar},
#         {"name":"OrderID","type":TYPES.NVarChar},
#         {"name":"Amount","type":TYPES.Decimal, options:{"precision":6,"scale":2}  },
# ]});

class write_imis_transaction(object):
    """
    posts transactions from postgres to imis
    """

    def post_order(order_id):
        """
        writes the purchase and payment
        """
        order = Order.objects.get(id = order_id)
        purchases = Purchase.objects.filter(order = order)
        payment = Payment.objects.get(order = order)

        imis_trans_number = 0
        invoice_reference_num = 0

        imis_trans_number, invoice_reference_num = post_purchases(purchases)
        post_payment(payment)

    def post_payment(payment):
        """
        writes the payment to imis for a particular order id passed
        """

        post_data = {"OrderID":order_id, "WebUserID":username, 

                    "Amount":amount, "TransactionDate": transaction_date,
                    "PNRef": pnref, "Balance": balance }

        r = requests.post(RESTIFY_SERVER_ADDRESS + "/imis/payment/create", data=post_data)

        data = r.json()['data']
        print('DATA' + str(data))

        #if data[0]['response'] == 'success':
                    
        

    def post_purchases(purchases):
        """
        writes the purchase to imis for a particualr order id passed
        """

        imis_trans_number = 0
        invoice_reference_num = 0

        for purchase in purchases:

            post_data = {"WebUserID":purchase.user.username, "ProductCode":purchase.product.code, 
                        "Quantity": purchase.quantity, "ProductPrice": purchase.product_price, 
                        "IsStandby": 0, "ProductTypeCode": purchase.product.product_type, 
                        "TransactionDate": purchase.submitted_time, "ImisTransNumber": imis_trans_number, 
                        "InvoiceReferenceNum": invoice_reference_num, "SourceSystem" : "MEETING"}

            r = requests.post(RESTIFY_SERVER_ADDRESS + "/imis/purchase/create", data=post_data)

            data = r.json()['data']
            print('DATA' + str(data))

            if data[0]['response'] == 'success':
                imis_trans_number = data[0]['imis_trans_number']
                invoice_reference_num = data[0]['invoice_reference_num']

                print("Purchase written for: " + purchase.user.username)
                print("Product: " + purchase.product)
                print ("***********************")

            else:
                print("MISSING SUCCESS MESSAGE....")

        return imis_trans_number, invoice_reference_num

def get_freestudents_list(school_id):
    """
    returns a list of free students written to imis based on school id
    """

    students_list = load_json('http://localhost:8080/freestudents/' + str(school_id) + '/list')

    return students_list

def sql_to_utc(string_date):
    """
    converts a string date in YYYY-MM-DDTHH:MM:SS.000Z format into utc DateTimeField
    """

    # convert times to UTC
    # http://stackoverflow.com/questions/79797/how-do-i-convert-local-time-to-utc-in-python
    try:
        if string_date != None:
            local = pytz.timezone("US/Eastern")
            datetime_format = "%Y-%m-%d %H:%M:%S"

            string_date = string_date.replace('T', ' ').split('.')[0]
            naive = datetime.datetime.strptime(string_date, datetime_format)
            local_dt = local.localize(naive, is_dst=None)
            utc_dt = local_dt.astimezone(pytz.utc)
        else:
            utc_dt = None
    except:
        return None
        
    return utc_dt

def get_activity_all():
    """
    gets a list of all events in SQL and copies them into django
    
    ACTIVITIES START AT 4,XXX,XXX
    QUESTIONS: 
    1. WHERE TO STORE THE EVENT/ACTIVITY ID? 2,xxx,xxxx
    """

    number_of_groups = 76
    # used in case activites no longer have a provider admin associated with the activity

    apa_provider_admin = Contact.objects.get(user__username='119523')


    error_all = []
    error_activity_ids = []
    error_event_ids = []

    for x in range(0, number_of_groups):
        print("***********************")
        print("GROUP NUMBER #" + str(x))
        print("***********************")

        # filter out invalid statuses? 
        activity_all = load_json(RESTIFY_SERVER_ADDRESS + '/activity/' + str(x) + '/all')

        for activity in activity_all['data']:

            activity_id = activity.get('ActivityID', 0)
            activity_master_id = 4000000 + activity_id
            
            event_id = activity.get('EventID', 0)
            event_master_id = 3000000 + event_id

            provider_id = activity.get('ProviderCompanyID', 0)
            try:
                
                master, created = MasterContent.objects.get_or_create(id=activity_master_id)

                activity_new, created = Activity.objects.get_or_create(master=master, publish_status='SUBMISSION')

                event_parent = MasterContent.objects.get(id=event_master_id)

                plowe = User.objects.get(username='261337')

                try:
                    created_by = User.objects.get(username=event['CreatedByID'])
                    last_updated_by = User.objects.get(username=event['LastUpdatedByID'])
                except:
                    created_by = plowe
                    last_updated_by = plowe

                begin_time = activity.get('BeginDateTime', None)
                end_time = activity.get('EndDateTime', None)
                created_time = activity.get('CreatedDateTime', None)
                updated_time = activity.get('UpdatedDateTime', None)

                # activity_new.parent = ENTER_EVENT_INSTANCE HERE
                activity_new.master = master
                activity_new.parent = event_parent
                activity_new.publish_status = 'SUBMISSION'
                activity_new.event_type = 'ACTIVITY'
                activity_new.begin_time = begin_time
                activity_new.end_time = end_time
                activity_new.cm_status = activity.get('CreditStatus', '')
                
                if activity_new.cm_status == None:
                    activity_new.cm_status = 'I'

                activity_new.cm_requested = activity.get('CreditRequestedNumber', 0)
                activity_new.cm_approved = activity.get('CreditApprovedNumber', 0)
                activity_new.cm_law_requested = activity.get('CreditLawRequestedNumber', 0)
                activity_new.cm_law_approved = activity.get('CreditLawApprovedNumber', 0)
                activity_new.cm_ethics_requested = activity.get('CreditEthicsRequestedNumber', 0)
                activity_new.cm_ethics_approved = activity.get('CreditEthicsApprovedNumber', 0)
                

                if activity.get('FunctionCode', '') != None:
                    activity_new.code = activity.get('FunctionCode', '')[:200]

                if activity.get('ProgramTitle', '') != None:
                    activity_new.title = activity.get('ProgramTitle', '')[:200]

                activity_new.status = activity.get('ActivityStatus', '')
                activity_new.text = activity.get('ProgramDescription', '')

                activity_new.created_time = created_time
                activity_new.updated_time = updated_time
                
                
                activity_new.save()

                if provider_id != None and provider_id != '':
                    try:
                        provider = Contact.objects.get(user__username = provider_id)

                        contactrole, created = ContactRole.objects.get_or_create(content=activity_new, contact=provider, role_type='PROVIDER')
                    except:
                        provider = apa_provider_admin
                        error_activity_ids.append(activity_id)
                        error_all.append("unable to find provider - added APA as provider")
                        contactrole, created = ContactRole.objects.get_or_create(content=activity_new, contact=apa_provider_admin, role_type='PROVIDER')
                        continue

                    contactrole, created = ContactRole.objects.get_or_create(content=activity_new, contact=provider, role_type='PROVIDER')
                    contactrole.save()
                # create draft/published activities
                if activity_new.status == 'A':
                    if not Activity.objects.filter(master=master, publish_status='DRAFT').exists():
                        activity_new.pk = None
                        activity_new.id = None
                        activity_new.publish_status = 'DRAFT'
                        activity_new.save()
                        
                        master.content_draft = activity_new
                        master.save()

                        if provider_id != None and provider_id != '':
                            contactrole, created = ContactRole.objects.get_or_create(content=activity_new, contact=provider, role_type='PROVIDER')
                            contactrole.save()
                    else:
                        activity_new = Activity.objects.get(master=master, publish_status='DRAFT')
                        activity_new.cm_law_requested = activity.get('CreditLawRequestedNumber', 0)
                        activity_new.cm_law_approved = activity.get('CreditLawApprovedNumber', 0)
                        activity_new.cm_ethics_requested = activity.get('CreditEthicsRequestedNumber', 0)
                        activity_new.cm_ethics_approved = activity.get('CreditEthicsApprovedNumber', 0)
                        activity_new.save()
                        
                    if not Activity.objects.filter(master=master, publish_status='PUBLISHED').exists():
                        activity_new.pk = None
                        activity_new.id = None
                        activity_new.publish_status = 'PUBLISHED'
                        activity_new.save()

                        master.content_live = activity_new
                        master.save()

                        if provider_id != None and provider_id != '':
                            contactrole, created = ContactRole.objects.get_or_create(content=activity_new, contact=provider, role_type='PROVIDER')
                            contactrole.save()
                    else:
                        activity_new = Activity.objects.get(master=master, publish_status='PUBLISHED')
                        activity_new.cm_law_requested = activity.get('CreditLawRequestedNumber', 0)
                        activity_new.cm_law_approved = activity.get('CreditLawApprovedNumber', 0)
                        activity_new.cm_ethics_requested = activity.get('CreditEthicsRequestedNumber', 0)
                        activity_new.cm_ethics_approved = activity.get('CreditEthicsApprovedNumber', 0)
                        activity_new.save()

                print('imported activity id: ' + str(activity_id) + ' | for event id: ' + str(event_id))

            except Exception as e:
                print ('******* ERRROR ****** ')
                print('Activity ID: ' + str(activity_id))
                print(str(e))
                error_event_ids.append(str(event_id))
                error_activity_ids.append(activity_id)
                error_all.append(str(activity_id) + ": " + str(e))
                continue

    error_body_complete = "issue importing the following activities: " + str(error_activity_ids)
    error_body_complete += "\n" + "\n" + "issue importing the following events: " + str(error_activity_ids)
    error_body_complete += "\n" + "\n" + "***** exceptions ***** " + "\n"

    for error in error_all:
        error_body_complete += error + "\n" + "\n"

    send_mail("Error importing activities in get_activity_all()", error_body_complete, 'it@planning.org', ['plowe@planning.org'], fail_silently=True)

    print("activity import complete")

def get_event_all():
    """
    gets a list of all events in SQL and copies them into django
    where to store the event id to link activities??
    EVENT MASTER IDS START AT 3,XXX,XXX
    """

    number_of_groups = 29

    error_event_ids = []
    error_all = []

    # used in case events no longer have a provider admin associated with the event
    apa_provider_admin = Contact.objects.get(user__username='119523')


    for x in range(0, number_of_groups):
        print("***********************")
        print("GROUP NUMBER #" + str(x))
        print("***********************")
        

        event_all = load_json(RESTIFY_SERVER_ADDRESS + '/event/' + str(x) + '/all/' + str(event_id))
 
        for event in event_all['data']:

            # Event types: DATE, EVENT_RELIST, '', COURSE, EVENT_CONFERENCE, EVENT_SINGLE

            # CM_STATUSES = (
            # ('A','Active'),
            # ('I','Inactive'),
            # ('P','Pending'),
            # ('C','Cancelled')

            try:
                event_id = event.get('EventID', 0)
                event_master_id = 3000000 + event_id


                master, created = MasterContent.objects.get_or_create(id=event_master_id)

                event_code = event['EventTypeCode']

                if event_code == "EVENT_CONFERENCE": 
                    event_code = "EVENT_MULTI"


                # ***** IMPORTANT: where to add event id in django? *****
                
                # creates submission first!
                event_new, created = Event.objects.get_or_create(master = master, publish_status = 'SUBMISSION')

                plowe = User.objects.get(username='261337')

                try:
                    created_by = User.objects.get(username=event['CreatedByID'])
                    last_updated_by = User.objects.get(username=event['LastUpdatedByID'])
                except:
                    created_by = plowe
                    last_updated_by = plowe

                begin_time = event.get('BeginDateTime', None)
                end_time = event.get('EndDateTime', None)
                created_time = event.get('CreatedDateTime', None)
                updated_time = event.get('UpdatedDateTime', None)

                # determine if there is not a begin_time
                if event_code == "COURSE":

                    distanceperiod_begin = event.get('DistancePeriod_Begin', None)
                    distanceperiod_end = event.get('DistancePeriod_End', None)

                    if begin_time == None:
                        begin_time = distanceperiod_begin

                    end_time = distanceperiod_end
                
                archive_time = end_time

                if archive_time is not None:
                    archive_time = end_time.replace(month = 5, day = 1, year = end_time.year + 2)

                event_new.master = master
                event_new.event_type = event_code
                event_new.begin_time = begin_time
                event_new.end_time = end_time
                event_new.archive_time = archive_time
                event_new.cm_status = event.get('CreditStatus', '')
                
                if event_new.cm_status == None:
                    event_new.cm_status = 'I'

                event_new.publish_status='SUBMISSION'

                # not sure why this isn't repeated for published submissions...
                event_new.cm_requested = event.get('CreditRequestedNumber', 0)
                event_new.cm_approved = event.get('CreditApprovedNumber', 0)
                event_new.cm_law_requested = event.get('CreditLawRequestedNumber', 0)
                event_new.cm_law_approved = event.get('CreditLawApprovedNumber', 0)
                event_new.cm_ethics_requested = event.get('CreditEthicsRequestedNumber', 0)
                event_new.cm_ethics_approved = event.get('CreditEthicsApprovedNumber', 0)
                
                event_new.is_free = event.get('IsFree', 0)
                if event_new.is_free == None:
                    event_new.is_free = False

                if event.get('Address1') != None:
                    event_new.address1 = event.get('Address1')[:40]
                if event.get('Address2') != None:
                    event_new.address2 = event.get('Address2', '')[:40]
                if event.get('City') != None:
                    event_new.city = event.get('City', '')[:40]
                if event.get('StateProvince') != None:
                    event_new.state = event.get('StateProvince', '')[:15]
                if event.get('Zip') != None:
                    event_new.zip = event.get('Zip', '')[:10]
                if event.get('Country') != None:
                    event_new.country = event.get('Country', '')[:20]
                if event.get('ConferenceCode', '') != None:
                    event_new.code = event.get('ConferenceCode', '')[:200]
                if event.get('EventName', '') != None:
                    event_new.title = event.get('EventName', '')[:200]
                event_new.status = event.get('EventStatus', '')
                event_new.text = event.get('Description', '')

                event_new.resource_url = event.get('EventUrl', '') ## ?? OK to store event url here?
                event_new.created_time = created_time
                event_new.updated_time = updated_time
                
                # event.slug = ??
                # event.user_address_num = ??
                
                event_new.save()

                try:
                    provider = event.get('ProviderCompanyID', None)
                    if provider is not None:

                        provider = Contact.objects.get(user__username = provider)

                        contactrole, created = ContactRole.objects.get_or_create(content=event_new, contact=provider, role_type='PROVIDER')
                except:
                    error_event_ids.append(event_id)
                    error_all.append("unable to find provider - added APA as provider")
                    contactrole, created = ContactRole.objects.get_or_create(content=event_new, contact=apa_provider_admin, role_type='PROVIDER')
                    continue
                # ************** #
                # create draft/published content records
                if event.get('EventStatus', 'I') == 'A':
                    if not Event.objects.filter(master=master, publish_status='DRAFT').exists():
                        event_new.pk = None
                        event_new.id = None
                        event_new.publish_status='DRAFT'
                        event_new.save()

                        master.content_draft = event_new
                        master.save()

                        if provider is not None:
                            contactrole, created = ContactRole.objects.get_or_create(content=event_new, contact=provider, role_type='PROVIDER')

                    else:
                        event_new = Event.objects.get(master = master, publish_status = 'DRAFT')
                        event_new.cm_law_requested = event.get('CreditLawRequestedNumber', 0)
                        event_new.cm_law_approved = event.get('CreditLawApprovedNumber', 0)
                        event_new.cm_ethics_requested = event.get('CreditEthicsRequestedNumber', 0)
                        event_new.cm_ethics_approved = event.get('CreditEthicsApprovedNumber', 0)
                        event_new.begin_time = begin_time
                        event_new.end_time = end_time
                        event_new.archive_time = archive_time
                        event_new.save()

                    if not Event.objects.filter(master=master, publish_status='PUBLISHED').exists():
                        event_new.pk = None
                        event_new.id = None
                        event_new.publish_status='PUBLISHED'
                        event_new.master.content_live = event_new
                        event_new.begin_time = begin_time
                        event_new.end_time = end_time
                        event_new.archive_time = archive_time
                        event_new.save()

                        master.content_live = event_new
                        master.save()

                        if provider is not None:
                            contactrole, created = ContactRole.objects.get_or_create(content=event_new, contact=provider, role_type='PROVIDER')
                    else:
                        event_new = Event.objects.get(master = master, publish_status = 'PUBLISHED')
                        event_new.cm_law_requested = event.get('CreditLawRequestedNumber', 0)
                        event_new.cm_law_approved = event.get('CreditLawApprovedNumber', 0)
                        event_new.cm_ethics_requested = event.get('CreditEthicsRequestedNumber', 0)
                        event_new.cm_ethics_approved = event.get('CreditEthicsApprovedNumber', 0)
                        event_new.begin_time = begin_time
                        event_new.end_time = end_time
                        event_new.archive_time = archive_time
                        event_new.save()
                        
                print("imported event id: " + str(event_id) + " | master content id: " + str(event_master_id))
            
                # ************** #

            except Exception as e:
                print ('******* ERRROR ****** ')
                print('Event ID: ' + str(event_id))
                print(str(e))
                error_event_ids.append(event_id)
                error_all.append(str(event_id) + ": " + str(e))
                continue

    error_body_complete = "issue importing the following events: " + str(error_event_ids)

    error_body_complete += "\n" + "\n" + "***** exceptions ***** " + "\n"

    for error in error_all:
        error_body_complete += error + "\n" + "\n"

    send_mail("Error importing events in get_event_all()", error_body_complete, 'it@planning.org', ['plowe@planning.org'], fail_silently=True)

def get_cm_log_all():
    """
    Imports all cm logs into django
    link to published content
    """

    number_of_groups = 128

    for x in range(0, number_of_groups):

        cm_log_all = load_json(RESTIFY_SERVER_ADDRESS + '/cm/log/' + str(x) + '/all')

        for cm_log in cm_log_all['data']:

            try:

                username = cm_log.get('ID', None)


                status = cm_log.get('CREDIT_STATUS', None)
                is_current = cm_log.get('PERIOD_ISCURRENT', False)

                credits_required = cm_log.get('CREDIT_REQUIRED_ADJUST', 32)

                law_credits_required = 1.5 # ??? is this always 1.5? field does not exist in Custom Credit 
                ethics_credits_required = 1.5 # ??? see above

                try:

                    contact = Contact.objects.get(user__username=username)
                except Contact.DoesNotExist:

                    user_json = load_json(RESTIFY_SERVER_ADDRESS + '/contact/' + str(username))

                    for user in user_json['data']:
                        # create user and contact record for missing user
                        new_user, created = User.objects.get_or_create(username=username)


                        new_user.first_name = user["FIRST_NAME"]
                        new_user.last_name = user["LAST_NAME"]
                        new_user.email = user["EMAIL"]
                        new_user.set_password("AP@PL@Nn1NG.")
                        new_user.save()

                        contact, created = Contact.objects.get_or_create(user__username = username)

                        contact.first_name = user["FIRST_NAME"][:20]
                        if user["MIDDLE_NAME"] != None:
                            contact.middle_name = user["MIDDLE_NAME"][:20]

                        contact.last_name = user["LAST_NAME"][:30]
                        if user["SUFFIX_NAME"] != None:
                            contact.suffix_name = user["SUFFIX_NAME"][:10]
                        contact.email = user["EMAIL"][:100]

                        if user["TITLE"] != None:
                            contact.job_title = user["TITLE"][:80]

                        if user["COMPANY"] != None:
                            contact.company = user["COMPANY"][:80]

                        if user["PHONE"]:
                            contact.phone = user["PHONE"][:20]
                        if user["CELL_PHONE"]:
                            contact.cell_phone = user["CELL_PHONE"][:20]

                        contact.designation = user["DESIGNATION"][:20]
                        contact.prefix_name = user["PREFIX"][:25]
                        contact.address1 = user["ADDRESS_1"][:40]
                        contact.address2 = user["ADDRESS_2"][:40]
                        contact.city = user["CITY"][:40]
                        contact.state = user["STATE_PROVINCE"][:15]
                        contact.zip_code = user["ZIP"][:10]
                        contact.user_address_num = user["ADDRESS_NUM"] 
                        contact.country = user["COUNTRY"][:20]
                        contact.bio = user["BIO"] 
                        contact.save()

                period = Period.objects.get(code=cm_log['CREDIT_PERIOD'])

                log, created = Log.objects.get_or_create(contact=contact, period=period, status=status, is_current = is_current, credits_required = credits_required)
                
                print("Log created for username: " + username + " | Period: " + period.code)

            except Exception as e:
                print ('******* ERRROR ****** ')
                print(str(e))

                send_mail("Error importing CM Log for username: " + str(username) + " | Credit Period: " + str(period), str(e), 'it@planning.org', ['plowe@planning.org'], fail_silently=True)

                continue

def get_cm_creditclaim_all():
    """
    gets all credit claims 
    QUESTION: self reported?
    FLAGGED / PUBLISHED fields in comment?
    NEED TO DO AD-HOC CLAIMS!!
    """
    
    number_of_groups = 2522

    error_claim_ids = []
    error_all = []
    for x in range(0, number_of_groups):

        credit_claim_all = load_json(RESTIFY_SERVER_ADDRESS + '/cm/creditclaim/' + str(x) + '/all')

        for credit_claim in credit_claim_all['data']:

            try:
                claim_id = credit_claim['ClaimID']
                username = credit_claim['WebUserID']

                period_code = credit_claim['PeriodCode']
                event_id = credit_claim.get('EventID', 0)
                activity_id = credit_claim.get('ActivityID', 0)
                comment = credit_claim.get('Comments', None)
                verified = credit_claim.get('ClaimIsVerified', False)
                is_speaker = credit_claim.get('IsSpeaker', False)
                is_author = credit_claim.get('IsAuthor', False)
                submitted_time = credit_claim.get('ClaimSubmittedDateTime')
                title = credit_claim.get('Logged_EventName', '') #?????
                rating = credit_claim.get('RatingStars', None)
                ad_hoc_id = credit_claim.get('AdHocID', 0)
                provider_name = credit_claim.get('COMPANY', 'CM_PROVIDER_TEST')
                claim_status = credit_claim.get('ClaimStatus', 'A')
                is_self_reported = credit_claim.get('IsSelfReported', False)

                contact = Contact.objects.get(user__username = username)

                period = Period.objects.get(code = period_code)
                log = Log.objects.get(contact=contact, period = period)

                # if event or activity id is passed, get credit claim from those
                if credit_claim.get('UseOverrideCredits', False):   
                    credits = credit_claim.get('Override_CreditApprovedNumber', 0)
                    law_credits = credit_claim.get('Override_CreditLawApprovedNumber', 0)
                    ethics_credits = credit_claim.get('Override_CreditEthicsApprovedNumber', 0)
                else:
                    credits = credit_claim.get('CreditApprovedNumber', 0)
                    law_credits = credit_claim.get('CreditLawApprovedNumber', 0)
                    ethics_credits = credit_claim.get('CreditEthicsApprovedNumber', 0)

                claim, created = Claim.objects.get_or_create(id = claim_id, contact=contact, log = log)
                
                claim.rating = rating
                claim.title = title
                claim.verified = verified 
                claim.is_speaker = is_speaker
                claim.is_author = is_author
                claim.self_reported = is_self_reported
                claim.submitted_time = submitted_time
                claim.provider_name = provider_name

                claim.credits = credits
                claim.law_credits = law_credits
                claim.ethics_credits = ethics_credits

                if event_id != None and event_id != 0:
                    if activity_id == None or activity_id == 0:
                        event_id = 3000000 + event_id

                    else:
                        event_id = 4000000 + activity_id
                    try:  
                        event = Event.objects.get(master=event_id, publish_status='PUBLISHED')
                        claim.event = event
                    
                    # event does not exist? continue adding the credits
                    except Exception as e:
                        print(" could not find event: " + str(event_id) + ". adding anyway...")
                        error_claim_ids.append(claim_id)
                        error_all.append(str(claim_id) + ": " +  str(e))
                        event = Event.objects.get(code='EVENT_MISSING')
                        continue

                    try: 
                        if comment != None or rating != None:
                            comment, created = CMComment.objects.get_or_create(contact = contact, content = event, commentary=comment, rating=rating, submitted_time = submitted_time)
                            claim.comment = comment
                    except:
                        print("issue saving comment")
                        error_claim_ids.append(claim_id)
                        error_all.append(str(claim_id) + ": issue saving comment. " + str(e) )
                        continue

                elif ad_hoc_id != 0 and ad_hoc_id != None:
                    author_journal = credit_claim.get('ProviderName', '')
                    description = credit_claim.get('Description', '') # description of article?
                    author_issue = credit_claim.get('EventSubName', '')
                    begin_time = credit_claim.get('BeginDateTime')
                    end_time = credit_claim.get('EndDateTime')
                    city = credit_claim.get('City', '')
                    state = credit_claim.get('StateProvince', '')
                    country = credit_claim.get('Country', '')
                    
                    claim.author_journal = author_journal
                    claim.title = title

                    claim.begin_time = begin_time
                    claim.end_time = end_time
                    claim.description = description
                    claim.city = city
                    claim.state = state
                    claim.country = country


                try:
                    claim.save()
                except Exception as e:
                    print ('******* DUPLICATE KEY ERRROR ? ****** ')
                    print('Claim ID: ' + str(claim_id))
                    print(str(e))
                    error_claim_ids.append(claim_id)
                    error_all.append(str(claim_id) + ": " + str(e))

                    claim.comment = None
                    claim.save()
                    continue
                    
                print ("Claim added ID: " + str(claim_id))

                if claim_status == "X":
                    claim.delete()

            except Exception as e:

                print ('******* ERRROR ****** ')
                print('Claim ID: ' + str(claim_id))
                print(str(e))
                error_claim_ids.append(claim_id)
                error_all.append(str(claim_id) + ": " + str(e))
                continue

    error_body_complete = "issue importing the following claims: " + str(error_claim_ids)

    error_body_complete += "\n" + "\n" + "***** exceptions ***** " + "\n"

    for error in error_all:
        error_body_complete += error + "\n" + "\n"

    send_mail("Error importing claims in get_cm_creditclaim_all()", error_body_complete, 'it@planning.org', ['plowe@planning.org'], fail_silently=True)

def get_cm_creditclaim_all_2():
    """
    gets all credit claims - goes from the reverse
    """
    
    number_of_groups = 2522

    error_claim_ids = []
    error_all = []

    while True:

        print("*** importing group number: " + str(number_of_groups) + " ***")

        credit_claim_all = load_json(RESTIFY_SERVER_ADDRESS + '/cm/creditclaim/' + str(number_of_groups) + '/all')

        for credit_claim in credit_claim_all['data']:

            try:
                claim_id = credit_claim['ClaimID']

                username = credit_claim['WebUserID']

                period_code = credit_claim['PeriodCode']
                event_id = credit_claim.get('EventID', 0)
                activity_id = credit_claim.get('ActivityID', 0)
                comment = credit_claim.get('Comments', None)
                verified = credit_claim.get('ClaimIsVerified', False)
                is_speaker = credit_claim.get('IsSpeaker', False)
                is_author = credit_claim.get('IsAuthor', False)
                submitted_time = credit_claim.get('ClaimSubmittedDateTime')
                title = credit_claim.get('Logged_EventName', '') #?????
                rating = credit_claim.get('RatingStars', None)
                ad_hoc_id = credit_claim.get('AdHocID', 0)
                provider_name = credit_claim.get('COMPANY', 'CM_PROVIDER_TEST')
                title = credit_claim.get('Logged_EventName', '')
                claim_status = credit_claim.get('ClaimStatus', 'A')

                is_self_reported = credit_claim.get('IsSelfReported', False)

                contact = Contact.objects.get(user__username = username)

                period = Period.objects.get(code = period_code)
                log = Log.objects.get(contact=contact, period = period)

                # if event or activity id is passed, get credit claim from those
                if credit_claim.get('UseOverrideCredits', False):   
                    credits = credit_claim.get('Override_CreditApprovedNumber', 0)
                    law_credits = credit_claim.get('Override_CreditLawApprovedNumber', 0)
                    ethics_credits = credit_claim.get('Override_CreditEthicsApprovedNumber', 0)
                else:
                    credits = credit_claim.get('CreditApprovedNumber', 0)
                    law_credits = credit_claim.get('CreditLawApprovedNumber', 0)
                    ethics_credits = credit_claim.get('CreditEthicsApprovedNumber', 0)

                claim, created = Claim.objects.get_or_create(id = claim_id, contact=contact, log = log)
     
                claim.verified = verified 
                claim.is_speaker = is_speaker
                claim.is_author = is_author
                claim.self_reported = is_self_reported
                claim.submitted_time = submitted_time
                claim.provider_name = provider_name

                claim.title = title
                claim.credits = credits
                claim.law_credits = law_credits
                claim.ethics_credits = ethics_credits

                if event_id != None and event_id != 0:
                    if activity_id == None or activity_id == 0:
                        event_id = 3000000 + event_id

                    else:
                        event_id = 4000000 + activity_id
                    try:  
                        event = Event.objects.get(master=event_id, publish_status='PUBLISHED')
                        claim.event = event
                    
                    # event does not exist? continue adding the credits
                    except Exception as e:
                        print(" could not find event: " + str(event_id) + ". adding anyway...")
                        error_claim_ids.append(claim_id)
                        error_all.append(str(claim_id) + ": " +  str(e))
                        event = Event.objects.get(code='EVENT_MISSING')
                        continue
                    
                    try:
                        if comment != None or rating != None:
                            comment, created = CMComment.objects.get_or_create(contact = contact, content = event, commentary=comment, rating=rating, submitted_time = submitted_time)
                            claim.comment = comment
                    except:
                        print("issue saving comment")
                        error_claim_ids.append(claim_id)
                        error_all.append(str(claim_id) + ": issue saving comment. " + str(e) )
                        continue
                        
                elif ad_hoc_id != 0 and ad_hoc_id != None:
                    author_journal = credit_claim.get('ProviderName', '')
                    description = credit_claim.get('Description', '') # description of article?
                    author_issue = credit_claim.get('EventSubName', '')
                    begin_time = credit_claim.get('BeginDateTime')
                    end_time = credit_claim.get('EndDateTime')
                    city = credit_claim.get('City', '')
                    state = credit_claim.get('StateProvince', '')
                    country = credit_claim.get('Country', '')
                    
                    claim.author_journal = author_journal
                    claim.title = title

                    claim.begin_time = begin_time
                    claim.end_time = end_time
                    claim.description = description
                    claim.city = city
                    claim.state = state
                    claim.country = country

                try:
                    claim.save()
                except Exception as e:
                    print ('******* DUPLICATE KEY ERRROR ? ****** ')
                    print('Claim ID: ' + str(claim_id))
                    print(str(e))
                    error_claim_ids.append(claim_id)
                    error_all.append(str(claim_id) + ": " + str(e))

                    claim.comment = None
                    claim.save()
                    continue

                print ("Claim added ID: " + str(claim_id))

                if claim_status == "X":
                    claim.delete()
                    
            except Exception as e:

                print ('******* ERRROR ****** ')
                print('Claim ID: ' + str(claim_id))
                print(str(e))
                error_claim_ids.append(claim_id)
                error_all.append(str(claim_id) + ": " + str(e))
                continue

        if number_of_groups == 0:
            break
        else:
            number_of_groups -= 1

    error_body_complete = "issue importing the following claims: " + str(error_claim_ids)

    error_body_complete += "\n" + "\n" + "***** exceptions ***** " + "\n"

    for error in error_all:
        error_body_complete += error + "\n" + "\n"

    send_mail("Error importing claims in get_cm_creditclaim_all()", error_body_complete, 'it@planning.org', ['plowe@planning.org'], fail_silently=True)

def get_cm_period_all():
    """
    imports all cm periods into t3go
    """
    credit_period_all = load_json(RESTIFY_SERVER_ADDRESS + '/cm/creditperiod/all')

    for credit_period in credit_period_all['data']:

        try:
            code = credit_period['PeriodCode']
            begin_time = credit_period['EffectiveStartDateTime']
            end_time = credit_period['EffectiveEndDateTime']
            grace_end_time = credit_period['GraceEndDateTime']
            rollover_from = credit_period.get('RolloverFromPeriodCode', None)
            period, created = Period.objects.get_or_create(code=code, begin_time=begin_time, end_time=end_time, grace_end_time=grace_end_time)

            if rollover_from != None and rollover_from != '':
                try:
                    rollover_from_period = Period.objects.get(code = rollover_from)
                    period.rollover_from = rollover_from_period
                except:
                    print("Rollover Period code does not exist yet!!")

            period.save()
            print("Period code created: " + code)
        except Exception as e:
            print(e)
            continue

def get_cm_instructor_all():
    """
    imports instructors from [events].dbo.[Credit_Instructor]
    WILL NOT IMPORT INSTRUCTORS WITH BLANK FIRST/LAST NAMES!!!
    QUESTIONS: HOW TO TREAT THOSE EVENTS THAT HAVE NOT BEEN PUBLISHED YET? CURRENTLY IGNORING THEM!!
    ALSO ... GET EVENT STATUS TO SAVE DIFFERENT EVENT RECORD TYPES
    """

    number_of_groups = 500

    for x in range(0, number_of_groups):


        credit_instructor_all = load_json(RESTIFY_SERVER_ADDRESS + '/cm/instructor/' + str(x) + '/all')

        created_by = User.objects.get(username='261337')
        for credit_instructor in credit_instructor_all['data']:

            try:
                event_id = credit_instructor.get('EventID', 0)
                activity_id = credit_instructor.get('ActivityID', 0)
                created_time = credit_instructor.get('CreatedDateTime', datetime.datetime.now())
                first_name = credit_instructor.get('FirstName', '')
                last_name = credit_instructor.get('LastName', '')
                designation = credit_instructor.get('Designation', '')
                bio = credit_instructor.get('InstructorBio', '')
                company = credit_instructor.get('Company', '')
                sort_number = credit_instructor.get('InstructorNumber', 1)
                instructor_id = credit_instructor.get('InstructorID')
                event_status = credit_instructor.get('EventStatus', 'I')

                username = credit_instructor.get('WebUserID', None)


                if activity_id != None and activity_id != 0 and activity_id != '':
                    master_id = activity_id + 4000000
                    event = Activity.objects.get(master = master_id, publish_status = 'SUBMISSION')
                elif event_id != None and event_id != 0 and event_id != '':
                    master_id = event_id + 3000000
                    event = Event.objects.get(master = master_id, publish_status = 'SUBMISSION')

                if username is None or username == '':
                    username = 'ANONYMOUS'

                # ?? is this good enough to limit contacts
                contact, created = Contact.objects.get_or_create(instructor_id = instructor_id, created_by = created_by, updated_by = created_by, username=username, first_name = first_name, last_name = last_name, designation = designation, bio = bio, company = company)

                contact.save()

                print("anonymous contact created for event/activity: " + str(master_id))

                contactrole, created = ContactRole.objects.get_or_create(content = event, contact = contact, role_type='SPEAKER', sort_number = sort_number, confirmed = True)
                contactrole.save()


                if event_status != None and event_status == 'A':
                    if not Event.objects.filter(master=master_id, publish_status='DRAFT').exists():
                        event.pk = None
                        event.id = None
                        event.publish_status='DRAFT'
                        event.save()
                    else:
                        event = Event.objects.get(master=master_id, publish_status='DRAFT')

                    contactrole, created = ContactRole.objects.get_or_create(content = event, contact = contact, role_type='SPEAKER', sort_number = sort_number, confirmed = True)
                    contactrole.save()

                    if not Event.objects.filter(master=master_id, publish_status='PUBLISHED').exists():
                        event.pk = None
                        event.id = None
                        event.publish_status='PUBLISHED'
                        event.save()
                    else:
                        event = Event.objects.get(master=master_id, publish_status='PUBLISHED')
                        
                    contactrole, created = ContactRole.objects.get_or_create(content = event, contact = contact, role_type='SPEAKER', sort_number = sort_number, confirmed = True)
                    contactrole.save()

            except Exception as e:
                print ("***** ERROR importing credit instructors : " + str(e))
                continue

def get_provider_transactions():
    """
    imports all provider transactions from credit_order, credit_transaction_payment, and credit_transaction_purchase
    
    what is registration status in transaction_purchase??
    NOTE: Order model should have contact relationship 
    """


    number_of_groups = 10

    # all products
    product_cm_bundle_100 = Product.objects.get(code='CM_PROVIDER_BUNDLE100_2015', publish_status="PUBLISHED")
    product_cm_bundle_50 = Product.objects.get(code='CM_PROVIDER_BUNDLE50_2015', publish_status="PUBLISHED")
    product_cm_distance = Product.objects.get(code='CM_PROVIDER_DISTANCE_2015', publish_status="PUBLISHED")

    product_per_credit = Product.objects.get(code='PRODUCT_CM_PER_CREDIT_2015', publish_status="PUBLISHED")
    product_cm_registration = Product.objects.get(code='CM_PROVIDER_REGISTRATION_2015', publish_status="PUBLISHED")

    product_cm_unlimited_2015 = Product.objects.get(code='CM_PROVIDER_ANNUAL_2015', publish_status="PUBLISHED")

    product_cm_day = Product.objects.get(code='CM_PROVIDER_DAY_2015', publish_status="PUBLISHED")
    product_cm_week = Product.objects.get(code='CM_PROVIDER_WEEK_2015', publish_status="PUBLISHED")

    product_cm_misc = Product.objects.get(code='CM_PROVIDER_MISC', publish_status="PUBLISHED")

    product_cm_unlimited = Product.objects.get(code='CM_PROVIDER_REGISTRATION', publish_status="PUBLISHED")
    product_cm_per_credit = Product.objects.get(code='PRODUCT_CM_PER_CREDIT', publish_status="PUBLISHED")

    product_option_unlimited_1 = ProductOption.objects.get(code='CM_UNLIMITED_1', publish_status="PUBLISHED")
    product_option_unlimited_inhouse = ProductOption.objects.get(code='CM_UNLIMITED_INHOUSE', publish_status="PUBLISHED")
    product_option_unlimited_nonprofit_1 = ProductOption.objects.get(code='CM_UNLIMITED_NONPROFIT_1', publish_status="PUBLISHED")
    product_option_unlimited_nonprofit_2 = ProductOption.objects.get(code='CM_UNLIMITED_NONPROFIT_2', publish_status="PUBLISHED")
    product_option_unlimited_nonprofit_3 = ProductOption.objects.get(code='CM_UNLIMITED_NONPROFIT_3', publish_status="PUBLISHED")
    product_option_unlimited_nonprofit_4 = ProductOption.objects.get(code='CM_UNLIMITED_NONPROFIT_4', publish_status="PUBLISHED")
    

    product_price_bundle_100 = ProductPrice.objects.get(title='CM Provider Bundle 100 - 2015', publish_status="PUBLISHED")
    product_price_bundle_50 = ProductPrice.objects.get(title='CM Provider Bundle 50 - 2015', publish_status="PUBLISHED")

    product_price_distance = ProductPrice.objects.get(title='CM Provider Distance - 2015', publish_status="PUBLISHED")

    product_price_per_credit = ProductPrice.objects.get(title='Per Credit Price - 2015', publish_status="PUBLISHED")
    product_price_registration = ProductPrice.objects.get(title='CM Provider Registration - 2015', publish_status="PUBLISHED")
    
    product_price_government = ProductPrice.objects.get(title='Annual Unlimited - Government and University Rate', publish_status="PUBLISHED")
    product_price_inhouse = ProductPrice.objects.get(title='In House Annual Unlimited (for employee training only)', publish_status="PUBLISHED")
    product_price_under_500k = ProductPrice.objects.get(title='Annual Unlimited (nonprofit, less than $500,000)', publish_status="PUBLISHED")
    product_price_500K_5M = ProductPrice.objects.get(title='Annual Unlimited (nonprofit, $500,000 to $5M)', publish_status="PUBLISHED")
    product_price_5M_15M = ProductPrice.objects.get(title='Annual Unlimited (nonprofit, $5M to 15M)', publish_status="PUBLISHED")
    product_price_over_15M = ProductPrice.objects.get(title='Annual Unlimited (nonprofit, over $15M)', publish_status="PUBLISHED")
    
    product_price_day = ProductPrice.objects.get(title='CM Provider Day 2015', publish_status="PUBLISHED")
    product_price_week = ProductPrice.objects.get(title='CM Provider Week 2015', publish_status="PUBLISHED")

    product_price_misc = ProductPrice.objects.get(title='CM Provider Misc Archived', publish_status="PUBLISHED")
    
    error_order_ids = []
    error_purchase_ids = []
    error_payment_ids = []
    error_all = []
    error_body_complete = ''

    for x in range(0, number_of_groups):

        order_all = load_json(RESTIFY_SERVER_ADDRESS + '/cm/order/' + str(x) + '/all')

        for order in order_all['data']:

            try:
                # create the new order
                submitted_username= order.get('SubmittedByID', '')
                submitted_time = order.get('SubmittedDateTime', None)
                order_id = order["OrderID"]
                provider_company_id = order['ProviderCompanyID']

                try:
                    user = User.objects.get(username=submitted_username)
                except:
                    user = None
                # assumes submitted time (and ID) is good enough to loop over duplicate records
                order, created  = Order.objects.get_or_create(submitted_user_id = provider_company_id, order_status='PROCESSED', submitted_time = submitted_time, user = user)

                order.order_status = 'PROCESSED'
                order.is_manual = False
                order.submitted_time = submitted_time
                order.save()

                purchase_all = load_json(RESTIFY_SERVER_ADDRESS + '/cm/purchase/' + str(order_id) + '/all')
                payment_all = load_json(RESTIFY_SERVER_ADDRESS + '/cm/payment/' + str(order_id) + '/all')


                for purchase in purchase_all['data']:

                    old_product_code = purchase.get('ProductCode', '')
                    purchase_description = purchase.get('PurchaseDescription','')
                    purchase_quantity = purchase.get('PurchaseQuantity', 0)
                    payment_required_total = purchase.get('PaymentRequiredTotal', 0)
                    is_period_unlimited = purchase.get('IsPeriodUnlimited', False)
                    submitted_time = purchase.get('SubmittedDateTime', None)
                    description = purchase.get('PurchaseDescription', '')
                    if purchase_quantity > 0:
                        submitted_product_price_amount = payment_required_total / purchase_quantity
                    else:
                        submitted_product_price_amount = payment_required_total
                        
                    purchase_id = purchase.get('PurchaseID', '')

                    if old_product_code == 'BUNDLE_100':
                        product = product_cm_bundle_100
                        option = None
                        price = product_price_bundle_100
                    elif old_product_code == 'BUNDLE_50':
                        product = product_cm_bundle_50
                        option = None
                        price = product_price_bundle_50
                    elif old_product_code == 'DISTANCE_FEE':
                        product = product_cm_distance
                        option = None
                        price = product_price_distance
                    elif old_product_code == 'PERCREDIT':
                        product = product_cm_per_credit
                        option = None
                        price = product_price_per_credit
                    elif old_product_code == 'REGISTRATION':
                        product = product_cm_registration
                        option = None
                        price = product_price_registration
                    elif old_product_code == 'UNLIMITED_1':
                        product = product_cm_unlimited_2015
                        option = product_option_unlimited_1
                        price = product_price_government
                    elif old_product_code == 'UNLIMITED_INHOUSE':
                        product = product_cm_unlimited_2015
                        option = product_option_unlimited_inhouse
                        price = product_price_inhouse
                    elif old_product_code == 'UNLIMITED_NONPROFIT_1':
                        product = product_cm_unlimited_2015
                        option = product_option_unlimited_nonprofit_1
                        price = product_price_under_500k
                    elif old_product_code == 'UNLIMITED_NONPROFIT_2':
                        product = product_cm_unlimited_2015
                        option = product_option_unlimited_nonprofit_2
                        price = product_price_500K_5M
                    elif old_product_code == 'UNLIMITED_NONPROFIT_3':
                        product = product_cm_unlimited_2015
                        option = product_option_unlimited_nonprofit_3
                        price = product_price_5M_15M
                    elif old_product_code == 'UNLIMITED_NONPROFIT_4':
                        product = product_cm_unlimited_2015
                        option = product_option_unlimited_nonprofit_4
                        price = product_price_over_15M
                    elif old_product_code == 'UNLIMITED_DAY':
                        product = product_cm_day
                        option = None
                        price = product_price_day
                    elif old_product_code == 'UNLIMITED_WEEK':
                        product = product_cm_week
                        option = None
                        price = product_price_week
                    else:
                        product = product_cm_misc
                        option = None
                        price = product_price_misc

                    try:
                        user = User.objects.get(username=submitted_username)
                    except:
                        user = None

                    try:
                        contact = Contact.objects.get(user__username=provider_company_id)

                    except:
                        user = None

                    purchase_new, created = Purchase.objects.get_or_create(submitted_time = submitted_time, order = order, contact = contact, user = user, quantity = purchase_quantity, status='A', product = product, option = option, product_price=price, amount = payment_required_total, submitted_product_price_amount = submitted_product_price_amount, description = description)
                    purchase_new.save()

                for payment in payment_all['data']:

                    payment_type_code = payment.get('PaymentTypeCode', '')
                    provider_company_id = payment.get('ProviderCompanyID', 0)
                    payment_total = payment.get('PaymentTotal', 0)
                    submitted_by_id = payment.get('SubmittedByID', None)

                    address_1 = payment.get('BillingAddress1', '')
                    address_2 = payment.get('BillingAddress2','')
                    city = payment.get('BillingCity', '')
                    state = payment.get('BillingStateProvince', '')
                    country = payment.get('BillingCountry', '')
                    zip_code = payment.get('BillingZip', '')
                    submitted_time = payment.get('SubmittedDateTime', None)
                    billing_name = payment.get('PaymentName', '')
                    description = payment.get('PaymentDescription', '')

                    payment_type_code = payment.get('PaymentTypeCode', '')
                    if payment_type_code == 'CREDIT':
                        payment_type_code = 'CC'
                    elif payment_type_code == 'REFUND_CREDIT':
                        payment_type_code = 'CC_REFUND'
                    elif payment_type_code == 'MAIL':
                        payment_type_code = 'CHECK'
                    elif payment_type_code == ' REFUND_MAIL':
                        payment_type_code = 'CHECK_REFUND'

                    payment_new, created = Payment.objects.get_or_create(method = payment_type_code, billing_name = billing_name, order = order, address1 = address_1, address2 = address_2, city = city, state = state, zip_code = zip_code, country = country, amount = payment_total, description = description, user = user, contact = contact)
                    payment_new.save()

                print("order id: " + str(order_id) + " imported successfully.")
            except Exception as e:

                print ('******* ERRROR ****** ')
                print('Inserting Order failed')
                print (str(e))
                error_order_ids.append(order_id)
                error_all.append('order id: ' + str(order_id) + '| exception: ' + str(e))
                #error_all.append("order id: " + str(order_id) + " | purchase id: " + str(purchase_id) + " | payment_id: " + str(payment_id) + "\n" + str(e))
  
                error_body_complete = "issue importing the following orders: " + str(error_order_ids)

                error_body_complete += "\n" + "\n" + "***** exceptions ***** " + "\n"

                for error in error_all:
                    error_body_complete += error + "\n" + "\n"
                
                continue

    send_mail("Error importing orders in get_provider_transactions()", error_body_complete, 'it@planning.org', ['plowe@planning.org'], fail_silently=True)

def get_cm_approved_apps():
    """
    for all providers with a Credit_Transaction_Purchase record with RegistrationStatus="A" ... 
    create a new ProviderApplication record for them with begin/end dates for 4/1/2007 to 1/1/2016 and status ="A"
    NEEDS TO BE TESTED
    """
    error_purchase_ids = []
    error_all = []

    number_of_groups = 31

    begin_date = '2007-04-01'
    end_date = '2016-01-01'

    for x in range(0, number_of_groups):
        purchases_all = load_json(RESTIFY_SERVER_ADDRESS + '/cm/approved/application/' + str(x) + '/all')

        for purchase in purchases_all["data"]:
            try:
                purchase_id = purchase.get("PurchaseID")
                year = purchase.get("RegistrationPeriodCode")

                try:
                    provider = purchase.get('ProviderCompanyID', None)
                    if provider is not None:

                        provider = Contact.objects.get(user__username = provider)

                except:
                    error_purchase_ids.append(purchase_id)
                    error_all.append("unable to find provider - added APA as provider")
                    continue

                provider_application, created = ProviderApplication.objects.get_or_create(provider = provider, begin_date = begin_date, end_date = end_date)
                provider_application.year = '2015'
                provider_application.save()
            except Exception as e:
                print("import provider error for purchase id: " + str(purchase_id) + ": " + str(e))
                error_purchase_ids.append(purchase_id)
                error_all.append(str(purchase_id) + ": " + str(e))
                continue

    error_body_complete = "issue importing the following apps: " + str(error_purchase_ids)

    error_body_complete += "\n" + "\n" + "***** exceptions ***** " + "\n"

    for error in error_all:
        error_body_complete += error + "\n" + "\n"

    send_mail("Error importing events in get_cm_approved_apps()", error_body_complete, 'it@planning.org', ['plowe@planning.org'], fail_silently=True)

def get_cm_registrations():
    """
    gets cm approved applications (unlimited)
    NOTE: No purchases created
    """

    error_purchase_ids = []
    error_all = []

    registration_all = load_json(RESTIFY_SERVER_ADDRESS + '/cm/registration/all')
    purchase_id = ""
    for registration in registration_all["data"]:
        try:
            purchase_id = registration.get("PurchaseID")
            year = registration.get("RegistrationPeriodCode")
            product_code = registration.get("ProductCode")
            status = registration.get("RegistrationStatus")
            payment_plan_code = registration.get('PaymentPlanCode', 'ADHOC')
            is_unlimited = False
            if payment_plan_code == 'ANNUAL_UNLIMITED':
                is_unlimited = True

            if product_code == "UNLIMITED_NONPROFIT_2":
                registration_type = "CM_UNLIMITED_MEDIUM"
            elif product_code == "UNLIMITED_NONPROFIT_1":
                registration_type = "CM_UNLIMITED_SMALL"
            elif product_code == "UNLIMITED_NONPROFIT_3":
                registration_type = "CM_UNLIMITED_LARGE"
            elif product_code == "UNLIMITED_NONPROFIT_4":
                registration_type = "CM_UNLIMITED_LARGEST"
            elif product_code == "UNLIMITED_1":
                registration_type = "CM_UNLIMITED_MEDIUM"
            else:
                registration_type = "CM_PER_CREDIT"

            try:
                provider = registration.get('ProviderCompanyID', None)
                if provider is not None:

                    provider = Contact.objects.get(user__username = provider)

            except:
                error_purchase_ids.append(purchase_id)
                error_all.append("unable to find provider - added APA as provider")
                continue

            provider_application, created = ProviderRegistration.objects.get_or_create(provider = provider, year = year)
            if provider_application.shared_from_partner_registration is None and "UNLIMITED" not in provider_application.registration_type:
                provider_application.registration_type = registration_type

            provider_application.status = status
            
            if provider_application.shared_from_partner_registration is not None:
                is_unlimited = True

            provider_application.is_unlimited = is_unlimited
            provider_application.save()

            print("purchase id: " + str(purchase_id) + " | registration imported OK")

        except Exception as e:
            print("import provider error for purchase id: " + str(purchase_id) + ": " + str(e))
            error_purchase_ids.append(purchase_id)
            error_all.append(str(purchase_id) + ": " + str(e))
            continue

    error_body_complete = "issue importing the following registrations: " + str(error_purchase_ids)

    error_body_complete += "\n" + "\n" + "***** exceptions ***** " + "\n"

    for error in error_all:
        error_body_complete += error + "\n" + "\n"

    send_mail("Error importing events in get_cm_registrations()", error_body_complete, 'it@planning.org', ['plowe@planning.org'], fail_silently=True)

def compare_cm_totals(period_code):
    """
    compares CM totals from django and microsoft sql
    """

    # compare cm totals 1 period at a time
    all_logs = Log.objects.filter(period__code=period_code)


    total_log_periods = all_logs.count()

    error_log_ids = []
    error_all = []

    removed_credit_claims = []
    added_credit_claims = []
    
    imported_events = []

    for log in all_logs:
        try:

            username = log.contact.user.username

            period = log.period.code
            log_id = log.id
            
            contact = log.contact
            period = log.period

            credits_dict = log.credits_overview()
            law_postgres = credits_dict['law']
            ethics_postgres = credits_dict['ethics']
            general_postgres = credits_dict['general']

            sql_json = load_json(RESTIFY_SERVER_ADDRESS + '/cm/log/' + str(username) + "/" +  str(period))

            postgres_claims = []
            postgres_claim_objects = Claim.objects.filter(log = log, contact = contact)
            for postgres_claim_object in postgres_claim_objects:
                postgres_claims.append(postgres_claim_object.id)

            law_sql = sql_json["data"][0]["CREDIT_LAW_NUMBER"]
            ethics_sql = sql_json["data"][0]["CREDIT_ETHICS_NUMBER"]
            general_sql = sql_json["data"][0]["CREDIT_NUMBER"]

            general_match = False
            law_match = False
            ethics_match = False

            if general_postgres == general_sql:
                general_match = True

            if law_postgres == law_sql:
                law_match = True

            if ethics_postgres == ethics_sql:
                ethics_match = True

            if not(general_match) or not(law_match) or not(ethics_match):

                print("deleting all claims for this log - attempt to re-add them...")
                postgres_claim_objects.delete()

                print("credits match failed for " + str(username) + " | period code: " + str(period))
                print(" attempting to add or remove records records... ")
                # fix attempt
                claims = load_json(RESTIFY_SERVER_ADDRESS + '/cm/creditclaim/' + str(username) + "/" +  str(period))


                sql_claims = []

                sql_claims_count = len(claims["data"])

                # send only an email to the last record added if the counts do not match up
                sql_claim_position = sql_claims_count

                for credit_claim in claims["data"]:

                    try:

                        # attempt to re-add / update event data.
                        old_event_id = credit_claim['EventID']
                        old_activity_id = credit_claim.get('ActivityID', 0)
                        if old_activity_id == 0:
                            old_activity_id = None

                        if old_event_id not in imported_events:
                            get_event(old_event_id)

                            if old_activity_id != None:
                                get_activities(old_event_id)

                            imported_events.append(old_event_id)

                        claim_id = credit_claim['ClaimID']

                        sql_claims.append(claim_id)

                        event_id = credit_claim.get('EventID', 0)
                        activity_id = credit_claim.get('ActivityID', 0)
                        comment = credit_claim.get('Comments', None)
                        verified = credit_claim.get('ClaimIsVerified', False)
                        is_speaker = credit_claim.get('IsSpeaker', False)
                        is_author = credit_claim.get('IsAuthor', False)
                        submitted_time = credit_claim.get('ClaimSubmittedDateTime')
                        title = credit_claim.get('Logged_EventName', '') #?????
                        rating = credit_claim.get('RatingStars', None)
                        ad_hoc_id = credit_claim.get('AdHocID', 0)
                        provider_name = credit_claim.get('COMPANY', 'CM_PROVIDER_TEST')
                        title = credit_claim.get('Logged_EventName', '')
                        claim_status = credit_claim.get('ClaimStatus', 'A')
                        ad_hoc_id = credit_claim.get('AdHocID', None)

                        is_self_reported = credit_claim.get('IsSelfReported', False)

                        # if event or activity id is passed, get credit claim from those
                        if credit_claim.get('UseOverrideCredits', False):   
                            credits = credit_claim.get('Override_CreditApprovedNumber', 0)
                            law_credits = credit_claim.get('Override_CreditLawApprovedNumber', 0)
                            ethics_credits = credit_claim.get('Override_CreditEthicsApprovedNumber', 0)
                        else:
                            credits = credit_claim.get('CreditApprovedNumber', 0)
                            law_credits = credit_claim.get('CreditLawApprovedNumber', 0)
                            ethics_credits = credit_claim.get('CreditEthicsApprovedNumber', 0)

                        if claim_status != "X":
                            claim, created = Claim.objects.get_or_create(id = claim_id, contact=contact, log = log)
                 
                            claim.verified = verified 
                            claim.is_speaker = is_speaker
                            claim.is_author = is_author
                            claim.self_reported = is_self_reported
                            claim.submitted_time = submitted_time
                            claim.provider_name = provider_name
                            claim.title = title

                            claim.credits = credits
                            claim.law_credits = law_credits
                            claim.ethics_credits = ethics_credits

                            if event_id != None and event_id != 0:
                                if activity_id == None or activity_id == 0:
                                    event_id = 3000000 + event_id

                                else:
                                    event_id = 4000000 + activity_id
                                try:  
                                    event = Event.objects.get(master=event_id, publish_status='PUBLISHED')
                                    claim.event = event
                                
                                
                                except Exception as e:
                                    print(" could not find event: " + str(event_id) + ". adding anyway...")
                                    error_log_ids.append(claim_id)
                                    error_all.append(str(claim_id) + ": " +  str(e))
                                    event = Event.objects.get(code='EVENT_MISSING')
                                    continue

                                try: 
                                    if comment != None or rating != None:
                                        comment, created = CMComment.objects.get_or_create(contact = contact, content = event, commentary=comment, rating=rating, submitted_time = submitted_time)
                                        claim.comment = comment
                                except:
                                    print("issue saving comment")
                                    error_log_ids.append(claim_id)
                                    error_all.append(str(claim_id) + ": issue saving comment. " + str(e) )
                                    continue

                            elif ad_hoc_id != 0 and ad_hoc_id != None:
                                author_journal = credit_claim.get('ProviderName', '')
                                description = credit_claim.get('Description', '') # description of article?
                                author_issue = credit_claim.get('EventSubName', '')
                                begin_time = credit_claim.get('BeginDateTime')
                                end_time = credit_claim.get('EndDateTime')
                                city = credit_claim.get('City', '')
                                state = credit_claim.get('StateProvince', '')
                                country = credit_claim.get('Country', '')
                                
                                claim.author_journal = author_journal
                                claim.title = title

                                claim.begin_time = begin_time
                                claim.end_time = end_time
                                claim.description = description
                                claim.city = city
                                claim.state = state
                                claim.country = country


                            try:
                                claim.save()
                            except Exception as e:
                                print ('******* DUPLICATE KEY ERRROR ? ****** ')
                                print('Claim ID: ' + str(claim_id))
                                print(str(e))
                                error_claim_ids.append(claim_id)
                                error_all.append(str(claim_id) + ": " + " Error saving comments. CHECK IF TOTALS MATCH! "+ str(e))

                                claim.comment = None
                                claim.save()
                                continue

                        if claim_status == "X":

                            try:
                                claim = Claim.objects.get(id = claim_id, contact=contact, log = log)
                                claim.delete()
                            except Exception as e:
                                print("claim does not exist to delete.. assume OK")
                                continue

                        # get the log again for comparison...
                        log_new = Log.objects.get(period = log.period, contact = log.contact)

                        credits_dict_new = log_new.credits_overview()
                        law_postgres = credits_dict_new['law']
                        ethics_postgres = credits_dict_new['ethics']
                        general_postgres = credits_dict_new['general']

                        general_match = False
                        law_match = False
                        ethics_match = False

                        if general_postgres == general_sql:
                            general_match = True

                        if law_postgres == law_sql:
                            law_match = True

                        if ethics_postgres == ethics_sql:
                            ethics_match = True

                        if sql_claim_position == 1 and (not(general_match) or not(law_match) or not(ethics_match)):
                            print(" no exceptions, but credit claim totals still do not match! ")
                            error_log_ids.append(log_id)

                            error_message = "WebUserID: " + str(username) + "\n"

                            error_message += "Period: " + str(period) + "\n"
                            error_message += "general_match: " + str(general_match) + " | " + "law_match: " + str(law_match) + " | " + "ethics_match: " + str(ethics_match) + "\n"
                            error_message += "general_postgres: " + str(general_postgres) + " | " + "law_postgres: " + str(law_postgres) + " | " + "ethics_postgres: " + str(ethics_postgres) + "\n"
                            error_message += "general_sql: " + str(general_sql) + " | " + "law_sql: " + str(law_sql) + " | " + "ethics_sql: " + str(ethics_sql) + "\n"

                            error_message += "number of postgres claims: " + str(Claim.objects.filter(log = log, contact = contact).count()) + "\n"
                            error_message += "number of sql claims: " + str(sql_claims_count) + "\n"

                            error_message += "postgres claim ids: " + str(postgres_claims) +  "\n"
                            error_message += "sql claim ids: " + str(sql_claims) + "\n"
                            error_message += "\n"
                            error_all.append(error_message)

                            send_mail("credit claim mismatch", error_message, 'it@planning.org', ['plowe@planning.org'], fail_silently=True)

                        sql_claim_position -= 1

                    except Exception as e:
                        print(" adding credit claim still failed! ")
                        error_log_ids.append(log_id)

                        error_message = "WebUserID: " + str(username) + "\n"

                        error_message += "Period: " + str(period) + "\n"
                        error_message += "general_match: " + str(general_match) + " | " + "law_match: " + str(law_match) + " | " + "ethics_match: " + str(ethics_match) + "\n"
                        error_message += "general_postgres: " + str(general_postgres) + " | " + "law_postgres: " + str(law_postgres) + " | " + "ethics_postgres: " + str(ethics_postgres) + "\n"
                        error_message += "general_sql: " + str(general_sql) + " | " + "law_sql: " + str(law_sql) + " | " + "ethics_sql: " + str(ethics_sql) + "\n"

                        error_message += "number of postgres claims: " + str(Claim.objects.filter(log = log, contact = contact).count()) + "\n"
                        error_message += "number of sql claims: " + str(sql_claims_count) + "\n"

                        error_message += "postgres claim ids: " + str(postgres_claims) +  "\n"
                        error_message += "sql claim ids: " + str(sql_claims) + "\n"
                        error_message += "exception: " + str(e)
                        error_message += "\n"
                        error_all.append(error_message)

                        send_mail("Error adding/removing credit claims", error_message, 'it@planning.org', ['plowe@planning.org'], fail_silently=True)

            else:

                print("match OK! for period: " + str(period) + " and user: " + str(username))


        except Exception as e:
            print("error comparing CM totals for user id: " + str(username) + " on period code: " + str(period))

            print(str(e))
            error_log_ids.append(log_id)
            error_all.append("log id: " + str(log_id) + " || " + str(e) + "EVENT ID: " + str(event_id))
            continue

    if len(error_all) != 0:
        error_body_complete = "issue comparing the following cm logs: " + str(error_log_ids)

        error_body_complete += "\n" + "\n" + "***** exceptions ***** " + "\n"

        for error in error_all:
            error_body_complete += error + "\n" + "\n"

        send_mail("Error importing events in compare_cm_totals()", error_body_complete, 'it@planning.org', ['plowe@planning.org'], fail_silently=True)

def resave_claims():
    """
    saves claims again so we can pull the correct cm_ethics_approved and cm_law_approved totals!
    """

    claims = Claim.objects.all()

    for claim in claims:
        claim.save()

        print ("claim saved for claim id: " + str(claim.id))

        
def get_event(event_id):
    """
    attempts to import a single event
    """

    sql_json = load_json(RESTIFY_SERVER_ADDRESS + '/event/' + str(event_id))

    error_event_ids = []
    error_all = []

    print("running get_event() for event id: " + (str(event_id)))

    apa_provider_admin = Contact.objects.get(user__username='119523')

    try: 
        for event in sql_json['data']:

            event_id = event.get('EventID', 0)
            event_type = event.get('EventTypeCode', '')
            event_status = event.get('EventStatus', 'A')

            try:
                created_by = User.objects.get(username=event['CreatedByID'])
                last_updated_by = User.objects.get(username=event['LastUpdatedByID'])
            except:
                created_by = plowe
                last_updated_by = plowe

            begin_time = event.get('BeginDateTime', None)
            end_time = event.get('EndDateTime', None)
            created_time = event.get('CreatedDateTime', None)
            updated_time = event.get('UpdatedDateTime', None)

            cm_requested = event.get('CreditRequestedNumber', 0)
            cm_approved = event.get('CreditApprovedNumber', 0)
            cm_law_requested = event.get('CreditLawRequestedNumber', 0)
            cm_law_approved = event.get('CreditLawApprovedNumber', 0)
            cm_ethics_requested = event.get('CreditEthicsRequestedNumber', 0)
            cm_ethics_approved = event.get('CreditEthicsApprovedNumber', 0)
            
            is_free = event.get('IsFree', False)
            event_url = event.get('EventUrl', '')

            if is_free == None:
                event_new.is_free = False

            address1 = ''
            address2 = ''
            city = ''
            state = ''
            zip_code = ''
            country = ''
            code = ''
            title = ''

            if event.get('Address1', None) != None:
                address1 = event.get('Address1')[:40]
            if event.get('Address2', None) != None:
                address2 = event.get('Address2', '')[:40]
            if event.get('City', None) != None:
                city = event.get('City', '')[:40]
            if event.get('StateProvince', None) != None:
                state = event.get('StateProvince', '')[:15]
            if event.get('Zip', None) != None:
                zip_code = event.get('Zip', '')[:10]
            if event.get('Country', None) != None:
                country = event.get('Country', '')[:20]
            if event.get('ConferenceCode', '') != None:
                code = event.get('ConferenceCode', '')[:200]
            if event.get('EventName', '') != None:
                title = event.get('EventName', '')[:200]
            status = event.get('EventStatus', '')
            text = event.get('Description', '')

            resource_url = event.get('EventUrl', '') ## ?? OK to store event url here?

            if event_type == "COURSE":

                distanceperiod_begin = event.get('DistancePeriod_Begin', None)
                distanceperiod_end = event.get('DistancePeriod_End', None)

                if begin_time == None:
                    begin_time = distanceperiod_begin

                end_time = distanceperiod_end
            
            archive_time = end_time

            if archive_time is not None:
                archive_time = end_time.replace(month = 5, day = 1, year = end_time.year + 2)

            cm_status = event.get('CreditStatus', None)
            if cm_status == None:
                cm_status = 'I'


            event_master_id = 3000000 + event_id

            master, created = MasterContent.objects.get_or_create(id=event_master_id)

            if event_type == "EVENT_CONFERENCE": 
                event_type = "EVENT_MULTI"
      
            event_new, created = Event.objects.get_or_create(master = master, publish_status = 'SUBMISSION')
            event_new.event_type = event_type
            event_new.begin_time = begin_time
            event_new.end_time = end_time
            event_new.archive_time = archive_time
            event_new.cm_status = cm_status

            event_new.cm_requested = cm_requested
            event_new.cm_approved = cm_approved
            event_new.cm_law_requested = cm_law_requested
            event_new.cm_law_approved = cm_law_approved
            event_new.cm_ethics_requested = cm_ethics_requested
            event_new.cm_ethics_approved = cm_ethics_approved
                
            event_new.is_free = is_free    

            event_new.resource_url = event.get('EventUrl', '') ## ?? OK to store event url here?
            event_new.created_time = created_time
            event_new.updated_time = updated_time
                     
            event_new.save()

            try:
                provider = event.get('ProviderCompanyID', None)
                if provider is not None:

                    provider = Contact.objects.get(user__username = provider)

                    contactrole, created = ContactRole.objects.get_or_create(content=event_new, contact=provider, role_type='PROVIDER')
            except:
                error_event_ids.append(event_id)
                contactrole, created = ContactRole.objects.get_or_create(content=event_new, contact=apa_provider_admin, role_type='PROVIDER')
                continue

            if event_status == 'A':
                if not Event.objects.filter(master=master, publish_status='DRAFT').exists():
                    event_new.pk = None
                    event_new.id = None
                    event_new.publish_status='DRAFT'
                    event_new.save()

                    master.content_draft = event_new
                    master.save()

                    if provider is not None:
                        contactrole, created = ContactRole.objects.get_or_create(content=event_new, contact=provider, role_type='PROVIDER')

                else:
                    event_new = Event.objects.get(master = master, publish_status = 'DRAFT')
                    event_new.cm_law_requested = event.get('CreditLawRequestedNumber', 0)
                    event_new.cm_law_approved = event.get('CreditLawApprovedNumber', 0)
                    event_new.cm_ethics_requested = event.get('CreditEthicsRequestedNumber', 0)
                    event_new.cm_ethics_approved = event.get('CreditEthicsApprovedNumber', 0)
                    event_new.begin_time = begin_time
                    event_new.end_time = end_time
                    event_new.archive_time = archive_time
                    event_new.save()

                if not Event.objects.filter(master=master, publish_status='PUBLISHED').exists():
                    event_new.pk = None
                    event_new.id = None
                    event_new.publish_status='PUBLISHED'
                    event_new.master.content_live = event_new
                    event_new.begin_time = begin_time
                    event_new.end_time = end_time
                    event_new.archive_time = archive_time
                    event_new.save()

                    master.content_live = event_new
                    master.save()

                    if provider is not None:
                        contactrole, created = ContactRole.objects.get_or_create(content=event_new, contact=provider, role_type='PROVIDER')
                else:
                    event_new = Event.objects.get(master = master, publish_status = 'PUBLISHED')
                    event_new.cm_law_requested = event.get('CreditLawRequestedNumber', 0)
                    event_new.cm_law_approved = event.get('CreditLawApprovedNumber', 0)
                    event_new.cm_ethics_requested = event.get('CreditEthicsRequestedNumber', 0)
                    event_new.cm_ethics_approved = event.get('CreditEthicsApprovedNumber', 0)
                    event_new.begin_time = begin_time
                    event_new.end_time = end_time
                    event_new.archive_time = archive_time
                    event_new.save()
                    
            print("imported event id: " + str(event_id) + " | master content id: " + str(event_master_id))
        

    except Exception as e:
        print ('******* ERRROR ****** ')
        print('Event ID: ' + str(event_id))
        print(str(e))
        error_event_ids.append(event_id)
        error_all.append(str(event_id) + ": " + str(e))

    if len(error_all) != 0:
        error_body_complete = "issue importing the following events: " + str(error_event_ids)

        error_body_complete += "\n" + "\n" + "***** exceptions ***** " + "\n"

        for error in error_all:
            error_body_complete += error + "\n" + "\n"

        send_mail("Error importing events in get_event_all()", error_body_complete, 'it@planning.org', ['plowe@planning.org'], fail_silently=True)

def get_activities(event_id):
    """
    attempts to import all activities for a particular event
    """

    sql_json = load_json(RESTIFY_SERVER_ADDRESS + '/event/' + str(event_id) + '/activities')

    error_activity_ids = []
    error_all = []

    apa_provider_admin = Contact.objects.get(user__username='119523')



    for activity in sql_json['data']:
        try:
            activity_id = activity.get('ActivityID', 0)

            plowe = User.objects.get(username='261337')

            try:
                created_by = User.objects.get(username=activity['CreatedByID'])
                last_updated_by = User.objects.get(username=activity['LastUpdatedByID'])
            except:
                created_by = plowe
                last_updated_by = plowe

            begin_time = activity.get('BeginDateTime', None)
            end_time = activity.get('EndDateTime', None)
            created_time = activity.get('CreatedDateTime', None)
            updated_time = activity.get('UpdatedDateTime', None)

            cm_requested = activity.get('CreditRequestedNumber', 0)
            cm_approved = activity.get('CreditApprovedNumber', 0)
            cm_law_requested = activity.get('CreditLawRequestedNumber', 0)
            cm_law_approved = activity.get('CreditLawApprovedNumber', 0)
            cm_ethics_requested = activity.get('CreditEthicsRequestedNumber', 0)
            cm_ethics_approved = activity.get('CreditEthicsApprovedNumber', 0)
            

            archive_time = end_time

            if archive_time is not None:
                archive_time = end_time.replace(month = 5, day = 1, year = end_time.year + 2)

            cm_status = activity.get('CreditStatus', None)
            if cm_status == None:
                cm_status = 'I'

            activity_master_id = 4000000 + activity_id
            
            event_id = activity.get('EventID', 0)

            provider_id = activity.get('ProviderCompanyID', 0)


            event_master_id = 3000000 + event_id
            event_parent = MasterContent.objects.get(id=event_master_id)

            master, created = MasterContent.objects.get_or_create(id=activity_master_id)

            activity_new, created = Activity.objects.get_or_create(master = master, publish_status = 'SUBMISSION')
            activity_new.begin_time = begin_time
            activity_new.end_time = end_time
            activity_new.archive_time = archive_time
            activity_new.cm_status = cm_status

            activity_new.cm_requested = cm_requested
            activity_new.cm_approved = cm_approved
            activity_new.cm_law_requested = cm_law_requested
            activity_new.cm_law_approved = cm_law_approved
            activity_new.cm_ethics_requested = cm_ethics_requested
            activity_new.cm_ethics_approved = cm_ethics_approved
                
            activity_new.created_time = created_time
            activity_new.updated_time = updated_time
            
            activity_new.parent = event_parent
            
            if activity.get('FunctionCode', '') != None:
                activity_new.code = activity.get('FunctionCode', '')[:200]

            if activity.get('ProgramTitle', '') != None:
                activity_new.title = activity.get('ProgramTitle', '')[:200]

            activity_new.status = activity.get('ActivityStatus', '')
            activity_new.text = activity.get('ProgramDescription', '')


            activity_new.save()

            # create draft/published activities
            if (activity_new.status == 'A' or event_id == 31693) and activity_new.status != 'X':
                if not Activity.objects.filter(master=master, publish_status='DRAFT').exists():
                    activity_new.pk = None
                    activity_new.id = None
                    activity_new.publish_status = 'DRAFT'
                    activity_new.save()
                    
                    master.content_draft = activity_new
                    master.save()

                else:
                    activity_new = Activity.objects.get(master=master, publish_status='DRAFT')
                    activity_new.cm_law_requested = activity.get('CreditLawRequestedNumber', 0)
                    activity_new.cm_law_approved = activity.get('CreditLawApprovedNumber', 0)
                    activity_new.cm_ethics_requested = activity.get('CreditEthicsRequestedNumber', 0)
                    activity_new.cm_ethics_approved = activity.get('CreditEthicsApprovedNumber', 0)
                    activity_new.save()
                    
                if not Activity.objects.filter(master=master, publish_status='PUBLISHED').exists():
                    activity_new.pk = None
                    activity_new.id = None
                    activity_new.publish_status = 'PUBLISHED'
                    activity_new.save()

                    master.content_live = activity_new
                    master.save()

                else:
                    activity_new = Activity.objects.get(master=master, publish_status='PUBLISHED')
                    activity_new.cm_law_requested = activity.get('CreditLawRequestedNumber', 0)
                    activity_new.cm_law_approved = activity.get('CreditLawApprovedNumber', 0)
                    activity_new.cm_ethics_requested = activity.get('CreditEthicsRequestedNumber', 0)
                    activity_new.cm_ethics_approved = activity.get('CreditEthicsApprovedNumber', 0)
                    activity_new.save()
            
            print('imported activity id: ' + str(activity_id) + ' | for event id: ' + str(event_id))

        except Exception as e:
            print ('******* ERRROR ****** ')
            print('Activity ID: ' + str(activity_id))
            print(str(e))
            error_activity_ids.append(str(event_id))
            error_activity_ids.append(activity_id)
            error_all.append(str(activity_id) + ": " + str(e))
            continue

    if len(error_all) != 0:
        error_body_complete = "issue importing the following activities: " + str(error_activity_ids)
        error_body_complete += "\n" + "\n" + "issue importing the following events: " + str(error_activity_ids)
        error_body_complete += "\n" + "\n" + "***** exceptions ***** " + "\n"

        for error in error_all:
            error_body_complete += error + "\n" + "\n"

        send_mail("Error importing activities in get_activities()", error_body_complete, 'it@planning.org', ['plowe@planning.org'], fail_silently=True)

    print("activity import complete")


def get_comments(period_code):
    """
    tries to go through each sql activity with comments and adds them to the given postgres for a given period_code
    """
    pass

def log_mismatch(period_code):
    """
    returns a count for log totals that do not match sql
    """

    # compare cm totals 1 period at a time
    all_logs = Log.objects.filter(period__code=period_code)

    total_logs = all_logs.count()

    logs_mismatch = 0
    mismatch_users = []

    for log in all_logs:
        try:
            username = log.contact.user.username

            period = log.period.code
            log_id = log.id
            
            contact = log.contact
            period = log.period

            credits_dict = log.credits_overview()
            law_postgres = credits_dict['law']
            ethics_postgres = credits_dict['ethics']
            general_postgres = credits_dict['general']
            general_without_carryover_postgres = credits_dict['general_without_carryover']

            sql_json = load_json(RESTIFY_SERVER_ADDRESS + '/cm/log/' + str(username) + "/" +  str(period))

           
            postgres_claims = []
            postgres_claim_objects = Claim.objects.filter(log = log, contact = contact)
            for postgres_claim_object in postgres_claim_objects:
                postgres_claims.append(postgres_claim_object.id)

            law_sql = sql_json["data"][0]["CREDIT_LAW_NUMBER"]
            ethics_sql = sql_json["data"][0]["CREDIT_ETHICS_NUMBER"]
            general_sql = sql_json["data"][0]["CREDIT_NUMBER"]

            general_match = False
            law_match = False
            ethics_match = False

            if (general_postgres == general_sql or general_without_carryover_postgres == general_sql) :
                general_match = True

            if law_postgres == law_sql:
                law_match = True

            if ethics_postgres == ethics_sql:
                ethics_match = True

            if not(general_match) or not(law_match) or not(ethics_match):
                logs_mismatch += 1

                mismatch_users.append(username)

        except Exception as e: 
            print("error: ")
            print(str(e))

    print("total logs: " + str(total_logs))
    print("logs mismatched: " + str(logs_mismatch))
    print("users with mismatched logs: " + str(mismatch_users))

def fix_log_period(period_code, group_id):
    """
    searches for cm logs by period, finds counts that do not match, and corrects it.
    run log_mismatch function to verify
        
    groups by 500
    """
    logs_mismatch = get_log_mismatch_all(period_code, group_id)
    log_list_failed_fix = []

    for username in logs_mismatch:

        fix_response = cm_log_check(username, period_code)
        if fix_response == False:
            log_list_failed_fix.append(username)


    if len(log_list_failed_fix) == 0:
        print("FIXED COMPLETELY! NO ERRORS!")
    else:
        print("could not fix the following ids: ")
        print(str(log_list_failed_fix))
        print("logs still mismatched for the id: " + str(len(log_list_failed_fix)) )
        
def get_log_mismatch_all(period_code, group_id):
    """
    returns a list of logs that do not match sql for a period
    """

    # compare cm totals 1 period at a time - still timing out. group the logs
    # 

    min_count = group_id * 500
    max_count = min_count + 500
    all_logs = Log.objects.filter(period__code=period_code)
    
    group_logs = all_logs[min_count:max_count]
    total_logs = all_logs.count()
    
    total_groups = math.floor(total_logs / 500)

    print("total groups: " + str(total_groups))
    logs_mismatch = []
    
    for log in group_logs:
        try:
            username = log.contact.user.username

            period = log.period.code
            log_id = log.id
            
            contact = log.contact
            period = log.period

            credits_dict = log.credits_overview()
            law_postgres = credits_dict['law']
            ethics_postgres = credits_dict['ethics']
            general_postgres = credits_dict['general']
            general_without_carryover_postgres = credits_dict['general_without_carryover']


            sql_json = load_json(RESTIFY_SERVER_ADDRESS + '/cm/log/' + str(username) + "/" +  str(period))

           
            law_sql = sql_json["data"][0]["CREDIT_LAW_NUMBER"]
            ethics_sql = sql_json["data"][0]["CREDIT_ETHICS_NUMBER"]
            general_sql = sql_json["data"][0]["CREDIT_NUMBER"]

            general_match = False
            law_match = False
            ethics_match = False

            if general_postgres == general_sql or general_without_carryover_postgres == general_sql:
                general_match = True

            if law_postgres == law_sql:
                law_match = True

            if ethics_postgres == ethics_sql:
                ethics_match = True

            if general_match != True or law_match != True or ethics_match != True:

                logs_mismatch.append(log.contact.user.username)

 
        except Exception as e: 
            print("error: ")
            print(str(e))

    print("total logs: " + str(total_logs))
    print("contact logs mismatched: " + str(logs_mismatch))

    return logs_mismatch

def update_claim_title(period_code):
    """
    gets a list of claim objects by period code and updates the title if missing
    """

    claims = Claim.objects.filter((Q(title='') | Q(title__isnull=True)) & Q(log__period__code=period_code))

    for claim in claims:
        claim_id = claim.id

        try:
               
            claims_data = load_json(RESTIFY_SERVER_ADDRESS + '/cm/claim/' + str(claim_id))

            title = claims_data['data'][0]['Logged_EventName']
            status = claims_data['data'][0]['ClaimStatus']

            if status == "C":
                claim.is_carryover = True

            if title == None or title == '':
                if claim.event is not None:
                    claim.title = claim.event.title

            claim.save()

            if status == "X":
                claim.delete()

        except:
            print('error finding claim for claim id:' + str(claim_id))
            pass

        print("Claim title updated for claim id: " + str(claim_id))


def cm_log_check(username, period_code):
    """
    will verify a single log and attempt to fix it if the totals to do match with sql
    """
    contact = Contact.objects.get(user__username = username)

    log = Log.objects.get(contact=contact, period__code=period_code)
    username = log.contact.user.username

    period = log.period

    postgres_claims = Claim.objects.filter(log = log, contact = log.contact)

    claims_json = load_json(RESTIFY_SERVER_ADDRESS + '/cm/creditclaim/' + str(username) + "/" +  str(period.code))
    claims_json = claims_json['data']

    claims_match = claims_count_check(postgres_claims, claims_json, username, period.code, log, contact)

    print("Claims match status for user: " + str(username) + " in period: " + str(period.code) + " | " + str(claims_match))

    return claims_match

def claims_count_check(postgres_claims, claims_json, username, period_code, log, contact):

    """
    verify the claim totals match for a particular period

    """

    postgres_claim_ids_check = []
    sql_claim_ids = []
    sql_claim_ids_missing = []

    username 

    for claim in postgres_claims:
        postgres_claim_ids_check.append(claim.id)

    for sql_claim in claims_json:
        claim_id = sql_claim.get('ClaimID')
        sql_claim_ids.append(claim_id)

    sql_postgres_claims_match = True

    for sql_claim_id in sql_claim_ids:

        # missing sql claim. attempt to add in another function
        if sql_claim_id not in postgres_claim_ids_check:
            sql_postgres_claims_match = False
            sql_claim_ids_missing.append(sql_claim_id)

            # tries to write the missing claim 
            get_single_claim(sql_claim_id)

        # last attempt to verify sql data before we determine this a failure!
        if sql_postgres_claims_match == False:

            # postgres add completed... test counts again
            postgres_claims = Claim.objects.filter(contact=contact, log = log)
            postgres_claim_ids_check = []
            for claim in postgres_claims:
                postgres_claim_ids_check.append(claim.id)

            sql_claim_ids_retry = []
            

            claims_json_retry = load_json(RESTIFY_SERVER_ADDRESS + '/cm/creditclaim/' + str(username) + "/" +  str(period_code))

            claims_json_retry = claims_json_retry['data']

            for sql_claim_retry in claims_json_retry:
                claim_id_retry = sql_claim_retry.get('ClaimID')
                sql_claim_ids_retry.append(claim_id_retry)

            for sql_claim_retry in sql_claim_ids_retry:

                if sql_claim_retry not in postgres_claim_ids_check:
                    sql_postgres_claims_match = False
                    print(" adding claims failed.")
                    print("SQL IDS: " + str(sql_claim_ids_retry))
                    print("Postgres IDS: " + str(postgres_claim_ids_check))
                    return sql_postgres_claims_match
                else:
                    sql_postgres_claims_match = True
                    
    for postgres_claim in postgres_claim_ids_check:
        
        # delete any postgres claims that are NOT returned by SQL (assume status = X)
        if postgres_claim not in sql_claim_ids:
            postgres_claim_ids_check.remove(postgres_claim)
            claim = Claim.objects.get(id=postgres_claim)
            claim.delete()
    
    # lastly... verify totals!!
    credits_overview = log.credits_overview()
    general_postgres = credits_overview['general']
    ethics_postgres = credits_overview['ethics']
    law_postgres = credits_overview['law']
    general_carryover_postgres = credits_overview['general_without_carryover']

    sql_json = load_json(RESTIFY_SERVER_ADDRESS + '/cm/log/' + str(username) + "/" +  str(period_code))

           
    law_sql = sql_json["data"][0]["CREDIT_LAW_NUMBER"]
    ethics_sql = sql_json["data"][0]["CREDIT_ETHICS_NUMBER"]
    general_sql = sql_json["data"][0]["CREDIT_NUMBER"]

    if (general_postgres == general_sql or general_carryover_postgres == general_sql) and ethics_postgres == ethics_sql and law_postgres == law_sql:
        print("counts match!")
    else:
        print("counts are still off... ")
        return False

    return sql_postgres_claims_match

def get_single_claim(claim_id):
    """
    attempts to get and insert a missing claim
    also kicks off writing event/activities related to the claim if they are missing
    """

    error_log_ids = []
    error_all = []

    credit_claim = load_json(RESTIFY_SERVER_ADDRESS + '/cm/claim/' + str(claim_id))
    credit_claim = credit_claim['data'][0]


    username = credit_claim.get('WebUserID')

    event_id = credit_claim.get('EventID', 0)
    activity_id = credit_claim.get('ActivityID', 0)
    comment = credit_claim.get('Comments', None)
    verified = credit_claim.get('ClaimIsVerified', False)
    is_speaker = credit_claim.get('IsSpeaker', False)
    is_author = credit_claim.get('IsAuthor', False)
    submitted_time = credit_claim.get('ClaimSubmittedDateTime')
    title = credit_claim.get('Logged_EventName', '') #?????
    rating = credit_claim.get('RatingStars', None)
    ad_hoc_id = credit_claim.get('AdHocID', 0)
    provider_name = credit_claim.get('COMPANY', 'CM_PROVIDER_TEST')
    title = credit_claim.get('Logged_EventName', '')
    claim_status = credit_claim.get('ClaimStatus', 'A')
    ad_hoc_id = credit_claim.get('AdHocID', None)
    is_self_reported = credit_claim.get('IsSelfReported', False)
    period_code = credit_claim.get('PeriodCode', '')


    contact = Contact.objects.get(user__username = username)

    period = Period.objects.get(code=period_code)
    log = Log.objects.get(contact = contact, period = period)

    # if event or activity id is passed, get credit claim from those
    if credit_claim.get('UseOverrideCredits', False):   
        credits = credit_claim.get('Override_CreditApprovedNumber', 0)
        law_credits = credit_claim.get('Override_CreditLawApprovedNumber', 0)
        ethics_credits = credit_claim.get('Override_CreditEthicsApprovedNumber', 0)
    else:
        credits = credit_claim.get('CreditApprovedNumber', 0)
        law_credits = credit_claim.get('CreditLawApprovedNumber', 0)
        ethics_credits = credit_claim.get('CreditEthicsApprovedNumber', 0)

    if claim_status != "X":
        claim, created = Claim.objects.get_or_create(id = claim_id, contact=contact, log = log)

        if claim_status == "C":
            claim.is_carryover = True
            
        claim.verified = verified 
        claim.is_speaker = is_speaker
        claim.is_author = is_author
        claim.self_reported = is_self_reported
        claim.submitted_time = submitted_time
        claim.provider_name = provider_name
        claim.title = title

        claim.credits = credits
        claim.law_credits = law_credits
        claim.ethics_credits = ethics_credits

        if event_id is not None and event_id != 0:
            if activity_id is None or activity_id == 0:
                event_id = 3000000 + event_id
            else:
                event_id = 4000000 + activity_id
            try:  
                event = Event.objects.get(master=event_id, publish_status='PUBLISHED')
                claim.event = event
            
            except Exception as e:

                # add function here to attempt writing the missing event / activity

                ### STOPPED HERE!!! ADDING EVENT AND ACTIVITIES

                # attempt to re-add / update event data.
                        old_event_id = credit_claim['EventID']
                        old_activity_id = credit_claim.get('ActivityID', 0)
                        if old_activity_id == 0:
                            old_activity_id = None

                            # adds the event
                            get_event(old_event_id)

                            # adds the activities
                            if old_activity_id is not None:
                                print("importing activities ... ")
                                get_activities(old_event_id)

                ### STOPPED HERE!! ADDING EVENT AND ACTIVITIES

            try: 
                if comment != None or rating != None:
                    #comment, created = CMComment.objects.get_or_create(contact = contact, content = event, commentary=comment, rating=rating, submitted_time = submitted_time)
                    comment, created = CMComment.objects.get_or_create(cm_claim= claim)
                        #contact = contact, content = event, commentary=comment, rating=rating, submitted_time = submitted_time)
                    claim.comment = comment
            except:
                print("issue saving comment")
                error_log_ids.append(claim_id)
                error_all.append(str(claim_id) + ": issue saving comment. " + str(e) )

        elif ad_hoc_id != 0 and ad_hoc_id is not None:
            author_journal = credit_claim.get('ProviderName', '')
            description = credit_claim.get('Description', '') # description of article?
            author_issue = credit_claim.get('EventSubName', '')
            begin_time = credit_claim.get('BeginDateTime')
            end_time = credit_claim.get('EndDateTime')
            city = credit_claim.get('City', '')
            state = credit_claim.get('StateProvince', '')
            country = credit_claim.get('Country', '')
            
            claim.author_journal = author_journal

            claim.begin_time = begin_time
            claim.end_time = end_time
            claim.description = description
            claim.city = city
            claim.state = state
            claim.country = country


        try:
            claim.save()
        except Exception as e:
            print ('******* comment error?  issue saving claim ****** ')
            print('Claim ID: ' + str(claim_id))
            print(str(e))
            error_claim_ids.append(claim_id)
            error_all.append(str(claim_id) + ": " + " Error saving comments. CHECK IF TOTALS MATCH! "+ str(e))

            claim.comment = None
            claim.save()

    elif claim_status == "X":

        try:
            claim = Claim.objects.get(id = claim_id, contact=contact, log = log)
            claim.delete()
        except Exception as e:
            print("claim does not exist to delete.. assume OK")




def get_partner_registrations(period_code):
    """
    gets a list of providers and partner registrations
    """
    # these ein umbers are used by multiple provider companies
    ein_list = ['043167352','060904879','11-216717','223004888','226001086','237431522','510150311','520821608','521134021','521296856','530204534','566000756','610722001','746000537','860196696','911393557','916001537','942909979','956006143']
    
    year = period_code[3:]

    for ein in ein_list:
        try:
            contacts = Contact.objects.filter(ein_number = ein)

            purchases = load_json(RESTIFY_SERVER_ADDRESS + '/cm/provider/purchase/' +  str(ein) + '/' + year)

            main_provider = None
            main_provider_registration = None

            # get the main provider 
            for purchase in purchases['data']:

                product_code = purchase.get('ProductCode', '')

                if purchase.get('PaymentPlanCode', '') == 'ANNUAL_UNLIMITED':
                    provider_id = purchase.get('ProviderCompanyID')

                    main_provider = Contact.objects.get(user__username = provider_id)

                    main_provider_registration = ProviderRegistration.objects.get(provider=main_provider, year = year)

                    print('main reg found! main contact: ' + str(provider_id))
            # get registrations linked to the main provider purchase
            for purchase in purchases['data']:

                product_code = purchase.get('ProductCode', '')
                linked_provider_id = purchase.get('ProviderCompanyID')

                if product_code == 'REGISTRATION' and linked_provider_id != main_provideruser.username :
                    status = purchase.get("RegistrationStatus", "N")
                    contact, created = Contact.objects.get_or_create(user__username = linked_provider_id)

                    registration, created = ProviderRegistration.objects.get_or_create(is_unlimited = True, registration_type='CM_UNLIMITED_PARTNER', provider=contact, year = year)
                    
                    registration.shared_from_partner_registration = main_provider_registration
                    registration.status = status
                    registration.save()

                    print('partner found! partner contact: ' + str(linked_provider_id))
                    
            print('link complete')
        except Exception as e:
            print("ERROR on ein: " + str(ein) + ": " + str(e))
            continue

def event_archive_time_check():
    """
    re-saves all events to generate an archive time
    """

    events_all = Event.objects.all()

    for event in events_all:
        end_time = event.end_time

        if end_time is not None:
            archive_time = end_time.replace(month = 5, day = 1, year = end_time.year + 2)
            event.archive_time = archive_time
            event.save()

        print('archive timed saved for event: '+ str(event.id))

def event_utc_rollback():
    """
    takes utc time for all events and rolls them back to eastern time
    substracts 4 hours
    """

    events_all = Event.objects.all()
    #events_all = Event.objects.filter(master='3030875')

    events_failed = []

    for event in events_all:

        master = event.master

        if master != None and master != '3027311':

            try:
                if event.begin_time != None:
                    event.begin_time = event.begin_time - timedelta(hours = 4)
                if event.end_time != None:
                    event.end_time = event.end_time - timedelta(hours = 4)
                if event.created_time != None:
                    event.created_time = event.created_time - timedelta(hours = 4)
                if event.updated_time != None:
                    event.updated_time = event.updated_time - timedelta(hours = 4)
                if event.archive_time != None:
                    event.archive_time = event.archive_time - timedelta(hours = 4)

                event.save()
                print("time updated for event: " + str(event.id))
            except Exception as e:
                print ("error: " + str(e))
                events_failed.append(str(event.master))
        
        else:
            print("skip conference")

    
    print("events failed list: " + str(events_failed))


def get_log_mismatch_2(period_code, group_id):
    """
    returns a list of logs in postgres that has fewer claims then sql
    """

    # compare cm totals 1 period at a time - still timing out. group the logs
    # 

    min_count = group_id * 500
    max_count = min_count + 500
    all_logs = Log.objects.filter(period__code=period_code)

    # # contact = Contact.objects.get(user__username = "203506")


    # log = Log.objects.get(period__code = period_code, contact = contact)
    
    group_logs = all_logs[min_count:max_count]
    total_logs = all_logs.count()
    
    total_groups = math.floor(total_logs / 500)

    print("total groups: " + str(total_groups))

    mismatch_username = []
    
    for log in group_logs:
        try:
            username = log.contact.user.username

            # period = log.period.code
            log_id = log.id
            
            contact = log.contact
            period = log.period

            credits_dict = log.credits_overview()
            postgres_general = credits_dict['general']
            postgres_law = credits_dict['law']
            postgres_ethics = credits_dict['ethics']

            sql_json = load_json(RESTIFY_SERVER_ADDRESS + '/cm/log/' + str(username) + "/" +  str(period))


            sql_log = sql_json['data']
            sql_log_general = sql_log[0]['CREDIT_NUMBER']
            sql_log_law = sql_log[0]['CREDIT_LAW_NUMBER']
            sql_log_ethics = sql_log[0]['CREDIT_ETHICS_NUMBER']


            if float(postgres_general) < float(sql_log_general) or float(postgres_law) < float(sql_log_law) or float(postgres_ethics) < float(sql_log_ethics):

                mismatch_username.append(username)


        except Exception as e: 
            print("error: ")
            print(str(e))

    print("total logs: " + str(total_logs))
    print("contact logs mismatched: " + str(mismatch_username))



def resave_claim(period_code="JAN2014", min_id=2511, max_id=2538248):
# def resave_claim(period_code):
    """
    resaves claim for all claims that have an event associated with it
    """
    claims = Claim.objects.filter(event__isnull=False, log__period__code=period_code, id__gt=min_id, id__lt=max_id)
    # claims = Claim.objects.filter(event__isnull=False, log__period__code=period_code)

    for claim in claims:
        claim.save()
        

def import_national_conference_claims():
    """
    imports claims for the national conference
    """

    # there was a bug re-saving credit claims for national conference
    # must delete existing credit claims and reimport those for national conference

    Claim.objects.filter(event__master=3027311).delete()

    number_of_groups = 65
    
    for x in range(0, number_of_groups):
    
        claims = load_json(RESTIFY_SERVER_ADDRESS + '/cm/conference/claims/' + str(x))

        for credit_claim in claims['data']:
            claim_id = credit_claim['ClaimID']

            username = credit_claim.get('WebUserID')

            event_id = credit_claim.get('EventID', 0)
            activity_id = credit_claim.get('ActivityID', 0)
            comment = credit_claim.get('Comments', None)
            verified = credit_claim.get('ClaimIsVerified', False)
            is_speaker = credit_claim.get('IsSpeaker', False)
            is_author = credit_claim.get('IsAuthor', False)
            submitted_time = credit_claim.get('ClaimSubmittedDateTime')
            title = credit_claim.get('Logged_EventName', '') #?????
            rating = credit_claim.get('RatingStars', None)
            ad_hoc_id = credit_claim.get('AdHocID', 0)
            provider_name = credit_claim.get('COMPANY', 'CM_PROVIDER_TEST')
            title = credit_claim.get('Logged_EventName', '')
            claim_status = credit_claim.get('ClaimStatus', 'A')
            ad_hoc_id = credit_claim.get('AdHocID', None)
            is_self_reported = credit_claim.get('IsSelfReported', False)
            period_code = credit_claim.get('PeriodCode', '')
            master_id = credit_claim.get('MasterID')

            contact = Contact.objects.get(user__username = username)

            period = Period.objects.get(code=period_code)
            log = Log.objects.get(contact = contact, period = period)


            # if event or activity id is passed, get credit claim from those
            if credit_claim.get('UseOverrideCredits', False):   
                credits = credit_claim.get('Override_CreditApprovedNumber', 0)
                law_credits = credit_claim.get('Override_CreditLawApprovedNumber', 0)
                ethics_credits = credit_claim.get('Override_CreditEthicsApprovedNumber', 0)
            else:
                credits = credit_claim.get('CreditApprovedNumber', 0)
                law_credits = credit_claim.get('CreditLawApprovedNumber', 0)
                ethics_credits = credit_claim.get('CreditEthicsApprovedNumber', 0)

            event_id = master_id


            try:  
                event = Event.objects.get(master=event_id, publish_status='PUBLISHED')

                claim, created = Claim.objects.get_or_create(contact=contact, log = log, event=event)
                    
                claim.verified = verified 
                claim.is_speaker = is_speaker
                claim.is_author = is_author
                claim.self_reported = is_self_reported
                claim.submitted_time = submitted_time
                claim.provider_name = provider_name
                claim.title = title

                claim.credits = credits
                claim.law_credits = law_credits
                claim.ethics_credits = ethics_credits

                claim.save()
                
            except:
                print('error finding event..')
                pass
