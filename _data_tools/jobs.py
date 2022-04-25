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


# YET ANOTHER RANDOM COMMENT
from django.utils.text import slugify
from django.contrib.auth.models import User, Group, Permission
from django.contrib.sites.models import Site
from django.contrib.auth.hashers import is_password_usable
from django.core.mail import send_mail

from datetime import timedelta

from django.db.models import Q

from wagtail.wagtailcore.models import Page as WagtailPage, Site as WagtailSite, Collection as WagtailCollection
from wagtail.wagtailcore.models import GroupPagePermission, GroupCollectionPermission

from content.models import *
from myapa.models.contact_role import ContactRole
from store.models import *
from events.models import *
from media.models import *
from exam.models import *
from submissions.models import *
from jobs.models import *
from planning.settings import ENVIRONMENT_NAME, RESTIFY_SERVER_ADDRESS
from urllib.request import urlopen
from urllib import parse
from decimal import * 
from xml.dom import minidom

from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from io import BytesIO

# from publications.models import Book, EBook
from content.utils import generate_random_string

logger = logging.getLogger(__name__)

json_server='http://localhost:8081/dataimport';

node_url = "http://localhost:8081/dataimport/"


def import_jobs(start_job_id = 0):
    """
    import jobs
    """

    url = node_url + 'jobs/all/' + str(start_job_id)

    r = requests.get(url)

    jobs_import = r.json()['data']

    f = '%Y-%m-%d %H:%M:%S'

    job_import_errors = {}


    # all job product ids.... some do not match will be given archive job_type
    # 1000 - entry level 4 weeks online
    # 1001 entry level jobmartpost
    # 1002 - job online post 2 weeks online
    # 1003 - jobs online post 3 weeks online
    # 1004 - jobs online post 4 weeks online
    # 1007 - internship online post


    job_exerpeience_tag_type = TagType.objects.get(code="JOB_EXPERIENCE_LEVEL")
    tag_aicp_job_entry = Tag.objects.get(code="ENTRY")
    tag_aicp_job_mid_ii = Tag.objects.get(code="MID_II")
    tag_aicp_job_senior = Tag.objects.get(code="SENIOR")
    tag_aicp_job_executive = Tag.objects.get(code="EXECUTIVE")
    tag_aicp_job_mid_i = Tag.objects.get(code="MID_I")

    # job_category_tag_type = TagType.objects.get(code="JOB_CATEGORY")
    # do we need this since the categories have changed?? 

    job_aicp_level_tag_type = TagType.objects.get(code="AICP_LEVEL")
    tag_aicp_not_required = Tag.objects.get(code="NOT_REQUIRED")
    tag_aicp_desirable = Tag.objects.get(code="DESIRABLE")
    tag_aicp_preferred = Tag.objects.get(code="PREFERRED")
    tag_aicp_required = Tag.objects.get(code="REQUIRED")

    job_category_tag_type = TagType.objects.get(code="JOB_CATEGORY")
    tag_category_other = Tag.objects.filter(code="OTHER").first() #0
    tag_category_urban = Tag.objects.filter(code="URBAN_DESIGN").first() #2, 27
    tag_category_econ = Tag.objects.filter(code="ECON_PLAN").first() #4
    tag_category_land = Tag.objects.filter(code="LAND_USE_PLAN").first() #6
    tag_category_trans = Tag.objects.filter(code="TRANS_PLAN").first() #7
    tag_category_comp = Tag.objects.filter(code="COMPRE_PLAN").first() # 9, 21
    tag_category_community = Tag.objects.filter(code="COMM_DEV").first() #10
    tag_category_landscape = Tag.objects.filter(code="LANDSCAPE_ARCH").first() #12
    tag_category_resources = Tag.objects.filter(code="ENVIRON_NATRL_PLAN").first() # 13, 18
    tag_category_academic = Tag.objects.filter(code="ACADEMIA").first() #14
    tag_category_hist = Tag.objects.filter(code="HIST_PRESERVE").first() #19
    tag_category_housing = Tag.objects.filter(code="HOUSING").first() #20
    tag_category_management = Tag.objects.filter(code="PLAN_MGMT").first() #22
    tag_category_park = Tag.objects.filter(code="PARK_REC_PLAN").first() #24
    
    #create a generic job post for all other job imports 
    for job_import in jobs_import:
        try:
            legacy_id = job_import.get('AdID')
            status = job_import.get('AdStatus')
            title = job_import.get('AdTitle')
            text = job_import.get('AdText')
            if text:
                text = text.replace("\n", "<br/>")

            company = job_import.get('AdCompany')
            city = job_import.get('AdCity')
            state = job_import.get('AdStateProvince')
            salary_range = job_import.get('AdSalaryRange')
            show_contact_info = job_import.get('AdContactShowName')
            first_name = job_import.get('AdContactFirstName')
            last_name = job_import.get('AdContactLastName')
            email = job_import.get('AdContactEmail')
            phone = job_import.get('AdContactPhone')
            # how to do full address ??
            website = job_import.get('AdContactWebSite')
            user_id = job_import.get('WebUserID')
            post_start_date = job_import.get('PostingStartDate')
            post_end_date = job_import.get('PostingEndDate')
            specialty_code = job_import.get('_SpecialtyCode')
            product_id = job_import.get('TemporaryProductID')
            ad_created_time = job_import.get('AdCreatedDateTime')

            years_experience = job_import.get('_YearsExperienceTypeID')
            experience_type = job_import.get('_ExperienceTypeID')
            aicp_level = job_import.get('_AICPTypeID')
            job_category = job_import.get('_JobCategoryTypeID')
            contact = Contact.objects.get(user__username=str(user_id))
            job_type = "ARCHIVE"

            if not show_contact_info:
                show_contact_info = False
                
            if product_id == 1004:
                job_type = "PROFESSIONAL_4_WEEKS"
            elif product_id == 1002:
                job_type = "PROFESSIONAL_2_WEEKS"
            elif product_id == 1007:
                job_type = "INTERN"
            elif product_id == 1000:
                job_type = "ENTRY_LEVEL"

            #years_experience = None

            job, created = Job.objects.get_or_create(legacy_id = legacy_id, job_type = job_type, publish_status="SUBMISSION")

            contactrole, created = ContactRole.objects.get_or_create(contact=contact, content=job, role_type="AUTHOR")
            job.title = title
            job.display_contact_info = show_contact_info
            if salary_range:
                job.salary_range = salary_range[:49]
            job.company = company
            job.city = city
            job.state = state
            job.text = text
            job.contact_us_first_name = first_name
            job.contact_us_last_name = last_name
            job.contact_us_email = email
            if phone:
                job.contact_us_phone = phone[:19]
            job.status = status
            job.resource_url = website

            content_tag_type_experience, created = ContentTagType.objects.get_or_create(content=job, tag_type=job_exerpeience_tag_type, publish_status="SUBMISSION")
            if years_experience:
                if years_experience in [2,3,4]:
                    content_tag_type_experience.tags.add(tag_aicp_job_entry)
                    content_tag_type_experience.save()
                elif years_experience in [5,6,7]: #note 7 falls in between the new categories!!
                    content_tag_type_experience.tags.add(tag_aicp_job_mid_i)
                    content_tag_type_experience.save()             
                elif years_experience in [8]: #note 7 falls in between the new categories!!
                    content_tag_type_experience.tags.add(tag_aicp_job_mid_ii)
                    content_tag_type_experience.save()  
                elif years_experience in [9]: #note 7 falls in between the new categories!!
                    content_tag_type_experience.tags.add(tag_aicp_job_senior)
                    content_tag_type_experience.save()  
                elif years_experience in [10]:
                    content_tag_type_experience.tags.add(tag_aicp_job_executive)
                    content_tag_type_experience.save() 

            content_tag_type_aicp, created = ContentTagType.objects.get_or_create(content=job, tag_type=job_aicp_level_tag_type, publish_status="SUBMISSION")
            if aicp_level:
                if str(aicp_level) == "1":
                    content_tag_type_aicp.tags.add(tag_aicp_not_required)
                    content_tag_type_aicp.save()
                elif str(aicp_level) == "4": #note 7 falls in between the new categories!!
                    content_tag_type_aicp.tags.add(tag_aicp_desirable)
                    content_tag_type_aicp.save()             
                elif str(aicp_level) == "3": #note 7 falls in between the new categories!!
                    content_tag_type_aicp.tags.add(tag_aicp_preferred)
                    content_tag_type_aicp.save()  
                elif str(aicp_level) == "2": #note 7 falls in between the new categories!!
                    content_tag_type_aicp.tags.add(tag_aicp_required)
                    content_tag_type_aicp.save() 

            content_tag_type_category, created = ContentTagType.objects.get_or_create(content=job, tag_type=job_category_tag_type, publish_status="SUBMISSION")
            if job_category == 0 or job_category:
                print('this has a job category: ' + str(job_category))
                if job_category == 0:
                    print("this job category matches 0")
                    content_tag_type_category.tags.add(tag_category_other)
                    content_tag_type_category.save()
                elif job_category in [2,27]: 
                    content_tag_type_category.tags.add(tag_category_urban)
                    content_tag_type_category.save()
                elif job_category in [4]: 
                    content_tag_type_category.tags.add(tag_category_econ)
                    content_tag_type_category.save()   
                elif job_category in [6]: 
                    content_tag_type_category.tags.add(tag_category_land)
                    content_tag_type_category.save()   
                elif job_category in [7]: 
                    content_tag_type_category.tags.add(tag_category_trans)
                    content_tag_type_category.save()   
                elif job_category in [9,21]: 
                    content_tag_type_category.tags.add(tag_category_comp)
                    content_tag_type_category.save()   
                elif job_category in [10]: 
                    content_tag_type_category.tags.add(tag_category_community)
                    content_tag_type_category.save()   
                elif job_category in [12]: 
                    content_tag_type_category.tags.add(tag_category_landscape)
                    content_tag_type_category.save()   
                elif job_category in [13,18]: 
                    content_tag_type_category.tags.add(tag_category_resources)
                    content_tag_type_category.save()   
                elif job_category in [14]: 
                    content_tag_type_category.tags.add(tag_category_academic)
                    content_tag_type_category.save()   
                elif job_category in [19]: 
                    content_tag_type_category.tags.add(tag_category_hist)
                    content_tag_type_category.save()   
                elif job_category in [20]: 
                    content_tag_type_category.tags.add(tag_category_housing)
                    content_tag_type_category.save()   
                elif job_category in [22]: 
                    content_tag_type_category.tags.add(tag_category_management)
                    content_tag_type_category.save()   
                elif job_category in [24]: 
                    content_tag_type_category.tags.add(tag_category_park)
                    content_tag_type_category.save()   

            if post_start_date:
                post_time_converted = datetime.strptime(post_start_date, f)
            else:
                post_time_converted = None

            if post_end_date:
                post_end_time_converted = datetime.strptime(post_end_date, f)
            else:
                post_end_time_converted = None
            created_time_converted = datetime.strptime(ad_created_time, f)

            # additional check for ad tags for current 
            url = node_url + 'jobs/tags/' + str(legacy_id)

            r = requests.get(url)

            job_tags = r.json()['data']

            for job_tag in job_tags:
                tag_type_code = job_tag.get('TagTypeCode')
                tag_id = job_tag.get('TagID')

                if tag_type_code == 'JOBS_AICPSTATUS':
                    if str(tag_id) == "230":
                        content_tag_type_aicp.tags.add(tag_aicp_not_required)
                        content_tag_type_aicp.save()
                    elif str(tag_id) == "231": #note 7 falls in between the new categories!!
                        content_tag_type_aicp.tags.add(tag_aicp_desirable)
                        content_tag_type_aicp.save()             
                    elif str(tag_id) == "232": #note 7 falls in between the new categories!!
                        content_tag_type_aicp.tags.add(tag_aicp_preferred)
                        content_tag_type_aicp.save()  
                    elif str(tag_id) == "234": #note 7 falls in between the new categories!!
                        content_tag_type_aicp.tags.add(tag_aicp_required)
                        content_tag_type_aicp.save() 

                if tag_type_code == "JOBS_EXPERIENCELEVEL":
                    if tag_id in [235,236]:
                        content_tag_type_experience.tags.add(tag_aicp_job_entry)
                        content_tag_type_experience.save()
                    elif tag_id in [237]: #note 7 falls in between the new categories!!
                        content_tag_type_experience.tags.add(tag_aicp_job_mid_i)
                        content_tag_type_experience.save()             
                    elif tag_id in [238]: #note 7 falls in between the new categories!!
                        content_tag_type_experience.tags.add(tag_aicp_job_mid_ii)
                        content_tag_type_experience.save()  
                    elif tag_id in [239]: #note 7 falls in between the new categories!!
                        content_tag_type_experience.tags.add(tag_aicp_job_senior)
                        content_tag_type_experience.save()  
                    elif tag_id in [240]:
                        content_tag_type_experience.tags.add(tag_aicp_job_executive)
                        content_tag_type_experience.save()

                if tag_type_code == "SPECIALTY":
                    if tag_id == 117:
                        content_tag_type_category.tags.add(tag_category_other)
                        content_tag_type_category.save()
                    elif tag_id in [109]: 
                        content_tag_type_category.tags.add(tag_category_urban)
                        content_tag_type_category.save()
                    elif tag_id in [103]: 
                        content_tag_type_category.tags.add(tag_category_econ)
                        content_tag_type_category.save()   
                    elif tag_id in [112]: 
                        content_tag_type_category.tags.add(tag_category_land)
                        content_tag_type_category.save()   
                    elif tag_id in [105]: 
                        content_tag_type_category.tags.add(tag_category_trans)
                        content_tag_type_category.save()   
                    # elif tag_id in [102]: 
                    #     content_tag_type_category.tags.add(tag_category_comp)
                    #     content_tag_type_category.save()   
                    elif tag_id in [102]: 
                        content_tag_type_category.tags.add(tag_category_community)
                        content_tag_type_category.save()   
                    # elif tag_id in [12]: 
                    #     content_tag_type_category.tags.add(tag_category_landscape)
                    #     content_tag_type_category.save()   
                    elif tag_id in [104]: 
                        content_tag_type_category.tags.add(tag_category_resources)
                        content_tag_type_category.save()   
                    # elif tag_id in [14]: 
                    #     content_tag_type_category.tags.add(tag_category_academic)
                    #     content_tag_type_category.save()   
                    # elif tag_id in [19]: 
                    #     content_tag_type_category.tags.add(tag_category_hist)
                    #     content_tag_type_category.save()   
                    elif tag_id in [107]: 
                        content_tag_type_category.tags.add(tag_category_housing)
                        content_tag_type_category.save()   
                    # elif tag_id in [22]: 
                    #     content_tag_type_category.tags.add(tag_category_management)
                    #     content_tag_type_category.save()   
                    elif tag_id in [11]: 
                        content_tag_type_category.tags.add(tag_category_park)
                        content_tag_type_category.save()   

            if datetime.now() > post_end_time_converted:
                job.status = "I"

            job.post_time = post_time_converted
            job.created_time = created_time_converted
            job.make_inactive_time = post_end_time_converted
            job.save()

            super(Job, job).publish(publish_type="DRAFT")
            published_job = super(Job, job).publish(publish_type="PUBLISHED")

            published_job.solr_publish()



                #job = Job.objects.get()
                
            print('Success! import job id: ' + str(legacy_id))

        except Exception as e:
            job_import_errors[legacy_id] = str(e)
            print('error importing job: '+ str(legacy_id) + " || " + str(e))
            continue

    print(job_import_errors)
    
        # class Job(Content, BaseAddress):
        # post_time = models.DateTimeField(blank=True, null=True)


