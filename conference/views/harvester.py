import ast
import json

from django.conf import settings
from django.http import HttpResponse, Http404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from conference.models import Microsite, NationalConferenceActivity, CadmiumSync
from events.models import Event, Activity

import logging
logger = logging.getLogger(__name__)

def get_dummy_json(dict_string):
    post_list = ast.literal_eval(dict_string)
    post_dict = post_list[0]
    post_json_str = json.dumps(post_dict)
    obj_dict = json.loads(post_json_str)
    return obj_dict


# NOT CURRENTLY OPERATIONAL -- WOULD HAVE TO BE REFACTORED AS BELOW
class DeletePresentation(View):

    # COMMENT OUT FOR DEPLOY
    # @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        context = {}
        external_key = kwargs.get("external_key")
        e = None

        if request.method == 'POST':
            received_json_data=json.loads(request.body.decode('utf-8'))
            e = received_json_data

        if e:
            # CADMIUM REFACTOR NOT SURE IF EventKey PULLED LIKE THIS:
            event_key = e["EventKey"]
            sync = CadmiumSync.objects.get(cadmium_event_key=event_key)
            microsite = getattr(sync, "microsite", None)
            if microsite and microsite.is_npc:
                activities = NationalConferenceActivity.objects.filter(
                    external_key=external_key, publish_status="DRAFT")
            else:
                activities = Activity.objects.filter(
                    external_key=external_key, publish_status="DRAFT")
            # OLD -- CADMIUM REFACTOR:
            # activities = NationalConferenceActivity.objects.filter(
            #     external_key=external_key, publish_status="DRAFT")
            num = activities.count()

            if num == 1:
                # Here "self" is the view
                context = sync.delete_presentation(self)
                # context = delete_presentation(self, e)
                context["success"] = True
                context["message"] = "Successfully marked activity for deletion."
            else:
                raise Http404("Error: %s Draft Activity records found." % num)

        return HttpResponse(json.dumps(context), content_type='application/json')


class UpdatePresentation(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        api_key = request.GET.get('api_key', '')
        if api_key != settings.API_KEY:
            return HttpResponse('Unauthorized', status=401)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        context = {}
        external_key = kwargs.get("external_key")
        info = None
        event_key = request.GET.get('id', '')

        try:
            if request.method == 'POST':
                data = request.body.decode('utf-8')
                received_json_data = json.loads(data)
                info = received_json_data[0]

            if info:
                if event_key:
                    sync = CadmiumSync.objects.filter(cadmium_event_key=event_key).first()
                    microsite = getattr(sync, "microsite", None)
                else:
                    sync = None
                    microsite = None

                if not sync:
                    generic_event = Event.objects.filter(
                        external_key=external_key, publish_status="DRAFT").first()
                    event_master = getattr(generic_event, 'parent', None)
                    microsite = Microsite.objects.filter(event_master=event_master).first() if event_master else None
                    sync = microsite.cadmium_sync.first() if microsite else None

                if sync and external_key:
                    if microsite and microsite.is_npc:
                        activities = NationalConferenceActivity.objects.filter(
                            external_key=external_key, publish_status="DRAFT")
                    else:
                        activities = Activity.objects.filter(
                            external_key=external_key, publish_status="DRAFT")
                    if activities.count() == 0 or activities.count() == 1:
                        context = sync.update_presentation(self, info)
                    else:
                        raise Http404("Error: More than one Draft Activity record found.")
                else:
                    raise Http404("Error: No Django sync record exists or no external_key sent from Cadmium")
        except Exception as e:
            msg = 'Cadmium Real-time Sync Error Calling UpdatePresentation'
            getattr(logger, "error")(msg, exc_info=True, extra={
                "data": {
                    "Exception": e,
                    "request": request,
                    "external_key": external_key,
                    "data_sent": info
                },
            })

        if not context:
            context = { "request": str(request), "external_key": external_key, "data_sent": info }
        return HttpResponse(json.dumps(context), content_type='application/json')


class UpdatePresenter(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        api_key = request.GET.get('api_key', '')
        if api_key != settings.API_KEY:
            return HttpResponse('Unauthorized', status=401)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        context = {}
        external_id = kwargs.get("external_id")
        s = None

        try:
            if request.method == 'POST':
                data = request.body.decode('utf-8')
                received_json_data = json.loads(data)
                s = received_json_data[0]

            if s:
                context = CadmiumSync().update_presenter(self, s)
        except Exception as e:
            msg = 'Cadmium Real-time Sync Error Calling UpdatePresenter'
            getattr(logger, "error")(msg, exc_info=True, extra={
                "data": {
                    "Exception": e,
                    "request": request,
                    "external_id": external_id,
                    "data_sent": s
                },
            })

        if not context:
            context = {"request": str(request), "external_id": external_id, "data_sent": s}
        return HttpResponse(json.dumps(context), content_type='application/json')


