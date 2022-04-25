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

def create():
	"""
	creates a provider user for those contacts without one
	"""

	contacts = Contact.objects.filter(contact_type='ORGANIZATION')

	for contact in contacts:
		user, created = User.objects.get_or_create(username=contact.olduser_id)
		user.is_active = False
		user.save()
		if created:
			print("user account created for id: " + str(contact.olduser_id))

def provider_orders_fix():
	"""
	fixes the purchase contact_recipient field for cm registration and cm per credit purchases
	"""
	purchases = Purchase.objects.filter(product__code__in=("CM_PROVIDER_MISC","PRODUCT_CM_PER_CREDIT_2015","PRODUCT_CM_PER_CREDIT","CM_PROVIDER_DAY_2015","CM_PROVIDER_WEEK_2015","CM_PROVIDER_BUNDLE100_2015","CM_PROVIDER_DISTANCE_2015","CM_PROVIDER_BUNDLE50_2015","CM_PROVIDER_REGISTRATION_2015","CM_PROVIDER_REGISTRATION","CM_PROVIDER_ANNUAL_2015")).exclude(order__isnull=True)

	print("There are {0} CM purchases".format(str(len(purchases))))

	orders_updated = []
	failed_orders = []
	for purchase in purchases:

		if purchase.contact == purchase.contact_recipient or purchase.user.contact == purchase.contact_recipient:
			try:
				provider_relationship = ContactRelationship.objects.select_related("source").filter(target=purchase.user.contact, relationship_type='ADMINISTRATOR').first()

				if provider_relationship:
					purchase.contact_recipient = provider_relationship.source
					purchase.save()
					print("contact recipient field changed successfully!")
					orders_updated.append(purchase.order.id)
				else:
					print("The user does not appear to be an administrator for any provider.")
					failed_orders.append(purchase.order.id)
			except Exception as e:
				print('failed to update purchase record!')
				print('reason: ' + str(e))
				pass

	print('complete!')
	print('successful changes: ' + str(len(orders_updated)))
	print('failed changes: ' + str(len(failed_orders)))

