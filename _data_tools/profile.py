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
from io import BytesIO
from urllib.request import urlopen
from django.core.files import File

# YET ANOTHER RANDOM COMMENT
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import is_password_usable
from django.core.mail import send_mail

from datetime import timedelta

from django.db.models import Q

from content.models import *
from store.models import *
from myapa.models import *
from uploads.models import *

from planning.settings import ENVIRONMENT_NAME, RESTIFY_SERVER_ADDRESS
from urllib.request import urlopen
from urllib import parse
from decimal import * 
from xml.dom import minidom

from django.core.files import File
from django.core.files.temp import NamedTemporaryFile


from content.utils import generate_random_string

logger = logging.getLogger(__name__)

json_server='http://localhost:8081/dataimport';

node_url = "http://localhost:8081/dataimport/"

# import event, activity, then everything else..
def get_profiles():
	"""
	imports all profile data from old site to django
	"""
	url = node_url + 'profiles'

	r = requests.get(url)

	profiles = r.json()['data']

	for profile in profiles:
		try:
			about_me = profile.get('AboutMe', None)
			personal_url = profile.get('PersonalUrl', None)
			linkedin_url = profile.get('LinkedInUrl', None)
			facebook_url = profile.get('FacebookUrl', None)
			twitter_url = profile.get('TwitterUrl', None)
			user_id = profile.get('WebUserID')


			share_profile = profile.get('ShareTagCode', 'PRIVATE')
			share_contact = profile.get('ShareContactTagCode', 'MEMBER')
			share_bio = profile.get('ShareBioTagCode', 'PUBLIC')
			share_social = profile.get('ShareSocialMediaTagCode', 'MEMBER')

			share_education = profile.get('ShareEducationTagCode', 'MEMBER')
			share_jobs = profile.get('ShareJobsTagCode', 'MEMBER')
			share_events = profile.get('ShareCMTagCode', 'MEMBER')
			share_resume = profile.get('ShareResumeTagCode', 'MEMBER')
			share_conference = profile.get('ShareEventScheduleTagCode', 'MEMBER')

			
			vanity_slug = profile.get('VanitySlug', None)

			try:
				contact = Contact.objects.get(user__username=user_id)
			except Contact.DoesNotExist:
				user, created = User.objects.get_or_create(username=user_id)
				if created:
					user.set_password(''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8)))
					user.save()

				contact, created = Contact.objects.get_or_create(user=user)
				contact.save()

			if (contact.personal_url == '' or not contact.personal_url) and personal_url:
				contact.personal_url = personal_url

			if (contact.linkedin_url == '' or not contact.linkedin_url) and linkedin_url:
				contact.linkedin_url = linkedin_url

			if (contact.facebook_url == '' or not contact.facebook_url) and facebook_url:
				contact.facebook_url = facebook_url

			if (contact.twitter_url == '' or not contact.twitter_url) and twitter_url:
				contact.twitter_url = twitter_url

			if (contact.about_me == '' or not contact.about_me) and about_me:
				contact.about_me = about_me

			contact.save()

			profile, created = IndividualProfile.objects.get_or_create(contact = contact)
			profile.slug = vanity_slug
			profile.share_profile = share_profile
			profile.share_contact = share_contact
			profile.share_bio = share_bio
			profile.share_social = share_social
			profile.share_education = share_education
			profile.share_jobs = share_jobs
			profile.share_events = share_events
			profile.share_resume = share_resume
			profile.share_conference = share_conference
			profile.save()
			
			print("imported profile for user: " + user_id)
		except Exception as e:
			print("error importing profile for user : " + user_id)
			print("error message: " + str(e))

