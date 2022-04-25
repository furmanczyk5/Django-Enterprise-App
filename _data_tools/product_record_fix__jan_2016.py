import uuid
import sys
from datetime import datetime

from django.contrib.auth.models import User
from django.db.models import F

from content.models import MasterContent, Content, ContentTagType
from myapa.models import ContactRole
from events.models import Event
from store.models import Product, ProductOption, ProductPrice, ContentProduct

# ALL assign_uuids_* functions can run at the same time

def assign_uuids_content():
	"""
	script to assign uuids to Content based on Master ID
	"""
	print("Querying for all master records...")
	masters = MasterContent.objects.all()

	GROUP_SIZE = 100
	TOTAL = masters.count()
	count = 0
	group_count = 0

	for master in masters:
		count += 1
		group_count += 1
		publish_uuid = uuid.uuid4()
		Content.objects.filter(master=master).update(publish_uuid=publish_uuid)

		if group_count >= GROUP_SIZE or count >= TOTAL:
			group_count = 0
			print("Completed %s/%s master groups: %.2f%% complete" % (count, TOTAL, float(count/TOTAL)*100.0 ))

	print("Flawless Victory!")


def assign_uuids_contactrole():
	"""
	Assigns publish_uuids to the ContactRoles based on related content, contact, role_type combo
	Also assigns the correct publish_status based on content__publish_status
	"""

	print("Querying all contactroles...")
	contactroles = ContactRole.objects.select_related(
		"content__master"
	).order_by(
		"content__master", "role_type", "contact", "first_name", "last_name"
	).distinct(
		"content__master", "role_type", "contact", "first_name", "last_name" )

	GROUP_SIZE = 20
	TOTAL = contactroles.count()
	count = 0
	group_count = 0

	for contactrole in contactroles:
		count += 1
		group_count += 1
		publish_uuid = uuid.uuid4()
		contactrole_set = ContactRole.objects.filter(
			content__master=contactrole.content.master,
			role_type=contactrole.role_type,
			contact=contactrole.contact,
			first_name=contactrole.first_name,
			last_name=contactrole.last_name
		).select_related("content")

		for cr in contactrole_set:
			cr.publish_uuid = publish_uuid
			cr.publish_status = cr.content.publish_status
			cr.save()

		if group_count >= GROUP_SIZE or count >= TOTAL:
			group_count = 0
			print("Completed (%s/%s)" % (count, TOTAL))

	print("Flawless Victory!")


def assign_uuids_contenttagtype():
	"""
	Assigns publish_uuids to the ContentTagType based on related content, tagtype, combo
	Also assigns the correct publish_status based on content__publish_status
	"""

	print("Querying all contenttagtypes...")
	contenttagtypes = ContentTagType.objects.select_related(
		"content"
	).order_by(
		"content__master", "tag_type"
	).distinct(
		"content__master", "tag_type"
	)

	TOTAL = contenttagtypes.count()
	count = 0

	for contenttagtype in contenttagtypes:
		count += 1
		publish_uuid = uuid.uuid4()
		contenttagtype_set = ContentTagType.objects.filter(
			tag_type=contenttagtype.tag_type,
			content__master=contenttagtype.content.master,
		)

		for ctt in contenttagtype_set:
			ctt.publish_uuid = publish_uuid
			ctt.publish_status = ctt.content.publish_status
			ctt.save()

		print("Completed %s (%s/%s)" % (contenttagtype, count, TOTAL))

	print("Flawless Victory!")


def assign_uuids_store():
	"""
	Assigns publish_uuid for Products, ProductOptions, and ProductPrice
	WARNING: THIS WAS MENT FOR USE ONLY BEFORE PRODUCTS COUNLD BE PUBLISHED
	"""

	PUBLISHABLE_CLASSES = [Product, ProductOption, ProductPrice]

	for PublishableClass in PUBLISHABLE_CLASSES:

		print("Starting Assignment of publish_uuids for %s" % PublishableClass.__name__)

		records = PublishableClass.objects.all()
		total = records.count()
		count = 0

		for record in records:
			count += 1
			publish_uuid = uuid.uuid4()
			record.publish_uuid = publish_uuid
			record.save()
			print("%s: Completed %s (%s/%s)" % (PublishableClass.__name__, record, count, total))

		print("")
		print("")

	print("Flawless Victory!")

