import factory
from django.utils import timezone

from myapa.tests.factories import contact as contact_factory
from store.models.order import Order


class OrderFactory(factory.DjangoModelFactory):

    user = factory.SubFactory(contact_factory.UserFactory)
    submitted_time = timezone.now()

    class Meta:
        model = Order

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        instance.submitted_user_id = instance.user.username
