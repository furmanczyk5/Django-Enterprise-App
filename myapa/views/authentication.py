import hashlib
import json
import urllib
import xml.etree.ElementTree as ET

import jwt
import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.views import password_reset
from django.core import serializers
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, View, TemplateView
from rest_framework.authtoken.models import Token

from cm.models.claims import Log, Period as CMPeriod
from component_sites.viewmixins import ComponentSitesNavMixin
from content.utils import generate_random_string
from content.views.render_content import REGISTRATION_LOGIN_GROUPS
from exam.models import ExamRegistration
from imis.models import Name, NameAddress
from learn.utils.wcw_api_utils import WCWContactSync
from myapa.authentication import AuthenticationBackend
from myapa.forms import PasswordResetSendEmailForm
from myapa.models.auth import UserAuthorizationToken
from myapa.models.contact import Contact
from myapa.utils import is_authenticated_check_all, has_webgroup
from myapa.viewmixins import AuthenticateLoginMixin, AuthenticateMemberMixin
from planning.settings import (BLUE_TOAD_USERNAME, BLUE_TOAD_PASSWORD,
                               LEARN_DOMAIN, SBS_SECRET_KEY,
                               SURVEY_BALLOT_SYSTEMS_ADDRESS,
                               # OPEN_WATER_SECRET_KEY,
                               OPEN_WATER_SECRET_KEYS)
from store.models import Product

# import logging
# logger = logging.getLogger(__name__)


MEMBER_GROUPS = ["member", "nonmember"]

SESSION_EXPIRE_TIME = 60 * 60 * 24 * 14  # 14 days


class UserLogin(FormView):
    """ View For logging into the website """
    template_name = 'myapa/newtheme/login.html'
    form_class = AuthenticationForm
    next_url = None

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        posted_data = request.POST
        user = authenticate(username=posted_data.get("username"), password=posted_data.get("password"))
        return_url = request.GET.get('return_url', '')
        next_url = self.next_url or request.GET.get("next", return_url)

        if user is not None:
            login(request, user)
            if next_url:
                response = redirect(next_url)
            else:
                response = redirect('/myapa/')
            response.set_cookie("groups_updated", value="TRUE")
            if request.POST.get("remember_me", "off") == "on":
                request.session.set_expiry(SESSION_EXPIRE_TIME)
                sso_max_age = SESSION_EXPIRE_TIME
            else:
                request.session.set_expiry(0)
                sso_max_age = None
            response.set_cookie(
                "sso_id",
                value=user.username,
                max_age=sso_max_age,
                domain="planning.org",
                secure=True
            )
            return response
        else:
            messages.error(request, "Your username and password didn't match. Please try again.")

            # Ensure redirect persists after unsuccessful login attempt
            if next_url:
                return redirect("/login/?next={}".format(next_url or ''))

            return redirect('/login/')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["encoded_next"] = self.get_encoded_next_url()
        return context

    def get_encoded_next_url(self):
        next_url = self.request.GET.get("next", None)
        return urllib.parse.quote(urllib.parse.unquote(next_url)) if next_url else None


class ResetPasswordView(FormView):
    """ View for requesting reset of password by email """

    form_class = PasswordResetSendEmailForm
    template_name = "myapa/newtheme/password/reset-form.html"
    email_template_name = "myapa/newtheme/password/reset-email.html"
    post_reset_redirect = "password_reset_done"
    from_email = "customerservice@planning.org"

    def form_valid(self, form):
        email = form.cleaned_data.get("email")
        name = Name.objects.filter(email=email).first()
        if name is not None:
            Contact.update_or_create_from_imis(name.id)

            user = User.objects.get(username=name.id)
            if not user.has_usable_password():
                user.set_password(generate_random_string(20))
                user.save()

            return password_reset(
                self.request,
                template_name=self.template_name,
                email_template_name=self.email_template_name,
                post_reset_redirect=self.post_reset_redirect,
                from_email=self.from_email
            )
        else:
            self.display_errors = ["The email address entered is not in APA’s database. Please try again."]
            return self.form_invalid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["display_errors"] = getattr(self, "display_errors", [])
        return context


