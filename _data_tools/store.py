from store.models import *
from datetime import datetime, date, timedelta
from django.db.models import Q
from store.models import Product as DjangoProduct
from imis.models import Product as ImisProduct
def update_life_ret_prices():
	"""
	updates the chapter prices for life and retired members
	"""

	life_prices = ProductPrice.objects.filter(product__product_type='CHAPTER', title='Life Member Price')

	ret_prices = ProductPrice.objects.filter(product__product_type='CHAPTER', title='Retired Member Price')

	for x in life_prices:
		x.code='MEMBERSHIP_LIFE'
		x.required_groups.clear()
		x.save()

	for x in ret_prices:
		x.code='MEMBERSHIP_RET'
		x.required_groups.clear()
		x.save()

	print('completed!')

def update_exam_prep_expiration():

	purchases = Purchase.objects.filter(product__code="STR_EXAM3").exclude(order__isnull=True, expiration_time__isnull=True)

	print("number of exam prep purchases: {0}".format(str(purchases.count())))

	for purchase in purchases:
		if purchase.expiration_time is not None and purchase.order and purchase.order.submitted_time:
				# assume EVERYONE needs the additional time added for purchasing the streaming product. 
				purchase.expiration_time = purchase.expiration_time + timedelta(days=911)
				purchase.save()
				print("updated expiration time for user {0}".format(str(purchase.user.username)))
	print("bam")

def create_streaming_products():
	"""
	creates individual imis products for the streaming products we have in iMIS
	"""
	errors = {}

	streaming_products = DjangoProduct.objects.filter(product_type='STREAMING', imis_code='STREAM_LMS', status='A', publish_status='DRAFT')
	income_account='470130-MF1408'
	for x in streaming_products:
		try:
			if not ImisProduct.objects.filter(product_code=x.code).exists():
				ImisProduct.objects.create(
					product_code=x.code,
					product_major=x.code,
					product_minor='',
					prod_type='SALES',
					category='',
					title_key=x.title.upper(), #capitalize this
					title = x.title,
					description='',
					status='A',
					group_1='',
					group_2='',
					group_3='',
					price_rules_exist=0,
					lot_serial_exist=0,
					payment_priority=0,
					renew_months=0,
					prorate='',
					stock_item=0,
					unit_of_measure='',
					weight=0,
					taxable=0,
					commisionable=0,
					commision_percent=0,
					decimal_points=0,
					income_account=income_account, #create income-account
					deferred_income_account='',
					inventory_account='',
					adjustment_account='',
					cog_account='',
					intent_to_edit='',
					price_1=0,
					price_2=0,
					price_3=0,
					complimentary=0,
					attributes='',
					pst_taxable=0,
					taxable_value=0,
					org_code='',
					tax_authority='',
					web_option=0, # should we make this 1?
					image_url='',
					apply_image=0,
					is_kit=0,
					info_url='',
					apply_info=0,
					plp_code='',
					promote=0,
					thumbnail_url='',
					apply_thumbnail=0,
					location='DEFAULT',
					premium=0,
					fair_market_value=0,
					is_fr_item=0,
					appeal_code='',
					campaign_code='',
					price_from_components=0,
					tax_by_location=0,
					taxcategory_code=''
					)

			x.imis_code = x.code
			x.save()
			x.publish()

			print("successfully created imis product {0}".format(x.code))
		except Exception as e:
			print("error creating imis product: {0}".format(str(e)))
			errors[x.code] = str(e)
	print("product creation completed")
	print("the errors....")
	print(str(errors))

def create_digital_publication_products():
	"""
	creates individual imis products for the digital publication products we have in iMIS
	zoning - 470150-UZ2102 
	commisioner - 450500-AD6400
	pas - 470150-UA3100
	"""
	errors = {}



	digital_publications = DjangoProduct.objects.filter(product_type='DIGITAL_PUBLICATION', status='A', publish_status='DRAFT').filter(Q(imis_code__startswith="ZP_") | Q(imis_code__startswith="PAS_EIP") | Q(imis_code__startswith="PAS_M") | Q(imis_code__startswith="PAS_Q") | Q(imis_code__startswith="PAS_"))
	income_account='470130-MF1408'
	for x in digital_publications:
		try:

			income_account = 0
			if "ZP_" in x.imis_code:
				income_account = "470150-UZ2102"
			elif "PAS_EIP" in x.imis_code:
				income_account = "470150-UA3800"
			elif "PAS_M" in x.imis_code:
				income_account = "470150-UA3100"
			elif "PAS_Q" in x.imis_code:
				income_account = "470150-UA3100"
			elif "PAS_" in x.imis_code:
				income_account = "470110-UA3100"

			title = ''
			if x.title:
				title = x.title.upper()[:59]
			else:
				title = x.content.title.upper()[:59]

			if not ImisProduct.objects.filter(product_code=x.imis_code).exists():

				ImisProduct.objects.create(
					product_code=x.imis_code,
					product_major=x.imis_code,
					product_minor='',
					prod_type='SALES',
					category='',
					title_key=title, #capitalize this
					title = title,
					description='',
					status='A',
					group_1='',
					group_2='',
					group_3='',
					price_rules_exist=0,
					lot_serial_exist=0,
					payment_priority=0,
					renew_months=0,
					prorate='',
					stock_item=0,
					unit_of_measure='',
					weight=0,
					taxable=0,
					commisionable=0,
					commision_percent=0,
					decimal_points=0,
					income_account=income_account, #create income-account
					deferred_income_account='',
					inventory_account='',
					adjustment_account='',
					cog_account='',
					intent_to_edit='',
					price_1=0,
					price_2=0,
					price_3=0,
					complimentary=0,
					attributes='',
					pst_taxable=0,
					taxable_value=0,
					org_code='',
					tax_authority='',
					web_option=0, # should we make this 1?
					image_url='',
					apply_image=0,
					is_kit=0,
					info_url='',
					apply_info=0,
					plp_code='',
					promote=0,
					thumbnail_url='',
					apply_thumbnail=0,
					location='DEFAULT',
					premium=0,
					fair_market_value=0,
					is_fr_item=0,
					appeal_code='',
					campaign_code='',
					price_from_components=0,
					tax_by_location=0,
					taxcategory_code=''
					)
			else:

				ImisProduct.objects.filter(product_code=x.imis_code, product_major=x.imis_code).update(
					title_key=title, #capitalize this
					title = title)
			print("successfully created imis product {0}".format(x.imis_code))
		except Exception as e:
			print("error creating imis product: {0}".format(str(e)))
			errors[x.code] = str(e)
	print("product creation completed")
	print("the errors....")
	print(str(errors))
