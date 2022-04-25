from django.contrib import messages
from django.shortcuts import redirect, render, reverse
from django.views.generic import View
from sentry_sdk import capture_message

from myapa.forms.organization import OrgLogoForm, EmployerBioForm, OrgBioForm
from myapa.models.profile import OrganizationProfile
from myapa.views.myorg.authentication import AuthenticateOrganizationAdminMixin


class OrgLogoView(AuthenticateOrganizationAdminMixin, View):

    form_class = OrgLogoForm
    profile = None
    template_name = "myorg/logo-update.html"

    def get(self, request, *args, **kwargs):
        self.profile = getattr(self.organization, "organizationprofile", None)
        form = self.form_class(instance=self.profile)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            imageupload = form.save(commit=False)
            imageupload.created_by = self.request.user
            imageupload.save()
            profile, _ = OrganizationProfile.objects.get_or_create(
                contact=self.organization
            )
            profile.image = imageupload
            profile.save()
            messages.success(
                request,
                "Successfully updated your logo."
            )
        else:
            messages.error(
                request,
                "There was a problem uploading your logo. Please ensure it is an image "
                "file in JPG, GIF, or PNG format."
            )
        return redirect(reverse("myorg"))


class OrgLogoDeleteView(AuthenticateOrganizationAdminMixin, View):

    def get(self, request, *args, **kwargs):

        profile = OrganizationProfile.objects.filter(contact=self.organization).first()
        if profile is not None:
            if profile.image:
                profile.image.delete()
                messages.success(self.request, "Successfully removed your organization's logo")
        return redirect(reverse('myorg'))


class OrgBioView(AuthenticateOrganizationAdminMixin, View):

    form_class = OrgBioForm
    template_name = "myorg/org-bio.html"

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=dict(bio=self.organization.bio))
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):

        form = self.form_class(request.POST)
        if form.is_valid():
            self.organization.bio = form.cleaned_data.get('bio')
            self.organization.save()

            messages.success(
                request,
                "Successfully updated your organization bio."
            )
        else:
            # Could this ever happen with a form of just a TextField that allows nulls/blanks?
            capture_message(
                "Error updating employer bio for {}".format(self.organization.title),
            )
            messages.error(
                request,
                "Something went wrong trying to update your organization bio"
            )
        return redirect("myorg")


class OrgEmployerBioView(AuthenticateOrganizationAdminMixin, View):

    profile = None
    form_class = EmployerBioForm
    template_name = "myorg/employer-bio.html"

    def get(self, request, *args, **kwargs):
        self.profile = getattr(self.organization, "organizationprofile", None)
        if self.profile is not None:
            form = self.form_class(
                initial=dict(employer_bio=self.profile.employer_bio)
            )
        else:
            form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):

        form = self.form_class(request.POST)
        if form.is_valid():
            profile, _ = OrganizationProfile.objects.get_or_create(
                contact=self.organization
            )
            profile.employer_bio = form.cleaned_data.get('employer_bio')
            profile.save()

            messages.success(
                request,
                "Successfully updated your employer bio."
            )
        else:
            capture_message(
                "Error updating employer bio for {}".format(self.organization.title)
            )
            messages.error(
                request,
                "Something went wrong trying to update your employer bio"
            )
        return redirect("myorg")
