import base64
import json
from decimal import Decimal
from sentry_sdk import add_breadcrumb, capture_exception
import datetime
import pytz
import math

from imis import models as im
from imis.db_accessor import DbAccessor

from django.conf import settings
from django.utils import timezone

from myapa.models.contact import Contact
from api.clients.base import ExternalService

import logging
logger = logging.getLogger(__name__)
DEBUG_MODE = False

if settings.ENVIRONMENT_NAME == 'PROD':
    CREDLY_BADGE_TEMPLATE_IDS = {
        'AICP':'b671da8c-d4d0-49aa-9950-176f47dcf81b',
        'AICP Candidate':'a0e88652-4862-44da-b3db-d4cb40b3f647',
        'FAICP':'7511fbd0-265d-4080-a090-9a13982eac40',
        'CEP':'bdba1c01-096e-4b12-a39d-5635b94ec204',
        'CTP':'ade6d6d4-821b-428a-83bb-19b5d14d1246',
        'CUD':'f66029c9-8ad6-48d0-a313-b8fee41774de',
    }
else:
    CREDLY_BADGE_TEMPLATE_IDS = {
        'AICP':'f0c2300d-03a0-44c5-82b8-7c48553d41f2',
        'AICP Candidate':'ef6f92b0-f439-4b8b-8e69-1a3d5522702d',
        'FAICP':'2be373dc-4575-47ae-84e2-08a77adcfa39',
        'CEP':'b21146d0-a770-44cf-8472-2af32bce4145',
        'CTP':'80386b0c-98d2-4d37-a601-d4a574a4ab1c',
        'CUD':'7b79ded0-3812-4a6a-9a76-f2ff986296ff',
    }

CREDLY_MEMBER_TYPES = ('FCLTI', 'FCLTS', 'LIFE', 'MEM', 'RET', 'STF', 'STU')


class CredlyCallHelper(ExternalService):
    """
    Creates callable objects that make HTTP method calls to Credly's Badge API.
    """

    def __init__(self,
                 endpoint_path,
                 http_method="get",
                 **kwargs
                 ):
        self.endpoint_path = endpoint_path
        self.http_method = http_method
        self.response = None
        self.success = None
        self.json = None
        self.headers = None
        # self.instance = kwargs.pop("instance", None)
        self.organization_id = settings.CREDLY_ORGANIZATION_ID
        self.__dict__.update(kwargs)
        super().__init__(timeout=30)


    @property
    def endpoint(self):
        """
        The endpoint url for making the call to Credly's API.
        """
        api_url = settings.CREDLY_API_URL

        return api_url

    def log_error(self, log_method="error", endpoint="", exception=""):
        """
        Logs to logger (Sentry) either as error or exception
        """
        msg = 'Credly API Error Calling "%s"' % self.endpoint_path
        getattr(logger, log_method)(msg, exc_info=True, extra={
            "data": {
                "endpoint": endpoint,
                "response": self.response.text if self.response else None,
                "exception": exception
            },
        })

    def __call__(self, fail_silently=True, log_soft_fails=True, **kwargs):
        """
        Makes the call, passing in kwargs as parameters, and returns the response as JSON.
        """
    # put try back in after testing??
    # try:
        exception = ""
        self.success = False
        at = settings.CREDLY_AUTHORIZATION_TOKEN
        atb = at.encode('utf-8')
        b64atb = base64.b64encode(atb)
        b64atbstr = b64atb.decode()
        self.headers = {'accept': 'application/json',
                        'authorization': 'Basic ' + b64atbstr,
                        'content-type': 'application/json'
                        }
        if self.http_method == 'get':
            # this is because credly inserts another directory in callback URLs:
            endpoint_stem = settings.CREDLY_API_URL.split(".com")[0]
            if self.endpoint_path.find(endpoint_stem) >= 0:
                url = self.endpoint_path
            else:
                url = self.endpoint + self.endpoint_path
            self.response = self.make_request(url, method=self.http_method, params=kwargs, headers=self.headers)
        elif self.http_method == 'post' or self.http_method == 'put':
            self.response = self.make_request(self.endpoint + self.endpoint_path,
                                                method=self.http_method,
                                                json=kwargs,
                                                headers=self.headers)
        elif self.http_method == 'delete':
            self.response = self.make_request(self.endpoint + self.endpoint_path,
                                                method=self.http_method,
                                                headers=self.headers)

        # boolean logic on these response obejcts depends on their status code; if code is >= 400
        # it has a boolean value == None
        if self.response:
            # print("request headers is ", self.response.request.headers)
            # print("request method is ", self.response.request.method)
            # print("request url is ", self.response.request.url)
            # print("request body is ", self.response.request.body, "\n")

            try:
                self.json = self.response.json()
            except Exception as e:
                exception = e
                print("Exception: ", e)
                self.json = {}

            if len(self.json) > 0:
                self.success = True
            else:
                self.success = False

            if not self.success:
                if not fail_silently:
                    raise Exception("Credly response had an error or was explicitly unsuccessful, raising exception since fail_silently=False")
                elif log_soft_fails:
                    self.log_error("error", self.response.url, exception)

            if DEBUG_MODE:
                print(self.response.url)
                print(self.json)
                print("-------")
        # IF WE HAVE AN ERROR RESPONSE FROM A REPLACE CALL, WE STILL WANT THE JSON BECAUSE IT'S THE ONLY WAY TO GET THE current_badge_id
        if not self.json:
            try:
                self.json = self.response.json()
                # If this is not a credly replace error, then do nothing.
                if self.json['data']['message'].find('Validation failed: This badge cannot be replaced because it has already been replaced.') < 0:
                    self.json = None
            except Exception as e:
                print("EXCEPTION GETTING JSON FROM ERROR RESPONSE: ", e)
                self.json = None
        return self.json
    # put back in after testing?
    # except Exception as e:
    #     self.log_error("exception")
    #
    #     if not fail_silently:
    #         raise e

