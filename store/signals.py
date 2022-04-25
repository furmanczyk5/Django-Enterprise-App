from django.core.signals import request_started, request_finished
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.urls import reverse
from sentry_sdk import add_breadcrumb, capture_message

from store.models.purchase import Purchase


# @receiver(pre_save, sender=Purchase)
# def enhance_membership_purchase_handler(sender, instance, raw, using, **kwargs):
#     product = instance.product
#     if product.product_type == 'DIVISION':
#         user = instance.user
#         contact = user.contact
#         data = dict(
#             user=user,
#             user_groups=[x.name for x in user.groups.all()],
#             salary_range=contact.salary_range,
#             contact_nmq=contact.is_new_membership_qualified,
#             contact_country=contact.country,
#             product=product,
#             product_price=instance.product_price,
#             get_price_by_contact=product.get_price(contact=contact)
#         )
#         import pprint; pprint.pprint(data)
