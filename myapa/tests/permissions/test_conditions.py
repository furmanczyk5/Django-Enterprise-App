from datetime import timedelta

from django.utils import timezone

from imis.enums.members import ImisMemberTypes
from imis.tests.factories.activity import ImisActivityFactory
from imis.tests.factories.name import ImisNameFactoryAmerica
from imis.tests.factories.order_lines import ImisOrderLinesFactory
from imis.tests.factories.orders import ImisOrdersFactory
from imis.tests.factories.subscriptions import ImisSubscriptionFactory
from imis.utils import sql as sql_utils
from myapa.models.contact import Contact
from myapa.permissions import conditions, utils
from myapa.tests.factories.contact_role import ContactRoleFactory
from planning.global_test_case import GlobalTestCase


class PermissionGroupsTestCase(GlobalTestCase):

    def test_has_member_type(self):
        name_mem = ImisNameFactoryAmerica(
            member_type=ImisMemberTypes.MEM.value
        )
        name_mem.save()
        contact_mem = Contact.update_or_create_from_imis(name_mem.id)
        contact_mem = utils.get_contact_for_groups(contact_mem.user)
        cond = conditions.HasMemberType(ImisMemberTypes.MEM.value)
        self.assertTrue(cond.has_group(contact_mem))

        name_xmem = ImisNameFactoryAmerica(
            member_type=ImisMemberTypes.XMEM.value
        )
        name_xmem.save()
        contact_xmem = Contact.update_or_create_from_imis(name_xmem.id)
        contact_xmem = utils.get_contact_for_groups(contact_xmem.user)
        self.assertFalse(cond.has_group(contact_xmem))

    def test_has_company_member_type(self):
        name_company = ImisNameFactoryAmerica(
            company_record=True,
            member_type=ImisMemberTypes.AGC.value
        )
        name_company.save()
        name_employee = ImisNameFactoryAmerica(
            co_id=name_company.id
        )
        name_employee.save()

        contact = Contact.update_or_create_from_imis(name_employee.id)
        contact = utils.get_contact_for_groups(contact.user)
        cond = conditions.HasCompanyMemberType(ImisMemberTypes.AGC.value)
        self.assertTrue(cond.has_group(contact))

        name_company_dvn = ImisNameFactoryAmerica(
            company_record=True,
            member_type=ImisMemberTypes.DVN.value
        )
        name_company_dvn.save()
        name_employee_dvn = ImisNameFactoryAmerica(
            co_id=name_company_dvn.id
        )
        name_employee_dvn.save()
        contact_dvn = Contact.update_or_create_from_imis(name_employee_dvn.id)
        contact_dvn = utils.get_contact_for_groups(contact_dvn.user)
        self.assertFalse(cond.has_group(contact_dvn))

    def test_has_subscription(self):
        name = ImisNameFactoryAmerica()
        name.save()

        apa_sub = ImisSubscriptionFactory(
            id=name.id,
            product_code='APA',
            status='A'
        )
        apa_sub.save()

        contact = Contact.update_or_create_from_imis(name.id)
        contact = utils.get_contact_for_groups(contact.user)

        cond = conditions.HasSubscription('APA')
        self.assertTrue(cond.has_group(contact))

        cond_aicp = conditions.HasSubscription('AICP')
        self.assertFalse(cond_aicp.has_group(contact))

    def test_has_subscription_product_type(self):
        name = ImisNameFactoryAmerica()
        name.save()

        sub_chapt = ImisSubscriptionFactory(id=name.id, prod_type='CHAPT', status='A')
        sub_chapt.save()

        contact = Contact.update_or_create_from_imis(name.id)
        contact = utils.get_contact_for_groups(contact.user)
        cond = conditions.HasSubscriptionProductType('CHAPT')
        self.assertTrue(cond.has_group(contact))

        # Add a DUES prod_type to same user, check existing condition still applies
        # UPDATE: can't do this because Subscriptions has a compound primary key of
        # (id, product_code). Django complains about models having a column called "id"
        # that is not the primary_key. If you attempt to write multiple records with the
        # same id, the Django ORM appears to just silently replace the one existing record

        # TODO: Investigate workarounds -
        # overwrite django.db.models.base.Model._check_id_field ?
        # write raw SQL? Will that bypass the _check_id_field classmethod?
        # https://docs.djangoproject.com/en/1.11/topics/db/sql/#executing-custom-sql-directly

        # sub_dues = ImisSubscriptionFactory(id=name.id, prod_type='DUES', status='A')
        # sub_dues.save()
        # self.assertEqual(contact.get_imis_subscriptions(status='A').count(), 2)
        # # self.assertTrue(cond.has_group(contact))

        name_dues = ImisNameFactoryAmerica()
        name_dues.save()
        sub_dues = ImisSubscriptionFactory(id=name_dues.id, prod_type='DUES', status='A')
        sub_dues.save()
        contact_dues = Contact.update_or_create_from_imis(name_dues.id)
        contact_dues = utils.get_contact_for_groups(contact_dues.user)
        self.assertFalse(cond.has_group(contact_dues))

    def test_has_committee(self):
        name = ImisNameFactoryAmerica()
        name.save()

        act = ImisActivityFactory(
            id=name.id,
            activity_type='COMMITTEE',
            other_code='ACADEMICS',
            product_code='COMMITTEE/ACADEMICS',
            thru_date=timezone.now() + timedelta(days=180)
        )
        act.save()

        contact = Contact.update_or_create_from_imis(name.id)
        contact = utils.get_contact_for_groups(contact.user)
        cond = conditions.HasCommittee('ACADEMICS')
        self.assertTrue(cond.has_group(contact))

    def test_is_staff(self):
        name_staff_chi = ImisNameFactoryAmerica(co_id='119523')  # APA Chicago Office
        name_staff_chi.save()
        contact = Contact.update_or_create_from_imis(name_staff_chi.id)
        contact = utils.get_contact_for_groups(contact.user)
        cond = conditions.IsStaff()
        self.assertTrue(cond.has_group(contact))

        name = ImisNameFactoryAmerica()
        name.save()
        contact_no_co_id = Contact.update_or_create_from_imis(name.id)
        contact_no_co_id = utils.get_contact_for_groups(contact_no_co_id.user)
        self.assertFalse(cond.has_group(contact_no_co_id))

    def test_has_staff_team(self):
        name = ImisNameFactoryAmerica()
        name.save()

        contact = Contact.update_or_create_from_imis(name.id)
        contact = utils.get_contact_for_groups(contact.user)
        contact.staff_teams = 'EDITOR'
        contact.save()

        cond_editor = conditions.HasStaffTeam('EDITOR')
        self.assertTrue(cond_editor.has_group(contact))

        cond_marketing = conditions.HasStaffTeam('MARKETING')
        self.assertFalse(cond_marketing.has_group(contact))

        contact.staff_teams = 'EDITOR,MARKETING'
        contact.save()
        self.assertTrue(cond_marketing.has_group(contact))

        contact.staff_teams = 'MARKETING,EDITOR'
        contact.save()
        self.assertTrue(cond_marketing.has_group(contact))

        contact.staff_teams = 'RESEARCH,EDITOR'
        contact.save()
        self.assertFalse(cond_marketing.has_group(contact))
        self.assertTrue(cond_editor.has_group(contact))

    def test_has_attr(self):
        name = ImisNameFactoryAmerica(company='')
        name.save()
        contact = Contact.update_or_create_from_imis(name.id)
        contact = utils.get_contact_for_groups(contact.user)

        cond_user = conditions.HasAttrs('user')
        self.assertTrue(cond_user.has_group(contact))

        cond_noexists = conditions.HasAttrs('subscriptions')
        self.assertFalse(cond_noexists.has_group(contact))

        cond_aecom = conditions.HasAttrs(company="AECOM")
        self.assertFalse(cond_aecom.has_group(contact))

        name.company = "AECOM"
        name.save()
        contact.sync_from_imis()
        contact = utils.get_contact_for_groups(contact.user)
        self.assertTrue(cond_aecom.has_group(contact))

    def test_has_related_record(self):
        name = ImisNameFactoryAmerica()
        name.save()
        contact = Contact.update_or_create_from_imis(name.id)
        contact = utils.get_contact_for_groups(contact.user)

        ContactRoleFactory(
            contact=contact,
            role_type="SPEAKER"
        )

        cond_speaker = conditions.HasRelatedRecord(
            related_name="contactrole",
            role_type="SPEAKER"
        )
        self.assertTrue(cond_speaker.has_group(contact))

        cond_provider = conditions.HasRelatedRecord(
            related_name="contactrole",
            role_type="PROVIDER"
        )
        self.assertFalse(cond_provider.has_group(contact))

    def test_is_leadership(self):
        name = ImisNameFactoryAmerica()
        name.save()

        act_big_city = ImisActivityFactory(
            id=name.id,
            product_code="COMMITTEE/BIG CITY PLN DI",
            thru_date=timezone.now() + timedelta(days=180)
        )
        act_big_city.save()

        contact = Contact.update_or_create_from_imis(name.id)
        contact = utils.get_contact_for_groups(contact.user)
        cond = conditions.IsLeadership()
        self.assertTrue(cond.has_group(contact))

        name_nolead = ImisNameFactoryAmerica()
        name_nolead.save()
        act_academics = ImisActivityFactory(
            id=name_nolead.id,
            product_code="COMMITTEE/ACADEMICS",
            thru_date=timezone.now() + timedelta(days=180)
        )
        act_academics.save()
        contact_nolead = Contact.update_or_create_from_imis(name_nolead.id)
        contact_nolead = utils.get_contact_for_groups(contact_nolead.user)

        self.assertFalse(cond.has_group(contact_nolead))

    def test_is_attending(self):

        name = ImisNameFactoryAmerica()
        name.save()
        contact = Contact.update_or_create_from_imis(name.id)

        order = ImisOrdersFactory(
            bt_id=contact.user.username,
            org_code='MTG'
        )
        order_data = sql_utils.format_values(order.__dict__)
        order_ins = sql_utils.make_insert_statement('Orders', order_data)
        sql_utils.do_insert(order_ins, order_data)

        order_line = ImisOrderLinesFactory(
            order_number=order.order_number,
            product_code='TESTCONF19'
        )
        order_line_data = sql_utils.format_values(order_line.__dict__)
        order_line_ins = sql_utils.make_insert_statement('Order_Lines', order_line_data)
        sql_utils.do_insert(order_line_ins, order_line_data)

        contact = utils.get_contact_for_groups(contact.user)

        cond = conditions.IsAttending('TESTCONF19')
        self.assertTrue(cond.has_group(contact))

    def test_is_member(self):
        name = ImisNameFactoryAmerica()
        name.save()

        apa_sub = ImisSubscriptionFactory(
            id=name.id,
            product_code='APA',
            status='A'
        )
        apa_sub.save()

        contact = Contact.update_or_create_from_imis(name.id)
        contact = utils.get_contact_for_groups(contact.user)
        cond = conditions.IsMember()
        self.assertTrue(cond.has_group(contact))

        name_aicp = ImisNameFactoryAmerica()
        name_aicp.save()

        aicp_sub = ImisSubscriptionFactory(
            id=name_aicp.id,
            product_code='AICP',
            status='A'
        )
        aicp_sub.save()

        contact_aicp = Contact.update_or_create_from_imis(name_aicp.id)
        contact_aicp = utils.get_contact_for_groups(contact_aicp.user)
        self.assertFalse(cond.has_group(contact_aicp))

        # Making the AICP member part of a division should return True for IsMember
        name_dvn = ImisNameFactoryAmerica(
            company_record=True,
            member_type=ImisMemberTypes.DVN.value
        )
        name_dvn.save()
        name_aicp.co_id = name_dvn.id
        name_aicp.save()
        contact_aicp = Contact.update_or_create_from_imis(name_aicp.id)
        contact_aicp = utils.get_contact_for_groups(contact_aicp.user)
        self.assertTrue(cond.has_group(contact_aicp))

    def test_is_aicp(self):
        name = ImisNameFactoryAmerica()
        name.save()

        aicp_sub = ImisSubscriptionFactory(
            id=name.id,
            product_code='AICP',
            status='A'
        )
        aicp_sub.save()
        contact = Contact.update_or_create_from_imis(name.id)
        contact = utils.get_contact_for_groups(contact.user)

        cond = conditions.IsAICP()
        self.assertTrue(cond.has_group(contact))

        aicp_sub.status = 'I'
        aicp_sub.save()
        contact = utils.get_contact_for_groups(contact.user)
        self.assertFalse(cond.has_group(contact))
