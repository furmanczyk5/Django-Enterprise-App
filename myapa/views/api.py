import datetime
import json

from django.http import HttpResponse, JsonResponse
from django.views.generic import View
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone

import imis
from imis.event_tickets import save_activity_to_schedule, \
    cancel_activity_on_schedule, ACTIVE
from imis.models import Name
from planning.settings import API_KEY
from myapa.authentication import AuthenticationBackend
from myapa.models.auth import UserAuthorizationToken
from myapa.models import Contact
from events.models import Activity
from content.utils import generate_random_string
from content.models import Content
from cm.models import Log, Period as CMPeriod

class ApiCheckKeyMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.GET.get("api_key", None) != API_KEY:
            return HttpResponse('Unauthorized', status=401)
        return super().dispatch(request, *args, **kwargs)


class ApiSearchContactsView(ApiCheckKeyMixin, View):
    """
    returns search results from iMIS Contacts (Name records)
    based on first name, last name, email
    """

    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data())

    def get_context_data(self, *args, **kwargs):

        search_qs = self.get_search_qs(**self.request.GET)

        data = [
            dict(
                imis_id = imis_contact.id,
                first_name = imis_contact.first_name,
                last_name = imis_contact.last_name,
                designation = imis_contact.designation,
                title = imis_contact.title,
                email = imis_contact.email,
                company = imis_contact.company,
                full_address = imis_contact.full_address,
                # address1 = imis_contact.address_num_1,
                # address2 = imis_contact.address_num_2,
                # address3 = imis_contact.address_num_3,
                city = imis_contact.city,
                state_province = imis_contact.state_province,
                zip = imis_contact.zip,
                country = imis_contact.country,
                phone = imis_contact.home_phone,
                memberstatus = imis_contact.status,
                member_type = imis_contact.member_type,
            ) for imis_contact in search_qs
        ]
        return dict(success=True, data=data)

    def get_search_qs(self, **kwargs):
        return imis.models.Name.objects.filter(
            first_name__icontains=kwargs.get("first_name", [""])[0],
            last_name__icontains=kwargs.get("last_name", [""])[0],
            email__icontains=kwargs.get("email", [""])[0],
            status="A",
            company_record=False,
            ).order_by("-member_record", "last_name")[:10]

    def render_to_response(self, context):
        return JsonResponse(context)


class ApiGetContactView(ApiCheckKeyMixin, View):

    def get(self, request, *args, **kwargs):
        token = kwargs.get("token", None)
        if not token:
            return HttpResponse('Unauthorized', status=401)
        try:
            self.user = User.objects.select_related('contact').get(auth_token__key=token)
        except User.DoesNotExist:
            return HttpResponse('Unauthorized', status=401)
        self.contact = self.user.contact
        # TO DO MAYBE: remove this silent fail?
        return self.render_to_response(self.get_context_data())

    def get_context_data(self, *args, **kwargs):
        data = dict(
            imis_id = self.user.username,
            first_name = self.contact.first_name,
            last_name = self.contact.last_name,
            email = self.contact.email,
            full_name = self.contact.title,
            designation = self.contact.designation,
            member_type = self.contact.member_type,
            city = self.contact.city,
            state = self.contact.state,
            permission_groups = [g.name for g in self.user.groups.all()],
            chapter = self.contact.chapter,
            company = self.contact.company,
        )
        return dict(success=True, data=data)

    def render_to_response(self, context):
        return JsonResponse(context)

class ApiGetScheduleView(ApiCheckKeyMixin, View):
    """
    Returns complete list of items on attendee's schedule
    """

    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data())

    def get_context_data(self, *args, **kwargs):

        imis_id = kwargs.get("imis_id", [""])[0]
        contact = Contact.objects.get(user__username=imis_id)
        schedule_qs = self.get_schedule_qs(**self.request.GET)
        data = [
            dict(activities=
                [
                    {
                    "id":event.master_id,
                    "code":event.code,
                    "quantity":self.get_quantity_from_event(event),
                    "ticketed":self.get_ticketed_from_event(event)
                    } for event in self.get_events_from_schedule(schedule_qs) if event
                ]
            )
        ]
        return dict(success=True, data=data)

    def get_schedule_qs(self, **kwargs):
        """
        get my schedule queryset
        """
        return imis.models.CustomEventSchedule.objects.filter(
            id=kwargs.get("imis_id", [""])[0], status='A')

    def get_quantity_from_event(self, event):
        if getattr(event, "product", None):
            purchase = Purchase.objects.filter(
                contact=contact, content_master=event.master)
            quantity = purchase.quantity
        else:
            quantity = 1
        return quantity

    def get_ticketed_from_event(self, event):
        product = getattr(event, "product", None)
        return True if product else False

    def get_events_from_schedule(self, schedule_qs):
        the_events = []
        for sched in schedule_qs:
            code = sched_product_codce = sched.product_code
            if sched_product_codce.startswith("NPC19/"):
                code = sched_product_codce[6:]
            if code:
                event = Content.objects.filter(code=code).first()
                the_events.append(event)
        return the_events

    def render_to_response(self, context):
        return JsonResponse(context)

