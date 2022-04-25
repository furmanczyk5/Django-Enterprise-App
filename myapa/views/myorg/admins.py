from django.contrib import messages
from django.shortcuts import redirect, reverse
from django.utils import timezone
from django.utils.html import escape
from django.views.generic import TemplateView, View
from sentry_sdk import capture_exception

from content.mail import Mail
from imis.enums.relationship_types import ImisRelationshipTypes
from imis.models import Counter, Relationship
from imis.tests.factories.relationship import RelationshipFactoryBlank
from myapa.models.proxies import IndividualContact
from myapa.views.myorg.authentication import AuthenticateOrganizationAdminMixin


class AdminDeleteView(AuthenticateOrganizationAdminMixin, View):

    def get_email_context(self, removed_admin_username):
        removed_admin = IndividualContact.objects.only(
            'first_name', 'last_name', 'email'
        ).get(
            user__username=removed_admin_username
        )

        context = dict(
            organization=self.organization,
            removed_admin=removed_admin
        )
        return context

    def post(self, request, *args, **kwargs):
        submit_type = request.POST.get('submit', None)
        admin_username = request.POST.get('username')

        if submit_type == 'delete':
            Relationship.objects.filter(
                id=admin_username,
                target_id=self.organization.user.username
            ).delete()
            messages.success(
                request,
                'Successfully revoked admin rights from {}'.format(request.POST.get('title', ''))
            )
            context = self.get_email_context(admin_username)
            other_admins = self.organization.get_admin_contacts().exclude(user__username=admin_username)
            Mail.send(
                mail_code="MYORG_REMOVED_ADMIN_TO_REMOVED_ADMIN",
                mail_to=context["removed_admin"].email,
                mail_context=context
            )
            Mail.send(
                mail_code="MYORG_REMOVED_ADMIN_TO_OTHER_ADMINS",
                mail_to=[x.email for x in other_admins if x.email],
                mail_context=context
            )

        if admin_username == self.request.user.username:
            return redirect(reverse('myapa'))

        return redirect(reverse('myorg'))


class AdminAddView(AuthenticateOrganizationAdminMixin, View):

    def get_email_context(self, admin_username):
        new_admin = IndividualContact.objects.only(
            "first_name", "last_name", "email"
        ).get(
            user__username=admin_username
        )

        context = dict(
            new_admin=new_admin,
            organization=self.organization
        )
        return context

    def post(self, request, *args, **kwargs):
        submit_type = request.POST.get('submit', None)

        if submit_type == 'add':
            admin_username = request.POST.get('username')
            target_id = self.organization.user.username
            email = request.POST.get('email', '')
            now = timezone.now()

            existing_check = Relationship.objects.filter(
                id=admin_username,
                relation_type__in=(
                    ImisRelationshipTypes.ADMIN_I.value,
                    ImisRelationshipTypes.CM_I.value
                )
            )

            if existing_check.exists():
                if existing_check.filter(target_id=self.organization.user.username).exists():
                    messages.warning(
                        request,
                        "This individual is already an admin for your organization"
                    )
                else:
                    messages.warning(
                        request,
                        "This individual cannot be added as an administrator because "
                        "they are currently linked to another organization as an admin. "
                        "Once their current admin relationship is terminated, they can "
                        "then be added as an administrator."
                    )

            else:
                rel = RelationshipFactoryBlank(
                    id=admin_username,
                    target_id=target_id,
                    relation_type=ImisRelationshipTypes.ADMIN_I.value,
                    target_relation_type=ImisRelationshipTypes.ADMIN_C.value,
                    seqn=Counter.create_id(Relationship._meta.db_table),
                    date_added=now,
                    last_updated=now,
                    updated_by='WEBUSER'
                )

                try:
                    rel.save()
                    messages.success(
                        request,
                        "Successfully added {} as an admin for your organization.".format(
                            email
                        )
                    )
                    context = self.get_email_context(admin_username)
                    other_admins = self.organization.get_admin_contacts().exclude(user__username=admin_username)

                    Mail.send(
                        mail_code="MYORG_NEW_ADMIN_TO_NEW_ADMIN",
                        mail_to=context["new_admin"].email,
                        mail_context=context
                    )
                    Mail.send(
                        mail_code="MYORG_NEW_ADMIN_TO_OTHER_ADMINS",
                        mail_to=[x.email for x in other_admins if x.email],
                        mail_context=context
                    )
                except Exception as exc:
                    capture_exception(exc)
                    messages.error(
                        request,
                        'There was a problem attempting to add {} as an admin for '
                        'your organization. Please <a href="/customerservice/contact-us/">'
                        'contact us</a> for assistance. We apologize for the inconvenience.'.format(
                            email
                        )
                    )
        return redirect(reverse('myorg'))


class AdminSearchAutocompleteView(AuthenticateOrganizationAdminMixin, TemplateView):

    template_name = "myorg/add-org-admin.html"

    def get_context_data(self, **kwargs):
        email = self.request.GET.get('keyword', '').lower()
        is_search = self.request.GET.get('is_search', False)
        context = dict(
            email=email,
            results=[],
            results_total=0,
            is_search=is_search,
            org_name=self.organization.company,
            email_subject="APA Admin Relationship Request",
            email_body=escape("""Hello, I would like to add you as an administrator to the following organization: {}. In order to become an administrator, you must first create an APA account. Please create a new account at https://planning.org/myapa/account/create/. Once you have created your account, please let me know so that your admin account can be created. Thank you""".format(self.organization.company))
        )
        results = IndividualContact.objects.filter(email__icontains=email)
        count = results.count()
        if is_search:
            context['results'] = results
        else:
            context['results'] = results[:5]
        context['results_total'] = count
        return context
