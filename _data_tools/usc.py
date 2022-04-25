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
from content.utils import generate_random_string
from registrations.models import *

logger = logging.getLogger(__name__)

json_server='http://localhost:8081/dataimport';

node_url = "http://localhost:8081/dataimport/"

# import event, activity, then everything else..
def import_product():
	"""
	imports all products from the USC to django
	ASSUMES:
		1. if there is an existing content product, the USC_Product.ExternalCode = content.code
		2. if an activity, the parent event content = everything in between the product_code (ex. ACTIVITY_13CONF_W000 = 13CONF)

		*** DO THIS FIRST!! ***
		-- NO LONGER NEEDED [run import_tags()]
		run create_shipping_product()
		run import_tax()

	"""
	#['BOOK','STREAMING','DIGITAL_PUB','DONATION','EBOOK','EXAM_APPLICATION','EXAM_REGISTRATION','EVENT','ACTIVITY','SERVICE','ADJUSTMENT','AWARD',]
	product_type_codes = ['BOOK','STREAMING','DIGITAL_PUB','DONATION','EBOOK','EXAM_APPLICATION','EXAM_REGISTRATION','EVENT','ACTIVITY','SERVICE','ADJUSTMENT','AWARD',]
	

	for product_type_code in product_type_codes:
		url = node_url + 'products/' + product_type_code + '/all'

		r = requests.get(url)

		products = r.json()['data']

		#tag_type = TagType.objects.get(code='PRODUCT_FORMAT')

		# product type codes used in t3go
		if product_type_code == 'ACTIVITY':
			product_type_code = 'ACTIVITY_TICKET'
		if product_type_code == 'EVENT':
			product_type_code = 'EVENT_REGISTRATION'
		if product_type_code == "DIGITAL_PUB":
			product_type_code = 'PUBLICATION_SUBSCRIPTION'

		if product_type_code == "DIVISION_ONLY":
			product_type_code == "DIVISION"
		product_import_errors = {}

		for product in products:
			try:
				# 1. check if product exists in django
				product_code = product.get('ProductCode')
				product_id = product.get('ProductID')
				product_name = product.get('ProductName')
				product_description = product.get('ProductDescription')

				product_status = product.get('ProductStatus')
				product_default_price = product.get('ProductDefaultPrice') # add to product price?
				product_external_code = product.get('ExternalCode') # imis_code on product
				product_has_pricerules = product.get('HasPriceRules')
				product_required_groups = product.get('WebUserGroups') # add to product price 
				product_exclude_groups = product.get('ExcludeWebUserGroups') # add to product price
				product_custom_text_1 = product.get('CustomText1') # used for member types (MEM)... any other products
				product_future_groups = product.get('FutureWebUserGroups') # future_groups on product model
				product_quantity_available = product.get('QuantityAvailable') # max_quantity on product
				product_purchase_limit = product.get('PurchaseQuantityLimit') # max_quantity_per_person on product
				product_standby_available = product.get('StandbyAvailable') # max_quantity_standby on product
				product_sales_start_time = product.get('SalesStartDateTime')
				product_sales_end_time = product.get('SalesEndTime')
				product_has_options = product.get('HasOptions')
				product_hide_price = product.get('HidePrice')
				product_use_event_options = product.get('UseEventOptions')
				product_use_event_dates = product.get('UseEventDateRestrictions')
				product_subtitle = product.get('Subtitle')
				product_tied_to_product = product.get('TiedToProductCode')
				product_hasxhtml = product.get('HasXhtmlContent')
				product_isbn = product.get('ISBN')
				product_glaccount = product.get('TagCode')
				product_parent_code = product.get('ParentCode')
				product_published_date = product.get('ProductDate')
				product_shortdescription = product.get('ShortDescription')
				# for event (STREAMING) products
				product_credits = product.get('CreditApprovedNumber')
				product_law_credits = product.get('CreditLawApprovedNumber')
				product_ethics_credits = product.get('CreditEthicsApprovedNumber')
				product_series_number = product.get('SeriesNumber')

				product_file_location = product.get('FilesLocation')
				product_file_name = product.get('FileName')
				product_thumbnail_location = product.get('ThumbnailFilesLocation')
				product_thumbnail_file_name = product.get('ThumbnailFileName')

				# product format codes for book/e-book/streaming
				product_format_code = product.get('FormatCode')
				product_page_count = product.get('PageCount')
				product_table_of_contents = product.get('TableOfContents')
				product_reviews = product.get('Reviews')
				product_length_in_minutes = product.get('LengthInMinutes')
				product_publisher = product.get('Publisher')

				if product_format_code == 'USC_FORMAT_STREAMING':
					product_format_code = 'STREAMING'

				if product_published_date:
					product_published_date = product_published_date.replace('T00:00:00.000Z','')

				# isbn cannot be an integer ... too long.
				#if product_isbn:
				#	product_isbn = product_isbn.replace('-','')
				if product_type_code == 'ACTIVITY_TICKET' and product_parent_code is None:
					product_parent_code = product_code.split("_", 1)[1].split("_", 1)[0]

				if not product_glaccount:
					product_glaccount = "NONE"
				if not product_hasxhtml:
					product_hasxhtml = False
				if not product_subtitle:
					product_subtitle = ""

				######## content create ########
				try: 
					if product_type_code == 'ACTIVITY_TICKET':
						parent = Event.objects.filter(code=product_parent_code, publish_status='DRAFT').first().master
						if not parent:
							print('parent event could not be found')
							product_import_errors[product_external_code] = "parent could not be found for parent: " + product_parent_code
							continue
						event_code = product_external_code

						#Event.objects.filter(code=product_code, parent=parent).delete()
						content, created = Event.objects.get_or_create(code=event_code, parent=parent, publish_status='DRAFT')
						
					elif product_type_code == 'EVENT_REGISTRATION':

						event_code = product_external_code
			
						content, created = Event.objects.get_or_create(code=event_code, publish_status='DRAFT')
						if created:
							product_import_errors[event_code] = "Event did not exist. Created new one."
						# can remove this if we restore staging from a recent backup
					elif product_type_code == 'STREAMING':
							#Content.objects.filter(code=product_code).delete()
							# match off of streaming title
							streaming_code = product_code.split('_',1)[1]
							product_streaming_name = 'Streaming: ' + product_name

							if product_code in ('STR_TIP2D1','STR_TPFG','STR_T21CPC','STR_S531','STR_EXAM3','STR_TPCE','STR_TDRO','STR_TSPLRO','STR_TIP1','STR_S582','STR_TIZBAD','STR_S552','STR_TGPGC'):
								content, created = Content.objects.get_or_create(content_type='PRODUCT', code=product_code, publish_status='DRAFT')
								content.content_type='PRODUCT'
							elif product_code == 'STR_TSCMDFP1':
								content = Event.objects.get(master__id=3017011, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_S583':
								content = Event.objects.get(master__id=3031109, publish_status='DRAFT', event_type='COURSE')

							elif product_code == 'STR_TAZC':
								content = Event.objects.get(master__id=3027250, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TZSSB':
								content = Event.objects.get(master__id=3023665, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TPL12':
								content = Event.objects.get(master__id=3021797, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TPPDR':
								content = Event.objects.get(master__id=3024413, publish_status='DRAFT', event_type='COURSE')

							elif product_code == 'STR_TBFD':
								content = Event.objects.get(master__id=3018804, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_THDPPL':
								content = Event.objects.get(master__id=3026207, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TSCPW1':
								content = Event.objects.get(master__id=3017012, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TSGSTRA':
								content = Event.objects.get(master__id=3026206, publish_status='DRAFT', event_type='COURSE')

							elif product_code == 'STR_TATP':
								content = Event.objects.get(master__id=3018444, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_S526':
								content = Event.objects.get(master__id=3031104, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TUAFSP':
								content = Event.objects.get(master__id=3021815, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_S557':
								content = Event.objects.get(master__id=3031106, publish_status='DRAFT', event_type='COURSE')

							elif product_code == 'STR_TATP':
								content = Event.objects.get(master__id=3018444, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_S526':
								content = Event.objects.get(master__id=3031104, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TUAFSP':
								content = Event.objects.get(master__id=3021815, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_S557':
								content = Event.objects.get(master__id=3031106, publish_status='DRAFT', event_type='COURSE')

							elif product_code == 'STR_TSME':
								content = Event.objects.get(master__id=3019664, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TRRUF':
								content = Event.objects.get(master__id=3024187, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TPKOONTZ':
								content = Event.objects.get(master__id=3025006, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TPHC':
								content = Event.objects.get(master__id=3028199, publish_status='DRAFT', event_type='COURSE')

							elif product_code == 'STR_TPL11':
								content = Event.objects.get(master__id=3019620, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TPBP':
								content = Event.objects.get(master__id=3025005, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_S615':
								content = Event.objects.get(master__id=3030904, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_S546':
								content = Event.objects.get(master__id=3030984, publish_status='DRAFT', event_type='COURSE')

							elif product_code == 'STR_TRPA':
								content = Event.objects.get(master__id=3021812, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TPSE':
								content = Event.objects.get(master__id=3019619, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TFRECP':
								content = Event.objects.get(master__id=3024185, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TVMT':
								content = Event.objects.get(master__id=3027043, publish_status='DRAFT', event_type='COURSE')

							elif product_code == 'STR_TTPF':
								content = Event.objects.get(master__id=3030544, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TDSUFD':
								content = Event.objects.get(master__id=3021799, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TPLEFD':
								content = Event.objects.get(master__id=3021810, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TRFALU':
								content = Event.objects.get(master__id=3021811, publish_status='DRAFT', event_type='COURSE')

							elif product_code == 'STR_TPEL':
								content = Event.objects.get(master__id=3025590, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TSCEBS':
								content = Event.objects.get(master__id=3021142, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TCSM':
								content = Event.objects.get(master__id=3028923, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TSOCPD':
								content = Event.objects.get(master__id=3021814, publish_status='DRAFT', event_type='COURSE')

							elif product_code == 'STR_TESACC':
								content = Event.objects.get(master__id=3024186, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TMHTP':
								content = Event.objects.get(master__id=3021800, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TAEP':
								content = Event.objects.get(master__id=3018445, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TMCRP':
								content = Event.objects.get(master__id=3027251, publish_status='DRAFT', event_type='COURSE')

							elif product_code == 'STR_S618':
								content = Event.objects.get(master__id=3030900, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TZTSUF':
								content = Event.objects.get(master__id=3024414, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_S558':
								content = Event.objects.get(master__id=3031053, publish_status='DRAFT', event_type='COURSE')
							elif product_code == 'STR_TFIADST':
								content = Event.objects.get(master__id=3026208, publish_status='DRAFT', event_type='COURSE')

							elif product_code == 'STR_TPDRC':
								content = Event.objects.get(master__id=9005255, publish_status='DRAFT', event_type='COURSE')

							elif Event.objects.filter(title=product_streaming_name, publish_status='DRAFT', event_type='COURSE').exists():
								content = Event.objects.get(title=product_streaming_name, publish_status='DRAFT', event_type='COURSE')
							elif Event.objects.filter(title=product_name, publish_status='DRAFT', event_type='COURSE').exists():
								content = Event.objects.get(title=product_name, publish_status='DRAFT', event_type='COURSE')
							elif Event.objects.filter(code=streaming_code, publish_status='DRAFT', event_type='COURSE').exists():
								content = Event.objects.get(code=streaming_code, publish_status='DRAFT', event_type='COURSE')
							else:
								print('error finding streaming content...')
								product_import_errors[product_code] = "unable to find content"
								content, created = Event.objects.get_or_create(title=product_streaming_name,code=streaming_code, publish_status='DRAFT', event_type='COURSE')
								product_import_errors[product_code] = "could not find streaming content. created new one."
	
							content.resource_type = "E_LEARNING"
							content.length_in_minutes = product_length_in_minutes
					elif product_type_code == 'EBOOK':
						Content.objects.filter(code=product_code).delete()
						content, created = EBook.objects.get_or_create(code=product_code, publish_status='DRAFT')

						content.page_count = product_page_count
						content.table_of_contents = product_table_of_contents
						content.publication_format = product_format_code
					elif product_type_code == 'BOOK':
						# dupe key errors on republishing 
						Book.objects.filter(code=product_code).delete()
						content, created = Book.objects.get_or_create(code=product_code, publish_status='DRAFT')

						content.page_count = product_page_count
						content.table_of_contents = product_table_of_contents
						if not product_format_code:
							product_format_code = 'PAPERBACK'
						content.publication_format = product_format_code

					elif product_type_code == 'PUBLICATION_SUBSCRIPTION':
						content, created = Document.objects.get_or_create(code=product_code, publish_status='PUBLISHED')
						import_publication(content, product_thumbnail_file_name, product_file_name, product_code)
					else:

						content, created = Content.objects.get_or_create(code=product_code, publish_status='DRAFT')
						content.content_type='PRODUCT'

					if not content.subtitle or content.subtitle == '':
						content.subtitle = product_subtitle
					if not content.title or content.title == '':
						content.title = product_name
					if not content.status:
						content.status = product_status
					if not content.description or content.description == '':
						content.description = product_shortdescription
					if not content.text or content.text == '':
						content.text = product_description
					if not content.has_xhtml:
						content.has_xhtml = product_hasxhtml
					if not content.isbn or content.isbn == '':
						content.isbn = product_isbn
					if not content.resource_published_date:
						content.resource_published_date = product_published_date

					#content.volume_number = product_series_number
					if product_publisher and product_publisher != '':
						contact_role, created = ContactRole.objects.get_or_create(content=content, role_type='PUBLISHER', company=product_publisher)
					content.save()

				except Exception as e:
					print("error import/create content.   " + str(e))
					print(str(product_external_code))
					product_import_errors[product_code] = str(e)
					pass


				######## product create ########
				try:
					if product_type_code == 'EVENT_REGISTRATION' or product_type_code == 'ACTIVITY_TICKET':
						product, created = Product.objects.get_or_create(code = event_code,content = content)
					elif product_type_code=='PUBLICATION_SUBSCRIPTION':
						product, created = Product.objects.get_or_create(code = product_code,content = content)
						product.product_type = 'PUBLICATION_SUBSCRIPTION'
						product.publish_status='PUBLISHED'
					else:
						product, created = Product.objects.get_or_create(code = product_code,content = content)

					if created:
						product.title = product_name
						product.status = product_status
						product.description = product_shortdescription
						product.product_type = product_type_code
						product.imis_code = product_external_code #verify
						product.max_quantity = product_quantity_available
						product.max_quantity_per_person = product_purchase_limit
						product.max_quantity_standby = product_standby_available
						product.gl_account = product_glaccount
						product.reviews = product_reviews

					if product_type_code == 'BOOK':
						product.shippable = True
						
					if product_future_groups is not None:
						product_future_groups_list = product_future_groups.split(",")
						product_future_groups_list = list(filter(None, product_future_groups_list))

						product.future_groups.all().delete()

						for group in product_future_groups_list:
							try:
								group = Group.objects.get(name=group)
								product.future_groups.add(group)
							except Group.DoesNotExist:
								print("group name: " + group + "is missing in t3go")
							except Exception as e:
								print("Error adding groups: " + str(e))

					product.save()
					print("product: " + product_name + " imported.")

				except Exception as e:
					print("error import/create product.   " + str(e))
					print(str(content))
					product_import_errors[product_code] = str(e)
					pass

				if product_type_code == 'STREAMING':
					content.resource_url = product_file_name

				if product_type_code in ('BOOK','EBOOK','STREAMING'):
					# add thumbnail to AWS
					import_thumbnail(content, product_type_code, product_thumbnail_location, product_thumbnail_file_name)

				if product_type_code == 'EBOOK':
					import_ebook(content, product_type_code, product_file_location, product_file_name)

				# create product price for this
				if product_default_price or product_default_price == 0:
					ProductPrice.objects.filter(product=product, title="List Price").delete()

					productprice, created = ProductPrice.objects.get_or_create(product=product, title = "List Price")
					productprice.priority = 99
					productprice.price = product_default_price
					productprice.include_search_results = False # what should this be?

					if product_type_code == 'PUBLICATION_SUBSCRIPTION':
						productprice.publish_status='PUBLISHED'
					productprice.save()

				import_product_option(product, product_code)

				# adds price rules for the product where no options exist
				import_product_price(product, product_code)

				if product_type_code not in ('EVENT','STREAMING','ACTIVITY'):
					import_authorities(content, product)

				# content = Content.objects.get(id=content.id)
				if product_type_code != "PUBLICATION_SUBSCRIPTION":
					try:
						content.publish()
					except Exception as e:
						print("publish error: ")
						print(str(e))


			except Exception as e:
				print("error importing product... passing")
				print("error: " + str(e))
				product_import_errors[product_code] = str(e)
				pass
			
		print(product_import_errors)

def import_product_event_fix():
	"""
	code to fix the product codes for event and activities 
	"""
	#['BOOK','STREAMING','DIGITAL_PUB','DONATION','EBOOK','EXAM_APPLICATION','EXAM_REGISTRATION','EVENT','ACTIVITY','SERVICE','ADJUSTMENT','AWARD',]
	product_type_codes = ['EVENT','ACTIVITY']

	for product_type_code in product_type_codes:
		url = node_url + 'products/' + product_type_code + '/all'

		r = requests.get(url)

		products = r.json()['data']

		#tag_type = TagType.objects.get(code='PRODUCT_FORMAT')

		# product type codes used in t3go
		if product_type_code == 'ACTIVITY':
			product_type_code = 'ACTIVITY_TICKET'
		if product_type_code == 'EVENT':
			product_type_code = 'EVENT_REGISTRATION'
		product_import_errors = {}

		for product in products:
			try:
				# 1. check if product exists in django
				product_code = product.get('ProductCode')
				product_id = product.get('ProductID')
				product_name = product.get('ProductName')
				product_description = product.get('ProductDescription')

				product_status = product.get('ProductStatus')
				product_default_price = product.get('ProductDefaultPrice') # add to product price?
				product_external_code = product.get('ExternalCode') # imis_code on product
				product_has_pricerules = product.get('HasPriceRules')
				product_required_groups = product.get('WebUserGroups') # add to product price 
				product_exclude_groups = product.get('ExcludeWebUserGroups') # add to product price
				product_custom_text_1 = product.get('CustomText1') # used for member types (MEM)... any other products
				product_future_groups = product.get('FutureWebUserGroups') # future_groups on product model
				product_quantity_available = product.get('QuantityAvailable') # max_quantity on product
				product_purchase_limit = product.get('PurchaseQuantityLimit') # max_quantity_per_person on product
				product_standby_available = product.get('StandbyAvailable') # max_quantity_standby on product
				product_sales_start_time = product.get('SalesStartDateTime')
				product_sales_end_time = product.get('SalesEndTime')
				product_has_options = product.get('HasOptions')
				product_hide_price = product.get('HidePrice')
				product_use_event_options = product.get('UseEventOptions')
				product_use_event_dates = product.get('UseEventDateRestrictions')
				product_subtitle = product.get('Subtitle')
				product_tied_to_product = product.get('TiedToProductCode')
				product_hasxhtml = product.get('HasXhtmlContent')
				product_isbn = product.get('ISBN')
				product_glaccount = product.get('TagCode')
				product_parent_code = product.get('ParentCode')
				product_published_date = product.get('ProductDate')
				product_shortdescription = product.get('ShortDescription')
				# for event (STREAMING) products
				product_credits = product.get('CreditApprovedNumber')
				product_law_credits = product.get('CreditLawApprovedNumber')
				product_ethics_credits = product.get('CreditEthicsApprovedNumber')
				product_series_number = product.get('SeriesNumber')

				product_file_location = product.get('FilesLocation')
				product_file_name = product.get('FileName')
				product_thumbnail_location = product.get('ThumbnailFilesLocation')
				product_thumbnail_file_name = product.get('ThumbnailFileName')

				# product format codes for book/e-book/streaming
				product_format_code = product.get('FormatCode')
				product_page_count = product.get('PageCount')
				product_table_of_contents = product.get('TableOfContents')
				product_reviews = product.get('Reviews')
				product_length_in_minutes = product.get('LengthInMinutes')
				product_publisher = product.get('Publisher')

				if product_published_date:
					product_published_date = product_published_date.replace('T00:00:00.000Z','')

				# isbn cannot be an integer ... too long.
				#if product_isbn:
				#	product_isbn = product_isbn.replace('-','')
				if product_type_code == 'ACTIVITY_TICKET' and product_parent_code is None:
					product_parent_code = product_code.split("_", 1)[1].split("_", 1)[0]

				######## content create ########
				try: 
					if product_type_code == 'ACTIVITY_TICKET':
						parent = Event.objects.filter(code=product_parent_code, publish_status='DRAFT').first()
						if parent:
							parent = parent.master
						if not parent:
							print('parent event could not be found..attempting to link to  code=productcode')

							parent = Event.objects.filter(code='EVENT_' + product_parent_code, publish_status='DRAFT').first()
							if parent:
								parent = parent.master
							else:
								product_import_errors[product_external_code] = "parent could not be found for parent: " + product_parent_code
								continue
						event_code = product_external_code
						try:
							content  = Event.objects.filter(code=event_code, parent=parent, publish_status='DRAFT').first()
						except Event.DoesNotExist:
							content = Event.objects.filter(code=product_code, parent=parent, publish_status='DRAFT').first()
							continue

					elif product_type_code == 'EVENT_REGISTRATION':

						event_code = product_external_code
						try:
							content  = Event.objects.filter(code=event_code, publish_status='DRAFT').first()
						except Event.DoesNotExist:
							content = Event.objects.filter(code=product_code, publish_status='DRAFT').first()

				except Exception as e:
					print("error import/create content.   " + str(e))
					print(str(product_external_code))
					product_import_errors[product_code] = str(e)
					pass


				######## product create ########
				try:

					product, created = Product.objects.get_or_create(content = content)
					product.code = product_code
					product.save()

					print("product: " + product_name + " imported.")

					if created:
						# this product did not exist prior to the import script fix. create a generic product price so orders can be attached
						productprice, created = ProductPrice.objects.get_or_create(product=product, title="List Price", price=0)
				except Exception as e:
					print("error import/create product.   " + str(e))
					print(str(content))
					product_import_errors[product_code] = str(e)
					pass


				try:
					content.publish()
				except Exception as e:
					print("publish error: ")
					print(str(e))


			except Exception as e:
				print("error importing product... passing")
				print("error: " + str(e))
				product_import_errors[product_code] = str(e)
				pass
			
		print(product_import_errors)


def import_ebook(content, product_type_code, file_location, file_name):
	"""
	imports ebook products
	"""
	try:

		file_path = 'https://www.planning.org/' + file_location + file_name

		# filetype, created = FileType.objects.get_or_create(extension='.pdf', title='.pdf')
		# filetype, created = FileType.objects.get_or_create(extension='.mobi', title='.mobi')
		# filetype, created = FileType.objects.get_or_create(extension='.epub', title='.epub')

		# epub_allowed_types = FileType.objects.filter(Q(extension='.pdf') | Q(extension='.mobi') | Q(extension='.epub'))
		# upload_type_store_ebooks, created = UploadType.objects.get_or_create(allowed_min=0, allowed_max=1, max_file_size=10000, folder='store/ebook/document', code='STORE_EBOOK_DOCUMENT', title='Store E-Book Document')

		# upload_type_store_ebooks.allowed_types.add(*epub_allowed_types)
		# upload_type_store_ebooks.save()

		response = urlopen(file_path)
		io = BytesIO(response.read())

		# ebook_upload, created = Upload.objects.get_or_create(upload_type = upload_type_store_ebooks, code = file_name)
		# ebook_upload.content = content

		content.publication_download.save(file_name, File(io))
		content.save()

	except Exception as e:
		print("error importing ebook: " + str(e))
		pass

def import_publication(content, product_thumbnail_file_name, product_file_name, product_code):

	try:


		file_type = product_file_name.split('.',1)[1]
		product_file = 'product_' + product_code + '.' + file_type
		file_path = 'https://www.planning.org' + product_file_name

		response = urlopen(file_path)
		io = BytesIO(response.read())


		content.uploaded_file.save(product_file, File(io))

		product_thumbnail_type = product_thumbnail_file_name.split('.',1)[1]
		product_thumbnail_name = 'thumbnail_' + product_code + '.' + product_thumbnail_type
		file_path = 'https://www.planning.org' + product_thumbnail_file_name

		response = urlopen(file_path)
		io = BytesIO(response.read())

		content.image_file.save(product_thumbnail_name, File(io))
		content.save()
	except Exception as e:
		pass
		print("error importing ebook: " + str(e))

def import_thumbnail(content, product_type_code, thumbnail_file_location, thumbnail_file_name):
	"""
	imports thumbnail images to AWS
	"""
	try:
		image_path = 'https://www.planning.org' + thumbnail_file_location + thumbnail_file_name

		# filetype, created = FileType.objects.get_or_create(extension='.png', title='.png')

		# thumbnail_allowed_types = FileType.objects.filter(Q(extension='.png') | Q(extension='.jpg'))
		# upload_type_store_thumbnail, created = UploadType.objects.get_or_create(allowed_min=0, allowed_max=1, max_file_size=5000, folder='store/thumbnail', code='STORE_THUMBNAIL', title='Store Thumbnail')

		# upload_type_store_thumbnail.allowed_types.add(*thumbnail_allowed_types)
		# upload_type_store_thumbnail.save()

		
		response = urlopen(image_path)
		io = BytesIO(response.read())

		# image_upload, created = ImageUpload.objects.get_or_create(upload_type = upload_type_store_thumbnail, code=thumbnail_file_name)
		# image_upload.content = content
		# image_upload.image_file.save(thumbnail_file_name, File(io))

		content.thumbnail.save(thumbnail_file_name, File(io))
		content.save()
	except Exception as e:
		pass
		print("ERROR IMPORTING thumbnail: " + str(e))

def import_product_option(product, product_code):
	"""
	creates/updates all product options for a single product code
	MISSING FIELD: GL_ACCOUNT!!!
	"""

	url = node_url + 'products/' + product_code+ '/options'

	r = requests.get(url)

	options = r.json()['data']

	for option in options:
		option_external_code = option.get('ExternalCode')
		option_name = option.get('OptionName')
		option_description = option.get('OptionDescription')
		option_priority = option.get('OptionPriority')
		option_status = option.get('OptionStatus')
		option_id = option.get('OptionID')
		try:
			option, created = ProductOption.objects.get_or_create(product=product, code = option_external_code)

			if created:
				option.title = option_name
				option.code = option_external_code
				option.description = option_description
				option.status = option_status
				option.sort_number = option_priority
				option.save()
			print("product option: " + option_name + " imported.")
		except Exception as e:
			print("error import/create product.   " + str(e))

		# adds only the price rules for the particular product option
		import_product_price(product, product_code, option_id, option_external_code)

def import_product_price(product, product_code,  option_id = None, option_code = None):
	"""
	creates product price records for a product and/or option passed
	"""


	url = node_url + 'products/' + product_code + '/options/'

	if not option_id:
		url += 'none/prices'
	else:
		url += str(option_id) + '/prices'

	r = requests.get(url)

	prices = r.json()['data']

	for price in prices:
		price_name = price.get('PriceRuleName')
		price_priority = price.get('PriceRulePriority')
		price_status = price.get('PriceRuleStatus')
		price_webusergroups = price.get('WebUserGroups')
		price_excludegroups = price.get('ExcludeWebUserGroups')
		price_begintime = price.get('StartDateTime')
		price_endtime = price.get('EndDateTime')
		price_code = price.get('ExternalCode')
		price_price = price.get('ProductPrice')

		price_id = price.get('PriceRuleID')

		try:
			productprice = ProductPrice.objects.get(product=product, legacy_id=price_id)
		except Exception as e:

			print("error: " + str(e))
			productprice, created = ProductPrice.objects.get_or_create(product=product, title=price_name)
			productprice.legacy_id = price_id
		productprice.title = price_name
		productprice.priority = price_priority
		productprice.price = price_price
		# productprice.imis_reg_class = ??
		
		if price_webusergroups is not None:
			price_webusergroups_list = price_webusergroups.split(",")
			price_webusergroups_list = list(filter(None, price_webusergroups_list))
			for group in price_webusergroups_list:
				try:
					group = Group.objects.get(name=group)
					productprice.required_groups.add(group)
				except Exception as e:
					print("group name: " + group + " is missing in t3go")
					print("exception: " + str(e))
					continue
		if price_excludegroups is not None:
			price_excludegroups_list = price_excludegroups.split(",")
			price_excludegroups_list = list(filter(None, price_excludegroups_list))
			for group in price_excludegroups_list:
				try:
					group = Group.objects.get(name=group)
					productprice.exclude_groups.add(group)
				except Exception as e:
					print("group name: " + group + " is missing in t3go")
					print("exception: " + str(e))
					continue

		productprice.option_code = option_code
		productprice.begin_time = price_begintime
		if product.product_type in ('BOOK','STREAMING','EBOOK') and price_name not in ('APA member','PAS subscriber','Regular Price','PDO price','APA Staff Price','NPC15 attendee','AICP member','Group viewing','Nonmember'):
			productprice.end_time = price_endtime

		if product.product_type == 'PUBLICATION_SUBSCRIPTION':
			productprice.publish_status='PUBLISHED'

		productprice.save()
		print("product price: " + price_name + " imported.")

def import_authorities(content, product):
	"""
	import authors and providers
	"""

	url = node_url + 'products/' + product.code + '/authorities'

	r = requests.get(url)

	authorities = r.json()['data']

	for authority in authorities:

		try:
			webuserid = authority.get('WebUserID', None)
			contact_type = authority.get('AuthorityTypeCodes')
			designation = authority.get('Designation')
			sort_number = authority.get('SortNumber')
			first_name = authority.get('FirstName')
			middle_name = authority.get('MiddleName')
			last_name = authority.get('LastName')
			suffix = authority.get('Suffix')
			bio = authority.get('AuthorityBio')
			organization_name = authority.get('OrganizationName')

			if webuserid:
				contact, created = Contact.objects.get(user_id=webuserid)
				contact_role, created = ContactRole.objects.get_or_create(content=content, contact=contact)
			else:
				contact_role, created = ContactRole.objects.get_or_create(content=content, first_name=first_name, last_name=last_name, contact__isnull=True)
			
			if created:
				contact_role.first_name = first_name
				contact_role.middle_name = middle_name
				contact_role.last_name = last_name
				contact_role.bio = bio
				contact_role.role_type = contact_type
				contact_role.sort_number = sort_number
				contact_role.save()

			print("imported user for content: " + str(content))
		except Exception as e:
			continue
			print("error importing contact ")
			print(str(e))


# def import_orders():
# 	"""
# 	imports all shopping cart orders into t3go
# 	"""

# 	# there are 86 order groups
# 	# groups are made of 1000 orders

# 	number_of_groups = 86
# 	order_errors = {}

# 	for x in range(1, number_of_groups):

#    		try:
#    			print("importing order range number: " + str(x))
#    			order_url = ('http://localhost:8081/dataimport/orders/%s' % x)

#    			r = requests.get(order_url)

#    			orders = r.json()['data']
#    			for order in orders:
#    				try:
# 	   				order_id = order.get('OrderID')
# 	   				webuserid = order.get('WebUserID')
# 	   				order_status = order.get('OrderStatus')
# 	   				last_updated_by_id = order.get('LastUpdatedByID')
# 	   				is_manual = order.get('IsManualOrder', False)
# 	   				order_submitted_date = order.get('SubmittedDateTime')

# 	   				if order_status == 'A':
# 	   					order_status = 'PROCESSED'
# 	   				elif order_status == 'P':
# 	   					order_status = 'SUBMITTED'
# 	   				elif order_status == 'X' or order_status == 'CAN':
# 	   					order_status = 'CANCELLED'

# 	   				try:

# 	   					print("importing order id : " + str(order_id))
# 	   					order_submitted_date = order_submitted_date.split(".", 1)[0]
# 	   					user, created = User.objects.get_or_create(username=webuserid)
# 	   					user_order, created = Order.objects.get_or_create(legacy_id = order_id, user = user, submitted_time = order_submitted_date)
# 	   					user_order.order_status = order_status
# 	   					user_order.submitted_user_id = last_updated_by_id
# 	   					user_order.is_manual = is_manual
# 	   					user_order.save()
# 	   				except Exception as e:
# 	   					print("error saving user order : " + str(order_id))
# 	   					print("error: " + str(e))
# 	   					continue

# 	   				purchase_url = ("http://localhost:8081/dataimport/purchases/" + str(order_id))
# 	   				purchases_request = requests.get(purchase_url)
# 	   				purchases = purchases_request.json()['data']

# 	   				for purchase in purchases:
# 	   					try:
# 	   						purchase_id = purchase.get('PurchaseID')
# 	   						purchase_product_code = purchase.get('ProductCode')
# 	   						purchase_price_rule_id = purchase.get('PriceRuleID')
# 	   						purchase_webuserid = purchase.get('WebUserID')
# 	   						purchase_productprice = purchase.get('ProductPrice')
# 	   						purchase_option_id = purchase.get('OptionID')
# 	   						purchase_quantity = purchase.get('PurchaseQuantity')
# 	   						purchase_amount = purchase.get('PaymentRequiredTotal')
# 	   						purchase_submitted_time = purchase.get('SubmittedDateTime')
# 	   						purchase_imis_number = purchase.get('ExternalTransactionID')
# 	   						purchase_status = purchase.get('PurchaseStatus')
# 	   						purchase_product_type = purchase.get('ProductTypeCode')
# 	   						purchase_submitted_time = purchase_submitted_time.split(".", 1)[0]
# 	   						purchase_external_code = purchase.get('ExternalCode')

# 	   						if purchase_product_type == 'ACTIVITY':
# 	   							purchase_product_code = product_code.split("_", 1)[1].split("_", 1)[1]
# 	   							event_code = product_code.split("_", 1)[1].split("_",1)[0]

# 	   						if purchase_product_type == 'ACTIVITY':
# 	   							purchase_product = Product.objects.get(code = purchase_external_code, content__parent__content_live__code = event_code, content__publish_status='PUBLISHED')
# 	   						else:
# 	   							purchase_product = Product.objects.get(code = purchase_product_code, content__publish_status='PUBLISHED')
	   						
# 	   						purchase_contact = Contact.objects.get(user__username = purchase_webuserid)
# 	   						purchase_option = None
# 	   						if purchase_option_id and purchase_option_id != 0:
# 	   							try:
# 	   								purchase_option = ProductOption.objects.get(code=externalcode, product=purchase_product)
# 	   							except:
# 	   								purchase_option = None
# 	   						if purchase_price_rule_id and purchase_price_rule_id != 0:
# 	   							try:

# 	   								purchase_price = ProductPrice.objects.get(legacy_id = purchase_price_rule_id)

# 	   							except:
# 	   								print("product price legacy id does not match... attempt to match based off of price")
# 	   								print("price rule id: " + str(purchase_price_rule_id))
# 	   								print("product: " + str(purchase_product))
# 	   								purchase_price = ProductPrice.objects.filter(product = purchase_product, price = purchase_amount).first()
# 	   						else:
# 	   							try:
# 	   								purchase_price = ProductPrice.objects.get(product=purchase_product, title='List Price')
#    								except:
#    									purchase_price = ProductPrice.objects.get(product=purchase_product, title='Archive Price')

#    							purchase,created = Purchase.objects.get_or_create(legacy_id = purchase_id, order = user_order, product = purchase_product, contact = purchase_contact, contact_recipient = purchase_contact, product_price = purchase_price, user = user, amount = purchase_amount, submitted_product_price_amount = purchase_amount)
   							
#    							purchase.option = purchase_option
#    							purchase.submitted_product_price_amount = purchase_productprice
#    							purchase.quantity = purchase_quantity 
#    							purchase.amount = purchase_amount
#    							purchase.submitted_time = purchase_submitted_time
#    							purchase.status = purchase_status
#    							purchase.save()
#    							user_order.imis_trans_number = str(purchase_imis_number)
#    							user_order.save()
		   				
# 		   				except Exception as e:
# 	   						print("error writing purchase for order id : " + str(order_id))
# 	   						print("purchase id: " + str(purchase_id))
# 	   						print("product: " + str(purchase_product))

# 	   						print("price rule id: " + str(purchase_price_rule_id))
# 	   						print("error: " + str(e))
# 	   						continue

# 	   				payments_url = ("http://localhost:8081/dataimport/payments/%s"  % str(order_id))
# 	   				payments_request = requests.get(payments_url)
# 	   				payments = payments_request.json()['data']

# 	   				for payment in payments:
# 	   					try:
# 		   					payment_id = payment.get('PaymentID')
# 		   					payment_type_code = payment.get('PaymentTypeCode')
# 		   					payment_total = payment.get('PaymentTotal')
# 		   					submitted_by_id = payment.get('SubmittedByID')
# 		   					submitted_date_time = payment.get('SubmittedDateTime')
# 		   					payment_status = payment.get('ProcessStatus')
# 		   					pn_ref = payment.get('PNRef')
# 		   					webuserid = payment.get('WebUserID')

# 		   					imis_batch = payment.get('BatchNumber')
# 		   					imis_batch_time = payment.get('BatchDate')
# 		   					imis_batch_time = imis_batch_time.split(".", 1)[0]
# 		   					submited_date_time = submitted_date_time.split(".", 1)[0]

# 		   					contact = Contact.objects.get(user__username=webuserid)
							
# 							# unknown payment methods:
# 							# (empty string)
# 							# 'NONE'
# 							# NONE
# 							# REFUND-TUGO
# 							# REFUND
# 		   					if payment_type_code == 'CREDITCARD':
# 		   						payment_type_code = 'CC'
# 		   					elif payment_type_code == 'REFUNDCHECK' or payment_type_code =='REFUND-CHECK':
# 		   						payment_type_code = 'CHECK_REFUND'
# 		   					elif payment_type_code == 'REFUND-CC':
# 		   						payment_type_code = 'CC_REFUND'

# 		   					payment, created = Payment.objects.get_or_create(legacy_id = payment_id)
# 		   					payment.method = payment_type_code
# 		   					payment.amount = payment_total
# 		   					payment.pn_ref = pn_ref
# 		   					payment.user = user
# 		   					payment.contact = contact   
# 		   					payment.order = user_order
# 		   					payment.submitted_time = submited_date_time
# 		   					payment.save()

# 		   					user_order.imis_batch = imis_batch
# 		   					user_order.imis_batch_time = imis_batch_time
# 		   					user_order.save()
# 		   				except Exception as e:
# 		   					print("error writing payment for order id: " + str(order_id))
# 		   					print("exception: " + str(e))

# 	   				print("imported order id : " + str(order_id))

# 	   			except Exception as e:
# 	   				print("error importing order: " + str(order_id))
# 	   				print("exception: " + str(e))
# 	   				continue

#    		except Exception as e:
#    			("error importing order: " + str(e))
#    			order_errors[order_id] = str(e)

#    		print(order_errors)

def import_tags():
	"""
	import format tags
	"""

	tagtype, created = TagType.objects.get_or_create(code='PRODUCT_FORMAT', title='Product Format')

	tag, created = Tag.objects.get_or_create(tag_type = tagtype, code='HARDCOVER', title='Hardcover', sort_number=1)
	tag, created = Tag.objects.get_or_create(tag_type = tagtype, code='PAPERBACK', title='Paperback', sort_number=1)
	tag, created = Tag.objects.get_or_create(tag_type = tagtype, code='CD', title='CD', sort_number=1)
	tag, created = Tag.objects.get_or_create(tag_type = tagtype, code='PDF', title='Adobe PDF', sort_number=1)
	tag, created = Tag.objects.get_or_create(tag_type = tagtype, code='EPUB', title='EPUB', sort_number=1)
	tag, created = Tag.objects.get_or_create(tag_type = tagtype, code='MOBI', title='MOBI', sort_number=1)
	tag, created = Tag.objects.get_or_create(tag_type = tagtype, code='STREAMING', title='Streaming Media', sort_number=1)


def import_tax():

	content, created = Content.objects.get_or_create(code='TAX', content_type='PRODUCT', title='Tax', publish_status='DRAFT')

	product, created = Product.objects.get_or_create(code = "TAX",content = content, title= "Illinois Sales Tax", product_type="TAX")

	productprice, created = ProductPrice.objects.get_or_create(product=product, title="Illinois Sales Tax - 8%", price=0)


	content.publish()
	
def create_shipping_product():

	url = node_url + 'shipping'

	r = requests.get(url)

	shipping_options = r.json()['data']

	content, created = Content.objects.get_or_create(code="SHIPPING", title="Shipping", content_type="PRODUCT", publish_status='DRAFT')

	product, created = Product.objects.get_or_create(code = "SHIPPING",content = content, title= "Shipping", product_type="SHIPPING")
	

	ProductPrice.objects.filter(product=product).delete()
	ProductOption.objects.filter(product=product).delete()
	#productprice, created = ProductPrice.objects.get_or_create(product=product, title = "Default Shipping Price", price='10.00', gl_account='000000', imis_code='BOOK_SHIPPING')


	productoption, created = ProductOption.objects.get_or_create(product=product, title='International Shipping (discontinued)', code='INTERNATIONAL_SHIPPING', status='I')
	productprice, created = ProductPrice.objects.get_or_create(product=product, option_code='INTERNATIONAL_SHIPPING', code='75', title="Archived International Shipping Price", price=0)
	for shipping_option in shipping_options:

		shipping_price = 0

		code = shipping_option.get('ExternalCode')
		name = shipping_option.get('OptionName')

		if code=='UPS 3 DAY COM':
			name='UPS 3-Day Select Commercial'
		if code=='UPS 3 DAY RES':
			name='UPS 3-Day Select'
		if code=='APA COM GREATER $500':
			code='UPS COM GROUND'
			name='UPS Ground Commercial'
		if code=='APA RES GREATER $500':
			code='UPS RES GROUND'
			name='UPS Ground'
		# if code=='APA RES GREATER $500':
		# 	name='UPS Ground Residential > $500'
		# if code=='APA COM GREATER $500':
		# 	name='UPS Ground Commercial > $500'

		productoption, created = ProductOption.objects.get_or_create(product=product, title=name, code=code)

		productprice, created = ProductPrice.objects.get_or_create(product=product, option_code=code, code='75', title="Book Total < $75", price=8.00)
		if code in ('UPS 3 DAY COM', 'UPS 3 DAY RES'):
			productprice.price += 10
			productprice.save()
		if code in ('UPS NX RES'):
			productprice.price += 25
			productprice.save()	
		# if code in ('PRINT MAT SUR'):
		# 	productprice.price += 22
		# 	productprice.save()
		# if code in ('INTL AIRMAIL P P'):
		# 	productprice.price += 35
		# 	productprice.save()
		productprice, created = ProductPrice.objects.get_or_create(product=product, option_code=code, code='150', title="Book Total < $150", price=12.00)
		if code in ('UPS 3 DAY COM', 'UPS 3 DAY RES'):
			productprice.price += 10
			productprice.save()
		if code in ('UPS NX RES'):
			productprice.price += 25
			productprice.save()
		# if code in ('PRINT MAT SUR'):
		# 	productprice.price += 22
		# 	productprice.save()
		# if code in ('INTL AIRMAIL P P'):
		# 	productprice.price += 35
		# 	productprice.save()
		productprice, created = ProductPrice.objects.get_or_create(product=product, option_code=code, code='250', title="Book Total < $250", price=15.00)
		if code in ('UPS 3 DAY RES'):
			productprice.price += 10
			productprice.save()
		if code in ('UPS NX RES'):
			productprice.price += 25
			productprice.save()
		# if code in ('PRINT MAT SUR'):
		# 	productprice.price += 22
		# 	productprice.save()
		# if code in ('INTL AIRMAIL P P'):
		# 	productprice.price += 35
		# 	productprice.save()
		productprice, created = ProductPrice.objects.get_or_create(product=product, option_code=code, code='500', title="Book Total < $500", price=17.00)
		if code in ('UPS 3 DAY RES'):
			productprice.price += 10
			productprice.save()
		if code in ('UPS NX RES'):
			productprice.price += 25
			productprice.save()
		# if code in ('PRINT MAT SUR'):
		# 	productprice.price += 22
		# 	productprice.save()
		# if code in ('INTL AIRMAIL P P'):
		# 	productprice.price += 35
		# 	productprice.save()

		productprice, created = ProductPrice.objects.get_or_create(product=product, option_code=code, code='500PLUS', title="Book Total > $500", price=0)
		if code in ('UPS 3 DAY RES'):
			productprice.price += 10
			productprice.save()
		if code in ('UPS NX RES'):
			productprice.price += 25
			productprice.save()
	content.publish()


def create_archive_productprice():
	"""
	create an product price for chapter, dues/division_only, and subscription products for purchases that could not be linked to an existing content + price
	"""

	chapter_url = node_url + 'products/' +  'CHAPTER' + '/all'
	dues_url = node_url + 'products/' + 'DUES' + '/all'
	division_url = node_url + 'products/' + 'DIVISION_ONLY' + '/all'
	subscription_url = node_url + 'products/' + 'SUBSCRIPTION' + '/all'

	product_type_list = [chapter_url, dues_url, division_url, subscription_url]

	product_price_errors = {}

	for product_type in product_type_list:

		r = requests.get(product_type)

		products = r.json()['data']

		for product in products:

			product_code = product.get('ProductCode')
			product_type = product.get('ProductTypeCode')

			if product_type == 'DIVISION_ONLY':
				product_type = 'DIVISION'

			if product_type == 'SUBSCRIPTION':
				product_type = 'PUBLICATION_SUBSCRIPTION'
			try:
				content = Content.objects.get(code=product_code, publish_status='DRAFT', product__product_type=product_type)				
				product = content.product


				productprice, created = ProductPrice.objects.get_or_create(product = product, code='ARCHIVE_PRICE', title='Archive Price')
				productprice.description = 'Fallback productprice if imported orders did not match an existing content.'
				productprice.priority=999
				productprice.price = 0
				productprice.include_search_results = False
				productprice.status = 'I'
				productprice.save()

				content.publish()

			except Exception as e:
				print('failed creating default product price')
				print(str(e))
				product_price_errors[product_code] = str(e)
				pass


	print(product_price_errors)


def import_orders(product_type):
	"""
	for importing event, activity, books, streaming, and digital products ONLY
	"""

	url = node_url + 'orders/product_type/' + product_type

	r = requests.get(url)

	orders = r.json()['data']

	order_errors = {}
	for order in orders:

		order_id = order.get('OrderID')
		webuserid = order.get('WebUserID')
		order_status = order.get('OrderStatus')
		last_updated_by_id = order.get('LastUpdatedByID')
		is_manual = order.get('IsManualOrder', False)
		order_submitted_date = order.get('SubmittedDateTime')

		if order_status == 'A':
			order_status = 'PROCESSED'
		elif order_status == 'P':
			order_status = 'SUBMITTED'
		elif order_status == 'X' or order_status == 'CAN':
			order_status = 'CANCELLED'

		try:
			print("importing order id : " + str(order_id))
			order_submitted_date = order_submitted_date.split(".", 1)[0]

			user, created = User.objects.get_or_create(username=webuserid)
			contact, created = Contact.objects.get_or_create(user = user)
		

			user_order, created = Order.objects.get_or_create(legacy_id = order_id, user = user, submitted_time = order_submitted_date)
			user_order.order_status = order_status
			user_order.submitted_user_id = last_updated_by_id
			user_order.is_manual = is_manual
			user_order.save()

			order_errors.update(import_purchases(order=user_order, product_type=product_type, user=user, contact=contact))
			order_errors.update(import_payments(order=user_order, product_type=product_type, user=user, contact=contact))

		except Exception as e:
			print("error saving user order : " + str(order_id))
			print("error: " + str(e))
			order_errors[order_id] = str(e)
			pass
	print(order_errors)
	print("order error count for product type " + product_type + ": " + str(len(order_errors)))
	print('orders imported: ' + str(len(orders)))
def import_purchases(order, product_type, user, contact):

	url = (node_url + 'orders/' + str(order.legacy_id) + '/product_type/' + product_type + '/purchases')
	r = requests.get(url)
	purchases = r.json()['data']
	
	purchase_errors = {}

	for purchase in purchases:
		try:
			purchase_id = purchase.get('PurchaseID')
			purchase_product_code = purchase.get('ProductCode')
			purchase_price_rule_id = purchase.get('PriceRuleID')
			purchase_webuserid = purchase.get('WebUserID')
			purchase_productprice = purchase.get('ProductPrice')
			purchase_option_id = purchase.get('OptionID')
			purchase_quantity = purchase.get('PurchaseQuantity')
			purchase_amount = purchase.get('PaymentRequiredTotal')
			purchase_submitted_time = purchase.get('SubmittedDateTime')
			purchase_imis_number = purchase.get('ExternalTransactionID')
			purchase_status = purchase.get('PurchaseStatus')
			purchase_product_type = purchase.get('ProductTypeCode')
			purchase_submitted_time = purchase_submitted_time.split(".", 1)[0]
			purchase_external_code = purchase.get('ExternalCode')
			purchase_is_standby = purchase.get('IsStandby')
			if not purchase_is_standby:
				purchase_is_standby = False

			# note: this is needed
			purchase_option_code = purchase.get('OptionCode')

			# this should be OK for BOOK, EBOOK, and STREAMING products
			product_parent_code = None
			parent_master = None
			if not purchase_amount:
				purchase_amount = 0
				
			if purchase_product_code == 'BOOK_SHIPPING':
				purchase_product_code = 'SHIPPING'

			# this should be OK for events...
			# if product_type == 'EVENT':
			# 	purchase_product_code = purchase_product_code.split("_", 1)[1]

			# if product_type == 'ACTIVITY':
			# 	product_parent_code = purchase_product_code.split("_", 1)[1].split("_", 1)[0]
			# 	purchase_product_code = purchase_product_code.split("_", 1)[1].split("_",1)[1]

			# ew but it works. convert these codes to product codes later on
			# if product_type == "ACTIVITY":
			# 	try:
			# 		print('this is an activity')
			# 		print('purchase product code: ' + purchase_product_code)
			# 		print('product parent_code: ' + product_parent_code)
					# parent_master = Event.objects.filter(code=product_parent_code, publish_status='PUBLISHED').first().master
			# 		purchase_product = Product.objects.filter(code = purchase_product_code, publish_status='PUBLISHED', content__parent=parent_master).first()
				# except Exception as e:
				# 	print(str(e))
			# else:
			purchase_product = Product.objects.filter(code = purchase_product_code, publish_status='PUBLISHED').first()

			# some activities will not have purchases required... so skip this all and write to attendee!
			purchase_option = None
			# if purchase_product_code == 'SHIPPING':
			# 	if purchase_option_code in ('APA RES LESS $500', 'APA COM LESS $500', 'APA COM GREATER $500', 'APA RES GREATER $500'):
			# 		purchase_option = ProductOption.objects.get(code='UPS RES GROUND', product=purchase_product)
			# 	elif purchase_option_code in ('UPS 3 DAY COM','UPS 3 DAY RES','UPS 3 DAY COM %','UPS 3 DAY RES %', '1ST CLASS','1ST CLASS %'):
			# 		purchase_option = ProductOption.objects.get(code='3 DAY RES', product=purchase_product)
			# 	elif purchase_option_code in ('UPS NX RES'):
			# 		purchase_option = ProductOption.objects.get(code='UPS NX RES', product=purchase_product)
			# 	else:
			# 		purchase_option = ProductOption.objects.get(code='INTERNATIONAL_SHIPPING', product=purchase_product)
			
			if purchase_option_id and purchase_option_id != 0:
				try:
					purchase_option = ProductOption.objects.get(code=purchase_option_code, product=purchase_product)
				except:
					print('could not find option')
					purchase_option = None
					pass

			# shipping checks... commenting out for now
			# if purchase_product_code == 'SHIPPING':
			# 	if purchase_option_code in ('APA RES LESS $500', 'APA COM LESS $500', 'APA COM GREATER $500', 'APA RES GREATER $500'):
			# 		if purchase_productprice == 8:
			# 			purchase_price = ProductPrice.objects.get(option_code='UPS RES GROUND', code='75', product=purchase_product)
			# 		elif purchase_productprice == 12:
			# 			purchase_price = ProductPrice.objects.get(option_code='UPS RES GROUND', code='150', product=purchase_product)
			# 		elif purchase_productprice == 15:
			# 			purchase_price = ProductPrice.objects.get(option_code='UPS RES GROUND', code='250', product=purchase_product)
			# 		elif purchase_productprice == 17:
			# 			purchase_price = ProductPrice.objects.get(option_code='UPS RES GROUND', code='500', product=purchase_product)
			# 		else:
			# 			purchase_price = ProductPrice.objects.get(option_code='UPS RES GROUND', code='500PLUS', product=purchase_product)

			# 	elif purchase_option_code in ('UPS 3 DAY COM','UPS 3 DAY RES','UPS 3 DAY COM %','UPS 3 DAY RES %', '1ST CLASS',' 1ST CLASS %'):
			# 		if purchase_productprice == 8:
			# 			purchase_price = ProductPrice.objects.get(option_code='UPS 3 DAY RES', code='75', product=purchase_product)
			# 		elif purchase_productprice == 12:
			# 			purchase_price = ProductPrice.objects.get(option_code='UPS 3 DAY RES', code='150', product=purchase_product)
			# 		elif purchase_productprice == 15:
			# 			purchase_price = ProductPrice.objects.get(option_code='UPS 3 DAY RES', code='250', product=purchase_product)
			# 		elif purchase_productprice == 17:
			# 			purchase_price = ProductPrice.objects.get(option_code='UPS 3 DAY RES', code='500', product=purchase_product)
			# 		else:
			# 			purchase_price = ProductPrice.objects.get(option_code='UPS 3 DAY RES', code='500PLUS', product=purchase_product)

			# 	else:
			# 		purchase_price=ProductPrice.objects.get(option_code='INTERNATIONAL_SHIPPING', product=purchase_product)
			
			if purchase_price_rule_id and purchase_price_rule_id != 0:
				print('this has a price rule id')
				try:
					purchase_price = ProductPrice.objects.get(legacy_id = purchase_price_rule_id, publish_status='PUBLISHED')
				except:
					purchase_price = ProductPrice.objects.filter(product = purchase_product, price = purchase_amount).first()

					if not purchase_price:
						purchase_price, created = ProductPrice.objects.get_or_create(product = purchase_product, title="List Price", publish_status='PUBLISHED', status="I")
						purchase_price.price = 0.00
						purchase_price.save()
						pass
			else:
				print('this does NOT have a price rule id')
				try:
					purchase_price = ProductPrice.objects.get(product=purchase_product, title='List Price', publish_status='PUBLISHED')
				except Exception as e:
					print('product price is missing... creating one')
					print("error: " + str(e))

					purchase_price, created = ProductPrice.objects.get_or_create(product=purchase_product, title='List Price', publish_status='PUBLISHED')

					if created:
						purchase_price.price = 0.00
						purchase_price.save()

					pass
			if purchase_product_code != "SHIPPING":
				try:
					purchase_new = Purchase.objects.get(legacy_id = purchase_id)
				except Purchase.DoesNotExist:
					print("this purchase does not exist yet")
					if purchase_product and purchase_price:
						purchase_new = Purchase.objects.create(legacy_id = purchase_id, order = order, product = purchase_product, contact = contact, contact_recipient = contact, product_price = purchase_price, user = user, amount = purchase_amount, submitted_product_price_amount = purchase_amount)
						pass
			else:
				purchase_new,created = Purchase.objects.get_or_create(legacy_id = purchase_id, order = order, product = purchase_product, contact = contact, contact_recipient = contact, product_price = purchase_price, user = user, amount = purchase_amount, submitted_product_price_amount = purchase_amount)
				purchase_new.first_name = purchase.get('ShippingFirstName')
				purchase_new.last_name = purchase.get('ShippingLastName')
				purchase_new.address1 = purchase.get('ShippingAddress1')
				purchase_new.address2 = purchase.get('ShippingAddress2')
				purchase_new.city = purchase.get('ShippingCity')
				purchase_new.state = purchase.get('ShippingStateProvince')
				purchase_new.country = purchase.get('ShippingCountry')
				purchase_new.zip_code = purchase.get('ShippingZip')

			# if purchase_product and purchase_price:
			# 	purchase_new.option = purchase_option
			# 	purchase_new.quantity = purchase_quantity
			# 	purchase_new.submitted_time = purchase_submitted_time
			# 	purchase_new.status = purchase_status
			# 	purchase_new.save()
		
			if product_type in ("EVENT","ACTIVITY"):
				import_attendee(purchase_new, contact, purchase_status, purchase_submitted_time, purchase_is_standby)

		except Exception as e:
			print("error writing purchase for order id : " + str(order.legacy_id))
			print("purchase id: " + str(purchase_id))
			print("product: " + str(purchase_product))
			purchase_errors[str(order.legacy_id)] = "error writing purchase for purchase id: "  + str(purchase_id) + " | ERROR: " + str(e)

			print("price rule id: " + str(purchase_price_rule_id))
			print("error: " + str(e))
			pass

	return purchase_errors

def import_attendee(purchase, contact, purchase_status, purchase_submitted_time, purchase_is_standby):
	
	if purchase.product.product_type == "ACTIVITY_TICKET":
		parent_event_code = purchase.product.code.split("_", 1)[1].split("_", 1)[0]
		parent_master = Event.objects.filter(code=parent_event_code, publish_status='PUBLISHED').first()
		if parent_master:
			parent_master = parent_master.master
		event = Event.objects.filter(code=purchase.product.content.code, parent=parent_master, publish_status='PUBLISHED').first()
	else:
		event = Event.objects.filter(code=purchase.product.content.code, publish_status='PUBLISHED').first()
	Attendee.objects.filter(event=event, contact=contact).delete()
	attendee, created = Attendee.objects.get_or_create(event=event, contact=contact, purchase=purchase, added_time=purchase_submitted_time)
	attendee.status = purchase_status
	attendee.is_standby = purchase_is_standby
	attendee.save()

def import_payments(order, product_type, user, contact):

	url = node_url + 'orders/' + str(order.legacy_id) + '/payments'
	r = requests.get(url)
	payments = r.json()['data']

	payment_errors = {}

	for payment in payments:
		try:
			payment_id = payment.get('PaymentID')
			payment_type_code = payment.get('PaymentTypeCode')
			payment_total = payment.get('PaymentTotal')
			submitted_by_id = payment.get('SubmittedByID')
			submitted_date_time = payment.get('SubmittedDateTime')
			payment_status = payment.get('ProcessStatus')
			pn_ref = payment.get('PNRef')
			webuserid = payment.get('WebUserID')

			imis_batch = payment.get('BatchNumber')
			imis_batch_time = payment.get('BatchDate')

			address_1 = payment.get('BillingAddress1')
			address_2 = payment.get('BillingAddress2')
			city = payment.get('BillingCity')
			state = payment.get('BillingStateProvince')
			country = payment.get('BillingCountry')
			zip_code = payment.get('BillingZip')
			address_num = payment.get('BillingAddressNum')

			if payment_total == None:
				payment_total = 0

			try:
				imis_batch_time = imis_batch_time.split("T", 1)[0]
			except:
				imis_batch_time = None
			try:
				submitted_date_time = submitted_date_time.split(".", 1)[0]

			except:
				submitted_date_time = None
		# unknown payment methods:
		# (empty string)
		# 'NONE'
		# NONE
		# REFUND-TUGO
		# REFUND
			if payment_type_code == 'CREDITCARD':
				payment_type_code = 'CC'
			elif payment_type_code == 'REFUNDCHECK' or payment_type_code =='REFUND-CHECK':
				payment_type_code = 'CHECK_REFUND'
			elif payment_type_code == 'REFUND-CC':
				payment_type_code = 'CC_REFUND'
			elif payment_type_code in ('NONE',"'NONE'",''):
				payment_type_code = 'NONE'
			elif payment_type_code in ('REFUND','REFUND-TUGO'):
				payment_type_code = 'REFUND'
			else:
				payment_type_code = 'UNKNOWN'
			try:
				payment = Payment.objects.get(legacy_id = payment_id)
			except Payment.DoesNotExist:
				payment = Payment.objects.create(legacy_id = payment_id, amount=payment_total)
				
			payment.method = payment_type_code
			payment.amount = payment_total
			payment.pn_ref = pn_ref
			payment.user = user
			payment.contact = contact   
			payment.order = order
			payment.submitted_time = submitted_date_time

			payment.address1 = address_1
			payment.address2 = address_2
			payment.city = city
			payment.state = state
			payment.zip_code = zip_code
			payment.country = country
			payment.user_address_num = address_num
			payment.save()

			order.imis_batch = imis_batch
			order.imis_batch_time = imis_batch_time
			order.save()
		except Exception as e:
			print("error writing payment for order id: " + str(order.legacy_id))
			print("exception: " + str(e))
			payment_errors[str(order.legacy_id)] = "payment id:" + str(payment_id) + "error processing payment: " + str(e)
			continue

	return payment_errors

def update_streaming_description():
	"""
	quick script to update streaming descriptions
	"""

	url = node_url + 'products/STREAMING/all'

	r = requests.get(url)

	products = r.json()['data']

	
	product_import_errors = {}

	for product in products:
		try:
			# 1. check if product exists in django
			product_code = product.get('ProductCode')
			product_id = product.get('ProductID')
			product_name = product.get('ProductName')
			product_description = product.get('ProductDescription')

			product_status = product.get('ProductStatus')
			product_default_price = product.get('ProductDefaultPrice') # add to product price?
			product_external_code = product.get('ExternalCode') # imis_code on product
			product_has_pricerules = product.get('HasPriceRules')
			product_required_groups = product.get('WebUserGroups') # add to product price 
			product_exclude_groups = product.get('ExcludeWebUserGroups') # add to product price
			product_custom_text_1 = product.get('CustomText1') # used for member types (MEM)... any other products
			product_future_groups = product.get('FutureWebUserGroups') # future_groups on product model
			product_quantity_available = product.get('QuantityAvailable') # max_quantity on product
			product_purchase_limit = product.get('PurchaseQuantityLimit') # max_quantity_per_person on product
			product_standby_available = product.get('StandbyAvailable') # max_quantity_standby on product
			product_sales_start_time = product.get('SalesStartDateTime')
			product_sales_end_time = product.get('SalesEndTime')
			product_has_options = product.get('HasOptions')
			product_hide_price = product.get('HidePrice')
			product_use_event_options = product.get('UseEventOptions')
			product_use_event_dates = product.get('UseEventDateRestrictions')
			product_subtitle = product.get('Subtitle')
			product_tied_to_product = product.get('TiedToProductCode')
			product_hasxhtml = product.get('HasXhtmlContent')
			product_isbn = product.get('ISBN')
			product_glaccount = product.get('TagCode')
			product_parent_code = product.get('ParentCode')
			product_published_date = product.get('ProductDate')
			product_shortdescription = product.get('ShortDescription')
			# for event (STREAMING) products
			product_credits = product.get('CreditApprovedNumber')
			product_law_credits = product.get('CreditLawApprovedNumber')
			product_ethics_credits = product.get('CreditEthicsApprovedNumber')
			product_series_number = product.get('SeriesNumber')

			product_file_location = product.get('FilesLocation')
			product_file_name = product.get('FileName')
			product_thumbnail_location = product.get('ThumbnailFilesLocation')
			product_thumbnail_file_name = product.get('ThumbnailFileName')

			# product format codes for book/e-book/streaming
			product_format_code = product.get('FormatCode')
			product_page_count = product.get('PageCount')
			product_table_of_contents = product.get('TableOfContents')
			product_reviews = product.get('Reviews')
			product_length_in_minutes = product.get('LengthInMinutes')
			product_publisher = product.get('Publisher')


			product = Product.objects.get(code=product_code, publish_status='DRAFT')
			product.content.text = product_description
			product.content.save()

			product.content.publish()
			print('updated description for streaming product: ' + product.content.title)

		except Exception as e:
			print("error importing product... passing")
			print("error: " + str(e))
			product_import_errors[product_code] = str(e)
			pass
		
	print(product_import_errors)


def update_purchase_expiration():
	"""
	quick script to update expiration dates for streaming purchases from SQL
	"""

	url = node_url + 'webuser/purchases/expirationtime'

	r = requests.get(url)

	purchases = r.json()['data']

	purchase_import_errors = {}

	f = '%Y-%m-%d %H:%M:%S'

	for purchase in purchases:
		try:
			purchase_id = purchase.get('PurchaseID')
			order_id = purchase.get('OrderID')
			product_code = purchase.get('ProductCode')
			user_id = purchase.get('WebUserID')
			download_expires_time = purchase.get('DownloadExpiresDateTime')

			download_expires_time
			# http://stackoverflow.com/questions/14291636/what-is-the-proper-way-to-convert-between-mysql-datetime-and-python-timestamp
			expires_datetime = datetime.strptime(download_expires_time, f)
			print('expiration time:' + str(expires_datetime))

			previous_purchase = Purchase.objects.get(legacy_id = purchase_id)
			previous_purchase.expiration_time = expires_datetime
			previous_purchase.save()

			print('added expiration date for purchase id: ' + str(purchase_id))

		except Exception as e:
			print('error importing expiration time: ' + str(e))
			purchase_import_errors[purchase_id] = str(e)
			continue

def import_jobs():
	"""
	imports all job orders
	"""

	url = node_url + 'jobs/orders'

	r = requests.get(url)

	job_orders = r.json()['data']

	purchase_import_errors = {}

	job_draft_product = Product.objects.get(code="JOB_AD", publish_status="DRAFT")
	ProductPrice.objects.get_or_create(product = job_draft_product, code="ARCHIVED_JOB", title="Archived Job Price", price="0.00")

	job_draft_product.publish()

	

	# create default job product
	for job_order in job_orders:
		order_id = job_order.get('OrderID')
		status = job_order.get('OrderStatus')
		order_time = job_order.get('OrderSubmittedDateTime')

		first_name = job_order.get('OrderBillingFirstName')
		last_name = job_order.get('OrderBillingLastName')
		middle_name = job_order.get('OrderBillingMiddleName')
		address1 = job_order.get('OrderBillingAddress1')
		address2 = job_order.get('OrderBillingAddress2')
		city = job_order.get('OrderBillingCity')
		state = job_order.get('OrderBillingStateProvince')
		country = job_order.get('OrderBillingCountry')
		zip_code = job_order.get('OrderBillingZip')
		cc_type = job_order.get('OrderCreditCardType')
		payment_amount = job_order.get('OrderCreditCardPayment')
		pn_ref = job_order.get('OrderTransactionID')
		user_id = job_order.get('WebUserID')

def deactivate_old_event_products():
	# sets the product price status for old events to inactive.
	event_products = Product.objects.filter(product_type='EVENT_REGISTRATION').exclude(Q(code__icontains='16') | Q(code__icontains='17') | Q(code__iexact='STR_TSPLRO') | Q(code__iexact="STR_HMPF") | Q(content__title="Policy and Advocacy Conference 2016 Live Webcast") | Q(content__title="Urban Design for Planners 1: Software Tools") | Q(code__icontains="15AUDIO"))
	print("There will be {0} event product status changes".format(event_products.count()))
	for event_product in event_products:
		# get the product prices of this event
		print("Changing the status of {0} and it's activities.".format(str(event_product)))
		event_activity_all = Product.objects.filter(Q(id=event_product.id) | Q(content__parent=event_product.content.master))
		event_activity_all.update(status="I")

