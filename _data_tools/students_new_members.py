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

from datetime import date

# YET ANOTHER RANDOM COMMENT
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import is_password_usable
from django.core.mail import send_mail

from datetime import timedelta

from django.db.models import Q

from content.models import *
from myapa.models import ContactRole
from store.models import *

# WHAT ARE THE DIVISION / CHAPTER / MEMBERSHIP PRICING STRUCTURE FOR NEW MEMBERS??
# STUDENT = K
# NEW MEMBER = R

def create_products():
	chapters = Product.objects.filter(product_type='CHAPTER', publish_status='DRAFT')
	divisions = Product.objects.filter(product_type='DIVISION', publish_status='DRAFT')
	memberships = Product.objects.filter(product_type='DUES', publish_status='DRAFT', imis_code='APA')

	for membership in memberships:
		print("creating membership product price: " + str(membership.title))
		if membership.code == "MEMBERSHIP_STU":
			ProductPrice.objects.filter(code="K", product=membership).delete()
			stu_mem, created = ProductPrice.objects.get_or_create(product = membership,code='K')
			stu_mem.price = 0
			stu_mem.title = "Student Member Price"
			stu_mem.save()
			membership.content.publish()
		elif membership.code == "MEMBERSHIP_MEM":
			ProductPrice.objects.filter(code="L", product=membership).delete()
			nm_mem, created = ProductPrice.objects.get_or_create(product = membership, code='L')
			nm_mem.price = 75
			nm_mem.title = "New Member Price"
			nm_mem.save()
			membership.content.publish()

	for chapter in chapters:
		print("creating chapter product price: " + str(chapter.title))

		ProductPrice.objects.filter(code="K", product=chapter).delete()
		stu_chapt, created = ProductPrice.objects.get_or_create(product = chapter, code='K')
		stu_chapt.price = 0
		stu_chapt.title = "Student Member Price"
		stu_chapt.save()
		chapter.content.publish()


		ProductPrice.objects.filter(code="L", product=chapter).delete()
		nm_chapt, created = ProductPrice.objects.get_or_create(product = chapter, code='L')
		nm_chapt.price = 20
		nm_chapt.title = "New Member Price"
		nm_chapt.save()
		chapter.content.publish()

	for division in divisions:
		print("creating division product price: " + str(division.title))

		ProductPrice.objects.filter(code="K", product=division).delete()
		stu_div, created = ProductPrice.objects.get_or_create(product = division, code='K')
		stu_div.price = 0
		stu_div.title = "Student Member Price"
		stu_div.save()
		division.content.publish()


		ProductPrice.objects.filter(code="L", product=division).delete()
		nm_div, created = ProductPrice.objects.get_or_create(product = division, code='L')
		nm_div.price = 10
		nm_div.title = "New Member Price"
		nm_div.save()
		division.content.publish()


	print("complete")
