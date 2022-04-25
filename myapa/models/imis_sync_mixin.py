"""imis_sync_mixin.py

Module for syncing Contact data between iMIS and Django
"""
from datetime import datetime

import pytz
from django.conf import settings
from django.db import connections
from django.db.models import Q
from sentry_sdk import capture_message

from imis import models as imis_models
from imis.enums.members import ImisNameAddressPurposes
from imis.tests.factories import name as name_facts
from imis.tests.factories.demographics import MailingDemographicsFactoryBlank, OrgDemographicsFactoryBlank
from imis.tests.factories.ind_demographics import ImisIndDemographicsFactoryBlank
from imis.tests.factories.name_address import ImisNameAddressFactoryBlank
from imis.utils import sql as sql_utils
from imis.utils.addresses import get_primary_address
from myapa.models.constants import APA_COMPANY_IDS, DjangoContactTypes, DjangoOrganizationTypes


class ImisSyncMixin(object):

    NAME_LOG_CHANGE_RECORD = dict(
        date_time=datetime.now(tz=pytz.timezone(settings.TIME_ZONE)),
        log_type='CHANGE',
        sub_type='security',
        user_id='webuser',
        log_text='change record'
    )

    def sync_from_imis(self):
        """Sync data between this member's record in iMIS and Django"""

        # Importing here to avoid circular import
        from myapa.utils import get_contact_class

        imis_name = self.get_imis_name()
        if imis_name is None:
            capture_message("%s not found in iMIS" % self, level='warning')
            return
        self._set_contact_type_from_imis(imis_name)
        primary_address = get_primary_address(imis_name.id)
        if primary_address is not None:
            self._set_address_from_imis(primary_address)
        else:
            capture_message("No Name_Address record found for %s" % self, level='warning')
        self._set_contact_info_from_imis(imis_name)
        self._set_bio_info_from_imis(imis_name)
        self._set_chapter_from_imis(imis_name)
        self._set_org_type_from_imis(imis_name)
        self._set_member_type_from_imis(imis_name)
        self._set_company_is_apa()
        if self.organization_type == DjangoOrganizationTypes.PR005.value:
            self._set_consultant_listing_until()
        self._sync_parent_org(imis_name)
        imis_ind_demo = self.get_imis_ind_demographics()
        if imis_ind_demo is not None:
            self._set_demographics_data_from_imis(imis_ind_demo)

        model_class = get_contact_class(self)()
        model_class.__dict__.update(**self.__dict__)
        if model_class.contact_type == DjangoContactTypes.ORGANIZATION.value:
            model_class.update_or_create_relationships_from_imis()
        model_class.save()
        return model_class

    def imis_create(self, **kwargs):
        """Create records in iMIS from this Contact"""
        name = name_facts.ImisNameFactoryBlank(
            org_code='APA',
            member_type=kwargs.get('member_type', 'NOM'),
            category=kwargs.get('category', ''),
            status='A',
            last_first='{}, {}'.format(self.last_name or '', self.first_name or '').upper(),
            full_name='{} {} {}'.format(
                self.first_name or '',
                self.middle_name or '',
                self.last_name or ''
            ),
            prefix=self.prefix_name or '',
            first_name=self.first_name or '',
            middle_name=self.middle_name or '',
            last_name=self.last_name or '',
            suffix=self.suffix_name or '',
            informal=kwargs.get("informal_name", ''),
            city=self.city or '',
            state_province=self.state or '',
            zip=self.zip_code or '',
            country=self.country or '',
            email=self.email,
            updated_by='WEBUSER',
            last_updated=self.getdate(),
            source_code='WEB',
            birth_date=self.birth_date,
            home_phone=self.phone or '',
            work_phone=self.secondary_phone or '',
            mobile_phone=self.cell_phone or ''
        )
        name.id = imis_models.Counter.create_id('Name')
        name.save()

        ind_demo = ImisIndDemographicsFactoryBlank(
            id=name.id,
            hint_password=kwargs.get('hint_password', ''),
            hint_answer=kwargs.get('hint_answer', ''),
            email_secondary=self.secondary_email or ''
        )
        ind_demo.save()

        # TODO: Should this only be created if it's an organization?
        org_demo = OrgDemographicsFactoryBlank(id=name.id, org_type=kwargs.get('org_type', ''))
        org_demo.save()

        mailing_demo = MailingDemographicsFactoryBlank(id=name.id)
        mailing_demo.save()

        self.insert_name_log_record(
            dict(
                date_time=self.getdate(),
                log_type="CHANGE",
                sub_type="ADD",
                user_id="WEBUSER",
                id=name.id,
                log_text='{} {}'.format(self.first_name or '', self.last_name or '')
            )
        )

        name_fin = name_facts.ImisNameFinFactoryBlank(id=name.id)
        name_fin.save()

        self.insert_name_picture(name.id)
        self.insert_name_security(name.id)
        self.insert_name_security_groups(name.id)

        return name

    @staticmethod
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

    @staticmethod
    def insert_name_picture(name_id):
        name_picture = name_facts.ImisNamePictureFactoryBlank(
            id=name_id,
            picture_num=imis_models.Counter.create_id('Name_Picture')
        )
        name_picture.save()

    @staticmethod
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

    def make_name_log_data(self, data):
        name_log_data = data.copy()
        name_log_data['id'] = self.user.username
        return name_log_data

    @staticmethod
    def getdate():
        return datetime.now(tz=pytz.timezone(settings.TIME_ZONE))

    @staticmethod
    def insert_name_log_record(data):

        name_log_insert = sql_utils.make_insert_statement(
            'Name_Log',
            data,
            exclude_id_field=False
        )
        sql_utils.do_insert(name_log_insert, data)

    def update_country_codes(self):
        """Update the user's country_codes value in IndDemographics, based on their country
        (and only if they're outside of the US)"""
        ind_demo = self.get_imis_ind_demographics()
        if ind_demo is not None:
            ind_demo.country_codes = self.get_country_codes()
            ind_demo.save()

    def get_country_codes(self):
        """
        For international members, get the country_codes to be used in the Ind_Demographics table.
        Not to be confused with :meth:`myapa.models.contact.Contact.get_country_type_code`,
        which is used for determining pricing in the e-commerce store

        iMIS Query:
        SELECT * FROM Gen_Tables WHERE TABLE_NAME = 'COUNTRY_CODES'

        KK: Student Member outside US
        LL: New Prof Member outside US
        MM: Plng Brd Member outside US
        NN: Retired Member outside US
        OO: Life Member outside US
        :return: str
        """

        if not self.is_international:
            return ''
        elif self.member_type == 'STU':
            return "KK"
        elif self.member_type == 'PBM':
            return "MM"
        elif self.member_type == "RET":
            return "NN"
        elif self.member_type == "LIFE":
            return "OO"
        else:
            return "LL"

    def create_imis_name_address(self, **kwargs):
        """Create :class:`imis.models.NameAddress` for this Contact"""

        # importing here to avoid circular import
        from myapa.tasks import vv_validate_address_imis

        preferred_mail = kwargs.get('preferred_mail', False)
        preferred_bill = kwargs.get('preferred_bill', False)
        purpose = kwargs.get('purpose', False)
        is_additional = False
        try:
            imis_id = self.user.username
        except AttributeError:
            imis_id = kwargs.get('imis_id')
            is_additional = True

        address = ImisNameAddressFactoryBlank(
            id=imis_id,
            address_num=imis_models.Counter.create_id('Name_Address'),
            purpose=purpose,
            address_1=self.address1,
            address_2=self.address2 or '',
            city=self.city,
            state_province=self.state or '',
            zip=self.zip_code or '',
            country=self.country,
            preferred_mail=preferred_mail,
            preferred_bill=preferred_bill,
            last_updated=self.getdate(),
            company=self.company or '',
        )
        address.full_address = address.get_full_address()
        address.company_sort = address.get_company_sort()
        address.save()
        vv_validate_address_imis.delay(self, address_num=address.address_num)

        if not is_additional:
            self.update_country_codes()

        self.update_imis_name_address_num(address, imis_id)

        return address

    @staticmethod
    def _handle_preferred_ship(imis_id: str):
        addresses = imis_models.NameAddress.objects.filter(id=imis_id)
        addresses.update(preferred_ship=False)

    @staticmethod
    def update_imis_name_address_num(address, imis_id: str):
        """
        Behold the genius of the iMIS address data model. It occupies a different plane of existence and cannot be
        comprehended by mere mortals.

        https://americanplanning.atlassian.net/browse/DEV-7980

        :param address: iMIS Name Address record
        :type address: :class:`imis.models.NameAddress`
        :param imis_id: Name id
        :return: iMIS Name record or None
        """

        imis_name = imis_models.Name.objects.get(id=imis_id)

        # Initialize everything to home address at the start, updating as necessary
        if address.purpose == ImisNameAddressPurposes.HOME_ADDRESS.value:
            imis_name.address_num_1 = address.address_num
            imis_name.address_num_2 = address.address_num
            imis_name.address_num_3 = address.address_num
            imis_name.mail_address_num = address.address_num
            imis_name.bill_address_num = address.address_num
            imis_name.ship_address_num = address.address_num
        elif address.purpose == ImisNameAddressPurposes.WORK_ADDRESS.value:
            imis_name.address_num_2 = address.address_num
        elif address.purpose == ImisNameAddressPurposes.OTHER_ADDRESS.value:
            imis_name.address_num_3 = address.address_num

        if address.preferred_bill:
            imis_name.bill_address_num = address.address_num
        if address.preferred_mail:
            imis_name.mail_address_num = address.address_num
        if address.preferred_ship:
            imis_name.ship_address_num = address.address_num

        # More stupid code to make iMIS happy...
        if address.preferred_bill and address.preferred_mail:
            ImisSyncMixin._handle_preferred_ship(imis_id)
            imis_name.ship_address_num = address.address_num
            address.preferred_ship = True
            address.save()

        imis_name.save()
        return imis_name

    def update_imis_address(self, imis_address_data: dict):

        imis_address = self.get_imis_name_address(purpose=imis_address_data['purpose'])
        imis_address.update(**imis_address_data)
        imis_address = imis_address.first()
        if imis_address is not None and imis_address.address_1 and imis_address.city and imis_address.country:
            imis_address.full_address = imis_address.get_full_address()
            imis_address.save()
            self.update_imis_name_address_num(imis_address, self.user.username)
        return imis_address

    def get_imis_name(self):
        """Get the :class:`imis.models.Name` for this Contact"""
        return imis_models.Name.objects.filter(id=self.user.username).first()

    def get_imis_name_address(self, **kwargs):
        """
        Get the :class:`imis.models.NameAddress` for this Contact

        :return: :class:`django.db.models.QuerySet`
        """
        return imis_models.NameAddress.objects.filter(id=self.user.username, **kwargs)

    def get_imis_ind_demographics(self):
        """Get the :class:`imis.models.IndDemographics` for this Contact"""
        return imis_models.IndDemographics.objects.filter(id=self.user.username).first()

    def get_imis_subscriptions(self, **kwargs):
        """
        Get the :class:`imis.models.Subscriptions` for this Contact.

        :return: :class:`django.db.models.QuerySet`
        """
        return imis_models.Subscriptions.objects.filter(id=self.user.username, **kwargs)

    def get_imis_activities(self, **kwargs):
        """
        Get the :class:`imis.models.Activity` for this Contact
        :param kwargs: optional additional filters
        :return: :class:`django.db.models.QuerySet`
        """
        return imis_models.Activity.objects.filter(id=self.user.username, **kwargs)

    def get_imis_orders(self):
        """
        Get the :class:`imis.models.Orders` for this Contact
        :return: list
        """
        select_statement = sql_utils.make_select_statement('Orders')
        select_statement += ' WHERE BT_ID = %s'
        with connections['MSSQL'].cursor() as cursor:
            cursor.execute(select_statement, [self.user.username])
            return sql_utils.namedtuplefetchall(cursor)

    def get_imis_order_lines(self):
        """
        Get the entries in the iMIS Order_Lines table related to this Contact
        :return: list
        """
        orders = self.get_imis_orders()
        order_numbers = [i.ORDER_NUMBER for i in orders]
        if order_numbers:
            select_statement = sql_utils.make_select_statement('OrderLines')
            select_statement += " WHERE ORDER_NUMBER IN ("
            select_statement += "%s, " * len(order_numbers)
            select_statement = select_statement[:-2] + ")"
            with connections['MSSQL'].cursor() as cursor:
                cursor.execute(select_statement, order_numbers)
                return sql_utils.namedtuplefetchall(cursor) or []
        return []

    def get_imis_race_origin(self, **kwargs):
        """
        Get the :class:`imis.models.RaceOrigin` for this Contact
        :param kwargs: optional Django QuerySet filters
        :return: :class:`imis.models.RaceOrigin`
        """
        return imis_models.RaceOrigin.objects.filter(id=self.user.username, **kwargs).first()

    def get_imis_advocacy(self, **kwargs):
        """
        Get the :class:`imis.models.Advocacy` for this Contact
        :param kwargs: optional Django QuerySet filters
        :return: :ckass:`imis.models.Advocacy`
        """
        return imis_models.Advocacy.objects.filter(id=self.user.username, **kwargs).first()

    def get_imis_mailing_demographics(self):
        """
        Get the :class:`imis.models.MailingDemographics` for this Contact
        :return: :class:`imis.models.MailingDemographics`
        """
        return imis_models.MailingDemographics.objects.filter(id=self.user.username).first()

    def get_imis_contact_legacy(self):
        """
        LEGACY: Replacing the old Node Restify API response
        :return: dict
        """
        name = self.get_imis_name()
        if name is None:
            return {
                'success': False,
                'message': '{} not found in iMIS'.format(self)
            }
        address = get_primary_address(self.user.username)

        if not address:
            class address(object):
                pass
            address.address_1 = ""
            address.address_2 = ""

        demographics = self.get_imis_ind_demographics()
        return {
            'success': True,
            'data': {
                'webuserid': name.id,
                'member_type': name.member_type,
                'status': name.status,
                'co_id': name.co_id or '',
                'ecp_type': name.category or '',
                'last_first': name.last_first or '',
                'company': name.company or '',
                'full_name': name.full_name or '',
                'chapter': name.chapter or '',
                'title': name.title or '',
                'full_address': name.full_address or '',
                'prefix': name.prefix or '',
                'suffix': name.suffix or '',
                'designation': name.designation or '',
                'informal': name.informal or '',
                'work_phone': name.work_phone or '',
                'home_phone': name.home_phone or '',
                'mobile_phone': name.mobile_phone or '',
                'fax': name.fax or '',
                'city': name.city or '',
                'state_province': name.state_province or '',
                'zip': name.zip or '',
                'country': name.country or '',
                'gender': name.gender or '',
                'birth_date': name.birth_date.strftime(
                    '%Y-%m-%dT%H:%M:%S.000Z'
                ) if name.birth_date is not None else None,
                'join_date': name.join_date.strftime(
                    '%Y-%m-%dT%H:%M:%S.000Z'
                ) if name.join_date is not None else None,
                'paid_thru': name.paid_thru.strftime(
                    '%Y-%m-%dT%H:%M:%S.000Z'
                ) if name.paid_thru is not None else None,
                'email': name.email or '',
                'website': name.website or '',
                'salary_range': demographics.salary_range or '',
                'password_hint_code': demographics.hint_password or '',
                'password_hint_answer': demographics.hint_answer or '',
                'country_codes': demographics.country_codes,
                'email_secondary': demographics.email_secondary or '',
                'first_name': name.first_name or '',
                'last_name': name.last_name or '',
                'middle_name': name.middle_name or '',
                'address1': address.address_1 or '',
                'address2': address.address_2 or '',
                'company_record': name.company_record,
                'member_record': name.member_record
            }
        }

    def get_imis_subscriptions_legacy(self):
        """
        LEGACY: Replicating the old Node Restify API response
        :return: dict
        """
        subs = self.get_imis_subscriptions(status='A', bill_amount__gt=0)
        response = {'success': True, 'data': []}
        for sub in subs:
            response['data'].append(sub.json_response())
        return response

    def get_imis_demographics_legacy(self):
        """
        LEGACY: Replicating the old Node Restify API response
        :return: dict
        """
        name = self.get_imis_name()
        race_origin = imis_models.RaceOrigin.objects.filter(id=self.user.username).first()
        ind_demographics = self.get_imis_ind_demographics()

        mailing_demographics = self.get_imis_mailing_demographics()
        return {
            'success': True,
            'data': {
                'race': getattr(race_origin, 'race', None),
                'origin': getattr(race_origin, 'origin', None),
                'span_hisp_latino': getattr(race_origin, 'span_hisp_latino', None),
                'ai_an': getattr(race_origin, 'ai_an', None),
                'asian_pacific': getattr(race_origin, 'asian_pacific', None),
                'other': getattr(race_origin, 'other', None),
                'ethnicity_noanswer': getattr(race_origin, 'ethnicity_noanswer', None),
                'origin_noanswer': getattr(race_origin, 'origin_noanswer', None),
                'gender': getattr(ind_demographics, "gender", None),
                'gender_other': getattr(ind_demographics, 'gender_other', None),
                'salary_range': getattr(ind_demographics, 'salary_range', None),
                'functional_title': getattr(name, 'functional_title', None),
                'exclude_planning_print': getattr(
                    mailing_demographics, 'excl_planning_print', None
                )
            }
        }

    def get_imis_advocacy_legacy(self):
        """
        LEGACY: Replicating the old Node Restify API response
        :return: dict
        """
        advocacy = imis_models.Advocacy.objects.filter(id=self.user.username).first()
        if advocacy is not None:
            return advocacy.json_response()
        return {}

    def get_imis_company_legacy(self):
        """
        LEGACY: Replicating the old Node Restify API response
        :return: dict
        """
        response = {'success': True, 'data': []}
        # TODO: This should be covered by _sync_parent_org and the if check should be
        # for self.company_fk
        name = self.get_imis_name()
        if name is not None:
            if name.co_id is not None and name.co_id.strip():
                company_record = imis_models.Name.objects.filter(id=name.co_id).first()
                if company_record is not None:
                    # TODO: This will always only return one?
                    response['data'].append(company_record.json_response_company())
        return response

    def get_imis_company_roster(self):
        name = self.get_imis_name()
        if not name.company_record:
            return {'success': False}
        roster = imis_models.Name.objects.filter(co_id=name.id)
        response = {'success': True, 'data': [x.json_response() for x in roster]}
        return response

    def get_imis_company_relationships_legacy(self):
        """
        LEGACY: Replicating the old Node Restify API response for
        /contacts/organizations/{id}/relationships
        :return: dict
        """
        response = {'success': True, 'data': []}
        name = self.get_imis_name()
        if name.co_id is not None and name.co_id.strip():
            # Get a flat list of ids in Relationship table
            related_ids = imis_models.Relationship.objects.filter(
                Q(id=self.user.username) | Q(target_id=self.user.username)
            )
            related_ids = [(i.id, i.target_id) for i in related_ids]
            related_ids = set([x for y in related_ids for x in y if x != self.user.username])
            related_names = imis_models.Name.objects.filter(id__in=related_ids)
            for name in related_names:
                response['data'].append(name.json_response())
            return response

    def get_imis_contact_preferences_legacy(self):
        """
        LEGACY: Replicating the old Node Restify API response for
        /contacts/{id}/preferences
        :return: dict
        """
        response = {'success': True, 'data': []}
        mdemo = self.get_imis_mailing_demographics()
        if mdemo is not None:
            response['data'].append(mdemo.json_response())
        return response

    def _set_contact_info_from_imis(self, imis_name):
        """
        Set email, phone, etc. info from iMIS
        :param imis_name: :class:`imis.models.Name`
        :return: None
        """
        if imis_name.company:
            self.company = imis_name.company
        self.email = imis_name.email
        # TODO: Verify these no longer needs to be limited to 20 chars
        self.phone = imis_name.home_phone[:20]
        self.secondary_phone = imis_name.work_phone[:20]
        self.cell_phone = imis_name.mobile_phone[:20]

    def _set_bio_info_from_imis(self, imis_name):
        """
        Set first/middle/last names, designations, titles of nobility/peerage and such yes jolly good

        :param imis_name: :class:`imis.models.Name`
        :return: None
        """

        self.prefix_name = imis_name.prefix
        self.first_name = imis_name.first_name
        self.middle_name = imis_name.middle_name
        self.last_name = imis_name.last_name
        self.suffix_name = imis_name.suffix
        self.designation = imis_name.designation

        self.job_title = imis_name.title
        self.birth_date = imis_name.birth_date

        # Also update our AUTH_USER_MODEL, so that the member
        # can now log in with their iMIS-updated email
        self.user.first_name = imis_name.first_name
        self.user.last_name = imis_name.last_name
        self.user.email = imis_name.email
        self.user.save()

    def _set_chapter_from_imis(self, imis_name):
        """
        Set the chapter code from iMIS
        :param imis_name: :class:`imis.models.Name`
        :return: None
        """
        self.chapter = imis_name.chapter

    def _set_org_type_from_imis(self, imis_name):
        """
        Set the correct organization_type based on iMIS data
        :param imis_name: :class:`imis.models.Name`
        :return: None
        """
        if self.contact_type == DjangoContactTypes.ORGANIZATION.value:
            org_demo = imis_models.OrgDemographics.objects.filter(id=imis_name.id).first()
            if org_demo is not None:
                self.organization_type = org_demo.org_type

    def _set_member_type_from_imis(self, imis_name):
        """
        Set the member_type from iMIS
        :param imis_name: :class:`imis.models.Name`
        :return: None
        """
        self.member_type = imis_name.member_type

    def _set_contact_type_from_imis(self, imis_name):
        """
        Set contact_type to be INDIVIDUAL or ORGANIZATION, based on the boolean value
        of :attr:`imis.models.Name.company_record`
        :param imis_name: :class:`imis.models.Name`
        :return: None
        """
        self.contact_type = "ORGANIZATION" if imis_name.company_record else "INDIVIDUAL"

    def _set_address_from_imis(self, primary_address):
        """
        Set address fields from iMIS
        :param primary_address: :class:`imis.models.NameAddress`
        :return: None
        """
        self.user_address_num = primary_address.address_num
        self.address1 = primary_address.address_1
        self.address2 = primary_address.address_2
        self.city = primary_address.city
        self.state = primary_address.state_province
        self.zip_code = primary_address.zip
        # TODO: Verify this no longer needs to be limited to 20 chars
        self.country = primary_address.country[:20]

    def _set_demographics_data_from_imis(self, ind_demo):
        """
        Set data from iMIS Ind_Demographics table
        :param ind_demo: :class:`imis.models.IndDemographics`
        :return: None
        """
        self.salary_range = getattr(ind_demo, "salary_range", '').strip()
        self.secondary_email = ind_demo.email_secondary

    def _set_company_is_apa(self):
        """
        Is this Contact a Chapter or Division or the APA offices
        :return: :type:`bool`
        """
        self.company_is_apa = self.member_type in ('CHP', 'DVN') or self.user.username in APA_COMPANY_IDS

    def _set_consultant_listing_until(self):
        """
        If this is a :class:`consultants.models.Consultant`, get or create its
        :class:`myapa.models.profile.OrganizationProfile` and update its
        consultant_listing_until date
        :return: None
        """
        # importing here to avoid circular import
        from myapa.models.profile import OrganizationProfile
        profile, _ = OrganizationProfile.objects.get_or_create(
            contact=self
        )
        profile.set_consultant_listing_until()

    def _sync_parent_org(self, imis_name, grandparent=False):
        """
        Set this Contact's parent organization if exists (e.g., an employee of an Organization)

        TODO: Should this also create a ContactRelationship at the same time?

        :param imis_name: :class:`imis.models.Name`
        :param grandparent: whether or not to also sync the parent of the parent
        (limited to one level up to guard against possible race condition if data stored
        incorrectly in iMIS)
        :type grandparent: bool
        :return: None
        """
        # importing here to avoid circular import
        from myapa.models.contact import Contact

        if grandparent:
            # parent_org = self.sync_from_imis(imis_name, False)
            # TODO: Handle this edge case differently, probably in a util function
            raise NotImplementedError()
        else:
            if imis_name.co_id is not None and imis_name.co_id.strip():
                parent_org = Contact.objects.filter(user__username=imis_name.co_id).first()
                if parent_org is not None:
                    self.company_fk = parent_org
                    self.company = parent_org.company if parent_org.company else self.company
                else:
                    # Create the org Contact and re-sync
                    Contact.update_or_create_from_imis(imis_name.co_id)
                    self._sync_parent_org(imis_name)

    def get_imis_target_relationships(self):
        """Get the :class:`imis.models.Relationship` for which this Contact is the target"""
        return imis_models.Relationship.objects.filter(target_id=self.user.username)

    # MERGE CONFLICT GOO GOGOGOG
    def get_imis_source_relationships(self):
        """Get the :class:`imis.models.Relationship` for which this Contact is the source"""
        return imis_models.Relationship.objects.filter(id=self.user.username)