def get_profiles_uploads():
	"""
	imports all profile upload data from old site to django
	"""
	url = node_url + 'profiles/uploads'

	r = requests.get(url)

	uploads = r.json()['data']

	planning_path = 'https://www.planning.org/upload/'

	# create the new upload type profile/photo and profile/resume

	# Stores a possible type of upload (such as "Supplemental Materials")

	#filetype, created = FileType.objects.get_or_create(extension='.png', title='.png')

	#profile_photo_allowed_types = FileType.objects.filter(Q(extension='.png') | Q(extension='.jpg'))
	upload_type_profile_photo = UploadType.objects.get(code='PROFILE_PHOTOS')

	#upload_type_profile_photo.allowed_types.add(*profile_photo_allowed_types)
	#upload_type_profile_photo.save()

	#profile_resume_allowed_types = FileType.objects.filter(Q(extension='.doc') | Q(extension='.docx') | Q(extension='.pdf') | Q(extension='.png'))
	upload_type_profile_resume = UploadType.objects.get(code='RESUMES')

	#upload_type_profile_resume.allowed_types.add(*profile_resume_allowed_types)
	#upload_type_profile_resume.save()

	upload_errors = {}
	for upload in uploads:
		try:
			folder = upload.get('Folder')
			file_name = upload.get('FileName')
			user_id = upload.get('WebUserID')

			image_path = planning_path + folder + '/' + file_name
			print("file path: " + image_path)
			if folder == 'profile\photo':
				upload_type = upload_type_profile_photo
			else:
				upload_type = upload_type_profile_resume

			contact = Contact.objects.get(user__username=user_id)

			file_extension = "." + file_name.split('.')[-1]
			
			response = urlopen(image_path)
			io = BytesIO(response.read())
			profile, created = IndividualProfile.objects.get_or_create(contact = contact)

			if upload_type.code == 'PROFILE_PHOTOS':
				image_name = str(user_id) + file_extension # this is actually the path?

				image_upload, created = ImageUpload.objects.get_or_create(upload_type = upload_type, code=image_name)
				image_upload.image_file.save(image_name, File(io))
				profile.image = image_upload
				profile.save()
			else:
				document_name = str(user_id) + file_extension
				document_upload, created = DocumentUpload.objects.get_or_create(upload_type = upload_type, code = document_name)
				document_upload.uploaded_file.save(document_name, File(io))
				profile.resume = document_upload
				profile.save()
		except Exception as e:
			print("error uploading: " + str(e))
			upload_errors[user_id] = str(e)


	print(upload_errors)

def get_job_history():
	"""
	job history for My APA
	"""
	url = node_url + 'profiles/jobhistory'

	r = requests.get(url)

	jobhistory = r.json()['data']

	job_errors = {}

	for job in jobhistory:
		try:
			user_id = job.get('WebUserID')
			job_id = job.get('JobID')
			title = job.get('JobTitle')
			company = job.get('CompanyName')
			city = job.get('City')
			state = job.get('StateProvince')
			country = job.get('Country')

			full_time_present = job.get('FullTimeIsPresent')
			part_time_present = job.get('PartTimeIsPresent')

			full_time_start_date = job.get('FullTimeStartDate')
			if full_time_start_date:
				full_time_start_date = full_time_start_date.split("T",1)[0]

			full_time_end_date = job.get('FullTimeEndDate')
			if full_time_end_date:
				full_time_end_date = full_time_end_date.split("T",1)[0]

			part_time_start_date = job.get('PartTimeStartDate')
			if part_time_start_date:
				part_time_start_date = part_time_start_date.split("T",1)[0]
			
			part_time_end_date = job.get('PartTimeEndDate')
			if part_time_end_date:
				part_time_end_date = part_time_end_date.split("T",1)[0]

			is_part_time = False
			is_current = False
			try:
				contact = Contact.objects.get(user__username=user_id)
			except Contact.DoesNotExist:
				user, created = User.objects.get_or_create(username=user_id)
				if created:
					user.set_password(''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8)))
					user.save()

				contact = Contact.objects.create(user=user)

			individual_contact, created = IndividualContact.objects.get_or_create(user__username=user_id)

			if full_time_present or part_time_present:
				is_current = True

			if full_time_start_date and full_time_start_date != '1900-01-01':
				start_date = full_time_start_date
				end_date = full_time_end_date
			else:
				start_date = part_time_start_date
				end_date = part_time_end_date
				is_part_time = True

			user_job, created =  JobHistory.objects.get_or_create(contact=individual_contact, title=title, company=company, city=city, state=state, country=country, start_date=start_date, end_date=end_date, is_current=is_current, is_part_time=is_part_time)

			print('Job created for user: ' + str(user_id) + " | job : " + title)

		except Exception as e:
			print("error importing job for user : " + str(user_id))
			print("error: " + str(e))

			job_errors[user_id] = str(e)
			continue

	print(job_errors)

