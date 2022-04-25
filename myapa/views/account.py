import datetime

import pytz
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.views import redirect_to_login
from django.core.urlresolvers import reverse_lazy
from django.db.models import Max
from django.forms.models import modelformset_factory
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.generic import TemplateView, FormView

from cm.models import Log, Period, ProviderApplication
from conference.cadmium_api_utils import *
from content.models import MessageText
from content.viewmixins import AppContentMixin
from content.views.render_content import REGISTRATION_LOGIN_GROUPS
from events.models import Event, Speaker, NATIONAL_CONFERENCE_CURRENT, NATIONAL_CONFERENCE_NEXT
from exam.open_water_api_utils import OpenWaterAPICaller
from imis import models as imis_models
from imis.enums.members import ImisNameAddressPurposes
from imis.enums.relationship_types import ImisRelationshipTypes
from imis.models import NameAddress
from imis.tests.factories.demographics import MailingDemographicsFactoryBlank
from learn.models import LearnCourseBundle
from myapa import utils
from myapa.forms import CreateAccountForm, UpdateAccountForm, UpdateAddressesForm, ResumeUploadForm, \
    PersonalInformationForm, AdvocacyNetworkForm, ProfileShareForm, \
    JobHistoryUpdateForm, EducationDegreeForm, UpdateSocialLinksForm, AboutMeAndBioUpdateForm, \
    ContactPreferencesUpdateForm, ImageUploadForm
from myapa.geonames_imis_country_mapping import GEONAMES_IMIS_COUNTRY_MAPPING
from myapa.models.constants import SHARE_CHOICES
from myapa.models.contact import Contact
from myapa.models.educational_degree import EducationalDegree
from myapa.models.imis_sync_mixin import ImisSyncMixin
from myapa.models.job_history import JobHistory
from myapa.models.profile import IndividualProfile
from myapa.models.proxies import Bookmark, IndividualContact
from myapa.models.proxies import Organization
from myapa.viewmixins import AuthenticateLoginMixin
from store.models import Purchase, ContentProduct
from store.models.settings import GENERIC_IMIS_PRODUCTS
from uploads.models import ImageUpload, DocumentUpload


