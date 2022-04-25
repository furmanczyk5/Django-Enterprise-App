from decimal import Decimal

from django.contrib.auth.models import Group

from myapa.tests.factories.contact import ContactFactoryIndividual
from planning.global_test_case import GlobalTestCase
from store.models.product_cart import ProductCart


class ProductCartMembershipTestCase(GlobalTestCase):

    fixtures = [
        "contenttypes.json",
        "permissions.json",
       # "groups.json",
        "sites.json",
        "administrator.json",
        'product_groups.json',
        'chapter_content.json',
        'division_content.json',
        'membership_content.json',
        "chapter_products.json",
        "chapter_product_prices.json",
        "division_products.json",
        "division_product_prices.json",
        "membership_products.json",
        "membership_product_prices.json"
    ]

    def test_get_prices_returns_code_that_matches_salary_range_and_country_for_membership(self):
        contact = ContactFactoryIndividual(salary_range='L', country="United States")
        membership_mem = ProductCart.objects.get(code="MEMBERSHIP_MEM")
        price = membership_mem.get_price(contact=contact)
        self.assertEqual(price.code, 'L')
        self.assertEqual(price.price, Decimal('79.00'))

        contact.country = "Canada"
        contact.save()
        price = membership_mem.get_price(contact=contact)
        self.assertNotEqual(price.code, 'L')

        contact.country = 'United States'
        contact.salary_range = 'F'
        contact.save()
        price = membership_mem.get_price(contact=contact)
        self.assertEqual(price.code, 'F')
        self.assertEqual(price.price, Decimal('310.00'))

    def test_new_member_gets_correct_division_price(self):
        contact = ContactFactoryIndividual(salary_range='L', country='United States')
        div_city_plan = ProductCart.objects.get(code='DIVISION_CITY_PLAN')
        price = div_city_plan.get_price(contact=contact)
        # no new-member Group and no active APA Membership purchase, should not apply
        self.assertIsNone(price)

        contact.user.groups.add(Group.objects.get(name='new-member'))
        price = div_city_plan.get_price(contact=contact)
        self.assertEqual(price.code, 'L')
        self.assertEqual(price.price, Decimal('10.00'))

