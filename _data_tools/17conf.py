from store.models import *
from events.models import *
from content.models import *

def clear_shopping_cart(master_id='9102340'):
	"""
	deletes old shopping cart activities
	"""

	title = Content.objects.get(master__id=master_id, publish_status='PUBLISHED').title
	old_master_ids = Content.objects.filter(parent__id=master_id).values_list('master__id', flat=True)
	old_purchases = Purchase.objects.filter(product__content__master__id__in=old_master_ids, order__isnull=True)
	
	# how to return a real flat list so this can be added to the above queryset? 
	old_master_purchases = Purchase.objects.filter(product__content__master__id=master_id, order__isnull=True)

	print("{0} shopping cart items will be deleted that are for item {1} ".format(old_master_purchases.count(), title))
	print("{0} shopping cart items to be deleted that are related to {1}".format(old_purchases.count(), title))
	print("There's no going back after this. Please verify the master id entered is correct.")

	user_response = input("Are you sure you want to continue? Enter YES or NO: ")

	if user_response == "YES":
		old_purchases.delete()
		old_master_purchases.delete()
		print("The deed is done.")
	else:
		print("Nothing was deleted.")