class MyapaOverviewView(AuthenticateLoginMixin, TemplateView):
    """ The Myapa dashboard View. This is where users can manage their account/membership/etc. """

    template_name = "myapa/newtheme/account/overview.html"

    def get(self, request, *args, **kwargs):

        self.contact = self.request.user.contact
        self.profile = self.get_profile()

        self.subscriptions = self.get_subscriptions()
        self.subscription_product_urls = self.get_subscription_product_urls()
        self.membership = self.get_membership_info()

        self.orders = self.get_orders()
        self.cm = self.get_cm_info()
        self.events = self.get_events()
        self.downloads = self.get_downloads()
        self.bookmarks = self.get_bookmarks()
        self.organization = self.get_organization_info()
        self.learn = self.get_learn()

        if 'log' in self.cm:
            try:
                period_code = self.cm['log'].period.code
                message = MessageText.objects.get(code="CM_LOG_NOTIFICATION", status="A")
            except (Period.DoesNotExist, MessageText.DoesNotExist):
                period_code = None
            if period_code and period_code in ('JAN2021', 'JAN2022'):
                messages.add_message(request, message.message_level, message.text)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["contact"] = self.contact
        context["profile"] = self.profile
        context["membership"] = self.membership
        context["subscriptions"] = self.subscriptions
        context["orders"] = self.orders
        context["cm"] = self.cm
        context["events"] = self.events
        context["downloads"] = self.downloads
        context["bookmarks"] = self.bookmarks
        context["organization"] = self.organization
        context["learn"] = self.learn
        context["LEARN_DOMAIN"] = settings.LEARN_DOMAIN

        context["share_choices"] = SHARE_CHOICES
        context["profile_image_form"] = ImageUploadForm()

        ind_demo = self.request.user.contact.get_imis_ind_demographics()
        context["aicp_start"] = getattr(ind_demo, 'aicp_start', None)
        context["aicp_cert_no"] = getattr(ind_demo, 'aicp_cert_no', None)


        one_year_post_current_npc_course_launch = datetime.datetime(
            2020, 10, 31, 0, 0, tzinfo=pytz.timezone("America/Chicago")
        )
        context['one_year_post_current_npc_course_launch'] = one_year_post_current_npc_course_launch

        # Special case for one year after launch of APA Learn
        # Hide the on-demand module in every case
        # TODO: Clean this and the overview.html template up after this date
        apa_learn_one_year_post_launch = datetime.datetime(
            2019, 11, 13, 0, 0, tzinfo=pytz.timezone("America/Chicago")
        )
        context['apa_learn_one_year_post_launch'] = apa_learn_one_year_post_launch

        context['is_one_year_post_apa_learn_launch'] = False
        days_delta = (apa_learn_one_year_post_launch - timezone.now()).days
        if days_delta < 0:
            context['is_one_year_post_apa_learn_launch'] = True
        designation = self.contact.designation
        context["has_cep"] = 'CEP' in designation if designation is not None else False
        context["has_ctp"] = 'CTP' in designation if designation is not None else False
        context["has_cud"] = 'CUD' in designation if designation is not None else False

        return context

    def get_subscriptions(self):
        subscriptions = imis_models.Subscriptions.objects.filter(
            id=self.contact.user.username,
            status="A"
        ).values(
            "id", "product_code", "prod_type", "status",
            "begin_date", "paid_thru", "copies", "bill_begin",
            "bill_thru", "bill_amount", "bill_copies",
            "copies_paid", "balance"
        )
        return subscriptions

    def get_all_subscriptions(self):
        subscriptions = imis_models.Subscriptions.objects.filter(
            id=self.contact.user.username,
            status__in=('A', 'I')
        ).values(
            "id", "product_code", "prod_type", "status",
            "begin_date", "paid_thru", "copies", "bill_begin",
            "bill_thru", "bill_amount", "bill_copies",
            "copies_paid", "balance"
        )
        return subscriptions

    def get_subscription_product_urls(self):
        """ adds info urls to the subscriptions passed in """
        subscription_product_urls = dict()
        subscription_products = ContentProduct.objects.filter(
            product__imis_code__in=[s.get("product_code") for s in self.subscriptions]
        ).values(
            "product__imis_code",
            "resource_url"
        )
        for sp in subscription_products:
            subscription_product_urls[sp.get("product__imis_code")] = (sp.get(
                "resource_url", None
            ) or "").strip()
        return subscription_product_urls


    def get_events(self):

        event_purchases = Purchase.objects.filter(
            contact=self.contact,
            product__product_type="EVENT_REGISTRATION"
        ).exclude(
            order__isnull=True
        ).values("product__content__id")

        events = Event.objects.filter(
            id__in=[p.get("product__content__id") for p in event_purchases]
        ).order_by("-begin_time", "-end_time", "title")[:3]

        return events

    def get_learn(self):
        return Purchase.objects.filter(
            contact=self.contact,
            product__product_type="LEARN_COURSE"
        ).exclude(
            order__isnull=True
        ).order_by(
            '-created_time'
        ).select_related(
            "product__content__master"
        )[:3]

    def get_downloads(self):
        return Purchase.objects.filter(
            contact=self.contact,
            product__product_type__in=("DIGITAL_PUBLICATION", "EBOOK")
        ).exclude(
            order__isnull=True
        ).select_related(
            "product__content__master"
        )[:3]

    def get_bookmarks(self):
        return Bookmark.objects.filter(contact=self.contact)[:3]

    def get_orders(self):
        contact_orders_qset = imis_models.Trans.objects.filter(
            bt_id=self.request.user.username,
            transaction_type="PAY"
        ).exclude(source_system="ORDER").order_by('-transaction_date')
        return contact_orders_qset[:3]

    @staticmethod
    def get_npc_info():
        npc_info = dict()
        most_recent_npc = Event.objects.filter(
            # TODO: Hardcoding this in now; will have to change post NPC19
            # code=NATIONAL_CONFERENCE_CURRENT[0],
            code="21CONF",
            publish_status="PUBLISHED"
        ).first()
        current_bundle_code_stem = "LRN_NPC" + most_recent_npc.code[0:2]
        current_bundle = LearnCourseBundle.objects.filter(publish_status="PUBLISHED", code__contains=current_bundle_code_stem).first()
        current_digital_product_url_id = None
        previous_digital_product_url_id = None
        # IS THERE A GENERALIZED SOLUTION TO THIS NEED FOR CURRENT AND PREVIOUS CONFERENCE DATA?
        # METHOD ON EVENT MODEL? DATABASE SOLUTION? CENTRALIZED SETTINGS DATA? Would be a much larger refactoring task...
        # First problem is how to define current and previous and are these definitions context-dependent?
        previous_to_most_recent_npc = Event.objects.filter(
            code="20CONF",
            publish_status="PUBLISHED"
        ).first()
        previous_bundle_code_stem = "LRN_NPC" + previous_to_most_recent_npc.code[0:2]
        previous_bundle = LearnCourseBundle.objects.filter(publish_status="PUBLISHED", code__contains=previous_bundle_code_stem).first()

        if current_bundle:
            current_digital_product_url = current_bundle.digital_product_url
            url_parts = current_digital_product_url.split("?") if current_digital_product_url else []
            current_digital_product_url_id = url_parts[1] if len(url_parts) > 1 else None

        if previous_bundle:
            previous_digital_product_url = previous_bundle.digital_product_url
            url_parts = previous_digital_product_url.split("?") if previous_digital_product_url else []
            previous_digital_product_url_id = url_parts[1] if len(url_parts) > 1 else None

        if not current_digital_product_url_id or not previous_digital_product_url_id:
            if settings.ENVIRONMENT_NAME == 'PROD':
                current_digital_product_url_id = "id=830"
                previous_digital_product_url_id = "id=6"
            else:
                current_digital_product_url_id = "id=201"
                previous_digital_product_url_id = "id=111"

        if most_recent_npc is not None:
            npc_info['npc_post_one_year_date'] = most_recent_npc.end_time + datetime.timedelta(days=365)
            npc_info['npc_short_name'] = 'NPC{}'.format(str(most_recent_npc.end_time.year)[-2:])
            npc_info['previous_npc_short_name'] = 'NPC{}'.format(str(previous_to_most_recent_npc.end_time.year)[-2:])
            npc_info['current_digital_product_url_id'] = current_digital_product_url_id
            npc_info['previous_digital_product_url_id'] = previous_digital_product_url_id
        return npc_info

    def _get_membership_info_member_types(self, user_groups):
        member_types = dict(
            is_member=next((True for g in user_groups if g.name == "member"), False),
            is_xmem=self.contact.member_type == "XMEM",
            is_leadership=next((True for g in user_groups if g.name == "leadership"), False),
            is_staff=next((True for g in user_groups if g.name == "staff"), False),
            is_aicp=next((True for g in user_groups if g.name == "aicp-cm"), False),
            is_cand=next((True for g in user_groups if g.name == "candidate-cm"), False),
            is_student=self.contact.is_student()
        )

        return member_types

    def get_membership_info(self):
        """ gets info about user's membership, chapters, and divisions """

        user_groups = self.request.user.groups.all()

        has_current_npc_webgroup = self._has_current_npc_webgroup(user_groups)

        npc_info = dict()
        if has_current_npc_webgroup:
            npc_info = self.get_npc_info()

        membership = self._get_membership_info_member_types(user_groups)
        subscription_info = self.get_subscription_info()
        membership.update(subscription_info)
        membership.update(dict(
            expiry_date=subscription_info['apa_expiry_date'],
            renew_alert=self.contact.can_renew() and not self.contact.has_autodraft_payment(),
            primary_chapter=self.contact.chapter,
            member_type=self.contact.member_type,
            has_current_npc_webgroup=has_current_npc_webgroup,
            has_previous_npc_webgroup=self._has_previous_npc_webgroup(user_groups)
        ))
        membership.update(npc_info)

        return membership

    def get_subscription_info(self):
        subscription_info = dict(
            apa_expiry_date=None,
            apa_expired=False,
            aicp_expiry_date=None,
            aicp_expired=False,
            aicp_prorate_balance=None,
            chapters=[],
            divisions=[]
        )

        for subscription in self.get_all_subscriptions():

            if subscription["product_code"] == "APA":

                if subscription["paid_thru"]:
                    subscription_info['apa_expiry_date'] = subscription['paid_thru']
                    subscription_info['apa_expired'] = subscription['status'] == 'I'

            elif subscription["product_code"] == "AICP":
                if subscription["paid_thru"]:
                    subscription_info['aicp_expiry_date'] = datetime.datetime(
                        year=int(subscription["paid_thru"].year),
                        month=int(subscription["paid_thru"].month),
                        day=int(subscription["paid_thru"].day)
                    )
                    subscription_info['aicp_expired'] = subscription['status'] == 'I'

            elif subscription["product_code"] == "AICP_PRORATE":
                if subscription["balance"]:
                    subscription_info['aicp_prorate_balance'] = subscription["balance"]

            elif subscription["prod_type"] == "CHAPT":
                product_code = subscription["product_code"]
                image_code = product_code.split('/')[1]
                if image_code[:2] == "CA" and len(image_code) > 2:
                    image_code = image_code[:2]
                subscription_info['chapters'].append(dict(
                    image_code=image_code,
                    product_code=product_code,
                    url=self.subscription_product_urls.get(product_code, None)
                ))

            elif subscription["prod_type"] == "SEC":
                product_code = subscription["product_code"]
                image_code = product_code.split(' ')[0]
                subscription_info['divisions'].append(dict(
                    image_code=image_code,
                    product_code=product_code,
                    url=self.subscription_product_urls.get(product_code, None)
                ))
        return subscription_info

    @staticmethod
    def _has_current_npc_webgroup(user_groups):
        current_npc_webgroup = REGISTRATION_LOGIN_GROUPS[-1]
        return next(
            (True for g in user_groups if g.name == current_npc_webgroup),
            False
        )

    @staticmethod
    def _has_previous_npc_webgroup(user_groups):
        previous_npc_webgroup = REGISTRATION_LOGIN_GROUPS[-2]
        return next(
            (True for g in user_groups if g.name == previous_npc_webgroup),
            False
        )

    def get_profile(self):
        profile, _ = IndividualProfile.objects.get_or_create(contact=self.contact)
        return profile

    def get_cm_info(self):
        cm_info = dict()
        current_log = Log.objects.filter(
            contact=self.contact,
            is_current=True
        ).select_related("period").order_by("period__begin_time").first()
        if current_log:
            log_overview = current_log.credits_overview()
            credits_earned = float(log_overview.get('general'))
            cm_info["log"] = current_log
            cm_info["credits_earned"] = credits_earned
            cm_info["general_credits_needed"] = max(float(log_overview.get('general_needed')), 0.0)
            cm_info["law_credits_needed"] = max(float(log_overview.get('law_needed')), 0.0)
            cm_info["ethics_credits_needed"] = max(float(log_overview.get('ethics_needed')), 0.0)
            cm_info["log_carryover"] = float(log_overview.get('carry_over'))
        return cm_info

    def get_organization_info(self):

        organization_info = dict()
        relationships = self.contact.get_imis_source_relationships().filter(
            relation_type__in=(
                ImisRelationshipTypes.ADMIN_I.value,
                ImisRelationshipTypes.CM_I.value
            )
        )
        company = None
        if relationships.exists():
            company = Contact.objects.filter(
                user__username=relationships.last().target_id
            ).first()

        if company:
            organization_info["contact"] = company
            organization_info["organization_type"] = company.organization_type
            organization_info["company"] = company.company
            organization_info["company_admin"] = True
            organization_info["is_provider"] = ProviderApplication.objects.filter(
                provider=company,
                status="S"
            ).exists()

        return organization_info


