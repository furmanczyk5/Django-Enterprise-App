from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from content.models import Content
from content.utils.utils import validate_lon_lat
from myapa.models.constants import UNITED_STATES
from myapa.tests.factories.contact import ContactFactoryIndividual
from planning.global_test_case import GlobalTestCase


class ContentTestCase(GlobalTestCase):

    @classmethod
    def setUpClass(cls):
        super(ContentTestCase, cls).setUpClass()
        cls.test_user, user_created = User.objects.get_or_create(username="000007", password="norman_pass")

    def setUp(self):
        con = Content.objects.create(title='test_content_truthiness')
        con.created_by = self.test_user
        con.save()

    def test_is_content(self):
        con = Content.objects.get(title='test_content_truthiness')
        self.assertEqual(con.is_content, True)

    def test_get_voter_voice_address_query(self):
        contact_us = ContactFactoryIndividual(country=UNITED_STATES)
        vv_query = contact_us.get_voter_voice_address_query()
        self.assertDictEqual(
            vv_query,
            dict(
                address1=contact_us.address1,
                address2=contact_us.address2,
                city=contact_us.city,
                state=contact_us.state,
                zipcode=contact_us.zip_code,
                country='US'
            )
        )

        contact_canada = ContactFactoryIndividual(country='Canada')
        self.assertDictEqual(
            contact_canada.get_voter_voice_address_query(),
            dict()
        )

    def test_lon_lat_validation(self):
        contact = ContactFactoryIndividual()

        contact.longitude = -87.7
        contact.latitude = 41.9
        contact.save()  # implicit assert

        contact.longitude = 'foo'
        with self.assertRaises(ValidationError):
            validate_lon_lat(contact.longitude, contact.latitude)

        contact.latitude = 150
        contact.longitude = -87
        with self.assertRaises(ValidationError):
            validate_lon_lat(contact.longitude, contact.latitude)

        contact.latitude = 50
        contact.longitude = -200
        with self.assertRaises(ValidationError):
            validate_lon_lat(contact.longitude, contact.latitude)

