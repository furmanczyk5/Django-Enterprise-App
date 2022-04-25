from django.contrib import messages
from django.http import Http404
from django.urls import reverse_lazy
from django.views.generic import FormView

from imis.enums.members import ImisNameAddressPurposes
from myapa.forms.account import UpdateOrgAddressesForm
from myapa.models.constants import MyOrgMessages
from myapa.views.account import CreateAccountFormViewMixin
from myapa.views.myorg.authentication import AuthenticateOrganizationAdminMixin


class MyOrganizationAddressesView(AuthenticateOrganizationAdminMixin, FormView):

    template_name = "myorg/addresses.html"

    form_class = UpdateOrgAddressesForm

    success_url = reverse_lazy("myorg")

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["instance"] = self.organization
        form_kwargs["is_individual"] = False
        return form_kwargs

    def get_initial(self):
        mailing_preferences = None
        billing_preferences = None
        self.contact = self.request.user.contact
        org_address = self.organization.get_imis_name_address().all()
        # primary_address, secondary_address = None, None
        # for addr in org_address:
        #     if addr.preferred_mail:
        #         primary_address = addr
        #     elif not addr.preferred_mail:
        #         secondary_address = addr
        primary_address = org_address.filter(purpose='Home Address')
        if primary_address.count() == 1:
            primary_address = primary_address.first()
        elif primary_address.count() > 1:
            raise Http404("Error: More than one primary address.")
        else:
            # primary_address = None
            raise Http404("Error: No primary address found.")

        secondary_address = org_address.filter(purpose='Work Address')
        if secondary_address.count() == 1:
            secondary_address = secondary_address.first()
        elif secondary_address.count() > 1:
            raise Http404("Error: More than one secondary address.")
        else:
            secondary_address = None

        initial = {}
        if primary_address is not None:
            initial = primary_address.as_django_form_initial()
        if secondary_address is not None:
            initial.update(
                secondary_address.as_django_form_initial(additional=True)
            )
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
            "home_preferred_mail": getattr(primary_address, "preferred_mail", None),
            "home_preferred_bill": getattr(primary_address, "preferred_bill", None),
            "work_preferred_mail": getattr(secondary_address, "preferred_mail", None),
            "work_preferred_bill": getattr(secondary_address, "preferred_bill", None),
        })

        return initial

    def form_valid(self, form):
        form.save()
        CreateAccountFormViewMixin.post_address_data_to_imis(form, self.organization)

        # Do we need to do anything Cadmium Harvester-related here?

        messages.success(
            self.request,
            MyOrgMessages.ADDRESS_CHANGE_SUCCESS.value
        )
        return super(MyOrganizationAddressesView, self).form_valid(form)
