import random
from datetime import datetime
from unittest import skip

import pytz
from django.contrib.auth.models import User

from consultants.models import Consultant
from imis import models as imis_models
from imis.enums import members
from imis.tests.factories import (name as name_facts, name_address as name_addr_facts,
                                  ind_demographics as indd_facts, subscriptions as sub_facts)
from imis.utils import sql as sql_utils
from imis.utils.addresses import get_primary_address
from myapa.models import constants
from myapa.models import proxies
from myapa.models.contact import Contact
from myapa.models.contact_tag_type import ContactTagType
from myapa.tests.factories import contact as contact_factory
from myapa.tests.factories import profile as profile_factory
from planning.global_test_case import GlobalTestCase

CHAPTER_CODES = [i[0] for i in constants.CHAPTER_CHOICES]
SALARY_CODES = [i[0] for i in constants.SALARY_CHOICES_ALL]


class ContactTestCase(GlobalTestCase):

    def setUp(self):
        self.user = contact_factory.UserFactory()
        self.contact = contact_factory.ContactFactory()
        # An INDIVIDUAL with a static name
        self.brendanaquits = contact_factory.ContactFactoryIndividual(
            first_name='Mark',
            last_name='Brendanawicz',
            job_title='City Planner',
            company='City of Pawnee'
        )
        # An ORGANIZATION with a static name
        self.pawnee = contact_factory.ContactFactoryOrganization(
            company="City of Pawnee"
        )

        # iMIS users
        self.imis_user_american = name_facts.ImisNameFactoryAmerica()
        self.imis_user_american.save()

    def test_user_factory_works(self):
        self.assertIsNotNone(self.user.pk)
        self.assertFalse('unittest' in self.user.password)

    def test_get_imis_name(self):
        """Make sure our Factory created iMIS user gets saved to Name"""
        self.assertTrue(imis_models.Name.objects.filter(
            id=self.imis_user_american.id).exists()
        )

    def test_get_correct_country_code(self):
        self.contact.country = "United States"
        self.contact.save()
        self.assertEqual(self.contact.get_country_type_code(), "CC")

        self.contact.country = None
        self.contact.save()
        self.assertIsNotNone(self.contact.get_country_type_code())

    def test_contact_save_sets_correct_title(self):
        self.assertEqual(self.brendanaquits.title, 'Mark Brendanawicz')

        self.brendanaquits.designation = 'FAICP'
        self.brendanaquits.save()
        self.assertEqual(self.brendanaquits.title, 'Mark Brendanawicz, FAICP')

        self.brendanaquits.designation = None
        self.brendanaquits.save()
        self.assertEqual(self.brendanaquits.title, 'Mark Brendanawicz')

        self.brendanaquits.designation = ''
        self.brendanaquits.save()
        self.assertEqual(self.brendanaquits.title, 'Mark Brendanawicz')

        self.assertEqual(self.pawnee.title, "City of Pawnee")

    def test_full_title(self):
        self.assertEqual(self.brendanaquits.full_title(), "Mark Brendanawicz")

        self.brendanaquits.middle_name = 'Norton'
        self.brendanaquits.save()
        self.assertEqual(self.brendanaquits.full_title(), "Mark N. Brendanawicz")

        self.brendanaquits.suffix_name = 'DDS'
        self.brendanaquits.save()
        self.assertEqual(self.brendanaquits.full_title(), "Mark N. Brendanawicz DDS")

        self.brendanaquits.designation = 'FAICP'
        self.brendanaquits.save()
        self.assertEqual(self.brendanaquits.full_title(), 'Mark N. Brendanawicz DDS, FAICP')

        self.assertEqual(self.pawnee.full_title(), "City of Pawnee")

    def test_set_address_from_imis(self):

        # Create a Contact, then create an imis Name with the Contact's username
        contact = contact_factory.ContactFactory()
        imis_name = name_facts.ImisNameFactory(id=contact.user.username)
        imis_name.save()

        self.assertIsNone(contact.address1)
        self.assertIsNone(contact.city)
        self.assertIsNone(contact.country)

        american_address_1 = name_addr_facts.ImisNameAddressFactoryAmerica(
            id=contact.user.username,
            purpose="Work Address",
            preferred_mail=False
        )
        american_address_1.save()

        american_address_2 = name_addr_facts.ImisNameAddressFactoryAmerica(
            id=contact.user.username,
            purpose="Work Address",
            preferred_mail=False
        )
        american_address_2.save()

        american_address_3 = name_addr_facts.ImisNameAddressFactoryAmerica(
            id=contact.user.username,
            preferred_mail=True,
            purpose="Work Address"
        )
        american_address_3.save()

        primary_address = get_primary_address(
            username=contact.user.username
        )
        self.assertIsNotNone(primary_address)

        self.assertEqual(primary_address.address_num, american_address_3.address_num)

        # sync from iMIS
        contact._set_address_from_imis(primary_address)
        contact.save()
        self.assertEqual(contact.address1, american_address_3.address_1)
        self.assertEqual(contact.city, american_address_3.city)
        self.assertEqual(contact.state, american_address_3.state_province)
        self.assertEqual(contact.zip_code, american_address_3.zip)
        self.assertEqual(contact.country, american_address_3.country)

    def test_set_contact_info_from_imis(self):
        contact = contact_factory.ContactFactory()
        imis_name = name_facts.ImisNameFactoryAmerica(id=contact.user.username)
        imis_name.save()

        contact._set_contact_info_from_imis(imis_name)
        contact.save()
        self.assertEqual(contact.company, imis_name.company)
        self.assertEqual(contact.email, imis_name.email)
        self.assertEqual(contact.phone, imis_name.home_phone[:20])
        self.assertEqual(contact.secondary_phone, imis_name.work_phone[:20])
        self.assertEqual(contact.cell_phone, imis_name.mobile_phone[:20])

    def test_set_bio_info_from_imis(self):
        contact = contact_factory.ContactFactory()
        imis_name = name_facts.ImisNameFactoryAmerica(id=contact.user.username)
        imis_name.save()

        contact._set_bio_info_from_imis(imis_name)
        contact.save()
        self.assertEqual(contact.prefix_name, imis_name.prefix)
        self.assertEqual(contact.first_name, imis_name.first_name)
        self.assertEqual(contact.middle_name, imis_name.middle_name)
        self.assertEqual(contact.last_name, imis_name.last_name)
        self.assertEqual(contact.suffix_name, imis_name.suffix)
        self.assertEqual(contact.designation, imis_name.designation)

        self.assertEqual(contact.job_title, imis_name.title)
        self.assertEqual(contact.birth_date, imis_name.birth_date)

        self.assertEqual(contact.user.first_name, imis_name.first_name)
        self.assertEqual(contact.user.last_name, imis_name.last_name)
        self.assertEqual(contact.user.email, imis_name.email)

    def test_set_chapter_from_imis(self):
        contact = contact_factory.ContactFactory()
        imis_name = name_facts.ImisNameFactoryAmerica(id=contact.user.username)
        imis_name.save()

        contact._set_chapter_from_imis(imis_name)
        contact.save()

        self.assertEqual(contact.chapter, imis_name.chapter)

    @skip
    def test_set_org_type_from_imis(self):
        contact = contact_factory.ContactFactoryOrganization()
        imis_name = name_facts.ImisNameFactoryAmerica(
            id=contact.user.username,
            member_type=members.ImisMemberTypes.DVN.value
        )
        imis_name.save()

        contact_pri = contact_factory.ContactFactoryOrganization()
        imis_name_pri = name_facts.ImisNameFactoryAmerica(
            id=contact_pri.user.username,
            member_type=members.ImisMemberTypes.PRI.value
        )

        contact_ppri = contact_factory.ContactFactoryOrganization()
        imis_name_ppri = name_facts.ImisNameFactoryAmerica(
            id=contact_ppri.user.username,
            member_type=members.ImisMemberTypes.PPRI.value
        )
        imis_name_ppri.save()

        contact._set_org_type_from_imis(imis_name)
        contact.save()
        self.assertNotEqual(
            contact.organization_type,
            constants.DjangoOrganizationTypes.CONSULTANT.value
        )

        contact_pri._set_org_type_from_imis(imis_name_pri)
        contact_pri.save()
        self.assertEqual(
            contact_pri.organization_type,
            constants.DjangoOrganizationTypes.CONSULTANT.value
        )

        contact_ppri._set_org_type_from_imis(imis_name_ppri)
        contact_ppri.save()
        self.assertEqual(
            contact_ppri.organization_type,
            constants.DjangoOrganizationTypes.CONSULTANT.value
        )

    def test_set_member_type_from_imis(self):
        contact = contact_factory.ContactFactory()
        imis_name = name_facts.ImisNameFactoryAmerica(id=contact.user.username)
        imis_name.save()

        self.assertIn(imis_name.member_type, name_facts.MEMBER_TYPES)

        contact._set_member_type_from_imis(imis_name)
        contact.save()
        self.assertEqual(contact.member_type, imis_name.member_type)

    def test_default_contact_type_proxies(self):
        contact = contact_factory.ContactFactory()
        # contact_type defaults to "INDIVIDUAL"...
        self.assertEqual(contact.contact_type, constants.DjangoContactTypes.INDIVIDUAL.value)
        # ...which by default also means it should be an IndividualContact proxy
        self.assertIsInstance(contact, proxies.IndividualContact)

        contact_org = contact_factory.ContactFactoryOrganization()
        self.assertEqual(contact_org.contact_type, constants.DjangoContactTypes.ORGANIZATION.value)
        self.assertIsInstance(contact_org, proxies.Organization)

    @skip
    def test_set_contact_type_from_imis(self):
        contact = contact_factory.ContactFactoryIndividual()

        imis_name = name_facts.ImisNameFactoryAmerica(
            id=contact.user.username,
            company_record=False
        )
        imis_name.save()

        contact._set_contact_type_from_imis(imis_name)
        # TODO see note below. This save only "works" because the default is INDIVIDUAL
        contact.save()
        self.assertEqual(contact.contact_type, constants.DjangoContactTypes.INDIVIDUAL.value)

        # Change the iMIS record, then re-sync and test
        imis_name.company_record = True
        imis_name.id = contact.user.username
        imis_name.save()

        contact._set_contact_type_from_imis(imis_name)
        # TODO WHY does calling save() here reset the contact_type to INDIVIDUAL?
        # UPDATE: after calling the super(Contact, self).save in Contact, the value of
        # contact_type is set to NULL, so it gets applied the default of INDIVIDUAL and
        # causes this test to fail. Removing the `default="INDIVIDUAL"` keyword argument to
        # Contact.contact_type will make this test pass after uncommenting the
        # following contact.save() line.
        # The reason removing the default kwarg works is because
        # SubclassableModel __init__ method calls its django.db.Models super().__init__
        # before assigning its __class__ with get_subclass
        # Using the ImisSyncMixin.sync_from_imis works because it instantiates
        # the proper proxy model
        contact.save()
        self.assertEqual(contact.contact_type, constants.DjangoContactTypes.ORGANIZATION.value)

    def test_set_salary_range_and_secondary_email_from_imis(self):
        contact = contact_factory.ContactFactory()
        imis_name = name_facts.ImisNameFactoryAmerica(
            id=contact.user.username
        )
        imis_name.save()
        imis_ind_demo = indd_facts.ImisIndDemographicsFactory(
            id=contact.user.username,
            salary_range='D'
        )
        imis_ind_demo.save()

        # we're explicitly assigning an Ind_Demographics to a test user here,
        # so the get_imis_ind_demographics should not return None
        indemo = contact.get_imis_ind_demographics()
        self.assertIsNotNone(indemo)

        contact._set_demographics_data_from_imis(indemo)
        self.assertEqual(contact.salary_range, indemo.salary_range)
        self.assertEqual(contact.secondary_email, indemo.email_secondary)

    def test_set_company_is_apa(self):
        contact = contact_factory.ContactFactoryOrganization(
            member_type=random.choice(
                [x for x in name_facts.MEMBER_TYPES
                 if x not in (members.ImisMemberTypes.CHP.value, members.ImisMemberTypes.DVN.value)]
            )
        )
        self.assertFalse(contact._set_company_is_apa())

        contact_chapter = contact_factory.ContactFactoryOrganization(
            member_type=members.ImisMemberTypes.CHP.value
        )
        contact_chapter._set_company_is_apa()
        contact_chapter.save()
        self.assertTrue(contact_chapter.company_is_apa)

        contact_division = contact_factory.ContactFactoryOrganization(
            member_type=members.ImisMemberTypes.DVN.value
        )
        contact_division._set_company_is_apa()
        contact_division.save()
        self.assertTrue(contact_division.company_is_apa)

    @skip
    def test_update_consultant_profile_from_imis(self):
        contact_consultant = contact_factory.ContactFactoryOrganization()

        # TODO Assigning an organization_type on creation fails because
        # it tries to assign an unsaved related contact object
        # consultants.models.Consultant has class_query_args of CONSULTANT
        # Instead, should we just instantiate a Consultant model directly?
        contact_consultant.organization_type = "CONSULTANT"
        contact_consultant.save()
        self.assertTrue(ContactTagType.objects.filter(contact=contact_consultant).exists())

        consultant_proxy = Consultant.objects.filter(
            company=contact_consultant.company
        ).first()
        self.assertIsNotNone(consultant_proxy)

        org_profile = profile_factory.OrganizationProfileFactory(
            contact=contact_consultant
        )
        self.assertEqual(contact_consultant, org_profile.contact)

        self.assertEqual(consultant_proxy.organizationprofile, org_profile)

        imis_sub = sub_facts.ImisSubscriptionFactory(
            id=contact_consultant.user.username,
            product_code="CSCC",
            paid_thru=datetime(2018, 6, 30, tzinfo=pytz.utc)
        )
        imis_sub.save()

        contact_subscriptions = contact_consultant.get_imis_subscriptions()
        self.assertTrue(contact_subscriptions.exists())

        consultant_subscriptions = consultant_proxy.get_imis_subscriptions(
            product_code="CSCC"
        )
        self.assertTrue(consultant_subscriptions.exists())

        imis_sub_2 = sub_facts.ImisSubscriptionFactory(
            id=contact_consultant.user.username,
            product_code="CSCC",
            paid_thru=datetime(2017, 6, 30, tzinfo=pytz.utc)
        )
        imis_sub_2.save()

        imis_sub_3 = sub_facts.ImisSubscriptionFactory(
            id=contact_consultant.user.username,
            product_code="CSCC",
            paid_thru=datetime(2019, 6, 30, tzinfo=pytz.utc)
        )
        imis_sub_3.save()

        consultant_proxy.organizationprofile.set_consultant_listing_until()
        self.assertEqual(
            consultant_proxy.organizationprofile.consultant_listing_until,
            imis_sub_3.paid_thru
        )

    def test_set_parent_organization(self):
        company_contact = contact_factory.ContactFactory()

        parent_org = name_facts.ImisNameFactoryAmerica(
            id=company_contact.user.username,
            company_record=True
        )
        parent_org.save()

        company_contact._set_contact_type_from_imis(parent_org)
        self.assertEqual(
            company_contact.contact_type,
            constants.DjangoContactTypes.ORGANIZATION.value
        )

        employee_contact = contact_factory.ContactFactory()
        employee_of_parent_org = name_facts.ImisNameFactoryAmerica(
            id=employee_contact.user.username,
            co_id=parent_org.id
        )
        employee_of_parent_org.save()

        employee_contact._sync_parent_org(employee_of_parent_org)
        employee_contact.save()

        self.assertEqual(employee_contact.company_fk, company_contact)
        self.assertEqual(employee_contact.company, company_contact.company)

        no_parent_org_contact = contact_factory.ContactFactory()
        no_parent_org_name = name_facts.ImisNameFactoryAmerica(
            id=no_parent_org_contact.user.username
        )
        no_parent_org_name.save()

        no_parent_org_contact._sync_parent_org(no_parent_org_name)
        no_parent_org_contact.save()
        self.assertIsNone(no_parent_org_contact.company_fk)

        # Testing an org that exists in iMIS but not Django yet
        imis_org = name_facts.ImisNameFactoryAmerica(
            id='SOMECO',
            company_record=True
        )
        imis_org.save()
        imis_employee = name_facts.ImisNameFactoryAmerica(co_id=imis_org.id)
        imis_employee.save()
        django_employee = Contact.update_or_create_from_imis(imis_employee.id)
        self.assertIsNotNone(django_employee.company_fk)

    def test_create_individual_contact_from_imis(self):
        ind_member = name_facts.ImisNameFactoryAmerica()
        ind_member.save()
        contact = Contact.update_or_create_from_imis(ind_member.id)
        self.assertEqual(contact.user.username, ind_member.id)
        self.assertEqual(contact.company, ind_member.company)
        self.assertEqual(contact.email, ind_member.email)

        # iMIS...(╯°□°）╯︵ ┻━┻
        self.assertEqual(contact.phone[:20], ind_member.home_phone[:20])
        self.assertEqual(contact.secondary_phone[:20], ind_member.work_phone[:20])
        self.assertEqual(contact.cell_phone[:20], ind_member.mobile_phone[:20])

        self.assertEqual(contact.prefix_name, ind_member.prefix)
        self.assertEqual(contact.first_name, ind_member.first_name)
        self.assertEqual(contact.middle_name, ind_member.middle_name)
        self.assertEqual(contact.last_name, ind_member.last_name)
        self.assertEqual(contact.suffix_name, ind_member.suffix)
        self.assertEqual(contact.designation, ind_member.designation)
        self.assertEqual(contact.job_title, ind_member.title)
        self.assertEqual(contact.birth_date, ind_member.birth_date)
        self.assertEqual(contact.first_name, contact.user.first_name)

        django_user = contact.user
        self.assertIsNotNone(django_user)
        self.assertEqual(django_user.username, ind_member.id)
        self.assertEqual(django_user.first_name, ind_member.first_name)
        self.assertEqual(django_user.last_name, ind_member.last_name)
        self.assertEqual(django_user.email, ind_member.email)

        self.assertEqual(contact.chapter, ind_member.chapter)

        self.assertEqual(contact.member_type, ind_member.member_type)

    def test_is_aicp(self):
        contact = contact_factory.ContactFactory()

        subscription = sub_facts.ImisSubscriptionFactory(
            id=contact.user.username,
            product_code="APA",
            status='A'
        )
        subscription.save()

        self.assertFalse(contact.is_aicp)

        subscription.product_code = "AICP"
        subscription.save()

        self.assertTrue(contact.is_aicp)

    def test_is_aicp_prorate(self):
        contact = contact_factory.ContactFactory()

        sub_aicp = sub_facts.ImisSubscriptionFactory(
            id=contact.user.username,
            product_code="AICP",
            status='A'
        )
        sub_aicp.save()

        self.assertFalse(contact.is_aicp_prorate)

        sub_aicp_prorate = sub_facts.ImisSubscriptionFactory(
            id=contact.user.username,
            product_code="AICP_PRORATE",
            status='A'
        )
        sub_aicp_prorate.save()

        self.assertTrue(contact.is_aicp_prorate)

    def test_is_international(self):
        contact = contact_factory.ContactFactory(country=None)
        name_addr = name_addr_facts.ImisNameAddressFactory(
            id=contact.user.username,
            preferred_mail=True,
            country="United States"
        )
        name_addr.save()
        self.assertFalse(contact.is_international)

        name_addr.country = "Canada"
        name_addr.save()
        self.assertTrue(contact.is_international)

        name_addr.country = ''
        name_addr.save()
        self.assertFalse(contact.is_international)

    def test_is_new_member(self):
        name_nonrenewing = name_facts.ImisNameFactoryAmerica(category='')
        name_nonrenewing.save()
        contact_nonrenewing = Contact.update_or_create_from_imis(name_nonrenewing.id)
        self.assertFalse(contact_nonrenewing.is_new_member)

        name_renewing = name_facts.ImisNameFactoryAmerica(
            category=members.ImisMemberCategories.NM1.value
        )
        name_renewing.save()
        contact_renewing = Contact.update_or_create_from_imis(name_renewing.id)
        self.assertTrue(contact_renewing.is_new_member)

    def test_is_new_membership_qualified(self):
        contact_student = contact_factory.ContactFactory(
            member_type=members.ImisMemberTypes.STU.value
        )
        self.assertTrue(contact_student.is_new_membership_qualified)

        contact_nonmember = contact_factory.ContactFactory(
            member_type=members.ImisMemberTypes.NOM.value
        )
        self.assertTrue(contact_nonmember.is_new_membership_qualified)

        contact_member = contact_factory.ContactFactory(
            member_type=random.choice(
                [x for x in name_facts.MEMBER_TYPES if x not in
                 (members.ImisMemberTypes.STU.value, members.ImisMemberTypes.NOM.value)]
            )
        )
        self.assertFalse(contact_member.is_new_membership_qualified)

        contact_xstu = contact_factory.ContactFactory(member_type=members.ImisMemberTypes.XSTU.value)
        self.assertFalse(contact_xstu.is_new_membership_qualified)

    def test_imis_create(self):
        contact = Contact(
            first_name="Mark",
            last_name="Brendanawicz",
            email="mbrendanawicz@cityofpawnee.org",
            city="Pawnee",
            state="IN",
            country="United States",
            secondary_phone="213-555-1234",
            birth_date=datetime(1978, 3, 12, tzinfo=pytz.utc),
            secondary_email='test@unittest.org'
        )

        name = contact.imis_create()
        contact_factory.UserFactory(username=name.id, contact=contact)

        self.assertEqual(contact.first_name, name.first_name)
        self.assertEqual(contact.last_name, name.last_name)
        self.assertEqual(contact.email, name.email)

        ind_demo = imis_models.IndDemographics.objects.get(id=contact.user.username)
        self.assertEqual(ind_demo.email_secondary, contact.secondary_email)
        self.assertTrue(imis_models.OrgDemographics.objects.filter(id=contact.user.username).exists())
        self.assertTrue(imis_models.MailingDemographics.objects.filter(
            id=contact.user.username
        ).exists())

        name_log_select = sql_utils.make_select_statement_no_model(
            table_name='Name_Log',
            fields=['id', 'log_text'],
            exclude_id_field=False
        )

        name_log_select += " WHERE ID = %s"
        name_log_result = sql_utils.do_select(name_log_select, [str(name.id)])

        self.assertEqual(
            name_log_result[0].LOG_TEXT,
            '{} {}'.format(contact.first_name, contact.last_name)
        )

        self.assertTrue(
            imis_models.NameFin.objects.filter(id=contact.user.username).exists()
        )

        self.assertTrue(
            imis_models.NamePicture.objects.filter(id=contact.user.username).exists()
        )

        name_security_select = sql_utils.make_select_statement(
            'NameSecurity',
            exclude_id_field=False
        )
        name_security_select += " WHERE ID = %s"
        name_security_result = sql_utils.do_select(name_security_select, [str(name.id)])
        self.assertTrue(len(name_security_result) > 0)

        name_security_groups_select = sql_utils.make_select_statement_no_model(
            table_name='Name_Security_Groups',
            fields=['id', 'security_group'],
            exclude_id_field=False
        )

        name_security_groups_select += " WHERE ID = %s"
        name_security_groups_result = sql_utils.do_select(
            name_security_groups_select,
            [str(name.id)]
        )
        self.assertTrue(len(name_security_groups_result) > 0)

        Contact.objects.filter(pk=contact.pk).delete()
        User.objects.filter(username=name.id).delete()

    def test_push_addresses_to_imis(self):
        contact = Contact(
            first_name="Mark",
            last_name="Brendanawicz",
            email="mbrendanawicz@cityofpawnee.org",
            address1='1 Paunchburger Way',
            city="Pawnee",
            state="IN",
            country="United States",
            zip_code='50012',
            secondary_phone="213-555-1234",
            birth_date=datetime(1978, 3, 12, tzinfo=pytz.utc),
            secondary_email='test@unittest.org',
            company='City of Pawnee'
        )

        name = contact.imis_create()
        user = User.objects.create(
            username=name.id,
            first_name=name.first_name,
            last_name=name.last_name,
            email=name.email
        )
        contact.user = user
        contact.save()

        self.assertFalse(contact.get_imis_name_address().exists())

        contact.push_addresses_to_imis()
        addresses = contact.get_imis_name_address()
        self.assertTrue(addresses.exists())

        address = addresses.first()

        self.assertMultiLineEqual(
            address.full_address,
            '1 Paunchburger Way\rPawnee, IN 50012\rUNITED STATES'
        )

        self.assertEqual(
            address.company_sort,
            "CITY OF PAWNEE"
        )
