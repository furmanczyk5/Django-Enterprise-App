from decimal import Decimal

from django.test import RequestFactory

from content.models.settings import ContentStatus, PublishStatus
from imis.enums.relationship_types import ImisRelationshipTypes
from imis.tests.factories.relationship import RelationshipFactory
from myapa.functional_tests.utils import build_imis_org_and_admin
from myapa.models.contact import Contact
from planning.global_test_case import GlobalTestCase
from store.models.factories.product import (
    ProductFactory, CMProviderRegistrationProductFactory, CMPerCreditProductFactory
)
from store.models.factories.purchase import PurchaseFactory
from store.models.product_option import ProductOption
from store.models.product_price import ProductPrice
from store.models.purchase import Purchase

REGISTRATION_PRODUCT_OPTION_CODES_PRICES = [
    ("CM_PER_CREDIT", Decimal('224.00')),
    ("CM_UNLIMITED_SMALL", Decimal('1254.00')),
    ("CM_UNLIMITED_MEDIUM", Decimal('2461.00')),
    ("CM_UNLIMITED_LARGE", Decimal('3611.00')),
    ("CM_UNLIMITED_LARGEST", Decimal('6084.00'))
]


class CMProviderEcommerceTest(GlobalTestCase):

    @classmethod
    def setUpTestData(cls):
        super(CMProviderEcommerceTest, cls).setUpTestData()

        # assuming org, org_admin, and relationship record have already been created
        cls.org, cls.org_admin = build_imis_org_and_admin()
        cls.org.save()
        cls.org_admin.save()
        cls.rel_imis = RelationshipFactory(
            id=cls.org_admin.id,
            relation_type=ImisRelationshipTypes.CM_I.value,
            target_id=cls.org.id,
            target_relation_type=ImisRelationshipTypes.CM_C.value,
        )
        cls.rel_imis.save()

        cls.cm_provider_reg_product = CMProviderRegistrationProductFactory()
        for x in REGISTRATION_PRODUCT_OPTION_CODES_PRICES:
            ProductOption.objects.create(
                code=x[0],
                product=cls.cm_provider_reg_product,
                status=ContentStatus.ACTIVE.value,
                publish_status=PublishStatus.PUBLISHED.value
            )
            ProductPrice.objects.create(
                option_code=x[0],
                product=cls.cm_provider_reg_product,
                price=x[1],
                status=ContentStatus.ACTIVE.value,
                publish_status=PublishStatus.PUBLISHED.value
            )

        # Per-credit fee for the actual event
        # The per-credit product options/prices above are for
        # Provider registration.
        cls.cm_per_credit_product = CMPerCreditProductFactory()
        cls.cm_per_credit_product_option = ProductOption.objects.create(
            product=cls.cm_per_credit_product,
            code="PRODUCT_CM_PER_CREDIT_DEFAULT",
            title="Cm Per Credit Option",
            status=ContentStatus.ACTIVE.value,
            publish_status=PublishStatus.PUBLISHED.value
        )
        cls.cm_per_credit_product_price = ProductPrice.objects.create(
            product=cls.cm_per_credit_product,
            option_code=cls.cm_per_credit_product_option.code,
            status=ContentStatus.ACTIVE.value,
            publish_status=PublishStatus.PUBLISHED.value,
            price=Decimal('115.00')
        )

    def setUp(self):
        self.factory = RequestFactory()
        self.org_django = Contact.update_or_create_from_imis(self.org.id)
        self.org_admin = self.org_django.get_admin_contacts().first()

    def test_buy_cm_registration(self):
        self._create_reg_purchase("CM_UNLIMITED_SMALL")
        self.assertEqual(self.org_admin.user.purchase_set.count(), 1)

        # The Org's Django user or contact shouldn't have purchases
        # instead, we should be looking at Purchases where the
        # contact_recipient is the org
        self.assertFalse(self.org_django.user.purchase_set.exists())
        self.assertFalse(self.org_django.purchase_set.exists())
        self.assertEqual(Purchase.objects.filter(contact_recipient=self.org_django).count(), 1)

    def _create_reg_purchase(self, option_code):
        price = ProductPrice.objects.get(option_code=option_code)
        reg_purchase = PurchaseFactory(
            product=self.cm_provider_reg_product,
            product_price=price,
            option=ProductOption.objects.get(code=option_code),
            contact=self.org_admin,
            user=self.org_admin.user,
            amount=price.price,
            submitted_product_price_amount=price.price
        )
        return reg_purchase

    def test_cm_reg_purchase_sets_contact_recipient(self):
        # TODO: Are there restrictions on who is allowed to purchase CM_REGISTRATION or CM_PER_CREDIT?

        reg_purchase = self._create_reg_purchase("CM_UNLIMITED_SMALL")

        self.assertEqual(reg_purchase.contact_recipient, self.org_django)

        # test converse - non CM product should have contact_recipient the same
        # as the contact who is purchasing
        prod = ProductFactory(code="19CONF")
        price = ProductPrice.objects.create(price=Decimal('100.00'), product=prod)
        purch = PurchaseFactory(
            product=prod,
            product_price=price,
            contact=self.org_admin,
            user=self.org_admin.user,
            amount=price.price,
            submitted_product_price_amount=price.price
        )
        purch.save()
        self.assertNotEqual(purch.contact_recipient, self.org_django)

    def test_per_credit_purchase(self):
        reg_purchase = self._create_reg_purchase("CM_PER_CREDIT")