class AutoLoginViaMobile(FormView):
    """ View for logging into browser using user_id and token combination,
            Useful for logging into webviews and mobile browser when coming from the app"""

    template_name = 'myapa/newtheme/login.html'
    form_class = AuthenticationForm

    def dispatch(self, request, *args, **kwargs):

        if request.method == "GET":
            auth_login = request.GET.get('auth_login', '') == "true"
            next_url = request.GET.get("next", None)
            user_id = request.GET.get("auth_user_id", None)
        else:
            auth_login = request.POST.get('auth_login', '') == "true"
            next_url = request.POST.get("next", None)
            user_id = request.POST.get("auth_user_id", None)

        response = redirect(next_url or '/myapa/')

        if auth_login:
            is_logged_in = request.user.username
            current_user_logged_in = request.user.username == user_id

            if user_id and not current_user_logged_in:

                is_authenticated, authenticated_username = is_authenticated_check_all(request)

                if is_authenticated:

                    user = AuthenticationBackend.authenticate(
                        self=request,
                        username=authenticated_username,
                        auto=True
                    )

                    login(request, user)

                    response.set_cookie("groups_updated", value="TRUE")
                    if request.POST.get("remember_me", "off") == "on":
                        request.session.set_expiry(SESSION_EXPIRE_TIME)
                    else:
                        request.session.set_expiry(0)
                else:
                    logout(request)

            elif is_logged_in and not user_id:
                # log out if no user_id is sent
                logout(request)

        return response


def login_as_user(request, *args, **kwargs):
    """
    allows staff to auto login as another user
    """

    username = kwargs.get("username", request.user.username)

    response = redirect("/myapa/")

    if has_webgroup(
            user=request.user,
            required_webgroups=['staff', 'staff-aicp', 'staff-membership']
    ) or request.user.is_superuser:

        user = AuthenticationBackend.authenticate(self=request, username=username, auto=True)

        login(request, user)

    else:
        response = HttpResponseForbidden("You are not authorized to view this page.")
    return response


@csrf_exempt
def login_mobile(request, *args, **kwargs):
    """
    logs in mobile app user by creating and returning a token for them (tokens are not unique so you still need to pass username after login)
        Used by conference mobile app api 0.0 - current (0.2)
    """

    json_response = {}

    if request.method == "POST":

        username = request.POST.get('username', '')
        password = request.POST.get('password', '')

        user = authenticate(username=username, password=password)

        if user is not None:

            # delete all tokens for that user (not sure we want to do this, but want to have mechanism to clean up unused tokens)
            UserAuthorizationToken.objects.filter(user=user).delete()

            # create new token for user
            new_token = UserAuthorizationToken(user=user, token=generate_random_string(20))
            new_token.save()

            # return username and token
            json_response["success"] = True
            json_response["data"] = {
                "user_id": user.username,

                "token": new_token.token
            }

        else:
            json_response["success"] = False
            json_response["message"] = "username and password did not match"

    else:
        json_response["success"] = False
        json_response["message"] = "bad request"

    return HttpResponse(json.dumps(json_response), content_type='application/json')


@csrf_exempt
def logout_mobile(request, *args, **kwargs):
    """
    logs out mobile app user by deleting all of their tokens (logs them out everywhere)
        Used by conference mobile app api 0.0 - current (0.2)
    """

    json_response = {}

    if request.method == "POST":

        username = request.POST.get('user_id', '')

        # delete all tokens for that user, logout user everywhere!!! (not sure we want to do this, but want to have mechanism to clean up unused tokens)
        UserAuthorizationToken.objects.filter(user__username=username).delete()
        json_response["success"] = True

    else:
        json_response["success"] = False
        json_response["message"] = "bad request"

    return JsonResponse(json_response)


# DOES THIS BELONG HERE?
@csrf_exempt
def get_contact_mobile(request, *args, **kwargs):
    """
    returns contact info to user if passed token exists for username
        Used by conference mobile app api 0.0 - current (0.2)
    """

    json_response = {}

    if request.method == "GET":

        is_authenticated, username = is_authenticated_check_all(request)

        if is_authenticated:

            try:
                contact = Contact.objects.get(user__username=username)
                user = User.objects.get(username=username)
                json_response["success"] = True
                json_response["contact"] = serializers.serialize("python", [contact])[0]
                json_response["contact"]["web_groups"] = [group.name for group in user.groups.all()]

            except:
                json_response["success"] = False
                json_response["message"] = "token exists, but something went wrong"
        else:
            json_response["success"] = False
            json_response["message"] = "Token does not exist"
            json_response["action"] = "LOGOUT"
    else:
        json_response["success"] = False
        json_response["message"] = "request must be GET"

    return JsonResponse(json_response)