################################################
##    STOP ABOVE SCRIPTS MUST FINISH FIRST    ##
################################################
##        TURN PUBLISHING PRODUCTS OFF        ##
################################################

def publish_content_for_products():

	draft_content = ContentProduct.objects.filter(publish_status="DRAFT", master__content_live__isnull=True).exclude(product__isnull=True) # only need to publish, if not already published
	
	TOTAL = draft_content.count()
	count = 0
	for c in draft_content:
		count += 1
		c.publish()
		print("Content Products Published %s/%s" % (count, TOTAL))

	print("Flawless Victory!")


def publish_event_for_products():

	draft_events = Event.objects.filter(publish_status="DRAFT", master__content_live__isnull=True).exclude(product__isnull=True) # only need to publish, if not already published

	TOTAL = draft_events.count()
	count = 0
	for e in draft_events:
		count += 1
		e.publish()
		print("Event Products Published %s/%s" % (count, TOTAL))

	print("Flawless Victory!")

################################################
##    STOP ABOVE SCRIPTS MUST FINISH FIRST    ##
################################################

def move_draft_products_to_live():
	"""
	Will assign all draft products to the appropriate live content version if no product exists for the live copy.
	"""
	print("Querying for draft products that need to be attached to live content...")
	draft_products = Product.objects.filter(
		content__publish_status="DRAFT", # get_products tied to draft content records...
		content__master__content_live__product__isnull=True # ...but only if without live product
	).select_related("content__master__content_live")

	TOTAL = draft_products.count()
	count = 0
	failures = []

	datetime_now = datetime.now()
	administrator = User.objects.get(username="administrator")

	for p in draft_products:
		count += 1
		try:
			p.content = p.content.master.content_live
			p.publish_status = "PUBLISHED"
			p.published_time = datetime_now
			p.published_by = administrator
			p.save()

			# if we got this far, we can then move options and prices for this product
			p.options.update(
				publish_status="PUBLISHED", 
				published_time=datetime_now, 
				published_by=administrator)
			p.prices.update(
				publish_status="PUBLISHED", 
				published_time=datetime_now, 
				published_by=administrator
			)
			print("Saved live product for %s (%s/%s)" % (p.content.title, count, TOTAL) )
		except:
			s = sys.exc_info()
			failures.append((p.id, s[1]))
			print("FAILED (id=%s): %s" % (p.content.master, s[1]) )

	print()
	if not failures:
		print("Flawless Victory!")
	else:
		print("Complete with %s Failed" % len(failures))
		for x in failures:
			print("    %s: %s" % (x[0], x[1]))


###############################################
## NEED TO SWITCH PUBLISHING PRODUCTS ON NOW ##
###############################################

def create_draft_products_from_live():
	"""
	script to create draft copies of all products with live copies but no draft copy,
	uses the publish function
	"""
	print("Querying for draft products that need draft copies...")
	live_products = Product.objects.filter(
		publish_status="PUBLISHED", # get_products tied to published content records...
	).select_related("content__master__content_draft")

	TOTAL = live_products.count()
	count = 0
	failures = []

	for p in live_products:
		count += 1

		try:
			p.publish(replace=("content", p.content.master.content_draft), publish_type="DRAFT")
			print("Copied live product to draft for %s (%s/%s)" % (p.content.title, count, TOTAL) )
		except:
			s = sys.exc_info()
			failures.append((p.id, s[1]))
			print("FAILED (id=%s): %s" % (p.content.master, s[1]) )

	print()
	if not failures:
		print("Flawless Victory!")
	else:
		print("Complete with %s Failed" % len(failures))
		for x in failures:
			print("    %s: %s" % (x[0], x[1]))






#################################
## FOR CHECKNG THAT DATA IS OK ##
#################################