# ***** ACTUALLY USE: myapa/models -> CHAPTER_CHOICES

# these lists come from Organizations:
chapter_titles ="""APA Alabama Chapter
APA Alaska Chapter
APA Arizona Chapter
APA Arkansas Chapter
APA California Chapter
APA California Chapter, Central Coast Section
APA California Chapter, Inland Empire Section
APA California Chapter, Los Angeles Section
APA California Chapter, Northern Section
APA California Chapter, Orange Section
APA California Chapter, Sacramento Valley Section
APA California Chapter, San Diego Section
APA Colorado Chapter
APA Connecticut Chapter
APA Delaware Chapter
APA Florida Chapter
APA Florida Chapter, Broward Section
APA Florida Chapter, Emerald Coast Section
APA Florida Chapter, First Coast Section
APA Florida Chapter, Gold Coast Section
APA Florida Chapter, Heart of Florida Section
APA Florida Chapter, Orlando Metro Section
APA Florida Chapter, Promised Lands Section
APA Florida Chapter, Suncoast Section
APA Georgia Chapter
APA Hawaii Chapter
APA Idaho Chapter
APA Illinois Chapter
APA Indiana Chapter
APA Iowa Chapter
APA Kansas Chapter
APA Kentucky Chapter
APA Louisiana Chapter
APA Maryland Chapter
APA Massachusetts Chapter
APA Michigan Chapter
APA Minnesota Chapter
APA Mississippi Chapter
APA Missouri Chapter
APA National Capital Area Chapter
APA Nebraska Chapter
APA Nevada Chapter
APA New Jersey Chapter
APA New Mexico Chapter
APA New York Metro Chapter
APA New York Upstate Chapter
APA North Carolina Chapter
APA Northern New England Chapter
APA Ohio Chapter
APA Oklahoma Chapter
APA Oregon Chapter
APA Pennsylvania Chapter
APA Rhode Island Chapter
APA South Carolina Chapter
APA Tennessee Chapter
APA Texas Chapter
APA Texas Chapter, Central Section
APA Texas Chapter, Midwest Section
APA Texas Chapter, North Central Section
APA Texas Chapter, Northwest Section
APA Texas Chapter, San Antonio Section
APA Texas Chapter, Southmost Section
APA Texas Chapter, Southwest Section
APA Texas Chapter, West Section
APA Utah Chapter
APA Virginia Chapter 
APA Washington Chapter
APA Western Central Chapter
APA West Virginia Chapter
APA Wisconsin Chapter"""

