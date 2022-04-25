# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.

from __future__ import unicode_literals

import datetime
import json
import logging
import os
import re
import xml.etree.ElementTree as ET
import random
import string
import pytz
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction, IntegrityError
from django.utils import timezone

from api.clients.voter_voice import VoterVoiceClient, STATE_HOUSE, STATE_SENATE, US_HOUSE
from content.utils import ImplicitFTP_TLS, validate_lon_lat
from planning.settings import PROMETRIC_FTP_HOST, PROMETRIC_FTP_PORT, PROMETRIC_FTP_USERNAME, PROMETRIC_FTP_PASSWORD
from .db_accessor import DbAccessor

logger = logging.getLogger(__name__)

DEGREE_LEVELS = (
    ("B", "Undergraduate"),
    ("M", "Graduate"),
    ("P", "PhD/J.D."),
    ("N", "Other Degree"),
)

DEGREE_TYPES = [
    "Planning",
    "Architecture",
    "Engineering",
    "Environmental Science",
    "Geography",
    "International Studies",
    "Landscape Architecture",
    "Political Science",
    "Public Administration",
    "Public Health",
    "Social Work",
    "Sociology",
    "Urban Studies"]


def remove_degree_program_dupes(degree_programs):
    excludes = []
    temp_programs = degree_programs
    for dp in degree_programs:
        others = temp_programs.exclude(seqn=dp.seqn)
        for o in others:
            if dp.degree_program == o.degree_program and dp.degree_level == o.degree_level:
                if dp.school_program_type == "PAB":
                    cut = o
                elif o.school_program_type == "PAB":
                    cut = dp
                else:
                    cut = o if dp.school_program_type != '' else dp
                excludes.append(cut)
        temp_programs = others
    ex_seqn = [e.seqn for e in excludes]
    return degree_programs.exclude(seqn__in=ex_seqn)


def split_zip_code(zip_code):
    retval = {'zip_code': '', 'zip_code_extension': ''}
    if not isinstance(zip_code, str):
        return retval
    zip_code_split = zip_code.split('-')
    retval['zip_code'] = zip_code_split[0]
    retval['zip_code_extension'] = zip_code_split[1] if len(zip_code_split) > 1 else ''
    return retval


class JSONResponseMixin(object):
    """
    Mixin for serving up JSON responses that mimic the old Node Restify API
    """
    def json_response(self):
        """
        A JSON-encodeable dict of all fields for this record
        :return: dict
        """
        resp = self.__dict__
        resp.pop('_state')
        for field in self._meta.fields:
            field_type = field.get_internal_type()
            if field_type == 'DateTimeField' \
                    and getattr(self, field.name, None) is not None:
                resp[field.name] = resp[field.name].strftime(
                    '%Y-%m-%dT%H:%M:%S.000Z'
                )
            elif field_type == 'DecimalField' \
                    and getattr(self, field.name, None) is not None:
                resp[field.name] = round(float(resp[field.name]), 2)
        assert json.dumps(resp)
        return resp


class Name(JSONResponseMixin, models.Model):
    id = models.CharField(db_column='ID', primary_key=True, max_length=10)  # Field name made lowercase.
    org_code = models.CharField(db_column='ORG_CODE', max_length=5)  # Field name made lowercase.
    member_type = models.CharField(db_column='MEMBER_TYPE', max_length=5)  # Field name made lowercase.
    category = models.CharField(db_column='CATEGORY', max_length=5)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=5)  # Field name made lowercase.
    major_key = models.CharField(db_column='MAJOR_KEY', max_length=15)  # Field name made lowercase.
    co_id = models.CharField(db_column='CO_ID', max_length=10)  # Field name made lowercase.
    last_first = models.CharField(db_column='LAST_FIRST', max_length=70)  # Field name made lowercase.
    company_sort = models.CharField(db_column='COMPANY_SORT', max_length=30)  # Field name made lowercase.
    bt_id = models.CharField(db_column='BT_ID', max_length=10)  # Field name made lowercase.
    dup_match_key = models.CharField(db_column='DUP_MATCH_KEY', max_length=20)  # Field name made lowercase.
    full_name = models.CharField(db_column='FULL_NAME', max_length=70)  # Field name made lowercase.
    title = models.CharField(db_column='TITLE', max_length=80)  # Field name made lowercase.
    company = models.CharField(db_column='COMPANY', max_length=80)  # Field name made lowercase.
    full_address = models.CharField(db_column='FULL_ADDRESS', max_length=255)  # Field name made lowercase.
    prefix = models.CharField(db_column='PREFIX', max_length=25)  # Field name made lowercase.
    first_name = models.CharField(db_column='FIRST_NAME', max_length=20)  # Field name made lowercase.
    middle_name = models.CharField(db_column='MIDDLE_NAME', max_length=20)  # Field name made lowercase.
    last_name = models.CharField(db_column='LAST_NAME', max_length=30)  # Field name made lowercase.
    suffix = models.CharField(db_column='SUFFIX', max_length=10)  # Field name made lowercase.
    designation = models.CharField(db_column='DESIGNATION', max_length=20)  # Field name made lowercase.
    informal = models.CharField(db_column='INFORMAL', max_length=20)  # Field name made lowercase.
    work_phone = models.CharField(db_column='WORK_PHONE', max_length=25)  # Field name made lowercase.
    home_phone = models.CharField(db_column='HOME_PHONE', max_length=25)  # Field name made lowercase.
    fax = models.CharField(db_column='FAX', max_length=25)  # Field name made lowercase.
    toll_free = models.CharField(db_column='TOLL_FREE', max_length=25)  # Field name made lowercase.
    city = models.CharField(db_column='CITY', max_length=40)  # Field name made lowercase.
    state_province = models.CharField(db_column='STATE_PROVINCE', max_length=15)  # Field name made lowercase.
    zip = models.CharField(db_column='ZIP', max_length=10)  # Field name made lowercase.
    country = models.CharField(db_column='COUNTRY', max_length=25)  # Field name made lowercase.
    mail_code = models.CharField(db_column='MAIL_CODE', max_length=5)  # Field name made lowercase.
    crrt = models.CharField(db_column='CRRT', max_length=40)  # Field name made lowercase.
    bar_code = models.CharField(db_column='BAR_CODE', max_length=14)  # Field name made lowercase.
    county = models.CharField(db_column='COUNTY', max_length=30)  # Field name made lowercase.
    mail_address_num = models.IntegerField(db_column='MAIL_ADDRESS_NUM')  # Field name made lowercase.
    bill_address_num = models.IntegerField(db_column='BILL_ADDRESS_NUM')  # Field name made lowercase.
    gender = models.CharField(db_column='GENDER', max_length=1)  # Field name made lowercase.
    birth_date = models.DateTimeField(db_column='BIRTH_DATE', blank=True, null=True)  # Field name made lowercase.
    us_congress = models.CharField(db_column='US_CONGRESS', max_length=20)  # Field name made lowercase.
    state_senate = models.CharField(db_column='STATE_SENATE', max_length=20)  # Field name made lowercase.
    state_house = models.CharField(db_column='STATE_HOUSE', max_length=20)  # Field name made lowercase.
    sic_code = models.CharField(db_column='SIC_CODE', max_length=10)  # Field name made lowercase.
    chapter = models.CharField(db_column='CHAPTER', max_length=15)  # Field name made lowercase.
    functional_title = models.CharField(db_column='FUNCTIONAL_TITLE', max_length=50)  # Field name made lowercase.
    contact_rank = models.IntegerField(db_column='CONTACT_RANK')  # Field name made lowercase.
    member_record = models.BooleanField(db_column='MEMBER_RECORD')  # Field name made lowercase.
    company_record = models.BooleanField(db_column='COMPANY_RECORD')  # Field name made lowercase.
    join_date = models.DateTimeField(db_column='JOIN_DATE', blank=True, null=True)  # Field name made lowercase.
    source_code = models.CharField(db_column='SOURCE_CODE', max_length=40)  # Field name made lowercase.
    paid_thru = models.DateTimeField(db_column='PAID_THRU', blank=True, null=True)  # Field name made lowercase.
    member_status = models.CharField(db_column='MEMBER_STATUS', max_length=5)  # Field name made lowercase.
    member_status_date = models.DateTimeField(db_column='MEMBER_STATUS_DATE', blank=True, null=True)  # Field name made lowercase.
    previous_mt = models.CharField(db_column='PREVIOUS_MT', max_length=5)  # Field name made lowercase.
    mt_change_date = models.DateTimeField(db_column='MT_CHANGE_DATE', blank=True, null=True)  # Field name made lowercase.
    co_member_type = models.CharField(db_column='CO_MEMBER_TYPE', max_length=5)  # Field name made lowercase.
    exclude_mail = models.BooleanField(db_column='EXCLUDE_MAIL')  # Field name made lowercase.
    exclude_directory = models.BooleanField(db_column='EXCLUDE_DIRECTORY')  # Field name made lowercase.
    date_added = models.DateTimeField(db_column='DATE_ADDED', blank=True, null=True)  # Field name made lowercase.
    last_updated = models.DateTimeField(db_column='LAST_UPDATED', blank=True, null=True)  # Field name made lowercase.
    updated_by = models.CharField(db_column='UPDATED_BY', max_length=60)  # Field name made lowercase.
    intent_to_edit = models.CharField(db_column='INTENT_TO_EDIT', max_length=80)  # Field name made lowercase.
    address_num_1 = models.IntegerField(db_column='ADDRESS_NUM_1')  # Field name made lowercase.
    address_num_2 = models.IntegerField(db_column='ADDRESS_NUM_2')  # Field name made lowercase.
    address_num_3 = models.IntegerField(db_column='ADDRESS_NUM_3')  # Field name made lowercase.
    email = models.CharField(db_column='EMAIL', max_length=100)  # Field name made lowercase.
    website = models.CharField(db_column='WEBSITE', max_length=255)  # Field name made lowercase.
    ship_address_num = models.IntegerField(db_column='SHIP_ADDRESS_NUM')  # Field name made lowercase.
    display_currency = models.CharField(db_column='DISPLAY_CURRENCY', max_length=3)  # Field name made lowercase.
    mobile_phone = models.CharField(db_column='MOBILE_PHONE', max_length=25)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Name'

    def json_response_company(self):
        """
        A JSON-encodeable dict to replace the Node Restify API for /contacts/{id}/organizations
        :return: dict
        """
        if self.company_record:
            return {
                'id': self.id,
                'is_company': True,
                'member_type': self.member_type,
                'status': self.status,
                'co_id': self.co_id,
                'last_first': self.last_first,
                'company': self.company,
                'full_name': self.full_name,
                'chapter': self.chapter,
                'title': self.title,
                'full_address': self.full_address,
                'work_phone': self.work_phone,
                'home_phone': self.home_phone,
                'mobile_phone': self.mobile_phone,
                'fax': self.fax,
                'city': self.city,
                'state_province': self.state_province,
                'zip': self.zip,
                'country': self.country,
                'join_date': self.join_date.strftime(
                    '%Y-%m-%dT%H:%M:%S.000Z'
                ) if self.join_date is not None else None,
                'paid_thru': self.paid_thru.strftime(
                    '%Y-%m-%dT%H:%M:%S.000Z'
                ) if self.paid_thru is not None else None,
                'email': self.email
            }
        return {}

    def set_address_num_fields(self, address_num):
        for field in [
            'mail_address_num',
            'bill_address_num',
            'address_num_1',
            'address_num_2',
            'address_num_3'
        ]:
            setattr(self, field, address_num)
        self.save()


