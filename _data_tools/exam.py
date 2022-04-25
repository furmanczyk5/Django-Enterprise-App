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
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import is_password_usable
from django.core.mail import send_mail

from datetime import timedelta

from django.db.models import Q

from content.models import *
from myapa.models import *
from store.models import *
from events.models import *
from media.models import *
from exam.models import *
from submissions.models import *

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
from content.utils import generate_random_string

logger = logging.getLogger(__name__)

json_server='http://localhost:8081/dataimport';

node_url = "http://localhost:8081/dataimport/"

# JOB_CRITERIA = (
# ("1_1_PLANMAKING", "Plan Making and Implementation"),
# ("1_2_PRACTICE", "Functional Areas of Practice"),
# ("1_3_RESEARCH", "Resarch, Analysis and Teaching "),
# )

# def update_exam_content():
#     """
#     quick fix to update exam application content types
#     """

#     content = Content.objects.get(code='EXAM_APPLICATION_AICP', publish_status='DRAFT')
#     content.content_type='EXAM'
#     content.save()
#     content.publish()

#     content = Content.objects.get(code='EXAM_APPLICATION_CEP', publish_status='DRAFT')
#     content.content_type='EXAM'
#     content.save()
#     content.publish()

#     content = Content.objects.get(code='EXAM_APPLICATION_CTP', publish_status='DRAFT')
#     content.content_type='EXAM'
#     content.save()
#     content.publish()

#     content = Content.objects.get(code='EXAM_APPLICATION_CUD', publish_status='DRAFT')
#     content.content_type='EXAM'
#     content.save()
#     content.publish()


def create_job_criteria():
    """
    creates submission categories required for job criteria 
    content type: EXAM
    """

    # exam application
    content_aicp = Content.objects.get(code='EXAM_APPLICATION_AICP', publish_status='PUBLISHED')
    category, created = Category.objects.get_or_create(content_type='EXAM', code='EXAM_APPLICATION_AICP', product_master=content_aicp.master)
    category.title='Exam Application AICP'

    tagtype, created = TagType.objects.get_or_create(code="EXAM_PLANNING_PROCESS", title="Discuss how you applied a planning process appropriate to the situation at the position in question through one fo the three sections of professional planning content.")
    tag, created = Tag.objects.get_or_create(tag_type = tagtype, sort_number=1, title="Planning Making & Implementation", code="EXAM_PLANNING_PROCESS_PLANMAKING")
    tag, created = Tag.objects.get_or_create(tag_type = tagtype, sort_number=2, title="Functional Areas of Practice", code="EXAM_PLANNING_PROCESS_PRACTICE")
    tag, created = Tag.objects.get_or_create(tag_type = tagtype, sort_number=3, title="Research, Analysis, & Teaching", code="EXAM_PLANNING_PROCESS_RESEARCH")
    
    question1, created = Question.objects.get_or_create(question_type='TAG', code="EXAM_PLANNING_PROCESS_QUESTION", tag_type = tagtype, title="Discuss how you applied a planning process appropriate to the situation at the position in question through one fo the three sections of professional planning content.", required=True)

    question2, created = Question.objects.get_or_create(question_type='LONG_TEXT', code="EXAM_PLANNING_SITUATION", title="Apply a Planing Process Appropriate to the Situation", required=True, words_min=250, words_max=500)
    question3, created = Question.objects.get_or_create(question_type='LONG_TEXT', code="EXAM_COMPREHENSIVE_POV", title="Employ an Appropriately Comprehensive Point of View", required=True, words_min=250, words_max=500)
    question4, created = Question.objects.get_or_create(question_type='LONG_TEXT', code="EXAM_PUBLIC_DECISION_MAKING", title="Influence Public Decision Making in the Public Interest", required=True, words_min=250, words_max=500)
    
    category.questions.add(question1, question2, question3, question4)
    category.save()

    content_aicp.publish()


    content_aicp_advanced = Content.objects.get(code='EXAM_APPLICATION_CEP', publish_status='PUBLISHED')
    category, created = Category.objects.get_or_create(content_type='EXAM', code='EXAM_APPLICATION_CEP', product_master=content_aicp_advanced.master)
    category.title='Exam Application CEP'

    tagtype, created = TagType.objects.get_or_create(code="EXAM_ADVANCED_CONCENTRATION", title="Approximately what percent of your time was dedicated to this certifification type?")
    tag, created = Tag.objects.get_or_create(tag_type = tagtype, sort_number=1, title="0%", code="EXAM_ADVANCED_CONCENTRATION_0")
    tag, created = Tag.objects.get_or_create(tag_type = tagtype, sort_number=2, title="25%", code="EXAM_ADVANCED_CONCENTRATION_25")
    tag, created = Tag.objects.get_or_create(tag_type = tagtype, sort_number=3, title="50%", code="EXAM_ADVANCED_CONCENTRATION_50")
    tag, created = Tag.objects.get_or_create(tag_type = tagtype, sort_number=4, title="75%", code="EXAM_ADVANCED_CONCENTRATION_75")
    tag, created = Tag.objects.get_or_create(tag_type = tagtype, sort_number=5, title="100%", code="EXAM_ADVANCED_CONCENTRATION_100")
        

    question1, created = Question.objects.get_or_create(code="EXAM_ADVANCED_CONCENTRATION", question_type='TAG', tag_type = tagtype, title="Approximately what percent of your time was dedicated to this certifification type?", required=True)
    question2, created = Question.objects.get_or_create(question_type='LONG_TEXT', code="EXAM_ADVANCED_DUTIES", title="Please describe the scope and duties of this position and how they meet the defition of the advanced exam type.", required=True, words_min=250, words_max=500)

    category.questions.add(question1, question2)
    category.save()

    content_aicp.publish()

    content_aicp_advanced = Content.objects.get(code='EXAM_APPLICATION_CTP', publish_status='PUBLISHED')
    category, created = Category.objects.get_or_create(content_type='EXAM', code='EXAM_APPLICATION_CTP', product_master=content_aicp_advanced.master)
    category.title = 'Exam Application CTP'
    category.questions.add(question1, question2)
    category.save()

    content_aicp_advanced = Content.objects.get(code='EXAM_APPLICATION_CUD', publish_status='PUBLISHED')
    category, created = Category.objects.get_or_create(content_type='EXAM', code='EXAM_APPLICATION_CUD', product_master=content_aicp_advanced.master)
    category.title = 'Exam Application CUD'
    category.questions.add(question1, question2)
    category.save()

