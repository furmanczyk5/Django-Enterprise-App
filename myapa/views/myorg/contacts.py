from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import FormView

from myapa.forms.account import UpdateOrgAccountForm
from myapa.models.constants import MyOrgMessages
from myapa.views.myorg.authentication import AuthenticateOrganizationAdminMixin


class MyOrganizationContactsView(AuthenticateOrganizationAdminMixin, FormView):
    template_name = "myorg/account-information.html"
    form_class = UpdateOrgAccountForm
    success_url = reverse_lazy("myorg")

    def get_initial(self):
        initial = super().get_initial()
        initial.update(dict(
            verify_email=self.organization.email,
            secondary_verify_email=self.organization.secondary_email
        ))
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(dict(
            org=self.organization
        ))
        return context

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["instance"] = self.organization
        return form_kwargs

    def form_valid(self, form):
        form.save()

        imis_name = self.organization.get_imis_name()
        if imis_name is not None:
            imis_name.email = form.cleaned_data.get("email", '')
            imis_name.work_phone = form.cleaned_data.get("secondary_phone", '')
            imis_name.website = form.cleaned_data.get("personal_url", '')
            imis_name.save()

        secondary_email = form.cleaned_data.get("secondary_email", '')
        if secondary_email:
            imis_ind_demo = self.organization.get_imis_ind_demographics()
            if imis_ind_demo is not None:
                imis_ind_demo.email_secondary = secondary_email
                imis_ind_demo.save()
        messages.success(
            self.request,
            MyOrgMessages.CONTACT_INFO_CHANGE_SUCCESS.value
        )
        return super(MyOrganizationContactsView, self).form_valid(form)