class UpdateProfileImageView(FormView):
    """ post-only form view for updating user's profile image. Always returns to the referer """

    form_class = ImageUploadForm
    success_url = "/myapa/"
    http_method_names = ['post']

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["instance"] = ImageUpload.objects.filter(
            upload_type__code="PROFILE_PHOTOS",
            created_by=self.request.user
        ).first()
        return form_kwargs

    def form_valid(self, form):
        image = form.save(commit=False)
        image.created_by = self.request.user
        image.save()
        IndividualProfile.objects.update_or_create(
            contact=self.request.user.contact,
            defaults=dict(image=image)
        )

        # reindex solr speaker record
        Speaker.solr_reindex_contact(self.request.user.contact)

        messages.success(self.request, "Your profile image has been updated successfully")
        return redirect(self.request.META.get('HTTP_REFERER'))

    def form_invalid(self, form):
        return redirect(self.request.META.get('HTTP_REFERER'))


class CreateAccountFormViewMixin(object):
    """ Contains methods helpful for processing account form view data """

    @staticmethod
    def get_potential_duplicates(form, contact=None):
        """ returns potential duplicates based on submitted data """

        dup_check_kwargs = dict(
            contact=contact,
            first_name=form.cleaned_data.get("first_name"),
            last_name=form.cleaned_data.get("last_name"),
            birth_date=form.cleaned_data.get("birth_date"),
            email=form.cleaned_data.get("email"),
            secondary_email=form.cleaned_data.get("secondary_email"),
            phone=form.cleaned_data.get("phone"),
            secondary_phone=form.cleaned_data.get("secondary_phone"),
            cell_phone=form.cleaned_data.get("cell_phone"),
            address1=form.cleaned_data.get("address1"),
            address2=form.cleaned_data.get("address2"),
            city=form.cleaned_data.get("city"),
            state=form.cleaned_data.get("state"),
            country=form.cleaned_data.get("country"),
            zip_code=form.cleaned_data.get("zip_code"),
            secondary_address1=form.cleaned_data.get("additional_address1", None),
            secondary_address2=form.cleaned_data.get("additional_address2", None),
            secondary_city=form.cleaned_data.get("additional_city", None),
            secondary_state=form.cleaned_data.get("additional_state", None),
            secondary_country=form.cleaned_data.get("additional_country", None),
            secondary_zip_code=form.cleaned_data.get("additional_zip_code", None)
        )

        return utils.duplicate_check(**dup_check_kwargs)

    @staticmethod
    def post_new_user_to_imis(form):
        # Create an instance of Contact and call imis_create
        contact = Contact(
            prefix_name=form.cleaned_data.get("prefix_name", ''),
            first_name=form.cleaned_data.get("first_name", ''),
            middle_name=form.cleaned_data.get("middle_name", ''),
            last_name=form.cleaned_data.get("last_name", ''),
            suffix_name=form.cleaned_data.get("suffix_name", ''),
            email=form.cleaned_data.get("email"),
            secondary_email=form.cleaned_data.get("secondary_email", ''),
            phone=form.cleaned_data.get("phone"),
            secondary_phone=form.cleaned_data.get("secondary_phone", ''),
            cell_phone=form.cleaned_data.get("cell_phone", ''),
            birth_date=form.cleaned_data.get("birth_date"),
            member_type=form.cleaned_data.get("member_type"),
        )

        informal_name = form.cleaned_data.get("informal_name", '')
        if not informal_name:
            informal_name = contact.first_name
        imis_name = contact.imis_create(
            hint_password=form.cleaned_data.get("password_hint", ''),
            hint_answer=form.cleaned_data.get("password_answer", ''),
            informal_name=informal_name,
            member_type=form.cleaned_data.get("member_type", 'NOM')
        )
        return imis_name

    @staticmethod
    def prepare_home_address_data(form):
        country = CreateAccountFormViewMixin.get_country(form, "country")
        imis_home_address_data = {
            "address_num": form.cleaned_data.get("user_address_num", None),
            "address_1": form.cleaned_data.get("address1", ""),
            "address_2": form.cleaned_data.get("address2", ""),
            "city": form.cleaned_data.get("city", ""),
            "state_province": form.cleaned_data.get("state", ""),
            "zip": form.cleaned_data.get("zip_code", ""),
            "country": country,
            "company": form.cleaned_data.get("company", ""),
            "preferred_mail": CreateAccountFormViewMixin.is_preferred_mail(form, ImisNameAddressPurposes.HOME_ADDRESS.value),
            "preferred_bill": CreateAccountFormViewMixin.is_preferred_bill(form, ImisNameAddressPurposes.HOME_ADDRESS.value),
            "purpose": ImisNameAddressPurposes.HOME_ADDRESS.value
        }
        return imis_home_address_data

    @staticmethod
    def prepare_work_address_data(form):
        additional_country = CreateAccountFormViewMixin.get_country(form, "additional_country")
        imis_work_address_data = {
            "address_num": form.cleaned_data.get("additional_user_address_num", None),
            "address_1": form.cleaned_data.get("additional_address1", ""),
            "address_2": form.cleaned_data.get("additional_address2", ""),
            "city": form.cleaned_data.get("additional_city", ""),
            "state_province": form.cleaned_data.get("additional_state", ""),
            "zip": form.cleaned_data.get("additional_zip_code", ""),
            "country": additional_country,
            "company": form.cleaned_data.get("additional_company", ""),
        }
        return imis_work_address_data

    @staticmethod
    def get_country(form, field_name):
        country = form.cleaned_data.get(field_name, "")
        country = GEONAMES_IMIS_COUNTRY_MAPPING.get(country, country)
        return country

    @staticmethod
    def is_preferred_mail(form, purpose):
        return form.cleaned_data.get("mailing_preferences", "") == purpose

    @staticmethod
    def is_preferred_bill(form, purpose):
        return form.cleaned_data.get("billing_preferences", "") == purpose

    @staticmethod
    def post_address_data_to_imis(form, contact):

        imis_home_address_data = CreateAccountFormViewMixin.prepare_home_address_data(form)

        contact.set_imis_address_data(imis_home_address_data)
        contact.update_country_codes()

        if imis_home_address_data["address_num"]:
            contact.update_imis_address(imis_home_address_data)
        else:
            contact.create_imis_name_address(
                preferred_bill=imis_home_address_data['preferred_bill'],
                preferred_mail=imis_home_address_data['preferred_mail'],
                purpose=imis_home_address_data['purpose']
            )

        imis_work_address_data = CreateAccountFormViewMixin.prepare_work_address_data(form)

        # Don't write anything to iMIS if the user didn't enter anything
        if any(bool(x) for x in imis_work_address_data.values()):

            contact.company = imis_work_address_data["company"]
            contact.save()

            imis_work_address_data.update(
                preferred_mail=CreateAccountFormViewMixin.is_preferred_mail(form, ImisNameAddressPurposes.WORK_ADDRESS.value),
                preferred_bill=CreateAccountFormViewMixin.is_preferred_bill(form, ImisNameAddressPurposes.WORK_ADDRESS.value),
                purpose=ImisNameAddressPurposes.WORK_ADDRESS.value
            )
            if imis_work_address_data['address_num']:
                contact.update_imis_address(imis_work_address_data)
            else:
                # create a new Contact record with the additional address in order to call
                # its create_imis_name_address method but DO NOT persist it
                additional_contact = Contact()
                additional_contact.set_imis_address_data(imis_work_address_data)
                additional_contact.create_imis_name_address(
                    preferred_bill=imis_work_address_data['preferred_bill'],
                    preferred_mail=imis_work_address_data['preferred_mail'],
                    purpose=imis_work_address_data['purpose'],
                    imis_id=contact.user.username
                )


