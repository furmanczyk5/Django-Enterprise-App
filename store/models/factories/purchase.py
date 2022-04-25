import factory

from myapa.tests.factories import contact as contact_factory
from store.models.purchase import Purchase
from store.models.factories.product import CMProviderRegistrationProductFactory


class PurchaseFactory(factory.DjangoModelFactory):

    contact = factory.SubFactory(contact_factory.ContactFactory)
    gl_account = ''
    amount = 0
    submitted_product_price_amount = 0

    class Meta:
        model = Purchase

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        instance.user = instance.contact.user


class CMProviderRegistrationPurchaseFactory(PurchaseFactory):
    product = factory.SubFactory(CMProviderRegistrationProductFactory)
