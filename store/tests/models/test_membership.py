from decimal import Decimal

from django.test import TestCase

from myapa.tests.factories.contact import ContactFactoryIndividual, Contact, AdminUserFactory
from store.models.factories import product as product_factory
from store.models.factories.product_price import ProductPriceFactory
from store.models.membership import BluepayMembershipPaymentDispatcher
from store.models.purchase import Purchase
from store.models import settings as store_settings


class MembershipPaymentDispatcherTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.admin_user = AdminUserFactory()

        product_price_headers = ['code', 'imis_reg_class', 'price', 'title']

        cls.membership_product = product_factory.MembershipProductFactory()
        membership_prices = [
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
        for row in membership_prices:
            ProductPriceFactory.create(
                product=cls.membership_product,
                **dict(zip(product_price_headers, row))
            )

        cls.chapter_product = product_factory.ChapterProductFactory()
        chapter_prices = [
            ('A', None, Decimal('47.00'), 'Member Price A'),
            ('B', None, Decimal('47.00'), 'Member Price B'),
            ('C', None, Decimal('55.00'), 'Member Price C'),
            ('D', None, Decimal('64.00'), 'Member Price D'),
            ('E', None, Decimal('71.00'), 'Member Price E'),
            ('F', None, Decimal('78.00'), 'Member Price F'),
            ('G', None, Decimal('84.00'), 'Member Price G'),
            ('H', None, Decimal('91.00'), 'Member Price H'),
            ('I', None, Decimal('99.00'), 'Member Price I'),
            ('J', None, Decimal('109.00'), 'Member Price J'),
            ('K', '', Decimal('0.00'), ''),
            ('KK', '', Decimal('0.00'), ''),
            ('L', None, Decimal('20.00'), None),
            ('N', '', Decimal('10.00'), 'Retired Member Price'),
            ('NN', '', Decimal('10.00'), 'Retired International Member'),
            ('O', '', Decimal('10.00'), 'Life Member Price'),
            ('OO', '', Decimal('10.00'), 'Life International Member'),
            ('P', None, Decimal('108.00'), 'Member Price P')
        ]
        for row in chapter_prices:
            ProductPriceFactory.create(
                product=cls.chapter_product,
                **dict(zip(product_price_headers, row))
            )

        cls.division_product = product_factory.DivisionProductFactory()
        division_prices = [
            ('K', None, Decimal('0.00'), None),
            ('KK', None, Decimal('0.00'), None),
            ('L', None, Decimal('10.00'), None),
            (None, None, Decimal('40.00'), 'Non-member Rate'),
            (None, None, Decimal('25.00'), 'APA Member Rate')
        ]
        for row in division_prices:
            ProductPriceFactory.create(
                product=cls.division_product,
                **dict(zip(product_price_headers, row))
            )

        cls.aicp_product = product_factory.AICPMembershipProductFactory()
        aicp_prices = [
            ('A', 'AICP', Decimal('100.00'), 'Salary Range A'),
            ('AA', 'AICP', Decimal('110.00'), 'Outside US Regular Member AA'),
            ('B', 'AICP', Decimal('100.00'), 'Salary Range B'),
            ('BB', 'AICP', Decimal('110.00'), 'Outside US Regular Member BB'),
            ('C', 'AICP', Decimal('115.00'), 'Salary Range C'),
            ('CC', 'AICP', Decimal('110.00'), 'Outside US Regular Member CC'),
            ('D', 'AICP', Decimal('125.00'), 'Salary Range D'),
            ('E', 'AICP', Decimal('135.00'), 'Salary Range E'),
            ('F', 'AICP', Decimal('145.00'), 'Salary Range F'),
            ('G', 'AICP', Decimal('155.00'), 'Salary Range G'),
            ('H', 'AICP', Decimal('165.00'), 'Salary Range H'),
            ('I', 'AICP', Decimal('175.00'), 'Salary Range I'),
            ('J', 'AICP', Decimal('190.00'), 'Salary Range J'),
            ('K', 'AICP', Decimal('0.00'), 'Student (Salary Code K)'),
            ('KK', 'AICP', Decimal('0.00'), 'Outside US Student Member (Salary Code KK)'),
            ('L', 'AICP', Decimal('70.00'), 'NP (Salary Code L)'),
            ('LL', 'AICP', Decimal('25.00'), 'Outside US NP Member (LL)'),
            ('N', 'AICP', Decimal('25.00'), 'US Retired Member (Salary Code N)'),
            ('NN', 'AICP', Decimal('25.00'), 'Outside US Retired Member (NN)'),
            ('O', 'AICP', Decimal('15.00'), 'US Life Member (Salary Code O)'),
            ('OO', 'AICP', Decimal('15.00'), 'Outside US Life Member (OO)'),
            ('P', 'AICP', Decimal('185.00'), 'Salary P'),
            ('Q', 'AICP', Decimal('90.00'), 'Salary Q')
        ]
        for row in aicp_prices:
            ProductPriceFactory.create(
                product=cls.aicp_product,
                **dict(zip(product_price_headers, row))
            )

    def setUp(self) -> None:
        self.contact = ContactFactoryIndividual()

    def tearDown(self) -> None:
        Contact.objects.filter().delete()

    def test_remove_non_membership_products(self):
        self.set_contact_salary_range('D')

        self.membership_product.add_to_cart(self.contact)
        self.assertEqual(Purchase.cart_items(self.contact.user).count(), 1)

        biller = BluepayMembershipPaymentDispatcher(self.contact)
        biller._remove_non_membership_products_from_cart()
        self.assertEqual(Purchase.cart_items(self.contact.user).count(), 1)

        japa = product_factory.ProductCartFactory.create(code="SUB_JOUR")
        ProductPriceFactory.create(product=japa, price=Decimal('48.00'), title="Member Price")
        japa.add_to_cart(self.contact)

        self.assertEqual(Purchase.cart_items(self.contact.user).count(), 2)
        biller._remove_non_membership_products_from_cart()
        self.assertEqual(biller.cart_items.count(), 1)

    def test_get_bill_amount(self):
        self.set_contact_salary_range('D')
        self.membership_product.add_to_cart(self.contact)

        biller = BluepayMembershipPaymentDispatcher(self.contact)
        self.assertEqual(
            biller.get_initial_bill_amount(
                store_settings.AutodraftBillFrequency.MONTHLY,
                store_settings.AutodraftBillPeriod.ANNUAL
            ),
            Decimal("21.42")
        )

    def set_contact_salary_range(self, salary_range):
        self.contact.salary_range = salary_range
        self.contact.save()