class CreateAccountFormView(CreateAccountFormViewMixin, FormView):
    """ generic FormView for creating new user accounts """
    form_class = CreateAccountForm
    template_name = ""  # implement this on inherited views
    success_url = ""  # implement this on inherited views

    def form_valid(self, form):

        # only for new accounts, check for potential duplicates (on staging/prod only)
        # if getattr(settings, 'ENVIRONMENT_NAME', 'PROD') != 'LOCAL':
        self.potential_duplicates = self.get_potential_duplicates(form)
        if self.potential_duplicates \
                and self.request.POST.get("submit", "") != "duplicate_continue":
            return self.form_invalid(form)

        imis_name = self.post_new_user_to_imis(form)

        self.contact = form.save(commit=False)

        user = User.objects.create(
            username=imis_name.id,
            first_name=imis_name.first_name,
            last_name=imis_name.last_name,
            email=imis_name.email
        )

        self.contact.user = user
        self.contact.save()

        password = self.get_password(form)
        user.set_password(password)
        user.save()

        self.post_address_data_to_imis(form, self.contact)

        self.login_user(user.username, password)

        self.after_save(form)  # hook for any additional work

        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["display_errors"] = getattr(self, "display_errors", None)
        context["potential_duplicates"] = getattr(self, "potential_duplicates", [])
        return context

    def get_password(self, form):
        return form.cleaned_data['password']

    def login_user(self, username, password):
        auto_log_user = authenticate(username=username, password=password)
        login(self.request, auto_log_user)

    def after_save(self, form):
        """hook for doing additional things after all saving is done"""
        pass


class MyapaAccountFormView(AuthenticateLoginMixin, CreateAccountFormView):
    """ View to edit basic account info in myapa """
    template_name = "myapa/newtheme/account/account-information.html"
    form_class = UpdateAccountForm
    success_url = reverse_lazy("myapa")

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["instance"] = self.request.user.contact
        return form_kwargs

    def get_initial(self):
        initial = super().get_initial()
        self.contact = self.request.user.contact

        initial.update({
            "verify_email": self.contact.email if self.contact else "",
            "secondary_verify_email": self.contact.secondary_email if self.contact else "",
            "informal_name": self.contact.informal_name if self.contact else "",
        })
        return initial

    def form_valid(self, form):
        self.update_imis_contact(form)
        self.update_harvester(form)
        form.save()
        user = self.request.user
        user.email = form.cleaned_data.get("email", "")
        user.save()

        # reindex solr speaker record
        Speaker.solr_reindex_contact(self.contact)

        return super(CreateAccountFormView, self).form_valid(form)

    def update_imis_contact(self, form):
        user_data = {
            "informal": form.cleaned_data.get("informal_name", ""),
            "birth_date": form.cleaned_data.get("birth_date", ""),
            "email": form.cleaned_data.get("email", ""),
            "email_secondary": form.cleaned_data.get("secondary_email", ""),
            "home_phone": form.cleaned_data.get("phone", ""),
            "work_phone": form.cleaned_data.get("secondary_phone", ""),
            "mobile_phone": form.cleaned_data.get("cell_phone", "")
        }
        ind_demo = self.contact.get_imis_ind_demographics()
        if ind_demo is not None:
            ind_demo.email_secondary = user_data.pop('email_secondary')
            ind_demo.save()
        name = self.contact.get_imis_name()
        name.__dict__.update(user_data)
        name.last_updated = self.contact.getdate()
        name.updated_by = 'WEBUSER'
        name.save()
        self.contact.insert_name_log_record(
            data=self.contact.make_name_log_data(
                self.contact.NAME_LOG_CHANGE_RECORD
            )
        )

    def update_harvester(self, form):
        jsonbody = [{
            "PresenterEmail": form.cleaned_data.get("email", ""),
            "PresenterTelephoneOffice": form.cleaned_data.get("secondary_phone", ""),
            "PresenterTelephoneCell": form.cleaned_data.get("cell_phone", "")
        }]
        cadmium_api_caller = CadmiumAPICaller()
        return_string = cadmium_api_caller.update_harvester_presenter(self.contact, jsonbody)
        current_or_next_conference = (NATIONAL_CONFERENCE_CURRENT[0], NATIONAL_CONFERENCE_NEXT[0])

        if next((True for cr in self.contact.contactrole.all()
                 if cr.content
                 and cr.content.parent
                 and cr.content.parent.content_live
                 and cr.content.parent.content_live.code
                 in current_or_next_conference
                 ),
                False):
            if return_string[0]:
                messages.success(self.request, return_string[1])
            else:
                messages.warning(self.request, return_string[1])

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["contact"] = self.contact
        return context


class MyapaAddressesFormView(AuthenticateLoginMixin, CreateAccountFormView):
    """ VIew to edit address infor in myapa """
    template_name = "myapa/newtheme/account/addresses.html"
    form_class = UpdateAddressesForm
    success_url = reverse_lazy("myapa")

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["instance"] = self.request.user.contact
        form_kwargs["is_individual"] = True
        return form_kwargs

    def get_initial(self):
        initial = super().get_initial()
        self.contact = self.request.user.contact
        mailing_preferences = None
        billing_preferences = None
        addresses = self.contact.get_imis_name_address()
        primary_address = home_address = addresses.filter(purpose='Home Address')
        if primary_address.count() == 1:
            primary_address = primary_address.first()
        elif primary_address.count() > 1:
            raise Http404("Error: More than one home address.")
        else:
            raise Http404("Error: No home address found.")

        secondary_address = work_address = addresses.filter(purpose='Work Address')
        if secondary_address.count() == 1:
            secondary_address = secondary_address.first()
        elif secondary_address.count() > 1:
            raise Http404("Error: More than one work address.")
        else:
            secondary_address = None
        # instead of hard-coding the school address fields...would be nice if we could just use one form
        # and submit in sequence
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
            "user_address_num": getattr(primary_address, "address_num", None),
            "address1": getattr(primary_address, "address_1", None),
            "address2": getattr(primary_address, "address_2", None),
            "city": getattr(primary_address, "city", None),
            "state": getattr(primary_address, "state_province", None),
            "zip_code": getattr(primary_address, "zip", None),
            "country": getattr(primary_address, "country", None),
            "company": getattr(primary_address, "company", None),
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

    def update_harvester(self, form):
        jsonbody = [{
            "PresenterOrganization": form.cleaned_data.get("company", ""),
            "PresenterAddress1": form.cleaned_data.get("address1", ""),
            "PresenterAddress2": form.cleaned_data.get("address2", ""),
            "PresenterCity": form.cleaned_data.get("city", ""),
            "PresenterState": form.cleaned_data.get("state", ""),
            "PresenterZip": form.cleaned_data.get("zip_code", ""),
            "PresenterCountry": form.cleaned_data.get("country", ""),
        }]
        cadmium_api_caller = CadmiumAPICaller()
        return_string = cadmium_api_caller.update_harvester_presenter(self.contact, jsonbody)
        current_or_next_conference = (NATIONAL_CONFERENCE_CURRENT[0], NATIONAL_CONFERENCE_NEXT[0])

        if next((True for cr in self.contact.contactrole.all()
                 if cr.content
                 and cr.content.parent
                 and cr.content.parent.content_live
                 and cr.content.parent.content_live.code
                 in current_or_next_conference),
                False):
            if return_string[0]:
                messages.success(self.request, return_string[1])
            else:
                messages.warning(self.request, return_string[1])

    def form_valid(self, form):
        form.save()
        self.post_address_data_to_imis(form, self.contact)
        self.update_harvester(form)

        # reindex solr speaker record
        Speaker.solr_reindex_contact(self.contact)

        return super(CreateAccountFormView, self).form_valid(form)


