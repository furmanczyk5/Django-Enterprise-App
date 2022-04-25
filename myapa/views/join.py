import datetime
from functools import reduce

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import TemplateView, FormView
from sentry_sdk import capture_message, configure_scope

from content.mail import Mail
from content.utils import generate_random_string
from imis.enums.members import ImisNameAddressPurposes
from imis.enums.relationship_types import ImisRelationshipTypes
from imis.models import CustomDegree, Counter, Advocacy, MailingDemographics, \
    Subscriptions
from myapa.forms import NonMemberCreateAccountForm, JoinCreateAccountForm, \
    JoinUpdateAccountForm, JoinPersonalInformationForm, JoinEnhanceMembershipForm, \
    StudentJoinEnhanceMembershipForm, StudentJoinSchoolInformationForm, StudentAddFreeDivisionsForm
from myapa.models.constants import DEGREE_TYPE_CHOICES
from myapa.models.educational_degree import EducationalDegree
from myapa.permissions import utils as permissions_utils
from myapa.utils import get_primary_chapter_code_from_zip_code
from myapa.viewmixins import JoinRenewMixin, AuthenticateWebUserGroupMixin, \
    AuthenticateStudentMemberMixin
from myapa.views.account import CreateAccountFormView, PersonalInformationView
from store.models import Purchase, ProductCart, Order, Payment


class MembershipCartViewMixin(object):
    """Various methods for adding membership products to user's cart and processing the cart"""
    membership_product_code = "MEMBERSHIP_MEM"
    chapter_product = None

    def add_membership_to_cart(self, user=None):

        user = user or self.request.user

        Purchase.objects.filter(
            user=user,
            product__code__in=["MEMBERSHIP_MEM", "MEMBERSHIP_STU"],
            order__isnull=True
        ).delete()

        product = ProductCart.objects.get(code=self.membership_product_code)
        product.add_to_cart(contact=user.contact, purchases=user.contact.purchase_set.all())

    def add_primary_chapter_to_cart(self, chapter, user=None):
        user = user or self.request.user
        self.chapter_product = ProductCart.objects.get(
            code="CHAPT_{0}".format(chapter),
        )
        self.chapter_product.add_to_cart(
            contact=user.contact,
            purchases=user.contact.purchase_set.all()
        )

    def add_aicp_dues_to_cart(self, user=None):
        user = user or self.request.user
        aicp_product = ProductCart.objects.get(code="MEMBERSHIP_AICP")
        aicp_product.add_to_cart(contact=user.contact, purchases=user.contact.purchase_set.all())

    def get_membership_purchases(self, user=None):
        user = user or self.request.user
        # Excludes anything that has a dollar ammount. Gets only the following products:
        #   1.student membership, 2.primary chapter, 3.divisions, 4.aicp dues, 5.aicp prorated dues

        primary_chapter_code = get_primary_chapter_code_from_zip_code(user.contact.zip_code)
        primary_chapter_product_code = "CHAPT_{0}".format(primary_chapter_code)

        return Purchase.objects.filter(
            Q(contact=user.contact) | Q(user=user),
            Q(product__code__in=[
                self.membership_product_code,
                primary_chapter_product_code,
                "MEMBERSHIP_AICP",
                "MEMBERSHIP_AICP_PRORATE"
            ]) | Q(product__product_type="DIVISION"),
            order__isnull=True
        )

    def process_membership(self, purchases, user=None, send_order_confirmation=True):
        user = user or self.request.user

        order = Order.objects.create(
            user=user,
            submitted_user_id=user.username,
            order_status="SUBMITTED",
            submitted_time=timezone.now()
        )
        purchases.update(order=order)

        payment = Payment.objects.create(
            method='NONE',
            order=order,
            user=user,
            submitted_time=timezone.now(),
            amount=0
        )
        payment.process()

        for purchase in order.get_purchases():
            purchase.process(checkout_source="CART")

        order.process()

        if send_order_confirmation:
            order.send_confirmation()

        permissions_utils.update_user_groups(user)

        return order


