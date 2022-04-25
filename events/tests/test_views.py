from planning.global_test_case import GlobalTestCase
from myapa.functional_tests import utils as test_utils
from django.test import Client
from imis.tests.factories.relationship import RelationshipFactory
from imis.enums.relationship_types import ImisRelationshipTypes as RelTypes
from cm.models.providers import ProviderApplication


class AuthenticateProviderMixinTest(GlobalTestCase):

    def setUp(self):
        # An administrator for an organization has records correctly set up
        # in the iMIS Name and Relationship tables by the Membership department
        self.org_imis, self.org_imis_admin = test_utils.build_imis_org_and_admin()
        self.org_imis.save()
        self.org_imis_admin.save()

        self.rel_imis = RelationshipFactory(
            id=self.org_imis_admin.id,
            relation_type=RelTypes.ADMIN_I.value,
            target_id=self.org_imis.id,
            target_relation_type=RelTypes.ADMIN_C.value,
        )
        self.rel_imis.save()

        self.client = Client()

    def tearDown(self):
        self.client.logout()

    def test_existing_is_validated_provider(self):
        pass

    def test_new_is_validated_provider(self):
        pass
