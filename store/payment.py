import json
import uuid

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from requests import Request, Session
from sentry_sdk import capture_message


try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse


class PaymentException(Exception):
    pass


class PaymentClass(object):
    """
    Example Usage:

    vendor = "APAStreamingProducts"
    user = "apaconference"  # vendor
    password = "****"

    pc = PaymentClass(vendor=vendor, user=user, password=password)
    secure_token_id, secure_token = pc.get_secure_token(amount=1)

    trxtype = A : partial authorization
    trxtype = S: sales transaction - immediate

    """
    def __init__(self, **kwargs):
        self.test_mode = kwargs.get('test_mode', True)
        self.currency = kwargs.get('currency', 'USD')
        self.partner = kwargs.get('partner', "PayPal")
        self.username = kwargs.get("username")
        self.vendor = kwargs.get('vendor')
        self.user = kwargs.get('user')
        self.password = kwargs.get('password')
        self.url = kwargs.get('url')
        self.comment1 = kwargs.get("comment1")
        self.comment2 = kwargs.get("comment2")

        self.user2 = kwargs.get("user2", "")

        print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
        print(self.username)

        self.pn_ref = kwargs.get("pn_ref", "")
        if not self.url:
            if self.test_mode:
                self.url = "https://pilot-payflowpro.paypal.com/"
            else:
                self.url = "https://payflowpro.paypal.com/"

    def get_response_value(self, response_dict, key, index=0):
        try:
            value = response_dict[key][index]
        except KeyError as exc:
            msg = "Unable to get the {} from the response".format(key)
            raise PaymentException(msg)
        except TypeError as exc:
            msg = "The {} is not in the correct format".format(key)
            raise PaymentException(msg)
        except IndexError as exc:
            msg = "The {} is not formatted correctly".format(key)
            raise PaymentException(msg)
        return value

    def generate_secure_token_id(self):
        uid = uuid.uuid4()
        token = uid.hex
        return token

    def _prepare_secure_token_request(self, amount, trxtype="A"):
        url = self.url
        secure_token_id = self.generate_secure_token_id()
        payload = dict(
            PARTNER=self.partner,
            VENDOR=self.vendor,
            USER=self.user,
            PWD=self.password,
            TRXTYPE=trxtype,
            CUSTCODE=self.username,
            AMT=amount,
            CURRENCY=self.currency,
            CREATESECURETOKEN="Y",
            SECURETOKENID=secure_token_id,
            COMMENT1=self.comment1,
            COMMENT2=self.comment2,
            ORIGID=self.pn_ref,
            USER2=self.user2,

            # For debugging
            VERBOSITY='HIGH'

        )
        if getattr(settings, 'PAYPAL_DEBUG', False):
            debug_dict = payload.copy()
            del debug_dict['PWD']
            del debug_dict["SECURETOKENID"]
            capture_message('PAYPAL DEBUG: Sending payload:\n{}'.format(
                json.dumps(debug_dict, cls=DjangoJSONEncoder, indent=2)
            ), level='debug')

        session = Session()
        req = Request('POST', url, data=payload)
        prepped = req.prepare()
        self._prepped = prepped
        return prepped, session, secure_token_id

    def get_secure_token(self, amount, trxtype="A"):

        prepped, session, secure_token_id = self._prepare_secure_token_request(
            amount, trxtype)

        resp = session.send(prepped,)
        self._resp = resp
        if resp.status_code >= 300:
            capture_message(resp.text, level='error')
            raise PaymentException(
                "Unable to connect to processor - http code {}".format(
                    resp.status_code))

        response_dict = urlparse.parse_qs(resp.text)

        result_code = self.get_response_value(response_dict, "RESULT")
        try:
            result_code = int(result_code)
        except (TypeError, ValueError):
            msg = "The result code '{}' must be a number".format(result_code)
            raise PaymentException(msg)
        if result_code != 0:
            msg = "Unsuccessful reponse '{}' from payment gateway. RESPMSG: {}".format(result_code, response_dict.get("RESPMSG"))
            capture_message(msg, level='error')
            raise PaymentException(msg)

        secure_token = self.get_response_value(response_dict, "SECURETOKEN")
        return secure_token_id, secure_token

    def get_test_curl(self, amount, trxtype="A"):
        prepped, session, secure_token_id = self._prepare_secure_token_request(
            amount, trxtype)
        return "curl -X POST -d '{data}' {url}".format(data=prepped.body, url=self.url)