class PersonalInformationView(FormView):
    """ Generic FormView to update user's personal/demographics information"""
    form_class = PersonalInformationForm
    template_name = ""  # implement this on inherited class
    success_url = ""  # implement this on inherited class

    def get_initial(self):

        self.contact = self.request.user.contact
        self.demographics = self.contact.get_imis_demographics_legacy()
        if self.demographics.get('success', False):
            self.demographics = self.demographics['data']
        else:
            self.demographics = {}

        initial = super().get_initial()

        initial.update({
            "race": (self.demographics.get("race", "") or "").split(","),
            "hispanic_origin": self.demographics.get("origin", ""),
            "gender": self.demographics.get("gender", None),
            "gender_other": self.demographics.get("gender_other", None),

            "ai_an": self.demographics.get("ai_an", None),
            "asian_pacific": self.demographics.get("asian_pacific", None),
            "other": self.demographics.get("other", None),
            "span_hisp_latino": self.demographics.get("span_hisp_latino", None),

            "functional_title": self.demographics.get("functional_title", None),
            # TODO: Clarify business rules around this
            "job_title": getattr(self.contact, "job_title", None),
            "salary_range": self.get_initial_salary()
        })

        return initial

    def get_initial_salary(self):
        if self.contact.member_type == "RET":
            initial_salary = "NN" if self.contact.is_international else "N"
        elif self.contact.member_type == "LIFE":
            initial_salary = "OO" if self.contact.is_international else "O"
        else:
            initial_salary = self.demographics.get("salary_range", None)
        return initial_salary

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update({
            "instance": self.contact,
            "is_international": self.contact.is_international,
            "member_type": self.contact.member_type
        })
        return form_kwargs

    def form_valid(self, form):
        job_title = form.cleaned_data.get("job_title", "")
        self.contact = form.save(commit=False)
        if job_title:
            self.contact.job_title=job_title
        self.contact.save()
        self.post_data_to_imis(form)
        self.after_save(form)
        return super().form_valid(form)

    def post_data_to_imis(self, form):
        self.demographics.update({
            "ethnicity_noanswer": bool("NO_ANSWER" in form.cleaned_data.get("race", [])),
            "race_noanswer": bool("NO_ANSWER" in form.cleaned_data.get("race", [])),
            "origin_noanswer": bool(form.cleaned_data.get("hispanic_origin", "") == "O000"),
            "functional_title": form.cleaned_data.get("functional_title", ""),
            "salary_range": form.cleaned_data.get("salary_range", ""),
            "job_title": form.cleaned_data.get("job_title", ""),
            "ethnicity": ",".join(form.cleaned_data.get("race", [])),
            "origin": form.cleaned_data.get("hispanic_origin"),
            "gender": form.cleaned_data.get("gender", ""),
            "gender_other": form.cleaned_data.get("gender_other", ""),

            "ai_an": form.cleaned_data.get("ai_an", ""),
            "asian_pacific": form.cleaned_data.get("asian_pacific", ""),
            "ethnicity_other": form.cleaned_data.get("other", ""),
            "span_hisp_latino": form.cleaned_data.get("span_hisp_latino", ""),
        })

        if self.demographics['functional_title'] or self.demographics['job_title']:
            self.update_title()

        if self.demographics['salary_range']:
            self.update_ind_demographics()

        self.update_race_origin()

    def update_race_origin(self):
        # Can't do `get_or_create` on just the id - the table (like many in iMIS) allows
        # empty strings but not nulls...
        race_origin = imis_models.RaceOrigin.objects.filter(
            id=self.contact.user.username
        ).first()

        if race_origin is None:
            race_origin = imis_models.RaceOrigin(id=self.contact.user.username)

        race_origin.span_hisp_latino = self.demographics['span_hisp_latino']
        race_origin.origin = self.demographics['origin']
        race_origin.race = self.demographics['ethnicity']
        race_origin.ai_an = self.demographics['ai_an']
        race_origin.asian_pacific = self.demographics['asian_pacific']
        race_origin.other = self.demographics['ethnicity_other']
        race_origin.ethnicity_noanswer = self.demographics['ethnicity_noanswer']
        race_origin.origin_noanswer = self.demographics['origin_noanswer']
        race_origin.ethnicity_verifydate = self.contact.getdate()
        race_origin.origin_verifydate = self.contact.getdate()
        race_origin.save()

    def update_ind_demographics(self):
        ind_demo = self.contact.get_imis_ind_demographics()
        ind_demo.salary_range = self.demographics['salary_range']
        ind_demo.salary_verifydate = self.contact.getdate()
        ind_demo.functional_title_verifydate = self.contact.getdate()
        # TODO: Should we ask for specialty on the form?
        # ind_demo.specialty = self.demographics['']
        ind_demo.gender = self.demographics['gender']
        if ind_demo.gender == 'S':
            ind_demo.gender_other = self.demographics['gender_other']
        else:
            ind_demo.gender_other = ''
        ind_demo.save()

    def update_title(self):
        name = self.contact.get_imis_name()
        if self.demographics['functional_title']:
            name.functional_title = self.demographics['functional_title']
        if self.demographics['job_title']:
            name.title = self.demographics['job_title']
        name.save()

    def after_save(self, form):
        """hook for doing additional things after all saving is done"""
        pass


class MyapaPersonalInformationFormView(AuthenticateLoginMixin, PersonalInformationView):
    template_name = "myapa/newtheme/account/personal-information.html"
    form_class = PersonalInformationForm
    success_url = reverse_lazy("myapa")

    def get_initial_salary(self):
        self.is_new_membership_qualified = self.contact.is_new_membership_qualified

        if self.is_new_membership_qualified:
            initial_salary = "L"
        else:
            initial_salary = super().get_initial_salary()
        return initial_salary

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update({
            "is_student": self.contact.member_type in ["STU", "FSTU"],
            "is_new_membership_qualified": self.is_new_membership_qualified
        })
        return form_kwargs