@csrf_exempt
def overdrive_access(request):
    """
    HTTP authentication for access to OverDrive digital library...
    example URL:
    http://[YourServerName]/[YourPath]?LibraryCard=20000000000000&PIN=1234
    The LibraryCard will be username and PIN will be password
    actual URL:
    https://www.planning.org/api/0.2/overdrive/authenticate/?username=336371&password=driveoverm3
    """
    username = request.GET.get('username', '')
    password = request.GET.get('password', '')

    if "username" in request.GET and "password" in request.GET:
        this_user = authenticate(username=username, password=password)

        if this_user is not None:
            if this_user.groups.filter(name="planning").exists():
                # json_response["success"] = True
                xml = '<?xml version="1.0"?>\
                    <AuthorizeResponse>\
                    <Status>1</Status>\
                        </AuthorizeResponse>'
            else:
                xml = '<?xml version="1.0"?>\
                    <AuthorizeResponse>\
                    <Status>0</Status>\
                    <ErrorDetails>We’re sorry, you must be an APA member to continue.</ErrorDetails>\
                    </AuthorizeResponse>'

        else:
            xml = '<?xml version="1.0"?>\
                <AuthorizeResponse>\
                <Status>0</Status>\
                <ErrorDetails>Your username and password did not match. Please try again.</ErrorDetails>\
                </AuthorizeResponse>'
    else:
        xml = '<?xml version="1.0"?>\
            <AuthorizeResponse>\
            <Status>0</Status>\
            <ErrorDetails>Username and password required.</ErrorDetails>\
            </AuthorizeResponse>'

    return HttpResponse(xml, content_type='text/xml')


@csrf_exempt
def planning_mag_access(request):
    """
    tests for access to planning magazine... used by api for BlueToad
    """
    json_response = {"success": False}

    if "username" in request.POST and "password" in request.POST:
        this_user = authenticate(
            username=request.POST["username"],
            password=request.POST["password"]
        )

        if this_user is not None:
            if this_user.groups.filter(name="planning").exists():
                json_response["success"] = True

                # code here to add/update user info
                planning_mag_create_user(this_user)
            else:
                json_response["message"] = "No access to planning magazine."
        else:
            json_response["message"] = "Incorrect username or password."
    else:
        json_response["message"] = "Username and password required."

    return JsonResponse(json_response)


def planning_mag_create_user(user):
    """
    creates/updates blue toad user record
    """

    url = "http://magazine.planning.org/xml/subscription_import/"

    root = ET.Element(
        'subscription_import',
        attrib={
            'user': BLUE_TOAD_USERNAME,
            'pass': BLUE_TOAD_PASSWORD,
            'method': 'insert',
            'subscription_id': '12707'
        }
    )

    subscriber = ET.SubElement(root, 'subscriber')
    email = ET.SubElement(subscriber, 'email')
    email.text = user.contact.email
    issue_id = ET.SubElement(subscriber, 'issue_id')
    issue_id.text = '294733'
    host = ET.SubElement(subscriber, 'host')
    host.text = 'magazine.planning.org'
    expiration = ET.SubElement(subscriber, 'expiration')
    expiration.text = '0000-00-00'
    body = ET.tostring(root)
    r = requests.post(url=url, data=body)

    return r


class ComponentUserLogin(ComponentSitesNavMixin, UserLogin):
    template_name = "component-sites/component-theme/templates/login.html"

    def post(self, request, *args, **kwargs):
        posted_data = request.POST
        user = authenticate(
            username=posted_data.get("username"),
            password=posted_data.get("password")
        )
        if user is not None:
            login(request, user)
            next_url = request.GET.get("next", None)
            if next_url:
                response = redirect(next_url)
            else:
                # redirect to component site home instead of /myapa
                response = redirect('/')
            response.set_cookie("groups_updated", value="TRUE")
            if request.POST.get("remember_me", "off") == "on":
                request.session.set_expiry(SESSION_EXPIRE_TIME)
                return response
            else:
                request.session.set_expiry(0)
                return response
        else:
            messages.error(request, "Your username and password didn't match. Please try again.")
            return redirect('/login/')


