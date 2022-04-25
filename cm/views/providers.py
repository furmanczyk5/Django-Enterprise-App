import datetime
import re

import pytz
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Q, Avg, Count
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView, View, FormView

from cm.enums.applications import ProviderApplicationStatus, ProviderApplicationReviewStatus
from cm.forms import ProviderApplicationForm, ProviderEventSearchFilterForm, \
    ProviderRegistration2015Form, ProviderRegistrationForm, \
    ProviderNewRegistrationForm, ProviderLogoUploadForm, ProviderApplicationReviewForm, \
    ProviderApplicationReturningForm
from cm.models import Provider, ProviderApplication, PROVIDER_APPLICATION_YEAR
from comments.models import Comment
from content.mail import Mail
from content.models import MessageText
from content.viewmixins import AppContentMixin
from events.models import Event, EVENT_TYPES
from events.viewmixins import AuthenticateProviderMixin
from imis.enums.relationship_types import ImisRelationshipTypes
from myapa.models.contact import Contact
from myapa.models.contact_relationship import ContactRelationship
from myapa.models.contact_role import ContactRole
from myapa.models.profile import OrganizationProfile
from myapa.models.constants import DjangoContactTypes
from myapa.tasks import org_dupe_check
from myapa.viewmixins import AuthenticateLoginMixin
from myapa.views.myorg.authentication import AuthenticateOrganizationAdminMixin
from store.models import ProductOption, Purchase, ProductCart


class ProviderApplicationView(AuthenticateOrganizationAdminMixin, AppContentMixin, FormView):
    template_name = "cm/newtheme/provider/application-form.html"
    form_class = ProviderApplicationForm
    content_url = "/cm/activities/regprocess/"
    is_strict = False
    application = None
    provider = None

    def setup(self):
        self.provider = self.organization
        application_id = self.kwargs.get("application_id", None)
        if application_id:
            self.application = get_object_or_404(
                ProviderApplication,
                provider=self.provider,
                id=application_id,
                status__in=(
                    ProviderApplicationStatus.DEFERRED.value,
                    ProviderApplicationStatus.INCOMPLETE.value
                )
            )

        self.is_strict = self.request.POST.get("submit", "continue") != "continue_later"

    def get(self, request, *args, **kwargs):
        self.setup()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.setup()
        return super().post(request, *args, **kwargs)

    def get_form_class(self):
        if self.application and self.application.review_status:
            return ProviderApplicationReturningForm
        else:
            return super().get_form_class()

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        form_kwargs["instance"] = self.application
        form_kwargs["is_strict"] = self.is_strict
        return form_kwargs

    def form_valid(self, form):
        self.application = form.save(commit=False)
        self.application.provider = self.provider
        self.application.status = ProviderApplicationStatus.INCOMPLETE.value
        self.application.save()

        return super().form_valid(form)

    def get_success_url(self, *args, **kwagrs):
        if self.is_strict:
            return reverse("cm:provider_application_review", kwargs=dict(application_id=self.application.id))
        else:
            return reverse("myorg")

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["provider"] = self.organization
        context["application"] = self.application
        return context


class ProviderApplicationSubmissionReviewView(
    AuthenticateOrganizationAdminMixin, AppContentMixin, FormView
):
    template_name = "cm/newtheme/provider/application-review.html"
    form_class = ProviderApplicationReviewForm
    content_url = "/cm/activities/regprocess/"
    provider = None
    application = None

    def setup(self):
        application_id = self.kwargs.get("application_id")
        self.provider = self.organization
        self.application = get_object_or_404(
            ProviderApplication,
            provider=self.provider,
            status__in=(
                ProviderApplicationStatus.DEFERRED.value,
                ProviderApplicationStatus.INCOMPLETE.value
            ),
            id=application_id
        )

    def get(self, request, *args, **kwargs):
        self.setup()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.setup()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        self.application.status = ProviderApplicationStatus.SUBMITTED.value
        self.application.submitted_time = timezone.now()
        if self.application.review_status == ProviderApplicationReviewStatus.DUE.value:
            self.application.review_status = ProviderApplicationReviewStatus.REVIEWING.value
        self.application.save()

        for administrator in self.organization.get_admin_contacts():
            Mail.send('PROVIDER_APPLICATION_SUCCESSFUL_SUBMIT', administrator.email)

        return super().form_valid(form)

    def get_success_url(self, *args, **kwagrs):
        return reverse("cm:provider_application_confirm", kwargs=dict(application_id=self.application.id))

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["provider"] = self.provider
        context["application"] = self.application
        return context


