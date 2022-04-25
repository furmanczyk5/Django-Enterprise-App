import csv
import os
from datetime import datetime

import pytz
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from cm.models import Provider
from imis import models as imis_models
from imis.tests.factories import name as name_facts
from imis.tests.factories.demographics import (
    MailingDemographicsFactoryBlank, OrgDemographicsFactoryBlank
)
from imis.tests.factories.ind_demographics import ImisIndDemographicsFactoryBlank
from imis.tests.factories.name_address import ImisNameAddressFactoryBlank
from imis.utils import sql as sql_utils
from myapa.models.contact_relationship import ContactRelationship
from myapa.models.proxies import IndividualContact


class Command(BaseCommand):
    help = """Create an Organization record from the given CSV file"""
    data = None
    HEADERS = [
        'company',
        'organization_type',
        'address1',
        'address2',
        'city',
        'state_province',
        'zip_code',
        'country',
        'phone',
        'website',
        'ein_number',
        'bio'
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '-c',
            '--csv',
            help='Path to the CSV file',
            dest='csvfile',
            required=True
        )
        parser.add_argument(
            '-a',
            '--admin-id',
            help='The iMIS ID of the admin of the Organization you want to create',
            dest='admin_id',
            required=True
        )

    def read_csv(self, **options):
        with open(os.path.join(options['csvfile'])) as infile:
            reader = csv.reader(infile)
            header = next(reader)
            self.data = dict(zip(header, next(reader)))

    def _imis_create_name(self):
        name = name_facts.ImisNameFactoryBlank(
            id=imis_models.Counter.create_id('Name'),
            org_code='APA',
            member_type=get_imis_member_type(self.data['organization_type']),
            status='A',
            company_record=True,
            company=self.data['company'],
            work_phone=self.data['phone'],
            city=self.data['city'],
            state_province=self.data['state'],
            country=self.data['country'],
            zip=self.data['zip_code'],
            source_code='WEB',
            website=self.data['personal_url']
        )
        return name

    def _imis_create_name_address(self, name_id):
        name_address = ImisNameAddressFactoryBlank(
            id=name_id,
            address_num=imis_models.Counter.create_id('Name_Address'),
            purpose="Work Address",
            company=self.data['company'],
            address_1=self.data['address1'],
            address_2=self.data['address2'],
            city=self.data['city'],
            state_province=self.data['state'],
            zip=self.data['zip_code'],
            country=self.data['country'],
        )
        name_address.full_address = name_address.get_full_address()
        return name_address

    def create_provider(self, **kwargs):
        provider, _ = Provider.objects.get_or_create(
            company=self.data['company'],
            organization_type=self.data['organization_type'],
            ein_number=self.data['ein_number'],
            address1=self.data['address1'],
            address2=self.data['address2'],
            city=self.data['city'],
            state=self.data['state'],
            zip_code=self.data['zip_code'],
            phone=self.data['phone'],
            personal_url=self.data['personal_url'],
            bio=self.data['bio'],
            contact_type="ORGANIZATION"
        )
        self.provider = provider
        return provider

    def imis_create(self, **kwargs):
        name = self._imis_create_name()
        name_address = self._imis_create_name_address(name.id)
        name.full_address = name_address.full_address
        name.company_sort = name_address.get_company_sort()
        name.set_address_num_fields(name_address.address_num)
        name_address.save()
        create_id_only_records(name.id)
        insert_name_security(name.id)
        insert_name_picture(name.id)
        insert_name_log_record(
            dict(
                date_time=getdate(),
                log_type="CHANGE",
                sub_type="ADD",
                user_id="WEBUSER",
                id=name.id,
                log_text=''
            )
        )
        name.save()
        self.name = name
        user = User.objects.create(username=name.id)
        self.provider.user = user
        self.provider.save()
        return name

    def create_contact_relationship(self):
        cr, _ = ContactRelationship.objects.get_or_create(
            source=self.provider,
            target=self.admin,
            relationship_type="ADMINISTRATOR"
        )
        self.cr = cr

    def handle(self, *args, **options):
        self.read_csv(**options)
        self.create_provider()
        self.imis_create()
        self.admin = IndividualContact.objects.get(user__username=options['admin_id'])
        create_imis_relationship(self.admin, self.name.id, "ADMIN_I", "ADMIN_C")
        self.create_contact_relationship()


def insert_name_security_groups(name_id):
    name_security_groups_data = {
        'id': name_id,
        'security_group': 'WEBUSER'
    }
    name_security_group_insert = sql_utils.make_insert_statement(
        'Name_Security_Groups',
        name_security_groups_data,
        exclude_id_field=False
    )
    sql_utils.do_insert(name_security_group_insert, name_security_groups_data)


def insert_name_picture(name_id):
    name_picture = name_facts.ImisNamePictureFactoryBlank(
        id=name_id,
        picture_num=imis_models.Counter.create_id('Name_Picture')
    )
    name_picture.save()


def insert_name_security(name_id):
    name_security = name_facts.ImisNameSecurityFactoryBlank(
        id=name_id
    )
    name_security_data = name_security.__dict__
    name_security_data.pop('_state')
    name_security_insert = sql_utils.make_insert_statement(
        'Name_Security',
        name_security_data,
        exclude_id_field=False
    )

    sql_utils.do_insert(name_security_insert, name_security_data)


def getdate():
    return datetime.now(tz=pytz.timezone(settings.TIME_ZONE))


def make_name_log_data(data, username):
    name_log_data = data.copy()
    name_log_data['id'] = username
    return name_log_data


def insert_name_log_record(data):
    name_log_insert = sql_utils.make_insert_statement(
        'Name_Log',
        data,
        exclude_id_field=False
    )
    sql_utils.do_insert(name_log_insert, data)


def get_imis_member_type(organization_type):
    mapping = {
        "PRIVATE": "PRI",
        "TRAINING": "PRI",
        "GOV": "AGC",
        "ACADEMIC": "SCH",
        "CONSULTANT": "PRI",
        "NONPROFIT": "PRI"
    }
    return mapping[organization_type]


def create_id_only_records(name_id):
    """
    Create necessary records (empty other than the Name id)
    :param name_id: str
    :return: None
    """
    org_demo = OrgDemographicsFactoryBlank(id=name_id)
    org_demo.save()
    ind_demo = ImisIndDemographicsFactoryBlank(id=name_id)
    ind_demo.save()
    name_fin = name_facts.ImisNameFinFactoryBlank(id=name_id)
    name_fin.save()
    mdemo = MailingDemographicsFactoryBlank(id=name_id)
    mdemo.save()


def create_imis_relationship(contact, co_id, relation_type, target_relation_type):
    now = timezone.now()
    relationship = imis_models.Relationship(
        id=contact.user.username,
        target_id=co_id,
        relation_type=relation_type,
        target_relation_type=target_relation_type,
        seqn=imis_models.Counter.create_id('Relationship'),
        last_updated=now,
        date_added=now,
        updated_by="WEBUSER",
        title='',
        functional_title='',
        status='',
        last_string='',
        group_code=''
    )
    relationship.save()
    name = imis_models.Name.objects.get(id=contact.user.username)
    name.co_id = co_id
    name.save()
    return relationship

