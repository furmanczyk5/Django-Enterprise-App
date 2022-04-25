from free_students.models import Accreditation, SCHOOL_ACCREDITATION_TYPES
from imis.enums.relationship_types import ImisRelationshipTypes
from imis.enums.organizations import SchoolAccreditationTypes
from imis.enums.members import ImisMemberTypes
from imis.tests.factories.demographics import OrgDemographicsFactory
from imis.tests.factories.name import ImisNameFactoryAmerica
from imis.tests.factories.name_address import ImisNameAddressFactoryAmerica
from imis.tests.factories.relationship import RelationshipFactory
from myapa.models.constants import DjangoContactTypes
from myapa.models.contact import Contact
from myapa.models.contact_relationship import ContactRelationship
from myapa.models.proxies import Organization
from myapa.tests.factories.contact import ContactFactoryOrganization
from planning.global_test_case import GlobalTestCase


class SchoolTestCase(GlobalTestCase):

    @classmethod
    def setUpTestData(cls):

        super(SchoolTestCase, cls).setUpTestData()

        accreditations = [
            Accreditation(accreditation_type=x[0]) for x in SCHOOL_ACCREDITATION_TYPES
        ]
        Accreditation.objects.bulk_create(accreditations)

    def test_get_imis_org_demographics(self):
        contact = ContactFactoryOrganization()
        orgdemo = OrgDemographicsFactory(
            id=contact.user.username
        )
        orgdemo.save()

        self.assertTrue(contact.get_imis_org_demographics().exists())

    def test_update_or_create_relationships_from_imis(self):

        orgimis = ImisNameFactoryAmerica(
            company_record=True
        )
        orgimis.save()
        orgdjango = Contact.update_or_create_from_imis(orgimis.id)

        self.assertEqual(orgdjango.contact_type, DjangoContactTypes.ORGANIZATION.value)
        self.assertIsInstance(orgdjango, Organization)
        self.assertEqual(orgdjango.company, orgimis.company)

        adminimis = ImisNameFactoryAmerica(
            co_id=orgdjango.user.username
        )
        adminimis.save()

        reladmin = RelationshipFactory(
            id=adminimis.id,
            target_id=orgdjango.user.username,
            relation_type=ImisRelationshipTypes.ADMIN_I.value
        )
        reladmin.save()

        orgdjango.update_or_create_relationships_from_imis()
        admindjango = Contact.objects.get(user__username=adminimis.id)
        self.assertTrue(orgdjango.related_contact_sources.exists())
        self.assertEqual(orgdjango.related_contact_sources.first(), admindjango)

        nonself_related_contact = orgdjango.related_contact_sources.first()
        self.assertEqual(nonself_related_contact.user.username, adminimis.id)

        # Same result as above
        self.assertEqual(
            ContactRelationship.objects.filter(source=admindjango).first().target.user.username,
            orgdjango.user.username
        )

        # TODO: Can one admin only have one company_fk? Couldn't this be a many-to-many?
        self.assertEqual(admindjango.company_fk, orgdjango)

        # add another relationship
        adminimis2 = ImisNameFactoryAmerica(
            co_id=orgdjango.user.username
        )
        adminimis2.save()
        relbilling = RelationshipFactory(
            id=adminimis2.id,
            target_id=orgdjango.user.username,
            relation_type=ImisRelationshipTypes.BILLING_I.value
        )
        relbilling.save()
        orgdjango.update_or_create_relationships_from_imis()
        self.assertEqual(orgdjango.related_contact_sources.count(), 2)

        # add a relationship with a relation_type that we exclude
        excluded_rel_type = ImisNameFactoryAmerica(
            co_id=orgdjango.user.username
        )
        excluded_rel_type.save()

        relcm = RelationshipFactory(
            id=excluded_rel_type.id,
            target_id=orgdjango.user.username,
            relation_type=ImisRelationshipTypes.CM_I.value
        )
        relcm.save()

        orgdjango.update_or_create_relationships_from_imis()
        self.assertEqual(orgdjango.related_contact_sources.count(), 2)

        # Remove an existing Relationship in iMIS and
        # test if Django ContactRelationship is removed as well
        relbilling.relation_type = 'ZONING_I'
        relbilling.save()

        orgdjango.update_or_create_relationships_from_imis()
        self.assertEqual(orgdjango.related_contact_sources.count(), 1)

    def test_get_program_types(self):
        contact = ContactFactoryOrganization(
            member_type=ImisMemberTypes.SCH.value
        )
        orgdemo = OrgDemographicsFactory(
            id=contact.user.username,
            school_program_type=SchoolAccreditationTypes.A001.value
        )
        orgdemo.save()

        self.assertEqual(SchoolAccreditationTypes.A001.value, contact.get_program_type())

        orgdemo.school_program_type = SchoolAccreditationTypes.N002.value
        orgdemo.save()

        self.assertEqual(SchoolAccreditationTypes.N002.value, contact.get_program_type())

    def test_sync_from_imis(self):

        school = ContactFactoryOrganization(
            member_type=ImisMemberTypes.SCH.value
        )

        orgdemo = OrgDemographicsFactory(
            id=school.user.username,
            school_program_type=SchoolAccreditationTypes.A001.value
        )
        orgdemo.save()

        name = ImisNameFactoryAmerica(
            id=school.user.username,
            company_record=True
        )
        name.save()

        name_address = ImisNameAddressFactoryAmerica(
            id=school.user.username,
            preferred_mail=True,
            purpose="Work Address"
        )
        name_address.save()

        school.sync_from_imis()

        # test super() sync_from_imis
        self.assertEqual(school.company, name.company)
        self.assertEqual(school.address1, name_address.address_1)

        self.assertIsNotNone(school.accredited_school)

        self.assertIn(
            Accreditation.objects.get(accreditation_type=SchoolAccreditationTypes.A001.value),
            school.accredited_school.accreditation.all()
        )

        self.assertNotIn(
            Accreditation.objects.get(accreditation_type=SchoolAccreditationTypes.N002.value),
            school.accredited_school.accreditation.all()
        )

        orgdemo.school_program_type = '{},{}'.format(
            SchoolAccreditationTypes.A001.value,
            SchoolAccreditationTypes.A002.value
        )
        orgdemo.save()

        school.sync_from_imis()

        self.assertEqual(school.accredited_school.accreditation.count(), 2)