# TO DO: these SSO views could all inherit from a Base SSO view / mixin to make it cleaner
class ProposalsSsoView(AuthenticateLoginMixin, View):
    login_redirect_url = reverse_lazy("npcproposals_login")

    def get_token(self):
        return self.request.user.username

    def get(self, request, *args, **kwargs):
        return_url = request.GET.get("return_url", '').lstrip()

        # decode encoded return url
        decoded_url = urllib.parse.unquote(return_url)

        # parse parts of url
        parse_result = urllib.parse.urlparse(decoded_url)

        # add token to return url querystring
        query_dict = dict(urllib.parse.parse_qsl(parse_result.query))
        query_dict["token"] = self.get_token()
        parse_result_list = list(parse_result)
        parse_result_list[4] = urllib.parse.urlencode(query_dict)

        # reformat to url
        redirect_url = urllib.parse.urlunparse(parse_result_list)

        return redirect(redirect_url)


class LearnSsoView(AuthenticateLoginMixin, View):

    show_message_text = False
    # login_redirect_url = reverse_lazy('learn_sso')  # This borked staging pretty good
    redirect_field_name = "return_url"

    def get_token(self):
        token, created = Token.objects.get_or_create(user=self.request.user)
        return token.key

    def get(self, request, *args, **kwargs):
        return_path = request.GET.get("return_path", "/login/")

        return_url = request.GET.get("return_url", "https://" + LEARN_DOMAIN + return_path)

        # decode encoded return url
        decoded_url = urllib.parse.unquote(return_url)

        # parse parts of url
        parse_result = urllib.parse.urlparse(decoded_url)

        # add token to return url querystring
        query_dict = dict(urllib.parse.parse_qsl(parse_result.query))
        query_dict["token"] = self.get_token()
        parse_result_list = list(parse_result)
        parse_result_list[4] = urllib.parse.urlencode(query_dict)

        # reformat to url
        redirect_url = urllib.parse.urlunparse(parse_result_list)

        return redirect(redirect_url)


class ProposalsSsoUserDataView(View):
    api_key = "cab139df-4b9f-4451-9ad2-7d2be3c11c4d"

    @staticmethod
    def _has_current_npc_webgroup(user_groups):
        current_npc_webgroup = REGISTRATION_LOGIN_GROUPS[-1]
        return next(
            (True for g in user_groups if g.name == current_npc_webgroup),
            False
        )

    def get(self, request, *args, **kwargs):

        encoded_key = request.GET.get("key", "")
        encoded_username = request.GET.get("token", "")
        username = urllib.parse.unquote(encoded_username)

        response_context = dict()

        if urllib.parse.unquote(encoded_key) == self.api_key:

            contact = Contact.objects.filter(user__username=username).first()
            imis_contact = Name.objects.values("member_status").filter(id=username).first()

            if contact and imis_contact:

                divisions = []
                subs = contact.get_imis_subscriptions()
                for s in subs:
                    if s.prod_type == "SEC" and s.status == "A":
                        product_code = s.product_code
                        product = Product.objects.filter(
                            imis_code=product_code).first()
                        if product:
                            product_title=product.content.title
                            current_dict = dict(
                                division_title=product_title,
                                division_code=product_code)
                            divisions.append(current_dict)

                user_groups = contact.user.groups.all() if contact.user else None
                registered = self._has_current_npc_webgroup(user_groups)

                data = dict(
                    first_name=contact.first_name,
                    middle_name=contact.middle_name,
                    last_name=contact.last_name,
                    credentials=contact.designation,
                    organization=contact.company,
                    title=contact.job_title,
                    address1=contact.address1,
                    address2=contact.address2,
                    city=contact.city,
                    state=contact.state,
                    zip=contact.zip_code,
                    country=contact.country,
                    member_status=imis_contact.get("member_status"),
                    member_type=contact.member_type,
                    member_id=username,
                    email=contact.email,
                    bio=contact.bio,
                    divisions=divisions,
                    registered=registered
                )

                response_context["data"] = data
                response_context["success"] = True
            else:
                response_context["message"] = "No User found for the given token"
                response_context["success"] = False
        else:
            response_context["message"] = "You do not have access to view this page"
            response_context["success"] = False

        return JsonResponse(response_context)