chapter_abbrevs="""AK
AL
AZ
AR
CA
CA_CC
CA_IE
CA_LA
CA_N
CA_O
CA_SV
CA_SD
CO
CT
DE
FL
FL_B
FL_EC
FL_FC
FL_GC
FL_HF
FL_OM
FL_PL
FL_SS
GA
HI
ID
IL
IN
IA
KS
KY
LA
MD
MA
MI
MN
MS
MO
NCA
NE
NV
NJ
NM
NY_M
NY_U
NC
NNE
OH
OK
OR
PA
RI
SC
TN
TX
TX_C
TX_M
TX_NC
TX_NW
TX_SA
TX_SM
TX_SW
TX_W
UT
VA
WA
WC
WV
WI"""



# Instead get data from chapter membership products:
# DUPLICATE CA CENTRAL COAST AND CA CENTRAL ??

chapter_abbrevs_products="""AL
AK
AZ
AR
CA_CC
CA_C
CA_IE
CA_LA
CA_N
CA_O
CA_SV
CA_SD
CO
CT
DE
FL
GA
HI
ID
IL
IN
IA
KS
KY
LA
MD
MA
MI
MN
MS
MO
NCA
NE
NV
NJ
NM
NY_M
NY_U
NC
NNE
OH
OK
OR
PA
RI
SC
TN
TX
UT
VA
WA
WC
WV
WI"""