class NonMemberJoinView(CreateAccountFormView):
    """View for users to create an non-member account"""
    template_name = "myapa/newtheme/nonmember-account-create-form.html"
    form_class = NonMemberCreateAccountForm
    is_admin = False
    contact = None

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["is_individual"] = True
        return form_kwargs

    def setup(self):

        if getattr(self.request, "user", None) is not None:
            self.contact = getattr(self.request.user, "contact", None)

        # check MyOrg admin relationship for admins creating new admins
        # that don't have accounts yet
        if self.contact is not None:
            self.is_admin = self.contact.get_imis_source_relationships().filter(
                relation_type__in=(
                    ImisRelationshipTypes.ADMIN_I.value,
                    ImisRelationshipTypes.CM_I.value
                )
            ).exists()

    def get(self, request, *args, **kwargs):
        self.setup()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.setup()
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        if self.is_admin:
            return reverse_lazy('myorg')
        else:
            return reverse_lazy('nonmember_join')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_admin"] = self.is_admin
        context["contact"] = self.contact
        return context

    def get_password(self, form):
        if self.is_admin:
            return generate_random_string(length=10)
        else:
            return super().get_password(form)

    def login_user(self, username, password):
        if not self.is_admin:
            super().login_user(username, password)

    def after_save(self, form):
        super().after_save(form)
        if self.is_admin:
            messages.success(
                self.request,
                "{0} {1} ({2}) has been created with User ID: {3}".format(
                    self.contact.first_name,
                    self.contact.last_name,
                    self.contact.email,
                    self.contact.user.username
                )
            )
        Mail.send(
            mail_code='MYAPA_NONMEMBER_CREATE',
            mail_to=form.cleaned_data.get("email"),
            mail_context=form.cleaned_data
        )

    def get_template_names(self):
        if self.is_admin or not self.contact:
            return ["myapa/newtheme/nonmember-account-create-form.html"]
        else:
            return ["myapa/newtheme/nonmember-account-create-confirmation.html"]


class NonMemberJoinViewAdmin(AuthenticateWebUserGroupMixin, NonMemberJoinView):
    """A marginally more secure way of allowing staff admins to create new nonmember
    Django users by inheriting from :class:`myapa.viewmixins.AuthenticateStafffMixin`"""

    authenticate_groups = ["component-admin", "staff"]
    prompt_login = True

    def setup(self):
        super().setup()
        self.is_admin = True

    def get_success_url(self):
        return reverse_lazy('nonmember_join_admin')