class ProviderApplicationSubmissionConfirmationView(AuthenticateProviderMixin, AppContentMixin, TemplateView):
    template_name = "cm/newtheme/provider/application-success.html"
    content_url = "/cm/activities/regprocess/"


class ProviderPastApplicationView(AuthenticateProviderMixin, AppContentMixin, TemplateView):
    template_name = "cm/newtheme/provider/application-details.html"
    content_url = "/cm/activities/regprocess/"
    application = None

    def get(self, request, *args, **kwargs):
        application_id = kwargs.get("application_id")
        self.application = get_object_or_404(ProviderApplication, id=application_id)
        if self.application.provider_id == self.provider.id:
            return super().get(request, *args, **kwargs)
        else:
            messages.error(request, "You do not have permission to view this applicaton.")
            return reverse("cm:provider_dashboard")

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["application"] = self.application
        return context


def redirect_to_myorg(request):
    """View for redirecting to /myorg/"""
    return HttpResponseRedirect(reverse_lazy('myorg'))




class ProviderEventComments(AuthenticateProviderMixin, View):
    """
    View that renders a list of comments for an event
    """
    template_name = "cm/newtheme/provider/includes/event-comments.html"
    error_message = "You must be an administrator to view these comments. Please make sure that you are logged in."

    def set_content(self, request, *args, **kwargs):
        event_master_id = kwargs.get("event_master_id", None)
        self.content = Event.objects.filter(master__id=event_master_id, publish_status="DRAFT")
        self.comments = Comment.objects.select_related("content__event").filter(is_deleted=False).filter(Q(content__master_id=event_master_id) | Q(content__parent_id=event_master_id)).order_by("content__event__begin_time", "submitted_time")

        self.breakdown = {"r_0":0, "r_1":0, "r_2":0,"r_3":0, "r_4":0, "r_5":0}
        self.comments_w_commentary = []
        for comment in self.comments:
            if comment.rating and comment.rating >= 0 and comment.rating <= 5:
                self.breakdown["r_%s" % comment.rating] += 1
                if comment.commentary and comment.commentary.strip():
                    self.comments_w_commentary.append(comment)


    def dispatch(self, request, *args, **kwargs):
        if self.authenticate(request, *args, **kwargs) is not None:
            return render(request, self.template_name, {"error_message":self.error_message})
        return render(request, self.template_name, {"comments":self.comments_w_commentary, "event":self.content, "breakdown":self.breakdown, "total":len(self.comments)})





class ProviderSearchView(AppContentMixin, TemplateView):
    """
    View for searching for providers
    """
    content_url = "/cm/"
    template_name = "cm/newtheme/provider-search.html"
    title = "CM Provider Search"

    def get(self, request, *args, **kwargs):

        self.keyword = keyword = request.GET.get("keyword", "")
        q_args = []
        if keyword:
            q_args.append( Q(title__icontains=keyword) | Q(country__icontains=keyword) | Q(state__icontains=keyword) | Q(city__icontains=keyword) )

        self.providers = Provider.objects.filter(*q_args).order_by('title').exclude(status='H')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context["title"] = "CM Provider Search"
        context["providers"] = self.providers
        context["provider_search"] = {
            "keyword":self.keyword
        }
        return context


