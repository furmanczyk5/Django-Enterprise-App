import json

from sentry_sdk import add_breadcrumb, capture_exception

from django.conf import settings

from myapa.models.contact_role import ContactRole
from events.models import Event, NATIONAL_CONFERENCE_CURRENT
from learn.utils.wcw_api_utils import ExternalService
from store.models import Purchase

from .models import CadmiumSync
from .models.settings import *

import logging
logger = logging.getLogger(__name__)
DEBUG_MODE = False

class CadmiumCallHelper(ExternalService):
    """
    Creates callable objects that make get/post calls to Cadmium's API.
    """

    def __init__(self,
                 method_name,  # the Cadmium API method name
                 http_method="get"
                 ):
        self.method_name = method_name
        self.http_method = http_method
        self.response = None
        self.success = None
        self.json = None
        super().__init__(timeout=30)

    @property
    def endpoint(self):
        """
        The endpoint url for making the call to Cadmium's server.
        """
        api_url = 'http://www.conferenceharvester.com/conferenceportal3/webservices/HarvesterJsonAPI.asp'
        # TEST ENDPOINT HAS NO DATA -- NO POINT IN USING RIGHT NOW
        # if settings.ENVIRONMENT_NAME == 'LOCAL' or settings.ENVIRONMENT_NAME == 'STAGING':
        #     api_url = 'https://www.conferenceharvester.com/conferenceportal3/webservices/HarvesterJsonAPITest.asp'
        # elif settings.ENVIRONMENT_NAME == 'PROD':
        #     api_url = 'http://www.conferenceharvester.com/conferenceportal3/webservices/HarvesterJsonAPI.asp'

        return api_url

    def log_error(self, log_method="error"):
        """
        Logs to logger (Sentry) as either as an error or exception
        """
        msg = 'Cadmium Sync Error Calling "%s"' % self.method_name
        getattr(logger, log_method)(msg, exc_info=True, extra={
            "data": {
                "endpoint": HARVESTER_API_URL,
                "response": self.response.text if self.response else None
            },
        })

    def __call__(self, fail_silently=True, log_soft_fails=True, **kwargs):
        """
        Makes the call, passing in kwargs as parameters, and returns the response as JSON.
        """
    # put try back in after testing??
    # try:
        self.success = False

        if self.http_method == 'get':
            self.response = self.make_request(self.endpoint, method=self.http_method, params=kwargs)
        elif self.http_method == 'post':
            params_dict = {'APIKey': kwargs.pop("APIKey"), 'Method': kwargs.pop("Method")}
            d = json.dumps(kwargs)
            post_body_json = [json.loads(d)]
            self.response = self.make_request(self.endpoint,
                                              method=self.http_method,
                                              json=post_body_json,
                                              params=params_dict)
        if self.response:
            print("request headers is ", self.response.request.headers)
            print("request method is ", self.response.request.method)
            print("request url is ", self.response.request.url)
            print("request body is ", self.response.request.body, "\n")
            self.json = self.response.json()
            if type(self.json) == type([]):
                if len(self.json) > 0:
                    self.success = not self.json[0].get("error", False) and self.json[0].get("success", True)
                else:
                    self.success = False
            else:
                self.json = self.response.json()
                self.success = False

        if not self.success:
            if not fail_silently:
                raise Exception("Cadmium response had an error or was explicitly unsuccessful, raising exception since fail_silently=False")
            elif log_soft_fails:
                self.log_error("error")

        if DEBUG_MODE:
            print(self.response.url)
            print(self.json)
            print("-------")

        return self.json
    # put back in after testing
    # except Exception as e:
    #     self.log_error("exception")
    #
    #     if not fail_silently:
    #         raise e