# for now we don't need this -- can just use the preexisting product prices
# APA jobs price data:
apa_price_titles="""Professional (various levels of experience) - 4 weeks online
Professional (various levels of experience) - 2 weeks online
Entry Level only (zero to one year of experience) - 4 weeks online
Internship only (temporary position; no experience required) - 4 weeks online"""

apa_job_price_codes="""PROFESSIONAL_4_WEEKS
PROFESSIONAL_2_WEEKS
ENTRY_LEVEL
INTERN"""

apa_job_prices = [Decimal('295.00'), Decimal('195.00'), Decimal('50.00'), Decimal('0.00')]

# Chapter Jobs Price DAta:
price_titles="""Professional (various levels of experience) - 4 weeks online
Professional (various levels of experience) - 4 weeks online
Professional (various levels of experience) - 4 weeks online
Professional (various levels of experience) - 4 weeks online
Professional (various levels of experience) - 2 weeks online
Professional (various levels of experience) - 2 weeks online
Professional (various levels of experience) - 2 weeks online
Entry Level only (zero to one year of experience; not AICP) - 4 weeks online
Entry Level only (zero to one year of experience; not AICP) - 4 weeks online
Internship only (temporary position; no experience required) - 4 weeks online"""

job_price_codes="""PROFESSIONAL_4_WEEKS_100
PROFESSIONAL_4_WEEKS_75
PROFESSIONAL_4_WEEKS_50
PROFESSIONAL_4_WEEKS_0
PROFESSIONAL_2_WEEKS_75
PROFESSIONAL_2_WEEKS_50
PROFESSIONAL_2_WEEKS_0
ENTRY_LEVEL_50
ENTRY_LEVEL_0
INTERN_0"""

job_prices = [
    Decimal('100.00'), Decimal('75.00'), Decimal('50.00'), Decimal('0.00'),
    Decimal('75.00'), Decimal('50.00'), Decimal('0.00'),
    Decimal('50.00'), Decimal('0.00'), Decimal('0.00'),
    ]

def create_chapter_titles():
    title_string = ''
    ps=Product.objects.filter(product_type='CHAPTER', publish_status='PUBLISHED').order_by("title")

    for p in ps:
        if title_string == '':
            title_string = title_string + p.title
        else:
            title_string = title_string + '\n' + p.title

    titles=title_string.split('\n')
    # codes = []

    # for chap in chaps:
    #     codes.append("JOB_AD_" + chap)

    return titles

def create_division_titles():
    title_string = ''
    # dvs=Product.objects.filter(product_type='DIVISION', publish_status='PUBLISHED').order_by("title")
    dvs=Contact.objects.filter(member_type="DVN") #.order_by("title")

    for dv in dvs:
        if title_string == '':
            title_string = title_string + dv.title
        else:
            title_string = title_string + '\n' + dv.title

    titles=title_string.split('\n')

    return titles

def create_job_codes(chap_abbrevs=None):
    chaps=chap_abbrevs.split('\n')
    codes = []

    for chap in chaps:
        codes.append("JOB_AD_" + chap)

    return codes

def create_job_titles():
    # chaps=chapter_titles.split('\n')
    chaps = create_chapter_titles()
    titles = []

    for chap in chaps:
        titles.append("Job Ad, " + chap)

    return titles

def create_job_gls():
    chaps=chapter_abbrevs.split('\n')
    gls = []
    gls_start = 4067

    for chap in chaps:
        gls_start+=1
        gls.append("460100-MN" + str(gls_start))

    return gls

def create_job_price_tuples():
    titles = price_titles.split('\n')
    codes = job_price_codes.split('\n')
    job_tuples = []

    for i in range(0, len(titles)):
        job_tuples.append((titles[i],codes[i],job_prices[i]))

    return job_tuples

# all codes same, except for product price code
# content product: title=title, description=title, code=code
# product: code=code, product_type='JOB_AD', imis_code=code, gl_account=gl, max_quantity=Decimal('1.00')
# product price: title, price, priority, code // for now just query for preexisting product prices for jobs

