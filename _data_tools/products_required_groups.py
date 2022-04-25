import csv
import os
import yaml
from datetime import datetime

from django.contrib.auth.models import Group

from store.models import Product


def load_yaml(path):
    with open(path) as infile:
        group_names = yaml.load(infile)['group_names_to_delete']
        return group_names


def get_products(group_names):
    group_names = load_yaml('myapa/management/commands/login_group_config/group_names_to_delete.yml')
    groups = Group.objects.get(name__in=group_names)

    products = Product.objects.filter(status='A', publish_status="PUBLISHED", prices__required_groups__in=groups)
    return products


def write_csv(products, outfile='/tmp/products_required_groups.csv'):
    headers = [
            'PRODUCT_TYPE'
            'PRODUCT_IMIS_CODE',
            'PRODUCT_CONTENT_MASTER_ID',
            'PRODUCT_CONTENT_TITLE',
            'PRODUCT_CONTENT_TYPE'
            'PRODUCT_CONTENT_RESOURCE_URL',
            'PRODUCT_PRICE_REQUIRED_GROUPS',
        ]

    with open(outfile, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)

        for prod in products:
            row = []
            row.append(prod.product_type)
            row.append(prod.imis_code or '')
            row.append(prod.content.master_id)
            row.append(prod.content.title)
            row.append(prod.content.content_type)
            row.append(prod.content.resource_url or '')
            price_required_groups = []
            for price in prod.prices.all():
                price_required_groups.extend([x.name for x in price.required_groups.all()])
            row.append('|'.join(list(set(price_required_groups))))

            writer.writerow(row)