class CadmiumAPICaller():

    def django_event_to_cadmium_sync(self, event):
        try:
            if event.parent:
                microsite = event.parent.event_microsite.first()
                sync = microsite.cadmium_sync.first()
            else:
                microsite = event.master.event_microsite.first()
                sync = microsite.cadmium_sync.first()
        except Exception as e:
            sync = None
            # print("EXCEPTION GETTING CADMIUM API KEY FROM EVENT: ", e)
            capture_exception(e)
        return sync

    def sync_from_harvester(self, event):
        """
        Django button sync ("Harvest") of one event from Cadmium Harvester.
        :param event:
        :return:
        """
        json_data = ''
        print("CADMIUM EXTERNAL KEY FOR THIS EVENT IS ")
        print(event.external_key)
        sync = self.django_event_to_cadmium_sync(event)
        api_key = settings.CADMIUM_API_KEYS.get(sync.cadmium_event_key)

        if event.external_key:
            cadmium_method = 'getSinglePresentationWithPresenters'
            json_list = CadmiumCallHelper(cadmium_method, http_method='get')(
                # EventKey=event_key,
                APIKey=api_key,
                Method=cadmium_method,
                PresentationID=event.external_key
            )
            print("CADMIUM getSinglePresentationWithPresenters RESPONSE IS ")
            print(json_list)
            if not json_list[0].get('error', None):
                if json_list:
                    sync.update_presentation(event, json_list[0])

    def update_harvester_presenter(self, contact, jsonbody):
        """
        Update Harvester Presenter when member changes info in myAPA
        :param contact:
        :param jsonbody:
        :return:
        """
        event_keys = settings.CADMIUM_API_KEYS.keys()
        sync = CadmiumSync.objects.filter(cadmium_event_key__in=event_keys).first()
        if sync is None:
            return False, "No CadmiumSync object found with any key defined in CADMIUM_API_KEYS"
        api_key = settings.CADMIUM_API_KEYS.get(sync.cadmium_event_key)

        if contact.external_id:
            api_method = 'addUpdatePresenter'

            if jsonbody and len(jsonbody) > 0:
                response = CadmiumCallHelper(api_method, http_method='post')(
                    APIKey=api_key,
                    Method=api_method,
                    PresenterMemberNumber=contact.user.username,
                    **jsonbody[0]
                )
                print("UPDATE HARVESTER PRESENTER RESPONSE IS:")
                print(response)

                return (True, "Harvester update successful.")
            else:
                return (False, "Cannot update Harvester (no information provided).")
        else:
            return (False, "Contact does not have an external id from Cadmium.")

    def harvester_sync_all(self, test=True, event_key=None):
        """
        Sync all Postgres from Harvester at the command line
        :param test:
        :return:
        """
        api_method = 'getPresentationCount'
        num_presentations = 0
        api_key = settings.CADMIUM_API_KEYS.get(event_key)
        sync = CadmiumSync.objects.get(cadmium_event_key=event_key)
        json_list = CadmiumCallHelper(api_method, http_method='get')(
            APIKey=api_key,
            Method=api_method,
        )
        print("GET PRESENTATION COUNT RESPONSE IS:")
        print(json_list)
        if type(json_list) == type([]) and len(json_list) > 0:
            json_dict = json_list[0]
        else:
            json_dict = {}

        if not json_dict.get('error', None):
            num_presentations = int(json_dict['Count'])
        print("num presentations is --------------- ", num_presentations,"\n")
        interval = 10

        if test:
            num_presentations = 1
            interval = 10

        for i in range(0, num_presentations, interval):
            api_method = 'getPresentationsWithPresenters'

            json_list = CadmiumCallHelper(api_method, http_method='get')(
                APIKey=api_key,
                Method=api_method,
                Between='%s-%s' % (i, i+interval-1)
            )

            if not json_list[0].get('error', None):
                if json_list:
                    for presentation in json_list:
                        update_response = sync.update_presentation(
                            None, presentation)
                        print(update_response)

        print("-------------------------")
        print("YAY ALL DONE!")
        print("-------------------------")

    def imis_to_cadmium_sync_all(self, test=True):
        """
        USED FOR A MASS PUSH OF SPEAKERS FROM DJANGO TO HARVESTER
        :return:
        """
        current_conference = Event.objects.get(code=NATIONAL_CONFERENCE_CURRENT[0], publish_status="PUBLISHED")
        current_conference_roles = ContactRole.objects.filter(content__parent__content_live=current_conference)
        if test:
            current_conference_roles = [current_conference_roles.last()]
        contact_set = set()
        for cr in current_conference_roles:
            contact_set.add(cr.contact)
        for c in contact_set:
            c.sync_from_imis()
            jsonbody = [{
                "PresenterEmail":c.email,
                "PresenterTelephoneOffice":c.secondary_phone,
                "PresenterTelephoneCell":c.cell_phone,
                "PresenterOrganization":c.company,
                "PresenterAddress1":c.address1,
                "PresenterAddress2":c.address2,
                "PresenterCity":c.city,
                "PresenterState":c.state,
                "PresenterZip":c.zip_code,
                "PresenterCountry":c.country,
                "PresenterWebsite":c.personal_url,
                "PresenterLinkedIn":c.linkedin_url,
                "PresenterFacebook":c.facebook_url,
                "PresenterTwitter":c.twitter_url,
                "PresenterInstagram":c.instagram_url,
                "PresenterBiographyText":c.bio,
                "PresenterBioSketchText":c.about_me
            }]
            # REMOVE EMPTY STRING VALS FROM DICT OR THEY MIGHT OVERWRITE CADMIUM DATA
            jsonbody = [{k: v for k, v in jsonbody[0].items() if v is not ''}]
            update_harvester_presenter(c, jsonbody)
            print("UPDATING BIO -----------------------------")
            if test:
                print("INFO THAT WOULD BE SENT IS ")
                print(jsonbody)
            else:
                self.update_harvester_presenter(c, jsonbody)

    def view_presentation(self, event_code):
        """
        utility to look at json coming from Harvester
        :return:
        """
        ev = Event.objects.filter(code=event_code, publish_status='PUBLISHED').first()
        sync = self.django_event_to_cadmium_sync(ev)
        api_key = settings.CADMIUM_API_KEYS.get(sync.event_key)

        if ev.external_key:
            api_method = 'getSinglePresentationWithPresenters'

            response = CadmiumCallHelper(api_method, http_method='get')(
                APIKey=api_key,
                Method=api_method,
                PresentationID=ev.external_key
            )
            print("GET SINGLE PRESENTATION WITH PRESENTERS RESPONSE IS:")
            print(response)
            if not response.get('error', None):
                json_list = response.json()
                print("presentations json list is --- ", json_list, "\n")
    vp = view_presentation

    def update_registration_status(self, contact, event_key):
        """
        update Harvester registration status -- assumes that the speaker has already synced
        from Harvester to Django and their contact has an "external_id" value from Harvester
        :return:
        """
        if contact.external_id:
            username = contact.user.username
            external_id = contact.external_id
            api_method = 'completeTask'
            api_key = settings.CADMIUM_API_KEYS.get(event_key)
            reg_task_id = settings.CADMIUMCD_REGISTRATION_TASK_IDS[event_key]

            response_1 = CadmiumCallHelper(api_method, http_method='get')(
                # EventKey=event_key,
                APIKey=api_key,
                Method=api_method,
                PresenterID=external_id,
                TaskID = reg_task_id
            )
            print("COMPLETE TASK RESPONSE IS:")
            print(response_1)
            api_method = 'presenterReg'
            response_2 = CadmiumCallHelper(api_method, http_method='get')(
                APIKey=api_key,
                Method=api_method,
                PresenterID=external_id,
                TaskID=reg_task_id,
                PresenterRegCode=username,
                PresenterRegFlag=1
            )
            print("PRESENTER REG RESPONSE IS:")
            print(response_2)
            message = "%s NPC19 SPEAKER REGISTRAION" % (username)
            add_breadcrumb(
                message=message,
                data={
                    'complete_task_response': response_1,
                    'presenter_reg_response': response_2,
                    'username': username,
                    'external_id': external_id
                },
                level='debug'
            )

    def push_completed_reg(self, speaker_purchases=None, event_key=None):
        """
        BULK PUSH COMPLETED HARVESTER REGISTRATION TASKS
        :param speaker_purchases:
        :return:
        """
        try:
            sync = CadmiumSync.objects.get(cadmium_event_key=event_key)
            reg_product_code = sync.microsite.event_master.content_live.product.code
        except Exception as e:
            reg_product_code = None
            print("EXCEPTION GETTING PRODUCT CODE FROM SYNC: ", e)
        print("reg product code is ", reg_product_code)
        # current_npc_code = "19CONF"

        if not speaker_purchases:
            # speaker_purchases = Purchase.objects.filter(product__code=current_npc_code
            #     ).exclude(contact__external_id__isnull=True)
            speaker_purchases = Purchase.objects.filter(product__code=reg_product_code
                ).exclude(contact__external_id__isnull=True)

        count = speaker_purchases.count()
        i = 0
        for sp in speaker_purchases:
            contact = sp.contact
            if contact.external_id:
                i+=1
                self.update_registration_status(contact, event_key)
                print("%s of %s done." % (i, count))