# *** will also have to be published ***
def create_chapter_job_products(codes_list=[], titles_list=[]):
    if codes_list:
        codes = codes_list
    else:
        codes = create_job_codes(chapter_abbrevs_products)
    if titles_list:
        titles = titles_list
    else:
        titles = create_job_titles()
    gls = create_job_gls()
    jp_tuples = create_job_price_tuples()

    for i in range(0, len(codes)):
        print("i is ", i)
        cjcp, cjcp_created = ContentProduct.objects.get_or_create(title=titles[i], description=titles[i], code=codes[i])
        cjp, cjp_created = Product.objects.get_or_create(
            code=codes[i], content=cjcp, product_type='JOB_AD', imis_code=codes[i], gl_account=gls[i], max_quantity=Decimal('1.00'))

        for i, toop in enumerate(jp_tuples):
            prod_price, prod_price_created = ProductPrice.objects.get_or_create(
                title=toop[0], code=toop[1], price=toop[2], product=cjp, priority=i)
        # cpj.publish()

def delete_chapter_job_products(codes_list=[]):
    if codes_list:
        codes = codes_list
    else:
        codes = create_job_codes(chapter_abbrevs)
    print("codes is ", codes)
    print("len codes is ", len(codes))

    for i in range(0, len(codes)):
        queryset = ContentProduct.objects.filter(code=codes[i])
        print("i is ", i)
        print("queryset is ", queryset)
        num_objs_deleted, num_deletions_per_obj_dict = queryset.delete()
        print("code is ", codes[i])
        print("num_objs_deleted is ", num_objs_deleted)
        print("num_deletions_per_obj_dict is ", num_deletions_per_obj_dict)
        print()

# ALSO HAVE TO CREATE THE SUBMISSION CATEGORIES AND PERIODS FOR EVERY CHAPTER JOB PRODUCT

def create_chapter_job_categories(chap_job_products=[]):
    if not chap_job_products:
        codes = create_job_codes(chapter_abbrevs_products)
        chap_job_products = Product.objects.filter(
            publish_status='PUBLISHED', code__in=codes)
    for prod in chap_job_products:
        new_cat, created = Category.objects.get_or_create(
            code=prod.code,
            title=prod.content.title,
            product_master=prod.content.master,
            description=prod.content.title,
            )
        jun_1_2017 = datetime.datetime(year=2017, month=6, day=1)
        jun_1_2018 = datetime.datetime(year=2018, month=6, day=1)
        new_per, created = Period.objects.get_or_create(
            title=prod.content.title,
            content_type='JOB',
            begin_time=jun_1_2017,
            end_time=jun_1_2018,
            category=new_cat
            )
        print("category, created: ", new_cat, created)
        print("period, created: ", new_per, created)

def delete_chapter_job_categories(cats=[]):
    pass

def create_sites_config_dicts():
    sites_dict = {}
    urls = create_hosts_urls()
    logo_key = "logo_block"
    logo_sig_key = "logo_signature"
    uname_key = "username"
    for url in urls:
        s = url.replace("local-development.", "")
        name = s.replace(".planning.org", "")
        print("name is ", name)
        print()
        sites_dict[url] = {
        "logo_block": "component-sites/image/" + name + "/logo.svg",
        "logo_signature":"component-sites/image/" + name + "/signature.svg",
        "username": "",
        "color": "R, G, B",
        "jobs_product_code": "JOB_AD_" + name
        }
    return sites_dict

chapter_subs=[
'alabama',
 'alaska',
 'arizona',
 'arkansas',
 'california.central.coast',
 'california.central',
 'california.inland.empire',
 'california.los.angeles',
 'california.northern',
 'california.orange',
 'california.sacramento.valley',
 'california.san.diego',
 'colorado',
 'connecticut',
 'delaware',
 'florida',
 'georgia',
 'hawaii',
 'idaho',
 'illinois',
 'indiana',
 'iowa',
 'kansas',
 'kentucky',
 'louisiana',
 'maryland',
 'massachusetts',
 'michigan',
 'minnesota',
 'mississippi',
 'missouri',
 'national.capital',
 'nebraska',
 'nevada',
 'new.jersey',
 'new.mexico',
 'new.york.metro',
 'new.york.upstate',
 'north.carolina',
 'northern.new.england',
 'ohio',
 'oklahoma',
 'oregon',
 'pennsylvania',
 'rhode.island',
 'south.carolina',
 'tennessee',
 'texas',
 'utah',
 'virginia',
 'washington',
 'western.central',
 'west.virginia',
 'wisconsin']

division_subs=[
'county',
 'law',
 'housing',
 'indigenous',
 'rural',
 'women',
 'federal',
 'urbanism',
 'wippolt',
 'environment',
 'city',
 'tourism',
 'international',
 'privatepractice',
 'technology'
 'transportation',
 'latinos',
 'economic',
 'intergovernmental',
 'blackcommunity',
 'gayslesbians',
 'urbandesign']

def create_local_hosts_urls():
    # chap_subs = chapter_subs.split("\n")
    # div_subs = division_subs.split("\n")
    urls = []
    # division_subs.sort()
    for chap in chapter_subs:
        urls.append("local-development-" + chap + ".planning.org")
    for div in division_subs:
        urls.append("local-development-" + div + ".planning.org")
    return urls

def create_staging_hosts_urls():
    # chap_subs = chapter_subs.split("\n")
    # div_subs = division_subs.split("\n")
    urls = []
    # division_subs.sort()
    for chap in chapter_subs:
        urls.append("staging-" + chap + ".planning.org")
    for div in division_subs:
        urls.append("staging-" + div + ".planning.org")
    return urls

def create_prod_hosts_urls():
    # chap_subs = chapter_subs.split("\n")
    # div_subs = division_subs.split("\n")
    urls = []
    # division_subs.sort()
    for chap in chapter_subs:
        urls.append(chap + ".planning.org")
    for div in division_subs:
        urls.append(div + ".planning.org")
    return urls

LOCAL_DOMAIN_NAMES = [
    "virginia-local-development.planning.org",
    "wisconsin-local-development.planning.org",
    "missouri-local-development.planning.org",
    "ct-local-development.planning.org",
    "wcc-local-development.planning.org",
    "florida-local-development.planning.org",
    "hawaii-local-development.planning.org",
    "california-local-development.planning.org",
    "arizona-local-development.planning.org",
    "tennessee-local-development.planning.org",
    "ncac-local-development.planning.org",
    "nne-local-development.planning.org",
    "texas-local-development.planning.org",
    "kansas-local-development.planning.org",
    "iowa-local-development.planning.org",
    "urbandesign-local-development.planning.org",
    "transportation-local-development.planning.org",
    "housing-local-development.planning.org",
    "blackcommunity-local-development.planning.org",
    "women-local-development.planning.org",
    "city-local-development.planning.org",
    "privatepractice-local-development.planning.org",
    "tech-local-development.planning.org",

]

