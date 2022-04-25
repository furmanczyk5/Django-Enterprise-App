from django.test import Client

from cm.enums.claims import ClaimPeriodCodes
from cm.models.claims import Period
from imis.tests.factories.name import ImisNameFactoryAmerica
from myapa.models.contact import Contact
from planning.global_test_case import GlobalTestCase


class AuthenticateWebUserGroupMixinTestCase(GlobalTestCase):

    @classmethod
    def setUpTestData(cls):
        super(AuthenticateWebUserGroupMixinTestCase, cls).setUpTestData()
        Period.objects.get_or_create(code=ClaimPeriodCodes.CAND.value)

    def setUp(self):
        self.client = Client()

    def tearDown(self):
        self.client.logout()

    def test_staff_can_access_create_django_user_view(self):
        resp = self.client.get('/conference/admin/create-django-user/')
        self.assertRedirects(resp, "/login/?next=/conference/admin/create-django-user/")

        name = ImisNameFactoryAmerica(
            co_id='119523'
        )
        name.save()
        contact = Contact.update_or_create_from_imis(name.id)

        self.client.login(username=contact.user.username, password='unittest')
        resp = self.client.get('/conference/admin/create-django-user/')
        self.assertTemplateUsed(resp, 'myapa/newtheme/admin/create-contact.html')

    def test_onsite_conference_admin_can_access_create_django_user_view(self):

        name_not_staff = ImisNameFactoryAmerica()
        name_not_staff.save()
        contact_not_staff = Contact.update_or_create_from_imis(name_not_staff.id)

        self.client.login(username=contact_not_staff.user.username, password='unittest')
        resp = self.client.get('/conference/admin/create-django-user/')
        self.assertTemplateUsed(resp, 'myapa/newtheme/member-access-only.html')

        contact_not_staff.staff_teams = 'TEMP_STAFF'
        contact_not_staff.save()
        self.client.logout()
        self.client.login(username=contact_not_staff.user.username, password='unittest')
        resp = self.client.get('/conference/admin/create-django-user/')
        self.assertTemplateUsed(resp, 'myapa/newtheme/admin/create-contact.html')

    def test_only_aicp_cm_group_can_access_claim_views(self):

        # Anonymous user
        resp = self.client.get('/cm/log/')
        self.assertRedirects(resp, '/login/?next=/cm/log/')

        # Non AICP member
        name = ImisNameFactoryAmerica()
        name.save()
        contact = Contact.update_or_create_from_imis(name.id)
        self.client.login(username=contact.user.username, password='unittest')
        resp = self.client.get('/cm/log/')
        self.assertIn(
            "NO_ACTIVE_CM_LOG",
            resp.context['content_messages']
        )

