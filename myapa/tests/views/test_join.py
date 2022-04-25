import csv
import datetime
import os
import random
import time

from django.conf import settings
from django.test.client import Client
from django.urls import reverse
from faker import Faker

from imis import models as imis_models
from imis.tests.factories.name import ImisNameFactoryAmerica
from imis.tests.factories.subscriptions import ImisSubscriptionFactory
from myapa.forms import join as joinforms
from myapa.models.constants import APACompanyIDs
from myapa.models.contact import Contact
from myapa.permissions.utils import update_user_groups
from myapa.tests.factories import contact as contact_factory
from myapa.views import join as joinviews
from planning.global_test_case import GlobalTestCase


fake = Faker()


def get_state_zip():
    with open(os.path.join(
        settings.BASE_DIR, 'myapa/fixtures/imis_state_zip.csv'
    )) as state_zip_csv:
        reader = csv.reader(state_zip_csv)
        return [x for x in reader]


def get_zip_code_for_state(state_abbr, state_zip=None):
    """
    Get an appropriate zip code for the given state
    :param state_abbr: str, two-letter state abbreviation
    :param state_zip: list
    :return: str
    """
    if not state_zip:
        state_zip = get_state_zip()
    zip_code_choices = [x for x in state_zip if x[0] == state_abbr]
    return random.choice([x[1] for x in zip_code_choices])


class JoinViewsTestCase(GlobalTestCase):

    fixtures = ['cities_light_country.json', 'cities_light_region.json']
    state_zip = []



    @classmethod
    def setUpTestData(cls):

        super(JoinViewsTestCase, cls).setUpTestData()

        cls.state_zip = get_state_zip()
        cls.test_user_data = dict(
            join_account_data=get_join_account_data()
        )

    def setUp(self) -> None:
        self.client = Client()

    def tearDown(self) -> None:
        self.client.logout()

    def test_create_account_form_view(self):
        data = self.test_user_data['join_account_data']
        resp = self.client.post(
            path=reverse('join_account'),
            data=data
        )
        self.assertEqual(resp.status_code, 200)
        time.sleep(5)
        name = imis_models.Name.objects.filter(
            first_name=data['first_name'],
            last_name=data['last_name'],
            birth_date__date=datetime.datetime.strptime(data['birth_date'], '%Y-%m-%d').date(),
            email=data['email'],
            work_phone=data['secondary_phone']
        )
        self.assertEqual(name.count(), 1)

    def test_admin_nonmember_create_view_resolves_correctly(self):
        resp = self.client.get('/myapa/account/create/admin/')
        self.assertEqual(
            resp.resolver_match.func.__name__,
            joinviews.NonMemberJoinViewAdmin.as_view().__name__
        )
        resp = self.client.get('/myapa/account/create/')
        self.assertEqual(
            resp.resolver_match.func.__name__,
            joinviews.NonMemberJoinView.as_view().__name__
        )

    def test_only_admins_can_access_nonmember_join_view_admin(self):
        resp = self.client.get('/myapa/account/create/admin/')
        self.assertRedirects(
            resp,
            '/login/?next=/myapa/account/create/admin/'
        )

        # staff user should see the form
        staff = ImisNameFactoryAmerica(co_id=APACompanyIDs.CHICAGO_OFFICE.value)
        staff.save()
        staff = Contact.update_or_create_from_imis(staff.id)
        staff = update_user_groups(staff.user)

        self.assertTrue(staff.user.is_staff)

        c = Client()
        c.force_login(staff.user)
        resp = c.get("/myapa/account/create/admin/")

        self.assertIn('form', resp.context)

    def test_anonymous_user_gets_correct_form(self):
        # AnonymousUser should see JoinCreateAccountForm
        resp = self.client.get('/join/account/')
        self.assertIsInstance(
            resp.context['form'],
            joinforms.JoinCreateAccountForm
        )

        contact = contact_factory.ContactFactory()
        c = Client()
        c.login(username=contact.user.username, password='unittest')
        resp = c.get('/join/account/')
        self.assertIsInstance(
            resp.context['form'],
            joinforms.JoinUpdateAccountForm
        )

    def test_member_not_up_for_renewal_gets_correct_response(self):
        contact = contact_factory.ContactFactory()
        name = ImisNameFactoryAmerica(
            id=contact.user.username
        )
        name.save()

        membership_sub = ImisSubscriptionFactory(
            id=name.id,
            product_code="APA",
            copies_paid=1,
            bill_copies=1,
            status='A'
        )
        membership_sub.save()

        template_name = "myapa/newtheme/join/not-up-for-renewal.html"

        self.client.login(username=contact.user.username, password='unittest')
        resp = self.client.get('/join/account/')
        self.assertTemplateUsed(
            resp,
            template_name
        )

        # Membership changes copies_paid in iMIS
        membership_sub.copies_paid = 0
        membership_sub.save()

        resp = self.client.get('/join/account/')
        self.assertTemplateNotUsed(
            resp,
            template_name
        )

        membership_sub.copies_paid = 1
        membership_sub.save()
        # anonymous users should never see the not-up-for-renewal template
        self.client.logout()
        resp = self.client.get('/join/account/')
        self.assertTemplateNotUsed(
            resp,
            template_name
        )

    def test_aicp_gets_dues_added_to_cart_on_join_or_renew(self):
        pass


def get_join_account_data():
    email = fake.email()
    password = 'unittest'
    state_abbr = fake.state_abbr()

    join_account_data = dict(
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        birth_date=fake.date_of_birth().strftime('%Y-%m-%d'),
        email=email,
        verify_email=email,
        password=password,
        verify_password=password,
        password_hint='B',
        password_answer=fake.city(),
        secondary_phone=str(random.randrange(1000000000, 9999999999)),
        address1=fake.street_address(),
        city=fake.city(),
        state=state_abbr,
        zip_code=get_zip_code_for_state(state_abbr),
        country="United States"
    )
    return join_account_data