STAGING_DOMAIN_NAMES = [
    "virginia-staging.planning.org",
    "wisconsin-staging.planning.org",
    "missouri-staging.planning.org",
    "ct-staging.planning.org",
    "wcc-staging.planning.org",
    "florida-staging.planning.org",
    "hawaii-staging.planning.org",
    "california-staging.planning.org",
    "arizona-staging.planning.org",
    "tennessee-staging.planning.org",
    "ncac-staging.planning.org",
    "nne-staging.planning.org",
    "texas-staging.planning.org",
    "kansas-staging.planning.org",
    "iowa-staging.planning.org",
    "urbandesign-staging.planning.org",
    "transportation-staging.planning.org",
    "housing-staging.planning.org",
    "blackcommunity-staging.planning.org",
    "women-staging.planning.org",
    "city-staging.planning.org",
    "privatepractice-staging.planning.org",
    "tech-staging.planning.org",

]

PROD_DOMAIN_NAMES = [
    "virginia.planning.org",
    "wisconsin.planning.org",
    "missouri.planning.org",
    "ct.planning.org",
    "wcc.planning.org",
    "florida.planning.org",
    "hawaii.planning.org",
    "california.planning.org",
    "arizona.planning.org",
    "tennessee.planning.org",
    "ncac.planning.org",
    "nne.planning.org",
    "texas.planning.org",
    "kansas.planning.org",
    "iowa.planning.org",
    "urbandesign.planning.org",
    "transportation.planning.org",
    "housing.planning.org",
    "blackcommunity.planning.org",
    "women.planning.org",
    "city.planning.org",
    "privatepractice.planning.org",
    "tech.planning.org",

]

# small town is duplicated so there are two "small town" titles
def create_django_sites(urls):
    # urls = create_hosts_urls()
    # names = create_chapter_titles() + create_division_titles()
    # names.remove('Small Town and Rural Planning Division APA')
    for url in urls:
        print(url)
        print()
    # for name in names:
    #     print(name)
    for i in range(0, len(urls)):
        # Site.get_or_create(name=names[i], url=urls[i])
        Site.objects.get_or_create(name=urls[i], domain=urls[i])
        print("name is %s, url is %s" % (urls[i], urls[i]))
        print()

chap_keywords = [
    "Virginia",
    "Wisconsin",
    "Missouri",
    "Connecticut",
    "Western Central",
    "Florida",
    "Hawai‘i",
    "California",
    "Arizona",
    "Tennessee",
    "National Capital Area",
    "Northern New England",
    "Texas",
    "Kansas",
    "Iowa",
]
div_keywords = [
    "Urban Design",
    "Transportation",
    "Housing",
    "Black Community",
    "Women",
    "City Planning",
    "Private Practice",
    "Technology",
]

component_data = [
("CHAPT_VA-admin","Virginia"),
("CHAPT_WI-admin","Wisconsin"),
("CHAPT_MO-admin","Missouri"),
("CHAPT_CT-admin","Connecticut"),
("CHAPT_WCC-admin","Western Central"),
("CHAPT_FL-admin","Florida"),
("CHAPT_HI-admin","Hawai‘i"),
("CHAPT_CA-admin","California"),
("CHAPT_AZ-admin","Arizona"),
("CHAPT_TN-admin","Tennessee"),
("CHAPT_NCAC-admin","National Capital Area"),
("CHAPT_NNE-admin","Northern New England"),
("CHAPT_TX-admin","Texas"),
("CHAPT_KS-admin","Kansas"),
("CHAPT_IA-admin","Iowa"),

("BLACK-admin","Black Community"),
("CITY_PLAN-admin","City Planning"),
("HOUSING-admin","Housing"),
("PRIVATE-admin","Private Practice"),
("TECH-admin","Technology"),
("TRANS-admin","Transportation"),
("URBAN_DES-admin","Urban Design"),
("WOMEN-admin","Women"),
]

# TO CREATE WAGTAIL SITES YOU NEED TO IMPORT THE Site model as Wagtail_Site
# and you must point the site to a root page during create -- and you must import 
# Wagtail Page as Wagtail_Page