class JoinAccountView(JoinRenewMixin, CreateAccountFormView):
    """ First Step of Join/Renew Process, for creating a new account or confirming existing email """
    template_name = "myapa/newtheme/join/account-information.html"
    success_url = reverse_lazy("join_personal_info")
    prompt_login = False

    def get_form_class(self):
        if self.is_authenticated:
            return JoinUpdateAccountForm
        else:
            return JoinCreateAccountForm

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["instance"] = self.contact
        return form_kwargs

    def get_initial(self):
        initial = super().get_initial()

        if self.contact:
            # Sync from iMIS at the beginning of the join/renew process
            # to make sure django has the latest iMIS data. (only syncing on GET so that
            # we don't needless re-sync when form is submitted)
            if self.request.method == "GET":
                self.contact.sync_from_imis()

            addresses = self.contact.get_imis_name_address()
            mailing_preferences = None
            billing_preferences = None

            primary_address = home_address = addresses.filter(purpose='Home Address')

            if primary_address.count() == 1:
                primary_address = primary_address.first()
            elif primary_address.count() > 1:
                raise Http404("Error: More than one home address.")
            else:
                primary_address = None

            secondary_address = work_address = addresses.filter(purpose='Work Address')

            if secondary_address.count() == 1:
                secondary_address = secondary_address.first()
            elif secondary_address.count() > 1:
                raise Http404("Error: More than one work address.")
            else:
                secondary_address = None

            if primary_address.preferred_mail:
                mailing_preferences = ImisNameAddressPurposes.HOME_ADDRESS.value
            elif secondary_address and secondary_address.preferred_mail:
                mailing_preferences = ImisNameAddressPurposes.WORK_ADDRESS.value

            if primary_address.preferred_bill:
                billing_preferences = ImisNameAddressPurposes.HOME_ADDRESS.value
            elif secondary_address and secondary_address.preferred_bill:
                billing_preferences = ImisNameAddressPurposes.WORK_ADDRESS.value

            initial.update({
                "mailing_preferences": mailing_preferences,
                "billing_preferences": billing_preferences,
                "verify_email": self.contact.email if self.contact else "",
                "secondary_verify_email": self.contact.secondary_email if self.contact else "",
                "informal_name": self.contact.informal_name,
                "user_address_num": getattr(primary_address, "address_num", None),
                "address1": getattr(primary_address, "address_1", ""),
                "address2": getattr(primary_address, "address_2", ""),
                "city": getattr(primary_address, "city", ""),
                "state": getattr(primary_address, "state_province", ""),
                "zip_code": getattr(primary_address, "zip", ""),
                "country": getattr(primary_address, "country", ""),
                "company": getattr(primary_address, "company", ""),
                "home_preferred_mail": getattr(primary_address, "preferred_mail", None),
                "home_preferred_bill": getattr(primary_address, "preferred_bill", None),

                "additional_user_address_num": getattr(secondary_address, "address_num", None),
                "additional_address1": getattr(secondary_address, "address_1", ""),
                "additional_address2": getattr(secondary_address, "address_2", ""),
                "additional_city": getattr(secondary_address, "city", ""),
                "additional_state": getattr(secondary_address, "state_province", ""),
                "additional_zip_code": getattr(secondary_address, "zip", ""),
                "additional_country": getattr(secondary_address, "country", ""),
                "additional_company": getattr(secondary_address, "company", ""),
                "work_preferred_mail": getattr(secondary_address, "preferred_mail", None),
                "work_preferred_bill": getattr(secondary_address, "preferred_bill", None),
            })

        return initial

    def form_valid(self, form):

        if self.is_authenticated:

            self.update_imis_contact(form)
            self.post_address_data_to_imis(form, self.contact)

            form.save()
            user = self.request.user
            user.email = form.cleaned_data.get("email", "")
            user.save()

            return super(CreateAccountFormView, self).form_valid(form)
        else:
            # new users taken care of by inherited form class
            return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["contact"] = getattr(self, "contact", None)
        context["is_recurring"] = False
        if context['contact']:
            context["is_recurring"] = self.contact.has_autodraft_payment()
        return context

    def get_template_names(self):
        if self.is_authenticated:
            return "myapa/newtheme/join/account-information.html"
        else:
            return "myapa/newtheme/join/account-information-newuser.html"

    def update_imis_contact(self, form):
        self.imis_name.informal = form.cleaned_data.get("informal_name", "")
        self.imis_name.birth_date = form.cleaned_data.get("birth_date", "")
        self.imis_name.email = form.cleaned_data.get("email", "")
        self.imis_name.home_phone = form.cleaned_data.get("phone", "")
        self.imis_name.work_phone = form.cleaned_data.get("secondary_phone", "")
        self.imis_name.mobile_phone = form.cleaned_data.get("cell_phone", "")

        self.imis_ind_demographics.secondary_email = form.cleaned_data.get("secondary_email", "")

        self.imis_name.save()
        self.imis_ind_demographics.save()
        self.contact.insert_name_log_record(
            self.contact.make_name_log_data(self.contact.NAME_LOG_CHANGE_RECORD)
        )