class ProviderDetails(TemplateView):
    """
    For Viewing Provider Profile and the Provider's events
    """
    template_name = "cm/newtheme/provider/details.html"
    rows = 50

    def get(self, request, *args, **kwargs):

        provider_id = kwargs.get("provider_id", None)

        # for filtering number of results
        self.page = int(request.GET.get("page", 0))
        self.start = self.page * self.rows
        self.end = self.start + self.rows

        try:
            self.provider = Provider.objects.annotate(rating_average=Avg("content__comments__rating"), rating_count=Count("content__comments__rating")).get(id=provider_id)
        except Provider.DoesNotExist:
            raise Http404

        provider_roles = ContactRole.objects.select_related("content","content__event").filter(content__content_type="EVENT", contact=self.provider, role_type="PROVIDER", content__publish_status="PUBLISHED").order_by("-content__event__begin_time")

        # pagination_stuff
        self.total = provider_roles.count()
        self.previous_page = "{0}?page={1}".format(request.path, self.page - 1) if self.page != 0 else None
        self.next_page = "{0}?page={1}".format(request.path, self.page + 1) if (self.end) < self.total else None

        self.provider_roles = provider_roles[self.start:self.end]

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.provider.title
        context["provider"] = self.provider
        context["rating_stats"] = self.provider.get_rating_stats()
        context["provider_roles"] = self.provider_roles
        context["previous_page"] = self.previous_page
        context["next_page"] = self.next_page
        context["total"] = self.total
        context["start"] = self.start + 1
        context["end"] = min(self.end, self.total)
        return context


class ProviderCommentsView(TemplateView):
    """DEVELOPMENT IN PROCESS"""
    template_name = "cm/newtheme/provider/comments.html"
    rows = 50

    def get(self, request, *args, **kwargs):

        master_id = kwargs.get("master_id", None)
        provider_id = kwargs.get("provider_id", None)
        page = int(request.GET.get("page", 0))

        self.start = page * self.rows
        self.end = self.start + self.rows

        # either master_id or provider_id should be passed
        if master_id:
            self.event = Event.objects.filter(master_id=master_id, publish_status="PUBLISHED").first()
            self.provider = next((cr.contact for cr in self.event.contactrole.all() if cr.role_type == "PROVIDER"), None)
            all_comments = Comment.objects.filter(is_deleted=False, content__master_id=master_id, content__parent_id=master_id, rating__range=[0,5]).select_related("content__event").distinct().order_by("-submitted_time")
        elif provider_id:
            self.provider = Provider.objects.filter(id=provider_id).first()
            all_comments = Comment.objects.filter(is_deleted=False, content__contactrole__contact_id=provider_id, content__parent__content__contactrole__contact_id=provider_id, rating__range=[0,5]).select_related("content__event").distinct().order_by("-submitted_time")

        self.stats = all_comments.aggregate(
            rating_avg=Avg("rating"),
            rating_total=Count("rating")
        )

        # Why doesn't this work????
        # breakdown = all_comments.values("rating").annotate(rating_count=Count("rating"))
        # print(breakdown)
        # print(all_comments.count())
        # self.stats["rating_breakdown"] = {
        #     "r_0":next((b["rating_count"] for b in breakdown if b["rating"] == 0), 0),
        #     "r_1":next((b["rating_count"] for b in breakdown if b["rating"] == 1), 0),
        #     "r_2":next((b["rating_count"] for b in breakdown if b["rating"] == 2), 0),
        #     "r_3":next((b["rating_count"] for b in breakdown if b["rating"] == 3), 0),
        #     "r_4":next((b["rating_count"] for b in breakdown if b["rating"] == 4), 0),
        #     "r_5":next((b["rating_count"] for b in breakdown if b["rating"] == 5), 0)
        # }

        self.stats["rating_breakdown"] = {
            "r_0":all_comments.filter(rating=0).count(),
            "r_1":all_comments.filter(rating=1).count(),
            "r_2":all_comments.filter(rating=2).count(),
            "r_3":all_comments.filter(rating=3).count(),
            "r_4":all_comments.filter(rating=4).count(),
            "r_5":all_comments.filter(rating=5).count()
        }

        visible_comments = all_comments.filter(publish=True).exclude(commentary__isnull=True).exclude(commentary__exact="")
        self.paginated_comments = visible_comments[self.start:self.end]

        self.total = visible_comments.count()
        self.previous_page = "{0}?page={1}".format(request.path, page - 1) if page != 0 else None
        self.next_page = "{0}?page={1}".format(request.path, page + 1) if (self.end) < self.total else None

        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["event"] = getattr(self, "event", None) # for displaying specific events
        context["provider"] = getattr(self, "provider", None)
        context["comments"] = self.paginated_comments
        context["stats"] = self.stats

        context["previous_page"] = self.previous_page
        context["next_page"] = self.next_page
        context["total"] = self.total
        context["start"] = self.start + 1
        context["end"] = min(self.end, self.total)

        return context


