from django.contrib import messages
from django.http import HttpResponseRedirect
from django.views.generic import View

from events.models import Event
from imis.event_tickets import add_to_waitlist


class JoinWaitListView(View):

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        session_master_id = request.GET.get("master_id", None)
        activity = Event.objects.filter(master_id=session_master_id, publish_status="PUBLISHED").first()
        username = request.GET.get("username", None)
        if activity:
            cursor = add_to_waitlist(activity, username)

        if cursor != -1:
            messages.success(self.request, "You have been added to the waitlist.")
        else:
            messages.warning(self.request, "Could not add you to the waitlist.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
