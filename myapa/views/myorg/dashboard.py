from copy import copy
from datetime import datetime

from django.views.generic import TemplateView
from django.utils import timezone

from cm.models.providers import Provider
from cm.enums.applications import ProviderApplicationStatus
from content.models.settings import PublishStatus, ContentType, ContentStatus
from imis.enums.relationship_types import ImisRelationshipTypes
from imis.utils.labels import get_label_for_enum
from myapa.forms import ImageUploadForm
from myapa.models.constants import ContactRoleTypes, DjangoOrganizationTypes
from myapa.models.contact_role import ContactRole
from myapa.views.myorg.authentication import AuthenticateOrganizationAdminMixin
from store.models.purchase import Purchase
from store.models.settings import ProductTypes


class MyOrganizationDashboardView(AuthenticateOrganizationAdminMixin, TemplateView):

    template_name = "myapa/newtheme/organization/dashboard.html"
    all_admins = None
    provider = None
    roles = []
    upcoming_events = []
    recent_events = []
    jobs = []
    purchases = []
    partners = []
    profile = None

    exclude_event_types = ("ACTIVITY", "LEARN_COURSE", "LEARN_COURSE_BUNDLE")

    def setup(self):
        self.provider = copy(self.organization)
        self.provider.__class__ = Provider
        self.profile = getattr(self.organization, "organizationprofile", None)

        self.roles = []
        self.set_org_roles()

        self.recent_events = []
        self.upcoming_events = []
        self.set_org_events()

        self.jobs = []
        self.set_org_jobs()

        self.purchases = []
        self.set_org_purchases()

        self.partners = []
        self.set_org_partners()

    def get(self, request, *args, **kwargs):
        self.setup()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        self.all_admins = self.organization.get_admin_contacts().order_by('last_name')

        org_type = get_label_for_enum(DjangoOrganizationTypes, self.organization.organization_type)

        app_label = None
        app_expiration_date = None
        most_recent_app = self.get_most_recent_provider_application()
        if most_recent_app is not None:
            app_label = get_label_for_enum(ProviderApplicationStatus, most_recent_app.status)
            app_expiration_date = most_recent_app.end_date

        registrations = self.get_registrations()

        context = dict(
            org_admin=self.request.user.contact,
            company=self.organization.company or '',
            logo_image_form=ImageUploadForm(),
            user_is_cm_admin=self.user_is_cm_admin,
            org_admin_type_label=self.get_org_admin_type_label(),
            all_admins=self.all_admins,
            org_type=org_type,
            ein_number=self.get_ein_number(),
            org_purchases=self.purchases[:3],
            org=self.organization,
            most_recent_app=most_recent_app,
            most_recent_active_app=self.get_most_recent_approvied_application(),
            app_label=app_label,
            app_expiration_date=app_expiration_date,
            rating_stats=self.provider.get_rating_stats(),
            upcoming_events=self.upcoming_events[:3],
            recent_events=self.recent_events[:3],
            provider=self.provider,
            partners=sorted([x.company for x in self.partners][:3]),
            partner_count=self.partners.count(),
            jobs=self.jobs[:3],
            profile=self.profile,
            registrations_initial=registrations[:3],
            most_recent_registration=registrations[:1],
        )
        if registrations.count() >= 3:
            context['registrations_remaining'] = registrations[3:]

        return context

    def get_most_recent_provider_application(self):
        return self.organization.applications.order_by('-end_date').first()

    def get_most_recent_approvied_application(self):
        return self.provider.applications.filter(status='A').order_by('-end_date').first()

    def get_registrations(self):
        return self.provider.registrations.order_by('-year')

    def set_org_partners(self):
        self.partners = self.provider.partner_providers() or Provider.objects.none()

    def get_ein_number(self):
        """
        Get 5 asterisks plus the last 4 digits of an organization's EIN number.
        Returns 9 asterisks if the organization does not have an EIN number set
        :return:
        """
        if not self.organization.ein_number:
            return '*' * 9
        else:
            return '*' * 5 + self.organization.ein_number[-4:]

    def get_org_admin_type_label(self):
        if self.user_is_admin and not self.user_is_cm_admin:
            return ImisRelationshipTypes.ADMIN_I_LABEL.value
        elif self.user_is_cm_admin:
            return ImisRelationshipTypes.CM_I_LABEL.value

    def set_org_purchases(self):
        self.purchases = self.get_org_purchases()

    def get_org_purchases(self):
        """
        Get the most recent Organization purchases
        :return: :class:`django.db.models.query.QuerySet`
        """
        org_purchases = Purchase.objects.select_related(
            'order'
        ).select_related(
            'product'
        ).filter(
            contact_recipient=self.organization,
            product__product_type__in=(
                ProductTypes.CM_REGISTRATION.value,
                ProductTypes.CM_PER_CREDIT.value
            ),
            order__isnull=False
        ).order_by(
            '-order__submitted_time'
        )

        [setattr(x,
                 "product_type_label",
                 get_label_for_enum(ProductTypes, x.product.product_type)
                 )
            for x in org_purchases]
        return org_purchases

    def set_org_events(self, maximum=1000):
        """
        Set the events associated with this Organization
        :param maximum: The maximum number of events to fetch, as a safeguard
        :return: None
        """
        now = timezone.now()

        for role in self.roles.filter(
            content__event__publish_status=PublishStatus.PUBLISHED.value,
            content__event__archive_time__gt=now,
            role_type=ContactRoleTypes.PROVIDER.value
        ).exclude(
            content__event__event_type__in=self.exclude_event_types
        )[:maximum]:
            event = getattr(role.content, 'event', None)
            begin_time = getattr(event, 'begin_time', None)
            if isinstance(begin_time, datetime) and begin_time > now:
                self.upcoming_events.append(role.content.event)
            else:
                self.recent_events.append(role.content.event)

        if self.upcoming_events:
            self.upcoming_events.sort(key=lambda x: x.begin_time)

        if self.recent_events:
            self.recent_events.sort(key=lambda x: x.end_time, reverse=True)

    def set_org_roles(self):
        self.roles = ContactRole.objects.filter(
            contact=self.organization,
            content__isnull=False,
        ).select_related(
            "content__event",
            "content__event__master",
            "content__job",
            "content__job__master"
        ).order_by(
            "-content__master"
        )

    def set_org_jobs(self):
        self.jobs = self.roles.filter(
            content__content_type=ContentType.JOB.value,
            content__job__publish_status=PublishStatus.PUBLISHED.value,
            content__job__status=ContentStatus.ACTIVE.value,
            content__make_inactive_time__gt=timezone.now()
        )
        for job in self.jobs:
            purchase = Purchase.objects.select_related(
                "order"
            ).filter(
                content_master=job.content.master
            ).first()

            setattr(job, "purchase", purchase)