class ProviderRegistrationView(AuthenticateProviderMixin, TemplateView):
    context = {}
    provider = None
    registration_form_class = ProviderRegistrationForm
    default_year = PROVIDER_APPLICATION_YEAR # remove this
    registration_form_obj = None
    template_name = "cm/newtheme/provider/registration-form.html"
    active_providers_only = True
    product_code = "CM_PROVIDER_REGISTRATION"

    registration_choices = [
        "CM_UNLIMITED_SMALL",
        "CM_UNLIMITED_MEDIUM",
        "CM_UNLIMITED_LARGE",
        "CM_UNLIMITED_LARGEST",
    ]

    # NOTE... assume provider cannot re-register?

    def setup(self, request, *args, **kwargs):
        # TO DO: don't hard-code 2016
        # if self.provider:
        available_registration_years = self.provider.available_registration_years()

        if self.provider.partner_registration_eligible():
            self.registration_choices.append('CM_UNLIMITED_PARTNER')

        self.registration_form_obj = self.registration_form_class(
            request.POST or None,
            initial={"provider": self.provider, "year": self.default_year},
            years_choices=[(y, y) for y in available_registration_years],
            registration_choices=self.registration_choices
        )
        self.context["provider_name"] = self.provider.company


        # else:
        #     self.template_name = ("/cm/templates/cm/non_provider_registration.html")
        #     return self.render_template(request)
        # self.claim_form_obj.fields["contact"] = self.contact
        # print("---------------------------------")
        # print(dir(self.claim_form_obj))
        # TO DO... set comments form here...

    def get(self, request, *args, **kwargs):
        self.setup(request, *args, **kwargs)
        provider_app_qset = ProviderApplication.objects.filter(provider=self.provider, status='A')
        if provider_app_qset.count() == 0:
            self.template_name = "cm/newtheme/provider/application-no-submitted-records.html"

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.setup(request, *args, **kwargs)

        if not self.registration_form_obj.is_valid():
            messages.error(
                request,
                "Your registration could not be processed. Please check that "
                "you have completed all required fields."
            )
        else:
            instance = self.registration_form_obj.save()

            provider_approved_through_year = self.provider.application_approved_through_year()
            if (not provider_approved_through_year) or (provider_approved_through_year < instance.year):
                messages.error(
                    request,
                    "Your registration could not be processed because you do "
                    "not have an approved application for the selected "
                    "registration period."
                )
            else:

                product = ProductCart.objects.get(code=self.product_code)
                product_option = ProductOption.objects.get(
                    code=instance.registration_type,
                    product=product
                )

                purchase = product.add_to_cart(
                    contact=self.request.contact,
                    company_contact_id=self.provider.user.username,
                    provider=self.provider,
                    product=product,
                    option=product_option
                )
                # TO DO... prevent saving twice?
                instance.is_unlimited = True
                instance.status = "P"
                instance.purchase = purchase
                instance.save()
                return redirect("/store/cart/")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["registration_form"] = self.registration_form_obj
        context["provider"] = self.provider # necessary?
        return context


class ProviderRegistration2015View(ProviderRegistrationView):
    """
    view for the 2015 provider registration form... has slightly different form and
    logic on the post (including different product/options)
    """
    registration_form_class = ProviderRegistration2015Form
    default_year = 2015
    product_code = "CM_PROVIDER_ANNUAL_2015"