def create_wagtail_sites(hostnames, is_local=False, chap_keywords=chap_keywords, div_keywords=div_keywords):
    from wagtail.wagtailcore.models import Page as Wagtail_Page
    from wagtail.wagtailcore.models import Site as Wagtail_Site
    from component_sites.models import ChapterHomePage, DivisionHomePage
    port = 80 if not is_local else 8000
    root_page = Wagtail_Page.objects.get(title='Root')

    # chapters
    vc=ChapterHomePage.objects.filter(title__contains="Virginia").first()
    wc=ChapterHomePage.objects.filter(title__contains="Wisconsin").first()
    mc=ChapterHomePage.objects.filter(title__contains="Missouri").first()
    ct=ChapterHomePage.objects.filter(title__contains="Connecticut").first()
    wcc=ChapterHomePage.objects.filter(title__contains="Western Central").first()
    fl=ChapterHomePage.objects.filter(title__contains="Florida").first()
    hi=ChapterHomePage.objects.filter(title__contains="Hawai‘i").first()
    ca=ChapterHomePage.objects.filter(title__contains="California").first()
    az=ChapterHomePage.objects.filter(title__contains="Arizona").first()
    tn=ChapterHomePage.objects.filter(title__contains="Tennessee").first()
    ncac = ChapterHomePage.objects.filter(title__contains="National Capital Area").first()
    nne=ChapterHomePage.objects.filter(title__contains="Northern New England").first()
    tx=ChapterHomePage.objects.filter(title__contains="Texas").first()
    ks=ChapterHomePage.objects.filter(title__contains="Kansas").first()
    ia = ChapterHomePage.objects.filter(title__contains="Iowa").first()
    # hostname, sitename, root_page, *and port for local
    chaps = [vc, wc, mc, ct, wcc, fl, hi, ca, az, tn, nne, ncac, tx, ks, ia]
    # divisions
    ud = DivisionHomePage.objects.filter(title__contains="Urban Design").first()
    td = DivisionHomePage.objects.filter(title__contains="Transportation").first()
    hd = DivisionHomePage.objects.filter(title__contains="Housing").first()
    bc = DivisionHomePage.objects.filter(title__contains="Black Community").first()
    wom = DivisionHomePage.objects.filter(title__contains="Women").first()
    cp = DivisionHomePage.objects.filter(title__contains="City Planning").first()
    pp = DivisionHomePage.objects.filter(title__contains="Private Practice").first()
    tech = DivisionHomePage.objects.filter(title__contains="Technology").first()
    divs = [ud, td, hd, bc, wom, cp, pp, tech]

    for i, chap in enumerate(chaps):
        if not chap:
            new_page = ChapterHomePage()
            new_page.title = "Welcome to APA " + chap_keywords[i]
            new_page.slug = slugify(new_page.title)
            page = root_page.add_child(instance=new_page)

    for i, div in enumerate(divs):
        if not div:
            new_page = DivisionHomePage()
            new_page.title = "APA " + div_keywords[i] + " Division"
            new_page.slug = slugify(new_page.title)
            page = root_page.add_child(instance=new_page)

    # chapters
    vc=ChapterHomePage.objects.get(title__contains="Virginia")
    wc=ChapterHomePage.objects.get(title__contains="Wisconsin")
    mc=ChapterHomePage.objects.get(title__contains="Missouri")
    ct=ChapterHomePage.objects.get(title__contains="Connecticut")
    wcc=ChapterHomePage.objects.get(title__contains="Western Central")
    fl=ChapterHomePage.objects.get(title__contains="Florida")
    hi=ChapterHomePage.objects.get(title__contains="Hawai‘i")
    ca=ChapterHomePage.objects.get(title__contains="California")
    az=ChapterHomePage.objects.get(title__contains="Arizona")
    tn=ChapterHomePage.objects.get(title__contains="Tennessee")
    ncac = ChapterHomePage.objects.get(title__contains="National Capital Area")
    nne=ChapterHomePage.objects.get(title__contains="Northern New England")
    ks = ChapterHomePage.objects.get(title__contains="Kansas")
    ia = ChapterHomePage.objects.get(title__contains="Iowa")
    # hostname, sitename, root_page, *and port for local

    # divisions
    ud = DivisionHomePage.objects.get(title__contains="Urban Design")
    td = DivisionHomePage.objects.get(title__contains="Transportation")
    hd = DivisionHomePage.objects.get(title__contains="Housing")
    bc = DivisionHomePage.objects.get(title__contains="Black Community")
    wom = DivisionHomePage.objects.get(title__contains="Women")
    cp = DivisionHomePage.objects.get(title__contains="City Planning")
    pp = DivisionHomePage.objects.get(title__contains="Private Practice")
    tech = DivisionHomePage.objects.get(title__contains="Technology")

    comps = [vc, wc, mc, ct, wcc, fl, hi, ca, az, tn, nne, ncac, tx, ks, ia,
        ud, td, hd, bc, wom, cp, pp, tech]

    i=-1
    for comp in comps:
        i+=1
        ws, created = Wagtail_Site.objects.get_or_create(root_page_id=comp.id,
            hostname=hostnames[i], port=port)
        if created:
            print("ws was created: ", ws)
            ws.site_name=hostnames[i]
            # ws.port=port
            ws.save()
        else:
            print("ws was not created: ", ws)

def delete_wagtail_sites(hostnames, is_local=False, chap_keywords=chap_keywords, div_keywords=div_keywords):
    from wagtail.wagtailcore.models import Page as Wagtail_Page
    from wagtail.wagtailcore.models import Site as Wagtail_Site
    from component_sites.models import ChapterHomePage, DivisionHomePage
    port = 80 if not is_local else 8000
    root_page = Wagtail_Page.objects.get(title='Root')
    # chapters
    for site in Wagtail_Site.objects.all():
        site.delete()


# NEED ANOTHER SCRIPT TO DELETE THE PROD DJANGO/WAGTAIL SITES on local/staging (only sites, not home pages)

# SCRIPT TO CREATE LANDING PAGES ?? ( i never had to do this before, so wait on this)

# ALSO SCRIPT TO SET UP WAGTAIL PERMISSIONS ON EACH GROUP -- ALWAYS ALMOST THE SAME FOR EACH GROUP
# https://stackoverflow.com/questions/43095869/how-to-modify-wagtail-cms-so-that-any-user-can-post-blog-posts-under-their-own-b#43103642
# you will assign wagtail permission objects to the Django group -- or to a group that inherits from Django group??

# g=Group.objects.filter(name__contains="VA-admin").first()
# pp=g.page_permissions.all()[23]
# p=g.permissions.first()

# check my early emacs code for how to add permissions to groups programmatically

# PERMISSIONS TO ADD FOR INDIVIDUAL ADMIN GROUPS
# Can access wagtail admin
# home pages: edit, publish, lock
# other pages: add, edit, publish, lock
# CREATE COLLECTION -- resources collection for component
# https://stackoverflow.com/questions/43178845/create-collection-with-python-code
# document permissions - component resources collection: add, edit
# image permissions -- same component resources collection: add, edit

# ALSO NEED TO ADD PERMISSIONS ON THE COMPONENT_ADMIN GROUP - (GENERAL WAGTAIL admin)
# THIS GROUP IS NOW CALLED wagtail-admin


def create_collection_names(chap_keywords=chap_keywords, div_keywords=div_keywords):
    pass
    col_names = []
    for chap_keyword in chap_keywords:
        col_names.append(chap_keyword + " Chapter Resources Collection")
    for div_keyword in div_keywords:
        col_names.append(div_keyword + " Division Resources Collection")
    return col_names

