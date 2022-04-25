import json
import os

from django.conf import settings
from django.contrib.auth.models import Group
from django.core import serializers
from django.core.management.base import BaseCommand

from content.models import Content
from store.models import ProductCart


PRODUCT_SERIALIZE_FIELDS = [
    'code',
    'content',
    'future_groups',
    'gl_account',
    'imis_code',
    'individuals_can_purchase',
    'max_quantity',
    'max_quantity_per_person',
    'max_quantity_standby',
    'product_type',
    'title',
    'created_time',
    'updated_time',
    'status',
    'publish_status'
]
PRODUCT_PRICE_SERIALIZE_FIELDS = [
    'begin_time',
    'code',
    'end_time',
    'exclude_groups',
    'max_quantity',
    'min_quantity',
    'option_code',
    'other_required_option_code',
    'other_required_product_code',
    'other_required_product_must_be_in_cart',
    'price',
    'priority',
    'product',
    'required_groups',
    'required_product',
    'required_product_option',
    'required_product_options',
    'title',
    'created_time',
    'updated_time',
    'status',
    'publish_status'
]


class Command(BaseCommand):
    help = """Serialize MEMBERSHIP_, CHAPT_, and DIVISION_ products to JSON files
    in store/fixtures/"""

    def handle(self, *args, **options):
        serialize_all()
        self.stdout.write(
            self.style.SUCCESS(
                "JSON files written to store/fixtures/"
            )
        )


def serialize_all():
    for codes in [
        ('MEMBERSHIP_', 'membership'),
        ('DIVISION_', 'division'),
        ('CHAPT_', 'chapter')
    ]:
        serialize_products(*codes)
    serialize_groups()


def serialize_products(code, file_prefix):
    """
    :param code: str, code to filter Products on startwsith
    :param file_prefix: str, filename prefix to use when writing serialized data to
    the store/fixtures directory

    Serialize Membership, Chapter, and Divison products.
    See the
    `Django docs <https://docs.djangoproject.com/en/1.11/topics/serialization/>`_
    for more information
    :return:
    """
    products = ProductCart.objects.filter(code__startswith=code)
    data = json.loads(serializers.serialize('json', products, fields=PRODUCT_SERIALIZE_FIELDS))
    for row in data:
        row['fields']['created_by'] = 1
        row['fields']['updated_by'] = 1
    with open(os.path.join(settings.BASE_DIR, 'store/fixtures/{}_products.json'.format(file_prefix)), 'w') as out:
        json.dump(data, out, indent=2)

    content = Content.objects.filter(product__in=products)
    data = json.loads(serializers.serialize('json', content, fields=('title', 'created_time', 'updated_time', 'status', 'publish_status')))
    for row in data:
        row['fields']['created_by'] = 1
        row['fields']['updated_by'] = 1
    with open(os.path.join(settings.BASE_DIR, 'store/fixtures/{}_content.json'.format(file_prefix)), 'w') as out:
        json.dump(data, out, indent=2)

    prices = []
    for x in products:
        data = json.loads(serializers.serialize('json', x.prices.all(), fields=PRODUCT_PRICE_SERIALIZE_FIELDS))
        for row in data:
            row['fields']['created_by'] = 1
            row['fields']['updated_by'] = 1
        prices.extend([z for z in data])
    with open(os.path.join(settings.BASE_DIR, 'store/fixtures/{}_product_prices.json'.format(file_prefix)), 'w') as out:
        json.dump(prices, out, indent=2)


def serialize_groups():
    groups = Group.objects.filter(permissions__isnull=True)
    data = json.loads(serializers.serialize('json', groups))
    with open(os.path.join(settings.BASE_DIR, 'store/fixtures/product_groups.json'), 'w') as out:
        json.dump(data, out, indent=2)
