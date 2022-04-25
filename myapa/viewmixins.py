from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import render

from content.models import MessageText
from imis.models import Subscriptions
from .models import ContactRole, Contact, ContactRelationship
from .utils import is_authenticated_check_all

MEMBER_LOGIN_GROUPS = ['member', 'planning']
AICP_LOGIN_GROUPS = ['aicpmember']
CM_LOGIN_GROUPS = ['aicp_cm']
SUBSCRIBER_LOGIN_GROUPS = ['PAS', 'ZONING', 'JAPA']
REGISTRATION_LOGIN_GROUPS = ['16CONF']
DIVISION_LOGIN_GROUPS = ["CITY_PLAN", "LAP", "SMALL_TOWN", "TRANS",
                         "URBAN_DES", "WOMEN", "LAW", "NEW_URB", "PLAN_BLACK",
                         "PRIVATE", "SCD", "CPD", "ECON", "FED_PLAN", "GALIP",
                         "HMDR", "HOUSING", "INFO_TECH", "INTER_GOV", "INTL",
                         "ENVIRON"]
CHAPTER_LOGIN_GROUPS = ["chapter", "CHAPT_AK", "CHAPT_KS", "CHAPT_MD",
                        "CHAPT_NV", "CHAPT_VA"]


class AuthenticateLoginMixin(object):
    """
    Will redirect to login if user is not logged in,
    Include as left-most mixin if want to call before anything else

    MOVE TO: myapa views?
    """

    show_message_text = True  # Whether or not to show a flash message
    prompt_login = True  # set this to False on views that don't require login to function
    login_redirect_url = "/login/"  # Where the user is redirected if they are not logged in
    redirect_field_name = "next"

    def authenticate(self, request, *args, **kwargs):
        """
        Checks if user is authenticated

        When inheriting, be sure to follow the return rules...
            - Return None if user is authenticated, return some form of HttpResponse if not.
            - Call super first (root ancestor login should go first)
        """

        self.is_authenticated, self.username = is_authenticated_check_all(request)

        if self.prompt_login and not self.is_authenticated:
            if self.show_message_text:
                msg = MessageText.objects.filter(code='LOGIN_REDIRECT').first()
                messages.warning(request, getattr(msg, "text", "Login to continue"))
            return redirect_to_login(
                request.get_full_path(),
                login_url=self.login_redirect_url,
                redirect_field_name=self.redirect_field_name
            )
        else:
            return None

    def dispatch(self, request, *args, **kwargs):

        authentication_response = self.authenticate(request, *args, **kwargs)

        if authentication_response is not None:
            return authentication_response
        else:
            return super().dispatch(request, *args, **kwargs)


class AuthenticateWebUserGroupMixin(AuthenticateLoginMixin):
    """
    Restricts view to users with one of the given login groups
    """

    authenticate_groups = []  # this should be set to the group you want to restrict view to
    authenticate_groups_message_code = "AUTO_LOGIN_DENIAL"  # pass a code for the messages

    def authenticate(self, request, *args, **kwargs):
        authentication_response = super().authenticate(request, *args, **kwargs)

        if authentication_response is not None:
            return authentication_response
        else:
            passing_groups = self.authenticate_groups + ["staff"]  # staff have access to everything
            user_is_valid = next((True for g in request.user.groups.all() if g.name in passing_groups), False)
            if user_is_valid:
                return None
            else:
                context = dict(
                    access_denied_message=self.get_authenticate_groups_restriction_message()
                )
                return render(request, "myapa/newtheme/member-access-only.html", context=context)

    def get_authenticate_groups_restriction_message(self):
        return MessageText.objects.get(code=self.authenticate_groups_message_code)


class AuthenticateMemberMixin(AuthenticateWebUserGroupMixin):
    """
    Checks if user is a member
    """
    authenticate_groups = ["member", "studentmember"]
    authenticate_groups_message_code = "NOT_APA_MEMBER"


class AuthenticateStaffMixin(AuthenticateWebUserGroupMixin):
    """
    Checks if user is staff
    """
    authenticate_groups = ["staff"]


class AuthenticateContactRoleMixin(AuthenticateLoginMixin):
    """
    View will render access restricted template logged in user doesn't match relationship with content
    NOTE: Assumes the view you are using implements a set_content method
    """

    authenticate_role_type = None  # None means all

    def get_authenticate_contactrole_contact(self):
        """
        Sometimes we want to auhenticate the contactrole of a related contact, like an organization
        """
        return self.request.user.contact

    def authenticate(self, request, *args, **kwargs):
        authentication_response = super().authenticate(request, *args, **kwargs)

        if authentication_response is not None:
            return authentication_response
        else:
            self.set_content(self, *args, **kwargs)

            role_type_list = self.authenticate_role_type if \
                isinstance(self.authenticate_role_type, (list, tuple)) \
                else (self.authenticate_role_type,)
            contact = self.get_authenticate_contactrole_contact()

            if self.content is not None:
                is_valid = ContactRole.objects.filter(
                    content=self.content,
                    contact=contact,
                    role_type__in=role_type_list
                ).exists()
            else:
                is_valid = True

            if not is_valid:
                return render(request, "myapa/newtheme/restricted-access.html")
            else:
                return None


