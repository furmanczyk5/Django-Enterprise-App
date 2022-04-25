import factory
from django.utils import timezone

from comments.models import Comment
from content.tests.factories.content import ContentFactory
from myapa.tests.factories.contact import ContactFactoryOrganization, ContactFactoryIndividual


class CommentFactory(factory.DjangoModelFactory):
    contact = factory.SubFactory(ContactFactoryOrganization)
    content = factory.SubFactory(ContentFactory)
    submitted_time = timezone.now()

    class Meta:
        model = Comment
