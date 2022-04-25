import factory

from store.models.product_price import ProductPrice
from store.models.factories import product as product_factories
from content.models.settings import PublishStatus, ContentStatus


class ProductPriceFactory(factory.DjangoModelFactory):
    status = ContentStatus.ACTIVE.value
    publish_status = PublishStatus.PUBLISHED.value

    class Meta:
        model = ProductPrice


class CMProviderRegistrationProductPriceFactory(ProductPriceFactory):
    product = factory.SubFactory(product_factories.CMProviderRegistrationProductFactory)