class ProposalsSsoLoginView(UserLogin):
    template_name = 'myapa/newtheme/authentication/npc-proposals/login.html'


class EngageSsoLoginView(UserLogin):
    def post(self, request, *args, **kwargs):
        self.next_url = request.GET.get("ReturnURL", "https://engage.planning.org/")
        return super().post(request, *args, **kwargs)


class SurveyBallotSystemsRedirectView(AuthenticateMemberMixin, TemplateView):
    """
    member clicks Voting link button on our site, they are sent to this page
    that has a "Vote Now" button. On clicking that button a token is generated
    and a form is posted to Survey and Ballot Systems to accomplish the SSO. The
     user is then able to vote for board members (every two years).
    """
    template_name = "myapa/newtheme/authentication/sbs-voting/vote.html"

    def generate_token(self, username):
        try:
            bytes_data = (username + SBS_SECRET_KEY).encode()
            encrypted_token = hashlib.sha384(bytes_data).hexdigest().upper()
            return encrypted_token
        except Exception as e:
            print(str(e))

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["action_url"] = SURVEY_BALLOT_SYSTEMS_ADDRESS
        username = self.request.user.username
        context["username"] = username
        context["token"] = self.generate_token(username)
        return context


class OpenWaterSsoLoginView(AuthenticateLoginMixin, View):
    def get(self, request, *args, **kwargs):
        # returnUrl will be a querystring parameter from Open Water
        returnUrl = request.GET.get("returnUrl")
        response = HttpResponseRedirect("/openwater/sso/")
        response.set_cookie("returnUrl", value=returnUrl)
        # msg = 'Get Return URL values from Open Water'
        # getattr(logger, "info")(msg, exc_info=True, extra={
        #     "data": {
        #         "request": request,
        #         "returnUrl": returnUrl,
        #     },
        # })

        return response


