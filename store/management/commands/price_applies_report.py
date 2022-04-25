import csv
import os
import tempfile

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError

from myapa.models.proxies import IndividualContact
from myapa.tests.factories.contact import ContactFactoryIndividual
from myapa.tests.views.test_join import get_zip_code_for_state, get_state_zip
from store.models.product_cart import ProductCart


REPORT_FIELDS = [
    "current_time",  # timezone.now
    "begin_time",  # price attr
    "end_time",  # price attr
    "option",  # method parameter
    "option_code",  # price attr
    "other_required_product_code",  # price attr
    "other_required_product_must_be_in_cart",  # price attr
    "other_required_option_code",  # price attr
    "min_quantity",  # price attr
    "max_quantity",  # price attr
    "code",  # ProductCart attr
    "product_type",  # ProductCart attr
    "contact",  # method parameter
    "contact.salary_range",  # Contact attr
    "price.code",  # price attr
    "contact.country",  # Contact attr
    "contact.get_country_type_code",  # Contact method
    "prices_applies_except_group",  # price
    "price.required_groups",  # price RelatedManager
    "user",  # contact.user if contact else None
    "has_required_group",  # if user in price.required_groups/all_future_groups
    "cart_products",  # [p.product for p in purchases] if p.order is None]
    "all_future_groups",  # all ProductCart.future_groups in cart_products
    "exclude_groups",  # price RelatedManager
    "applies",  # price attr, local method
]


def get_products():
    product_types = ["DIVISION", "CHAPTER", "PUBLICATION_SUBSCRIPTION"]
    products = ProductCart.objects.filter(product_type__in=product_types)
    return products


def get_contacts():
    contacts = []
    state_zip = get_state_zip()
    state_abbrs = list(set([x[0] for x in state_zip]))
    for state_abbr in state_abbrs:
        zip_code = get_zip_code_for_state(state_abbr, state_zip)
        contact = ContactFactoryIndividual(
            state=state_abbr,
            zip_code=zip_code,
            member_type='NOM',
            salary_range='L'
        )
        contact.user.groups.add(Group.objects.get(name='new-member'))
        contacts.append(contact)
    return contacts


class Command(BaseCommand):
    help = """ """

    def add_arguments(self, parser):
        parser.add_argument(
            '-o',
            '--outfile',
            dest='outfile',
            default='/tmp/price_report.csv'
        )

    def handle(self, *args, **options):
        header = [
            'PRODUCT_CODE',
            'PRODUCT_TITLE',
            'CONTACT_STATE',
            'CONTACT_WEB_GROUPS',
            'PRODUCT_REQUIRED_GROUPS',
            'CONTACT_SALARY_RANGE',
            'PRODUCT_PRICE_CODE',
            'PRODUCT_PRICE',
        ]
        contacts = get_contacts()
        products = get_products()

        with open(options['outfile'], 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)

            for product in products:
                for contact in contacts:
                    price = product.get_price(contact=contact)
                    if price is None:
                        continue
                    row = [
                        product.code,
                        product.title,
                        contact.state,
                        ', '.join([i.name for i in contact.user.groups.all()]),
                        ', '.join([i.name for i in price.required_groups.all()]),
                        contact.salary_range,
                        price.code,
                        price.price
                    ]
                    writer.writerow(row)

        User.objects.filter(pk__in=[x.user.pk for x in contacts]).delete()
        IndividualContact.objects.filter(pk__in=[x.pk for x in contacts]).delete()