class NameAddress(models.Model):
    id = models.CharField(db_column='ID', max_length=10)  # Field name made lowercase.
    address_num = models.IntegerField(db_column='ADDRESS_NUM', primary_key=True)  # Field name made lowercase.
    purpose = models.CharField(db_column='PURPOSE', max_length=20)  # Field name made lowercase.
    company = models.CharField(db_column='COMPANY', max_length=80)  # Field name made lowercase.
    address_1 = models.CharField(db_column='ADDRESS_1', max_length=40)  # Field name made lowercase.
    address_2 = models.CharField(db_column='ADDRESS_2', max_length=40)  # Field name made lowercase.
    city = models.CharField(db_column='CITY', max_length=40)  # Field name made lowercase.
    state_province = models.CharField(db_column='STATE_PROVINCE', max_length=15)  # Field name made lowercase.
    zip = models.CharField(db_column='ZIP', max_length=10)  # Field name made lowercase.
    country = models.CharField(db_column='COUNTRY', max_length=25)  # Field name made lowercase.
    crrt = models.CharField(db_column='CRRT', max_length=40)  # Field name made lowercase.
    dpb = models.CharField(db_column='DPB', max_length=8)  # Field name made lowercase.
    bar_code = models.CharField(db_column='BAR_CODE', max_length=14)  # Field name made lowercase.
    country_code = models.CharField(db_column='COUNTRY_CODE', max_length=10)  # Field name made lowercase.
    address_format = models.SmallIntegerField(db_column='ADDRESS_FORMAT')  # Field name made lowercase.
    full_address = models.CharField(db_column='FULL_ADDRESS', max_length=255)  # Field name made lowercase.
    county = models.CharField(db_column='COUNTY', max_length=30)  # Field name made lowercase.
    us_congress = models.CharField(db_column='US_CONGRESS', max_length=5)  # Field name made lowercase.
    state_senate = models.CharField(db_column='STATE_SENATE', max_length=5)  # Field name made lowercase.
    state_house = models.CharField(db_column='STATE_HOUSE', max_length=5)  # Field name made lowercase.
    mail_code = models.CharField(db_column='MAIL_CODE', max_length=5)  # Field name made lowercase.
    phone = models.CharField(db_column='PHONE', max_length=25)  # Field name made lowercase.
    fax = models.CharField(db_column='FAX', max_length=25)  # Field name made lowercase.
    toll_free = models.CharField(db_column='TOLL_FREE', max_length=25)  # Field name made lowercase.
    company_sort = models.CharField(db_column='COMPANY_SORT', max_length=30)  # Field name made lowercase.
    note = models.TextField(db_column='NOTE', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    status = models.CharField(db_column='STATUS', max_length=5)  # Field name made lowercase.
    last_updated = models.DateTimeField(db_column='LAST_UPDATED', blank=True, null=True)  # Field name made lowercase.
    list_string = models.CharField(db_column='LIST_STRING', max_length=255)  # Field name made lowercase.
    preferred_mail = models.BooleanField(db_column='PREFERRED_MAIL')  # Field name made lowercase.
    preferred_bill = models.BooleanField(db_column='PREFERRED_BILL')  # Field name made lowercase.
    last_verified = models.DateTimeField(db_column='LAST_VERIFIED', blank=True, null=True)  # Field name made lowercase.
    email = models.CharField(db_column='EMAIL', max_length=100)  # Field name made lowercase.
    bad_address = models.CharField(db_column='BAD_ADDRESS', max_length=10)  # Field name made lowercase.
    no_autoverify = models.BooleanField(db_column='NO_AUTOVERIFY')  # Field name made lowercase.
    last_qas_batch = models.DateTimeField(db_column='LAST_QAS_BATCH', blank=True, null=True)  # Field name made lowercase.
    address_3 = models.CharField(db_column='ADDRESS_3', max_length=40)  # Field name made lowercase.
    preferred_ship = models.BooleanField(db_column='PREFERRED_SHIP')  # Field name made lowercase.
    informal = models.CharField(db_column='INFORMAL', max_length=20)  # Field name made lowercase.
    title = models.CharField(db_column='TITLE', max_length=80)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Name_Address'

    def __str__(self):
        return "{address_1}\n{city}, {state_province} {zip}\n{country}".format(**self.__dict__)

    def json_response(self):
        return {
            'id': self.id,
            'purpose': self.purpose,
            'address_1': self.address_1,
            'address_2': self.address_2,
            'city': self.city,
            'state_province': self.state_province,
            'zip': self.zip,
            'country': self.country,
            'company': self.company,
            'country_code': self.country_code,
            'preferred_mail': self.preferred_mail,
            'preferred_bill': self.preferred_bill,
            'address_num': self.address_num
        }

    def get_full_address(self):
        """Build up the full_address field from its component parts.
        Using carriage returns for the newlines because Microsoft"""
        if not self.address_1 and not self.city and not self.country:
            raise ValueError(
                'Name_Address records must at least have values for address_1, city, and country'
            )
        lines = [
            self.address_1,
            '{}, {} {}'.format(self.city, self.state_province or '', self.zip or ''),
            self.country.upper()
        ]
        if self.address_2:
            lines.insert(1, self.address_2)
        # TODO: Do we have to use carriage returns only?
        return '\r'.join(lines)

    def get_company_sort(self):
        """Compute the value of the company_sort field, based on the company field"""
        if self.company:
            company_sort = self.company.upper()[:30].strip()
            # Remove "THE" from the front of a company name
            return re.sub('^THE\s+', '', company_sort)
        return ''

    def as_django_form_initial(self, additional=False):
        """
        Return a dictionary suitable for use in :class:`myapa.forms.account.UpdateAddressForm`
        :param additional: bool, whether or not to prefix the dict keys with "additional_",
                           for the additional address form
        :return: dict
        """
        initial = dict(
            user_address_num=self.address_num,
            address1=self.address_1.strip(),
            address2=self.address_2.strip(),
            city=self.city.strip(),
            state=self.state_province.strip(),
            zip_code=self.zip.strip(),
            country=self.country.strip(),
            company=self.company.strip()
        )
        if additional:
            initial = {"additional_{}".format(k): v for (k, v) in initial.items()}
        return initial

    def get_votervoice_address_query(self):
        from myapa.models.constants import UNITED_STATES

        if self.country == UNITED_STATES:
            return dict(
                address1=self.address_1,
                address2=self.address_2,
                city=self.city,
                state=self.state_province,
                zipcode=split_zip_code(self.zip)['zip_code'],
                country='US'
            )
        else:
            return dict()

    def validate_address(self):
        client = VoterVoiceClient()
        address_params = self.get_votervoice_address_query()
        if not all((isinstance(x[1], str) and x[1].strip()) for x in address_params.items()
                   if x[0] in client.REQUIRED_ADDRESS_FIELDS):
            logger.warning(
                "{} is missing one or more required address fields to validate with VoterVoice".format(
                    self.id
                )
            )
            return
        resp = client.validate_address(address_params)
        if not resp:
            # should be logged by client
            return
        if len(resp) > 1:
            logger.warning(
                "Multiple addresses returned by VoterVoice for {}; only using the first".format(self.id)
            )
        try:
            resp = resp[0]
            assert isinstance(resp, dict)
        except (TypeError, IndexError, AssertionError) as e:
            logger.error("Unable to process validated address: {}".format(e.__str__()))
            return

        # stupid iMIS null/empty strings...
        created = False
        geocode = CustomAddressGeocode.objects.filter(address_num=self.address_num).first()
        if geocode is None:
            geocode = CustomAddressGeocode(address_num=self.address_num)
            created = True

        geocode = self.handle_validated_address(resp, geocode, created)
        return geocode

    def handle_validated_address(self, resp, geocode, created):
        if resp.get('zipCodeExtension') and len(self.zip) <= 5 and '-' not in self.zip:
            self.zip = '{}-{}'.format(self.zip, resp['zipCodeExtension'])
            self.save()
        coordinates = resp.get('coordinates', {})
        try:
            longitude, latitude = validate_lon_lat(coordinates.get('longitude'), coordinates.get('latitude'))
        except ValidationError as e:
            logger.error(e.__str__())
            longitude, latitude = 0, 0
        geocode.longitude = longitude
        geocode.latitude = latitude
        geocode.weak_coordinates = coordinates.get('isWeakCoordinates', False)
        geocode.votervoice_checksum = resp.get('checksum', '')
        if created:
            geocode.us_congress = ''
            geocode.state_senate = ''
            geocode.state_house = ''
            geocode.id = self.id
        geocode.changed = False
        geocode.save()
        return geocode


class CustomDegree(models.Model):
    id = models.CharField(db_column='ID', max_length=10)  # Field name made lowercase.
    seqn = models.IntegerField(db_column='SEQN', primary_key=True)  # Field name made lowercase.
    school_id = models.CharField(db_column='SCHOOL_ID', max_length=10, default=0)  # Field name made lowercase.
    school_other = models.CharField(db_column='SCHOOL_OTHER', max_length=255)  # Field name made lowercase.
    degree_level = models.CharField(db_column='DEGREE_LEVEL', max_length=10)  # Field name made lowercase.
    degree_program = models.CharField(db_column='DEGREE_PROGRAM', max_length=255, default="")  # Field name made lowercase.
    degree_date = models.DateTimeField(db_column='DEGREE_DATE', blank=True, null=True)  # Field name made lowercase.
    degree_planning = models.BooleanField(db_column='DEGREE_PLANNING', default=False)  # Field name made lowercase.
    degree_complete = models.BooleanField(db_column='DEGREE_COMPLETE', default=False)  # Field name made lowercase.
    school_student_id = models.CharField(db_column='SCHOOL_STUDENT_ID', max_length=255, default="")  # Field name made lowercase.
    is_current = models.BooleanField(db_column="IS_CURRENT", default=False)
    school_seqn = models.IntegerField(db_column="SCHOOL_SEQN", default=0)
    degree_level_other = models.CharField(db_column="DEGREE_LEVEL_OTHER", max_length=50, default="")
    accredited_program = models.CharField(db_column='ACCREDITED_PROGRAM', max_length=255)  # Field name made lowercase.

    # all_schools = models.CharField(db_column='ALL_SCHOOLS', max_length=255)  # Field name made lowercase.
    # accred_schools = models.CharField(db_column='ACCRED_SCHOOLS', max_length=255)  # Field name made lowercase.
    # major = models.CharField(db_column='MAJOR', max_length=10)  # Field name made lowercase.

    def save(self, *args, **kwargs):

        if not self.pk:
            self.pk = Counter.create_id('Custom_Degree')

        # imis saves in UTC time - add timezone so it does not automatically convert
        if self.degree_date:
            self.degree_date = datetime.datetime(year=self.degree_date.year, month=self.degree_date.month, day=1, tzinfo=pytz.utc)
        super(CustomDegree, self).save(*args, **kwargs)


    def create_activity(self, *args, **kwargs):
        """
        Creates an activity record for the user in join/renew. Used for Student Metrics.
        """

        data_dict = self.activity_dict(*args, **kwargs)
        activity_degree = Activity.objects.create(**data_dict)

        return activity_degree

    def activity_dict(self, *args, **kwargs):
        """
        Returns dict format for creating an Activity record
        """

        name = kwargs.get("name")
        activity_type = kwargs.get("activity_type") # STU_RENEW, NM_RENEW, MEM_RENEW, STU_CHAPT, NM_CHAPT, MEM_CHAPT, STU_DIV, NM_DIV, or MEM_DIV
        previously_student = kwargs.get("previously_student", False) # used for NM and MEM - was this user previously a student? if student join date YES

        program_year = kwargs.get("program_year")
        school_name = "OTHER"

        if self.school_id and self.school_id != 0:
            try:
                school_name = Name.objects.get(id=self.school_id).company
            except Exception as e:
                pass

        data_dict = {
        "id":self.id,
        "member_type": name.member_type,
        "activity_type":activity_type,
        "action_codes":"ADD",
        "other_id":self.school_id if self.school_id != "" else "OTHER",
        "other_code": "STU" if previously_student else "",
        "uf_1": school_name,
        "uf_2": self.degree_level,
        "uf_3": self.degree_program if self.school_seqn or self.degree_program in DEGREE_TYPES else "Untracked Program",
        "uf_4": program_year,
        "uf_5": self.school_seqn,
        "description": "Student's affiliated school during join/renew.",
        }

        return data_dict

    class Meta:
        managed = False
        db_table = 'Custom_Degree'
        unique_together = (('id', 'seqn'),)


class CustomEventRegistration(models.Model):
    id = models.CharField(db_column='ID', primary_key=True, max_length=10)
    seqn = models.IntegerField(db_column='SEQN', primary_key=True, default=0)
    meeting = models.CharField(db_column='MEETING', max_length=10)
    address1 = models.CharField(db_column='ADDRESS_1', max_length=40, default='')
    address2 = models.CharField(db_column='ADDRESS_2', max_length=40, default='')
    city = models.CharField(db_column='CITY', max_length=40, default='')
    state = models.CharField(db_column='STATE_PROVINCE', max_length=15, default='')
    zip_code = models.CharField(db_column='ZIP', max_length=10, default='')
    country = models.CharField(db_column='COUNTRY', max_length=25, default='')
    badge_name = models.CharField(db_column='BADGE_NAME', max_length=20)
    badge_company = models.CharField(db_column='BADGE_COMPANY', max_length=80, default='')
    badge_location = models.CharField(db_column='BADGE_LOCATION', max_length=60)

    def save(self, *args, **kwargs):
        self.delete_related()

        try:
            return self.save_reusing_seqn(*args, **kwargs)
        except IntegrityError:
            return self.save_with_latest_seqn(*args, **kwargs)

    def save_reusing_seqn(self, *args, **kwargs):
        if self.seqn == 0:
            self.seqn = Counter.create_id('Custom_Event_Registration')
        return super().save(*args, **kwargs)

    def save_with_latest_seqn(self, *args, **kwargs):
        self.seqn = Counter.create_id('Custom_Event_Registration')
        return super().save(*args, **kwargs)

    def delete_related(self):
        with transaction.atomic():
            registrations = CustomEventRegistration.objects.filter(
                    id=self.id,
                    meeting=self.meeting)

            for registration in registrations:
                self.seqn = registration.seqn
                registration.delete()



    @classmethod
    def sync_registration(cls, user_id, event_code):
        """
        Syncs registration info from a user's event registration to OrderBadge and Custom_Event_Schedule.
        """

        query = """
         EXEC APA_IMIS_Events_Custom_Table_Sync @WebUserID=?, @ConferenceCode=?
        """

        DbAccessor().execute(query, [user_id, event_code])

    class Meta:
        managed = False
        db_table = 'Custom_Event_Registration'


class CustomEventScheduleManager(models.Manager):
    def create_schedule_entry(self, attributes):

        custom_event_schedule_seqn = Counter.create_id('Custom_Event_Schedule')
        attributes = {**attributes, **{'seqn': custom_event_schedule_seqn}}
        schedule_entry = self.create(**attributes)

        return schedule_entry


class CustomEventSchedule(models.Model):
    id = models.CharField(db_column='ID', primary_key=True, max_length=10)
    seqn = models.IntegerField(db_column='SEQN')
    meeting = models.CharField(db_column='MEETING', max_length=10)
    registrant_class = models.CharField(db_column='REGISTRANT_CLASS', max_length=10)
    product_code = models.CharField(db_column='PRODUCT_CODE', max_length=31)
    status = models.CharField(db_column='STATUS', max_length=5)
    unit_price = models.DecimalField(db_column='UNIT_PRICE', decimal_places=2, max_digits=8)

    objects = CustomEventScheduleManager()

    def update_status(self, status):
        query = """
         UPDATE Custom_Event_Schedule
         SET STATUS=?
         WHERE ID=? AND SEQN=?
        """
        DbAccessor().execute(query, [status, self.id, self.seqn])

    class Meta:
        managed = False
        db_table = 'Custom_Event_Schedule'


class CustomSchoolaccredited(models.Model):
    id = models.CharField(db_column='ID', max_length=10)  # Field name made lowercase.
    seqn = models.IntegerField(db_column='SEQN', primary_key=True)  # Field name made lowercase.
    start_date = models.DateTimeField(db_column='START_DATE', blank=True, null=True)  # Field name made lowercase.
    end_date = models.DateTimeField(db_column='END_DATE', blank=True, null=True)  # Field name made lowercase.
    degree_level = models.CharField(db_column='DEGREE_LEVEL', max_length=60)  # Field name made lowercase.
    school_program_type = models.CharField(db_column='SCHOOL_PROGRAM_TYPE', max_length=20)  # Field name made lowercase.
    degree_program = models.CharField(db_column='DEGREE_PROGRAM', max_length=255)  # Field name made lowercase.

    @property
    def degree_level_name(self):
        return next((dl[1] for dl in DEGREE_LEVELS if dl[0] == self.degree_level), "")

    @classmethod
    def get_all_schools(cls, school_program_types=["PAB","ACSP",""]):
        accredited_programs = cls.objects.filter(school_program_type__in=school_program_types).values_list("id", flat=True).distinct()
        accredited_schools = Name.objects.filter(id__in=accredited_programs).values("id", "company")
        return [(a["id"], a["company"]) for a in sorted(accredited_schools, key=lambda s: s.get("company"))]

    @classmethod
    def get_current_schools(cls):
        now = timezone.now()
        accredited_programs = cls.objects.exclude(
            #school_program_type="",
            end_date__lt=now # some current schools may not have end dates
        ).filter(
            start_date__lte=now,
        ).values_list("id", flat=True).distinct()

        accredited_schools = Name.objects.filter(id__in=accredited_programs).values("id", "company")

        return [(a["id"], a["company"]) for a in sorted(accredited_schools, key=lambda s: s.get("company"))]

    @classmethod
    def get_all_degree_programs(cls, school_id, school_program_types=["PAB","ACSP"]):
        degree_programs = CustomSchoolaccredited.objects.exclude(
            school_program_type=""
        ).filter(
            id=school_id,
            school_program_type__in=school_program_types
        ).only("seqn", "degree_program", "degree_level")
        return [(dp.seqn, "{program}, ({level})".format(program=dp.degree_program, level=dp.degree_level_name) ) for dp in degree_programs]

    @classmethod
    def get_current_degree_programs(cls, school_id):
        now = timezone.now()
        degree_programs = CustomSchoolaccredited.objects.exclude(
            end_date__lt=now # some current schools may not have end dates
        ).filter(
            id=school_id,
            start_date__lte=now,
        ).only("seqn", "degree_program", "degree_level", "school_program_type")
        degree_programs = remove_degree_program_dupes(degree_programs)
        return [(dp.seqn, "{program}, ({level})".format(program=dp.degree_program, level=dp.degree_level_name) ) for dp in degree_programs]

    @classmethod
    def is_valid_program_date(cls, seqn, check_date):
        """ check_date is a date (not a datetime) """
        today = datetime.date.today()
        check_date_past_or_now = min(check_date, today) # assume that currently accredited programs are indefinitely accredited
        return cls.objects.exclude(
            end_date__lt=check_date_past_or_now
        ).filter(
            seqn=seqn,
            start_date__lte=check_date_past_or_now
        ).exists()

    def __str__(self):
        school = Name.objects.filter(id=self.id).first()
        return school.company + " | " + self.degree_level_name + " | " + self.degree_program

    class Meta:
        managed = False
        db_table = 'Custom_SchoolAccredited'
        unique_together = (('id', 'seqn'),)


class CustomSchoolaccreditedPostUpgrade(models.Model):
    # id should match Django School.user.username..must also match degree_level to Django AppDegree.level
    id = models.CharField(db_column='ID', max_length=10)  # Field name made lowercase.
    seqn = models.IntegerField(db_column='SEQN', primary_key=True)  # Field name made lowercase.
    start_date = models.DateTimeField(db_column='START_DATE', blank=True, null=True)  # Field name made lowercase.
    end_date = models.DateTimeField(db_column='END_DATE', blank=True, null=True)  # Field name made lowercase.
    degree_level = models.CharField(db_column='DEGREE_LEVEL', max_length=60)  # Field name made lowercase.
    school_program_type = models.CharField(db_column='SCHOOL_PROGRAM_TYPE', max_length=20)  # Field name made lowercase.
    degree_program = models.CharField(db_column='DEGREE_PROGRAM', max_length=255)  # Field name made lowercase.
    old_seqn  = models.IntegerField(db_column='OLD_SEQN')

    @classmethod
    def seqn_update(self, degrees=None):
        if not degrees:
            # to run for real pass in each of below querysets running in shell
            from exam.models import ApplicationDegree
            from myapa.models.educational_degree import EducationalDegree
            degrees = ApplicationDegree.objects.filter(school_seqn__isnull=False)[1000:1010]
            # degrees = EducationalDegree.objects.filter(school_seqn__isnull=False)[1000:1010]
        foo = set()
        for ad in degrees:
            print("App Degree is ", ad)
            print("App degree school_seqn is ", ad.school_seqn)
            csa = CustomSchoolaccreditedPostUpgrade.objects.filter(old_seqn=ad.school_seqn).first()
            print("Custom school accred is ", csa)
            if csa and (csa.id == ad.school.user.username):
                print("matched csa.id to ad.user_id")
                if csa.degree_level == ad.level:
                    print("matched degree levels")
                    print("before ad.school_seqn is ", ad.school_seqn)
                    ad.school_seqn = csa.seqn
                    print("after ad.school_seqn is ", ad.school_seqn)
                    ad.save()
            elif not csa:
                foo.add(ad.school_seqn)
                ad.school_seqn = None
                print("ad. school se is ", ad.school_seqn)
                ad.save()
        print("set of all Django degrees that don't pull a degree program in imis: ")
        print(foo)

    class Meta:
        managed = False
        db_table = 'Custom_SchoolAccredited_PostUpgrade'
        unique_together = (('id', 'seqn'),)


class IndDemographics(models.Model):
    id = models.CharField(db_column='ID', primary_key=True, max_length=10)  # Field name made lowercase.
    apa_life_date = models.DateTimeField(db_column='APA_LIFE_DATE', blank=True, null=True)  # Field name made lowercase.
    aicp_life_member = models.BooleanField(db_column='AICP_LIFE_MEMBER')  # Field name made lowercase.
    aicp_life_date = models.DateTimeField(db_column='AICP_LIFE_DATE', blank=True, null=True)  # Field name made lowercase.
    faculty_position = models.CharField(db_column='FACULTY_POSITION', max_length=5)  # Field name made lowercase.
    admin_position = models.CharField(db_column='ADMIN_POSITION', max_length=5)  # Field name made lowercase.
    salary_range = models.CharField(db_column='SALARY_RANGE', max_length=5)  # Field name made lowercase.
    promotion_codes = models.CharField(db_column='PROMOTION_CODES', max_length=60)  # Field name made lowercase.
    date_of_birth = models.DateTimeField(db_column='DATE_OF_BIRTH', blank=True, null=True)  # Field name made lowercase.
    sub_specialty = models.CharField(db_column='SUB_SPECIALTY', max_length=6)  # Field name made lowercase.
    usa_citizen = models.BooleanField(db_column='USA_CITIZEN')  # Field name made lowercase.
    aicp_start = models.DateTimeField(db_column='AICP_START', blank=True, null=True)  # Field name made lowercase.
    faicp_start = models.DateTimeField(db_column='FAICP_START', blank=True, null=True)  # Field name made lowercase.
    aicp_cert_no = models.CharField(db_column='AICP_CERT_NO', max_length=10)  # Field name made lowercase.
    perpetuity = models.BooleanField(db_column='PERPETUITY')  # Field name made lowercase.
    aicp_promo_1 = models.CharField(db_column='AICP_PROMO_1', max_length=20)  # Field name made lowercase.
    hint_password = models.CharField(db_column='HINT_PASSWORD', max_length=4)  # Field name made lowercase.
    hint_answer = models.CharField(db_column='HINT_ANSWER', max_length=60)  # Field name made lowercase.
    country_codes = models.CharField(db_column='COUNTRY_CODES', max_length=5)  # Field name made lowercase.
    specialty = models.CharField(db_column='SPECIALTY', max_length=50)  # Field name made lowercase.
    apa_life_member = models.BooleanField(db_column='APA_LIFE_MEMBER')  # Field name made lowercase.
    conf_code = models.CharField(db_column='CONF_CODE', max_length=4)  # Field name made lowercase.
    mentor_signup = models.BooleanField(db_column='MENTOR_SIGNUP')  # Field name made lowercase.
    department = models.CharField(db_column='DEPARTMENT', max_length=50)  # Field name made lowercase.
    conv_np = models.BooleanField(db_column='CONV_NP')  # Field name made lowercase.
    invoice_num = models.CharField(db_column='INVOICE_NUM', max_length=30)  # Field name made lowercase.
    prev_mt = models.CharField(db_column='PREV_MT', max_length=10)  # Field name made lowercase.
    conv_freestu = models.BooleanField(db_column='CONV_FREESTU')  # Field name made lowercase.
    conv_stu = models.BooleanField(db_column='CONV_STU')  # Field name made lowercase.
    chapt_only = models.BooleanField(db_column='CHAPT_ONLY')  # Field name made lowercase.
    asla = models.BooleanField(db_column='ASLA')  # Field name made lowercase.
    salary_verifydate = models.DateTimeField(db_column='SALARY_VERIFYDATE', blank=True, null=True)  # Field name made lowercase.
    functional_title_verifydate = models.DateTimeField(db_column='FUNCTIONAL_TITLE_VERIFYDATE', blank=True, null=True)  # Field name made lowercase.
    previous_aicp_cert_no = models.CharField(db_column='PREVIOUS_AICP_CERT_NO', max_length=10)  # Field name made lowercase.
    previous_aicp_start = models.DateTimeField(db_column='PREVIOUS_AICP_START', blank=True, null=True)  # Field name made lowercase.
    email_secondary = models.CharField(db_column='EMAIL_SECONDARY', max_length=100)  # Field name made lowercase.
    new_member_start_date = models.DateTimeField(db_column='NEW_MEMBER_START_DATE', blank=True, null=True)  # Field name made lowercase.
    conv_ecp5 = models.BooleanField(db_column='CONV_ECP5')  # Field name made lowercase.
    exclude_from_drop = models.BooleanField(db_column='EXCLUDE_FROM_DROP')  # Field name made lowercase.
    student_start_date = models.DateTimeField(db_column='STUDENT_START_DATE', blank=True, null=True)  # Field name made lowercase.
    is_current_student = models.BooleanField(db_column='IS_CURRENT_STUDENT', default=0)  # Field name made lowercase.
    join_type = models.CharField(db_column='JOIN_TYPE', max_length=25, default="")
    join_source = models.CharField(db_column='JOIN_SOURCE', max_length=25, default="")
    gender = models.CharField(db_column='GENDER', blank=True, null=True, max_length=5)
    gender_other = models.CharField(db_column='GENDER_OTHER', blank=True, null=True, max_length=25)

    class Meta:
        managed = False
        db_table = 'Ind_Demographics'

    def update_student_new_member_demographics(self):
        """
        update demographics based on student or new member purchase
        """
        current_date_utc = datetime.datetime(year=datetime.datetime.now().year,
                                             month=datetime.datetime.now().month,
                                             day=datetime.datetime.now().day, tzinfo=pytz.utc)
        if self.salary_range == "K":
            self.is_current_student = 1

            if not self.student_start_date:
                self.student_start_date = current_date_utc
        else:
            self.is_current_student = 0

            # update new member start date only if it does not exist
            if not self.new_member_start_date:
                self.new_member_start_date = current_date_utc

        self.save()

class Activity(models.Model):

    seqn = models.IntegerField(db_column='SEQN', primary_key=True)  # Field name made lowercase.
    id = models.CharField(db_column='ID', max_length=10)  # Field name made lowercase.
    activity_type = models.CharField(db_column='ACTIVITY_TYPE', max_length=10)  # Field name made lowercase.
    transaction_date = models.DateTimeField(db_column='TRANSACTION_DATE', blank=True, null=True)  # Field name made lowercase.
    effective_date = models.DateTimeField(db_column='EFFECTIVE_DATE', blank=True, null=True)  # Field name made lowercase.
    product_code = models.CharField(db_column='PRODUCT_CODE', max_length=31, default="")  # Field name made lowercase.
    other_code = models.CharField(db_column='OTHER_CODE', max_length=30, default="")  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=255, default="")  # Field name made lowercase.
    source_system = models.CharField(db_column='SOURCE_SYSTEM', max_length=10, default="DJANGO")  # Field name made lowercase.
    source_code = models.CharField(db_column='SOURCE_CODE', max_length=40, blank=True, null=True)  # Field name made lowercase.
    quantity = models.DecimalField(db_column='QUANTITY', max_digits=15, decimal_places=2, default=0)  # Field name made lowercase.
    amount = models.DecimalField(db_column='AMOUNT', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    category = models.CharField(db_column='CATEGORY', max_length=15)  # Field name made lowercase.
    units = models.DecimalField(db_column='UNITS', max_digits=15, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    thru_date = models.DateTimeField(db_column='THRU_DATE', blank=True, null=True)  # Field name made lowercase.
    member_type = models.CharField(db_column='MEMBER_TYPE', max_length=5, default="")  # Field name made lowercase.
    action_codes = models.CharField(db_column='ACTION_CODES', max_length=255, default="")  # Field name made lowercase.
    pay_method = models.CharField(db_column='PAY_METHOD', max_length=50, default="")  # Field name made lowercase.
    tickler_date = models.DateTimeField(db_column='TICKLER_DATE', blank=True, null=True)  # Field name made lowercase.
    note = models.TextField(db_column='NOTE', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    note_2 = models.TextField(db_column='NOTE_2', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    batch_num = models.CharField(db_column='BATCH_NUM', max_length=15, default="")  # Field name made lowercase.
    co_id = models.CharField(db_column='CO_ID', max_length=10, default="")  # Field name made lowercase.
    object = models.BinaryField(db_column='OBJECT', blank=True, null=True)  # Field name made lowercase.
    intent_to_edit = models.CharField(db_column='INTENT_TO_EDIT', max_length=80, default="")  # Field name made lowercase.
    uf_1 = models.CharField(db_column='UF_1', max_length=255, default="")  # Field name made lowercase.
    uf_2 = models.CharField(db_column='UF_2', max_length=255, default="")  # Field name made lowercase.
    uf_3 = models.CharField(db_column='UF_3', max_length=255, default="")  # Field name made lowercase.
    uf_4 = models.DecimalField(db_column='UF_4', max_digits=15, decimal_places=4, default=0)  # Field name made lowercase.
    uf_5 = models.DecimalField(db_column='UF_5', max_digits=15, decimal_places=4, default=0)  # Field name made lowercase.
    uf_6 = models.DateTimeField(db_column='UF_6', blank=True, null=True)  # Field name made lowercase.
    uf_7 = models.DateTimeField(db_column='UF_7', blank=True, null=True)  # Field name made lowercase.
    originating_trans_num = models.IntegerField(db_column='ORIGINATING_TRANS_NUM', default=0)  # Field name made lowercase.
    org_code = models.CharField(db_column='ORG_CODE', max_length=5, default="")  # Field name made lowercase.
    campaign_code = models.CharField(db_column='CAMPAIGN_CODE', max_length=10, default="")  # Field name made lowercase.
    other_id = models.CharField(db_column='OTHER_ID', max_length=10, default="")  # Field name made lowercase.
    solicitor_id = models.CharField(db_column='SOLICITOR_ID', max_length=10, default="")  # Field name made lowercase.
    taxable_value = models.DecimalField(db_column='TAXABLE_VALUE', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    attach_seqn = models.IntegerField(db_column='ATTACH_SEQN', default=0)  # Field name made lowercase.
    attach_total = models.IntegerField(db_column='ATTACH_TOTAL', default=0)  # Field name made lowercase.
    recurring_request = models.BooleanField(db_column='RECURRING_REQUEST', default=0)  # Field name made lowercase.
    status_code = models.CharField(db_column='STATUS_CODE', max_length=1, blank=True, null=True)  # Field name made lowercase.
    next_install_date = models.DateTimeField(db_column='NEXT_INSTALL_DATE', blank=True, null=True)  # Field name made lowercase.
    grace_period = models.IntegerField(db_column='GRACE_PERIOD', blank=True, null=True)  # Field name made lowercase.
    mem_trib_code = models.CharField(db_column='MEM_TRIB_CODE', max_length=10, default="")  # Field name made lowercase.

    def save(self, *args, **kwargs):

        if not self.pk:
            self.pk = Counter.create_id('Activity')

        # imis saves in UTC time - add timezone so it does not automatically convert
        transaction_date = datetime.datetime(year=datetime.datetime.now().year, month=datetime.datetime.now().month, day=datetime.datetime.now().day, tzinfo=pytz.utc)

        if not self.transaction_date:
            self.transaction_date = transaction_date
        if not self.effective_date:
            self.effective_date = transaction_date

        super(Activity, self).save(*args, **kwargs)

    @classmethod
    def get_activity_type(*args, **kwargs):
        """
        builds and returns an activity type based on kwargs passed. Currently only used for student and new member metrics.
        activity type format: XX_YY
        XX = Member type or category
        YY = Subscription or group
        """

        activity_type = ""
        program_type = kwargs.get("program_type", "students_new_members")
        name = kwargs.get("name")

        if program_type == "student_new_members":
            record_type = kwargs.get("record_type")
            activity_type = name.member_type

            if name.category in ('NM1', 'NM2'):
                activity_type = 'NM'

            activity_type += "_" + record_type

        return activity_type

    class Meta:
        managed = False
        db_table = 'Activity'


class Subscriptions(models.Model):
    id = models.CharField(db_column='ID', max_length=10, primary_key=True)  # Field name made lowercase.
    product_code = models.CharField(db_column='PRODUCT_CODE', max_length=31)  # Field name made lowercase.
    bt_id = models.CharField(db_column='BT_ID', max_length=10)  # Field name made lowercase.
    prod_type = models.CharField(db_column='PROD_TYPE', max_length=10)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=5)  # Field name made lowercase.
    begin_date = models.DateTimeField(db_column='BEGIN_DATE', blank=True, null=True)  # Field name made lowercase.
    paid_thru = models.DateTimeField(db_column='PAID_THRU', blank=True, null=True)  # Field name made lowercase.
    copies = models.IntegerField(db_column='COPIES')  # Field name made lowercase.
    source_code = models.CharField(db_column='SOURCE_CODE', max_length=40)  # Field name made lowercase.
    first_subscribed = models.DateTimeField(db_column='FIRST_SUBSCRIBED', blank=True, null=True)  # Field name made lowercase.
    continuous_since = models.DateTimeField(db_column='CONTINUOUS_SINCE', blank=True, null=True)  # Field name made lowercase.
    prior_years = models.IntegerField(db_column='PRIOR_YEARS')  # Field name made lowercase.
    future_copies = models.IntegerField(db_column='FUTURE_COPIES')  # Field name made lowercase.
    future_copies_date = models.DateTimeField(db_column='FUTURE_COPIES_DATE', blank=True, null=True)  # Field name made lowercase.
    pref_mail = models.IntegerField(db_column='PREF_MAIL')  # Field name made lowercase.
    pref_bill = models.IntegerField(db_column='PREF_BILL')  # Field name made lowercase.
    renew_months = models.SmallIntegerField(db_column='RENEW_MONTHS')  # Field name made lowercase.
    mail_code = models.CharField(db_column='MAIL_CODE', max_length=5)  # Field name made lowercase.
    previous_balance = models.DecimalField(db_column='PREVIOUS_BALANCE', max_digits=19, decimal_places=4)  # Field name made lowercase.
    bill_date = models.DateTimeField(db_column='BILL_DATE', blank=True, null=True)  # Field name made lowercase.
    reminder_date = models.DateTimeField(db_column='REMINDER_DATE', blank=True, null=True)  # Field name made lowercase.
    reminder_count = models.SmallIntegerField(db_column='REMINDER_COUNT')  # Field name made lowercase.
    bill_begin = models.DateTimeField(db_column='BILL_BEGIN', blank=True, null=True)  # Field name made lowercase.
    bill_thru = models.DateTimeField(db_column='BILL_THRU', blank=True, null=True)  # Field name made lowercase.
    bill_amount = models.DecimalField(db_column='BILL_AMOUNT', max_digits=19, decimal_places=4)  # Field name made lowercase.
    bill_copies = models.IntegerField(db_column='BILL_COPIES')  # Field name made lowercase.
    payment_amount = models.DecimalField(db_column='PAYMENT_AMOUNT', max_digits=19, decimal_places=4)  # Field name made lowercase.
    payment_date = models.DateTimeField(db_column='PAYMENT_DATE', blank=True, null=True)  # Field name made lowercase.
    paid_begin = models.DateTimeField(db_column='PAID_BEGIN', blank=True, null=True)  # Field name made lowercase.
    last_paid_thru = models.DateTimeField(db_column='LAST_PAID_THRU', blank=True, null=True)  # Field name made lowercase.
    copies_paid = models.IntegerField(db_column='COPIES_PAID')  # Field name made lowercase.
    adjustment_amount = models.DecimalField(db_column='ADJUSTMENT_AMOUNT', max_digits=19, decimal_places=4)  # Field name made lowercase.
    ltd_payments = models.DecimalField(db_column='LTD_PAYMENTS', max_digits=19, decimal_places=4)  # Field name made lowercase.
    issues_printed = models.CharField(db_column='ISSUES_PRINTED', max_length=255)  # Field name made lowercase.
    balance = models.DecimalField(db_column='BALANCE', max_digits=19, decimal_places=4)  # Field name made lowercase.
    cancel_reason = models.CharField(db_column='CANCEL_REASON', max_length=10)  # Field name made lowercase.
    years_active_string = models.CharField(db_column='YEARS_ACTIVE_STRING', max_length=100)  # Field name made lowercase.
    last_issue = models.CharField(db_column='LAST_ISSUE', max_length=15)  # Field name made lowercase.
    last_issue_date = models.DateTimeField(db_column='LAST_ISSUE_DATE', blank=True, null=True)  # Field name made lowercase.
    date_added = models.DateTimeField(db_column='DATE_ADDED', blank=True, null=True)  # Field name made lowercase.
    last_updated = models.DateTimeField(db_column='LAST_UPDATED', blank=True, null=True)  # Field name made lowercase.
    updated_by = models.CharField(db_column='UPDATED_BY', max_length=60)  # Field name made lowercase.
    intent_to_edit = models.CharField(db_column='INTENT_TO_EDIT', max_length=80)  # Field name made lowercase.
    flag = models.CharField(db_column='FLAG', max_length=5)  # Field name made lowercase.
    bill_type = models.CharField(db_column='BILL_TYPE', max_length=1)  # Field name made lowercase.
    complimentary = models.BooleanField(db_column='COMPLIMENTARY')  # Field name made lowercase.
    future_credits = models.DecimalField(db_column='FUTURE_CREDITS', max_digits=19, decimal_places=4)  # Field name made lowercase.
    invoice_reference_num = models.IntegerField(db_column='INVOICE_REFERENCE_NUM')  # Field name made lowercase.
    invoice_line_num = models.IntegerField(db_column='INVOICE_LINE_NUM')  # Field name made lowercase.
    campaign_code = models.CharField(db_column='CAMPAIGN_CODE', max_length=10)  # Field name made lowercase.
    appeal_code = models.CharField(db_column='APPEAL_CODE', max_length=40)  # Field name made lowercase.
    org_code = models.CharField(db_column='ORG_CODE', max_length=5)  # Field name made lowercase.
    is_fr_item = models.BooleanField(db_column='IS_FR_ITEM')  # Field name made lowercase.
    fair_market_value = models.DecimalField(db_column='FAIR_MARKET_VALUE', max_digits=15, decimal_places=2)  # Field name made lowercase.
    is_group_admin = models.BooleanField(db_column='IS_GROUP_ADMIN')  # Field name made lowercase.

    def create_activity(self, *args, **kwargs):
        """
        Creates an activity record for the user in join/renew. Used for Student Metrics.
        """

        data_dict = self.activity_dict(*args, **kwargs)
        subscription_activity = Activity.objects.create(**data_dict)

        return subscription_activity

    def activity_dict(self, *args, **kwargs):
        """
        Returns dict format for creating an archive Activity record for the Student and New Member program.
        """

        # either the student_join_date or nm_join_date
        name = kwargs.get("name") # STU, MEM
        activity_type = kwargs.get("activity_type") # STU_RENEW, NM_RENEW, MEM_RENEW, STU_CHAPT, NM_CHAPT, MEM_CHAPT, STU_DIV, NM_DIV, or MEM_DIV
        previously_student = kwargs.get("previously_student", False) # used for NM and MEM - was this user previously a student? if student join date YES
        program_year = kwargs.get("program_year")

        data_dict = {
        "id":self.id,
        "member_type": name.member_type,
        "activity_type": activity_type,
        "action_codes":"ADD",
        "other_code": "STU" if previously_student else "",
        "product_code": self.product_code,
        "thru_date": self.paid_thru,
        "uf_4": program_year,
        "description": "Student subscription in join/renew",
        }

        return data_dict

    def json_response(self):
        """
        A JSON-encodeable dict to replace the Node Restify API
        :return: dict
        """
        return {
            'webuserid': self.bt_id,
            'product_code': self.product_code,
            'prod_type': self.prod_type,
            'status': self.status,
            'begin_date': self.begin_date.strftime(
                '%Y-%m-%dT%H:%M:%S.000Z'
            ),
            'paid_thru': self.paid_thru.strftime(
                '%Y-%m-%dT%H:%M:%S.000Z'
            ),
            'copies': self.copies,
            'bill_begin': self.bill_begin.strftime(
                '%Y-%m-%dT%H:%M:%S.000Z'
            ),
            'bill_thru': self.bill_thru.strftime(
                '%Y-%m-%dT%H:%M:%S.000Z'
            ),
            'bill_amount': round(float(self.bill_amount), 2),
            'bill_copies': self.bill_copies,
            'copies_paid': self.copies_paid,
            'balance': round(float(self.balance), 2)
        }

    @classmethod
    def aicp_drop(cls, user_id, period_code):

        query = """
         EXEC APA_IMIS_AICP_CM_Log_Drop @WebUserID = ?, @PeriodCode = ?
        """
        DbAccessor().execute(query, [user_id, period_code])

        return None

    class Meta:
        managed = False
        db_table = 'Subscriptions'
        unique_together = (('id', 'product_code'),)


class Counter(models.Model):
    counter_name = models.CharField(db_column='COUNTER_NAME', primary_key=True, max_length=30)  # Field name made lowercase.
    last_value = models.IntegerField(db_column='LAST_VALUE')  # Field name made lowercase.
    last_updated = models.DateTimeField(db_column='LAST_UPDATED', blank=True, null=True)  # Field name made lowercase.
    updated_by = models.CharField(db_column='UPDATED_BY', max_length=255)  # Field name made lowercase.
    pagepad1 = models.CharField(db_column='PAGEPAD1', max_length=255)  # Field name made lowercase.
    pagepad2 = models.CharField(db_column='PAGEPAD2', max_length=255)  # Field name made lowercase.
    pagepad3 = models.CharField(db_column='PAGEPAD3', max_length=255)  # Field name made lowercase.
    pagepad4 = models.CharField(db_column='PAGEPAD4', max_length=255)  # Field name made lowercase.
    has_checksum = models.BooleanField(db_column='HAS_CHECKSUM')  # Field name made lowercase.

    @classmethod
    def create_id(cls, counter_name):
        """
        returns a unique ID for the passed in counter_name
        """

        query = """
                EXEC  [sp_asi_GetCounter] @counterName = ?;
                """

        return DbAccessor().get_value(query, [counter_name])

    class Meta:
        managed = False
        db_table = 'Counter'


class Advocacy(models.Model):
    id = models.CharField(db_column='ID', primary_key=True, max_length=10)  # Field name made lowercase.
    congressional_district = models.CharField(db_column='Congressional_District', max_length=5, default="")  # Field name made lowercase.
    st_house = models.CharField(db_column='St_House', max_length=5, default="")  # Field name made lowercase.
    st_senate = models.CharField(db_column='St_Senate', max_length=5, default="")  # Field name made lowercase.
    state_chair = models.BooleanField(db_column='State_Chair', default=False)  # Field name made lowercase.
    district_captain = models.BooleanField(db_column='District_Captain', default=False)  # Field name made lowercase.
    transportation = models.BooleanField(db_column='Transportation', default=False)  # Field name made lowercase.
    community_development = models.BooleanField(db_column='Community_Development', default=False)  # Field name made lowercase.
    federal_data = models.BooleanField(db_column='Federal_Data', default=False)  # Field name made lowercase.
    water = models.BooleanField(db_column='Water', default=False)  # Field name made lowercase.
    other = models.CharField(db_column='Other', max_length=255, default=False)  # Field name made lowercase.
    grassrootsmember = models.BooleanField(db_column='GrassRootsMember', default=False)  # Field name made lowercase.
    join_date = models.DateTimeField(db_column='Join_Date', blank=True, null=True)  # Field name made lowercase.

    def create_activity(self, *args, **kwargs):
        """
        Creates an activity record for the user in join/renew. Used for Student Metrics.
        """

        data_dict = self.activity_dict(*args, **kwargs)
        activity_grassroots = Activity.objects.create(**data_dict)

        return activity_grassroots

    def activity_dict(self, *args, **kwargs):
        """
        Returns dict format for creating an Activity record
        """

        name = kwargs.get("name")
        activity_type = kwargs.get("activity_type") # STU_RENEW, NM_RENEW, MEM_RENEW, STU_CHAPT, NM_CHAPT, MEM_CHAPT, STU_DIV, NM_DIV, or MEM_DIV
        previously_student = kwargs.get("previously_student", False) # used for NM and MEM - was this user previously a student? if student join date YES
        action_codes = kwargs.get("action_codes", "ADD")
        program_year = kwargs.get("program_year")


        data_dict = {
        "id":name.id,
        "member_type":name.member_type,
        "activity_type":activity_type,
        "other_code": "STU" if previously_student else "",
        "action_codes": action_codes,
        "uf_4": program_year,
        "description": "Member's PAN status during join/renew",

        }

        return data_dict

    def json_response(self):
        """
        A JSON-encodeable dict to replace the Node Restify API

        :return: dict
        """
        retval = self.__dict__
        retval.pop('_state')
        if retval['join_date'] is not None:
            retval['join_date'] = retval['join_date'].strftime('%Y-%m-%dT%H:%M:%S.000Z')
        return retval

    class Meta:
        managed = False
        db_table = 'Advocacy'


class RaceOrigin(models.Model):
    id = models.CharField(db_column='ID', primary_key=True, max_length=10)  # Field name made lowercase.
    race = models.CharField(db_column='RACE', max_length=60)  # Field name made lowercase.
    origin = models.CharField(db_column='ORIGIN', max_length=60)  # Field name made lowercase.
    span_hisp_latino = models.CharField(db_column='SPAN_HISP_LATINO', max_length=60)  # Field name made lowercase.
    ai_an = models.CharField(db_column='AI_AN', max_length=60)  # Field name made lowercase.
    asian_pacific = models.CharField(db_column='ASIAN_PACIFIC', max_length=60)  # Field name made lowercase.
    other = models.CharField(db_column='OTHER', max_length=60)  # Field name made lowercase.
    ethnicity_verifydate = models.DateTimeField(db_column='ETHNICITY_VERIFYDATE', blank=True, null=True)  # Field name made lowercase.
    origin_verifydate = models.DateTimeField(db_column='ORIGIN_VERIFYDATE', blank=True, null=True)  # Field name made lowercase.
    ethnicity_noanswer = models.BooleanField(db_column='ETHNICITY_NOANSWER')  # Field name made lowercase.
    origin_noanswer = models.BooleanField(db_column='ORIGIN_NOANSWER')  # Field name made lowercase.
    # time_stamp = models.TextField(db_column='TIME_STAMP', blank=True, null=True)  # Field name made lowercase. This field type is a guess.

    class Meta:
        managed = False
        db_table = 'Race_Origin'


class MailingDemographics(JSONResponseMixin, models.Model):
    id = models.CharField(db_column='ID', primary_key=True, max_length=10)  # Field name made lowercase.
    job_mart_bulk = models.BooleanField(db_column='JOB_MART_BULK')  # Field name made lowercase.
    job_mart_address = models.CharField(db_column='JOB_MART_ADDRESS', max_length=20)  # Field name made lowercase.
    excl_mail_list = models.BooleanField(db_column='EXCL_MAIL_LIST')  # Field name made lowercase.
    excl_website = models.BooleanField(db_column='EXCL_WEBSITE')  # Field name made lowercase.
    excl_interact = models.BooleanField(db_column='EXCL_INTERACT')  # Field name made lowercase.
    leadership_address = models.CharField(db_column='LEADERSHIP_ADDRESS', max_length=20)  # Field name made lowercase.
    roster_address = models.CharField(db_column='ROSTER_ADDRESS', max_length=20)  # Field name made lowercase.
    speaker_address = models.CharField(db_column='SPEAKER_ADDRESS', max_length=20)  # Field name made lowercase.
    excl_all = models.BooleanField(db_column='EXCL_ALL')  # Field name made lowercase.
    job_mart_invoice = models.CharField(db_column='JOB_MART_INVOICE', max_length=20)  # Field name made lowercase.
    excl_natlconf = models.BooleanField(db_column='EXCL_NATLCONF')  # Field name made lowercase.
    excl_otherconf = models.BooleanField(db_column='EXCL_OTHERCONF')  # Field name made lowercase.
    excl_japa = models.BooleanField(db_column='EXCL_JAPA')  # Field name made lowercase.
    excl_zp = models.BooleanField(db_column='EXCL_ZP')  # Field name made lowercase.
    excl_pas = models.BooleanField(db_column='EXCL_PAS')  # Field name made lowercase.
    excl_commissioner = models.BooleanField(db_column='EXCL_COMMISSIONER')  # Field name made lowercase.
    excl_planning_print = models.BooleanField(db_column='EXCL_PLANNING_PRINT')  # Field name made lowercase.
    excl_pac = models.BooleanField(db_column="EXCL_PAC")
    excl_pan = models.BooleanField(db_column="EXCL_PAN")
    excl_foundation = models.BooleanField(db_column="EXCL_FOUNDATION")
    excl_learn = models.BooleanField(db_column="EXCL_LEARN")
    excl_planning_home = models.BooleanField(db_column="EXCL_PLANNING_HOME")
    excl_survey = models.BooleanField(db_column="EXCL_SURVEY")
    excl_planning = models.BooleanField(db_column="EXCL_PLANNING")

    class Meta:
        managed = False
        db_table = 'Mailing_Demographics'


class Product(models.Model):
    product_code = models.CharField(db_column='PRODUCT_CODE', primary_key=True, max_length=31)  # Field name made lowercase.
    product_major = models.CharField(db_column='PRODUCT_MAJOR', max_length=15, default='')  # Field name made lowercase.
    product_minor = models.CharField(db_column='PRODUCT_MINOR', max_length=15, default='')  # Field name made lowercase.
    prod_type = models.CharField(db_column='PROD_TYPE', max_length=10, default='')  # Field name made lowercase.
    category = models.CharField(db_column='CATEGORY', max_length=10, default='')  # Field name made lowercase.
    title_key = models.CharField(db_column='TITLE_KEY', max_length=60, default='')  # Field name made lowercase.
    title = models.CharField(db_column='TITLE', max_length=60, default='')  # Field name made lowercase.
    description = models.TextField(db_column='DESCRIPTION', default='')  # Field name made lowercase. This field type is a guess.
    status = models.CharField(db_column='STATUS', max_length=1, default='')  # Field name made lowercase.
    note = models.TextField(db_column='NOTE', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    group_1 = models.CharField(db_column='GROUP_1', max_length=31, default='')  # Field name made lowercase.
    group_2 = models.CharField(db_column='GROUP_2', max_length=31, default='')  # Field name made lowercase.
    group_3 = models.CharField(db_column='GROUP_3', max_length=31, default='')  # Field name made lowercase.
    price_rules_exist = models.BooleanField(db_column='PRICE_RULES_EXIST', default=0)  # Field name made lowercase.
    lot_serial_exist = models.BooleanField(db_column='LOT_SERIAL_EXIST', default=0)  # Field name made lowercase.
    payment_priority = models.IntegerField(db_column='PAYMENT_PRIORITY', default=0)  # Field name made lowercase.
    renew_months = models.IntegerField(db_column='RENEW_MONTHS', default=0)  # Field name made lowercase.
    prorate = models.CharField(db_column='PRORATE', max_length=50, default='')  # Field name made lowercase.
    stock_item = models.BooleanField(db_column='STOCK_ITEM', default=0)  # Field name made lowercase.
    unit_of_measure = models.CharField(db_column='UNIT_OF_MEASURE', max_length=10, default='')  # Field name made lowercase.
    weight = models.DecimalField(db_column='WEIGHT', max_digits=15, decimal_places=2, default=0)  # Field name made lowercase.
    taxable = models.BooleanField(db_column='TAXABLE', default=0)  # Field name made lowercase.
    commisionable = models.BooleanField(db_column='COMMISIONABLE', default=0)  # Field name made lowercase.
    commision_percent = models.DecimalField(db_column='COMMISION_PERCENT', max_digits=15, decimal_places=2, default=0)  # Field name made lowercase.
    decimal_points = models.IntegerField(db_column='DECIMAL_POINTS', default=0)  # Field name made lowercase.
    income_account = models.CharField(db_column='INCOME_ACCOUNT', max_length=50, default='')  # Field name made lowercase.
    deferred_income_account = models.CharField(db_column='DEFERRED_INCOME_ACCOUNT', max_length=50, default='')  # Field name made lowercase.
    inventory_account = models.CharField(db_column='INVENTORY_ACCOUNT', max_length=50, default='')  # Field name made lowercase.
    adjustment_account = models.CharField(db_column='ADJUSTMENT_ACCOUNT', max_length=50, default='')  # Field name made lowercase.
    cog_account = models.CharField(db_column='COG_ACCOUNT', max_length=50, default='')  # Field name made lowercase.
    intent_to_edit = models.CharField(db_column='INTENT_TO_EDIT', max_length=80, default='')  # Field name made lowercase.
    price_1 = models.DecimalField(db_column='PRICE_1', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    price_2 = models.DecimalField(db_column='PRICE_2', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    price_3 = models.DecimalField(db_column='PRICE_3', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    complimentary = models.BooleanField(db_column='COMPLIMENTARY', default=0)  # Field name made lowercase.
    attributes = models.CharField(db_column='ATTRIBUTES', max_length=255, default='')  # Field name made lowercase.
    pst_taxable = models.BooleanField(db_column='PST_TAXABLE', default=0)  # Field name made lowercase.
    taxable_value = models.DecimalField(db_column='TAXABLE_VALUE', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    org_code = models.CharField(db_column='ORG_CODE', max_length=5, default='')  # Field name made lowercase.
    tax_authority = models.CharField(db_column='TAX_AUTHORITY', max_length=15, default='')  # Field name made lowercase.
    web_option = models.SmallIntegerField(db_column='WEB_OPTION', default=1)  # Field name made lowercase.
    image_url = models.CharField(db_column='IMAGE_URL', max_length=100, default='')  # Field name made lowercase.
    apply_image = models.BooleanField(db_column='APPLY_IMAGE', default=0)  # Field name made lowercase.
    is_kit = models.BooleanField(db_column='IS_KIT', default=0)  # Field name made lowercase.
    info_url = models.CharField(db_column='INFO_URL', max_length=100, default='')  # Field name made lowercase.
    apply_info = models.BooleanField(db_column='APPLY_INFO', default=0)  # Field name made lowercase.
    plp_code = models.CharField(db_column='PLP_CODE', max_length=6, default='')  # Field name made lowercase.
    promote = models.BooleanField(db_column='PROMOTE', default=0)  # Field name made lowercase.
    thumbnail_url = models.CharField(db_column='THUMBNAIL_URL', max_length=100, default='')  # Field name made lowercase.
    apply_thumbnail = models.BooleanField(db_column='APPLY_THUMBNAIL', default=0)  # Field name made lowercase.
    catalog_desc = models.TextField(db_column='CATALOG_DESC', blank=True, null=True, default='')  # Field name made lowercase. This field type is a guess.
    web_desc = models.TextField(db_column='WEB_DESC', blank=True, null=True, default='')  # Field name made lowercase. This field type is a guess.
    other_desc = models.TextField(db_column='OTHER_DESC', blank=True, null=True, default='')  # Field name made lowercase. This field type is a guess.
    location = models.CharField(db_column='LOCATION', max_length=10, default='')  # Field name made lowercase.
    premium = models.BooleanField(db_column='PREMIUM', default=0)  # Field name made lowercase.
    fair_market_value = models.DecimalField(db_column='FAIR_MARKET_VALUE', max_digits=15, decimal_places=2, default=0)  # Field name made lowercase.
    is_fr_item = models.BooleanField(db_column='IS_FR_ITEM', default=0)  # Field name made lowercase.
    appeal_code = models.CharField(db_column='APPEAL_CODE', max_length=40, default='')  # Field name made lowercase.
    campaign_code = models.CharField(db_column='CAMPAIGN_CODE', max_length=10, default='')  # Field name made lowercase.
    price_from_components = models.BooleanField(db_column='PRICE_FROM_COMPONENTS', default=0)  # Field name made lowercase.
    publish_start_date = models.DateTimeField(db_column='PUBLISH_START_DATE', blank=True, null=True)  # Field name made lowercase.
    publish_end_date = models.DateTimeField(db_column='PUBLISH_END_DATE', blank=True, null=True)  # Field name made lowercase.
    tax_by_location = models.BooleanField(db_column='TAX_BY_LOCATION', default=0)  # Field name made lowercase.
    taxcategory_code = models.CharField(db_column='TAXCATEGORY_CODE', max_length=10, default='')  # Field name made lowercase.
    related_content_message = models.TextField(db_column='RELATED_CONTENT_MESSAGE', blank=True, null=True, default='')  # Field name made lowercase. This field type is a guess.

    class Meta:
        managed = False
        db_table = 'Product'

    @classmethod
    def create_event(cls, event, product_major, product_minor, product_code, option=None):

        # EW THIS IS NASTY TO BUILD THE IMIS PRODUCTS.
        # WE SHOULD HAVE SEPARATE COLUMNS IN DJANGO FOR MAJOR/MINOR/CODE!

        # SYNC PRODUCT OPTIONS (MAIN EVENT)
        if option:
            title = (option.code + ' ' + option.title)[:60]
            status = option.status
            price = 0 if not event.product.prices.filter(option_code=option.code).exclude(price=0) else event.product.prices.filter(option_code=option.code).exclude(price=0).first().price # default price will be the 1st price for the option... (is this okay?)

        # TICKETED ACTIVITIES
        elif hasattr(event, "product") and event.product:
            title = (product_minor + " " + event.title)[:55]
            status = event.product.status
            price = event.product.prices.all().first().price

        # SESSION (NO TICKET), USE EVENT CODE TO CREATE IMIS PRODUCT.
        else:
            title = (product_minor + " " + event.title)[:60]
            status = event.status
            price = 0

        imis_product, created = cls.objects.get_or_create(product_code=product_code)

        cls.objects.filter(product_code=product_code).update(
                product_code = product_code,
                product_major = product_major,
                product_minor = product_minor,
                prod_type = 'MEETING',
                title_key = title.upper(),
                title = title,
                description = "",
                status = status,
                price_rules_exist = 1 if option else 0, # ONLY OPTIONS HAVE PRICE RULES. TICKETS DO NOT.
                income_account = "000000-000000" if not hasattr(event, "product") else event.product.gl_account,
                complimentary = 1 if hasattr(event, "product") and event.product and price == 0 else 0,
                # set prices to 0 for chapter conferences
                price_1 = 0 if option else price,
                price_2 = 0 if option else price,
                price_3 = 0 if option else price
                )

class ScoresDemographics(models.Model):
    id = models.CharField(db_column='ID', max_length=10)  # Field name made lowercase.
    pass_field = models.BooleanField(db_column='PASS')  # Field name made lowercase. Field renamed because it was a Python reserved word.
    fail = models.BooleanField(db_column='FAIL')  # Field name made lowercase.
    exams_remaining = models.FloatField(db_column='EXAMS_REMAINING', blank=True, null=True)  # Field name made lowercase.
    scaled_score = models.FloatField(db_column='SCALED_SCORE', blank=True, null=True)  # Field name made lowercase.
    raw_score = models.FloatField(db_column='RAW_SCORE', blank=True, null=True)  # Field name made lowercase.
    exam_date = models.DateTimeField(db_column='EXAM_DATE', blank=True, null=True)  # Field name made lowercase.
    score_1 = models.FloatField(db_column='SCORE_1', blank=True, null=True)  # Field name made lowercase.
    score_2 = models.FloatField(db_column='SCORE_2', blank=True, null=True)  # Field name made lowercase.
    score_3 = models.FloatField(db_column='SCORE_3', blank=True, null=True)  # Field name made lowercase.
    score_4 = models.FloatField(db_column='SCORE_4', blank=True, null=True)  # Field name made lowercase.
    score_5 = models.FloatField(db_column='SCORE_5', blank=True, null=True)  # Field name made lowercase.
    score_6 = models.FloatField(db_column='SCORE_6', blank=True, null=True)  # Field name made lowercase.
    score_7 = models.FloatField(db_column='SCORE_7', blank=True, null=True, default=0)  # Field name made lowercase.
    score_8 = models.FloatField(db_column='SCORE_8', blank=True, null=True, default=0)  # Field name made lowercase.
    testform_code = models.CharField(db_column='TESTFORM_CODE', max_length=50, blank=True, null=True)  # Field name made lowercase.
    auto_counter = models.AutoField(db_column='AUTO_COUNTER', primary_key=True)  # Field name made lowercase.
    time_entered = models.DateTimeField(db_column='TIME_ENTERED', blank=True, null=True)  # Field name made lowercase.
    exam_code = models.CharField(db_column='EXAM_CODE', max_length=15, blank=True, null=True)  # Field name made lowercase.
    test_center = models.CharField(db_column='TEST_CENTER', max_length=20, blank=True, null=True)  # Field name made lowercase.
    registrant_type = models.CharField(db_column='REGISTRANT_TYPE', max_length=50, blank=True, null=True)
    file_name = models.CharField(db_column='FILE_NAME', max_length=255, blank=True, null=True)
    gee_eligibility_id = models.CharField(db_column='GEE_ELIGIBILITY_ID', max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'SCORES_Demographics'

    @classmethod
    def import_exam_results(cls, exam_code):
        """
        imports results from prometric
        requires exam code for scores demographics - assumes ALL files in prometric are for the exam code passed in
        NOTE: Run this on WEB01DO
        NOTE: create new folder in /var/lib/prometric/ + exam_code for each exam that needs to be uploaded
        ALSO NOTE: pass in ClientID (webuserid) to the exam registration so we can populate this automatically!
        ALSO ALSO NOTE: pass in exam_code to the exam registration so we can populate this automatically!
        ALSO ALSO ALSO NOTE: delete exam results after the upload is complete.
        """

        # authenticate on init and move to working directory
        prometric_ftp = ImplicitFTP_TLS()
        prometric_ftp.connect(host=PROMETRIC_FTP_HOST, port=PROMETRIC_FTP_PORT)
        prometric_ftp.login(user=PROMETRIC_FTP_USERNAME, passwd=PROMETRIC_FTP_PASSWORD)
        prometric_ftp.prot_p()

        file_match = '*xml'
        # save current working directory as variable
        working_directory = os.getcwd()

        # change staging working directory for ftp upload
        #os.chdir("/users/philliplowe/Desktop/prometric-test")
        os.chdir("/srv/prometric/" + exam_code)

        # change directory to exam results
        prometric_ftp.cwd('/From_PRO')

        ExamRegistration = apps.get_model(app_label="exam", model_name="ExamRegistration")
        # 1. upload all files to the webserver
        for filename in prometric_ftp.nlst(file_match):
            try:
                print("uploading {0} to web server".format(filename))
                prometric_ftp.retrbinary('RETR %s' % filename, open('%s' % filename, 'wb').write)

                # delete file from prometric after it is uploaded to the webserver
                # prometric_ftp.delete(filename)

            except Exception as e:
                print("ERROR UPLOADING TO WEB SERVER: " + str(e))
        # 2. import into SCORES_Demographics table


        for filename in os.listdir():
            try:
                print("uploading {0}".format(filename))
                score_dict = {}
                # write the file to the web server

                # parse the file
                tree = ET.parse(filename)
                root = tree.getroot()

                # fields needed for prometric score information
                # INSERT INTO SCORES_Demographics (SCALED_SCORE, RAW_SCORE,

                # ID, TESTFORM_CODE, TEST_CENTER, EXAM_DATE, TIME_ENTERED, PASS, FAIL (replaced with pass indicator),
                # SCORE_1, SCORE_2, SCORE_3, SCORE_4, SCORE_5,
                # SCORE_6
                # decommissioned - EXAMS_REMAINING

                # delivery - is there a cleaner way to grab this data?
                # look into using beautiful soup - Matt

                demographic = root.find('{http://sdk.prometric.com/schemas/SimpleXMLResults1_4}demographics')
                delivery = root.find('{http://sdk.prometric.com/schemas/SimpleXMLResults1_4}delivery')
                exam = root.find('{http://sdk.prometric.com/schemas/SimpleXMLResults1_4}exam')
                categories = exam.find('{http://sdk.prometric.com/schemas/SimpleXMLResults1_4}categories')

                score = exam.find('{http://sdk.prometric.com/schemas/SimpleXMLResults1_4}score')

                for x in demographic:
                    # we need to populate this in the clientid field
                    # if x.attrib.get('name') == "CandidateSSN":
                    #    score_dict['id'] = x.attrib.get("value")

                    # THIS IS TEMPORARY UNTIL WE CAN PROPERLY POPULATE THIS INFORMATION!
                    if x.attrib.get('name') == "eligibilityid1":
                        gee_eligibility_id = x.attrib.get("value")

                    # REGULAR OR AICP_CAND
                    if x.attrib.get('name') == "clientCandidateId2":
                        registrant_type = x.attrib.get("value")

                    if x.attrib.get('name') == "ClientID":
                        user_id = x.attrib.get("value")

                for category in categories:
                    category_name = category.attrib.get("name")

                    if category_name == "Areas of Practice":
                        score_dict['score_1'] = category.attrib.get("countcorrect")
                    elif category_name == "Plan Making and Implementation":
                        score_dict['score_2']  = category.attrib.get("countcorrect")
                    elif category_name == "Fundamental Planning Knowledge":
                        score_dict['score_3']  = category.attrib.get("countcorrect")
                    elif category_name == "AICP Code of Ethics and Professional Conduct":
                        score_dict['score_4']  = category.attrib.get("countcorrect")
                    elif category_name == "Leadership, Administration, and Management":
                        score_dict['score_5']  = category.attrib.get("countcorrect")

                pass_indicator = score.attrib.get('passindicator')
                score_dict['raw_score'] = exam.attrib.get("countcorrect")
                score_dict['scaled_score'] = score.attrib.get("scorevalue")
                score_dict['test_center'] = delivery.attrib.get('sitecode')
                score_dict['testform_code'] = exam.attrib.get('examformname')
                score_dict['exam_date'] = exam.attrib.get('enddatetime')
                #score_dict['pass_indicator'] = pass_indicator
                score_dict['pass_field'] = True if pass_indicator == "p" else False
                score_dict['fail'] = True if pass_indicator == "f" else False
                score_dict['time_entered'] = datetime.datetime.now()
                score_dict['exams_remaining'] = 0
                score_dict['exam_code'] = exam_code
                score_dict['registrant_type'] = registrant_type
                score_dict['file_name'] = filename
                score_dict['gee_eligibility_id'] = gee_eligibility_id
                score_dict['id'] = user_id

                ###### REMOVET THIS AFTER REG TYPES ARE IMPORTED INTO PROMETRIC #########P
                if not registrant_type or registrant_type == "":
                    try:
                        exam_registration = ExamRegistration.objects.get(gee_eligibility_id = gee_eligibility_id)

                        if exam_registration.registration_type in ["CAND_ENR_A", "CAND_T_0", "CAND_T_100"]:
                            score_dict['registrant_type'] = "AICP_CAND"
                        else:
                            score_dict['registrant_type'] = "REGULAR"
                    except Exception as e:
                        print("cannot find exam")

                ####### REMOVE THIS AFTER WE START IMPORTING THE USER IDS INTO PROMETRIC ########
                if not user_id or user_id == "":
                    try:

                        user_id = ExamRegistration.objects.get(gee_eligibility_id = gee_eligibility_id).contact.user.username
                        score_dict['id'] = user_id
                    except Exception as e:
                        print("cannot find user_id")

                # add results to scores_demographics
                # NOTE: GET_OR_CREATE does not work for unmanaged tables
                score_record = cls.objects.create(**score_dict)

                ######## UPDATE IS_PASS FIELD ON THE REGISTRATION #########
                try:
                    ExamRegistration.objects.filter(gee_eligibility_id = gee_eligibility_id, contact__user__username=score_dict['id']).update(is_pass = score_dict['pass_field'])
                except Exception as e:
                    print("cannot find registration.")

                # scores_instance, created = cls.objects.create(id=user_id, pass_field=pass_field, fail=fail, exams_ramining = 0, scaled_score = scaled_score, raw_score=raw_score, exam_date=exam_date, score_1=score_1, score_2=score_2, score_3=score_3, score_4=score_4, score_5=score_5, testform_code = exam_form_code, time_entered=datetime().now(), exam_code=exam_code, test_center=test_center)
            except Exception as e:
                print("ERROR: " + str(e))
        # change working directory back
        os.chdir(working_directory)


class CustomAICPExamScore(models.Model):
    id = models.CharField(db_column='ID', max_length=10, primary_key=True)  # Field name made lowercase.
    seqn = models.IntegerField(db_column='SEQN', primary_key=True)
    exam_code = models.CharField(db_column='EXAM_CODE', max_length=15, blank=True, null=True)  # Field name made lowercase.
    exam_date = models.DateTimeField(db_column='EXAM_DATE', blank=True, null=True)  # Field name made lowercase.
    pass_field = models.BooleanField(db_column='PASS')  # Field name made lowercase. Field renamed because it was a Python reserved word.
    scaled_score = models.FloatField(db_column='SCALED_SCORE', blank=True, null=True)  # Field name made lowercase.
    raw_score = models.FloatField(db_column='RAW_SCORE', blank=True, null=True)  # Field name made lowercase.
    score_1 = models.FloatField(db_column='SCORE_1', blank=True, null=True)  # Field name made lowercase.
    score_2 = models.FloatField(db_column='SCORE_2', blank=True, null=True)  # Field name made lowercase.
    score_3 = models.FloatField(db_column='SCORE_3', blank=True, null=True)  # Field name made lowercase.
    score_4 = models.FloatField(db_column='SCORE_4', blank=True, null=True)  # Field name made lowercase.
    score_5 = models.FloatField(db_column='SCORE_5', blank=True, null=True)  # Field name made lowercase.
    score_6 = models.FloatField(db_column='SCORE_6', blank=True, null=True, default=0)  # Field name made lowercase.
    score_7 = models.FloatField(db_column='SCORE_7', blank=True, null=True, default=0)  # Field name made lowercase.
    score_8 = models.FloatField(db_column='SCORE_8', blank=True, null=True, default=0)  # Field name made lowercase.
    testform_code = models.CharField(db_column='TESTFORM_CODE', max_length=50, blank=True, null=True)  # Field name made lowercase.
    test_center = models.CharField(db_column='TEST_CENTER', max_length=20, blank=True, null=True)  # Field name made lowercase.
    registrant_type = models.CharField(db_column='REGISTRANT_TYPE', max_length=50, blank=True, null=True)
    file_name = models.CharField(db_column='FILE_NAME', max_length=255, blank=True, null=True)
    gee_eligibility_id = models.CharField(db_column='GEE_ELIGIBILITY_ID', max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Custom_AICP_Exam_Score'

    @classmethod
    def create_seqn(cls):
        counter = Counter.objects.get(
            counter_name='Custom_AICP_Exam_Score')

        counter.last_value += 1
        counter.save()

        return counter.last_value

    @classmethod
    def import_exam_results(cls, exam_code):
        """
        imports results from prometric
        requires exam code for scores demographics - assumes ALL files in prometric are for the exam code passed in
        NOTE: Run this on WEB01DO
        NOTE: create new folder in /var/lib/prometric/ + exam_code for each exam that needs to be uploaded
        ALSO NOTE: pass in ClientID (webuserid) to the exam registration so we can populate this automatically!
        ALSO ALSO NOTE: pass in exam_code to the exam registration so we can populate this automatically!
        ALSO ALSO ALSO NOTE: delete exam results after the upload is complete.
        """

        # authenticate on init and move to working directory
        prometric_ftp = ImplicitFTP_TLS()
        prometric_ftp.connect(host=PROMETRIC_FTP_HOST, port=PROMETRIC_FTP_PORT)
        prometric_ftp.login(user=PROMETRIC_FTP_USERNAME, passwd=PROMETRIC_FTP_PASSWORD)
        prometric_ftp.prot_p()

        file_match = '*xml'
        # save current working directory as variable
        working_directory = os.getcwd()

        # change staging working directory for ftp upload
        # os.chdir("/users/plowe/Desktop/prometric-test")

        parent_dir = "/srv/prometric"
        path = os.path.join(parent_dir, exam_code)

        if not os.path.isdir(path):
            os.mkdir(path)

        os.chdir(path)

        # change directory to exam results
        prometric_ftp.cwd('/From_PRO')

        ExamRegistration = apps.get_model(app_label="exam", model_name="ExamRegistration")

        for filename in prometric_ftp.nlst(file_match):
            try:

                file_path = os.path.join(path, filename)

                if not os.path.isfile(file_path):
                    print("uploading {0} to web server".format(filename))
                    prometric_ftp.retrbinary('RETR %s' % filename, open('%s' % filename, 'wb').write)

                    # delete file from prometric after it is uploaded to the webserver
                    # prometric_ftp.delete(filename)
                else:
                    print("{0} already exists on server. Skipping download".format(filename))

            except Exception as e:
                print("ERROR UPLOADING TO WEB SERVER: " + str(e))

        for filename in os.listdir():

            try:
                    score_dict = {}
                    # write the file to the web server

                    # parse the file
                    tree = ET.parse(filename)
                    root = tree.getroot()

                    # delivery - is there a cleaner way to grab this data?
                    # look into using beautiful soup - Matt

                    demographic = root.find('{http://sdk.prometric.com/schemas/SimpleXMLResults1_4}demographics')
                    delivery = root.find('{http://sdk.prometric.com/schemas/SimpleXMLResults1_4}delivery')
                    exam = root.find('{http://sdk.prometric.com/schemas/SimpleXMLResults1_4}exam')
                    categories = exam.find('{http://sdk.prometric.com/schemas/SimpleXMLResults1_4}categories')

                    score = exam.find('{http://sdk.prometric.com/schemas/SimpleXMLResults1_4}score')

                    user_id = ""
                    email = "plowe@planning.org"

                    for x in demographic:

                        if x.attrib.get('name') == "eligibilityid1":
                            gee_eligibility_id = x.attrib.get("value")

                        # REGULAR OR AICP_CAND
                        if x.attrib.get('name') == "clientCandidateId2":
                            registrant_type = x.attrib.get("value")

                        if x.attrib.get('name') == "ClientID":
                            user_id = x.attrib.get("value")

                        # additional check to get user_id since Open Water es no bueno
                        if user_id == "":
                            if x.attrib.get('name') == "EmailAddress":
                                email = x.attrib.get("value")

                                name_instance = Name.objects.filter(email = email).first()

                                if name_instance:
                                    user_id = name_instance.id
                                else:
                                    # set user_id to random value so Jen can manually provide data
                                    user_id = '_' + ''.join(random.choice(string.ascii_uppercase) for _ in range(5))

                    if not CustomAICPExamScore.objects.filter(id=user_id, exam_code=exam_code):

                        for category in categories:
                            category_name = category.attrib.get("name")

                            if category_name == "Areas of Practice":
                                score_dict['score_1'] = int(category.attrib.get("countcorrect"))
                            elif category_name == "Plan Making and Implementation":
                                score_dict['score_2']  = int(category.attrib.get("countcorrect"))
                            elif category_name == "Fundamental Planning Knowledge":
                                score_dict['score_3']  = int(category.attrib.get("countcorrect"))
                            elif category_name == "AICP Code of Ethics and Professional Conduct":
                                score_dict['score_4']  = int(category.attrib.get("countcorrect"))
                            elif category_name == "Leadership, Administration, and Management":
                                score_dict['score_5']  = int(category.attrib.get("countcorrect"))

                        pass_indicator = score.attrib.get('passindicator')
                        score_dict['seqn'] = CustomAICPExamScore.create_seqn()
                        score_dict['raw_score'] = int(exam.attrib.get("countcorrect"))
                        score_dict['scaled_score'] = int(score.attrib.get("scorevalue"))
                        score_dict['test_center'] = delivery.attrib.get('sitecode')
                        score_dict['testform_code'] = exam.attrib.get('examformname')
                        score_dict['exam_date'] = exam.attrib.get('enddatetime')
                        score_dict['pass_field'] = True if pass_indicator == "p" else False
                        score_dict['exam_code'] = exam_code
                        score_dict['registrant_type'] = registrant_type
                        score_dict['file_name'] = filename
                        score_dict['gee_eligibility_id'] = gee_eligibility_id
                        score_dict['id'] = user_id

                        cls.objects.create(**score_dict)
                        print("uploading {0}".format(filename))

                        ######## UPDATE IS_PASS FIELD ON THE REGISTRATION #########
                        try:
                            ExamRegistration.objects.filter(gee_eligibility_id=gee_eligibility_id,
                                                            contact__user__username=score_dict['id']).update(
                                is_pass=score_dict['pass_field'])
                        except Exception as e:
                            print("cannot find registration.")

                    else:
                        print("{0} exists in iMIS. skipping insert.".format(filename))

            except Exception as e:
                print("ERROR: " + str(e))


class NPC18_Speakers_Temp(models.Model):
    id = models.CharField(db_column='ID', max_length=10, primary_key=True)  # Field name made lowercase.
    address_1 = models.CharField(db_column='ADDRESS_1', max_length=40)  # Field name made lowercase.
    address_2 = models.CharField(db_column='ADDRESS_2', max_length=40)  # Field name made lowercase.
    city = models.CharField(db_column='CITY', max_length=40)  # Field name made lowercase.
    state_province = models.CharField(db_column='STATE_PROVINCE', max_length=15)  # Field name made lowercase.
    zip = models.CharField(db_column='ZIP', max_length=10)  # Field name made lowercase.
    country = models.CharField(db_column='COUNTRY', max_length=25)  # Field name made lowercase.
    fax = models.CharField(db_column='FAX', max_length=25)  # Field name made lowercase.
    email = models.CharField(db_column='EMAIL', max_length=100)  # Field name made lowercase.
    first_name = models.CharField(db_column='FIRST_NAME', max_length=20)  # Field name made lowercase.
    last_name = models.CharField(db_column='LAST_NAME', max_length=30)  # Field name made lowercase.
    work_phone = models.CharField(db_column='WORK_PHONE', max_length=25)  # Field name made lowercase.
    cell_phone = models.CharField(db_column='CELL_PHONE', max_length=25)  # Field name made lowercase.
    pw = models.CharField(db_column='PW', max_length=50)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = '_NPC_2018_Speaker_Upload'


class OrderMeet(models.Model):
    order_number = models.DecimalField(db_column='ORDER_NUMBER', primary_key=True, max_digits=15, decimal_places=2)  # Field name made lowercase.
    meeting = models.CharField(db_column='MEETING', max_length=10)  # Field name made lowercase.
    registrant_class = models.CharField(db_column='REGISTRANT_CLASS', max_length=5)  # Field name made lowercase.
    arrival = models.DateTimeField(db_column='ARRIVAL', blank=True, null=True)  # Field name made lowercase.
    departure = models.DateTimeField(db_column='DEPARTURE', blank=True, null=True)  # Field name made lowercase.
    hotel = models.CharField(db_column='HOTEL', max_length=40)  # Field name made lowercase.
    lodging_instructions = models.CharField(db_column='LODGING_INSTRUCTIONS', max_length=255)  # Field name made lowercase.
    booth = models.CharField(db_column='BOOTH', max_length=255)  # Field name made lowercase.
    guest_first = models.CharField(db_column='GUEST_FIRST', max_length=20)  # Field name made lowercase.
    guest_middle = models.CharField(db_column='GUEST_MIDDLE', max_length=20)  # Field name made lowercase.
    guest_last = models.CharField(db_column='GUEST_LAST', max_length=30)  # Field name made lowercase.
    guest_is_spouse = models.BooleanField(db_column='GUEST_IS_SPOUSE')  # Field name made lowercase.
    additional_badges = models.TextField(db_column='ADDITIONAL_BADGES', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    delegate = models.CharField(db_column='DELEGATE', max_length=10)  # Field name made lowercase.
    uf_1 = models.BooleanField(db_column='UF_1')  # Field name made lowercase.
    uf_2 = models.BooleanField(db_column='UF_2')  # Field name made lowercase.
    uf_3 = models.BooleanField(db_column='UF_3')  # Field name made lowercase.
    uf_4 = models.BooleanField(db_column='UF_4')  # Field name made lowercase.
    uf_5 = models.BooleanField(db_column='UF_5')  # Field name made lowercase.
    uf_6 = models.CharField(db_column='UF_6', max_length=100)  # Field name made lowercase.
    uf_7 = models.CharField(db_column='UF_7', max_length=100)  # Field name made lowercase.
    uf_8 = models.CharField(db_column='UF_8', max_length=100)  # Field name made lowercase.
    share_status = models.IntegerField(db_column='SHARE_STATUS')  # Field name made lowercase.
    share_order_number = models.DecimalField(db_column='SHARE_ORDER_NUMBER', max_digits=15, decimal_places=2)  # Field name made lowercase.
    room_type = models.CharField(db_column='ROOM_TYPE', max_length=8)  # Field name made lowercase.
    room_quantity = models.IntegerField(db_column='ROOM_QUANTITY')  # Field name made lowercase.
    room_confirm = models.BooleanField(db_column='ROOM_CONFIRM')  # Field name made lowercase.
    uf_9 = models.TextField(db_column='UF_9', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    uf_10 = models.TextField(db_column='UF_10', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    arrival_time = models.DateTimeField(db_column='ARRIVAL_TIME', blank=True, null=True)  # Field name made lowercase.
    departure_time = models.DateTimeField(db_column='DEPARTURE_TIME', blank=True, null=True)  # Field name made lowercase.
    comp_registrations = models.IntegerField(db_column='COMP_REGISTRATIONS')  # Field name made lowercase.
    comp_reg_source = models.DecimalField(db_column='COMP_REG_SOURCE', max_digits=15, decimal_places=6, blank=True, null=True)  # Field name made lowercase.
    total_square_feet = models.DecimalField(db_column='TOTAL_SQUARE_FEET', max_digits=15, decimal_places=2)  # Field name made lowercase.
    comp_registrations_used = models.IntegerField(db_column='COMP_REGISTRATIONS_USED')  # Field name made lowercase.
    parent_order_number = models.DecimalField(db_column='PARENT_ORDER_NUMBER', max_digits=15, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    registered_by_id = models.CharField(db_column='REGISTERED_BY_ID', max_length=10, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Order_Meet'


class Trans(models.Model):
    trans_number = models.IntegerField(db_column='TRANS_NUMBER', primary_key=True)  # Field name made lowercase.
    line_number = models.IntegerField(db_column='LINE_NUMBER', primary_key=True)  # Field name made lowercase.
    batch_num = models.CharField(db_column='BATCH_NUM', max_length=15)  # Field name made lowercase.
    owner_org_code = models.CharField(db_column='OWNER_ORG_CODE', max_length=10)  # Field name made lowercase.
    source_system = models.CharField(db_column='SOURCE_SYSTEM', max_length=10)  # Field name made lowercase.
    journal_type = models.CharField(db_column='JOURNAL_TYPE', max_length=5)  # Field name made lowercase.
    transaction_type = models.CharField(db_column='TRANSACTION_TYPE', max_length=5)  # Field name made lowercase.
    transaction_date = models.DateTimeField(db_column='TRANSACTION_DATE')  # Field name made lowercase.
    bt_id = models.CharField(db_column='BT_ID', max_length=10)  # Field name made lowercase.
    st_id = models.CharField(db_column='ST_ID', max_length=10)  # Field name made lowercase.
    invoice_reference_num = models.IntegerField(db_column='INVOICE_REFERENCE_NUM')  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=255)  # Field name made lowercase.
    customer_name = models.CharField(db_column='CUSTOMER_NAME', max_length=60)  # Field name made lowercase.
    customer_reference = models.CharField(db_column='CUSTOMER_REFERENCE', max_length=40)  # Field name made lowercase.
    reference_1 = models.CharField(db_column='REFERENCE_1', max_length=50)  # Field name made lowercase.
    source_code = models.CharField(db_column='SOURCE_CODE', max_length=40)  # Field name made lowercase.
    product_code = models.CharField(db_column='PRODUCT_CODE', max_length=31)  # Field name made lowercase.
    effective_date = models.DateTimeField(db_column='EFFECTIVE_DATE', blank=True, null=True)  # Field name made lowercase.
    paid_thru = models.DateTimeField(db_column='PAID_THRU', blank=True, null=True)  # Field name made lowercase.
    months_paid = models.IntegerField(db_column='MONTHS_PAID')  # Field name made lowercase.
    fiscal_period = models.IntegerField(db_column='FISCAL_PERIOD')  # Field name made lowercase.
    deferral_months = models.IntegerField(db_column='DEFERRAL_MONTHS')  # Field name made lowercase.
    amount = models.DecimalField(db_column='AMOUNT', max_digits=19, decimal_places=4)  # Field name made lowercase.
    adjustment_amount = models.DecimalField(db_column='ADJUSTMENT_AMOUNT', max_digits=19, decimal_places=4)  # Field name made lowercase.
    pseudo_account = models.CharField(db_column='PSEUDO_ACCOUNT', max_length=50)  # Field name made lowercase.
    gl_acct_org_code = models.CharField(db_column='GL_ACCT_ORG_CODE', max_length=5)  # Field name made lowercase.
    gl_account = models.CharField(db_column='GL_ACCOUNT', max_length=50)  # Field name made lowercase.
    deferred_gl_account = models.CharField(db_column='DEFERRED_GL_ACCOUNT', max_length=50)  # Field name made lowercase.
    invoice_charges = models.DecimalField(db_column='INVOICE_CHARGES', max_digits=19, decimal_places=4)  # Field name made lowercase.
    invoice_credits = models.DecimalField(db_column='INVOICE_CREDITS', max_digits=19, decimal_places=4)  # Field name made lowercase.
    quantity = models.DecimalField(db_column='QUANTITY', max_digits=15, decimal_places=4)  # Field name made lowercase.
    unit_price = models.DecimalField(db_column='UNIT_PRICE', max_digits=19, decimal_places=4)  # Field name made lowercase.
    payment_type = models.CharField(db_column='PAYMENT_TYPE', max_length=10)  # Field name made lowercase.
    check_number = models.CharField(db_column='CHECK_NUMBER', max_length=10)  # Field name made lowercase.
    cc_number = models.CharField(db_column='CC_NUMBER', max_length=25)  # Field name made lowercase.
    cc_expire = models.CharField(db_column='CC_EXPIRE', max_length=10)  # Field name made lowercase.
    cc_authorize = models.CharField(db_column='CC_AUTHORIZE', max_length=10)  # Field name made lowercase.
    cc_name = models.CharField(db_column='CC_NAME', max_length=40)  # Field name made lowercase.
    terms_code = models.CharField(db_column='TERMS_CODE', max_length=5)  # Field name made lowercase.
    activity_seqn = models.IntegerField(db_column='ACTIVITY_SEQN')  # Field name made lowercase.
    posted = models.SmallIntegerField(db_column='POSTED')  # Field name made lowercase.
    prod_type = models.CharField(db_column='PROD_TYPE', max_length=5)  # Field name made lowercase.
    activity_type = models.CharField(db_column='ACTIVITY_TYPE', max_length=10)  # Field name made lowercase.
    action_codes = models.CharField(db_column='ACTION_CODES', max_length=255)  # Field name made lowercase.
    tickler_date = models.DateTimeField(db_column='TICKLER_DATE', blank=True, null=True)  # Field name made lowercase.
    date_entered = models.DateTimeField(db_column='DATE_ENTERED', blank=True, null=True)  # Field name made lowercase.
    entered_by = models.CharField(db_column='ENTERED_BY', max_length=60)  # Field name made lowercase.
    sub_line_number = models.IntegerField(db_column='SUB_LINE_NUMBER')  # Field name made lowercase.
    install_bill_date = models.DateTimeField(db_column='INSTALL_BILL_DATE', blank=True, null=True)  # Field name made lowercase.
    taxable_value = models.DecimalField(db_column='TAXABLE_VALUE', max_digits=19, decimal_places=4)  # Field name made lowercase.
    solicitor_id = models.CharField(db_column='SOLICITOR_ID', max_length=10)  # Field name made lowercase.
    invoice_adjustments = models.DecimalField(db_column='INVOICE_ADJUSTMENTS', max_digits=19, decimal_places=4)  # Field name made lowercase.
    invoice_line_num = models.IntegerField(db_column='INVOICE_LINE_NUM')  # Field name made lowercase.
    merge_code = models.CharField(db_column='MERGE_CODE', max_length=40)  # Field name made lowercase.
    salutation_code = models.CharField(db_column='SALUTATION_CODE', max_length=40)  # Field name made lowercase.
    sender_code = models.CharField(db_column='SENDER_CODE', max_length=40)  # Field name made lowercase.
    is_match_gift = models.SmallIntegerField(db_column='IS_MATCH_GIFT')  # Field name made lowercase.
    match_gift_trans_num = models.IntegerField(db_column='MATCH_GIFT_TRANS_NUM')  # Field name made lowercase.
    match_activity_seqn = models.IntegerField(db_column='MATCH_ACTIVITY_SEQN')  # Field name made lowercase.
    mem_trib_id = models.CharField(db_column='MEM_TRIB_ID', max_length=10)  # Field name made lowercase.
    receipt_id = models.IntegerField(db_column='RECEIPT_ID')  # Field name made lowercase.
    do_not_receipt = models.SmallIntegerField(db_column='DO_NOT_RECEIPT')  # Field name made lowercase.
    cc_status = models.CharField(db_column='CC_STATUS', max_length=1)  # Field name made lowercase.
    encrypt_cc_number = models.CharField(db_column='ENCRYPT_CC_NUMBER', max_length=100)  # Field name made lowercase.
    encrypt_cc_expire = models.CharField(db_column='ENCRYPT_CC_EXPIRE', max_length=100)  # Field name made lowercase.
    fr_activity = models.CharField(db_column='FR_ACTIVITY', max_length=1)  # Field name made lowercase.
    fr_activity_seqn = models.IntegerField(db_column='FR_ACTIVITY_SEQN')  # Field name made lowercase.
    mem_trib_name_text = models.CharField(db_column='MEM_TRIB_NAME_TEXT', max_length=100)  # Field name made lowercase.
    campaign_code = models.CharField(db_column='CAMPAIGN_CODE', max_length=10)  # Field name made lowercase.
    is_fr_item = models.BooleanField(db_column='IS_FR_ITEM')  # Field name made lowercase.
    encrypt_csc = models.CharField(db_column='ENCRYPT_CSC', max_length=100)  # Field name made lowercase.
    issue_date = models.CharField(db_column='ISSUE_DATE', max_length=10)  # Field name made lowercase.
    issue_number = models.CharField(db_column='ISSUE_NUMBER', max_length=2)  # Field name made lowercase.
    gl_export_date = models.DateTimeField(db_column='GL_EXPORT_DATE', blank=True, null=True)  # Field name made lowercase.
    fr_checkbox = models.BooleanField(db_column='FR_CHECKBOX')  # Field name made lowercase.
    gateway_ref = models.CharField(db_column='GATEWAY_REF', max_length=100)  # Field name made lowercase.
    tax_authority = models.CharField(db_column='TAX_AUTHORITY', max_length=15)  # Field name made lowercase.
    tax_rate = models.DecimalField(db_column='TAX_RATE', max_digits=15, decimal_places=4)  # Field name made lowercase.
    tax_1 = models.DecimalField(db_column='TAX_1', max_digits=15, decimal_places=4)  # Field name made lowercase.
    price_adj = models.BooleanField(db_column='PRICE_ADJ')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Trans'
        unique_together = (('trans_number', 'line_number', 'sub_line_number'),)


class Orders(models.Model):
    order_number = models.DecimalField(db_column='ORDER_NUMBER', primary_key=True, max_digits=15, decimal_places=2)  # Field name made lowercase.
    org_code = models.CharField(db_column='ORG_CODE', max_length=5)  # Field name made lowercase.
    order_type_code = models.CharField(db_column='ORDER_TYPE_CODE', max_length=10)  # Field name made lowercase.
    stage = models.CharField(db_column='STAGE', max_length=10)  # Field name made lowercase.
    source_system = models.CharField(db_column='SOURCE_SYSTEM', max_length=10)  # Field name made lowercase.
    batch_num = models.CharField(db_column='BATCH_NUM', max_length=15)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=10)  # Field name made lowercase.
    hold_code = models.CharField(db_column='HOLD_CODE', max_length=10)  # Field name made lowercase.
    order_date = models.DateTimeField(db_column='ORDER_DATE', blank=True, null=True)  # Field name made lowercase.
    bt_id = models.CharField(db_column='BT_ID', max_length=10)  # Field name made lowercase.
    st_id = models.CharField(db_column='ST_ID', max_length=10)  # Field name made lowercase.
    st_address_num = models.IntegerField(db_column='ST_ADDRESS_NUM')  # Field name made lowercase.
    entered_date_time = models.DateTimeField(db_column='ENTERED_DATE_TIME', blank=True, null=True)  # Field name made lowercase.
    entered_by = models.CharField(db_column='ENTERED_BY', max_length=60)  # Field name made lowercase.
    updated_date_time = models.DateTimeField(db_column='UPDATED_DATE_TIME', blank=True, null=True)  # Field name made lowercase.
    updated_by = models.CharField(db_column='UPDATED_BY', max_length=60)  # Field name made lowercase.
    invoice_reference_num = models.IntegerField(db_column='INVOICE_REFERENCE_NUM')  # Field name made lowercase.
    invoice_number = models.IntegerField(db_column='INVOICE_NUMBER')  # Field name made lowercase.
    invoice_date = models.DateTimeField(db_column='INVOICE_DATE', blank=True, null=True)  # Field name made lowercase.
    number_lines = models.IntegerField(db_column='NUMBER_LINES')  # Field name made lowercase.
    full_name = models.CharField(db_column='FULL_NAME', max_length=70)  # Field name made lowercase.
    title = models.CharField(db_column='TITLE', max_length=80)  # Field name made lowercase.
    company = models.CharField(db_column='COMPANY', max_length=80)  # Field name made lowercase.
    full_address = models.CharField(db_column='FULL_ADDRESS', max_length=255)  # Field name made lowercase.
    prefix = models.CharField(db_column='PREFIX', max_length=25)  # Field name made lowercase.
    first_name = models.CharField(db_column='FIRST_NAME', max_length=20)  # Field name made lowercase.
    middle_name = models.CharField(db_column='MIDDLE_NAME', max_length=20)  # Field name made lowercase.
    last_name = models.CharField(db_column='LAST_NAME', max_length=30)  # Field name made lowercase.
    suffix = models.CharField(db_column='SUFFIX', max_length=10)  # Field name made lowercase.
    designation = models.CharField(db_column='DESIGNATION', max_length=30)  # Field name made lowercase.
    informal = models.CharField(db_column='INFORMAL', max_length=20)  # Field name made lowercase.
    last_first = models.CharField(db_column='LAST_FIRST', max_length=30)  # Field name made lowercase.
    company_sort = models.CharField(db_column='COMPANY_SORT', max_length=30)  # Field name made lowercase.
    address_1 = models.CharField(db_column='ADDRESS_1', max_length=40)  # Field name made lowercase.
    address_2 = models.CharField(db_column='ADDRESS_2', max_length=40)  # Field name made lowercase.
    city = models.CharField(db_column='CITY', max_length=40)  # Field name made lowercase.
    state_province = models.CharField(db_column='STATE_PROVINCE', max_length=15)  # Field name made lowercase.
    zip = models.CharField(db_column='ZIP', max_length=10)  # Field name made lowercase.
    country = models.CharField(db_column='COUNTRY', max_length=25)  # Field name made lowercase.
    dpb = models.CharField(db_column='DPB', max_length=8)  # Field name made lowercase.
    bar_code = models.CharField(db_column='BAR_CODE', max_length=14)  # Field name made lowercase.
    address_format = models.SmallIntegerField(db_column='ADDRESS_FORMAT')  # Field name made lowercase.
    phone = models.CharField(db_column='PHONE', max_length=25)  # Field name made lowercase.
    fax = models.CharField(db_column='FAX', max_length=25)  # Field name made lowercase.
    notes = models.TextField(db_column='NOTES', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    total_charges = models.DecimalField(db_column='TOTAL_CHARGES', max_digits=19, decimal_places=4)  # Field name made lowercase.
    total_payments = models.DecimalField(db_column='TOTAL_PAYMENTS', max_digits=19, decimal_places=4)  # Field name made lowercase.
    balance = models.DecimalField(db_column='BALANCE', max_digits=19, decimal_places=4)  # Field name made lowercase.
    line_total = models.DecimalField(db_column='LINE_TOTAL', max_digits=19, decimal_places=4)  # Field name made lowercase.
    line_taxable = models.DecimalField(db_column='LINE_TAXABLE', max_digits=19, decimal_places=4)  # Field name made lowercase.
    freight_1 = models.DecimalField(db_column='FREIGHT_1', max_digits=19, decimal_places=4)  # Field name made lowercase.
    freight_2 = models.DecimalField(db_column='FREIGHT_2', max_digits=19, decimal_places=4)  # Field name made lowercase.
    handling_1 = models.DecimalField(db_column='HANDLING_1', max_digits=19, decimal_places=4)  # Field name made lowercase.
    handling_2 = models.DecimalField(db_column='HANDLING_2', max_digits=19, decimal_places=4)  # Field name made lowercase.
    cancellation_fee = models.DecimalField(db_column='CANCELLATION_FEE', max_digits=19, decimal_places=4)  # Field name made lowercase.
    tax_1 = models.DecimalField(db_column='TAX_1', max_digits=19, decimal_places=4)  # Field name made lowercase.
    tax_2 = models.DecimalField(db_column='TAX_2', max_digits=19, decimal_places=4)  # Field name made lowercase.
    tax_3 = models.DecimalField(db_column='TAX_3', max_digits=19, decimal_places=4)  # Field name made lowercase.
    line_pay = models.DecimalField(db_column='LINE_PAY', max_digits=19, decimal_places=4)  # Field name made lowercase.
    other_pay = models.DecimalField(db_column='OTHER_PAY', max_digits=19, decimal_places=4)  # Field name made lowercase.
    ar_pay = models.DecimalField(db_column='AR_PAY', max_digits=19, decimal_places=4)  # Field name made lowercase.
    tax_author_1 = models.CharField(db_column='TAX_AUTHOR_1', max_length=15)  # Field name made lowercase.
    tax_author_2 = models.CharField(db_column='TAX_AUTHOR_2', max_length=15)  # Field name made lowercase.
    tax_author_3 = models.CharField(db_column='TAX_AUTHOR_3', max_length=15)  # Field name made lowercase.
    tax_rate_1 = models.DecimalField(db_column='TAX_RATE_1', max_digits=15, decimal_places=4)  # Field name made lowercase.
    tax_rate_2 = models.DecimalField(db_column='TAX_RATE_2', max_digits=15, decimal_places=4)  # Field name made lowercase.
    tax_rate_3 = models.DecimalField(db_column='TAX_RATE_3', max_digits=15, decimal_places=4)  # Field name made lowercase.
    tax_exempt = models.CharField(db_column='TAX_EXEMPT', max_length=15)  # Field name made lowercase.
    terms_code = models.CharField(db_column='TERMS_CODE', max_length=5)  # Field name made lowercase.
    scheduled_date = models.DateTimeField(db_column='SCHEDULED_DATE', blank=True, null=True)  # Field name made lowercase.
    confirmation_date_time = models.DateTimeField(db_column='CONFIRMATION_DATE_TIME', blank=True, null=True)  # Field name made lowercase.
    ship_papers_date_time = models.DateTimeField(db_column='SHIP_PAPERS_DATE_TIME', blank=True, null=True)  # Field name made lowercase.
    shipped_date_time = models.DateTimeField(db_column='SHIPPED_DATE_TIME', blank=True, null=True)  # Field name made lowercase.
    bo_released_date_time = models.DateTimeField(db_column='BO_RELEASED_DATE_TIME', blank=True, null=True)  # Field name made lowercase.
    source_code = models.CharField(db_column='SOURCE_CODE', max_length=40)  # Field name made lowercase.
    salesman = models.CharField(db_column='SALESMAN', max_length=15)  # Field name made lowercase.
    commission_rate = models.DecimalField(db_column='COMMISSION_RATE', max_digits=15, decimal_places=2)  # Field name made lowercase.
    discount_rate = models.DecimalField(db_column='DISCOUNT_RATE', max_digits=15, decimal_places=2)  # Field name made lowercase.
    priority = models.IntegerField(db_column='PRIORITY')  # Field name made lowercase.
    hold_comment = models.CharField(db_column='HOLD_COMMENT', max_length=255)  # Field name made lowercase.
    affect_inventory = models.BooleanField(db_column='AFFECT_INVENTORY')  # Field name made lowercase.
    hold_flag = models.BooleanField(db_column='HOLD_FLAG')  # Field name made lowercase.
    customer_reference = models.CharField(db_column='CUSTOMER_REFERENCE', max_length=40)  # Field name made lowercase.
    valuation_basis = models.SmallIntegerField(db_column='VALUATION_BASIS')  # Field name made lowercase.
    undiscounted_total = models.DecimalField(db_column='UNDISCOUNTED_TOTAL', max_digits=19, decimal_places=4)  # Field name made lowercase.
    auto_calc_handling = models.BooleanField(db_column='AUTO_CALC_HANDLING')  # Field name made lowercase.
    auto_calc_restocking = models.BooleanField(db_column='AUTO_CALC_RESTOCKING')  # Field name made lowercase.
    backorders = models.SmallIntegerField(db_column='BACKORDERS')  # Field name made lowercase.
    member_type = models.CharField(db_column='MEMBER_TYPE', max_length=5)  # Field name made lowercase.
    pay_type = models.CharField(db_column='PAY_TYPE', max_length=10)  # Field name made lowercase.
    pay_number = models.CharField(db_column='PAY_NUMBER', max_length=25)  # Field name made lowercase.
    credit_card_expires = models.CharField(db_column='CREDIT_CARD_EXPIRES', max_length=10)  # Field name made lowercase.
    authorize = models.CharField(db_column='AUTHORIZE', max_length=10)  # Field name made lowercase.
    credit_card_name = models.CharField(db_column='CREDIT_CARD_NAME', max_length=30)  # Field name made lowercase.
    bo_status = models.SmallIntegerField(db_column='BO_STATUS')  # Field name made lowercase.
    bo_release_date = models.DateTimeField(db_column='BO_RELEASE_DATE', blank=True, null=True)  # Field name made lowercase.
    total_quantity_ordered = models.DecimalField(db_column='TOTAL_QUANTITY_ORDERED', max_digits=15, decimal_places=4)  # Field name made lowercase.
    total_quantity_backordered = models.DecimalField(db_column='TOTAL_QUANTITY_BACKORDERED', max_digits=15, decimal_places=4)  # Field name made lowercase.
    ship_method = models.CharField(db_column='SHIP_METHOD', max_length=10)  # Field name made lowercase.
    total_weight = models.DecimalField(db_column='TOTAL_WEIGHT', max_digits=15, decimal_places=2)  # Field name made lowercase.
    cash_gl_acct = models.CharField(db_column='CASH_GL_ACCT', max_length=30)  # Field name made lowercase.
    line_pst_taxable = models.DecimalField(db_column='LINE_PST_TAXABLE', max_digits=19, decimal_places=4)  # Field name made lowercase.
    intent_to_edit = models.CharField(db_column='INTENT_TO_EDIT', max_length=80)  # Field name made lowercase.
    prepaid_invoice_reference_num = models.IntegerField(db_column='PREPAID_INVOICE_REFERENCE_NUM')  # Field name made lowercase.
    auto_calc_freight = models.BooleanField(db_column='AUTO_CALC_FREIGHT')  # Field name made lowercase.
    co_id = models.CharField(db_column='CO_ID', max_length=10)  # Field name made lowercase.
    co_member_type = models.CharField(db_column='CO_MEMBER_TYPE', max_length=5)  # Field name made lowercase.
    email = models.CharField(db_column='EMAIL', max_length=100)  # Field name made lowercase.
    crrt = models.CharField(db_column='CRRT', max_length=40)  # Field name made lowercase.
    address_status = models.CharField(db_column='ADDRESS_STATUS', max_length=5)  # Field name made lowercase.
    recognized_cash_amount = models.DecimalField(db_column='RECOGNIZED_CASH_AMOUNT', max_digits=19, decimal_places=4)  # Field name made lowercase.
    is_fr_order = models.SmallIntegerField(db_column='IS_FR_ORDER')  # Field name made lowercase.
    vat_tax_code_fh = models.CharField(db_column='VAT_TAX_CODE_FH', max_length=31, blank=True, null=True)  # Field name made lowercase.
    encrypt_pay_number = models.CharField(db_column='ENCRYPT_PAY_NUMBER', max_length=100)  # Field name made lowercase.
    encrypt_credit_card_expires = models.CharField(db_column='ENCRYPT_CREDIT_CARD_EXPIRES', max_length=100)  # Field name made lowercase.
    auto_freight_type = models.SmallIntegerField(db_column='AUTO_FREIGHT_TYPE')  # Field name made lowercase.
    use_member_price = models.BooleanField(db_column='USE_MEMBER_PRICE')  # Field name made lowercase.
    st_print_company = models.BooleanField(db_column='ST_PRINT_COMPANY')  # Field name made lowercase.
    st_print_title = models.BooleanField(db_column='ST_PRINT_TITLE')  # Field name made lowercase.
    toll_free = models.CharField(db_column='TOLL_FREE', max_length=25)  # Field name made lowercase.
    mail_code = models.CharField(db_column='MAIL_CODE', max_length=5)  # Field name made lowercase.
    address_3 = models.CharField(db_column='ADDRESS_3', max_length=40)  # Field name made lowercase.
    encrypt_csc = models.CharField(db_column='ENCRYPT_CSC', max_length=100)  # Field name made lowercase.
    issue_date = models.CharField(db_column='ISSUE_DATE', max_length=10)  # Field name made lowercase.
    issue_number = models.CharField(db_column='ISSUE_NUMBER', max_length=2)  # Field name made lowercase.
    more_payments = models.DecimalField(db_column='MORE_PAYMENTS', max_digits=15, decimal_places=2)  # Field name made lowercase.
    gateway_ref = models.CharField(db_column='GATEWAY_REF', max_length=100)  # Field name made lowercase.
    originating_trans_num = models.IntegerField(db_column='ORIGINATING_TRANS_NUM')  # Field name made lowercase.
    freight_tax = models.DecimalField(db_column='FREIGHT_TAX', max_digits=19, decimal_places=4)  # Field name made lowercase.
    handling_tax = models.DecimalField(db_column='HANDLING_TAX', max_digits=19, decimal_places=4)  # Field name made lowercase.
    tax_rate_fh = models.DecimalField(db_column='TAX_RATE_FH', max_digits=15, decimal_places=4)  # Field name made lowercase.
    discount_code = models.CharField(db_column='DISCOUNT_CODE', max_length=50)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Orders'

class Invoice(models.Model):
    bt_id = models.CharField(db_column='BT_ID', max_length=10)  # Field name made lowercase.
    st_id = models.CharField(db_column='ST_ID', max_length=10)  # Field name made lowercase.
    reference_num = models.IntegerField(db_column='REFERENCE_NUM', primary_key=True)  # Field name made lowercase.
    invoice_num = models.IntegerField(db_column='INVOICE_NUM')  # Field name made lowercase.
    invoice_date = models.DateTimeField(db_column='INVOICE_DATE', blank=True, null=True)  # Field name made lowercase.
    customer_name = models.CharField(db_column='CUSTOMER_NAME', max_length=60)  # Field name made lowercase.
    effective_date = models.DateTimeField(db_column='EFFECTIVE_DATE', blank=True, null=True)  # Field name made lowercase.
    org_code = models.CharField(db_column='ORG_CODE', max_length=5)  # Field name made lowercase.
    invoice_type = models.CharField(db_column='INVOICE_TYPE', max_length=5)  # Field name made lowercase.
    source_system = models.CharField(db_column='SOURCE_SYSTEM', max_length=10)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=255)  # Field name made lowercase.
    customer_reference = models.CharField(db_column='CUSTOMER_REFERENCE', max_length=40)  # Field name made lowercase.
    charges = models.DecimalField(db_column='CHARGES', max_digits=19, decimal_places=4)  # Field name made lowercase.
    credits = models.DecimalField(db_column='CREDITS', max_digits=19, decimal_places=4)  # Field name made lowercase.
    balance = models.DecimalField(db_column='BALANCE', max_digits=19, decimal_places=4)  # Field name made lowercase.
    num_lines = models.IntegerField(db_column='NUM_LINES')  # Field name made lowercase.
    terms_code = models.CharField(db_column='TERMS_CODE', max_length=5)  # Field name made lowercase.
    due_date = models.DateTimeField(db_column='DUE_DATE', blank=True, null=True)  # Field name made lowercase.
    discount_date = models.DateTimeField(db_column='DISCOUNT_DATE', blank=True, null=True)  # Field name made lowercase.
    available_disc = models.DecimalField(db_column='AVAILABLE_DISC', max_digits=19, decimal_places=4)  # Field name made lowercase.
    credit_status = models.CharField(db_column='CREDIT_STATUS', max_length=5)  # Field name made lowercase.
    ar_account = models.CharField(db_column='AR_ACCOUNT', max_length=50)  # Field name made lowercase.
    note = models.CharField(db_column='NOTE', max_length=255)  # Field name made lowercase.
    source_code = models.CharField(db_column='SOURCE_CODE', max_length=40)  # Field name made lowercase.
    batch_num = models.CharField(db_column='BATCH_NUM', max_length=15)  # Field name made lowercase.
    install_bill_date = models.DateTimeField(db_column='INSTALL_BILL_DATE', blank=True, null=True)  # Field name made lowercase.
    originating_trans_num = models.IntegerField(db_column='ORIGINATING_TRANS_NUM')  # Field name made lowercase.
    has_been_billed = models.BooleanField(db_column='HAS_BEEN_BILLED')  # Field name made lowercase.
    bill_to_cc = models.BooleanField(db_column='BILL_TO_CC')  # Field name made lowercase.
    is_multi_org = models.BooleanField(db_column='IS_MULTI_ORG')  # Field name made lowercase.
    adjustments = models.DecimalField(db_column='ADJUSTMENTS', max_digits=19, decimal_places=4)  # Field name made lowercase.
    time_stamp = models.TextField(db_column='TIME_STAMP', blank=True, null=True)  # Field name made lowercase. This field type is a guess.

    class Meta:
        managed = False
        db_table = 'Invoice'


class OrgDemographics(models.Model):

    id = models.CharField(db_column='ID', max_length=10, primary_key=True)
    pas_code = models.CharField(db_column='PAS_CODE', max_length=15, blank=True)
    org_type = models.CharField(db_column='ORG_TYPE', max_length=60, null=True, blank=True)
    population = models.CharField(db_column='POPULATION', max_length=10, null=True, blank=True)
    annual_budget = models.CharField(db_column='ANNUAL_BUDGET', max_length=10, null=True, blank=True)
    staff_size = models.CharField(db_column='STAFF_SIZE', max_length=10, null=True, blank=True)
    parent_id = models.CharField(db_column='PARENT_ID', max_length=9, null=True, blank=True)
    top_city = models.BooleanField(db_column='TOP_CITY', default=False)
    top_county = models.BooleanField(db_column='TOP_COUNTY', default=False)
    planning_function = models.BooleanField(db_column='PLANNING_FUNCTION', default=False)
    school_program_type = models.CharField(
        db_column='SCHOOL_PROGRAM_TYPE',
        max_length=10,
        null=True,
        blank=True
    )

    class Meta:
        managed = False
        db_table = 'ORG_Demographics'


class Relationship(models.Model):
    id = models.CharField(db_column='ID', max_length=10)  # Field name made lowercase.
    relation_type = models.CharField(db_column='RELATION_TYPE', max_length=10)  # Field name made lowercase.
    target_id = models.CharField(db_column='TARGET_ID', max_length=10)  # Field name made lowercase.
    target_name = models.CharField(db_column='TARGET_NAME', max_length=60)  # Field name made lowercase.
    target_relation_type = models.CharField(db_column='TARGET_RELATION_TYPE',
                                            max_length=10)  # Field name made lowercase.
    title = models.CharField(db_column='TITLE', max_length=80)  # Field name made lowercase.
    functional_title = models.CharField(db_column='FUNCTIONAL_TITLE',
                                        max_length=50)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=5)  # Field name made lowercase.
    effective_date = models.DateTimeField(db_column='EFFECTIVE_DATE', blank=True,
                                          null=True)  # Field name made lowercase.
    thru_date = models.DateTimeField(db_column='THRU_DATE', blank=True, null=True)  # Field name made lowercase.
    note = models.TextField(db_column='NOTE', blank=True,
                            null=True)  # Field name made lowercase. This field type is a guess.
    last_string = models.CharField(db_column='LAST_STRING', max_length=255)  # Field name made lowercase.
    date_added = models.DateTimeField(db_column='DATE_ADDED', blank=True,
                                      null=True)  # Field name made lowercase.
    last_updated = models.DateTimeField(db_column='LAST_UPDATED', blank=True,
                                        null=True)  # Field name made lowercase.
    updated_by = models.CharField(db_column='UPDATED_BY', max_length=60)  # Field name made lowercase.
    seqn = models.IntegerField(db_column='SEQN', primary_key=True)  # Field name made lowercase.
    group_code = models.CharField(db_column='GROUP_CODE', max_length=30)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Relationship'


class ZipCode(models.Model):
    zip = models.CharField(db_column='ZIP', primary_key=True, max_length=5)  # Field name made lowercase.
    city = models.CharField(db_column='CITY', max_length=40)  # Field name made lowercase.
    state = models.CharField(db_column='STATE', max_length=2)  # Field name made lowercase.
    zip_type = models.CharField(db_column='ZIP_TYPE', max_length=1)  # Field name made lowercase.
    county_fips = models.CharField(db_column='COUNTY_FIPS', max_length=5)  # Field name made lowercase.
    county = models.CharField(db_column='COUNTY', max_length=30)  # Field name made lowercase.
    area_code = models.CharField(db_column='AREA_CODE', max_length=3)  # Field name made lowercase.
    chapter = models.CharField(db_column='CHAPTER', max_length=15)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Zip_Code'


# class NameLog(models.Model):
    """
    Leave this commented out. Django complains about duplicate id fields (even though
    there don't appear to be any) and will raise an Exception wherever this module is imported
    """
#     date_time = models.DateTimeField(db_column='DATE_TIME')  # Field name made lowercase.
#     log_type = models.CharField(db_column='LOG_TYPE', max_length=10)  # Field name made lowercase.
#     sub_type = models.CharField(db_column='SUB_TYPE', max_length=10)  # Field name made lowercase.
#     user_id = models.CharField(db_column='USER_ID', max_length=60)  # Field name made lowercase.
#     id = models.CharField(db_column='ID', max_length=10)  # Field name made lowercase.
#     log_text = models.CharField(db_column='LOG_TEXT', max_length=8000)  # Field name made lowercase.
#     time_stamp = models.CharField(db_column='TIME_STAMP', max_length=100)
#
#     class Meta:
#         managed = False
#         db_table = 'Name_Log'
#         unique_together = (('time_stamp', 'date_time'),)


class NameFin(models.Model):
    id = models.CharField(db_column='ID', primary_key=True, max_length=10)  # Field name made lowercase.
    tax_exempt = models.CharField(db_column='TAX_EXEMPT', max_length=15)  # Field name made lowercase.
    credit_limit = models.DecimalField(db_column='CREDIT_LIMIT', max_digits=19, decimal_places=4)  # Field name made lowercase.
    no_statements = models.BooleanField(db_column='NO_STATEMENTS')  # Field name made lowercase.
    terms_code = models.CharField(db_column='TERMS_CODE', max_length=5)  # Field name made lowercase.
    backorders = models.SmallIntegerField(db_column='BACKORDERS')  # Field name made lowercase.
    renew_months = models.DecimalField(db_column='RENEW_MONTHS', max_digits=15, decimal_places=4)  # Field name made lowercase.
    renewed_thru = models.DateTimeField(db_column='RENEWED_THRU', blank=True, null=True)  # Field name made lowercase.
    bt_id = models.CharField(db_column='BT_ID', max_length=10)  # Field name made lowercase.
    tax_author_default = models.CharField(db_column='TAX_AUTHOR_DEFAULT', max_length=31)  # Field name made lowercase.
    use_vat_taxation = models.BooleanField(db_column='USE_VAT_TAXATION')  # Field name made lowercase.
    vat_reg_number = models.CharField(db_column='VAT_REG_NUMBER', max_length=20)  # Field name made lowercase.
    vat_country = models.CharField(db_column='VAT_COUNTRY', max_length=25)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Name_Fin'


class NamePicture(models.Model):
    id = models.CharField(db_column='ID', max_length=10)  # Field name made lowercase.
    picture_num = models.IntegerField(db_column='PICTURE_NUM', primary_key=True)  # Field name made lowercase.
    purpose = models.CharField(db_column='PURPOSE', max_length=20, blank=True, null=True)  # Field name made lowercase.
    picture_logo = models.BinaryField(db_column='PICTURE_LOGO', blank=True, null=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=255, blank=True, null=True)  # Field name made lowercase.
    date_added = models.DateTimeField(db_column='DATE_ADDED', blank=True, null=True)  # Field name made lowercase.
    last_updated = models.DateTimeField(db_column='LAST_UPDATED', blank=True, null=True)  # Field name made lowercase.
    updated_by = models.CharField(db_column='UPDATED_BY', max_length=60, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Name_Picture'


class NameSecurity(models.Model):
    id = models.CharField(db_column='ID', primary_key=True, max_length=10)  # Field name made lowercase.
    login_disabled = models.BooleanField(db_column='LOGIN_DISABLED', default=0)  # Field name made lowercase.
    web_login = models.CharField(db_column='WEB_LOGIN', max_length=60, default='')  # Field name made lowercase.
    password = models.CharField(db_column='PASSWORD', max_length=100, default='')  # Field name made lowercase.
    expiration_date = models.DateTimeField(db_column='EXPIRATION_DATE', blank=True, null=True)  # Field name made lowercase.
    last_login = models.DateTimeField(db_column='LAST_LOGIN', blank=True, null=True)  # Field name made lowercase.
    previous_login = models.DateTimeField(db_column='PREVIOUS_LOGIN', blank=True, null=True)  # Field name made lowercase.
    # contactid = models.CharField(db_column='ContactID', max_length=10)  # Field name made lowercase.
    updated_by = models.CharField(db_column='UPDATED_BY', max_length=60)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Name_Security'


# class NameSecurityGroups(models.Model):
    """
    Leave this commented out. Django complains about duplicate id fields (even though
    there don't appear to be any) and will raise an Exception wherever this module is imported
    """
#     id = models.CharField(db_column='ID', max_length=10)  # Field name made lowercase.
#     security_group = models.CharField(db_column='SECURITY_GROUP', max_length=30)  # Field name made lowercase.
#
#     class Meta:
#         managed = False
#         db_table = 'Name_Security_Groups'
#         unique_together = (('id', 'security_group'),)


class OrderLines(models.Model):
    order_number = models.DecimalField(db_column='ORDER_NUMBER', max_digits=15, decimal_places=2, primary_key=True)  # Field name made lowercase.
    line_number = models.DecimalField(db_column='LINE_NUMBER', max_digits=15, decimal_places=2)  # Field name made lowercase.
    product_code = models.CharField(db_column='PRODUCT_CODE', max_length=31)  # Field name made lowercase.
    location = models.CharField(db_column='LOCATION', max_length=10)  # Field name made lowercase.
    lot_serial = models.CharField(db_column='LOT_SERIAL', max_length=20)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=255)  # Field name made lowercase.
    quantity_ordered = models.DecimalField(db_column='QUANTITY_ORDERED', max_digits=15, decimal_places=6)  # Field name made lowercase.
    quantity_shipped = models.DecimalField(db_column='QUANTITY_SHIPPED', max_digits=15, decimal_places=6)  # Field name made lowercase.
    quantity_backordered = models.DecimalField(db_column='QUANTITY_BACKORDERED', max_digits=15, decimal_places=6)  # Field name made lowercase.
    quantity_reserved = models.DecimalField(db_column='QUANTITY_RESERVED', max_digits=15, decimal_places=6)  # Field name made lowercase.
    quantity_committed = models.DecimalField(db_column='QUANTITY_COMMITTED', max_digits=15, decimal_places=6)  # Field name made lowercase.
    number_days = models.IntegerField(db_column='NUMBER_DAYS')  # Field name made lowercase.
    taxable = models.BooleanField(db_column='TAXABLE')  # Field name made lowercase.
    taxable_2 = models.BooleanField(db_column='TAXABLE_2')  # Field name made lowercase.
    unit_price = models.DecimalField(db_column='UNIT_PRICE', max_digits=19, decimal_places=4)  # Field name made lowercase.
    unit_cost = models.DecimalField(db_column='UNIT_COST', max_digits=19, decimal_places=4)  # Field name made lowercase.
    undiscounted_price = models.DecimalField(db_column='UNDISCOUNTED_PRICE', max_digits=19, decimal_places=4)  # Field name made lowercase.
    extended_amount = models.DecimalField(db_column='EXTENDED_AMOUNT', max_digits=19, decimal_places=4)  # Field name made lowercase.
    extended_cost = models.DecimalField(db_column='EXTENDED_COST', max_digits=19, decimal_places=4)  # Field name made lowercase.
    undiscounted_extended_amount = models.DecimalField(db_column='UNDISCOUNTED_EXTENDED_AMOUNT', max_digits=19, decimal_places=4)  # Field name made lowercase.
    cancel_code = models.CharField(db_column='CANCEL_CODE', max_length=10)  # Field name made lowercase.
    cancel_quantity = models.DecimalField(db_column='CANCEL_QUANTITY', max_digits=15, decimal_places=6)  # Field name made lowercase.
    commission_rate = models.DecimalField(db_column='COMMISSION_RATE', max_digits=15, decimal_places=4)  # Field name made lowercase.
    commission_amount = models.DecimalField(db_column='COMMISSION_AMOUNT', max_digits=19, decimal_places=4)  # Field name made lowercase.
    ceu_type = models.CharField(db_column='CEU_TYPE', max_length=15)  # Field name made lowercase.
    ceu_awarded = models.DecimalField(db_column='CEU_AWARDED', max_digits=15, decimal_places=2)  # Field name made lowercase.
    pass_fail = models.CharField(db_column='PASS_FAIL', max_length=5)  # Field name made lowercase.
    date_confirmed = models.DateTimeField(db_column='DATE_CONFIRMED', blank=True, null=True)  # Field name made lowercase.
    tickets_printed = models.IntegerField(db_column='TICKETS_PRINTED')  # Field name made lowercase.
    booth_numbers = models.CharField(db_column='BOOTH_NUMBERS', max_length=255)  # Field name made lowercase.
    note = models.CharField(db_column='NOTE', max_length=255, blank=True, null=True)  # Field name made lowercase.
    income_account = models.CharField(db_column='INCOME_ACCOUNT', max_length=50)  # Field name made lowercase.
    unit_weight = models.DecimalField(db_column='UNIT_WEIGHT', max_digits=15, decimal_places=2)  # Field name made lowercase.
    extended_weight = models.DecimalField(db_column='EXTENDED_WEIGHT', max_digits=15, decimal_places=2)  # Field name made lowercase.
    pst_taxable = models.BooleanField(db_column='PST_TAXABLE')  # Field name made lowercase.
    is_gst_taxable = models.BooleanField(db_column='IS_GST_TAXABLE')  # Field name made lowercase.
    added_to_wait_list = models.DateTimeField(db_column='ADDED_TO_WAIT_LIST', blank=True, null=True)  # Field name made lowercase.
    bin = models.CharField(db_column='BIN', max_length=10)  # Field name made lowercase.
    tax_authority = models.CharField(db_column='TAX_AUTHORITY', max_length=15)  # Field name made lowercase.
    tax_rate = models.DecimalField(db_column='TAX_RATE', max_digits=15, decimal_places=4)  # Field name made lowercase.
    tax_1 = models.DecimalField(db_column='TAX_1', max_digits=15, decimal_places=4)  # Field name made lowercase.
    kit_item_type = models.SmallIntegerField(db_column='KIT_ITEM_TYPE')  # Field name made lowercase.
    discount = models.DecimalField(db_column='DISCOUNT', max_digits=15, decimal_places=2)  # Field name made lowercase.
    uf_1 = models.CharField(db_column='UF_1', max_length=30)  # Field name made lowercase.
    uf_2 = models.CharField(db_column='UF_2', max_length=30)  # Field name made lowercase.
    uf_3 = models.CharField(db_column='UF_3', max_length=30)  # Field name made lowercase.
    uf_4 = models.CharField(db_column='UF_4', max_length=30)  # Field name made lowercase.
    extended_square_feet = models.DecimalField(db_column='EXTENDED_SQUARE_FEET', max_digits=15, decimal_places=2)  # Field name made lowercase.
    square_feet = models.DecimalField(db_column='SQUARE_FEET', max_digits=15, decimal_places=2)  # Field name made lowercase.
    meet_appeal = models.CharField(db_column='MEET_APPEAL', max_length=40)  # Field name made lowercase.
    meet_campaign = models.CharField(db_column='MEET_CAMPAIGN', max_length=10)  # Field name made lowercase.
    fair_market_value = models.DecimalField(db_column='FAIR_MARKET_VALUE', max_digits=15, decimal_places=2)  # Field name made lowercase.
    org_code = models.CharField(db_column='ORG_CODE', max_length=5)  # Field name made lowercase.
    is_fr_item = models.BooleanField(db_column='IS_FR_ITEM')  # Field name made lowercase.
    manual_price = models.DecimalField(db_column='MANUAL_PRICE', max_digits=15, decimal_places=2)  # Field name made lowercase.
    is_manual_price = models.BooleanField(db_column='IS_MANUAL_PRICE')  # Field name made lowercase.
    unit_tax_amount = models.DecimalField(db_column='UNIT_TAX_AMOUNT', max_digits=15, decimal_places=4)  # Field name made lowercase.
    price_from_components = models.BooleanField(db_column='PRICE_FROM_COMPONENTS')  # Field name made lowercase.
    quantity_per_kit = models.DecimalField(db_column='QUANTITY_PER_KIT', max_digits=15, decimal_places=6)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Order_Lines'
        unique_together = (('order_number', 'line_number'),)

class EventFunction(models.Model):
    event_id = models.CharField(db_column='EventId', max_length=15)
    event_function_id = models.CharField(db_column='EventFunctionId', max_length=31, primary_key=True)
    name = models.CharField(db_column='Name', max_length=60)
    description = models.TextField(db_column='Description', max_length=2147483647)
    code = models.CharField(db_column='Code', max_length=15)
    image_url = models.CharField(db_column='ImageURL', max_length=100)
    additional_description = models.TextField(db_column='AdditionalDescription', max_length=2147483647)
    financial_entity_id = models.CharField(db_column='FinancialEntityId', max_length=5)
    category_id = models.CharField(db_column='CategoryId', max_length=5)
    category_name = models.CharField(db_column='CategoryName', max_length=5)
    status = models.CharField(db_column='Status', max_length=50)
    start_date_time = models.DateTimeField(db_column='StartDateTime')
    end_date_time = models.DateTimeField(db_column='EndDateTime')
    facility_name = models.CharField(db_column='FacilityName', max_length=100)
    event_function_registration_type_code = models.IntegerField(db_column='EventFunctionRegistrationTypeCode')
    event_track = models.CharField(db_column='EventTrack', max_length=255)
    sort_order = models.IntegerField(db_column='SortOrder')
    event_category = models.CharField(db_column='EventCategory', max_length=255)
    is_event_registration_option = models.IntegerField(db_column='IsEventRegistrationOption')
    capacity = models.IntegerField(db_column='Capacity')
    max_quantity_per_registrant = models.IntegerField(db_column='MaxQuantityPerRegistrant')
    conflict_codes = models.CharField(db_column='ConflictCodes', max_length=10)
    form_definition_section_key = models.CharField(db_column='FormDefinitionSectionKey', max_length=36)
    available_to = models.IntegerField(db_column='AvailableTo')
    is_fund_raising_item = models.IntegerField(db_column='IsFundRaisingItem')

    def tickets_sold(self):
        return CustomEventSchedule.objects.filter(
            product_code=self.event_function_id,
            status='A'
        ).count()

    def soldout(self):
        max_tickets = int(self.capacity)
        tickets_sold = self.tickets_sold()
        return tickets_sold >= max_tickets

    def total_user_tickets(self, user_id):
        return CustomEventSchedule.objects.filter(
            id=user_id,
            product_code=self.event_function_id,
        ).count()

    def remaining_tickets_for_user(self, user_id):
        tickets_remaining = int(self.capacity) - self.tickets_sold()
        tickets_by_user = self.total_user_tickets(user_id)
        user_tickets_remaining = int(self.max_quantity_per_registrant) - tickets_by_user
        return (
            tickets_remaining if tickets_remaining < user_tickets_remaining else
            user_tickets_remaining
        )

    def tickets_in_cart(self, user_id):
        return CustomEventSchedule.objects.filter(
            id=user_id,
            product_code=self.event_function_id,
            status='I'
        ).count()

    def tickets_purchased(self, user_id):
        return CustomEventSchedule.objects.filter(
            id=user_id,
            product_code=self.event_function_id,
            status='A'
        ).count()

    class Meta:
        managed = False
        db_table = 'vSoaEventFunction'

class MeetMaster(models.Model):
    meeting = models.CharField(db_column='MEETING', primary_key=True, max_length=10)  # Field name made lowercase.
    title = models.CharField(db_column='TITLE', max_length=60, default='')  # Field name made lowercase.
    meeting_type = models.CharField(db_column='MEETING_TYPE', max_length=5, default='')  # Field name made lowercase.
    description = models.TextField(db_column='DESCRIPTION', blank=True, null=True, default='')  # Field name made lowercase. This field type is a guess.
    begin_date = models.DateTimeField(db_column='BEGIN_DATE', blank=True, null=True)  # Field name made lowercase.
    end_date = models.DateTimeField(db_column='END_DATE', blank=True, null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1)  # Field name made lowercase.
    address_1 = models.CharField(db_column='ADDRESS_1', max_length=50, default='')  # Field name made lowercase.
    address_2 = models.CharField(db_column='ADDRESS_2', max_length=50, default='')  # Field name made lowercase.
    address_3 = models.CharField(db_column='ADDRESS_3', max_length=50, default='')  # Field name made lowercase.
    city = models.CharField(db_column='CITY', max_length=40, default='')  # Field name made lowercase.
    state_province = models.CharField(db_column='STATE_PROVINCE', max_length=15, default='')  # Field name made lowercase.
    zip = models.CharField(db_column='ZIP', max_length=10, default='')  # Field name made lowercase.
    country = models.CharField(db_column='COUNTRY', max_length=25, default='')  # Field name made lowercase.
    directions = models.TextField(db_column='DIRECTIONS', blank=True, null=True, default='')  # Field name made lowercase. This field type is a guess.
    coordinators = models.CharField(db_column='COORDINATORS', max_length=200)  # Field name made lowercase.
    notes = models.TextField(db_column='NOTES', blank=True, null=True, default='')  # Field name made lowercase. This field type is a guess.
    allow_reg_string = models.TextField(db_column='ALLOW_REG_STRING', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    early_cutoff = models.DateTimeField(db_column='EARLY_CUTOFF', blank=True, null=True)  # Field name made lowercase.
    reg_cutoff = models.DateTimeField(db_column='REG_CUTOFF', blank=True, null=True)  # Field name made lowercase.
    late_cutoff = models.DateTimeField(db_column='LATE_CUTOFF', blank=True, null=True)  # Field name made lowercase.
    org_code = models.CharField(db_column='ORG_CODE', max_length=5, default='MTG')  # Field name made lowercase.
    logo = models.BinaryField(db_column='LOGO', blank=True, null=True)  # Field name made lowercase.
    max_registrants = models.IntegerField(db_column='MAX_REGISTRANTS', default=0)  # Field name made lowercase.
    total_registrants = models.IntegerField(db_column='TOTAL_REGISTRANTS', default=0)  # Field name made lowercase.
    total_cancelations = models.IntegerField(db_column='TOTAL_CANCELATIONS', default=0)  # Field name made lowercase.
    total_revenue = models.DecimalField(db_column='TOTAL_REVENUE', max_digits=15, decimal_places=2, default=0)  # Field name made lowercase.
    head_count = models.IntegerField(db_column='HEAD_COUNT', default=0)  # Field name made lowercase.
    tax_authority_1 = models.CharField(db_column='TAX_AUTHORITY_1', max_length=20, default=0)  # Field name made lowercase.
    suppress_coor = models.BooleanField(db_column='SUPPRESS_COOR', default=0)  # Field name made lowercase.
    suppress_dir = models.BooleanField(db_column='SUPPRESS_DIR', default=0)  # Field name made lowercase.
    suppress_notes = models.BooleanField(db_column='SUPPRESS_NOTES', default=0)  # Field name made lowercase.
    muf_1 = models.CharField(db_column='MUF_1', max_length=100, default='')  # Field name made lowercase.
    muf_2 = models.CharField(db_column='MUF_2', max_length=100, default='')  # Field name made lowercase.
    muf_3 = models.CharField(db_column='MUF_3', max_length=100, default='')  # Field name made lowercase.
    muf_4 = models.CharField(db_column='MUF_4', max_length=100, default='')  # Field name made lowercase.
    muf_5 = models.CharField(db_column='MUF_5', max_length=100, default='')  # Field name made lowercase.
    muf_6 = models.CharField(db_column='MUF_6', max_length=100, default='')  # Field name made lowercase.
    muf_7 = models.CharField(db_column='MUF_7', max_length=100, default='')  # Field name made lowercase.
    muf_8 = models.CharField(db_column='MUF_8', max_length=100, default='')  # Field name made lowercase.
    muf_9 = models.CharField(db_column='MUF_9', max_length=100, default='')  # Field name made lowercase.
    muf_10 = models.CharField(db_column='MUF_10', max_length=100)  # Field name made lowercase.
    intent_to_edit = models.CharField(db_column='INTENT_TO_EDIT', max_length=80)  # Field name made lowercase.
    suppress_confirm = models.BooleanField(db_column='SUPPRESS_CONFIRM', default=0)  # Field name made lowercase.
    web_view_only = models.BooleanField(db_column='WEB_VIEW_ONLY', default=0)  # Field name made lowercase.
    web_enabled = models.BooleanField(db_column='WEB_ENABLED', default=1)  # Field name made lowercase.
    post_registration = models.BooleanField(db_column='POST_REGISTRATION', default=1)  # Field name made lowercase.
    email_registration = models.BooleanField(db_column='EMAIL_REGISTRATION', default=0)  # Field name made lowercase.
    meeting_url = models.CharField(db_column='MEETING_URL', max_length=255, default='')  # Field name made lowercase.
    meeting_image_name = models.CharField(db_column='MEETING_IMAGE_NAME', max_length=255, default='')  # Field name made lowercase.
    contact_id = models.CharField(db_column='CONTACT_ID', max_length=10)  # Field name made lowercase.
    is_fr_meet = models.SmallIntegerField(db_column='IS_FR_MEET', default=0)  # Field name made lowercase.
    meet_appeal = models.CharField(db_column='MEET_APPEAL', max_length=40, default='')  # Field name made lowercase.
    meet_campaign = models.CharField(db_column='MEET_CAMPAIGN', max_length=10, default='')  # Field name made lowercase.
    meet_category = models.SmallIntegerField(db_column='MEET_CATEGORY', default=0)  # Field name made lowercase.
    comp_reg_reg_class = models.CharField(db_column='COMP_REG_REG_CLASS', max_length=100, blank=True, null=True)  # Field name made lowercase.
    comp_reg_calculation = models.TextField(db_column='COMP_REG_CALCULATION', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    square_foot_rules = models.TextField(db_column='SQUARE_FOOT_RULES', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    tax_by_address = models.BooleanField(db_column='TAX_BY_ADDRESS', default=0)  # Field name made lowercase.
    vat_ruleset = models.CharField(db_column='VAT_RULESET', max_length=10, default='')  # Field name made lowercase.
    reg_class_stored_proc = models.CharField(db_column='REG_CLASS_STORED_PROC', max_length=100, default='')  # Field name made lowercase.
    web_reg_class_method = models.IntegerField(db_column='WEB_REG_CLASS_METHOD', default=0)  # Field name made lowercase.
    reg_others = models.BooleanField(db_column='REG_OTHERS', default=0)  # Field name made lowercase.
    add_guests = models.BooleanField(db_column='ADD_GUESTS', default=0)  # Field name made lowercase.
    web_desc = models.TextField(db_column='WEB_DESC', blank=True, null=True, default='')  # Field name made lowercase. This field type is a guess.
    allow_reg_edit = models.BooleanField(db_column='ALLOW_REG_EDIT', default=0)  # Field name made lowercase.
    reg_edit_cutoff = models.DateTimeField(db_column='REG_EDIT_CUTOFF', blank=True, null=True)  # Field name made lowercase.
    form_definition_id = models.CharField(db_column='FORM_DEFINITION_ID', max_length=36, default='')  # Field name made lowercase.
    form_definition_section_id = models.CharField(db_column='FORM_DEFINITION_SECTION_ID', max_length=36, default='')  # Field name made lowercase.
    publish_start_date = models.DateTimeField(db_column='PUBLISH_START_DATE', blank=True, null=True)  # Field name made lowercase.
    publish_end_date = models.DateTimeField(db_column='PUBLISH_END_DATE', blank=True, null=True)  # Field name made lowercase.
    registration_start_date = models.DateTimeField(db_column='REGISTRATION_START_DATE', blank=True, null=True)  # Field name made lowercase.
    registration_end_date = models.DateTimeField(db_column='REGISTRATION_END_DATE', blank=True, null=True)  # Field name made lowercase.
    registration_closed_message = models.CharField(db_column='REGISTRATION_CLOSED_MESSAGE', max_length=400, blank=True, null=True, default='Registration is now closed.')  # Field name made lowercase.
    default_programitem_displaymode = models.IntegerField(db_column='DEFAULT_PROGRAMITEM_DISPLAYMODE', default=0)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Meet_Master'

    @classmethod
    def create_event(cls, event):
        """
        Creates or updates the meet master record for the EVENT_REGISTRATION product type
        """
        meeting, created = cls.objects.get_or_create(meeting=event.product.imis_code)

        cls.objects.filter(meeting=event.product.imis_code).update(
        meeting = event.product.imis_code,
        title = event.title[:60],
        meeting_type = 'REG', # THIS IS THE ONLY MEETING TYPE THAT EXISTS IN IMIS.
        description = event.description,
        begin_date = event.imis_begin_time,
        end_date = event.imis_end_time,
        status = event.status,
        city = event.city if event.city else '',
        state_province = event.state if event.state else '',
        zip = '', #address zip field not used in django for event... but we could
        country = '', #event.country if event.country is not None else event.country,
        early_cutoff = event.price_early_cutoff_time,
        reg_cutoff = event.price_regular_cutoff_time,
        late_cutoff = event.price_late_cutoff_time,
        max_registrants = event.product.max_quantity if event.product.max_quantity else 0,
        registration_start_date = event.registration_begin_time,
        registration_end_date = event.imis_end_time
        )

class ProductFunction(models.Model):
    product_code = models.CharField(db_column='PRODUCT_CODE', primary_key=True, max_length=31)  # Field name made lowercase.
    function_type = models.CharField(db_column='FUNCTION_TYPE', max_length=5)  # Field name made lowercase.
    begin_date_time = models.DateTimeField(db_column='BEGIN_DATE_TIME', blank=True, null=True)  # Field name made lowercase.
    end_date_time = models.DateTimeField(db_column='END_DATE_TIME', blank=True, null=True)  # Field name made lowercase.
    seq = models.IntegerField(db_column='SEQ', default=0)  # Field name made lowercase.
    minimum_attendance = models.IntegerField(db_column='MINIMUM_ATTENDANCE', default=0)  # Field name made lowercase.
    expected_attendance = models.IntegerField(db_column='EXPECTED_ATTENDANCE', default=0)  # Field name made lowercase.
    guaranteed_attendance = models.IntegerField(db_column='GUARANTEED_ATTENDANCE', default=0)  # Field name made lowercase.
    actual_attendance = models.IntegerField(db_column='ACTUAL_ATTENDANCE', default=0)  # Field name made lowercase.
    settings = models.IntegerField(db_column='SETTINGS', default=0)  # Field name made lowercase.
    setup_date_time = models.DateTimeField(db_column='SETUP_DATE_TIME', blank=True, null=True)  # Field name made lowercase.
    post_date_time = models.DateTimeField(db_column='POST_DATE_TIME', blank=True, null=True)  # Field name made lowercase.
    auto_enroll = models.BooleanField(db_column='AUTO_ENROLL', default=0)  # Field name made lowercase.
    print_ticket = models.BooleanField(db_column='PRINT_TICKET', default=0)  # Field name made lowercase.
    last_ticket = models.IntegerField(db_column='LAST_TICKET', default=0)  # Field name made lowercase.
    ceu_type = models.CharField(db_column='CEU_TYPE', max_length=15, default='')  # Field name made lowercase.
    ceu_amount = models.DecimalField(db_column='CEU_AMOUNT', max_digits=15, decimal_places=2, default=0)  # Field name made lowercase.
    course_code = models.CharField(db_column='COURSE_CODE', max_length=15, default='')  # Field name made lowercase.
    other_tickets = models.CharField(db_column='OTHER_TICKETS', max_length=255, default='')  # Field name made lowercase.
    ceu_entered = models.BooleanField(db_column='CEU_ENTERED', default=0)  # Field name made lowercase.
    maximum_attendance = models.IntegerField(db_column='MAXIMUM_ATTENDANCE', default=0)  # Field name made lowercase.
    parent = models.BooleanField(db_column='PARENT', default=0)  # Field name made lowercase.
    conflict_code = models.CharField(db_column='CONFLICT_CODE', max_length=10, default='')  # Field name made lowercase.
    web_enabled = models.BooleanField(db_column='WEB_ENABLED', default=1)  # Field name made lowercase.
    web_multi_reg = models.SmallIntegerField(db_column='WEB_MULTI_REG', default=0)  # Field name made lowercase.
    square_feet = models.DecimalField(db_column='SQUARE_FEET', max_digits=15, decimal_places=2, blank=True, null=True, default=0)  # Field name made lowercase.
    is_fr_item = models.BooleanField(db_column='IS_FR_ITEM', default=0)  # Field name made lowercase.
    is_guest_function = models.BooleanField(db_column='IS_GUEST_FUNCTION', default=0)  # Field name made lowercase.
    create_detail_activity = models.BooleanField(db_column='CREATE_DETAIL_ACTIVITY', default=0)  # Field name made lowercase.
    event_track = models.CharField(db_column='EVENT_TRACK', max_length=255, default='')  # Field name made lowercase.
    event_category = models.CharField(db_column='EVENT_CATEGORY', max_length=255, default='')  # Field name made lowercase.
    is_event_registration_option = models.BooleanField(db_column='IS_EVENT_REGISTRATION_OPTION', default=0)  # Field name made lowercase.
    form_definition_section_id = models.CharField(db_column='FORM_DEFINITION_SECTION_ID', max_length=36, default='')  # Field name made lowercase.
    available_to = models.IntegerField(db_column='AVAILABLE_TO', default=0)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Product_Function'

    @classmethod
    def create_event(cls, event, product_code, option=None):

        product_function, created = cls.objects.get_or_create(product_code=product_code)
        maximum_attendance = 0
        max_quantity_per_person = 1

        if hasattr(event, "product") and event.product:

            max_quantity_per_person = event.product.max_quantity_per_person or 0
            maximum_attendance = event.product.max_quantity
            maximum_attendance = 0 if not maximum_attendance else maximum_attendance

        cls.objects.filter(product_code = product_code).update(
            function_type = 'REG' if hasattr(event, "product") and event.product else 'MEMO', # IF PRODUCT, THIS IS A REGISTRATION. OTHERWISE, THIS IS A NON-TICKETED ITEM.
            begin_date_time = event.imis_begin_time,
            end_date_time = event.imis_end_time,
            web_multi_reg = max_quantity_per_person,
            is_event_registration_option = 1 if option else 0, # RIGHT NOW EACH DJANGO OPTION IS AN EVENT OPTION
            print_ticket = 1 if hasattr(event, "product") and event.product and not option else 0 ,
            maximum_attendance = maximum_attendance
            )

class ProductPrice(models.Model):
    rule_type = models.CharField(db_column='RULE_TYPE', max_length=2)  # Field name made lowercase.
    prod_type = models.CharField(db_column='PROD_TYPE', max_length=5)  # Field name made lowercase.
    product_code = models.CharField(db_column='PRODUCT_CODE', max_length=31, primary_key=True)  # Field name made lowercase.
    customer_type = models.CharField(db_column='CUSTOMER_TYPE', max_length=11)  # Field name made lowercase.
    customer_id = models.CharField(db_column='CUSTOMER_ID', max_length=10)  # Field name made lowercase.
    begin_date = models.DateTimeField(db_column='BEGIN_DATE', blank=True, null=True)  # Field name made lowercase.
    end_date = models.DateTimeField(db_column='END_DATE', blank=True, null=True)  # Field name made lowercase.
    rule_key = models.CharField(db_column='RULE_KEY', max_length=50)  # Field name made lowercase.
    rate_1 = models.DecimalField(db_column='RATE_1', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    rate_2 = models.DecimalField(db_column='RATE_2', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    rate_3 = models.DecimalField(db_column='RATE_3', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    rate_4 = models.DecimalField(db_column='RATE_4', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    rate_5 = models.DecimalField(db_column='RATE_5', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    rate_6 = models.DecimalField(db_column='RATE_6', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    rate_7 = models.DecimalField(db_column='RATE_7', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    rate_8 = models.DecimalField(db_column='RATE_8', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    rate_9 = models.DecimalField(db_column='RATE_9', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    rate_10 = models.DecimalField(db_column='RATE_10', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    rate_11 = models.DecimalField(db_column='RATE_11', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    rate_12 = models.DecimalField(db_column='RATE_12', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    rate_13 = models.DecimalField(db_column='RATE_13', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    rate_14 = models.DecimalField(db_column='RATE_14', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    rate_15 = models.DecimalField(db_column='RATE_15', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    rate_16 = models.DecimalField(db_column='RATE_16', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    rate_17 = models.DecimalField(db_column='RATE_17', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    rate_18 = models.DecimalField(db_column='RATE_18', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    rate_19 = models.DecimalField(db_column='RATE_19', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    rate_20 = models.DecimalField(db_column='RATE_20', max_digits=19, decimal_places=4, default=0)  # Field name made lowercase.
    step_1 = models.CharField(db_column='STEP_1', max_length=15, default='')  # Field name made lowercase.
    step_2 = models.CharField(db_column='STEP_2', max_length=15, default='')  # Field name made lowercase.
    step_3 = models.CharField(db_column='STEP_3', max_length=15, default='')  # Field name made lowercase.
    step_4 = models.CharField(db_column='STEP_4', max_length=15, default='')  # Field name made lowercase.
    step_5 = models.CharField(db_column='STEP_5', max_length=15, default='')  # Field name made lowercase.
    step_6 = models.CharField(db_column='STEP_6', max_length=15, default='')  # Field name made lowercase.
    step_7 = models.CharField(db_column='STEP_7', max_length=15, default='')  # Field name made lowercase.
    step_8 = models.CharField(db_column='STEP_8', max_length=15, default='')  # Field name made lowercase.
    step_9 = models.CharField(db_column='STEP_9', max_length=15, default='')  # Field name made lowercase.
    step_10 = models.CharField(db_column='STEP_10', max_length=15, default='')  # Field name made lowercase.
    step_11 = models.CharField(db_column='STEP_11', max_length=15, default='')  # Field name made lowercase.
    step_12 = models.CharField(db_column='STEP_12', max_length=15, default='')  # Field name made lowercase.
    step_13 = models.CharField(db_column='STEP_13', max_length=15, default='')  # Field name made lowercase.
    step_14 = models.CharField(db_column='STEP_14', max_length=15, default='')  # Field name made lowercase.
    step_15 = models.CharField(db_column='STEP_15', max_length=15, default='')  # Field name made lowercase.
    step_16 = models.CharField(db_column='STEP_16', max_length=15, default='')  # Field name made lowercase.
    step_17 = models.CharField(db_column='STEP_17', max_length=15, default='')  # Field name made lowercase.
    step_18 = models.CharField(db_column='STEP_18', max_length=15, default='')  # Field name made lowercase.
    step_19 = models.CharField(db_column='STEP_19', max_length=15, default='')  # Field name made lowercase.
    step_20 = models.CharField(db_column='STEP_20', max_length=15, default='')  # Field name made lowercase.
    base_1 = models.CharField(db_column='BASE_1', max_length=255, default='')  # Field name made lowercase.
    base_2 = models.CharField(db_column='BASE_2', max_length=255, default='')  # Field name made lowercase.
    base_3 = models.CharField(db_column='BASE_3', max_length=255, default='')  # Field name made lowercase.
    base_4 = models.CharField(db_column='BASE_4', max_length=255, default='')  # Field name made lowercase.
    base_5 = models.CharField(db_column='BASE_5', max_length=255, default='')  # Field name made lowercase.
    base_6 = models.CharField(db_column='BASE_6', max_length=255, default='')  # Field name made lowercase.
    base_7 = models.CharField(db_column='BASE_7', max_length=255, default='')  # Field name made lowercase.
    base_8 = models.CharField(db_column='BASE_8', max_length=255, default='')  # Field name made lowercase.
    base_9 = models.CharField(db_column='BASE_9', max_length=255, default='')  # Field name made lowercase.
    base_10 = models.CharField(db_column='BASE_10', max_length=255, default='')  # Field name made lowercase.
    base_11 = models.CharField(db_column='BASE_11', max_length=255, default='')  # Field name made lowercase.
    base_12 = models.CharField(db_column='BASE_12', max_length=255, default='')  # Field name made lowercase.
    base_13 = models.CharField(db_column='BASE_13', max_length=255, default='')  # Field name made lowercase.
    base_14 = models.CharField(db_column='BASE_14', max_length=255, default='')  # Field name made lowercase.
    base_15 = models.CharField(db_column='BASE_15', max_length=255, default='')  # Field name made lowercase.
    base_16 = models.CharField(db_column='BASE_16', max_length=255, default='')  # Field name made lowercase.
    base_17 = models.CharField(db_column='BASE_17', max_length=255, default='')  # Field name made lowercase.
    base_18 = models.CharField(db_column='BASE_18', max_length=255, default='')  # Field name made lowercase.
    base_19 = models.CharField(db_column='BASE_19', max_length=255, default='')  # Field name made lowercase.
    base_20 = models.CharField(db_column='BASE_20', max_length=255, default='')  # Field name made lowercase.
    complimentary = models.BooleanField(db_column='COMPLIMENTARY', default=0)  # Field name made lowercase.
    income_account = models.CharField(db_column='INCOME_ACCOUNT', max_length=50)  # Field name made lowercase.
    field_type = models.SmallIntegerField(db_column='FIELD_TYPE', default=0)  # Field name made lowercase.
    source_field = models.TextField(db_column='SOURCE_FIELD', blank=True, null=True, default=0)  # Field name made lowercase. This field type is a guess.
    steps_in_use = models.SmallIntegerField(db_column='STEPS_IN_USE', default=0)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=40, default='')  # Field name made lowercase.
    deferred_income_account = models.CharField(db_column='DEFERRED_INCOME_ACCOUNT', max_length=50)  # Field name made lowercase.
    base_type = models.SmallIntegerField(db_column='BASE_TYPE', default=0)  # Field name made lowercase.
    prcnt_1 = models.DecimalField(db_column='PRCNT_1', max_digits=15, decimal_places=5, default=0)  # Field name made lowercase.
    prcnt_2 = models.DecimalField(db_column='PRCNT_2', max_digits=15, decimal_places=5, default=0)  # Field name made lowercase.
    prcnt_3 = models.DecimalField(db_column='PRCNT_3', max_digits=15, decimal_places=5, default=0)  # Field name made lowercase.
    prcnt_4 = models.DecimalField(db_column='PRCNT_4', max_digits=15, decimal_places=5, default=0)  # Field name made lowercase.
    prcnt_5 = models.DecimalField(db_column='PRCNT_5', max_digits=15, decimal_places=5, default=0)  # Field name made lowercase.
    prcnt_6 = models.DecimalField(db_column='PRCNT_6', max_digits=15, decimal_places=5, default=0)  # Field name made lowercase.
    prcnt_7 = models.DecimalField(db_column='PRCNT_7', max_digits=15, decimal_places=5, default=0)  # Field name made lowercase.
    prcnt_8 = models.DecimalField(db_column='PRCNT_8', max_digits=15, decimal_places=5, default=0)  # Field name made lowercase.
    prcnt_9 = models.DecimalField(db_column='PRCNT_9', max_digits=15, decimal_places=5, default=0)  # Field name made lowercase.
    prcnt_10 = models.DecimalField(db_column='PRCNT_10', max_digits=15, decimal_places=5, default=0)  # Field name made lowercase.
    prcnt_11 = models.DecimalField(db_column='PRCNT_11', max_digits=15, decimal_places=5, default=0)  # Field name made lowercase.
    prcnt_12 = models.DecimalField(db_column='PRCNT_12', max_digits=15, decimal_places=5, default=0)  # Field name made lowercase.
    prcnt_13 = models.DecimalField(db_column='PRCNT_13', max_digits=15, decimal_places=5, default=0)  # Field name made lowercase.
    prcnt_14 = models.DecimalField(db_column='PRCNT_14', max_digits=15, decimal_places=5, default=0)  # Field name made lowercase.
    prcnt_15 = models.DecimalField(db_column='PRCNT_15', max_digits=15, decimal_places=5, default=0)  # Field name made lowercase.
    prcnt_16 = models.DecimalField(db_column='PRCNT_16', max_digits=15, decimal_places=5, default=0)  # Field name made lowercase.
    prcnt_17 = models.DecimalField(db_column='PRCNT_17', max_digits=15, decimal_places=5, default=0)  # Field name made lowercase.
    prcnt_18 = models.DecimalField(db_column='PRCNT_18', max_digits=15, decimal_places=5, default=0)  # Field name made lowercase.
    prcnt_19 = models.DecimalField(db_column='PRCNT_19', max_digits=15, decimal_places=5, default=0)  # Field name made lowercase.
    prcnt_20 = models.DecimalField(db_column='PRCNT_20', max_digits=15, decimal_places=5, default=0)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Product_Price'
        unique_together = (('product_code', 'rule_type', 'customer_type'),)

    @classmethod
    def create_event(cls, event, product_code, option=None):
        # IMIS PRODUCT PRICE = SINGLE RECORD FOR EARLY, REGULAR, AND LATE REGISTRATIONS.
        # DJANGO PRODUCT PRICE = MULTIPLE PRODUCT_PRICE RECORDS. LOOP THROUGH PRICES AND CREATE SINGLE DJANGO RECORD FOR THE GIVEN REG CLASS.

        # EVENT REGISTRATIONS - CREATE PRODUCT PRICES BASED ON DJANGO EARLY, REGULAR, LATE PRICING.
        # TICKETED ITEMS DO NOT WRITE TO PRODUCT_PRICE SINCE WE DO NOT HAVE MULTIPLE PRICES FOR TICKETS BASED ON TDATE PURCHASED

        registrant_classes = event.product.prices.filter(option_code=option.code).values_list("imis_reg_class", flat=True).distinct()

        for registrant_class in registrant_classes:

            # only create product prices if there are reg classes associated with them
            if registrant_class:
                registrant_class_price = {}
                registrant_class_price["EARLY"] = 0 if not event.product.prices.filter(option_code=option.code, imis_reg_class=registrant_class, event_pricing_cutoff_type="EARLY") else event.product.prices.filter(option_code=option.code, imis_reg_class=registrant_class, event_pricing_cutoff_type="EARLY").first().price
                registrant_class_price["REGULAR"] = 0 if not event.product.prices.filter(option_code=option.code, imis_reg_class=registrant_class, event_pricing_cutoff_type="REGULAR") else event.product.prices.filter(option_code=option.code, imis_reg_class=registrant_class, event_pricing_cutoff_type="REGULAR").first().price
                registrant_class_price["LATE"] = 0 if not event.product.prices.filter(option_code=option.code, imis_reg_class=registrant_class, event_pricing_cutoff_type="LATE") else event.product.prices.filter(option_code=option.code, imis_reg_class=registrant_class, event_pricing_cutoff_type="LATE").first().price

                # IF ALL PRICES == 0, POTENTIALLY ONLY 1 PRODUCT PRICE EXISTS. MAKE THIS THE PRICE FOR ALL CUT-OFF TIMES.
                if registrant_class_price["EARLY"] == 0 and registrant_class_price["REGULAR"] == 0 and registrant_class_price["LATE"] == 0:

                    price = event.product.prices.filter(option_code=option.code, imis_reg_class=registrant_class).first().price
                    registrant_class_price["EARLY"] = price
                    registrant_class_price["REGULAR"] = price
                    registrant_class_price["LATE"] = price

                imis_product_price, created = cls.objects.get_or_create(product_code=product_code, customer_type=registrant_class)

                cls.objects.filter(product_code=product_code, customer_type=registrant_class).update(
                    rule_type = 'CT', # appears to be the default value for all productprice records
                    product_code = product_code,
                    customer_type = registrant_class, #REG TYPE??
                    rate_1 = registrant_class_price["EARLY"],
                    rate_2 = registrant_class_price["REGULAR"],
                    rate_3 = registrant_class_price["LATE"],
                    complimentary = 1 if registrant_class_price["EARLY"] == 0 else 0, # IF NO PRICE FOR THE TICKET, ASSUME IT IS A COMP TICKET.
                    income_account = event.product.gl_account) # assume gl_account of product

class ProductInventory(models.Model):
    product_code = models.CharField(db_column='PRODUCT_CODE', max_length=31, primary_key=True)  # Field name made lowercase.
    quantity_on_hand = models.DecimalField(db_column='QUANTITY_ON_HAND', max_digits=15, decimal_places=4, default=0)  # Field name made lowercase.
    quantity_reserved = models.DecimalField(db_column='QUANTITY_RESERVED', max_digits=15, decimal_places=4, default=0)  # Field name made lowercase.
    quantity_committed = models.DecimalField(db_column='QUANTITY_COMMITTED', max_digits=15, decimal_places=4, default=0)  # Field name made lowercase.
    quantity_available = models.DecimalField(db_column='QUANTITY_AVAILABLE', max_digits=15, decimal_places=4, default=0)  # Field name made lowercase.
    quantity_backordered = models.DecimalField(db_column='QUANTITY_BACKORDERED', max_digits=15, decimal_places=4, default=0)  # Field name made lowercase.
    quantity_on_order = models.DecimalField(db_column='QUANTITY_ON_ORDER', max_digits=15, decimal_places=4, default=0)  # Field name made lowercase.
    expected_arrival_date = models.DateTimeField(db_column='EXPECTED_ARRIVAL_DATE', blank=True, null=True)  # Field name made lowercase.
    ltd_orders = models.IntegerField(db_column='LTD_ORDERS', default=0)  # Field name made lowercase.
    ltd_quantity = models.DecimalField(db_column='LTD_QUANTITY', max_digits=15, decimal_places=4, default=0)  # Field name made lowercase.
    ltd_canceled_quantity = models.DecimalField(db_column='LTD_CANCELED_QUANTITY', max_digits=15, decimal_places=4, default=0)  # Field name made lowercase.
    ltd_income = models.DecimalField(db_column='LTD_INCOME', max_digits=15, decimal_places=2, default=0)  # Field name made lowercase.
    ltd_cost = models.DecimalField(db_column='LTD_COST', max_digits=15, decimal_places=2, default=0)  # Field name made lowercase.
    standard_cost = models.DecimalField(db_column='STANDARD_COST', max_digits=15, decimal_places=2, default=0)  # Field name made lowercase.
    latest_cost = models.DecimalField(db_column='LATEST_COST', max_digits=15, decimal_places=2, default=0)  # Field name made lowercase.
    average_cost = models.DecimalField(db_column='AVERAGE_COST', max_digits=15, decimal_places=2, default=0)  # Field name made lowercase.
    total_cost = models.DecimalField(db_column='TOTAL_COST', max_digits=15, decimal_places=2, default=0)  # Field name made lowercase.
    last_order_date = models.DateTimeField(db_column='LAST_ORDER_DATE', blank=True, null=True)  # Field name made lowercase.
    first_order_date = models.DateTimeField(db_column='FIRST_ORDER_DATE', blank=True, null=True)  # Field name made lowercase.
    last_received_date = models.DateTimeField(db_column='LAST_RECEIVED_DATE', blank=True, null=True)  # Field name made lowercase.
    minimum_order_point = models.IntegerField(db_column='MINIMUM_ORDER_POINT', default=0)  # Field name made lowercase.
    minimum_order_quantity = models.IntegerField(db_column='MINIMUM_ORDER_QUANTITY', default=0)  # Field name made lowercase.
    location = models.CharField(db_column='LOCATION', max_length=10, default='')  # Field name made lowercase.
    bin = models.CharField(db_column='BIN', max_length=10, default='')  # Field name made lowercase.
    income_account = models.CharField(db_column='INCOME_ACCOUNT', max_length=50, default='')  # Field name made lowercase.
    inventory_account = models.CharField(db_column='INVENTORY_ACCOUNT', max_length=50, default='')  # Field name made lowercase.
    cog_account = models.CharField(db_column='COG_ACCOUNT', max_length=50, default='')  # Field name made lowercase.
    adjustment_account = models.CharField(db_column='ADJUSTMENT_ACCOUNT', max_length=50, default='')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Product_Inventory'
        unique_together = (('product_code', 'location'),)

class NPC19_Speakers_Temp(models.Model):
    id = models.CharField(db_column='ID', max_length=10, primary_key=True)  # Field name made lowercase.
    first_name = models.CharField(db_column='First Name', max_length=20)  # Field name made lowercase.
    last_name = models.CharField(db_column='Last Name', max_length=30)  # Field name made lowercase.
    email = models.CharField(db_column='Email', max_length=100)  # Field name made lowercase.
    city = models.CharField(db_column='City', max_length=40)  # Field name made lowercase.
    state_province = models.CharField(db_column='State', max_length=15)  # Field name made lowercase.
    zip = models.CharField(db_column='Zipcode', max_length=10)  # Field name made lowercase.
    pw = models.CharField(db_column='PW', max_length=50)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = '_Temp_NPC19_Create_Accounts'

class MeetResources(models.Model):
    product_code = models.CharField(db_column='PRODUCT_CODE', max_length=31)  # Field name made lowercase.
    resource_type = models.CharField(db_column='RESOURCE_TYPE', max_length=10, default='')  # Field name made lowercase.
    res_group = models.CharField(db_column='RES_GROUP', max_length=10, default='')  # Field name made lowercase.
    code = models.CharField(db_column='CODE', max_length=10, default='')  # Field name made lowercase.
    line_no = models.IntegerField(db_column='LINE_NO', default=0)  # Field name made lowercase.
    fld1_qty = models.DecimalField(db_column='FLD1_QTY', max_digits=15, decimal_places=4, default=0)  # Field name made lowercase.
    fld1_time = models.DateTimeField(db_column='FLD1_TIME', blank=True, null=True)  # Field name made lowercase.
    fld1_check = models.BooleanField(db_column='FLD1_CHECK', default=0)  # Field name made lowercase.
    fld1_id = models.CharField(db_column='FLD1_ID', max_length=10, default='')  # Field name made lowercase.
    note = models.TextField(db_column='NOTE', blank=True, null=True)  # Field name made lowercase. This field type is a guess.

    class Meta:
        managed = False
        db_table = 'Meet_Resources'
        unique_together = (('product_code', 'resource_type', 'res_group', 'code'),)

    @classmethod
    def create_location(cls, event, product_code):
        # ONLY USED FOR ROOM RESOURCE (AT THE MOMENT)
        MeetResources.objects.filter(product_code=product_code, resource_type='ROOM').delete()

        MeetResources.objects.create(product_code=product_code, resource_type='ROOM', res_group='FP', code='LOC',
                                     line_no=1, fld1_check=1, note=event.location)

class Giftreport(models.Model):
    id = models.CharField(db_column='ID', primary_key=True, max_length=10)  # Field name made lowercase.
    originaltransaction = models.IntegerField(db_column='OriginalTransaction')  # Field name made lowercase.
    transactionnumber = models.IntegerField(db_column='TransactionNumber')  # Field name made lowercase.
    sourcesystem = models.CharField(db_column='SourceSystem', max_length=10)  # Field name made lowercase.
    transactiondate = models.DateTimeField(db_column='TransactionDate', blank=True, null=True)  # Field name made lowercase.
    datereceived = models.DateTimeField(db_column='DateReceived', blank=True, null=True)  # Field name made lowercase.
    amount = models.DecimalField(db_column='Amount', max_digits=15, decimal_places=2)  # Field name made lowercase.
    fund = models.CharField(db_column='Fund', max_length=10)  # Field name made lowercase.
    appealcode = models.CharField(db_column='AppealCode', max_length=40)  # Field name made lowercase.
    solicitorid = models.CharField(db_column='SolicitorID', max_length=10)  # Field name made lowercase.
    checknumber = models.CharField(db_column='CheckNumber', max_length=10)  # Field name made lowercase.
    paymenttype = models.CharField(db_column='PaymentType', max_length=11)  # Field name made lowercase.
    campaigncode = models.CharField(db_column='CampaignCode', max_length=10)  # Field name made lowercase.
    fiscalyear = models.IntegerField(db_column='FiscalYear')  # Field name made lowercase.
    fiscalmonth = models.IntegerField(db_column='FiscalMonth')  # Field name made lowercase.
    gifttype = models.CharField(db_column='GiftType', max_length=30)  # Field name made lowercase.
    invoicereferencenumber = models.IntegerField(db_column='InvoiceReferenceNumber')  # Field name made lowercase.
    receiptid = models.IntegerField(db_column='ReceiptID')  # Field name made lowercase.
    matchingtransaction = models.IntegerField(db_column='MatchingTransaction')  # Field name made lowercase.
    ismatchinggift = models.SmallIntegerField(db_column='IsMatchingGift')  # Field name made lowercase.
    memorialid = models.CharField(db_column='MemorialID', max_length=10)  # Field name made lowercase.
    pledgeid = models.CharField(db_column='PledgeID', max_length=10)  # Field name made lowercase.
    listas = models.CharField(db_column='ListAs', max_length=255)  # Field name made lowercase.
    requestnumber = models.DecimalField(db_column='RequestNumber', max_digits=15, decimal_places=4)  # Field name made lowercase.
    installmentdate = models.DateTimeField(db_column='InstallmentDate', blank=True, null=True)  # Field name made lowercase.
    memorialnametext = models.CharField(db_column='MemorialNameText', max_length=100)  # Field name made lowercase.
    # time_stamp = models.TextField(db_column='TIME_STAMP', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    fairmktvalue = models.DecimalField(db_column='FairMktValue', max_digits=19, decimal_places=4)  # Field name made lowercase.
    memorialtributetype = models.CharField(db_column='MemorialTributeType', max_length=10)  # Field name made lowercase.
    memorialtributemessage = models.TextField(db_column='MemorialTributeMessage')  # Field name made lowercase. This field type is a guess.
    # tributenotificationcontactid = models.CharField(db_column='TributeNotificationContactID', max_length=10)  # Field name made lowercase.
    note = models.CharField(db_column='Note', max_length=255)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'GiftReport'

class Gifthistorysummary(models.Model):
    donorid = models.CharField(db_column='DonorId', primary_key=True, max_length=10)  # Field name made lowercase.
    firstgiftdate = models.DateTimeField(db_column='FirstGiftDate', blank=True, null=True)  # Field name made lowercase.
    firstgiftamount = models.DecimalField(db_column='FirstGiftAmount', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    firstgiftappeal = models.CharField(db_column='FirstGiftAppeal', max_length=40, blank=True, null=True)  # Field name made lowercase.
    nextlastgiftdate = models.DateTimeField(db_column='NextLastGiftDate', blank=True, null=True)  # Field name made lowercase.
    nextlastgiftamount = models.DecimalField(db_column='NextLastGiftAmount', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    nextlastgiftappeal = models.CharField(db_column='NextLastGiftAppeal', max_length=40, blank=True, null=True)  # Field name made lowercase.
    lastgiftdate = models.DateTimeField(db_column='LastGiftDate', blank=True, null=True)  # Field name made lowercase.
    lastgiftamount = models.DecimalField(db_column='LastGiftAmount', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    lastgiftappeal = models.CharField(db_column='LastGiftAppeal', max_length=40, blank=True, null=True)  # Field name made lowercase.
    lowestgiftamount = models.DecimalField(db_column='LowestGiftAmount', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    highestgiftamount = models.DecimalField(db_column='HighestGiftAmount', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    numberofgifts = models.IntegerField(db_column='NumberOfGifts', blank=True, null=True)  # Field name made lowercase.
    lifetimegiftvalue = models.DecimalField(db_column='LifetimeGiftValue', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    averagegiftvalue = models.DecimalField(db_column='AverageGiftValue', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    consecutiveyearsgiving = models.IntegerField(db_column='ConsecutiveYearsGiving', blank=True, null=True)  # Field name made lowercase.
    highesttransnumprocessed = models.IntegerField(db_column='HighestTransNumProcessed')  # Field name made lowercase.
    lastupdatedon = models.DateTimeField(db_column='LastUpdatedOn')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'GiftHistorySummary'


# Tables Used in getting Contactkey for CSI Donate SSO

# FIELDS COMMENTED OUT BELOW BECAUSE THESE TABLES ARE ONLY USED TO GET contactkey for purposes of CSI Donate SSO
# If we decide to update or insert to this table via pyodbc in future we need to comment this back in


class Accessmain(models.Model):
    accesskey = models.CharField(db_column='AccessKey', primary_key=True, max_length=36)  # Field name made lowercase.
    accessscope = models.CharField(db_column='AccessScope', max_length=20)  # Field name made lowercase.
    # createdbyuserkey = models.ForeignKey('Usermain', models.DO_NOTHING, db_column='CreatedByUserKey')  # Field name made lowercase.
    createdon = models.DateTimeField(db_column='CreatedOn')  # Field name made lowercase.
    # updatedbyuserkey = models.ForeignKey('Usermain', models.DO_NOTHING, db_column='UpdatedByUserKey')  # Field name made lowercase.
    updatedon = models.DateTimeField(db_column='UpdatedOn')  # Field name made lowercase.
    markedfordeleteon = models.DateTimeField(db_column='MarkedForDeleteOn', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'AccessMain'


class Addresscategoryref(models.Model):
    addresscategorycode = models.IntegerField(db_column='AddressCategoryCode', primary_key=True)  # Field name made lowercase.
    addresscategorydesc = models.CharField(db_column='AddressCategoryDesc', unique=True, max_length=50)  # Field name made lowercase.
    isphysicaladdress = models.BooleanField(db_column='IsPhysicalAddress')  # Field name made lowercase.
    addresscategoryname = models.CharField(db_column='AddressCategoryName', unique=True, max_length=20)  # Field name made lowercase.
    formatmask = models.CharField(db_column='FormatMask', max_length=255, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'AddressCategoryRef'


class Componentregistry(models.Model):
    componentkey = models.CharField(db_column='ComponentKey', primary_key=True, max_length=36)  # Field name made lowercase.
    name = models.CharField(db_column='Name', max_length=50)  # Field name made lowercase.
    description = models.CharField(db_column='Description', max_length=1000)  # Field name made lowercase.
    interfacename = models.CharField(db_column='InterfaceName', max_length=100)  # Field name made lowercase.
    typename = models.CharField(db_column='TypeName', max_length=200)  # Field name made lowercase.
    assemblyname = models.CharField(db_column='AssemblyName', max_length=100)  # Field name made lowercase.
    configurewebusercontrol = models.CharField(db_column='ConfigureWebUserControl', max_length=128, blank=True, null=True)  # Field name made lowercase.
    configurewindowscontrol = models.CharField(db_column='ConfigureWindowsControl', max_length=128, blank=True, null=True)  # Field name made lowercase.
    istyped = models.BooleanField(db_column='IsTyped')  # Field name made lowercase.
    isbusinessitem = models.BooleanField(db_column='IsBusinessItem')  # Field name made lowercase.
    componentsummarycontentkey = models.CharField(db_column='ComponentSummaryContentKey', max_length=36, blank=True, null=True)  # Field name made lowercase.
    componentnewlink = models.CharField(db_column='ComponentNewLink', max_length=768, blank=True, null=True)  # Field name made lowercase.
    componenteditlink = models.CharField(db_column='ComponentEditLink', max_length=768, blank=True, null=True)  # Field name made lowercase.
    componentexecutelink = models.CharField(db_column='ComponentExecuteLink', max_length=768, blank=True, null=True)  # Field name made lowercase.
    deploymentpackagecode = models.CharField(db_column='DeploymentPackageCode', max_length=50, blank=True, null=True)  # Field name made lowercase.
    markedfordeleteon = models.DateTimeField(db_column='MarkedForDeleteOn', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ComponentRegistry'


class Uniformregistry(models.Model):
    uniformkey = models.CharField(db_column='UniformKey', primary_key=True, max_length=36)  # Field name made lowercase.
    componentkey = models.ForeignKey(Componentregistry, models.DO_NOTHING, db_column='ComponentKey')  # Field name made lowercase.
    markedfordeleteon = models.DateTimeField(db_column='MarkedForDeleteOn', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'UniformRegistry'


class Contactmain(models.Model):
    contactkey = models.ForeignKey('Uniformregistry', models.DO_NOTHING, db_column='ContactKey', primary_key=True)  # Field name made lowercase.
    # contactstatuscode = models.ForeignKey('Contactstatusref', models.DO_NOTHING, db_column='ContactStatusCode')  # Field name made lowercase.
    fullname = models.CharField(db_column='FullName', max_length=110)  # Field name made lowercase.
    sortname = models.CharField(db_column='SortName', max_length=110)  # Field name made lowercase.
    isinstitute = models.BooleanField(db_column='IsInstitute')  # Field name made lowercase.
    taxidnumber = models.CharField(db_column='TaxIDNumber', max_length=12, blank=True, null=True)  # Field name made lowercase.
    nosolicitationflag = models.BooleanField(db_column='NoSolicitationFlag')  # Field name made lowercase.
    synccontactid = models.CharField(db_column='SyncContactID', max_length=20, blank=True, null=True)  # Field name made lowercase.
    updatedon = models.DateTimeField(db_column='UpdatedOn')  # Field name made lowercase.
    # updatedbyuserkey = models.ForeignKey('Usermain', models.DO_NOTHING, db_column='UpdatedByUserKey')  # Field name made lowercase.
    isideditable = models.NullBooleanField(db_column='IsIDEditable')  # Field name made lowercase.
    id = models.CharField(db_column='ID', max_length=12, blank=True, null=True)  # Field name made lowercase.
    preferredaddresscategorycode = models.ForeignKey(Addresscategoryref, models.DO_NOTHING, db_column='PreferredAddressCategoryCode')  # Field name made lowercase.
    issortnameoverridden = models.BooleanField(db_column='IsSortNameOverridden')  # Field name made lowercase.
    # COMMENTING OUT BECAUSE THIS TABLE IS ONLY USED TO GET contactkey for purposes of CSI Donate SSO
    # If we decide to update or insert to this table via pyodbc in future we need to comment this back in
    # primarymembershipgroupkey = models.ForeignKey('Groupmain', models.DO_NOTHING, db_column='PrimaryMembershipGroupKey', blank=True, null=True)  # Field name made lowercase.
    majorkey = models.CharField(db_column='MajorKey', max_length=30, blank=True, null=True)  # Field name made lowercase.
    accesskey = models.ForeignKey(Accessmain, models.DO_NOTHING, db_column='AccessKey')  # Field name made lowercase.
    # createdbyuserkey = models.ForeignKey('Usermain', models.DO_NOTHING, db_column='CreatedByUserKey')  # Field name made lowercase.
    createdon = models.DateTimeField(db_column='CreatedOn')  # Field name made lowercase.
    textonlyemailflag = models.BooleanField(db_column='TextOnlyEmailFlag')  # Field name made lowercase.
    # contacttypekey = models.ForeignKey('Contacttyperef', models.DO_NOTHING, db_column='ContactTypeKey')  # Field name made lowercase.
    optoutflag = models.BooleanField(db_column='OptOutFlag')  # Field name made lowercase.
    markedfordeleteon = models.DateTimeField(db_column='MarkedForDeleteOn', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ContactMain'


class Usermain(models.Model):
    userkey = models.ForeignKey(Contactmain, models.DO_NOTHING, db_column='UserKey', primary_key=True)  # Field name made lowercase.
    contactmaster = models.CharField(db_column='ContactMaster', max_length=50, blank=True, null=True)  # Field name made lowercase.
    userid = models.CharField(db_column='UserId', max_length=60)  # Field name made lowercase.
    isdisabled = models.BooleanField(db_column='IsDisabled')  # Field name made lowercase.
    effectivedate = models.DateTimeField(db_column='EffectiveDate')  # Field name made lowercase.
    expirationdate = models.DateTimeField(db_column='ExpirationDate', blank=True, null=True)  # Field name made lowercase.
    # updatedbyuserkey = models.ForeignKey('self', models.DO_NOTHING, db_column='UpdatedByUserKey')  # Field name made lowercase.
    updatedon = models.DateTimeField(db_column='UpdatedOn')  # Field name made lowercase.
    # createdbyuserkey = models.ForeignKey('self', models.DO_NOTHING, db_column='CreatedByUserKey')  # Field name made lowercase.
    createdon = models.DateTimeField(db_column='CreatedOn')  # Field name made lowercase.
    markedfordeleteon = models.DateTimeField(db_column='MarkedForDeleteOn', blank=True, null=True)  # Field name made lowercase.
    # COMMENTING OUT BECAUSE THIS TABLE IS ONLY USED TO GET contactkey for purposes of CSI Donate SSO
    # If we decide to update or insert to this table via pyodbc in future we need to comment this back in
    # defaultdepartmentgroupkey = models.ForeignKey(Groupmain, models.DO_NOTHING, db_column='DefaultDepartmentGroupKey', blank=True, null=True)  # Field name made lowercase.
    # COMMENTING OUT BECAUSE THIS TABLE IS ONLY USED TO GET contactkey for purposes of CSI Donate SSO
    # If we decide to update or insert to this table via pyodbc in future we need to comment this back in
    # defaultperspectivekey = models.ForeignKey(Perspective, models.DO_NOTHING, db_column='DefaultPerspectiveKey', blank=True, null=True)  # Field name made lowercase.
    providerkey = models.CharField(db_column='ProviderKey', max_length=100, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'UserMain'


class CustomAddressGeocode(models.Model):
    id = models.CharField(db_column='ID', max_length=10)
    seqn = models.IntegerField(db_column='SEQN', primary_key=True)
    address_num = models.IntegerField(db_column='ADDRESS_NUM', unique=True)
    votervoice_checksum = models.CharField(db_column='VOTERVOICE_CHECKSUM',
                                           max_length=255, null=True, blank=True)
    longitude = models.FloatField(db_column='LONGITUDE', null=True, blank=True)
    latitude = models.FloatField(db_column='LATITUDE', null=True, blank=True)
    weak_coordinates = models.BooleanField(db_column='WEAK_COORDINATES', default=False)
    us_congress = models.CharField(db_column='US_CONGRESS', max_length=100, null=True, blank=True)
    state_senate = models.CharField(db_column='STATE_SENATE', max_length=100, null=True, blank=True)
    state_house = models.CharField(db_column='STATE_HOUSE', max_length=100, null=True, blank=True)
    changed = models.BooleanField(db_column='CHANGED', default=False)
    last_updated = models.DateTimeField(db_column='LAST_UPDATED', auto_now=True)

    class Meta:
        managed = False
        db_table = 'Custom_Address_Geocode'

    def save(self, *args, **kwargs):

        if not self.pk:
            self.pk = Counter.create_id(self._meta.db_table)

        return super().save(*args, **kwargs)

    def get_votervoice_validated_address_query(self):

        if not self.votervoice_checksum:
            return {}

        name_address = NameAddress.objects.filter(address_num=self.address_num).first()
        if name_address is None or name_address.country.upper() != 'UNITED STATES':
            return {}
        address_dict = name_address.get_votervoice_address_query()

        zip_code = split_zip_code(name_address.zip)

        address_fields = dict(
            streetAddress=address_dict['address1'],
            city=address_dict['city'],
            state=address_dict['state'],
            zipCode=zip_code['zip_code'],
            zipCodeExtension=zip_code['zip_code_extension'],
            checksum=self.votervoice_checksum,
            country='US'
        )
        address_fields = {k: v for (k, v) in address_fields.items() if v}
        params = dict(
            address=json.dumps(address_fields),
            association=getattr(settings, 'VOTER_VOICE_ASSOCIATION_NAME', 'PLANNING')
        )
        return params

    def get_districts(self, changed=False):
        client = VoterVoiceClient()
        params = self.get_votervoice_validated_address_query()
        if params:
            resp = client.get_districts_by_address(params)
            if resp:
                for district in resp:
                    elected_body = district.get('electedBody')
                    if elected_body in STATE_HOUSE:
                        self.state_house = district.get('districtId', '')
                    elif elected_body == STATE_SENATE:
                        self.state_senate = district.get('districtId', '')
                    elif elected_body == US_HOUSE:
                        self.us_congress = district.get('districtId', '')
                self.changed = changed
                self.save()

class AicpDemographics(models.Model):
    id = models.CharField(db_column='ID', primary_key=True, max_length=10)  # Field name made lowercase.
    certification_no = models.CharField(db_column='CERTIFICATION_NO', max_length=6)  # Field name made lowercase.
    planning_inst = models.CharField(db_column='PLANNING_INST', max_length=4)  # Field name made lowercase.
    times_taken = models.FloatField(db_column='TIMES_TAKEN')  # Field name made lowercase.
    ethnicity = models.CharField(db_column='ETHNICITY', max_length=20)  # Field name made lowercase.
    last_test_date = models.DateTimeField(db_column='LAST_TEST_DATE', blank=True, null=True)  # Field name made lowercase.
    pass_fail_code = models.CharField(db_column='PASS_FAIL_CODE', max_length=10)  # Field name made lowercase.
    scaled_score = models.FloatField(db_column='SCALED_SCORE')  # Field name made lowercase.
    score_1 = models.FloatField(db_column='SCORE_1')  # Field name made lowercase.
    score_2 = models.FloatField(db_column='SCORE_2')  # Field name made lowercase.
    score_3 = models.FloatField(db_column='SCORE_3')  # Field name made lowercase.
    score_4 = models.FloatField(db_column='SCORE_4')  # Field name made lowercase.
    score_5 = models.FloatField(db_column='SCORE_5')  # Field name made lowercase.
    score_6 = models.FloatField(db_column='SCORE_6')  # Field name made lowercase.
    score_7 = models.FloatField(db_column='SCORE_7')  # Field name made lowercase.
    score_8 = models.FloatField(db_column='SCORE_8')  # Field name made lowercase.
    cert_name = models.CharField(db_column='CERT_NAME', max_length=60)  # Field name made lowercase.
    exam_center = models.CharField(db_column='EXAM_CENTER', max_length=6)  # Field name made lowercase.
    bif_date = models.DateTimeField(db_column='BIF_DATE', blank=True, null=True)  # Field name made lowercase.
    reg_ack_date = models.DateTimeField(db_column='REG_ACK_DATE', blank=True, null=True)  # Field name made lowercase.
    postcard_date = models.DateTimeField(db_column='POSTCARD_DATE', blank=True, null=True)  # Field name made lowercase.
    curr_exam_date = models.DateTimeField(db_column='CURR_EXAM_DATE', blank=True, null=True)  # Field name made lowercase.
    exam_year = models.FloatField(db_column='EXAM_YEAR')  # Field name made lowercase.
    schools = models.CharField(db_column='SCHOOLS', max_length=4)  # Field name made lowercase.
    birth_country = models.CharField(db_column='BIRTH_COUNTRY', max_length=25)  # Field name made lowercase.
    birth_place = models.CharField(db_column='BIRTH_PLACE', max_length=25)  # Field name made lowercase.
    usa_citizen = models.BooleanField(db_column='USA_CITIZEN')  # Field name made lowercase.
    planning_degree = models.BooleanField(db_column='PLANNING_DEGREE')  # Field name made lowercase.
    accredited_degree = models.BooleanField(db_column='ACCREDITED_DEGREE')  # Field name made lowercase.
    aicp_start = models.DateTimeField(db_column='AICP_START', blank=True, null=True)  # Field name made lowercase.
    birth_date = models.DateTimeField(db_column='BIRTH_DATE', blank=True, null=True)  # Field name made lowercase.
    aicp_promo_1 = models.CharField(db_column='AICP_PROMO_1', max_length=6)  # Field name made lowercase.
    aicp_promo_2 = models.CharField(db_column='AICP_PROMO_2', max_length=6)  # Field name made lowercase.
    sub_specialty = models.CharField(db_column='SUB_SPECIALTY', max_length=6)  # Field name made lowercase.
    org_type = models.CharField(db_column='ORG_TYPE', max_length=6)  # Field name made lowercase.
    yrs_experience = models.FloatField(db_column='YRS_EXPERIENCE')  # Field name made lowercase.
    degree_level = models.CharField(db_column='DEGREE_LEVEL', max_length=8)  # Field name made lowercase.
    degree_date = models.DateTimeField(db_column='DEGREE_DATE', blank=True, null=True)  # Field name made lowercase.
    major = models.CharField(db_column='MAJOR', max_length=3)  # Field name made lowercase.
    degree_title = models.CharField(db_column='DEGREE_TITLE', max_length=255)  # Field name made lowercase.
    date_span = models.CharField(db_column='DATE_SPAN', max_length=100)  # Field name made lowercase.
    time_stamp = models.TextField(db_column='TIME_STAMP', blank=True, null=True)  # Field name made lowercase. This field type is a guess.

    class Meta:
        managed = False
        db_table = 'AICP_Demographics'