def import_exam():
    """
    import exam data from iMIS
    """

    url = node_url + 'exam'

    r = requests.get(url)

    exams = r.json()['data']

    f = '%Y-%m-%d %H:%M:%S'

    for exam_import in exams:
        try:
            code = exam_import.get('ExamCode')
            title = exam_import.get('ExamName')
            application_start_time = exam_import.get('ExamApplicationStartTime')
            application_end_time = exam_import.get('ExamApplicationEndTime')
            exam_start_time = exam_import.get('ExamStartDate')
            exam_end_time = exam_import.get('ExamEndDate')
            exam_application_early_extended_end_time = exam_import.get('ExamApplicationEarlyExtendedDateTime')
            previous_exam_codes = exam_import.get('PreviousExamCodes')
            advanced = exam_import.get('Advanced', False)
            if not advanced:
                advanced = False

            print("exam: " + str(code))
            print("advanced:" + str(advanced))

            # http://stackoverflow.com/questions/14291636/what-is-the-proper-way-to-convert-between-mysql-datetime-and-python-timestamp
            if application_start_time:
                application_start_time_converted = datetime.datetime.strptime(application_start_time, f)
            else:
                application_start_time_converted = None
            if application_end_time:
                application_end_time_converted = datetime.datetime.strptime(application_end_time, f)
            else:
                application_end_time_converted = None
            if exam_start_time:
                exam_start_time_converted = datetime.datetime.strptime(exam_start_time, f)
            else:
                exam_start_time_converted = None
            if exam_end_time:
                exam_end_time_converted = datetime.datetime.strptime(exam_end_time, f)
            else:
                exam_end_time_converted = None

            if exam_application_early_extended_end_time:
                exam_application_early_extended_end_time_converted = datetime.datetime.strptime(exam_application_early_extended_end_time, f)
            else:
                exam_application_early_extended_end_time_converted = None

            exam, created = Exam.objects.get_or_create(code=code, title=title)
            exam.application_start_time = application_start_time_converted
            exam.application_end_time = application_end_time_converted
            exam.start_time = exam_start_time_converted
            exam.end_time = exam_end_time_converted
            exam.registration_start_time = application_start_time_converted
            exam.registration_end_time = application_end_time_converted
            exam.application_early_end_time = exam_application_early_extended_end_time_converted
            exam.is_advanced = advanced
            exam.save()
        except Exception as e:
            print("error: " + str(e))
    # another loop to attach the previous exams to newly created ones
    for exam_import in exams:
        try:
            code = exam_import.get('ExamCode')
            title = exam_import.get('ExamName')
            application_start_time = exam_import.get('ExamApplicationStartTime')
            application_end_time = exam_import.get('ExamApplicationEndTime')
            exam_start_time = exam_import.get('ExamStartDate')
            exam_end_time = exam_import.get('ExamEndDate')
            exam_application_early_extended_end_time = exam_import.get('ExamApplicationEarlyExtendedDateTime')
            previous_exam_codes = exam_import.get('PreviousExamCodes')

            exam = Exam.objects.get(code=code)
            if previous_exam_codes:

                previous_exam_codes_list = previous_exam_codes.replace(" ", "").split(",")
                for previous_exam_code in previous_exam_codes_list:

                    previous_exam = Exam.objects.get(code=previous_exam_code)
                    exam.previous_exams.add(previous_exam)

                exam.save()
        except Exception as e:
            print("previous_exam error: " + str(e))

# def import_registrations():
#     """
#     import exam registration data
#     NOTE: cannot do this until we import applications....
#     """