class OpenWaterSsoLoginPart2View(View):
    """
    After user logs in they are redirected here to generate
    the json web token and redirect them back to open water.
    """
    open_water_instance = None

    def get(self, request, *args, **kwargs):
        returnUrl = request.COOKIES.get('returnUrl')
        self.open_water_instance = self.get_open_water_instance(returnUrl)
        if self.open_water_instance:
            instance_secret_key = OPEN_WATER_SECRET_KEYS[self.open_water_instance]
        else:
            instance_secret_key = "None"

        username = request.user.username
        contact = Contact.objects.get(user__username=username)
        name = Name.objects.get(id=username)
        where = NameAddress.objects.filter(
            id=username
            ).exclude(Q(address_1='') & Q(address_2='')).first()
        salutation = suffix = phone = title = designation = chapter = ''
        member_info = 'NOM'
        exam_pass = aicp_candidate = user_is_member = False
        who = None

        if name:
            salutation = name.prefix
            suffix = name.suffix
            phone = name.work_phone or name.mobile_phone or name.home_phone
            title = name.title
            user_is_member = name.member_type is "MEM"
            member_info = name.member_type
            designation = name.designation
            chapter = name.chapter
            who = name

        if contact:
            salutation = salutation or contact.prefix_name
            suffix = suffix or contact.suffix_name
            phone = phone or contact.phone or contact.cell_phone
            title = title or contact.job_title
            user_is_member = user_is_member or contact.user.groups.filter(name='member').exists()
            mem_grp = contact.user.groups.filter(
                name__in=MEMBER_GROUPS).first()
            member_info = member_info or (mem_grp.name if mem_grp else 'NOM')
            aicp_candidate = contact.user.groups.filter(name='candidate-cm').exists()
            designation = designation or contact.designation
            chapter = chapter or contact.chapter
            exam_pass = ExamRegistration.objects.filter(contact=contact, is_pass=True).exists()
            who = who or contact
            cm_tracker_completed = self.is_cm_tracker_completed(contact)
        else:
            cm_tracker_completed = False

        if where:
            address = self.create_ow_address_imis(where)
        else:
            address = self.create_ow_address_django(contact)

        # if not name or not where:
        #     who = contact
        #     salutation = who.prefix_name
        #     suffix = who.suffix_name
        #     phone = who.phone or who.cell_phone
        #     title = who.job_title
        #     address = self.create_ow_address_django(who)
        # else:
        #     who = name
        #     salutation = who.prefix
        #     suffix = who.suffix
        #     phone = who.work_phone or who.mobile_phone or who.home_phone
        #     title = who.title
        #     address = self.create_ow_address_imis(where)
        #
        # user_is_member = who.member_type is "MEM" or \
        #                  contact.user.groups.filter(name='member'
        #                                             ).exists()

        # if there is no contact then there will be no member group -- then open water defaults them to Free (no fee)
        # if contact:
        #     mem_grp = contact.user.groups.filter(
        #         name__in=MEMBER_GROUPS).first()
        #     member_info = mem_grp.name if mem_grp else ''
        # else:
        #     member_info = who.member_type

        custom_data = [username, salutation, suffix, phone, designation, chapter,
                       cm_tracker_completed, aicp_candidate, exam_pass]

        user_profile = {
            'APAID': username,
            'TimestampUtc': timezone.now().__str__(),
            'UserIsMember': user_is_member,
            'ThirdPartyUniqueId': username,
            'JobTitle': title,
            'Suffix': suffix,
            'FirstName': getattr(who, "first_name", ""),
            'UserData': member_info,
            'Salutation': salutation,
            'UserNameExists': True if username else False,
            'LastName': getattr(who, "last_name", ""),
            'UserValidatedSuccessfully': True,
            'Company': getattr(who, "company", ""),
            'PrimaryAddress': address,
            'ProfileTextFieldData': self.get_custom_profile_fields(custom_data),
            'Email': getattr(who, "email", ""),
            'Phone': phone,
            # 'UserIsAICPCandidate': aicp_candidate,
            # 'Designation': designation,
            # 'UserPassedExam': exam_pass,
            # 'ChapterCode': getattr(who, "chapter", ""),
            # 'CMTrackerCompleted': cm_tracker_completed
        }

        # Plan B: Make 2 copies of View 1. Do all this in view 1, put the redirect_url in a cookie
        # secret_key = OPEN_WATER_SECRET_KEY
        secret_key = instance_secret_key
        token = jwt.encode(user_profile, secret_key, algorithm='HS256').decode('utf-8')

        if returnUrl.find('?') >= 0:
            param_char = '&'
        else:
            param_char = '?'
        # print("REDIRECT URL ..........................................")
        # print("{}{}token={}".format(returnUrl, param_char, token))
        return HttpResponseRedirect("{}{}token={}".format(
            returnUrl, param_char, token))

    def create_ow_address_django(self, contact):
        open_water_address = {
            "Line1": getattr(contact,"address1",""),
            "Line2": getattr(contact,"address2",""),
            "City": getattr(contact,"city",""),
            "StateProvinceAbbreviationOrName": getattr(contact,"state",""),
            "ZipPostalCode": getattr(contact,"zip_code",""),
            "CountryAbbreviationOrName": getattr(contact,"country","")
        }
        return open_water_address

    def create_ow_address_imis(self, address):
        open_water_address = {
            "Line1": getattr(address,"address_1",""),
            "Line2": getattr(address,"address_2",""),
            "City": getattr(address,"city",""),
            "StateProvinceAbbreviationOrName": getattr(address,"state_province",""),
            "ZipPostalCode": getattr(address,"zip",""),
            "CountryAbbreviationOrName": getattr(address,"country","")
        }
        return open_water_address

    def get_custom_profile_fields(self, custom_data):
        """
        Pass an ordered argument list of custom field data
        0: username
        :return: dict of Open Water custom field data
        """
        if self.open_water_instance == "awards_instance":
            APAID_guid = "40709ef4-c38c-4a77-a42a-e5e80aa93317"
            Prefix_guid = "6551aef4-c628-4c8e-8402-d5a8e4b0fc22"
            Suffix_guid = "21d37f12-c484-41bb-85da-0570a512c028"
            Phone_guid = "d784d155-453d-45ed-8631-915a7d5d2881"
            Designation_guid = "e7f6618d-7881-4705-a92e-47885123af11"
            Chapter_guid = "ccc42e7e-de89-40ee-92a6-389f9775f21f"
            CMTrackerCompleted_guid = "56c9b021-12d3-4baa-9d23-5fc1c11baee0"
            aicp_candidate_guid = "b4606dc7-f641-47ca-b8e4-27aeebd85fb7"
            exam_pass_guid = "5118d18c-726d-4963-890d-a9c8bf375306"
        elif self.open_water_instance == "aicp_instance":
            APAID_guid = "7725ad4e-d6f2-4f6b-8590-b91de97c8f42"
            Prefix_guid = "f4d0ea4d-24f9-443b-ba26-dd6254005ac6"
            Suffix_guid = "72272a0f-3bdb-404c-9855-91c2225e1a46"
            Phone_guid = "5dd0517e-ff37-4667-9397-ac3d8208d392"
            Designation_guid = "4e2ce92e-1426-453c-8694-4c5969462199"
            Chapter_guid = "289e002e-104d-4079-aa84-a6d76bba6bba"
            CMTrackerCompleted_guid = "79d19cd3-4117-485d-b39d-d948fab6a56f"
            aicp_candidate_guid = "4ee67152-7b36-4aca-82c1-eb2f6e568431"
            exam_pass_guid = "7b1c85ce-8b9b-4a37-8832-05ed7693f0d7"
        elif self.open_water_instance == "test_instance":
            APAID_guid = "b23ccd67-5673-4ca2-b7c1-0c6de213ecf7"
            Prefix_guid = "40fbe48b-2f44-4536-be33-6519703bdb00"
            Suffix_guid = "e63614c7-463a-4e47-9714-9db9d2af2062"
            Phone_guid = "6c0796dc-4a40-4564-933d-4fc4d2aa5226"
            Designation_guid = "0ee96899-c236-4367-8be5-16ebb7b8b5fa"
            Chapter_guid = "bfa08c5b-4567-4473-a837-e75c399a3d37"
            CMTrackerCompleted_guid = "95c0f203-e3f2-4312-99bd-f789afa0847a"
            aicp_candidate_guid = "17a87462-fd31-4cee-b71e-45f31a1b055f"
            exam_pass_guid = "94e15558-6dd9-417d-b08f-96f8261bee87"
        else:
            APAID_guid = "apaid-guid-no-open-water-instance-found"
            Prefix_guid = "prefix-guid-no-open-water-instance-found"
            Suffix_guid = "suffix-guid-no-open-water-instance-found"
            Phone_guid = "phone-guid-no-open-water-instance-found"
            Designation_guid = "designation-guid-no-open-water-instance-found"
            Chapter_guid = "chapter-guid-no-open-water-instance-found"
            CMTrackerCompleted_guid = "cmtrackercompleted-guid-no-open-water-instance-found"
            aicp_candidate_guid = "aicpcandidate-guid-no-open-water-instance-found"
            exam_pass_guid = "exampass-guid-no-open-water-instance-found"
        custom_fields = {
            APAID_guid: custom_data[0],
            Prefix_guid: custom_data[1],
            Suffix_guid: custom_data[2],
            Phone_guid: custom_data[3],
            Designation_guid: custom_data[4],
            Chapter_guid: custom_data[5],
            CMTrackerCompleted_guid: custom_data[6],
            aicp_candidate_guid: custom_data[7],
            exam_pass_guid: custom_data[8]
        }
        return custom_fields

    def is_cm_tracker_completed(self, contact):
        period = CMPeriod.objects.filter(code='CAND')
        cand_log = Log.objects.filter(contact=contact, period=period).first()
        if cand_log is not None:
            credits_overview = cand_log.credits_overview()
            if cand_log \
                    and credits_overview['general_needed'] <= 0 \
                    and credits_overview['ethics_needed'] <= 0 \
                    and credits_overview['law_needed'] <= 0:
                return True
            else:
                return False
        else:
            return False

    def get_open_water_instance(self, returnUrl):
        if returnUrl.find("planning") >= 0:
            return "awards_instance"
        elif returnUrl.find("aicp") >= 0:
            return "aicp_instance"
        elif returnUrl.find("test") >= 0:
            return "test_instance"
        else:
            return None