class PublicProfileView(TemplateView):
    template_name = "myapa/newtheme/profile/overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contact = self.request.user.contact if self.request.user.is_authenticated() else None

        if kwargs.get('slug'):
            profile_contact = Contact.objects.filter(
                individualprofile__slug__iexact=kwargs.get('slug')
            ).select_related(
                "individualprofile"
            ).prefetch_related(
                "educationaldegree_set"
            ).prefetch_related(
                "jobhistory_set"
            ).first()

            if profile_contact is None:
                raise Http404("Contact with this profile URL not found")

            context["profile_contact"] = profile_contact
            profile_contact_addresses = profile_contact.get_imis_name_address(
                preferred_mail=True
            ).first()

            if profile_contact_addresses is not None:
                context["address_1"] = profile_contact_addresses.address_1
                context['address_2'] = profile_contact_addresses.address_2
                context['city'] = profile_contact_addresses.city
                context['state'] = profile_contact_addresses.state_province
                context['zip'] = profile_contact_addresses.zip
                context['country'] = profile_contact_addresses.country

            profile_attrs = [
                field.name for field in profile_contact.individualprofile._meta.get_fields()
            ]
            share_attrs_filter = filter(lambda attr: attr.startswith('share_'), profile_attrs)
            individual_profile_data = {}

            for individual_profile_item in share_attrs_filter:
                individual_profile_attribute = str(individual_profile_item)
                individual_profile_value = getattr(
                    profile_contact.individualprofile,
                    individual_profile_item
                )
                individual_profile_data[individual_profile_attribute] = individual_profile_value

            for key, value in individual_profile_data.items():
                if value == "PUBLIC":
                    context[str(key)] = True
                elif value == "MEMBER":
                    if self.request.user.groups.filter(name="member").exists():
                        context[str(key)] = True
                    else:
                        context[str(key)] = False
                else:
                    context[str(key)] = False
            context["view_profile"] = True

            if profile_contact:
                d = profile_contact.designation
                context["is_asc"] = d.find('CEP') >= 0 or d.find('CTP') >= 0 or d.find('CUD') >= 0
            return context
        else:
            messages.error(
                self.request,
                "The requested user profile can not be found. For questions, contact customer service at <a href='customerservice@planning.org'>customerservice@planning.org</a>."
            )
            return redirect('/myapa/')


class EditProfileView(AuthenticateLoginMixin, AppContentMixin, TemplateView):
    template_name = "myapa/newtheme/profile/edit/overview.html"
    content_url = "/myapa/profile/"

    def setup(self):
        contact = self.request.user.contact
        self.education = EducationalDegree.objects.filter(contact=contact)
        self.jobs = JobHistory.objects.filter(contact=contact).order_by("-is_current", "-end_date")
        self.resume = DocumentUpload.objects.filter(
            upload_type__code="RESUMES",
            created_by=self.request.user
        ).last()

        if self.request.method == "GET":
            advocacy_grassroots_member = getattr(
                contact.get_imis_advocacy(),
                "grassrootsmember",
                False
            )

            self.advocacy_form = AdvocacyNetworkForm(
                initial={"grassroots_member": advocacy_grassroots_member}
            )
        elif self.request.method == "POST":
            self.advocacy_form = AdvocacyNetworkForm(self.request.POST)

    def get(self, request, *args, **kwargs):
        self.setup()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contact = self.request.user.contact
        context["contact"] = contact
        context["schools"] = self.education
        context["jobs"] = self.jobs
        context["resume"] = self.resume
        context["advocacy_form"] = self.advocacy_form

        return context

    def post(self, request, *args, **kwargs):

        self.setup()

        if self.advocacy_form:
            advocacy_data = self.request.contact.get_imis_advocacy()
            if advocacy_data is None:
                advocacy_data = imis_models.Advocacy(id=self.request.user.username)
            advocacy_data.grassrootsmember = request.POST.get("grassroots_member") == "on"
            advocacy_data.save()
            messages.success(request, "Your information has been updated.")

        return redirect("/myapa/profile/")


class ResumeUploadView(AuthenticateLoginMixin, TemplateView):
    template_name = "myapa/newtheme/profile/edit/resume-upload.html"
    resume = None
    form = None

    def setup(self):
        # temporarily disabling because the spammers are marauding it
        raise Http404()

        self.resume = DocumentUpload.objects.filter(
            upload_type__code="RESUMES",
            created_by=self.request.user
        ).last()

    def get(self, request, *args, **kwargs):

        self.setup()
        self.form = ResumeUploadForm(instance=self.resume)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.setup()
        self.form = ResumeUploadForm(self.request.POST, self.request.FILES)
        resume_is_valid = self.form.is_valid()
        if resume_is_valid:
            # delete existing DocumentUpload
            if self.resume is not None:
                self.resume.delete()
            # then save the new one
            self.resume = self.form.save(commit=False)
            self.resume.created_by = self.request.user
            self.resume.save()

            profile, created = IndividualProfile.objects.get_or_create(
                contact=self.request.user.contact
            )
            profile.resume = self.resume
            profile.save()
            messages.success(self.request, "Your resume has been uploaded successfully.")
            return redirect("/myapa/profile/")
        else:
            messages.error(
                self.request,
                "There was a problem uploading your resume. Please ensure the file "
                "you are attempting to upload is in PDF format and is less than 30MB."
            )
            return redirect(reverse_lazy('resume_upload'))

    def get_context_data(self, **kwargs):
        return dict(
            form=self.form
        )


class ProfileShareView(AuthenticateLoginMixin, AppContentMixin, FormView):
    """ View for editing public profile settings """
    template_name = "myapa/newtheme/profile/edit/sharing-preferences.html"
    content_url = "/myapa/profile/"
    form_class = ProfileShareForm
    success_url = "/myapa/profile/"

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["instance"] = IndividualProfile.objects.filter(
            contact=self.request.user.contact
        ).first()
        return form_kwargs

    def form_valid(self, form):
        profile = form.save(commit=False)
        profile.contact = self.request.user.contact
        profile.save()

        Speaker.solr_reindex_contact(profile.contact)

        messages.success(self.request, "Your sharing preferences are updated")
        return super().form_valid(form)


class UpdateSocialLinksView(AuthenticateLoginMixin, FormView):
    """ View for updating personal profile links from myapa dashboard """

    template_name = "myapa/newtheme/profile/edit/social-links.html"
    form_class = UpdateSocialLinksForm
    success_url = "/myapa/"

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["instance"] = self.request.user.contact
        return form_kwargs

    def form_valid(self, form):
        self.contact = form.save()
        self.update_harvester(form)
        messages.success(self.request, "Your Social Links are updated")
        return super().form_valid(form)

    def update_harvester(self, form):
        jsonbody = [{
            "PresenterWebsite": form.cleaned_data.get("personal_url", ""),
            "PresenterLinkedIn": form.cleaned_data.get("linkedin_url", ""),
            "PresenterFacebook": form.cleaned_data.get("facebook_url", ""),
            "PresenterTwitter": form.cleaned_data.get("twitter_url", ""),
            "PresenterInstagram": form.cleaned_data.get("instagram_url", ""),
        }]
        cadmium_api_caller = CadmiumAPICaller()
        return_string = cadmium_api_caller.update_harvester_presenter(self.contact, jsonbody)
        current_or_next_conference = (NATIONAL_CONFERENCE_CURRENT[0], NATIONAL_CONFERENCE_NEXT[0])

        if next(
                (True for cr in self.contact.contactrole.all()
                 if cr.content
                    and cr.content.parent
                    and cr.content.parent.content_live
                    and cr.content.parent.content_live.code
                    in current_or_next_conference),
                False
        ):
            if return_string[0]:
                messages.success(self.request, return_string[1])
            else:
                messages.warning(self.request, return_string[1])


class UpdateBioAndAboutMe(AuthenticateLoginMixin, AppContentMixin, FormView):
    """ View for user to update personal bio and abount me from myapa dashboard """

    template_name = "myapa/newtheme/profile/edit/aboutme-bio.html"
    content_url = "/myapa/profile/"
    form_class = AboutMeAndBioUpdateForm
    success_url = "/myapa/"

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["instance"] = self.request.user.contact
        return form_kwargs

    def form_valid(self, form):
        self.contact = form.save()

        Speaker.solr_reindex_contact(self.contact)

        self.update_harvester(form)

        messages.success(self.request, "Your changes are updated successfully to your profile.")
        return super().form_valid(form)

    def update_harvester(self, form):
        jsonbody = [{
            "PresenterBiographyText": form.cleaned_data.get("bio", ""),
            "PresenterBioSketchText": form.cleaned_data.get("about_me", ""),
        }]
        cadmium_api_caller = CadmiumAPICaller()
        return_string = cadmium_api_caller.update_harvester_presenter(self.contact, jsonbody)
        current_or_next_conference = (NATIONAL_CONFERENCE_CURRENT[0], NATIONAL_CONFERENCE_NEXT[0])

        if next(
                (True for cr in self.contact.contactrole.all()
                 if cr.content
                    and cr.content.parent
                    and cr.content.parent.content_live
                    and cr.content.parent.content_live.code
                    in current_or_next_conference),
                False
        ):
            if return_string[0]:
                messages.success(self.request, return_string[1])
            else:
                messages.warning(self.request, return_string[1])


