import factory

from imis.models import Relationship


class RelationshipFactory(factory.Factory):
    seqn = factory.Sequence(lambda n: str(n + 1000000))
    updated_by = 'DJANGO_TEST_FACTORY'
    relation_type = ''

    class Meta:
        model = Relationship


class RelationshipFactoryBlank(factory.Factory):

    title = ''
    functional_title = ''
    status = ''
    last_string = ''
    updated_by = ''
    group_code = ''

    class Meta:
        model = Relationship