def get_degree():
	"""
	imports degrees
	"""
	url = node_url + 'profiles/degree'

	r = requests.get(url)

	degrees = r.json()['data']

	degree_errors = {}
	school_missing = set()
	for degree in degrees:
		try:
			user_id = degree.get('ID')
			school_id = degree.get('SCHOOL_ID')
			school_other = degree.get('SCHOOL_OTHER')
			degree_level = degree.get('DEGREE_LEVEL')
			degree_date = degree.get('DEGREE_DATE')
			degree_planning = degree.get('DEGREE_PLANNING')

			if degree_date:
				degree_date = degree_date.split('T',1)[0]

			user, created = User.objects.get_or_create(username=user_id)
			contact, created = IndividualContact.objects.get_or_create(user=user)

			if not degree_planning:
				degree_planning = False

			if school_id and school_id != 0 and school_id != "0":
				try:
					school = School.objects.get(user__username=school_id)
					my_degree, created = EducationalDegree.objects.get_or_create(contact=contact, school=school, level=degree_level, is_planning=degree_planning, graduation_date = degree_date)
			
				except Exception as e:
					if school_other and school_other != '':
						my_degree, created = EducationalDegree.objects.get_or_create(contact=contact, other_school=school_other, level=degree_level, is_planning=degree_planning, graduation_date=degree_date)
						#degree_errors[user_id] = "school does not exist: " + str(school_id) + ". added school other."
						school_missing.add(school_id)
					else:

						degree_errors[user_id] ="school does not exist: " + str(school_id) + ". No school other field was used."
						school_missing.add(school_id)
					pass

			else:
				my_degree, created = EducationalDegree.objects.get_or_create(contact=contact, other_school=school_other, level=degree_level, is_planning=degree_planning, graduation_date=degree_date)
			print('imported education for user_id' + str(user_id))
		except Exception as e:
			degree_errors[user_id] = str(e)
			continue

	print("degree errors: " + str(degree_errors))
	print("missing schools: " + str(school_missing))

