import django
django.setup()
from store.models import Purchase

# CM remove purchases

def remove_purchases():
	cart_purchases = Purchase.objects.filter(product__product_type__in = ('CM_REGISTRATION','CM_PER_CREDIT'), order__isnull=True)
	print("Deleting all %s purchases " % cart_purchases.count() ) 
	cart_purchases.delete()

