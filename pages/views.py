import json
import datetime

from django.utils import timezone

from django.views.generic import View
from django.http import HttpResponse

from myapa.models.contact import Contact
from myapa.viewmixins import AuthenticateLoginMixin

from content.models import Content

CHECKIN_DURATION_MINUTES = 2


class AdminPageCheckinView(AuthenticateLoginMixin, View):

    def get(self, request, *args, **kwargs):

        content_id = kwargs.get("content_id")
        checkin = kwargs.get("action") == "checkin"

        datetime_now = timezone.now()
        checkin_cutoff_time = datetime_now - datetime.timedelta(minutes=CHECKIN_DURATION_MINUTES)

        # page_query = Page.objects.filter(id=content_id) # This was when we assumed checkin was only for pages
        page_query = Content.objects.filter(id=content_id) # IMPORTANT: Dont save directly as Content, use either update or get appropriate class
        username = request.user.username

        if checkin:

            other_user_checked_in = page_query.exclude(checkin_username=username).filter(checkin_time__gt=checkin_cutoff_time).exists()

            if not other_user_checked_in:
                page_query.update(checkin_username=username, checkin_time=datetime_now)
                context = dict(success=True, action="checkin")
            else:
                checked_in_contact = Contact.objects.filter(user__username=page_query.first().checkin_username).first()
                context = dict(success=False, action="checkout",
                    message="""{0} is currently checked into this page. Close the window and check back in later, after {0} has checked out of the page.""".format(checked_in_contact.title))

        else: #checkout
            page_query.filter(checkin_username=username).update(checkin_username=None, checkin_time=None)
            context = dict(success=True, action="checkout")

        return HttpResponse(json.dumps(context), content_type='application/json')