#     exam_codes = ['2000MAY', '2001MAY', '2002MAY', '2003MAY', '2004MAY', '2004NOV', '2005MAY', '2009MAY', '2009NOV', '2010MAY', '2010NOV', '2011MAY', '2011NOV', '2012ASC', '2014ASC', '2014MAY', '2014NOV', '2015ASC', '2011ASC', '2015MAY', '2015NOV', '2016ASC', '2016MAY', '2016NOV', '2005NOV', '2006MAY', '2006NOV', '2007MAY', '2007NOV', '2008MAY', '2008NOV', '2012MAY', '2012NOV', '2013ASC', '2013MAY', '2013NOV']

#     for exam_code in exam_codes:
#         url = node_url + 'examregistration/' + exam_code

#         r = requests.get(url)

#         exam_registrations = r.json()['data']
#         registration_import_errors = {}
#         registration_application_errors = {}
        
#         for exam_registration_import in exam_registrations:
#             try:
#                 user_id = exam_registration_import.get('ID')
#                 exam_application_type = exam_registration_import.get('EXAM_APPLICATION_TYPE')
#                 exam_application_status = exam_registration_import.get('EXAM_APPLICATION_STATUS')
#                 previous_code = exam_registration_import.get('PREVIOUS_CODE')
#                 ada_requirement = exam_registration_import.get('EXAM_ADA_REQUIREMENT')
#                 certificate_name = exam_registration_import.get('CERTIFICATE_NAME')
#                 received_time = exam_registration_import.get('RECEIVED_DATETIME')
#                 form_code = exam_registration_import.get('FORM_CODE')
#                 gee_code = exam_registration_import.get('GEE_ELIGIBILITY_ID')
#                 exam_registration_status = exam_registration_import.get('EXAM_REGISTRATION_STATUS') # is this needed?
#                 seqn = exam_registration_import.get('SEQN')
#                 exam_application_verification = exam_registration_import.get('EXAM_APPLICATION_VERIFICATION')
#                 legacy_id = exam_registration_import.get('SEQN')
#                 exam_verification_list = exam_application_verification.replace(" ", "").split(",")
#                 legacy_id_previous = exam_registration_import.get('ExamArchiveIDPrevious')

#                 exam = Exam.objects.get(code=exam_code)

#                 contact = Contact.objects.get(user__username=user_id)

#                 if exam_application_status =="A":
#                     try:
#                         application = ExamApplication.objects.get(legacy_id=legacy_id, publish_status='DRAFT')
#                     except Exception as e:
#                         print('could not find application... passing')
#                         application = None
#                         registration_application_errors[legacy_id] = "could not find appropriate application to attach"
#                         pass

#                 elif legacy_id_previous and (exam_application_status in ("A_P") or exam_application_type in ("REG_A", "REG_T_100","REG_T_100","SCHOLAR_A","NJ_REG_A","NJ_REG","NJ_NOAICP","MICP_A","CUD_T_100","CUD_T_10","CUD_T_0","CUD_A","CTP_T_100","CTP_T_0","CTP_A","CEP_T_100","CEP_T_0","CEP_A")):
#                     try:
#                         application = ExamApplication.objects.get(legacy_id = legacy_id_previous, publish_status='DRAFT')
#                     except Exception as e:
#                         print('could not find previous exam code')
#                         application = None
#                         registration_application_errors[legacy_id] = "could not find previous exam code for this registration"
#                         pass
#                 else:

#                     if not legacy_id_previous:
#                         registration_application_errors[legacy_id] = "legacy id is missing"
#                         print("legacy id is missing")

#                     else:
#                         registration_application_errors[legacy_id] = "application types / exam status do not match criteria"
#                         print("application types / exam status do not match criteria")

#                     application = None
#                     pass

#                 registration_type = exam_application_type

#                 if exam_application_type == "CEP":
#                     registration_type = "CEP_A"

#                 if exam_application_type == "CTP":
#                     registration_type = "CTP_A"

#                 if exam_application_type == "CUD":
#                     registration_type = "CUD_A"

#                 if exam_application_type == "MCIP":
#                     registration_type = "MCIP_A"

#                 if exam_application_type == "REG":
#                     registration_type = "REG_A"

#                 if exam_application_type == "SCHOLAR":
#                     registration_type = "SCHOLAR_A"

#                 registration, created = ExamRegistration.objects.get_or_create(legacy_id = seqn, exam=exam, contact=contact)
#                 registration.registration_type = registration_type
#                 registration.application = application
#                 registration.ada_requirement = ada_requirement
#                 registration.certificate_name = certificate_name
#                 registration.gee_eligibility_id = gee_code

#                 if "E" in exam_verification_list:
#                     registration.code_of_ethics = True

#                 if "R" in exam_verification_list:
#                     registration.release_information = True
                
#                 registration.save()
#                 print('registration added OK')
#             except Exception as e:
#                 print("error importing registration record: " + str(e))
#                 registration_import_errors[legacy_id] = str(e)
#                 continue

