import csv
import json

from django.core.management.base import BaseCommand

from content.models import MasterContent, TaxoTopicTag
from knowledgebase.models import Resource, Collection, CollectionRelationship
from myapa.models import Contact, ContactRole
from .csv_transforms.contact import *
from .csv_transforms.resource import *

REMAINDER_TEXT = (
    ', an electronic text contained in the APA Library E-book Collection. '
    'This text is available to APA members as a benefit of membership.'
)

COLLECTION_CODE = 'KNOWLEDGEBASE_PROCEEDINGS'


class Command(BaseCommand):
    help = 'Adds conference proceedings from CSV to KnowledgeBase'

    def add_arguments(self, parser):
        parser.add_argument('file_name', nargs='+', type=str)

    def handle(self, *args, **options):
        file_name = options['file_name'][0]
        self.read_file(file_name)

    def read_file(self, file_name):
        with open(file_name) as csv_file:
            collection = self.get_collection()
            csv_reader = csv.DictReader(csv_file)
            resources = self.transform_csv(csv_reader, collection)

    def get_collection(self):
        collection = Collection.objects.get(code=COLLECTION_CODE, publish_status='PUBLISHED')
        if not collection:
            raise Exception('Collection not found. Resources not created.')
  
        return collection

    def transform_csv(self, csv_reader, collection):
        resources = [
            self.transform_row(dict(row))
            for row in csv_reader
            if dict(row).get('Title', '').strip()
        ]

        [
            self.create_models(resource, collection)
            for resource in resources
        ]

        return resources

    def transform_row(self, row_dict):
        return reduce(
            lambda d, func: func(d),
            [
                remove_year,
                add_resource_url,
                add_title,
                add_subtitle,
                add_text,
                add_contact,
                add_additional_data
            ],
            row_dict
        )

    def create_models(self, resource_dict, collection):
        if resource_dict.get('contact'):
            contact = self.create_contact(resource_dict)
            resource = self.create_resource(resource_dict)
            contact_role = self.create_contact_role(resource, contact)
        else:
            resource = self.create_resource(resource_dict)

        collection_relationship = self.create_collection_relationship(resource, collection)
        resource.publish()
        resource.solr_publish()
        self.stdout.write(
            self.style.SUCCESS(
                'Published {}'.format(resource.title)
            )
        )
        return resource

    def create_contact(self, resource):
        contact = resource.pop('contact')
        if contact.get('contact_type') == "ORGANIZATION":
            contact = Contact.objects.filter(**contact).first()
            if contact is not None:
                return contact
        else:
            try:
                contact, _ = Contact.objects.get_or_create(**contact)
            except Contact.MultipleObjectsReturned:
                self.stdout.write(
                    self.style.WARNING(
                        "WARNING: Multiple Contacts returned with query parameters:\n{}".format(
                            json.dumps(contact, indent=2)
                        )
                    )
                )
                contact = Contact.objects.filter(**contact).first()

        return contact

    def create_resource(self, row_dict):
        resource, _ = Resource.objects.get_or_create(**row_dict)
        taxo_tag = TaxoTopicTag.objects.get(code='SKILLSETHISTORY')
        resource.url = '/knowledgebase/resource/{}'.format(resource.master_id)
        resource.taxo_topics.add(taxo_tag)
        resource.save()
        return resource

    def create_contact_role(self, resource, contact):
        contact_role, _ = ContactRole.objects.get_or_create(
            content=resource,
            contact=contact,
            role_type='AUTHOR'
        )
        return contact_role

    def create_collection_relationship(self, resource, collection):
        master_collection = MasterContent.objects.get(id=collection.master_id)
        collection_relationship, _ = CollectionRelationship.objects.get_or_create(
            content=resource,
            content_master_related=master_collection,
            relationship='KNOWLEDGEBASE_COLLECTION'
        )
        return collection_relationship