def update_users():
	"""
	this guy will attempt to update/create ALL users in T3go!
	"""

	url = node_url + 'webuser/all'

	r = requests.get(url)

	webusers = r.json()['data']

	user_import_error = {}

	for webuser in webusers:
		try:
			user_id = webuser.get('ID')

			webuser_url = node_url + 'webuser/' + user_id

			webuser_request = requests.get(webuser_url)

			webuser_data = webuser_request.json()['data'][0]

			member_type = webuser_data.get('MEMBER_TYPE')
			company = webuser_data.get('COMPANY')
			first_name = webuser_data.get('FIRST_NAME')
			last_name = webuser_data.get('LAST_NAME')
			middle_name = webuser_data.get('MIDDLE_NAME')
			suffix = webuser_data.get('SUFFIX')
			prefix = webuser_data.get('PREFIX')
			designation = webuser_data.get('DESIGNATION')
			informal = webuser_data.get('INFORMAL')
			work_phone = webuser_data.get('WORK_PHONE')
			home_phone = webuser_data.get('HOME_PHONE')
			phone = webuser_data.get('PHONE')
			address1 = webuser_data.get('ADDRESS_1')
			address2 = webuser_data.get('ADDRESS_2')
			city = webuser_data.get('CITY')
			state = webuser_data.get('STATE_PROVINCE')
			address_num = webuser_data.get('ADDRESS_NUM')
			zip_code = webuser_data.get('ZIP')
			email = webuser_data.get('EMAIL')
			country = webuser_data.get('COUNTRY')
			ecp = webuser_data.get('CATEGORY')

			about_me = webuser_data.get('AboutMe', None)
			personal_url = webuser_data.get('PersonalUrl', None)
			linkedin_url = webuser_data.get('LinkedInUrl', None)
			facebook_url = webuser_data.get('FacebookUrl', None)
			twitter_url = webuser_data.get('TwitterUrl', None)

			
			vanity_slug = webuser_data.get('VanitySlug', None)

			share_profile = webuser_data.get('ShareTagCode', 'PRIVATE')

			if not share_profile:
				share_profile = 'PRIVATE'

			share_contact = webuser_data.get('ShareContactTagCode', 'MEMBER')

			if not share_contact:
				share_contact = 'MEMBER'

			share_bio = webuser_data.get('ShareBioTagCode', 'PUBLIC')

			if not share_bio:
				share_bio = 'PUBLIC'

			share_social = webuser_data.get('ShareSocialMediaTagCode', 'MEMBER')

			if not share_social:
				share_social = 'MEMBER'

			share_education = webuser_data.get('ShareEducationTagCode', 'MEMBER')

			if not share_education:
				share_education = 'MEMBER'

			share_jobs = webuser_data.get('ShareJobsTagCode', 'MEMBER')

			if not share_jobs:
				share_jobs = 'MEMBER'			
			share_events = webuser_data.get('ShareCMTagCode', 'MEMBER')

			if not share_events:
				share_events = 'MEMBER'	

			share_resume = webuser_data.get('ShareResumeTagCode', 'MEMBER')

			if not share_resume:
				share_resume = 'MEMBER'	

			share_conference = webuser_data.get('ShareEventScheduleTagCode', 'MEMBER')

			if not share_conference:
				share_conference = 'MEMBER'	
			
			vanity_slug = webuser_data.get('VanitySlug', None)

			user, created = User.objects.get_or_create(username=user_id)
			user.first_name = first_name
			user.last_name = last_name
			user.email = email
			user.save()

			contact, created = Contact.objects.get_or_create(user=user)
			contact.member_type = member_type
			contact.company = company
			contact.first_name = first_name
			contact.last_name = last_name
			contact.middle_name = middle_name
			contact.suffix_name = suffix
			contact.prefix_name = prefix
			contact.designation = designation
			contact.phone = phone
			contact.address1 = address1
			contact.address2 = address2
			contact.state = state
			contact.city = city
			contact.zip_code = zip_code
			contact.country = country
			contact.email = email
			contact.ecp_type = ecp
			contact.slug = vanity_slug
			if (not contact.personal_url or contact.personal_url == '') and personal_url:
				contact.personal_url = personal_url

			if (not contact.linkedin_url or contact.linkedin_url == '') and linkedin_url:
				contact.linkedin_url = linkedin_url

			if (not contact.facebook_url or contact.facebook_url == '') and facebook_url:
				contact.facebook_url = facebook_url

			if (not contact.twitter_url or contact.twitter_url == '') and twitter_url:
				contact.twitter_url = twitter_url

			if (not contact.about_me or contact.about_me == '') and about_me:
				contact.about_me = about_me

			contact.save()

			profile, created = IndividualProfile.objects.get_or_create(contact = contact)
			profile.slug = vanity_slug
			profile.share_profile = share_profile
			profile.share_contact = share_contact
			profile.share_bio = share_bio
			profile.share_social = share_social
			profile.share_education = share_education
			profile.share_jobs = share_jobs
			profile.share_events = share_events
			profile.share_resume = share_resume
			profile.share_conference = share_conference
			profile.save()

			print('imported profile for user: ' + str(user_id))
		except Exception as e:
			print('error importing user: ' + user_id + '| error: ' + str(e))
			user_import_error[user_id] = str(e)
			continue

	print(user_import_error)