#     print("registration import errors: " + registration_import_errors)
#     print("registration application errors: " +  registration_application_errors)
# def import_applications():
#     """
#     import exam application data
#     NOTE: this import only works for submissions. does not imported 'not submitted' application data
#     # import priorities:
#     1. submission
#     2. submission_correction
#     3. early_resubmission
#     4. early_resubmission_correction
#     """

#     submission_type_codes = ["SUBMISSION","SUBMISSION_CORRECTION","EARLY_RESUBMISSION","EARLY_RESUBMISSION_CORRECTION"] #EARLY_RESUBMISSION, EARLY_RESUBMISSION_CORRECTION

#     application_import_errors = {}

#     #exam_codes = ['2000MAY', '2001MAY', '2002MAY', '2003MAY', '2004MAY', '2004NOV', '2005MAY', '2009MAY', '2009NOV', '2010MAY', '2010NOV', '2011MAY', '2011NOV', '2012ASC', '2014ASC', '2014MAY', '2014NOV', '2015ASC', '2011ASC', '2015MAY', '2015NOV', '2016ASC', '2016MAY', '2016NOV', '2005NOV', '2006MAY', '2006NOV', '2007MAY', '2007NOV', '2008MAY', '2008NOV', '2012MAY', '2012NOV', '2013ASC', '2013MAY', '2013NOV']
#     exam_codes = ['2016MAY']
#     for exam_code in exam_codes:
#         for submission_type_code in submission_type_codes:

#             url_submission = node_url + 'examapplication/examcode/' + exam_code + "/archivetypecode/" + submission_type_code
#             r = requests.get(url_submission)

#             exam_applications = r.json()['data']

#             exam = Exam.objects.get(code=exam_code)

#             submission_category_aicp = Category.objects.get(content_type='EXAM', code='EXAM_APPLICATION_AICP')
#             submission_category_cep = Category.objects.get(content_type='EXAM',code='EXAM_APPLICATION_CEP')
#             submission_category_ctp = Category.objects.get(content_type='EXAM', code='EXAM_APPLICATION_CTP')
#             submission_category_cud = Category.objects.get(content_type='EXAM',code='EXAM_APPLICATION_CUD')
            
#             f = '%Y-%m-%d %H:%M:%S'

#             publish_status = "DRAFT"

#             for exam_application_import in exam_applications:
#                 try:
#                     user_id = exam_application_import.get('ID')
#                     exam_code = exam_application_import.get('EXAM_CODE')
#                     exam_application_type = exam_application_import.get('EXAM_APPLICATION_TYPE')
#                     exam_application_status = exam_application_import.get('EXAM_APPLICATION_STATUS')
#                     previous_code = exam_application_import.get('PREVIOUS_CODE')
#                     received_time = exam_application_import.get('RECEIVED_DATETIME')
#                     approved_time = exam_application_import.get('APPROVED_DATETIME')
#                     advanced = exam_application_import.get('ADVANCED')
#                     legacy_id = exam_application_import.get('SEQN')
#                     exam_archive_id = exam_application_import.get('ExamArchiveID')
#                     archive_type_code = exam_application_import.get('ArchiveTypeCode')
#                     exam_application_verification = exam_application_import.get('EXAM_APPLICATION_VERIFICATION')
#                     code_of_ethics = False
         
#                     exam_verification_list = exam_application_verification.replace(" ", "").split(",")

#                     if "E" in exam_verification_list:
#                         code_of_ethics = True

#                     if received_time:
#                         received_time_converted = datetime.datetime.strptime(received_time, f)
#                     else:
#                         received_time_converted = None

#                     if approved_time:
#                         approved_time_converted = datetime.datetime.strptime(approved_time, f)
#                     else:
#                         approved_time_converted = None

#                     contact = Contact.objects.get(user__username=user_id)

#                     master = None
#                     original_uuid = None
#                     try:
#                         original_submission = ExamApplication.objects.filter(legacy_id=legacy_id).first()
#                         master = original_submission.master
#                         original_uuid = original_submission.publish_uuid

#                         #print('this master content for ' + submission_type_code + ' is: ' + str(master))
#                     except Exception as e:
#                         print('could not find existing submission... creating a new one with submissiont type: ' + submission_type_code)
#                         pass

#                     if not advanced:
#                         if master:
#                             application, created = ExamApplication.objects.get_or_create(publish_uuid=original_uuid, master=master, legacy_id = legacy_id, exam=exam, submission_category=submission_category_aicp, publish_status=publish_status, contact=contact)
#                         else:
#                             application, created = ExamApplication.objects.get_or_create(legacy_id = legacy_id, exam=exam, submission_category=submission_category_aicp, publish_status=publish_status, contact=contact)                        
#                     else:
#                         if exam_application_type == "CEP":
#                             if master:
#                                 application, created = ExamApplication.objects.get_or_create(publish_uuid=original_uuid,master=master, legacy_id = legacy_id, exam=exam, submission_category=submission_category_cep, publish_status=publish_status, contact=contact)
#                             else:
#                                 application, created = ExamApplication.objects.get_or_create(legacy_id = legacy_id, exam=exam, submission_category=submission_category_cep, publish_status=publish_status, contact=contact)
#                         elif exam_application_type == "CTP":
#                             if master:
#                                 application, created = ExamApplication.objects.get_or_create(publish_uuid=original_uuid,master=master, legacy_id = legacy_id, exam=exam, submission_category=submission_category_ctp, publish_status=publish_status, contact=contact)
#                             else:
#                                 application, created = ExamApplication.objects.get_or_create(legacy_id = legacy_id, exam=exam, submission_category=submission_category_ctp, publish_status=publish_status, contact=contact)
#                         elif exam_application_type == "CUD":
#                             if master:
#                                 application, created = ExamApplication.objects.get_or_create(publish_uuid=original_uuid,master=master, legacy_id = legacy_id, exam=exam, submission_category=submission_category_cud, publish_status=publish_status, contact=contact)
#                             else:
#                                 application, created = ExamApplication.objects.get_or_create(legacy_id = legacy_id, exam=exam, submission_category=submission_category_cud, publish_status=publish_status, contact=contact)
#                         else:
#                             pass

