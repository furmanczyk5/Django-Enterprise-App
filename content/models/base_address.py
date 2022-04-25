import json
import logging

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from api.clients.voter_voice import VoterVoiceClient
from content.utils import validate_lon_lat
from imis.models import CustomAddressGeocode
from imis.utils.addresses import get_primary_address

logger = logging.getLogger(__name__)


class BaseAddress(models.Model):
    user_address_num = models.IntegerField(blank=True, null=True)
    address1 = models.CharField(max_length=40, blank=True, null=True)
    address2 = models.CharField(max_length=40, blank=True, null=True)
    city = models.CharField(max_length=40, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    voter_voice_checksum = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="The checksum that is returned by a VoterVoice-validated address"
    )
    zip_code_extension = models.CharField(
        max_length=4,
        null=True,
        blank=True,
        help_text="The four-digit ZIP code extension"
    )

    # TODO: These should be on a separate model so that we can store
    #  multiple geocoding results from different services for the same
    #  address to compare/rank quality of results. We will need to figure
    #  out how to best associate them with this abstract base class though...
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # importing here to avoid circular import
        from myapa.tasks import vv_validate_address, vv_validate_address_imis
        from myapa.utils import dict_diff
        self.django_task = vv_validate_address
        self.imis_task = vv_validate_address_imis
        self.dict_diff = dict_diff

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        """Check that longitude and latitude values are valid, if present"""

        changed = False
        # update geocoding and district info from VoterVoice if the address changed
        if self.dict_diff(getattr(self, '_old_address', {}), self.get_address_dict(self.__dict__)):
            changed = True

        super().save(force_insert=force_insert, force_update=force_update, using=using,
                            update_fields=update_fields)
        if changed and not isinstance(self, apps.get_model('jobs', 'Job')):
            # self.django_task.delay(self)
            self.imis_task.delay(self)

    def get_voter_voice_address_query(self):
        """
        Get the fields necessary for validating an address with the VoterVoice API
        :return: dict
        """
        # importing here to avoid circular import
        from myapa.models.constants import UNITED_STATES

        # TODO: Do we need to worry about international addresses for this?
        if self.country == UNITED_STATES:
            return dict(
                address1=self.address1,
                address2=self.address2,
                city=self.city,
                state=self.state,
                zipcode=self.zip_code,
                country='US'
            )
        else:
            return dict()

    def get_voter_voice_validated_address_query(self):
        """
        After validating an address with `.get_voter_voice_address_query`, subsequent
        requests to VoterVoice require a checksum and sometimes our assocation name.
        As to why the field is "zipcode" in the validate call and "zipCode" here, well,
        you'll have to ask VoterVoice about that.
        :return: dict
        """
        if self.voter_voice_checksum:
            address_fields = dict(
                streetAddress=self.address1,
                city=self.city,
                state=self.state,
                zipCode=self.zip_code,
                zipCodeExtension=self.zip_code_extension,
                checksum=self.voter_voice_checksum,
                country='US'
            )
            address_fields = {k: v for (k, v) in address_fields.items() if v}
            params = dict(
                address=json.dumps(address_fields),
                association=getattr(settings, 'VOTER_VOICE_ASSOCIATION_NAME', 'PLANNING')
            )
            return params

    def validate_address(self):
        """
        Validate this address with VoterVoice
        https://votervoice.docs.apiary.io/#reference/addresses/addresses/validate-an-address
        """
        client = VoterVoiceClient()
        address_params = self.get_voter_voice_address_query()
        if not all((isinstance(x[1], str) and x[1].strip()) for x in address_params.items()
                   if x[0] in client.REQUIRED_ADDRESS_FIELDS):
            logger.warning(
                "{} is missing one or more required address fields to validate with VoterVoice".format(
                    self
                )
            )
            return
        resp = client.validate_address(address_params)
        if not resp:
            return
        if len(resp) > 1:
            logger.warning(
                "Multiple addresses returned by VoterVoice for {}; only using the first".format(self)
            )
        if isinstance(self, apps.get_model('myapa', 'IndividualContact')):
            self._handle_individual_contact_address(resp[0])

    @staticmethod
    def _get_vv_geo_data(resp):
        coordinates = resp.get('coordinates', {})
        data = dict(
            longitude=coordinates.get('longitude'),
            latitude=coordinates.get('latitude'),
            weak_coordinates=coordinates.get('isWeakCoordinates', False),
            voter_voice_checksum=resp.get('checksum'),
            zip_code_extension=resp.get('zipCodeExtension')
        )
        return data

    def _handle_individual_contact_address(self, resp):
        """
        Create/update fields with the results of validating an address for
        an IndividualContact
        :param resp: dict
        :return:
        """
        data = self._get_vv_geo_data(resp)
        self.voter_voice_checksum = data['voter_voice_checksum']
        self.zip_code_extension = data['zip_code_extension']
        try:
            # Don't run the diff check in our overridden save() method
            # will result in race condition
            self.longitude, self.latitude = validate_lon_lat(data['longitude'], data['latitude'])
            super().save()
        except ValidationError as e:
            logger.error(e.__str__())

    def _write_geocode_to_imis(self, resp):
        user = getattr(self, 'user', None)
        if not getattr(user, 'username', None):
            logger.warning('No iMIS ID associated with {}'.format(self))
            return
        address = get_primary_address(user.username)
        if address is None:
            logger.warning('No NameAddress record found for {}'.format(self))
            return
        data = self._get_vv_geo_data(resp)
        try:
            longitude, latitude = validate_lon_lat(data['longitude'], data['latitude'])
        except ValidationError as e:
            logger.error(e.__str__())
            return
        geocode, created = CustomAddressGeocode.objects.get_or_create(
            id=user.username,
            address_num=address.address_num
        )
        geocode.votervoice_checksum = data['voter_voice_checksum']
        geocode.longitude = longitude
        geocode.latitude = latitude
        geocode.weak_coordinates = data['weak_coordinates']
        return geocode

    @classmethod
    def get_address_dict(cls, address_dict=None):
        if address_dict is None:
            address_dict = cls.__dict__
        return {k: v for (k, v) in address_dict.items()
                if k in ('address1', 'address2', 'city', 'state', 'zip_code', 'country')}

    def get_full_street_address(self):
        fields = self.get_address_dict(self.__dict__)
        return "{address1}, {city}, {state} {zip_code} {country}".format(**fields)

    @classmethod
    def from_db(cls, db, field_names, values):
        if len(values) != len(cls._meta.concrete_fields):
            values = list(values)
            values.reverse()
            values = [
                values.pop() if f.attname in field_names else models.DEFERRED
                for f in cls._meta.concrete_fields
            ]
        instance = cls(*values)
        instance._state.adding = False
        instance._state.db = db
        # customization to store the original field values on the instance
        # https://docs.djangoproject.com/en/1.11/ref/models/instances/#customizing-model-loading
        instance._loaded_values = dict(zip(field_names, values))
        instance._old_address = cls.get_address_dict(instance._loaded_values)

        return instance