class ContactPreferencesUpdateView(AuthenticateLoginMixin, FormView):
    """ View for updating Contact preferences, i.e. What the user would like to receive email/communication about """
    template_name = "myapa/newtheme/account/contact-preferences.html"
    form_class = ContactPreferencesUpdateForm
    success_url = "/myapa/"

    def get_initial(self):

        initial = super().get_initial()

        self.contact = self.request.user.contact
        self.contact_preferences = self.contact.get_imis_mailing_demographics()
        if self.contact_preferences is None:
            self.contact_preferences = MailingDemographicsFactoryBlank(id=self.request.user.username)

        contact_preferences_list = []

        for key, value in self.contact_preferences.__dict__.items():
            if not value:
                contact_preferences_list.append(key)

        contact_preferences_list = [
            contact_preference.replace("excl", "CP").upper()
            for contact_preference in contact_preferences_list
        ]

        initial.update(
            dict(
                exclude_planning_print=self.contact_preferences.excl_planning_print,
                preferences=contact_preferences_list
            )
        )
        return initial

    def form_valid(self, form):

        excl_planning_print = form.cleaned_data.get("exclude_planning_print", False)
        preferences = form.cleaned_data.get("preferences")

        user_data = dict(
            excl_planning_print=excl_planning_print,
            excl_interact=not "CP_INTERACT" in preferences,
            excl_pas=not "CP_PAS" in preferences,
            excl_commissioner=not "CP_COMMISSIONER",
            excl_japa=not "CP_JAPA" in preferences,
            excl_planning=not "CP_PLANNING" in preferences,
            excl_zp=not "CP_ZP" in preferences,
            excl_natlconf=not "CP_NATLCONF" in preferences,
            excl_otherconf=not "CP_OTHERCONF" in preferences,
            excl_pac=not "CP_PAC" in preferences,
            excl_pan=not "CP_PAN" in preferences,
            excl_foundation=not "CP_FOUNDATION" in preferences,
            excl_learn=not "CP_LEARN" in preferences,
            excl_planning_home=not "CP_PLANNING_HOME" in preferences,
            excl_survey=not "CP_SURVEY" in preferences,
            excl_mail_list=not "CP_MAIL_LIST" in preferences
        )

        self.contact_preferences.__dict__.update(user_data)
        self.contact_preferences.save()

        # also remove them from PAN itself if they opt-out of PAN communications
        if user_data['excl_pan']:
            imis_models.Advocacy.objects.filter(id=self.request.user.username).update(grassrootsmember=False)

        messages.success(self.request, "Your contact preferences have been updated")
        return super().form_valid(form)


class EventsAttendedView(AuthenticateLoginMixin, AppContentMixin, TemplateView):
    """ View that lists past and upcoming events that this user has gone to. Accessible from myapa"""
    template_name = "myapa/newtheme/account/events-attended.html"
    content_url = "/myapa/events/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contact = self.request.user.contact

        event_purchases_qset = Purchase.objects.filter(
            contact=contact, product__product_type="EVENT_REGISTRATION"
        ).exclude(
            order__isnull=True
        ).order_by('product__content__event__begin_time')
        upcoming_events = []
        completed_events = []
        current_events = []
        for purchase in event_purchases_qset:
            purchased_event = Event.objects.get(id=purchase.product.content.id)

            if purchased_event.begin_time:

                if purchased_event.begin_time.replace(
                        tzinfo=None
                ) > timezone.now().replace(tzinfo=None):
                    upcoming_events.append(purchased_event)

                elif purchased_event.begin_time.replace(
                        tzinfo=None
                ) < timezone.now().replace(
                    tzinfo=None
                ) < purchased_event.end_time.replace(tzinfo=None):
                    current_events.append(purchased_event)

                else:
                    completed_events.append(purchased_event)

        context["completed_events"] = completed_events
        context["upcoming_event"] = upcoming_events[0] if upcoming_events else None
        context["upcoming_events"] = upcoming_events
        context["current_events"] = current_events

        return context



class EducationView(AuthenticateLoginMixin, AppContentMixin, FormView):
    """ View for user to update their education history """
    template_name = "myapa/newtheme/profile/edit/education.html"
    form_class = EducationDegreeForm
    content_url = "/myapa/profile/"
    success_url = "/myapa/education/update/"

    def setup(self):
        self.accredited_schools = imis_models.CustomSchoolaccredited.get_current_schools()

    def get(self, request, *args, **kwargs):
        self.setup()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.setup()
        return super().post(request, *args, **kwargs)

    def get_form_class(self):
        return modelformset_factory(EducationalDegree, self.form_class, extra=1)

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["queryset"] = EducationalDegree.objects.filter(
            contact=self.request.user.contact
        ).order_by("-is_current", "-graduation_date")
        form_kwargs["form_kwargs"] = {"accredited_school_choices": self.accredited_schools}
        return form_kwargs

    def form_valid(self, form):
        degrees = form.save(commit=False)
        for degree in degrees:
            degree.contact = self.request.user.contact
            degree.save()
            degree.write_to_imis()
        messages.success(self.request, "Your Education has been updated successfully!")
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["accredited_schools"] = self.accredited_schools
        return context


class JobHistoryView(AuthenticateLoginMixin, FormView):
    """ View for user to update their job history """
    template_name = "myapa/newtheme/profile/edit/jobhistory.html"
    content_url = "/myapa/profile/"
    form_class = JobHistoryUpdateForm
    job_formset = None

    def get_initial(self):
        contact = self.request.user.contact
        initial = super().get_initial()

        JobsFormSetFactory = modelformset_factory(JobHistory, JobHistoryUpdateForm, extra=1)
        self.job_formset = JobsFormSetFactory(queryset=JobHistory.objects.filter(contact=contact))

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_set"] = self.job_formset
        return context

    def post(self, request, *args, **kwargs):
        JobsFormSetFactory = modelformset_factory(JobHistory, JobHistoryUpdateForm)
        Ind_contact = IndividualContact.objects.get(user=request.user)
        posted_data = request.POST

        self.job_formset = JobsFormSetFactory(posted_data)

        if self.job_formset.is_valid():
            for job_details in self.job_formset:
                job_clean_data = job_details.cleaned_data
                # print(job_clean_data)
                if job_clean_data and job_clean_data['id'] is not None:
                    job_details.save()

                elif job_clean_data:
                    job_history_obj = JobHistory()
                    job_history_obj.contact = Ind_contact
                    job_history_obj.company = job_clean_data["company"]
                    job_history_obj.title = job_clean_data["title"]
                    job_history_obj.city = job_clean_data["city"]
                    job_history_obj.state = job_clean_data["state"]
                    job_history_obj.zip_code = job_clean_data["zip_code"]
                    job_history_obj.country = job_clean_data["country"]
                    job_history_obj.start_date = job_clean_data["start_date"]
                    job_history_obj.end_date = job_clean_data["end_date"]
                    job_history_obj.is_current = job_clean_data["is_current"]
                    job_history_obj.is_part_time = job_clean_data["is_part_time"]
                    job_history_obj.save()

            messages.success(request, "Your Job History has been updated successfully!")
            return redirect('/myapa/')

        else:
            return render(request, self.template_name, self.get_context_data(**kwargs))