class CredlyAPICaller():

    def __init__(self, **kwargs):
        # self.instance = kwargs.pop("instance", None)
        self.organization_id = settings.CREDLY_ORGANIZATION_ID
        # if we want kwargs in here later, we'll need this:
        self.__dict__.update(kwargs)

    def get_organizations(self):
        endpoint_path = 'organizations'
        response = CredlyCallHelper(endpoint_path, http_method='get')()
        return response or {}

    def get_badge_templates(self):
        endpoint_path = 'organizations/%s/badge_templates' % self.organization_id
        response = CredlyCallHelper(endpoint_path, http_method='get')()
        return response or {}

    def get_single_badge_template(self, badge_template_id):
        endpoint_path = 'organizations/%s/badge_templates/%s' % (self.organization_id, badge_template_id)
        response = CredlyCallHelper(endpoint_path, http_method='get')()
        return response or {}

    def get_issued_badges(self, user_id=None, filter_keys=None, sort_keys=None, page_keys=None):
        endpoint_path = 'organizations/%s/badges' % self.organization_id
        response = CredlyCallHelper(endpoint_path, http_method='get',)(
            # query=email,
            # user_id=user_id,
            filter=filter_keys,
            sort=sort_keys,
            page=page_keys
            )
        return response or {}

    def get_bulk_badges(self, user_id=None, filter_keys=None, badge_format='minimal'):
        endpoint_path = 'organizations/%s/high_volume_issued_badge_search' % self.organization_id
        response = CredlyCallHelper(endpoint_path, http_method='get',)(
            filter=filter_keys,
            badge_format=badge_format # can also be 'default' (more data)
            )
        data = response.get('data') or []
        metadata = response.get('metadata') or {}
        next_page_url = metadata.get('next_page_url')
        composite = []
        if not next_page_url:
            return response or {}
        else:
            composite = composite + data

        while next_page_url:
            response = CredlyCallHelper(next_page_url, http_method='get',)()
            data = response.get('data') or []
            composite = composite + data
            metadata = response.get('metadata') or {}
            next_page_url = metadata.get('next_page_url')
        return {'data': composite} if composite else {}

    def issue_badge(self, recipient_email, issued_to_first_name, issued_to_last_name, badge_template_id, issued_at,
                    issued_to_middle_name=None,
                    user_id=None, issuer_earner_id=None, locale='en', suppress_badge_notification_email=False,
                    expires_at=None, country_name=None, state_or_province=None, evidence=None):
        endpoint_path = 'organizations/%s/badges' % self.organization_id
        response = CredlyCallHelper(
            endpoint_path,
            http_method='post',
            )(
            recipient_email=recipient_email,
            issued_to_first_name=issued_to_first_name,
            issued_to_last_name=issued_to_last_name,
            badge_template_id=badge_template_id,
            issued_at=issued_at,
            issued_to_middle_name=issued_to_middle_name,
            # user_id=user_id, # not sure if we need/want this
            issuer_earner_id=issuer_earner_id,
            locale=locale,
            suppress_badge_notification_email=suppress_badge_notification_email,
            expires_at=expires_at,
            country_name=country_name,
            state_or_province=state_or_province,
            evidence=evidence
        )
        return response or {}

    def replace_badge(self, badge_id, badge_template_id, issued_at, issued_to=None, issued_to_first_name=None,
                        issued_to_middle_name=None, issued_to_last_name=None, issuer_earner_id=None, expires_at=None,
                        country_name=None, state_or_province=None, evidence=None, notification_message=None):
        endpoint_path = 'organizations/%s/badges/%s/replace' % (self.organization_id, badge_id)
        response = CredlyCallHelper(
            endpoint_path,
            http_method='post',
            )(
            # required fields
            # badge_id WAS MISSING UNTIL 2021-JUN-10:
            badge_id=badge_id,
            badge_template_id=badge_template_id,
            issued_at=issued_at,
            # optional fields
            issued_to=issued_to,
            issued_to_first_name=issued_to_first_name,
            issued_to_middle_name=issued_to_middle_name,
            issued_to_last_name=issued_to_last_name,
            issuer_earner_id=issuer_earner_id,
            expires_at=expires_at,
            country_name=country_name,
            state_or_province=state_or_province,
            evidence=evidence,
            notification_message=notification_message
        )
        return response or {}

    def revoke_badge(self, badge_id, reason="None", suppress_revoke_notification_email=False):
        endpoint_path = 'organizations/%s/badges/%s/revoke' % (self.organization_id, badge_id)
        response = CredlyCallHelper(
            endpoint_path,
            http_method='put',
            )(
            reason=reason,
            suppress_revoke_notification_email=suppress_revoke_notification_email
        )
        return response or {}

    def issue_badges_batch(self, badges):
        endpoint_path = 'organizations/%s/badges/batch' % (self.organization_id)
        response = CredlyCallHelper(
            endpoint_path,
            http_method='post',
            )(
            badges=badges
        )
        return response or {}

    # ONLY to delete earner's data for purposes of private data regulations
    def delete_badge(self, badge_id):
        endpoint_path = 'organizations/%s/badges/%s' % (self.organization_id, badge_id)
        response = CredlyCallHelper(
            endpoint_path,
            http_method='delete',
            )(
        )
        return response or {}

    def designation_to_badges(self, imis_name):
        ind = im.IndDemographics.objects.get(id=imis_name.id)
        aicp_cert_no = ind.aicp_cert_no
        if aicp_cert_no and aicp_cert_no.strip():
            evidence = [{"type": "IdEvidence","title": "AICP Certification Number",
                        "description": str(aicp_cert_no.strip())}]
        else:
            evidence = None
        designations_string = imis_name.designation
        recipient_email = imis_name.email
        issued_to = imis_name.full_name
        issued_to_first_name = imis_name.first_name
        issued_to_middle_name = imis_name.middle_name or None
        issued_to_last_name = imis_name.last_name
        now = timezone.now()
        issued_at_now=datetime.datetime.strftime(now, "%Y-%m-%d %H:%M:%S %z")
        literal_now=datetime.datetime.strftime(now, "%Y-%m-%d %H:%M:%S %z")
        # HANDLE issued_at LIKE THIS: (asdt = aicp start date)
        cen=pytz.timezone('US/Central')
        now_cen = now.astimezone(cen)
        asdt_default_utc = ind.aicp_start
        if asdt_default_utc:
            asdt=asdt_default_utc.astimezone(cen)
            new_now = now_cen.replace(year=asdt.year, month=asdt.month, day=asdt.day,
                hour=asdt.hour, minute=asdt.minute, second=asdt.second, microsecond=asdt.microsecond)
            issued_at_aicp=datetime.datetime.strftime(new_now, "%Y-%m-%d %H:%M:%S %z")
        else:
            issued_at_aicp=None
        fasdt_default_utc = ind.faicp_start
        if fasdt_default_utc:
            fasdt=fasdt_default_utc.astimezone(cen)
            new_now = now_cen.replace(year=fasdt.year, month=fasdt.month, day=fasdt.day,
                hour=fasdt.hour, minute=fasdt.minute, second=fasdt.second, microsecond=fasdt.microsecond)
            issued_at_faicp=datetime.datetime.strftime(new_now, "%Y-%m-%d %H:%M:%S %z")
        else:
            issued_at_faicp=None

        country_name = imis_name.country
        state_or_province = imis_name.state_province

        filter_keys='issuer_earner_id::%s|state::pending,accepted' % imis_name.id
        user_badges = self.get_issued_badges(filter_keys=filter_keys) or {}
        data=user_badges.get('data') or []
        badge_template_id_list = [d['badge_template']['id'] for d in data]

        for des in CREDLY_BADGE_TEMPLATE_IDS.keys():
            if designations_string.find(des) > -1:
                verified_aicp = True if des == 'AICP' and designations_string.find('AICP Candidate') < 0 else False
                if des != 'AICP' or verified_aicp:
                    if des != 'FAICP':
                        issued_at = issued_at_aicp if verified_aicp and issued_at_aicp else issued_at_now
                    else:
                        issued_at = issued_at_faicp if issued_at_faicp else issued_at_now

                    badge_template_id=CREDLY_BADGE_TEMPLATE_IDS[des]
                    if badge_template_id not in badge_template_id_list:
                        self.issue_badge(
                            recipient_email, issued_to_first_name, issued_to_last_name, badge_template_id, issued_at,
                            issued_to_middle_name=issued_to_middle_name,
                            # issuer_earner_id=aicp_cert_no, country_name=country_name, state_or_province=state_or_province,
                            issuer_earner_id=imis_name.id, country_name=country_name, state_or_province=state_or_province,
                            evidence=evidence)
                    else:
                        for badge in data:
                            if badge['badge_template']['id'] == badge_template_id:
                                if badge['expires_at']:
                                    self.replace_badge(
                                            badge['id'], badge_template_id, issued_at, issued_to=issued_to,
                                            issued_to_first_name=issued_to_first_name, issued_to_last_name=issued_to_last_name,
                                            # issuer_earner_id=aicp_cert_no,
                                            issuer_earner_id=imis_name.id, issued_to_middle_name=issued_to_middle_name,
                                            expires_at=None, country_name=country_name, state_or_province=state_or_province,
                                            notification_message="Your badge has been renewed.", evidence=evidence)
                                    data.remove(badge)
                                else:
                                    data.remove(badge)
        for badge in data:
            self.replace_badge(
                    badge['id'], badge['badge_template']['id'], badge['issued_at'], issued_to=issued_to,
                    issued_to_first_name=issued_to_first_name, issued_to_last_name=issued_to_last_name,
                    # issuer_earner_id=aicp_cert_no,
                    issuer_earner_id=imis_name.id, issued_to_middle_name=issued_to_middle_name,
                    expires_at=literal_now, country_name=country_name, state_or_province=state_or_province,
                    notification_message="Your badge has expired.", evidence=evidence)

    # ADAPT THIS TO FIX WRONGLY EXPIRED -- POSSIBLY FIXING THE WEIRD NAMES/emails ALSO?
    # Could also manually pull data consisting of just expired badges and pass into this?
    # I THINK THE SOLUTION IS TO RUN THIS ON THE EXPIRED BADGE DATA SET
    # THEN TO RUN designation_to_badges on each imis user in expired badge data set
    def credly_mass_replace(self, data=None, num=None):
        '''
        ONE-TIME MASS REPLACE TO WRITE IMIS IDS AND MIDDLE NAMES TO CREDLY (DOES NOT AFFECT THE BADGES OTHERWISE)
        KEPT HERE FOR REFERENCE PURPOSES ONLY.
        '''
        verified_imis_ids = set()
        if not data:
            bulk_badges = self.get_bulk_badges()
            data = bulk_badges.get('data') or []

        num_badges = len(data)
        # for testing a subset of the full run:
        if num:
            data = data[10000:10000+num]

        for i, badge in enumerate(data):
            print("\n+++++++++++++++++++++++++ STARTING %s of %s" % (i, num_badges))
            recipient_email = badge.get('recipient_email')
            issued_to = badge.get('issued_to')
            issued_to_first_name = badge.get('issued_to_first_name')
            issued_to_middle_name = badge.get('issued_to_middle_name')
            issued_to_last_name = badge.get('issued_to_last_name')
            issuer_earner_id = badge.get('issuer_earner_id')

            try:
                imis_name = im.Name.objects.get(first_name=issued_to_first_name,
                    last_name=issued_to_last_name, email=recipient_email)
            except Exception as e:
                imis_name = None
                print("EXCEPTION GETTING IMIS Name WITH EMAIL: ", e)
                print("FOR BADGE: ", badge)

            # because email may have changed since badge was issued we can catch some of these like this:
            # if more than one imis record exists on the name values, then it will have to be handled manually
            if not imis_name:
                try:
                    imis_name = im.Name.objects.get(first_name=issued_to_first_name,
                        last_name=issued_to_last_name)
                except Exception as e:
                    imis_name = None
                    print("EXCEPTION GETTING IMIS Name WITH ONLY FIRST NAME AND LAST NAME: ", e)
                    print("FOR BADGE: ", badge)

            if not imis_name:
                try:
                    ind = im.IndDemographics.objects.get(aicp_cert_no=issuer_earner_id)
                    imis_name = im.Name.objects.get(id=ind.id)
                except Exception as e:
                    imis_name = None
                    print("EXCEPTION GETTING IMIS Name WITH aicp_cert_no: ", e)
                    print("FOR BADGE: ", badge)

            if imis_name:
                try:
                    ind = im.IndDemographics.objects.get(id=imis_name.id)
                except Exception as e:
                    ind = None
                    print("EXCEPTION GETTING IMIS IndDemographics: ", e)
                    print("FOR BADGE: ", badge['recipient_email'])
                    print("AND FOR IMIS NAME: ", imis_name.id)

                if ind:
                    aicp_cert_no = ind.aicp_cert_no

                    if aicp_cert_no and aicp_cert_no.strip():
                        evidence = [{"type": "IdEvidence","title": "AICP Certification Number",
                                    "description": str(aicp_cert_no.strip())}]
                    else:
                        evidence = None

                    # I THINK HERE'S ALL WE NEED TO TRY TO FIX EXPIRED: GRAB THE IMIS IDS IN A SET AND RETURN IT
                    # THEN MANUALLY RUN designation_to_badge on that set of imis ids
                    verified_imis_ids.add(imis_name.id)

                    response = self.replace_badge(
                            badge['id'], badge['badge_template']['id'], badge['issued_at'], issued_to=issued_to,
                            issued_to_first_name=issued_to_first_name, issued_to_last_name=issued_to_last_name,
                            issuer_earner_id=imis_name.id,
                            issued_to_middle_name=issued_to_middle_name or imis_name.middle_name or None,
                            expires_at=badge['expires_at'], country_name=imis_name.country, state_or_province=imis_name.state_province,
                            evidence=evidence)
                    print("FINISHED REPLACE BADGE CALL FOR BADGE: ")
                    print(badge)
                    print("RESPONSE IS -------------------------------------------- ")
                    print(response)
                    try:
                        if response['data']['message'].find('Validation failed: This badge cannot be replaced because it has already been replaced.') >=0:
                            current_badge_id = response['metadata']['current_badge_id']
                            print("CURRENT BADGE FROM ERROR IS ", current_badge_id)
                            response = self.replace_badge(
                                    current_badge_id, badge['badge_template']['id'], badge['issued_at'], issued_to=issued_to,
                                    issued_to_first_name=issued_to_first_name, issued_to_last_name=issued_to_last_name,
                                    issuer_earner_id=imis_name.id,
                                    issued_to_middle_name=issued_to_middle_name or imis_name.middle_name or None,
                                    expires_at=badge['expires_at'], country_name=imis_name.country, state_or_province=imis_name.state_province,
                                    evidence=evidence)
                            print("FINISHED 2nd REPLACE BADGE CALL using current_badge_id from Error FOR BADGE: ")
                            print(badge)
                            print("RESPONSE IS -------------------------------------------- ")
                            print(response)
                    except Exception as e:
                        print("EXCEPTION REPLACING FROM ERROR METADATA: ", e)
        return verified_imis_ids

    def credly_fix_expired(self, data=None, num=None):
        '''
        POSSIBLY REUSABLE METHOD TO FIX WRONGLY EXPIRED BADGES
        SAME AS credly_mass_replace, EXCEPT IT CHECKS iMIS DESIGNATION AND EXPIRES/UNEXPIRES THE BADGE BEING
        REPLACED ACCORDINGLY
        '''
        # it's possible this will pull only 'properly' expired badges, or all?
        verified_imis_ids = set()

        if not data:
            filter_keys='expires_at_date_max::2021-06-26'
            bulk_badges = self.get_bulk_badges(filter_keys=filter_keys)
            data = bulk_badges.get('data') or []

        num_badges = len(data)
        print("NUM EXPIRED IS: ", num_badges)
        # once we have the expired badges, the question is: can we tie it to iMIS 1-to-1? If so we can replace
        # the badge if necessary based on current iMIS designation
        # BUT: If you have an expired badge and you tie it back to iMIS, you don't know if it is the current version of
        # that badge... but trying to replace it will tell you that so it's safe... the error will return the current badge
        # and it's safe to replace that badge based on current iMIS designation. But if there is no iMIS id it means
        # the mass replace failed to tie it to iMIS... so how can there be any hope of any new ties to iMIS? unless the
        # above mass replace overlooks expired badges?
        # for testing a subset of the full run:
        if num:
            data = data[10000:10000+num]

        for i, badge in enumerate(data):
            print("\n+++++++++++++++++++++++++ STARTING %s of %s" % (i, num_badges))
            recipient_email = badge.get('recipient_email')
            issued_to = badge.get('issued_to')
            issued_to_first_name = badge.get('issued_to_first_name')
            issued_to_middle_name = badge.get('issued_to_middle_name')
            issued_to_last_name = badge.get('issued_to_last_name')
            issuer_earner_id = badge.get('issuer_earner_id')

            try:
                imis_name = im.Name.objects.get(first_name=issued_to_first_name,
                    last_name=issued_to_last_name, email=recipient_email)
            except Exception as e:
                imis_name = None
                print("EXCEPTION GETTING IMIS Name WITH EMAIL: ", e)
                print("FOR BADGE: ", badge)

            # because email may have changed since badge was issued we can catch some of these like this:
            # if more than one imis record exists on the name values, then it will have to be handled manually
            if not imis_name:
                try:
                    imis_name = im.Name.objects.get(first_name=issued_to_first_name,
                        last_name=issued_to_last_name)
                except Exception as e:
                    imis_name = None
                    print("EXCEPTION GETTING IMIS Name WITH ONLY FIRST NAME AND LAST NAME: ", e)
                    print("FOR BADGE: ", badge)

            if not imis_name:
                try:
                    ind = im.IndDemographics.objects.get(aicp_cert_no=issuer_earner_id)
                    imis_name = im.Name.objects.get(id=ind.id)
                except Exception as e:
                    imis_name = None
                    print("EXCEPTION GETTING IMIS Name WITH aicp_cert_no: ", e)
                    print("FOR BADGE: ", badge)

            if imis_name:
                try:
                    ind = im.IndDemographics.objects.get(id=imis_name.id)
                except Exception as e:
                    ind = None
                    print("EXCEPTION GETTING IMIS IndDemographics: ", e)
                    print("FOR BADGE: ", badge['recipient_email'])
                    print("AND FOR IMIS NAME: ", imis_name.id)

                if ind:
                    aicp_cert_no = ind.aicp_cert_no

                    if aicp_cert_no and aicp_cert_no.strip():
                        evidence = [{"type": "IdEvidence","title": "AICP Certification Number",
                                    "description": str(aicp_cert_no.strip())}]
                    else:
                        evidence = None

                    # one more thing: use imis designation to figure out which badges should be expired/unexpired
                    # as they are being replaced
                    verified_imis_ids.add(imis_name.id)
                    # print("IMIS IDS ------------------------------------")
                    # print(verified_imis_ids)

                    # response = self.replace_badge(
                    #         badge['id'], badge['badge_template']['id'], badge['issued_at'], issued_to=issued_to,
                    #         issued_to_first_name=issued_to_first_name, issued_to_last_name=issued_to_last_name,
                    #         issuer_earner_id=imis_name.id,
                    #         issued_to_middle_name=issued_to_middle_name or imis_name.middle_name or None,
                    #         expires_at=badge['expires_at'], country_name=imis_name.country, state_or_province=imis_name.state_province,
                    #         evidence=evidence)
                    # print("FINISHED REPLACE BADGE CALL FOR BADGE: ")
                    # print(badge)
                    # print("RESPONSE IS -------------------------------------------- ")
                    # print(response)
                    # try:
                    #     if response['data']['message'].find('Validation failed: This badge cannot be replaced because it has already been replaced.') >=0:
                    #         current_badge_id = response['metadata']['current_badge_id']
                    #         print("CURRENT BADGE FROM ERROR IS ", current_badge_id)
                    #         response = self.replace_badge(
                    #                 current_badge_id, badge['badge_template']['id'], badge['issued_at'], issued_to=issued_to,
                    #                 issued_to_first_name=issued_to_first_name, issued_to_last_name=issued_to_last_name,
                    #                 issuer_earner_id=imis_name.id,
                    #                 issued_to_middle_name=issued_to_middle_name or imis_name.middle_name or None,
                    #                 expires_at=badge['expires_at'], country_name=imis_name.country, state_or_province=imis_name.state_province,
                    #                 evidence=evidence)
                    #         print("FINISHED 2nd REPLACE BADGE CALL using current_badge_id from Error FOR BADGE: ")
                    #         print(badge)
                    #         print("RESPONSE IS -------------------------------------------- ")
                    #         print(response)
                    # except Exception as e:
                    #     print("EXCEPTION REPLACING FROM ERROR METADATA: ", e)
        # THIS NO WORK?
        return verified_imis_ids

    # THIS CAN BE RUN MULTIPLE TIMES, BUT ONLY FOR THE INITIAL MASS SYNC (PREFERABLY SAME DAY)
    def credly_mass_sync(self, name_queryset):
        '''
        ONE-TIME ONLY FOR LAUNCH. KEPT HERE FOR REFERENCE PURPOSES ONLY.
        '''
        badges = []
        exclude_list = []

        if not name_queryset:
            name_queryset = im.Name.objects.filter(designation__isnull=False).exclude(designation='').filter(
                member_type__in=CREDLY_MEMBER_TYPES)
        bulk_badges = self.get_bulk_badges()
        data = bulk_badges.get('data') or []

        for badge in data:
            exclude_list.append(badge.get('recipient_email'))
        list_len = len(exclude_list)
        end = 100 if list_len > 100 else list_len
        exclude_set = set(exclude_list)
        exclude_list = list(exclude_set)
        list_len = len(exclude_list)
        total = name_queryset.count()

        for i in range(0, total, 30):
            top = i+30 if i+30 <= total else total
            imis_names = name_queryset[i:top]
            for imis_name in imis_names:
                if imis_name.email not in exclude_list:
                    ind=im.IndDemographics.objects.get(id=imis_name.id)
                    aicp_cert_no=ind.aicp_cert_no
                    if aicp_cert_no and aicp_cert_no.strip():
                        evidence = [{"type": "IdEvidence","title": "AICP Certification Number",
                                    "description": str(aicp_cert_no.strip())}]
                    else:
                        evidence = None
                    designations_string = imis_name.designation
                    cen=pytz.timezone('US/Central')
                    now=timezone.now()
                    issued_at_now = datetime.datetime.strftime(now, "%Y-%m-%d %H:%M:%S %z")
                    asdt_default_utc = ind.aicp_start
                    if asdt_default_utc:
                        asdt=asdt_default_utc.astimezone(cen)
                        now_cen = now.astimezone(cen)
                        new_now = now_cen.replace(year=asdt.year, month=asdt.month, day=asdt.day,
                            hour=asdt.hour, minute=asdt.minute, second=asdt.second, microsecond=asdt.microsecond)
                        issued_at_aicp=datetime.datetime.strftime(new_now, "%Y-%m-%d %H:%M:%S %z")
                    else:
                        issued_at_aicp=None
                    for des in CREDLY_BADGE_TEMPLATE_IDS.keys():
                        if designations_string.find(des) > -1:
                            verified_aicp = True if des == 'AICP' and designations_string.find('AICP Candidate') < 0 else False
                            if des != 'AICP' or verified_aicp:
                                issued_at = issued_at_aicp if verified_aicp and issued_at_aicp else issued_at_now
                                email = imis_name.email
                                fname = imis_name.first_name
                                lname = imis_name.last_name
                                mname = imis_name.middle_name or None
                                if email and fname and lname:
                                    badge = {}
                                    badge["badge_template_id"]=CREDLY_BADGE_TEMPLATE_IDS[des]
                                    badge["recipient_email"]=email
                                    badge["issued_to_first_name"]=fname
                                    badge["issued_to_middle_name"]=mname
                                    badge["issued_to_last_name"]=lname
                                    # badge["issuer_earner_id"]=aicp_cert_no
                                    badge["issuer_earner_id"]=imis_name.id
                                    badge["issued_at"]=issued_at
                                    badge["evidence"]=evidence
                                    badges.append(badge)
            if badges:
                self.issue_badges_batch(badges)
            badges = []

    def credly_nightly_sync(self):
        now = timezone.now()
        aday = datetime.timedelta(days=1)
        yday = now - aday
        yday_formatted = yday.strftime('%Y-%m-%d %H:%M:%S')
        query = """
                SELECT ID
                FROM Name_Log
                WHERE LOG_TYPE = 'CHANGE' AND LOG_TEXT = 'NAME.DESIGNATION UPDATE' AND DATE_TIME > ?;
                """
        rows = DbAccessor().get_rows(query, [yday_formatted])
        changed_name_ids = [r[0] for r in rows]
        # PROB. BEST TO NOT EXCLUDE ANYTHING HERE
        # ns = im.Name.objects.filter(
        #     id__in=changed_name_ids, designation__isnull=False).exclude(
        #     designation='').filter(
        #     member_type__in=CREDLY_MEMBER_TYPES)
        ns = im.Name.objects.filter(id__in=changed_name_ids)
        for n in ns:
            self.designation_to_badges(n)

    # ONLY FOR REMOVAL OF PERSONAL DATA FROM SERVER TO SATISFY DATA REGULATIONS
    # def delete_all_badges(self):
    #     user_badges = self.get_bulk_badges() or {}
    #     data=user_badges.get('data') or []

    #     for d in data:
    #         bid = d.get('id')
    #         print("badge id to delete is ......................................... ", bid)
    #         if bid:
    #             self.delete_badge(bid)

    def credly_initial_dues_sync(self, username):
        now = timezone.now()
        anhour = datetime.timedelta(hours=8)
        anhourago = now - anhour
        anhourago_formatted = anhourago.strftime('%Y-%m-%d %H:%M:%S')
        query = """
                SELECT TOP 1 Name_Log.ID
                FROM Name_Log
                JOIN Name ON Name_Log.ID = Name.ID
                WHERE Name_Log.LOG_TYPE = 'CHANGE'
                    AND Name_Log.LOG_TEXT = 'NAME.DESIGNATION UPDATE'
                    AND Name_Log.DATE_TIME > ?
                    AND Name_Log.ID = ?
                ORDER BY DATE_TIME DESC;
                """
        rows = DbAccessor().get_rows(query, [anhourago_formatted, username])
        initial_dues_id = [r[0] for r in rows]
        confirmed_id = initial_dues_id[0] if initial_dues_id else None
        if confirmed_id:
            ns = im.Name.objects.filter(
                id=confirmed_id, designation__isnull=False).exclude(
                designation='').filter(
                member_type__in=CREDLY_MEMBER_TYPES)
        else:
            ns = []
        for n in ns:
            self.designation_to_badges(n)