class JoinPersonalInformationView(JoinRenewMixin, MembershipCartViewMixin, PersonalInformationView):
    """
    View for Personal Information step of Join process
    """
    form_class = JoinPersonalInformationForm
    template_name = "myapa/newtheme/join/personal-information.html"
    success_url = reverse_lazy("join_subscriptions")
    membership_product_code = "MEMBERSHIP_MEM"

    def get_initial_salary(self):
        """ This determines pricing for membership """
        if self.is_new_membership_qualified:
            initial_salary = "L"
        else:
            initial_salary = super().get_initial_salary()
        return initial_salary

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update({"is_new_membership_qualified": self.is_new_membership_qualified})
        return form_kwargs

    def after_save(self, form):

        super().after_save(form)
        if getattr(settings, 'JOIN_RENEW_DEBUG', False):
            with configure_scope() as scope:
                scope.set_level('debug')
                scope.user = dict(username=self.contact.user.username)
                scope.set_extra("country", self.contact.country)
                scope.set_extra("salary_range", self.contact.salary_range)
            capture_message('Adding membership to cart')

        self.add_membership_to_cart()

        # TODO: Should we stop user on final step if they somehow don't have chapter and they are "United States"?
        #   On previous address step we are making sure zip code matches to chapter,
        #   but there is no guarantee that zip code is still the same on this step
        if self.contact.country == "United States":
            us_chapter = get_primary_chapter_code_from_zip_code(self.contact.zip_code)
            if us_chapter:
                self.add_primary_chapter_to_cart(us_chapter)
            else:
                capture_message("No chapter found for zip code {}".format(self.contact.zip_code), level='error')

        if self.contact.is_aicp:
            self.add_aicp_dues_to_cart()


class JoinEnhanceMembershipView(JoinRenewMixin, FormView):
    """
    View in join process for adding divisions, additional chapters, and subscriptions
    """
    form_class = JoinEnhanceMembershipForm
    template_name = "myapa/newtheme/join/enhance-membership.html"
    success_url = reverse_lazy("join_summary")

    def get(self, request, *args, **kwargs):
        self.setup()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.setup()
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update(
            dict(
                contact=self.contact,
                subscriptions=self.subscriptions,
                cart_products=[p.product for p in Purchase.cart_items(user=self.request.user)],
                primary_chapter_product=self.primary_chapter
            )
        )
        return form_kwargs

    def get_initial(self):
        initial = super().get_initial()

        if self.primary_chapter:
            initial["primary_chapter"] = self.primary_chapter.id

        initial["planners_advocacy"] = Advocacy.objects.filter(
            id=self.contact.user.username,
            grassrootsmember=True
        ).exists()

        initial["exclude_planning_print"] = MailingDemographics.objects.filter(
            id=self.contact.user.username,
            excl_planning_print=True
        ).exists()

        return initial

    def form_valid(self, form):
        form.save()

        Advocacy.objects.update_or_create(
            id=self.contact.user.username,
            defaults=dict(
                grassrootsmember=form.cleaned_data.get("planners_advocacy", False)
            )
        )

        MailingDemographics.objects.update_or_create(
            id=self.contact.user.username,
            defaults=dict(
                excl_planning_print=form.cleaned_data.get("exclude_planning_print", True)
            )
        )

        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["primary_chapter"] = self.primary_chapter
        context["primary_chapter_logo"] = self.primary_chapter_logo
        return context

    def get_chapter_from_zip(self):

        chapter_code = get_primary_chapter_code_from_zip_code(self.contact.zip_code)
        self.primary_chapter_logo = None
        if chapter_code is not None:
            self.primary_chapter_logo = "images/badges/{0}logo.jpg".format(chapter_code)

        chapter = ProductCart.objects.filter(
            code="CHAPT_{0}".format(chapter_code),
            publish_status="PUBLISHED"
        ).first()

        return chapter

    def setup(self):
        self.primary_chapter = None
        self.primary_chapter_logo = None
        if self.contact.country == 'United States':
            self.primary_chapter = self.get_chapter_from_zip()


