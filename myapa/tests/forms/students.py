
from myapa.forms.join import StudentJoinEnhanceMembershipForm
from myapa.tests.factories.contact import ContactFactoryIndividual
from myapa.tests.factories.educational_degree import EducationalDegreeFactory
from planning.global_test_case import GlobalTestCase
from store.models import Purchase
from store.models.product_cart import ProductCart


class StudentJoinEnhanceMembershipFormTestCase(GlobalTestCase):

    fixtures = [
        "administrator.json",
        "product_groups.json",
        "division_content.json",
        "division_products.json",
        "division_product_prices.json"
    ]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.student = ContactFactoryIndividual(
            member_type="NOM",
            salary_range='K',
            country='United States'
        )
        cls.educational_degree = EducationalDegreeFactory(contact=cls.student)

    def test_sjem_form_only_displays_division_products(self):
        form = StudentJoinEnhanceMembershipForm()
        form.init_optional_product_fields()
        self.assertTrue(all(x.product_type == 'DIVISION') for x in form.available_products)

    def test_existing_division_in_cart_does_not_populates_divisions_multiplechoicefield(self):
        div_city_plan = ProductCart.objects.get(code='DIVISION_CITY_PLAN')
        div_city_plan.add_to_cart(contact=self.student)

        # mimicking JoinEnhanceMembershipView.get_form_kwargs
        form = StudentJoinEnhanceMembershipForm(
            contact=self.student,
            cart_products=[p.product for p in Purchase.cart_items(user=self.student.user)]
        )

        form.init_optional_product_fields()

        self.assertNotIn(div_city_plan.id, form.fields['divisions'].initial)
