from django.shortcuts import render

from planning.settings import API_KEY

# TO DO... this is duplicated in My APA... need to move somewhere universal...
class ApiCheckKeyMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.GET.get("api_key", None) != API_KEY:
            return HttpResponse('Unauthorized', status=401)
        return super().dispatch(request, *args, **kwargs)