class JoinMembershipSummaryView(JoinRenewMixin, TemplateView):
    """
    View for Membership Summary step of the join process
    """

    template_name = "myapa/newtheme/join/summary.html"
    membership_product_code = "MEMBERSHIP_MEM"

    def get(self, request, *args, **kwargs):
        self.cart_items = Purchase.cart_items(user=request.user)
        self.imis_contact = self.contact.get_imis_contact_legacy()['data']
        self.demographics = self.contact.get_imis_demographics_legacy()['data']

        addresses = self.contact.get_imis_name_address()
        self.mailing_address = addresses.filter(preferred_mail=True).first()
        self.primary_address = addresses.filter(purpose="Home Address").first()
        self.secondary_address = addresses.filter(purpose="Work Address").first()

        self.membership_purchase = next(
            (p for p in self.cart_items if p.product.code == self.membership_product_code),
            None
        )

        self.aicp_dues_purchase = next(
            (p for p in self.cart_items if p.product.code == "MEMBERSHIP_AICP"),
            None
        )

        self.aicp_prorated_dues_purchase = next(
            (p for p in self.cart_items if p.product.code == "MEMBERSHIP_AICP_PRORATE"),
            None
        )
        primary_chapter_code = get_primary_chapter_code_from_zip_code(
            zip_code = getattr(self.mailing_address, "zip", None)
        )
        primary_chapter_product_code = "CHAPT_{0}".format(primary_chapter_code)
        self.primary_chapter_purchase = next(
            (p for p in self.cart_items if p.product.code == primary_chapter_product_code),
            None
        )

        self.other_chapter_purchases = [
            p for p in self.cart_items if
            p.product.product_type == "CHAPTER" and p.product.code != primary_chapter_product_code
        ]

        self.division_purchases = [
            p for p in self.cart_items if p.product.product_type == "DIVISION"
        ]

        self.subscription_purchases = [
            p for p in self.cart_items if p.product.product_type == "PUBLICATION_SUBSCRIPTION"
        ]
        all_purchases = [
            self.membership_purchase,
            self.aicp_dues_purchase,
            self.aicp_prorated_dues_purchase,
            self.primary_chapter_purchase
        ] + self.other_chapter_purchases + self.division_purchases + self.subscription_purchases

        self.planners_advocacy = Advocacy.objects.filter(
            id=self.contact.user.username,
            grassrootsmember=True
        ).exists()

        self.total = reduce(lambda x, y: x + (y.product_price.price if y else 0), all_purchases, 0)

        self.show_recurring_options = not self.contact.has_autodraft_payment()

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            "contact": self.contact,
            "imis_contact": self.imis_contact,
            "demographics": self.demographics,
            "primary_address": self.primary_address,
            "secondary_address": self.secondary_address,
            "membership_purchase": self.membership_purchase,
            "aicp_dues_purchase": self.aicp_dues_purchase,
            "aicp_prorated_dues_purchase": self.aicp_prorated_dues_purchase,
            "primary_chapter_purchase": self.primary_chapter_purchase,
            "other_chapter_purchases": self.other_chapter_purchases,
            "division_purchases": self.division_purchases,
            "subscription_purchases": self.subscription_purchases,
            "planners_advocacy": self.planners_advocacy,
            "total": self.total,
            "show_recurring_options": self.show_recurring_options
        })
        return context


class StudentJoinAccountView(JoinAccountView):
    template_name = "myapa/newtheme/join/student/account-information.html"
    success_url = reverse_lazy("join_student_school_information")

    def get_template_names(self):
        if self.is_authenticated:
            return "myapa/newtheme/join/student/account-information.html"
        else:
            return "myapa/newtheme/join/student/account-information-newuser.html"