class OrderHistoryView(AuthenticateLoginMixin, AppContentMixin, TemplateView):
    """
    Lists store orders (invoices & receipts) that a contact (user) has placed.
    """
    template_name = "myapa/newtheme/account/orderhistory.html"
    content_url = "/myapa/orderhistory/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # TO DO... OK to return all or should we paginate this?
        # context['orders'] = self.request.user.order_set.all().order_by('-submitted_time').
        # prefetch_related("purchase_set").prefetch_related("payment_set")

        # used for custom messages for special purposes...
        if "msg" in self.request.GET:
            messages.info(self.request, self.request.GET["msg"])

        context["orders"] = imis_models.Trans.objects.filter(
            bt_id=self.request.user.username,
            transaction_type="PAY"
        ).exclude(source_system="ORDER").order_by('-transaction_date')
        context["generic_imis_products"] = GENERIC_IMIS_PRODUCTS
        context["user"] = self.request.user
        return context


class BookmarksView(AuthenticateLoginMixin, AppContentMixin, TemplateView):
    """
    Lists areas of the site that user has bookmarked
    """
    template_name = "myapa/newtheme/account/bookmarks.html"
    content_url = "/myapa/bookmarks/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # TO DO... OK to return all or should we paginate this?
        # context['orders'] = self.request.user.order_set.all().order_by('-submitted_time').
        #       prefetch_related("purchase_set").prefetch_related("payment_set")
        context["bookmarks"] = Bookmark.objects.filter(contact=self.request.contact)
        return context


class AICPStatusView(AuthenticateLoginMixin, TemplateView):
    """ View for users to monitor their aicp candidate program status. Accessible from myapa dashboard."""

    template_name = "myapa/newtheme/account/aicp-status.html"
    contact = None
    is_candidate = False

    def get(self, request, *args, **kwargs):
        # messages.error(self.request, "We are currently conducting maintenance on this page. Your AICP "
        #                              "certification information will appear as soon as work has completed.")
        self.contact = self.request.user.contact
        self.exam = self.get_exam_info()
        return super().get(request, *args, **kwargs)

    def get_exam_info(self):

        now = timezone.now()
        candidate = False
        cand_cm_period = Period.objects.filter(code='CAND').first()
        cand_log = Log.objects.filter(
            period=cand_cm_period,
            contact=self.contact,
            status='A'
        ).first() if cand_cm_period else None

        if cand_log and now < cand_log.end_time:
            candidate = True

        # REMOVE FOR LOCAL TESTING AFTER IMIS RESTORE WIPES MY LOGIN
        aid = None
        max_score = imis_models.CustomAICPExamScore.objects.filter(
            id=self.contact.user.username).aggregate(Max('scaled_score'))
        max_score = max_score.get('scaled_score__max', None)

        if max_score:
            aid = imis_models.CustomAICPExamScore.objects.filter(
                id=self.contact.user.username,
                scaled_score=max_score).first()

        if not aid:
            max_date = imis_models.CustomAICPExamScore.objects.filter(
                id=self.contact.user.username).aggregate(Max('exam_date'))
            max_date = max_date.get('exam_date__max', None)
            if max_date:
                aid = imis_models.CustomAICPExamScore.objects.filter(
                    id=self.contact.user.username,
                    exam_date=max_date).first()

        if not aid:
            aid = imis_models.CustomAICPExamScore.objects.filter(id=self.contact.user.username).first()

        # CAN INSERT TEST VALUES HERE FROM A RECORD THAT HAS VALUES:
        # aid = imis_models.CustomAICPExamScore.objects.filter(
        #     exam_date__isnull=False,
        #     scaled_score__isnull=False).first()

        # REMOVE FOR LOCAL TESTING AFTER IMIS RESTORE WIPES MY LOGIN
        exam_date = getattr(aid, 'exam_date', "")
        scaled_score = getattr(aid, 'scaled_score', "")

        if settings.ENVIRONMENT_NAME != "PROD":
            open_water_api_caller = OpenWaterAPICaller(instance="test_instance")
        else:
            open_water_api_caller = OpenWaterAPICaller(instance="aicp_instance")

        exam_dict = dict(
            is_candidate=candidate,
            # from open water:
            cand_cert_sub_date=None,
            cand_cert_status=None,
            cand_essay_sub_date=None,
            cand_essay_status=None,
            trad_cert_sub_date=None,
            trad_cert_status=None,
            trad_essay_sub_date=None,
            trad_essay_status=None,
            exam_reg_sub_date=None,
            exam_reg_eligibility_id=None,
            exam_reg_exam_window_open=None,
            exam_reg_exam_window_close=None,
            # from imis:
            # REMOVE FOR LOCAL TESTING AFTER IMIS RESTORE WIPES MY LOGIN
            exam_date=exam_date,
            scaled_score=scaled_score
        )

        exam_dict = open_water_api_caller.get_ow_aicp_info(
            thirdPartyId=self.contact.user.username,
            info_dict=exam_dict)

        return exam_dict

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contact"] = self.contact
        context["exam"] = self.exam

        return context


def del_additional_address(request):
    if not request.user.is_authenticated:
        return redirect_to_login(next=request.get_full_path())

    contact = request.user.contact
    org_id = request.GET.get("org_id", None)

    if org_id:
        org = Organization.objects.get(user__username=org_id)
        work_address = org.get_imis_name_address(
            purpose=ImisNameAddressPurposes.WORK_ADDRESS.value)
        home_address = org.get_imis_name_address(
            purpose=ImisNameAddressPurposes.HOME_ADDRESS.value)
    else:
        work_address = contact.get_imis_name_address(
            purpose=ImisNameAddressPurposes.WORK_ADDRESS.value
        )
        home_address = contact.get_imis_name_address(
            purpose=ImisNameAddressPurposes.HOME_ADDRESS.value
        )

    home_address.update(
        preferred_mail=True,
        preferred_bill=True,
        preferred_ship=True
    )
    work_address_nums = [x.address_num for x in work_address.all()]
    if work_address_nums:
        imis_models.CustomAddressGeocode.objects.filter(
            address_num__in=work_address_nums,
            id=request.user.username
        ).delete()
    work_address.delete()

    home_address = home_address.first()
    if home_address is not None:  # this shouldn't happen, but never underestimate APA
        imis_models.Name.objects.filter(id=request.user.username).update(
            mail_address_num=home_address.address_num,
            bill_address_num=home_address.address_num,
            ship_address_num=home_address.address_num,
            address_num_1=home_address.address_num,
            address_num_2=home_address.address_num,
            address_num_3=home_address.address_num
        )

    if org_id:
        messages.success(request, "Additional Address deleted.")
    else:
        messages.success(request, "Work Address deleted.")

    return redirect(request.META.get('HTTP_REFERER'))


def generate_url(request, *args, **kwargs):
    url_text = request.GET.get("username")
    generated_url = "/profile/{}".format(url_text)

    if not IndividualProfile.objects.filter(slug=generated_url).exists():

        individual_contact = IndividualProfile.objects.get(contact=request.user.contact)
        individual_contact.slug = url_text
        individual_contact.save()

        # reindex solr speaker record
        Speaker.solr_reindex_contact(request.user.contact)

        return JsonResponse({"url": generated_url})

    else:
        messages.error(request, "The URL you entered has already been used!")
        return redirect("/myapa/profile/sharing/")