class ApiUpdateScheduleView(ApiCheckKeyMixin, View):
    """
    Adds or removes an activity to/from an attendee's schedule
    """
    # Docs do not specify if request will be GET or POST
    def get(self, request, *args, **kwargs):
        kwargs["imis_id"]=request.GET.get("imis_id")
        kwargs["activity_id"]=request.GET.get("activity_id")
        kwargs["method"]=request.GET.get("method")

        return self.render_to_response(self.get_context_data(
            *args, **kwargs))

    def get_context_data(self, *args, **kwargs):
        imis_id = kwargs.get("imis_id", [""])
        # master_id = kwargs.get("activity_id", [""])[0]
        cadmium_id = kwargs.get("activity_id", [""])
        method = kwargs.get("method", [""])
        contact = Contact.objects.get(user__username=imis_id)
        username = contact.user.username
        ret_val = None

        if cadmium_id:
            try:
                activity = Activity.objects.get(
                    # master_id=master_id,
                    external_key=cadmium_id,
                    publish_status="PUBLISHED",
                    product__isnull=True
                    )
            except Exception:
                activity = None
        else:
            activity = None

        data_dict = dict(activity={"activity_id":cadmium_id,})

        if activity:
            if method == 'ADD':
                ret_val = save_activity_to_schedule(activity, username, True)
                if not ret_val:
                    data_dict.update(message="Successfully updated your schedule")
                    data = [data_dict]
                    return dict(success=True, data=data)
                else:
                    data_dict.update(message="Successfully added your schedule")
                    data = [data_dict]
                    return dict(success=True, data=data)
            elif method == 'REMOVE':
                ret_val = cancel_activity_on_schedule(activity, username, True)
                if not ret_val:
                    data_dict.update(message="Successfully removed from your schedule")
                    data = [data_dict]
                    return dict(success=True, data=data)
                else:
                    data_dict.update(message="Remove failed: %s" % (ret_val))
                    data = [data_dict]
                    return dict(success=False, data=data)
            else:
                data_dict.update(message="Invalid method value (should be either 'ADD' or 'REMOVE')")
                data = [data_dict]
                return dict(success=False, data=data)
        else:
            data_dict.update(message="Not a valid Activity. E.g. cannot be ticketed.")
            data = [data_dict]
            return dict(success=False, data=data)


    def render_to_response(self, context):
        return JsonResponse(context)

class ApiLoginView(ApiCheckKeyMixin, View):
    """
    SSO Login originally for Cadmium Eventscribe mobile integration,
    but applicable to any third party needing API that authenticates
    by username and password.
    """
    def get(self, request, *args, **kwargs):

        json_response = {}

        if request.method == "GET":
            username = request.GET.get('username', '')
            password = request.GET.get('password', '')
        else:
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')

        if '@' in username:
            user = User.objects.filter(email__iexact=username).first()
            username = user.username if user else None

        user = authenticate(username=username, password=password)

        if user is not None:

            login(request, user)

            token_object = UserAuthorizationToken.objects.filter(user=user).first()
            # UserAuthorizationToken.objects.filter(user=user).delete()
            if not token_object:
                token_object = UserAuthorizationToken(user=user, token=generate_random_string(20))
                token_object.save()

            contact = Contact.objects.filter(user__username=username).first()
            imis_contact = Name.objects.values("member_status").filter(id=username).first()

            if contact and imis_contact:

                json_response["data"] = {
                    "imis_id": user.username,
                    "permission_groups":[g.name for g in contact.user.groups.all()],
                    "first_name":contact.first_name,
                    "middle_name":contact.middle_name,
                    "last_name":contact.last_name,
                    "city":contact.city,
                    "state":contact.state,
                    "country":contact.country,
                    "cell_phone":contact.cell_phone,
                    "work_phone":contact.phone,
                    "email":contact.email,
                    "member_type":contact.member_type,
                    "chapter":contact.chapter,
                    "designation":contact.designation,
                    "full_name":contact.full_title(),
                    "position_title":contact.job_title,
                    "company":contact.company,
                    "token": token_object.token
                }

                json_response["success"] = True
            else:
                logout(request)
                json_response["message"] = "At least one database is missing a user for the given id"
                json_response["success"] = False
        else:
            json_response["success"] = False
            json_response["message"] = "username and password did not match"
        # Bring this back if we only alLow POST
        # else:
        #     json_response["success"] = False
        #     json_response["message"] = "bad request"

        return HttpResponse(json.dumps(json_response), content_type='application/json')