class ContactOrganizationMixin(AuthenticateLoginMixin):

    def authenticate(self, request, *args, **kwargs):

        authentication_response = super().authenticate(request, *args, **kwargs)
        if authentication_response is not None:
            return authentication_response
        else:
            self.get_organization()

            if not self.organization:
                return render(
                    request,
                    "myapa/newtheme/restricted-access.html",
                    dict(
                        message="<h2>You are not associated with an organization in our database. "
                                "If you believe this is an error, contact "
                                "<a href='mailto:customerservice@planning.org'>customer service</a> "
                                "for assistance</h2>"
                        )
                )  # make sure to set access restricted template
            else:
                return None

    def get_organization(self):
        if not hasattr(self, "organization"):
            self.organization = self.request.user.contact.company_fk
            contactrelationships = ContactRelationship.objects.filter(
                source=self.organization,
                target=self.request.user.contact
            )
            self.organization_is_admin = next(
                (True for cr in contactrelationships if cr.relationship_type == "ADMINISTRATOR"),
                False
            )
            self.organization_is_billing = next(
                (True for cr in contactrelationships if cr.relationship_type == "BILLING_I"),
                False
            )
        return self.organization


class AuthenticateOrganizationContactRoleMixin(ContactOrganizationMixin, AuthenticateContactRoleMixin):

    def get_authenticate_contactrole_contact(self):
        return self.get_organization()


class AuthenticateProviderContactRoleMixin(AuthenticateLoginMixin):
    """
    View will render access restricted template logged in user doesn't match provider relationship with content
    NOTE: Assumes the view you are using implements a set_content method
    ALSO NOTE: Should be pass role_type or assume this will only be used for providers?
    """

    authenticate_role_type = "ADMINISTRATOR"

    # IF PROVIDER RECORD DOES NOT EXIST YET FOR THIS RECORD, THEN CREATE ONE
    def authenticate(self, request, *args, **kwargs):
        authentication_response = super().authenticate(request, *args, **kwargs)

        if authentication_response is not None:
            return authentication_response
        else:
            self.set_content(self, *args, **kwargs)

            role_type_list = self.authenticate_role_type if \
                isinstance(self.authenticate_role_type, (list, tuple)) \
                else (self.authenticate_role_type,)

            if request.user.is_staff:
                is_valid = True

            elif self.content is not None:
                provider = ContactRole.objects.get(content=self.content, role_type="PROVIDER").contact
                is_valid = ContactRelationship.objects.filter(
                    relationship_type=self.authenticate_role_type,
                    source=provider,
                    target__user__username=self.username
                ).exists()

            else:
                is_valid = True

            if not is_valid:
                return render(request, "myapa/newtheme/restricted-access.html")
            else:
                return None


class JoinRenewMixin(AuthenticateLoginMixin):
    """
    Tests whether membership forms belong to "join" vs "renew" process, and whether member is
    student, regular, or international
    NOTE: Consider not inheriting from AuthenticateLoginMixin, or using additonal hook on
    AuthenticateLoginMixin for extra setup logic? Would be clearer...
    """

    is_international = False
    is_student = False
    is_aicp = False
    has_renewed = False
    subscriptions = []
    imis_name = None
    imis_ind_demographics = None
    is_new_membership_qualified = False
    contact = None

    def authenticate(self, request, *args, **kwargs):

        authentication_response = super().authenticate(request, *args, **kwargs)
        if authentication_response:
            return authentication_response

        if self.is_authenticated:
            self.contact = Contact.objects.filter(
                user=self.request.user
            ).select_related("user").first()
            self.contact.sync_from_imis()
            self.subscriptions = self.get_active_subscriptions()

            # IF USER IS LOGGED IN, AND THEY HAVE MEMBERSHIP,
            # DON'T LET THEM CONTINUE UNLESS THEY ARE UP FOR RENEWAL
            membership_subscription = self.subscriptions.filter(
                product_code__in=("APA", "MEMBERSHIP_STU")
            ).first()

            if membership_subscription and self.contact.has_autodraft_payment():
                return render(
                    request,
                    "myapa/newtheme/join/enrolled-in-autodraft.html",
                    context=dict(membership=membership_subscription)
                )

            elif membership_subscription and \
                membership_subscription.copies_paid > 0 and \
                    membership_subscription.bill_copies > 0:
                return render(
                    request,
                    "myapa/newtheme/join/not-up-for-renewal.html",
                    context=dict(membership=membership_subscription)
                )
            # IF THE USER HAS A PARTIAL PAYMENT, DO NOT LET THEM RENEW
            elif membership_subscription and \
                membership_subscription.payment_amount != 0:
                return render(
                    request,
                    "myapa/newtheme/join/partial-payment.html",
                    context=dict(membership=membership_subscription)
                )

            self.imis_name = self.contact.get_imis_name()
            self.imis_ind_demographics = self.contact.get_imis_ind_demographics()

            self.is_new_membership_qualified = self.contact.is_new_membership_qualified

        else:
            self.contact = None

        return None

    def get_active_subscriptions(self):
        subscriptions = Subscriptions.objects.filter(
            # TODO: SHouldn't this be querying on bt_id?
            id=self.contact.user.username,
            status="A"
        ).only(
            "id", "product_code", "prod_type", "status",
            "begin_date", "paid_thru", "copies", "bill_begin",
            "bill_thru", "bill_amount", "bill_copies",
            "copies_paid", "balance", "payment_amount"
        )
        return subscriptions


class AuthenticateStudentMemberMixin(AuthenticateLoginMixin):

    def authenticate(self, request, *args, **kwargs):
        authentication_response = super().authenticate(request, *args, **kwargs)
        if authentication_response is not None:
            return authentication_response
        elif self.request.user.contact.member_type not in ["STU", "FSTU"]:
            return render(
                request,
                "myapa/newtheme/restricted-access.html"
            )
        else:
            return None