class ProviderNewRecord(AuthenticateLoginMixin, FormView):

    template_name = "cm/newtheme/provider/new-record.html"
    form_class = ProviderNewRegistrationForm
    org_django = None
    org_imis = None

    def authenticate(self, request, *args, **kwargs):
        authentication_response = super().authenticate(request, *args, **kwargs)
        if authentication_response is not None:
            return authentication_response
        else:
            # user can only be admin of one organization at a time
            relationship = self.request.user.contact.get_imis_source_relationships().filter(
                relation_type__in=(
                    ImisRelationshipTypes.ADMIN_I.value,
                    ImisRelationshipTypes.CM_I.value
                )
            ).last()
            if relationship is not None:
                org = Contact.objects.filter(user__username=relationship.target_id).first()
                return render(
                    request,
                    "myorg/existing-admin.html",
                    dict(org=org)
                )

    def form_valid(self, form):
        self.org_django = form.save(commit=False)
        self.org_django.contact_type = DjangoContactTypes.ORGANIZATION.value
        self.org_imis = self.org_django.imis_create(org_type=self.org_django.organization_type)

        # prevent dupes
        # Contact.update_or_create_from_imis will create a duplicate Contact
        # record if the related User doesn't exist yet
        user = User.objects.create(username=self.org_imis.id)

        self.org_django.user = user
        self.org_django.save()
        self.org_django = Contact.update_or_create_from_imis(self.org_imis.id)
        self.request.user.contact.create_imis_relationship(
            co_id=self.org_imis.id,
            relation_type=ImisRelationshipTypes.ADMIN_I.value
        )

        org_dupe_check.delay(self.org_django, self.request.user.contact)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('cm:provider_application_new')


class SpeakerConfirmRole(AuthenticateLoginMixin, TemplateView):
    """
    View for speakers to confirm speaker roles for cm events
    """

    template_name = "cm/newtheme/speaker-confirmation.html"

    def get(self, request, *args, **kwargs):

        try:


            self.contact = contact = Contact.objects.get(user__username=self.username)
            contact_role = ContactRole.objects.select_related("contact", "content").get(id=kwargs.get("contact_role_id"))
            old_contact = contact_role.contact # should only be different if an ANNONYMOUS RECORD WAS CREATED

            # contacts are no longer anonymous... how to treat this check?
            if old_contact == contact or str.startswith(old_contact.user.username, "A"):


                if not contact_role.confirmed:

                    # confirm for all versions of this event
                    ContactRole.objects.filter(content__master_id=contact_role.content.master_id).update(confirmed=True)

                    if str.startswith(old_contact.user.username, "A"):

                        # update all old_contact roles with confirmed contact
                        ContactRole.objects.filter(contact=old_contact).update(contact=contact)
                        # delete temp record
                        old_contact.delete()

                self.is_success = True
                self.message = "Thank you for confirming your participation in \"%s.\" Please update your personal bio." % contact_role.content

            else:
                self.is_success = False
                self.message = "Failed to confirm participation in \"%s.\" Please verify with the organizer that you are listed as a speaker for this session." % contact_role.content
        except ContactRole.DoesNotExist:
            self.is_success = False
            self.message = "This link does not match any speaker records in our database. Please verify with the organizer that you were not removed from this activity. Please contact customer service for assistance."
        except Contact.DoesNotExist:
            self.is_success = False
            self.message = "Your contact information could not be loaded. Please contact customer service for assistance."

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        self.contact = contact = Contact.objects.get(user__username=self.username)

        new_bio = request.POST.get("bio", contact.bio)

        if new_bio:
            contact.bio = request.POST.get("bio", contact.bio)
            contact.save()

            messages.success(request, "Thank you for updating your bio!")
        else:
            messages.error(request, "Bio: This field is required.")

        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_success"] = self.is_success
        context["contact"] = self.contact
        context["message"] = self.message
        return context

