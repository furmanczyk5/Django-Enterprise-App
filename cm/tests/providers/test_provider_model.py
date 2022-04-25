from copy import copy

from django.db.models import Count
from factory import fuzzy

from cm.models.providers import Provider
from comments.factories import CommentFactory
from content.tests.factories.content import ContentFactory
from myapa.models.constants import ContactRoleTypes
from myapa.tests.factories.contact import ContactFactoryOrganization
from myapa.tests.factories.contact_role import ContactRoleFactory, ContactRole
from planning.global_test_case import GlobalTestCase


class ProviderModelTest(GlobalTestCase):

    @classmethod
    def setUpTestData(cls):
        super(ProviderModelTest, cls).setUpTestData()
        cls.org = ContactFactoryOrganization()
        cls.provider = copy(cls.org)
        cls.provider.__class__ = Provider
        cls.content = ContentFactory()
        cls.contact_role = ContactRoleFactory(
            contact=cls.provider,
            content=cls.content,
            role_type=ContactRoleTypes.PROVIDER.value,
        )
        cls.comments = CommentFactory.create_batch(
            size=100,
            content=cls.content,
            contact=cls.provider,
            rating=fuzzy.FuzzyInteger(1, 5)
        )

    def test_get_rating_stats(self):
        stats = self.provider.get_rating_stats()
        self.assertEqual(stats['rating_count'], 100)
        self.assertGreater(stats['rating_avg'], 1)
        self.assertLess(stats['rating_avg'], 5)

    def test_content_rating_count(self):
        rating_count = self.content.comments.aggregate(rating_count=Count('rating'))
        self.assertEqual(rating_count['rating_count'], 100)
        self.assertEqual(self.content.rating_count, 100)

    def test_get_provider_content_through_contact_role(self):
        crs = ContactRole.objects.filter(contact=self.provider)
        self.assertEqual(
            crs.count(),
            1
        )

        self.assertEqual(
            self.provider.comments.count(),
            100
        )

        self.assertEqual(
            self.provider.comments.filter(content__isnull=False).count(),
            100
        )

    # def test_recalculate_rating_updates_rating_count_and_average(self):
    #     rating_stats =
        # [x.content.recalculate_rating() for x in self.provider.comments.all()]


        # rating_stats = self.provider.get_rating_stats()
        # self.assertEqual(
        #     rating_stats['rating_count'],
        #     100
        # )