class StudentJoinSchoolInformationView(JoinRenewMixin, FormView):
    template_name = "myapa/newtheme/join/student/school-information.html"
    success_url = reverse_lazy("join_student_personal_info")
    form_class = StudentJoinSchoolInformationForm

    def get_initial(self):

        initial = super().get_initial()

        current_degree = EducationalDegree.objects.filter(
            contact=self.request.user.contact,
            is_current=True
        ).first()

        if current_degree is not None:

            if current_degree.school_seqn:
                initial_degree_program = current_degree.school_seqn
                initial_degree_type_choice = None
                initial_degree_type_other = None
            elif current_degree.program in [dt[0] for dt in DEGREE_TYPE_CHOICES]:
                initial_degree_program = "OTHER"
                initial_degree_type_choice = current_degree.program
                initial_degree_type_other = None
            else:
                initial_degree_program = "OTHER"
                initial_degree_type_choice = "OTHER"
                initial_degree_type_other = current_degree.program

            initial.update({
                "school": current_degree.school.user.username if current_degree.school else "OTHER",
                "other_school": current_degree.other_school if not current_degree.school else None,
                "degree_program": initial_degree_program,
                "degree_type_choice": initial_degree_type_choice,
                "degree_type_other": initial_degree_type_other,
                "level": current_degree.level,
                "level_other": current_degree.level_other,
                "graduation_date": current_degree.graduation_date,
                "student_id": current_degree.student_id
            })

        return initial

    def form_valid(self, form):

        contact = self.request.user.contact
        contact.member_type = 'STU'
        # this will be faster than myapa.permissions.utils.update_user_groups
        studentmember_group = Group.objects.get(name='studentmember')
        if studentmember_group not in contact.user.groups.all():
            contact.user.groups.add(studentmember_group)
        contact.save()

        EducationalDegree.objects.filter(contact=contact, is_current=True).update(is_current=False)
        CustomDegree.objects.filter(
            id=self.request.user.username,
            is_current=True
        ).update(is_current=False)

        degree = form.save(commit=False)
        degree.contact = self.request.user.contact

        # for now always creating new degree
        custom_degree = CustomDegree.objects.create(
            id=self.request.user.username,
            seqn=Counter.create_id(counter_name="Custom_Degree"),
            school_id=degree.school.user.username if degree.school else "",
            school_other=degree.other_school,
            school_seqn=degree.school_seqn or 0,  # This is the pk to the
            degree_level=degree.level,
            degree_level_other=degree.level_other or "",
            degree_program=degree.program,
            accredited_program=degree.program if degree.school_seqn else "",
            degree_date=degree.graduation_date,
            degree_planning=degree.is_planning,
            degree_complete=degree.complete,
            school_student_id=degree.student_id,
            is_current=degree.is_current,
        )

        degree.seqn = custom_degree.seqn
        degree.save()

        return super().form_valid(form)


class StudentJoinPersonalInformationView(JoinPersonalInformationView):
    template_name = "myapa/newtheme/join/student/personal-information.html"
    success_url = reverse_lazy("join_student_subscriptions")
    membership_product_code = "MEMBERSHIP_STU"

    def get_initial_salary(self):
        """ This determines pricing for membership """
        return 'K'

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["is_student"] = True
        return form_kwargs

    def after_save(self, form):
        super().after_save(form)
        ind_demo = self.contact.get_imis_ind_demographics()
        ind_demo.is_current_student = True
        ind_demo.save()


class StudentJoinEnhanceMembershipView(JoinEnhanceMembershipView):
    template_name = "myapa/newtheme/join/student/enhance-membership.html"
    success_url = reverse_lazy("join_student_summary")
    form_class = StudentJoinEnhanceMembershipForm


class StudentJoinMembershipSummaryView(MembershipCartViewMixin, JoinMembershipSummaryView):
    membership_product_code = "MEMBERSHIP_STU"
    template_name = "myapa/newtheme/join/student/summary.html"

    def get(self, request, *args, **kwargs):
        self.school_information = self.get_school_information()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.school_information = self.get_school_information()
        membership_purchases = self.get_membership_purchases()

        # TODO...
        # verify information and products here:
        #  - user must have membership,
        #  - user must have primary chapter
        #  - user cannot have more than 5 chapters

        order = self.process_membership(membership_purchases)
        self.send_welcome_email(order)
        request.contact.sync_from_imis()
        permissions_utils.update_user_groups(request.contact.user)
        return redirect("join_student_confirmation")

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["school_information"] = self.school_information
        return context

    def get_membership_purchases(self, user=None):
        return super().get_membership_purchases(user=user).filter(
            product_price__price=0
        )

    def get_school_information(self):
        return EducationalDegree.objects.filter(
            contact=self.request.user.contact,
            is_current=True
        ).first()

    def send_welcome_email(self, order):
        contact = self.request.user.contact
        purchases = Purchase.objects.select_related("product__content").filter(order_id=order.id)

        school = self.school_information.school.title \
            if self.school_information.school \
            else self.school_information.other_school

        mail_context = dict(
            student=self.request.user.contact,
            school=school,
            divisions=[
                p.product.content for p in purchases if p.product.product_type == "DIVISION"
            ],
            primary_chapter=next(
                (p.product.content for p in purchases if p.product.product_type == "CHAPTER"),
                dict()
            ),
        )
        Mail.send(
            mail_code="STUDENT_JOIN_ONLINE_WELCOME",
            mail_to=contact.email,
            mail_context=mail_context
        )