COLLECTION_NAMES = create_collection_names()


def create_wagtail_collections(COLLECTION_NAMES=COLLECTION_NAMES):
    from wagtail.wagtailcore.models import Collection as WagtailCollection
    root_coll = WagtailCollection.get_first_root_node()

    for name in COLLECTION_NAMES:
        if not WagtailCollection.objects.filter(name=name).first():
            root_coll.add_child(name=name)

# tps = test permissions
def tps():
    vg=Group.objects.filter(name__contains="VA-admin").first()
    vpps=vg.page_permissions.all()
    vp=vg.permissions.first()
    udg = Group.objects.filter(name__contains="DES-admin").first()
    upps = udg.page_permissions.all()
    up = udg.permissions.first()
    print(vp)
    print(vp.__dict__)
    print()
    print(up)
    print(up.__dict__)


# aps = add permmissions
# comp_data = component data (see global above)
def aps(comp_data=None):
    from wagtail.wagtailcore.models import Page as Wagtail_Page
    from wagtail.wagtailcore.models import Site as Wagtail_Site
    from component_sites.models import ChapterHomePage, DivisionHomePage    

    # cag = component_admin_group = Group.objects.get(name="COMPONENT_ADMIN")
    cag = component_admin_group = Group.objects.get(name="wagtail-admin")

    # Django permissions -- only one: 'Can access Wagtail admin' already exists
    wap = wagtail_admin_permission = Permission.objects.get(name='Can access Wagtail admin')
    arps = add_redirect_perms = Permission.objects.filter(name='Can add redirect')
    crps = change_redirect_perms = Permission.objects.filter(name='Can change redirect')
    drps = delete_redirect_perms = Permission.objects.filter(name='Can delete redirect')

    for arp in arps:
        if arp.natural_key()[1] == 'wagtailredirects':
            car = can_add_redirect = arp
    for crp in crps:
        if crp.natural_key()[1] == 'wagtailredirects':
            ccr = can_change_redirect = crp
    for drp in drps:
        if drp.natural_key()[1] == 'wagtailredirects':
            cdr = can_delete_redirect = drp

    perm_types = ['add', 'edit', 'publish', 'lock']
    # to query for permission use: name, content_type (integer id of django model instance)
    perm_data = [
        ('Can add document', 252), 
        ('Can change document', 252),
        ('Can add image', 250), 
        ('Can change image', 250)]

    for cd in comp_data:
        print("\n***************************************")
        print("data: ", cd)
        group = Group.objects.get(name=cd[0])
        group.permissions.clear()
        group.permissions.set([wap, car, ccr, cdr])
        cag.permissions.clear()
        cag.permissions.set([wap, car, ccr, cdr])

        # Wagtail permissions, 1) GroupPagePermission
        homepage = ChapterHomePage.objects.filter(title__contains=cd[1]).first()
        if not homepage:
            homepage = DivisionHomePage.objects.filter(title__contains=cd[1]).first()

        # DO ADDING PERMISSION TO COMPONENT_ADMIN GROUP here
        # as we grab each home page add its page permissions to component_admin
        for ptype in perm_types:
            GroupPagePermission.objects.get_or_create(group=cag, permission_type=ptype, page=homepage)

        child_pages = homepage.get_children()
        for child in child_pages:
            for ptype in perm_types:
                GroupPagePermission.objects.get_or_create(group=group, permission_type=ptype, page=child)

        # Wagtail permissions, 2) GroupCollectionPermission
        collection=WagtailCollection.objects.get(name__contains=cd[1])

        for toop in perm_data:
            permission = Permission.objects.filter(
                name=toop[0],
                content_type=toop[1]
                ).first()
            cag_gcp = GroupCollectionPermission.objects.get_or_create(
                collection=collection,
                group=cag,
                permission=permission
                )
            gcp = GroupCollectionPermission.objects.get_or_create(
                collection=collection,
                group=group,
                permission=permission
                )
        print("***************************************\n")

# test call, only virginia
# data = [("CHAPT_VA-admin","Virginia")]
# aps(data)

# script to add APA provider to all jobs
def add_apa(jobs=None, show_progress=False):
    provider = Contact.objects.get(user__username='119523')
    if not jobs:
        jobs = Job.objects.filter(publish_status='DRAFT')
    for j in jobs:
        contact_role, created = ContactRole.objects.get_or_create(contact=provider, content=j, role_type='PROVIDER', publish_status='DRAFT')
        j.publish()
        # no need to solr_publish the old jobs
        if show_progress:
            if created:
                not_string = ""
            else:
                not_string = "not "
            print("%s contact role was " % (contact_role) + not_string + "created for job %s" % (j))


"""
************************************************************
# RESTORE STAGING CHAPTER JOB PRODUCT, ETC.
************************************************************
# TO restore JUST ONE jobs product, etc. on staging (E.G. VIRGINIA):
cs=create_job_codes(chapter_abbrevs_products)
codes_list=['JOB_AD_CHAPT_VA', 'JOB_AD_CHAPT_WI', 'JOB_AD_CHAPT_MO', 'JOB_AD_URBAN_DES', 'JOB_AD_TRANS', 'JOB_AD_HOUSING']
tits=create_job_titles()
titles_list=['Job Ad, Virginia Chapter', 'Job Ad, Wisconsin Chapter', 'Job Ad, Missouri Chapter', 'Job Ad, Urban Design Division', 'Job Ad, Transportation Division', 'Job Ad, Housing Division']
create_chapter_job_products(codes_list, titles_list)
# first you need to publish what you created:
job_products=Product.objects.filter(publish_status='DRAFT', code__in=codes_list)
jp=job_products.first()
for jp in job_products:
    c=Content.objects.filter(id=jp.content_id).first()
    c.publish()
#jp.publish()
# if the above doesn't work, publish in Django
chap_job_products=Product.objects.filter(publish_status='PUBLISHED', code__in=codes_list)
create_chapter_job_categories(chap_job_products)
************************************************************

"""