def check_contactroles():

	contactroles = ContactRole.objects.order_by("content__master", "role_type", "contact", "first_name", "last_name").distinct("content__master", "role_type", "contact", "first_name", "last_name")

	print("Total distinct roles: %s" % contactroles.count())

	for contactrole in contactroles:
		cr_set = ContactRole.objects.filter(
			content__master=contactrole.content.master,
			role_type=contactrole.role_type,
			contact=contactrole.contact,
			first_name=contactrole.first_name,
			last_name=contactrole.last_name
		)

		the_count = cr_set.count()
		if the_count > 3:
			print("count: %s, master:%s, contactrole:%s" % (the_count, contactrole.content.master_id, contactrole.id))

	#######
	## NOTE: AFTER RUNNING THIS, IT LOOKS LIKE THERE ARE A TON OF DUPLICATE CONTACT ROLES!!!
	## 		 AFTER LOOKING AT A FEW OF THE RECORDS, IT SEEMS TO ONLY HAPPEN WITH ANONYMOUS RECORDS
	#######

def delete_duplicate_contactroles():

	print("Querying Distinct Contact Roles")
	contactroles = ContactRole.objects.order_by("content", "role_type", "contact", "first_name", "last_name").distinct("content", "role_type", "contact", "first_name", "last_name")

	TOTAL =  contactroles.count()
	count = 0

	print("Total Distinct roles: %s" % TOTAL)

	for contactrole in contactroles:
		count += 1
		cr_set = cr_set = ContactRole.objects.filter(
			content=contactrole.content,
			role_type=contactrole.role_type,
			contact=contactrole.contact,
			first_name=contactrole.first_name,
			last_name=contactrole.last_name
		).order_by("-confirmed", "-invitation_sent", "-permission_av", "-permission_content", "special_status")

		cr_set_count = cr_set.count()

		if cr_set_count > 1:
			keeper = cr_set.first()
			print("Deleting Contact Roles (%s)" % str(int(cr_set_count)-1))
			print("    Keeping: id:%s, content_id:%s, role_type:%s, contact_id:%s" % (keeper.id, keeper.content_id, keeper.role_type, keeper.contact_id if keeper.contact else keeper.first_name + " " + keeper.last_name))
			cr_set.exclude(id=keeper.id).delete()

		if count % 50 == 0:
			print("---- Completed %s/%s" % (count, TOTAL))

	print("Flawless Victory!")

def draft_purchases_to_published():

	print("Querying for products with draft purchases...")

	products = Product.objects.filter(publish_status="DRAFT").exclude(purchases__isnull=True)

	TOTAL = products.count()
	count = 0
	failures = []

	for p in products:
		count += 1

		try:
			live_p = Product.objects.get(publish_status="PUBLISHED", publish_uuid=p.publish_uuid)
			draft_purchases = p.purchases.all()
			draft_purchases_count = draft_purchases.count()
			draft_purchases.update(product=live_p)
			print("Fixed %s purchase records for %s (%s/%s)" % (draft_purchases_count, live_p, count, TOTAL) )
		except:
			s = sys.exc_info()
			failures.append((p.id, s[1]))
			print("FAILED (id=%s): %s" % (p.content.master, s[1]) )

	print()
	if not failures:
		print("Flawless Victory!")
	else:
		print("Complete with %s Failed" % len(failures))
		for x in failures:
			print("    %s: %s" % (x[0], x[1]))


	# duplicate_contactroles = ContactRole.objects.values("content", "contact", "role_type", "first_name", "last_name").annotate(Count('id')).order_by().filter(id__count__gt=1)

# def move_draft_options_and_prices_to_live():
# 	"""
# 	Just need to change the publish_status for everything to "PUBLISHED"
# 	Assumes we haven't done any publishing for products yet.
# 	NOTE:MUST RUN THIS AFTER "move_draft_products_to_live"
# 	"""
# 	datetime_now = datetime.now()
# 	administrator = User.objects.get(username="administrator")

# 	print("Updating Product Options...")
# 	ProductOption.objects.filter(
# 		product__publish_status="PUBLISHED",
# 	).update(
# 		publish_status="PUBLISHED", 
# 		published_time=datetime_now, 
# 		published_by=administrator)

# 	print("Updating Product Prices...")
# 	ProductPrice.objects.filter(
# 		product__publish_status="PUBLISHED", # get_products tied to draft content records...
# 	).update(
# 		publish_status="PUBLISHED", 
# 		published_time=datetime_now, 
# 		published_by=administrator)

# 	print("Flawless Victory!")