class StudentJoinConfirmationView(TemplateView):
    template_name = "myapa/newtheme/join/student/confirmation.html"


class StudentUpdateDivisionsView(AuthenticateStudentMemberMixin, FormView):
    """ View for student members to add their five free divisions
        IMPORTANT:
            Later we will need to add the ability to remove and change which divisions during renewal period.
            Specifically for auto renewed students.
    """
    template_name = "myapa/newtheme/join/student/update-divisions.html"
    form_class = StudentAddFreeDivisionsForm
    success_url = reverse_lazy("myapa")

    def get(self, request, *args, **kwargs):
        self.setup()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.setup()
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["active_division_products"] = self.active_division_products
        form_kwargs["available_division_products"] = self.available_division_products
        form_kwargs["contact"] = self.request.user.contact
        return form_kwargs

    def form_valid(self, form):
        purchases = form.save()
        self.process_new_divisions(purchases)
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_division_products"] = self.active_division_products
        return context

    def setup(self):
        self.division_products = self.get_division_products()
        active_division_subscriptions = self.get_active_division_subscriptions()
        active_subscription_product_codes = ["DIVISION_{}".format(s.product_code) for s in
                                             active_division_subscriptions]
        self.active_division_products = [p for p in self.division_products if
                                         p.code in active_subscription_product_codes]
        self.available_division_products = [p for p in self.division_products if
                                            p.code not in active_subscription_product_codes]

    def get_division_products(self):
        return ProductCart.objects.filter(
            status="A",
            product_type="DIVISION"
        ).order_by(
            "content__title"
        )

    def get_active_division_subscriptions(self):
        return Subscriptions.objects.filter(
            id=self.request.user.username,
            status="A",
            prod_type="SEC"  # DIVISIONS HAVE prod_type "SEC" in imis
        ).only(
            "id", "product_code", "prod_type", "status",
            "begin_date", "paid_thru", "copies", "bill_begin",
            "bill_thru", "bill_amount", "bill_copies",
            "copies_paid", "balance"
        )

    def process_new_divisions(self, purchases):
        order = Order.objects.create(
            user=self.request.user,
            submitted_user_id=self.request.user.username,
            order_status="SUBMITTED",
            submitted_time=timezone.now()
        )

        Purchase.objects.filter(id__in=[p.id for p in purchases]).update(order=order)

        payment = Payment.objects.create(
            method='NONE',
            order=order,
            user=self.request.user,
            submitted_time=timezone.now(),
            amount=0
        )
        payment.process()

        for purchase in order.get_purchases():
            purchase.process(checkout_source="CART")

        order.process()
        order.send_confirmation()

        permissions_utils.update_user_groups(self.request.user)

        self.update_imis_division_subscriptions(purchases)

    def update_imis_division_subscriptions(self, purchases):
        new_division_product_codes = [p.product.code for p in purchases]
        current_active_membership = Subscriptions.objects.only(
            "begin_date", "paid_thru", "bill_date"
        ).get(
            id=self.request.user.username,
            product_code="APA",
            status="A"
        )
        Subscriptions.objects.filter(
            id=self.request.user.username,
            status="A",
            product_code__in=new_division_product_codes
        ).update(
            begin_date=current_active_membership.begin_date,
            bill_begin=current_active_membership.begin_date,
            paid_thru=current_active_membership.paid_thru,
            bill_date=current_active_membership.bill_date
        )