class MobileSsoView(View):
    """
    SSO originally for Cadmium Eventscribe mobile integration,
    but applicable to any mobile to browser situation that authenticates
    by token and redirects.
    """
    def get(self, request, *args, **kwargs):

        username = None

        # tokens are not unique? need username passed?
        if request.method == "GET":
            token = request.GET.get('token', '')
            remember_me = request.GET.get("remember_me", "off")
            next_url = request.GET.get("next", None)
        else:
            token = request.POST.get('token', '')
            # username = request.POST.get('username', '')
            remember_me = request.POST.get("remember_me", "off")
            next_url = request.POST.get("next", None)

        uat = UserAuthorizationToken.objects.filter(
                # user__username=username,
                token=token)
        if uat.count() == 1:
            uat = uat.first()
        else:
            uat = None

        if uat:
            username = str(uat.user.username).zfill(6)

        if username is not None:
            user = AuthenticationBackend.authenticate(
                self=request,
                username=username,
                auto=True
            )

            login(request, user)

            response = redirect(next_url or '/myapa/')
            response.set_cookie("groups_updated", value="TRUE")

            if remember_me == "on":
                request.session.set_expiry(15552000)
            else:
                request.session.set_expiry(0)

            return response
        else:
            messages.error(request, "No single username associated with logged in user.")
            return redirect('/login/')

# SHOULD WE REQUIRE THEM TO USE OUR API KEY??**
# Then we could just use the ApiLoginView
class HigherLogicApiLoginView(ApiCheckKeyMixin, View):
    """
    SSO Login Higher Logic MemberCentric mobile integration,
    authenticating by username and password, but using their
    own "security key" -- not our API_KEY
    """

    # If we must use Higher Logic security key, use this instead of ApiCheckKeyMixin:
    # def dispatch(self, request, *args, **kwargs):
    #     if request.GET.get("securityKey", None) != HIGHER_LOGIC_SECURITY_KEY:
    #         return HttpResponse('Unauthorized', status=401)
    #     return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):

        json_response = {}

        if request.method == "GET":
            username = request.GET.get('username', '')
            password = request.GET.get('password', '')
        else:
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')

        if '@' in username:
            user = User.objects.filter(email__iexact=username).first()
            username = user.username

        user = authenticate(username=username, password=password)

        if user is not None:

            login(request, user)

            contact = Contact.objects.filter(user__username=username).first()
            imis_contact = Name.objects.values("member_status").filter(id=username).first()

            if contact and imis_contact:
                json_response["imis_id"] = user.username
                json_response["success"] = True
            else:
                logout(request)
                json_response["success"] = False
                json_response["message"] = "At least one database is missing a user for the given id"
        else:
            json_response["success"] = False
            json_response["message"] = "username and password did not match"

        return HttpResponse(json.dumps(json_response), content_type='application/json')


class ApiCMTrackerCreateView(ApiCheckKeyMixin, View):
    """
    Endpoint for Open Water to use to create a CM tracker in Django when an AICP Candidate
    enrolls on the Open Water side.
    """
    success = False
    message = ""

    def get(self, request, *args, **kwargs):
        username = request.GET.get('username', '')
        contact = Contact.objects.filter(user__username=username).first()
        if contact:
            tracker_created = self.create_cm_tracker(contact)
            if tracker_created is not None:
                self.success = True
                if tracker_created:
                    self.message = "CM Tracker successfully created."
                else:
                    self.message = "CM Tracker already exists."
            else:
                self.success = False
                self.message = "Unable to create CM Tracker."
        else:
            self.success = False
            self.message = "User not found in our system."
        return self.render_to_response(self.get_context_data(**dict(kwargs, username=username)))

    def create_cm_tracker(self, contact):
        now = timezone.now()
        five_years = datetime.timedelta(days=365 * 5)
        period = CMPeriod.objects.get(code="CAND")
        log, created = Log.objects.get_or_create(
            contact=contact, period=period, status='A', is_current=True,
        )
        if created:
            log.credits_required = 16
            log.law_credits_required = 1.5
            log.ethics_credits_required = 1.5
            log.begin_time = now
            log.end_time = now + five_years
            log.save()
        if log:
            return created
        else:
            return None

    def get_context_data(self, *args, **kwargs):
        data = [dict(imis_id=kwargs.get("username", None), message=self.message)]
        return dict(success=self.success, data=data)

    def render_to_response(self, context):
        return JsonResponse(context)
