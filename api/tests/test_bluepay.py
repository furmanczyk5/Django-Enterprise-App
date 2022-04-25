import json
import os
import random
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.conf import settings
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from api.clients import bluepay
from imis.tests.factories.name import ImisNameFactoryAmerica
from imis.tests.factories.name_address import ImisNameAddressFactoryAmerica
from myapa.models.contact import Contact
from planning.global_test_case import GlobalTestCase
from store.models.factories.product import MembershipProductFactory
from store.models.factories.product_price import MembershipProductPriceFactory
from store.views.checkout_views import BluepayReturnView


def construct_client():
    return bluepay.BluePay(
        account_id=settings.BLUEPAY_SANDBOX_ACCOUNT_ID,
        secret_key=settings.BLUEPAY_SANDBOX_SECRET_KEY,
        mode='TEST'
    )


def generate_member():
    name = ImisNameFactoryAmerica(company_record=False)
    name.save()
    name_address = ImisNameAddressFactoryAmerica(id=name.id, preferred_bill=True)
    name_address.save()
    return name, name_address


def get_cc_information():
    return dict(
        card_number='4111111111111111',
        card_expire=(timezone.now() + timedelta(days=(365*random.randint(1, 5)))).strftime('%m%y'),
        cvv2='123'
    )


class BluePayTestCase(GlobalTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        for fixture in ['bluepay_shpf_approved', 'bluepay_shpf_declined', 'bluepay_shpf_missing']:
            with open(os.path.join(settings.BASE_DIR, 'store/fixtures/{}.json'.format(fixture))) as infile:
                setattr(cls, fixture, json.load(infile))

        cls.membership_product = MembershipProductFactory()

        headers = ['code', 'imis_reg_class', 'price', 'title']
        data = [
            ('A', 'APA', Decimal('189.00'), 'Salary Range A'),
            ('AA', None, Decimal('63.00'), 'Outside US Regular Member AA'),
            ('B', None, Decimal('189.00'), 'Salary Range B'),
            ('BB', None, Decimal('100.00'), 'Outside US Regular Member BB'),
            ('C', 'APA', Decimal('221.00'), 'Salary Range C'),
            ('CC', None, Decimal('184.00'), 'Outside US Regular Member CC'),
            ('D', 'APA', Decimal('257.00'), 'Salary Range D'),
            ('E', 'APA', Decimal('284.00'), 'Salary Range E'),
            ('F', 'APA', Decimal('310.00'), 'Salary Range F'),
            ('G', 'APA', Decimal('336.00'), 'Salary Range G'),
            ('H', 'APA', Decimal('362.00'), 'Salary Range H'),
            ('I', 'APA', Decimal('394.00'), 'Salary Range I'),
            ('J', 'APA', Decimal('436.00'), 'Salary Range J'),
            ('L', None, Decimal('79.00'), None),
            ('M', None, Decimal('63.00'), 'US Planning Board Member (Salary Code M)'),
            ('N', None, Decimal('95.00'), 'US Retired Member (Salary Code N)'),
            ('NN', None, Decimal('95.00'), 'Outside US Retired Member NN'),
            ('O', None, Decimal('68.00'), 'US Life Member (Salary Code O)'),
            ('OO', None, Decimal('68.00'), 'Outside US Life Member OO'),
            ('P', 'APA', Decimal('431.00'), 'Salary Range P')
        ]

        for row in data:
            MembershipProductPriceFactory.create(product=cls.membership_product, **dict(zip(headers, row)))

    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.name, self.name_address = generate_member()
        self.contact = Contact.update_or_create_from_imis(self.name.id)

    def test_generate_url(self):
        client = construct_client()
        params = bluepay.utils.get_default_rebilling_params()
        params.update({
            'reb_start_date': '1 MONTH',
            'reb_frequency': '10 MONTHS',
            'reb_amount': bluepay.utils.get_rebilling_amount(
                '10 MONTHS',
                self.membership_product.prices.filter(code='D').first()
            )
        })
        url = client.generate_url(**params)
        self.assertIn('REB_EXPR=10%20MONTHS', url)
        self.assertIn('AMOUNT=18%2E90', url)

    def test_contact_get_bluepay_customer_information(self):

        self.assertDictEqual(
            self.contact.get_bluepay_customer_information(),
            dict(
                name1=self.name.first_name,
                name2=self.name.last_name,
                addr1=self.name_address.address_1,
                addr2=self.name_address.address_2,
                city=self.name_address.city,
                state=self.name_address.state_province,
                zipcode=self.name_address.zip,
                country=self.name_address.country,
                phone=self.name_address.phone
            )
        )

    @patch('api.clients.bluepay.BluePay.process')
    def test_bluepay_payment(self, mock_bluepay_process):
        payment = self.get_recurring_payment()
        payment.process()
        self.assertTrue(mock_bluepay_process.called)
        print(mock_bluepay_process.return_value)

    def get_recurring_payment(self):
        payment = construct_client()
        payment.set_customer_information(**self.contact.get_bluepay_customer_information())
        payment.set_cc_information(**get_cc_information())
        rebill_params = {
            'reb_expr': '1 MONTH',
            'reb_cycles': '10',
            'reb_amount': bluepay.utils.get_rebilling_amount(
                '10 MONTHS',
                self.membership_product.prices.filter(code='B').first()
            )
        }
        payment.sale(amount=rebill_params['reb_amount'])
        payment.set_rebilling_information(
            reb_first_date=timezone.now().strftime('%Y-%m-%d'),
            **rebill_params
        )
        return payment

    def get_single_payment(self, amount: str):
        payment = construct_client()
        payment.set_customer_information(**self.contact.get_bluepay_customer_information())
        payment.set_cc_information(**get_cc_information())
        payment.sale(amount=amount)
        return payment

    def test_bluepay_transaction_status_function_mapping(self):
        resp = self.client.get(reverse('store:bluepay_return'), data=self.bluepay_shpf_approved)
        self.assertEqual(resp.content.decode('utf-8'), 'Approved')

        resp = self.client.get(reverse('store:bluepay_return'), data=self.bluepay_shpf_declined)
        self.assertEqual(resp.content.decode('utf-8'), 'Declined')

        resp = self.client.get(reverse('store:bluepay_return'), data=self.bluepay_shpf_missing)
        self.assertEqual(resp.content.decode('utf-8'), 'Missing')

        resp = self.client.get(reverse('store:bluepay_return'), data={'Result': 'Aviato'})
        self.assertEqual(resp.content.decode('utf-8'), 'Declined')

        resp = self.client.get(reverse('store:bluepay_return'), data={'What Result?': 'Huh?'})
        self.assertEqual(resp.content.decode('utf-8'), 'Declined')

    def test_get_django_autodraft_cart_submit_parameters(self):
        client = self.get_recurring_payment()
        data = self.bluepay_shpf_approved
        req = self.factory.get(reverse('store:bluepay_return'), data=data)
        params = bluepay.utils.get_django_autodraft_cart_submit_parameters(
            self.contact.user.username,
            client.amount,
            1,
            10,
            req
        )
        self.assertListEqual(
            params,
            [
                self.contact.user.username,
                Decimal(client.amount),
                data['CARD_TYPE'][0],
                data['PAYMENT_ACCOUNT'][0][-4],
                data['CARD_EXPIRE'][0],
                data['RRNO'][0],
                1,
                10,
                data['AUTH_CODE'][0],
            ]
        )

    def test_return_url_with_username(self):
        payment = self.get_recurring_payment()
        params = bluepay.utils.get_default_rebilling_params()
        params.update({
            'reb_start_date': '1 MONTH',
            'reb_frequency': '10 MONTHS',
            'reb_amount': bluepay.utils.get_rebilling_amount(
                '10 MONTHS',
                self.membership_product.prices.filter(code='D').first()
            ),
            'return_url': reverse('store:bluepay_return', kwargs=dict(username=self.contact.user.username))
        })
        payment.generate_url(**params, custom_id=self.contact.user.username)
        data = self.bluepay_shpf_approved
        url = reverse('store:bluepay_return', kwargs=dict(username=payment.custom_id1))
        resp = self.client.get(url, data=data)
        self.assertEqual(resp.text(), str(self.contact.user))