#                     application.application_type = exam_application_type
#                     application.application_status = exam_application_status # should this be a new field?
#                     application.submission_time = received_time_converted
#                     application.submission_approved_time = approved_time_converted
#                     application.code_of_ethics = code_of_ethics
                    
#                     if master:
#                         contactrole, created = ContactRole.objects.get_or_create(publish_uuid=original_uuid,content=application, contact=contact, role_type="AUTHOR", publish_status="DRAFT")
#                     else:
#                         contactrole, created = ContactRole.objects.get_or_create(content=application, contact=contact, role_type="AUTHOR", publish_status="DRAFT")

#                     contactrole.delete()
#                     # import_jobs(application, advanced, exam_archive_id)
                    
#                     # how to get old job documents?

#                     # how to get old school documents?
                   
#                     application.save()

#                     if submission_type_code in("SUBMISSION", "EARLY_RESUBMISSION"):
#                         super(Content, application).publish(publish_type=submission_type_code)

#                     print("imported exam archive id: " + str(legacy_id))
#                 except Exception as e:
#                     print("error importing application: " + str(e))
#                     application_import_errors[legacy_id] = str(e)
#                     continue
            
#     print(application_import_errors)

def import_jobs():
    """
    import jobs data for an archived exam
    SUBMISSION = ORIGINAL COPY
    DRAFT = ALTERED COPY (STAFF).. SUBMISSION_CORRECTIONS
    """

    exam_application_allowed_types = FileType.objects.filter(Q(extension='.png') | Q(extension='.jpg') |  Q(extension='.pdf'))

    upload_type_exam_application_jobs, created = UploadType.objects.get_or_create(code='EXAM_APPLICATION_JOB', title='Exam Application - Job Upload Type')
    upload_type_exam_application_education, created = UploadType.objects.get_or_create(code='EXAM_APPLICATION_EDUCATION', title= ' Exam Application - Education Upload Type')

    upload_type_exam_application_jobs.allowed_types.add(*exam_application_allowed_types)
    upload_type_exam_application_jobs.save()

    upload_type_exam_application_education.allowed_types.add(*exam_application_allowed_types)
    upload_type_exam_application_jobs.save()
    
    f = '%Y-%m-%d %H:%M:%S'

    planning_process_plan_tag = Tag.objects.get(code="EXAM_PLANNING_PROCESS_PLANMAKING")
    planning_process_practice_tag = Tag.objects.get(code="EXAM_PLANNING_PROCESS_PRACTICE")
    planning_process_research_tag = Tag.objects.get(code="EXAM_PLANNING_PROCESS_RESEARCH")

    advanced_concentration_0 = Tag.objects.get(code="EXAM_ADVANCED_CONCENTRATION_0")
    advanced_concentration_25 = Tag.objects.get(code="EXAM_ADVANCED_CONCENTRATION_25")
    advanced_concentration_50 = Tag.objects.get(code="EXAM_ADVANCED_CONCENTRATION_50")
    advanced_concentration_75 = Tag.objects.get(code="EXAM_ADVANCED_CONCENTRATION_75")
    advanced_concentration_100 = Tag.objects.get(code="EXAM_ADVANCED_CONCENTRATION_100")

    question1 = Question.objects.get(code="EXAM_PLANNING_PROCESS_QUESTION")
    question2 = Question.objects.get(code="EXAM_PLANNING_SITUATION")
    question3 = Question.objects.get(code="EXAM_COMPREHENSIVE_POV")
    question4 = Question.objects.get(code="EXAM_PUBLIC_DECISION_MAKING")
    
    question5 = Question.objects.get(code="EXAM_ADVANCED_CONCENTRATION")
    question6 = Question.objects.get(code="EXAM_ADVANCED_DUTIES")



    application_no_exist = []
    jobs_import_errors = []
    contact_no_exist = []
    general_error = {}

    exam_archive_type_codes = ['SUBMISSION', 'SUBMISSION_CORRECTION', 'EARLY_RESUBMISSION','EARLY_RESUBMISSION_CORRECTION']
    for exam_archive_code in exam_archive_type_codes:
        url = node_url + 'examapplication/archive/' + exam_archive_code

        r = requests.get(url)
        exam_archive_records = r.json()['data']

        for exam_archive_record in exam_archive_records:
            try:
                exam_archive_id = exam_archive_record.get('ExamArchiveID')
                exam_application_seqn = exam_archive_record.get('ExamApplicationSEQN')
                archive_type_code = exam_archive_record.get('ArchiveTypeCode')
                exam_code = exam_archive_record.get('ExamCode')
                advanced = exam_archive_record.get('Advanced')
                user_id = exam_archive_record.get('WebUserID')
                try:
                    contact = IndividualContact.objects.get(user__username=user_id)
                except Exception as e:
                    print('contact does not exist.')
                    contact = None
                    contact_no_exist.append(user_id)
                    continue

                try:
                    # draft copies written for submission, submission_correction, early_resubmission, early_resubmission_correction
                    # publish statuses: DRAFT, SUBMISSION, EARLY_RESUBMISSION

                    application = ExamApplication.objects.get(legacy_id=exam_application_seqn, publish_status='DRAFT')

                except Exception as e:
                    application = None
                    application_no_exist.append(exam_archive_id)
                    continue

                url = node_url + 'examapplication/jobhistory/' + str(exam_archive_id)

                r = requests.get(url)

                jobs = r.json()['data']

                if archive_type_code == 'SUBMISSION':
                    ApplicationJobHistory.objects.filter(application=application).delete()
                    ApplicationDegree.objects.filter(application=application).delete()
                    Answer.objects.filter(content=application).delete()
                    try:
                        VerificationDocument.objects.filter(content=application).delete()
                    except:
                        pass
                # hacky way to delete all existing answers for this newly created archive type so that it goes with the lastest copy
                if archive_type_code in ['SUBMISSION_CORRECTION','EARLY_RESUBMISSION','EARLY_RESUBMISSION_CORRECTION'] and exam_archive_id:

                    VerificationDocument.objects.filter(content=application, publish_status='DRAFT').delete()
                    ApplicationJobHistory.objects.filter(application=application, publish_status='DRAFT').delete()
                    ApplicationDegree.objects.filter(application=application, publish_status='DRAFT').delete()
                    Answer.objects.filter(content=application, publish_status='DRAFT').delete()
                
                for job in jobs:
                    job_id = job.get('JobID')
                    title = job.get('JobTitle')
                    company = job.get('CompanyName')
                    city = job.get('City')
                    state = job.get('StateProvince')
                    decision_making = job.get('Criteria_DecisionMaking')
                    comprehensive_pov = job.get('Criteria_ComprehensivePOV')
                    planning_process = job.get('Criteria_PlanningProcess')
                    criteria_e = job.get('CriteriaE')
                    country = job.get('Country')
                    phone = job.get('CompanyPhone')
                    contact_employer = job.get('ContactedEmployer')
                    supervisor_name = job.get('SupervisorName')
                    full_time_start_time = job.get('FullTimeStartDateFormatted')
                    full_time_end_time = job.get('FullTimeEndDateFormatted')
                    part_time_start_time = job.get('PartTimeStartDateFormatted')
                    part_time_end_time = job.get('PartTimeEndDateFormatted')
                    is_planning = job.get('IsPlanning')
                    currently_employed = job.get('CurrentlyEmployed')
                    advanced_concentration_percent = job.get('AdvancedConcentrationPercent')
                    criteria_planningprocess_sectioncode = job.get('Criteria_PlanningProcess_SectionCode')
                    file_name = job.get('FileName')
                    if file_name:
                        document_upload, created = VerificationDocument.objects.get_or_create(publish_status='DRAFT', content=application, upload_type=upload_type_exam_application_jobs, title=file_name)
                        document_upload.uploaded_file.name= 'uploads/' + upload_type_exam_application_jobs.code + '/' + file_name 
                        document_upload.save()
                    job_application, created = ApplicationJobHistory.objects.get_or_create(publish_status='DRAFT', contact=contact,application = application, legacy_id = job_id)
                    
                    if file_name:
                        job_application.verification_document=document_upload

                    job_application.title = title
                    job_application.company = company
                    job_application.city = city
                    job_application.state = state
                    job_application.country = country
                    job_application.phone = phone

                    work_start_time = None
                    work_end_time = None

                    if full_time_start_time:
                        work_start_time = datetime.datetime.strptime(full_time_start_time, f)
                        if full_time_end_time:
                            work_end_time = datetime.datetime.strptime(full_time_end_time, f)
                    elif part_time_start_time:
                        work_start_time = datetime.datetime.strptime(part_time_start_time, f)
                        if part_time_end_time:
                            work_end_time = datetime.datetime.strptime(part_time_end_time, f)

                    job_application.start_date = work_start_time
                    job_application.end_date = work_end_time
                    job_application.is_planning = is_planning
                    job_application.save()

                    if not advanced:
                        # default planingprocess section code
                        criteria_exam_process_tag = planning_process_plan_tag

                        if criteria_planningprocess_sectioncode is not None and criteria_planningprocess_sectioncode != '':
                            if criteria_planningprocess_sectioncode == "1_1_PLANNING":
                                criteria_exam_process_tag = planning_process_plan_tag
                            elif criteria_planningprocess_sectioncode == "1_2_PRACTICE":
                                criteria_exam_process_tag = planning_process_practice_tag
                            elif criteria_planningprocess_sectioncode == "1_3_RESEARCH":
                                criteria_exam_process_tag = planning_process_research_tag
                                
                            answer1, created = Answer.objects.get_or_create(publish_status='DRAFT',question = question1, content = application, tag = criteria_exam_process_tag)

                        answer2, created = Answer.objects.get_or_create(publish_status='DRAFT',question = question2, content = application, text=planning_process)
                        answer3, created = Answer.objects.get_or_create(publish_status='DRAFT',question = question3, content = application, text=comprehensive_pov)
                        answer4, created = Answer.objects.get_or_create(publish_status='DRAFT',question = question4, content = application, text=decision_making)

                    else:
                        if advanced_concentration_percent:
                            if advanced_concentration_percent == 0.0:
                                advanced_concentration_percent_tag = advanced_concentration_0
                            elif advanced_concentration_percent == 0.25:
                                advanced_concentration_percent_tag = advanced_concentration_25
                            elif advanced_concentration_percent == 0.50:
                                advanced_concentration_percent_tag = advanced_concentration_50
                            elif advanced_concentration_percent == 0.75:
                                advanced_concentration_percent_tag = advanced_concentration_75
                            else:
                                advanced_concentration_percent_tag = advanced_concentration_100

                            answer1, created = Answer.objects.get_or_create(publish_status='DRAFT',question = question5, content = application, tag = advanced_concentration_percent_tag)
                            answer2, created = Answer.objects.get_or_create(publish_status='DRAFT',question = question6, content= application, text = criteria_e)

                url = node_url + 'examapplication/degreehistory/' + str(exam_archive_id) # Add ArchiveTypeCode here?

                r = requests.get(url)

                degrees = r.json()['data']

                for degree in degrees:
                    file_name = degree.get('FileName')
                    school_id = degree.get('SCHOOL_ID')
                    school_other = degree.get('SCHOOL_OTHER')
                    degree_level = degree.get('DEGREE_LEVEL')
                    degree_date = degree.get('DEGREE_DATE')
                    degree_planning = degree.get('DEGREE_PLANNING')
                    degree_name = degree.get('DEGREE_NAME')
                    degree_major = degree.get('DEGREE_MAJOR')
                    degree_accredited = degree.get('ACCREDITED_PROGRAM')
                    degree_complete = degree.get('DEGREE_COMPLETE')
                    degree_accredited_school = degree.get('ACCRED_SCHOOLS')
                    degree_all_schools = degree.get('ALL_SCHOOLS')
                    exam_archive_id = degree.get('EXAM_ARCHIVE_ID')
                    seqn = degree.get('SEQN')
                    
                    school = None
                    accredited_program = False

                    if degree_accredited and degree_accredited is not None:
                        accredited_program = True

                    if school_id and school_id != '0':
                        try:
                            school = School.objects.get(user__username=school_id)
                        except School.DoesNotExist:
                            print('the school id is: ' + str(school_id))
                            Contact.update_or_create_from_imis(school_id)
                            school = School.objects.get(user__username=school_id)
                    
                    document_upload = None
                    education_application, created = ApplicationDegree.objects.get_or_create(publish_status='DRAFT', contact=contact,application = application, legacy_id = seqn)
                    
                    if file_name:
                        document_upload, created = VerificationDocument.objects.get_or_create(publish_status='DRAFT', content=application, upload_type=upload_type_exam_application_education, title=file_name)
                        document_upload.uploaded_file.name= 'uploads/' + upload_type_exam_application_education.code + '/' + file_name 
                        document_upload.save()
                        education_application.verification_document=document_upload
                    if school:
                        education_application.school = school

                    education_application.other_school = school_other
                    education_application.level = degree_level
                    education_application.is_planning = degree_planning

                    if degree_date:
                        degree_date = datetime.datetime.strptime(degree_date, f)  
                        education_application.graduation_date = degree_date

                    education_application.save()

                # archive type code = current code used in user's exam application archive loop
                # exam archive code = code used in exam archive type loop

                # if we are saving the submission/early resubmission and are not in the 
                # submission correction / early resubmission correction loop

                if archive_type_code in ["SUBMISSION", "EARLY_RESUBMISSION"]:
                    try:
                        application = ExamApplication.objects.get(legacy_id=exam_application_seqn, publish_status='DRAFT')
                        application.publish(publish_type=archive_type_code)
                    except Exception as e:
                        # ??
                        application_no_exist.append(exam_archive_id)
                        print('exam does not exist. exam archive id: ' + str(exam_archive_id))
                        pass
                print('imported user: ' + str(user_id))
            except Exception as e:
                print('ERROR: ' + str(e))
                pass
                general_error[user_id] = str(e)
    #print('job import errors: ' + str(job_import_errors))
    print('applications that do not exist: ' + str(application_no_exist))
    print('general errors: ' + str(general_error))
    print('job import errors: ' + str(jobs_import_errors))
    print('contact no exist' + str(contact_no_exist))

    print('application does not exist count: ' + str(len(application_no_exist)))
    print("job errors count: " + str(len(jobs_import_errors)))
    print('contact no exist count: ' + str(len(contact_no_exist)))
    print('general error count: ' + str(len(general_error)))

    application_no_exist = []
    jobs_import_errors = []
    contact_no_exist = []
    general_error = {}

