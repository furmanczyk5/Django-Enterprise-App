import json
import logging

from django.conf import settings

from .base import ExternalService

logger = logging.getLogger(__name__)


def log_unexpected_response(request):
    logger.error('Unexpected response from VoterVoice: {}'.format(
        getattr(request, 'text', '')[:1000])
    )


# String values from VoterVoice
STATE_HOUSE = ('State Assembly', 'State House')
STATE_SENATE = 'State Senate'
US_HOUSE = 'US House'


class VoterVoiceClient(ExternalService):

    REQUIRED_ADDRESS_FIELDS = ['address1', 'city', 'state', 'zipcode']

    def __init__(self, timeout=2):
        self.api_key = getattr(settings, "VOTER_VOICE_API_KEY", None)
        self.association_name = getattr(settings, "VOTER_VOICE_ASSOCIATION_NAME", None)
        assert self.api_key, "VOTER_VOICE_API_KEY not set in local settings"
        assert self.association_name, "VOTER_VOICE_ASSOCIATION_NAME not set in local settings"
        super().__init__(timeout=timeout)
        self.base_url = 'https://www.votervoice.net/api'
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json; charset=utf-8"
        }

    def validate_address(self, address_params):
        """
        Validate an address. This returns the ``checksum`` that is then used in all
        subsequent VV requests.
        https://votervoice.docs.apiary.io/#reference/addresses/addresses/validate-an-address
        :param address_params: dict
        :return: dict
        """
        req = self.make_request(url=self.base_url + '/addresses', params=address_params, headers=self.headers)
        if req is not None:
            try:
                return req.json()['addresses']
            except (json.JSONDecodeError, KeyError):
                log_unexpected_response(req)

    def get_districts_by_address(self, params):
        """
        Get all districts matched for the given address params.
        https://votervoice.docs.apiary.io/#reference/districts/get-districts-for-an-address
        :param params: dict
        :return: list
        """
        req = self.make_request(url=self.base_url + '/districts', params=params, headers=self.headers)
        if req is not None:
            try:
                return req.json()
            except json.JSONDecodeError:
                log_unexpected_response(req)