def job_degree_uuid_fix():
    """
    fixes the uuids for imported jobs and degrees
    """
    # first get all draft applications
    current_exam = Exam.objects.get(code="2016NOV")
    all_applications = ExamApplication.objects.filter(publish_status="DRAFT").exclude(exam=current_exam)


    question1 = Question.objects.get(code="EXAM_PLANNING_PROCESS_QUESTION")
    question2 = Question.objects.get(code="EXAM_PLANNING_SITUATION")
    question3 = Question.objects.get(code="EXAM_COMPREHENSIVE_POV")
    question4 = Question.objects.get(code="EXAM_PUBLIC_DECISION_MAKING")
    
    question5 = Question.objects.get(code="EXAM_ADVANCED_CONCENTRATION")
    question6 = Question.objects.get(code="EXAM_ADVANCED_DUTIES")


    for application in all_applications:
        # get jobs related to the app
        app_jobs = ApplicationJobHistory.objects.filter(application=application, publish_status="DRAFT")
        app_degree = ApplicationDegree.objects.filter(application=application, publish_status="DRAFT")
        
        for job in app_jobs:
            job_title = job.title
            job_company = job.company

            ApplicationJobHistory.objects.filter(application__exam=job.application.exam, contact=job.contact, title=job_title, company = job_company).update(publish_uuid=job.publish_uuid)

        for degree in app_degree:
            school = degree.school
            other_school = degree.other_school
            degree_level = degree.level
            degree_date = degree.graduation_date

            ApplicationDegree.objects.filter(application__exam=degree.application.exam, contact=degree.contact, school=school, other_school=other_school, level=degree_level, graduation_date=degree_date).update(publish_uuid=degree.uuid)

        app_jobs = ApplicationJobHistory.objects.filter(application=application, publish_status="DRAFT").exclude(verification_document__isnull=True)
        app_degree = ApplicationDegree.objects.filter(application=application, publish_status="DRAFT").exclude(verification_document__isnull=True)

  
        answer_1s = Answer.objects.filter(publish_status="DRAFT", question = question1)
        answer_2s = Answer.objects.filter(publish_status="DRAFT", question = question2)
        answer_3s = Answer.objects.filter(publish_status="DRAFT", question = question3)
        answer_4s = Answer.objects.filter(publish_status="DRAFT", question = question4)
        answer_5s = Answer.objects.filter(publish_status='DRAFT',question = question5)
        answer_6s = Answer.objects.filter(publish_status='DRAFT',question = question6)

        for answer_1 in answer_1s:
            answer_1_publish_uuid = answer_1.publish_uuid
            Answer.objects.filter(question=answer_1.question, content=application).update(publish_uuid=answer_1_publish_uuid)

        for answer_2 in answer_2s:
            answer_2_publish_uuid = answer_2.publish_uuid
            Answer.objects.filter(question=answer_2.question, content=application).update(publish_uuid=answer_2_publish_uuid)
        
        for answer_3 in answer_3s:
            answer_3_publish_uuid = answer_3.publish_uuid
            Answer.objects.filter(question=answer_3.question, content=application).update(publish_uuid=answer_3_publish_uuid)

        for answer_4 in answer_4s:
            answer_4_publish_uuid = answer_4.publish_uuid
            Answer.objects.filter(question=answer_4.question, content=application).update(publish_uuid=answer_4_publish_uuid)

        for answer_5 in answer_5s:
            answer_5_publish_uuid = answer_5.publish_uuid
            Answer.objects.filter(question=answer_5.question, content=application).update(publish_uuid=answer_5_publish_uuid)

        for answer_6 in answer_6s:
            answer_6_publish_uuid = answer_6.publish_uuid
            Answer.objects.filter(question=answer_6.question, content=application).update(publish_uuid=answer_6_publish_uuid)


def exam_question_switch():
    """
    switches the answer relationship for exams
    """

    exam = Exam.objects.get(code='2016NOV')
    exam_apps = ExamApplication.objects.filter(exam=exam)

    question_2 = Question.objects.get(code="EXAM_COMPREHENSIVE_POV")
    question_3 = Question.objects.get(code="EXAM_PUBLIC_DECISION_MAKING")
    for exam_app in exam_apps:
        answers = Answer.objects.filter(content=exam_app, question__in=(question_2,question_3))
        for answer in answers:
            if answer.question == question_2:
                answer.question = question_3
                answer.save()
                continue

            if answer.question == question_3:
                answer.question = question_2
                answer.save()
                continue
                
            answer.save()


