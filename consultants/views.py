from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse_lazy
from django.forms.models import modelformset_factory
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone
from django.utils.encoding import force_text
from django.views.generic import TemplateView, FormView

from content.mail import Mail
from content.models import Tag, TagType
from content.viewmixins import AppContentMixin
from content.views import LandingSearchView
from myapa.models.contact_relationship import ContactRelationship
from myapa.models.contact_role import ContactRole
from myapa.models.contact_tag_type import ContactTagType
from myapa.models.profile import OrganizationProfile
from myapa.viewmixins import AuthenticateLoginMixin, \
    AuthenticateContactRoleMixin
from submissions.views import SubmissionEditFormView, SubmissionReviewFormView
from uploads.models import UploadType, ImageUpload
from .forms import BranchOfficeForm, OrganizationProfileForm, ConsultantForm, \
    RFPSubmissionEditForm, RFPSubmissionVerificationForm, RFPSearchFilterForm
from .models import RFP, Consultant, BranchOffice


#######################################
# ############ CONSULTANTS ########## #
#######################################

def branch_delete(request, **kwargs):

    branch_id = request.GET.get("branch_id", False)
    # print("branch_id is: ", branch_id)

    if branch_id:
        branch = BranchOffice.objects.get(id=branch_id)
        branch.delete()
        messages.success(request,"The branch office has been removed")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if not branch_id:
        messages.error(request,"You can't remove an empty branch office.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class ConsultantDashboard(AuthenticateLoginMixin, TemplateView):
    """
    Dashboard to enter creating/editing a consultant profile
    """
    template_name = "consultants/newtheme/dashboard.html"
    consultant = None


class ConsultantDisplayView(TemplateView):
    """
    To display profile to all website visitors. 
    """

    template_name = "consultants/newtheme/display.html"
    organization = None
    specialty_tags = None
    branches = None
    profile = None
    MAX_IMAGE_HEIGHT = 300
    MAX_IMAGE_WIDTH = 900
    height = 0
    width = 0

    def setup(self, *args, **kwargs):
        org_id = kwargs.get("org_id")
        self.organization = Consultant.objects.filter(id=org_id).first()
        tag_type_specialty = TagType.objects.get(code="JOB_CATEGORY")
        contact_tag_type_specialty = ContactTagType.objects.get(contact=self.organization, tag_type=tag_type_specialty)
        self.specialty_tags = contact_tag_type_specialty.tags.all()
        self.branches = self.organization.branchoffices.all()
        if self.organization:
            self.profile = self.organization.organizationprofile


    def get(self, request, *args, **kwargs):
        self.setup(*args, **kwargs)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["organization"] = self.organization
        context["profile"] = self.organization.organizationprofile
        context["specialty_tags"] = self.specialty_tags
        context["branch_offices"] = self.branches

        if self.profile:
            if self.profile.image:
                if self.profile.image.height == None or self.profile.image.width == None:
                    self.height = self.MAX_IMAGE_HEIGHT
                    self.width = self.MAX_IMAGE_WIDTH
                elif self.profile.image.height > self.MAX_IMAGE_HEIGHT:
                    scaler = self.MAX_IMAGE_HEIGHT / self.profile.image.height
                    self.height = scaler * self.profile.image.height
                    self.width = scaler * self.profile.image.width
                    if self.width > self.MAX_IMAGE_WIDTH:
                        scaler = self.MAX_IMAGE_WIDTH / self.width
                        self.height = scaler * self.height
                        self.width = scaler * self.width
                elif self.profile.image.height <= self.MAX_IMAGE_HEIGHT:
                    self.height = self.profile.image.height
                    self.width = self.profile.image.width
                    if self.width > self.MAX_IMAGE_WIDTH:
                        scaler = self.MAX_IMAGE_WIDTH / self.width
                        self.height = scaler * self.height
                        self.width = scaler * self.width

        context["image_height"] = self.height
        context["image_width"] = self.width

        if self.profile and self.profile.image and self.profile.image.image_file:
            context["image_file_url"] = self.profile.image.image_file.url
        else:
            context["image_file_url"] = None

        return context


class ConsultantConfirmationView(AuthenticateLoginMixin, TemplateView):
    """
    Confirmation screen with link to list view.
    """

    template_name = "consultants/newtheme/confirmation.html"


# AuthenticateContactRoleMixin doesn't work here because there is no content?
class ConsultantPreviewView(AuthenticateLoginMixin, TemplateView):
    """
    To allow consultant to see consultant profile as it appears to website visitors. 
    """

    template_name = "consultants/newtheme/preview.html"
    organization = None
    specialty_tags = None
    branches = None
    profile = None
    MAX_IMAGE_HEIGHT = 300
    MAX_IMAGE_WIDTH = 900
    height = 0
    width = 0

    def setup(self, *args, **kwargs):
        org_id = kwargs.get("org_id")
        self.organization = Consultant.objects.filter(id=org_id).first()
        tag_type_specialty = TagType.objects.get(code="JOB_CATEGORY")
        contact_tag_type_specialty = ContactTagType.objects.get(contact=self.organization, tag_type=tag_type_specialty)
        self.specialty_tags = contact_tag_type_specialty.tags.all()
        self.branches = self.organization.branchoffices.all()
        if self.organization:
            self.profile = self.organization.organizationprofile


    def get(self, request, *args, **kwargs):
        self.setup(*args, **kwargs)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["organization"] = self.organization
        context["profile"] = self.organization.organizationprofile
        context["specialty_tags"] = self.specialty_tags
        context["branch_offices"] = self.branches

        if self.profile:
            if self.profile.image:
                if self.profile.image.height == None or self.profile.image.width == None:
                    self.height = self.MAX_IMAGE_HEIGHT
                    self.width = self.MAX_IMAGE_WIDTH
                elif self.profile.image.height > self.MAX_IMAGE_HEIGHT:
                    scaler = self.MAX_IMAGE_HEIGHT / self.profile.image.height
                    self.height = scaler * self.profile.image.height
                    self.width = scaler * self.profile.image.width
                    if self.width > self.MAX_IMAGE_WIDTH:
                        scaler = self.MAX_IMAGE_WIDTH / self.width
                        self.height = scaler * self.height
                        self.width = scaler * self.width
                elif self.profile.image.height <= self.MAX_IMAGE_HEIGHT:
                    self.height = self.profile.image.height
                    self.width = self.profile.image.width
                    if self.width > self.MAX_IMAGE_WIDTH:
                        scaler = self.MAX_IMAGE_WIDTH / self.width
                        self.height = scaler * self.height
                        self.width = scaler * self.width

        context["image_height"] = self.height
        context["image_width"] = self.width

        if self.profile and self.profile.image and self.profile.image.image_file:
            context["image_file_url"] = self.profile.image.image_file.url
        else:
            context["image_file_url"] = None

        return context


class ConsultantBranchView(AuthenticateLoginMixin, FormView):

    title = "Branch Offices"
    template_name = 'consultants/newtheme/branch.html'
    form_class = BranchOfficeForm

    form_obj = None
    org_id = None
    organization = None
    profile = None
    user_contact = None
    branch_formset = None
    contact = None
    
    def dispatch(self, request, *args, **kwargs):

        self.user_contact = request.user.contact
        self.contact = self.request.user.contact
        self.org_id = kwargs.get("org_id", None)

        imis_company_dict = None if not self.user_contact.get_imis_company() else self.user_contact.get_imis_company()[0]

        if imis_company_dict:
            imis_company_contact_id = imis_company_dict["webuserid"]
            imis_company_user = User.objects.filter(username=imis_company_contact_id).first()
            self.organization = Consultant.objects.filter(user=imis_company_user).first()
            if self.organization and self.org_id:
                if int(self.org_id) != int(self.organization.id):
                    messages.error(request, "We're sorry, there is a mismatch in your connection to your organization. Please contact customer service.")
                    return HttpResponseRedirect("/consultants/dashboard/")

        else:
            messages.error(request, "We're sorry, you are not a consultant admin or your organization is not listed among active consultants. Please contact customer service.")
            return HttpResponseRedirect("/consultants/dashboard/")

        # Only used for testing:
        # if not self.organization:
        #     self.organization = Consultant.objects.filter(id=self.org_id).first()

        self.profile = getattr(self.organization, "organizationprofile", None)        

        return super().dispatch(request, *args, **kwargs)


    def get(self, request, *args, **kwargs):

        BranchOfficeFormSetFactory = modelformset_factory(BranchOffice, self.form_class, extra=1)
        self.branch_formset = BranchOfficeFormSetFactory(queryset=self.organization.branchoffices.all())

        return super().get(request, *args, **kwargs)


    def post(self, request, *args, **kwargs):

        BranchOfficeFormSetFactory = modelformset_factory(BranchOffice, self.form_class, extra=1)
        posted_data=request.POST
        self.branch_formset = BranchOfficeFormSetFactory(posted_data, request.FILES)

        # print("IN POST BRANCH FORMSET IS::::::::::::", self.branch_formset)
        booly = self.branch_formset.is_valid()

        # print("FORMSET ERRORS:", self.branch_formset.errors)
        # for form in self.branch_formset:
            # print("FORM ERRORS::::::::::", form.errors)
        # print("BOOLY IS ::::::::::::::", booly)
        if self.branch_formset.is_valid():
            # print("BRANCH FORMSET IS VALID $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            for counter, branch_form in enumerate(self.branch_formset):
                if counter < (len(self.branch_formset)):
                    branch = branch_form.save(commit=False)
                    # the stuff to do to a pre-existing branch office:
                    if branch.city:
                        branch.parent_organization = self.organization
                        # cleaned_data = branch_form.cleaned_data
                        branch.save()
            return HttpResponseRedirect(self.get_success_url())

        else:
            context = self.get_context_data(**kwargs)
            self.branch_offices = self.organization.branchoffices.all()
            messages.error(request, "An error occurred. Please see below for any instructions.")
            return render(request, self.template_name, context)

    # def get_initial(self):

    #     BranchOfficeFormSetFactory = modelformset_factory(BranchOffice, self.form_class, extra=1)
    #     # posted_data=request.POST
    #     # self.branch_formset = BranchOfficeFormSetFactory(posted_data, request.FILES)
    #     self.branch_formset = BranchOfficeFormSetFactory(queryset=self.organization.branchoffices.all())
    #     print("IN GET INITIAL BRANCH FORMSET IS ::::::::::::::::", self.branch_formset)
    #     self.contact = self.request.user.contact
    #     initial = super().get_initial()

    #     return initial


# the form init throws an unexpected keyword arg error from this:
    # def get_form_kwargs(self):

    #     kwargs = super().get_form_kwargs()
    #     kwargs['org_id'] = self.organization.id

    #     return kwargs


    def get_success_url(self):
        """
        Returns the supplied success URL.
        """
        if self.request.POST.get('save_and_return'):
            messages.success(self.request,"Your branch office was added/edited successfully.")
            self.success_url = reverse_lazy("consultants:profile_update", kwargs={"org_id":self.org_id})
            # print("@@@@@@@@@@@@@@@@@@@@ in save and add another self.success_url is", self.success_url)
        elif self.request.POST.get('save_and_add_another'):
            messages.success(self.request,"Your branch office was added/edited successfully. You may add another.")
            self.success_url = reverse_lazy("consultants:manage_branch_offices", kwargs={"org_id":self.org_id})
            # print("@@@@@@@@@@@@@@@@@@@@ in save and continue self.success_url is", self.success_url)
        else:
            messages.error(self.request, "Your branch office could not be added/edited. Please contact customer service.")
            raise Http404("Incorrect submit.")
        url = force_text(self.success_url)
        return url


    def get_context_data(self, *args, **kwargs):

        context = super().get_context_data(**kwargs)

        keyword = kwargs.get("code", None)
        context["code"] = keyword

        try:
            user_company_dict = self.request.user.contact.get_imis_company()[0]
            # print("user_company_dict is: ", user_company_dict)

            company_contact_user = User.objects.get(username=user_company_dict["webuserid"])
            # print("company_contact_user is: ", company_contact_user)
            company_contact = company_contact_user.contact
            # print("company_contact is: ", company_contact)
            context['company'] = company_contact
            company_contact_admin = ContactRelationship.get_company_admin(contact=company_contact)
            # print("company_contact_admin is: ", company_contact_admin)
            if company_contact_admin and (company_contact_admin.user.username == self.request.user.username):
                if keyword == "ROSTER":
                    company_roster_list = company_contact.get_imis_company_relationships()
                    if company_roster_list.get("success") and not company_roster_list.get("error"):
                        context['contact_list'] = company_roster_list["data"]

                elif keyword == "SUBSCRIPTIONS":
                    # TO DO... need to pull from iMIS instead of using the model below, which no longer exists
                    # company_subs = Subscription.objects.filter(contact=company_contact)
                    # context["subscriptions"] = company_subs
                    pass

                elif keyword == "CONSULTANT":
                    company_roster_list = company_contact.get_imis_company_relationships()
                    # print("company_roster_list is: ", company_roster_list)
                    if company_roster_list.get("success") and not company_roster_list.get("error"):
                        context['contact_list'] = company_roster_list["data"]

            else:
                context['contact_list'] = False
        except:
            pass

        context['form_set'] = self.branch_formset

        return context


class ConsultantProfileView(AuthenticateLoginMixin, TemplateView):
    title = "Consultant Profile"
    template_name = 'consultants/newtheme/profile.html'

    op_formClass = OrganizationProfileForm
    o_formClass = ConsultantForm
    op_form_obj = None
    o_form_obj = None
    org_id = None
    organization = None
    org_type = "CONSULTANT"
    profile = None
    user_contact = None

    modelClass = Consultant
    product = None
    image = None
    MAX_IMAGE_HEIGHT = 300
    MAX_IMAGE_WIDTH = 900
    height = 0
    width = 0

    
    def dispatch(self, request, *args, **kwargs):

        self.user_contact = request.user.contact

        self.org_id = kwargs.get("org_id", None)
        imis_company_dict = None if not self.user_contact.get_imis_company() else self.user_contact.get_imis_company()[0]

        if imis_company_dict:
            imis_company_contact_id = imis_company_dict["webuserid"]
            imis_company_user = User.objects.filter(username=imis_company_contact_id).first()
            self.organization = Consultant.objects.filter(user=imis_company_user).first()

            if self.organization and self.org_id:
                if int(self.org_id) != int(self.organization.id):
                    messages.error(request, "We're sorry, there is a mismatch in your connection to your organization. Please contact customer service.")
                    return HttpResponseRedirect("/consultants/dashboard/")

            # This is just to facilitate testing should not normally be live:
            # if not self.organization:
            #     if self.org_id:
            #         self.organization = Consultant.objects.filter(id=self.org_id).first()

        else:
            messages.error(request, "We're sorry, you are not listed as a consultant admin or your organization is not listed among active consultants. Please contact customer service.")
            return HttpResponseRedirect("/consultants/dashboard/")

        if self.organization and not self.org_id:
            self.org_id = self.organization.id

        if not self.organization:
            messages.error(request, "We're sorry, you are not listed as a consultant admin or your organization is not listed among active consultants. Please contact customer service.")
            return HttpResponseRedirect("/consultants/dashboard/")
            
        self.profile = getattr(self.organization, "organizationprofile", None)
        self.setup(request, *args, **kwargs)

        return super().dispatch(request, *args, **kwargs)


    def setup(self, request, *args, **kwargs):

        if self.profile:
            self.profile.contact = self.organization
        else:
            self.profile = OrganizationProfile(contact=self.organization)
            self.profile.save()

        self.op_form_obj = self.op_formClass(request.POST or None, request.FILES or None, instance=self.profile)
        # print("op_form_obj.__dict__ is::::::::::::::::::::::::: ", self.op_form_obj.__dict__)
        self.o_form_obj = self.o_formClass(request.POST or None, request.FILES or None, instance=self.organization)
        # print("o_form_obj.__dict__ is::::::::::::::::::::::::: ", self.o_form_obj.__dict__)


    def post(self, request, *args, **kwargs):

        if self.o_form_obj.is_valid() and self.op_form_obj.is_valid():
            # cleaned_data = application_review_form.cleaned_data

            self.o_form_obj.save()
            # now, update the specialization tag
            # this will now be a list? 
            specialty_tag_ids = self.o_form_obj.cleaned_data["specialty_tag_ids"]
            # print("specialty_tag_ids are --------------------------------------------", specialty_tag_ids)
            tag_type_specialty = TagType.objects.get(code="JOB_CATEGORY")
            contact_tag_type_specialty, created = ContactTagType.objects.get_or_create(contact=self.organization, tag_type=tag_type_specialty)
            contact_tag_type_specialty.tags.clear()
            for tag_id in specialty_tag_ids:
                if int(tag_id) > 0:
                    tag = Tag.objects.get(id=tag_id)
                    contact_tag_type_specialty.tags.add(tag)
            contact_tag_type_specialty.save()

            profile = self.op_form_obj.save(commit=False)
            cleaned_data = self.op_form_obj.cleaned_data
            # print("cleaned_data is ^^^^^^^^^^^^^^^^^^^^^^", cleaned_data)

            posted_data=request.POST

            # if cleaned_data.get("image_uploaded_file", None):
            if cleaned_data.get("image_file", None):
            # if True:
            
                upload_type = UploadType.objects.filter(code="PROFILE_PHOTOS").first()
                # print("upload_type is ^^^^^^^^^^^^^^^^^^^^^^^^^^^", upload_type)
                self.image = ImageUpload.objects.filter(organizationprofile=profile).first()

            # if clear_image != 'on':
                # print("CLEAR_IMAGE IS NOT ON ^^^^^^^^^^^^^^^^ ")
                # print("IMAGE.WIDTH, HEIGHT IS ---------------------", self.image.width, self.image.height)
                # image.width = 1000
                # image.height = 600
                # pass width and height as context variables, set in the img tag
                # print("image is ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^", image)
                # image.organizationprofile_set.add(profile)
                if not self.image:
                    # content=self.application, 
                    self.image = ImageUpload(upload_type=upload_type)
                    # print("not image is ---------------------------", image)
                # image.uploaded_file = cleaned_data.get("image_uploaded_file", None)
                self.image.image_file = cleaned_data.get("image_file", None)
                # print("image.uploaded file is ^^^^^^^^^^^^^^^^^^^^^^^^^^", image.uploaded_file)
                self.image.save()
                profile.image = self.image
            elif posted_data.get('image_file-clear', None) == 'on' or cleaned_data.get("image_file", None) == False:
                # self.image.image_file = None
                self.image = None
                # self.image.save()
                profile.image = self.image
            profile.save()

                # print("profile.image is ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^", profile.image)

            # print("=====================================================")
            # image_uploaded_file = self.op_form_obj.cleaned_data["image_uploaded_file"]

            # THIS OVERWRITES PREVIOUS????????????????
            # image_file = self.op_form_obj.cleaned_data["image_file"]

            # print("op_form_obj is ---------------------------------", self.op_form_obj.instance)
            # print("self.op_form_obj.cleaned_data is -------------------", self.op_form_obj.cleaned_data)
            # print("self.op_form_obj.cleaned_data [image_uploaded_file] is :::::::::", self.op_form_obj.cleaned_data["image_uploaded_file"])
            # if image_uploaded_file:
            #     print("image_uploaded_file is ----------------------------------",image_uploaded_file)

            return HttpResponseRedirect(self.get_success_url())
        else:
            # messages.error(request, "An error occurred. Please see below for any instructions.")
            return super().get(request, *args, **kwargs)
            # return render(request, self.template_name, self.get_context_data(**kwargs))


    def get_success_url(self):
        """
        Returns the supplied success URL.
        """
        if self.request.POST.get('save_and_add_branch'):
            # print("IN SAVE AND ADD BRANCH SELF.ORG ID IS:::::::::::::", self.org_id)
            messages.success(self.request,"Your Profile was saved successfully. You may add a branch office.")
            self.success_url = reverse_lazy("consultants:manage_branch_offices", kwargs={"org_id":self.org_id})
        elif self.request.POST.get('save_and_return_later'):
            # print("IN SAVE AND ADD BRANCH SELF.ORG ID IS:::::::::::::", self.org_id)
            messages.success(self.request,"Successfully saved/updated your consultant profile..")
            self.success_url = reverse_lazy("consultants:profile_update", kwargs={"org_id":self.org_id})
        elif self.request.POST.get('save_and_continue'):
            messages.success(self.request,"Your Profile was saved successfully. Preview displayed below.")
            self.success_url = reverse_lazy("consultants:consultant_preview", kwargs={"org_id":self.org_id})
        else:
            messages.error(self.request, "Your Consultant Profile could not be created/updated. Please contact customer service.")
            # print("IN ERROR SELF.ORG ID IS:::::::::::::", self.org_id)
            raise Http404("Incorrect submit.")
        url = force_text(self.success_url)
        return url


    def get_context_data(self, *args, **kwargs):

        context = super().get_context_data(**kwargs)

        keyword = kwargs.get("code", None)
        context["code"] = keyword
        try:
            branches = self.organization.branchoffices.all()
        except:
            branches = None
        context["branch_offices"] = branches
        context["organization"] = self.organization
        context["profile"] = self.profile

        if self.profile:
            if self.profile.image:
                # first get teh actual values:
                if self.profile.image.height == None or self.profile.image.width == None:
                    self.height = self.MAX_IMAGE_HEIGHT
                    self.width = self.MAX_IMAGE_WIDTH                
                elif self.profile.image.height > self.MAX_IMAGE_HEIGHT:
                    scaler = self.MAX_IMAGE_HEIGHT / self.profile.image.height
                    self.height = scaler * self.profile.image.height
                    self.width = scaler * self.profile.image.width
                    if self.width > self.MAX_IMAGE_WIDTH:
                        scaler = self.MAX_IMAGE_WIDTH / self.width
                        self.height = scaler * self.height
                        self.width = scaler * self.width
                elif self.profile.image.height <= self.MAX_IMAGE_HEIGHT:
                    self.height = self.profile.image.height
                    self.width = self.profile.image.width
                    if self.width > self.MAX_IMAGE_WIDTH:
                        scaler = self.MAX_IMAGE_WIDTH / self.width
                        self.height = scaler * self.height
                        self.width = scaler * self.width

                # elif self.profile.image.width > self.MAX_IMAGE_WIDTH:
                #     scaler = self.MAX_IMAGE_WIDTH / self.profile.image.width
                #     self.width = scaler * self.profile.image.width
                #     self.height = scaler * self.profile.image.height
                # print("SELF DOT HEIGHT WIDTH ARE ------------------", self.height, self.width)

        context["image_height"] = self.height
        context["image_width"] = self.width
        # print("IN GET CONTEXT SELF DOT HEIGHT AND WIDTH ARE ------", self.height, self.width)
        if self.profile and self.profile.image and self.profile.image.image_file:
            context["image_file_url"] = self.profile.image.image_file.url
        else:
            context["image_file_url"] = None

        try:
            user_company_dict = self.request.user.contact.get_imis_company()[0]
            # print("user_company_dict is: ", user_company_dict)

            company_contact_user = User.objects.get(username=user_company_dict["webuserid"])
            # print("company_contact_user is: ", company_contact_user)
            company_contact = company_contact_user.contact
            # print("company_contact is: ", company_contact)
            context['company'] = company_contact
            company_contact_admin = ContactRelationship.get_company_admin(contact=company_contact)
            # print("company_contact_admin is: ", company_contact_admin)
            # print("company_contact_admin id is: ", company_contact_admin.id)
            if company_contact_admin and (company_contact_admin.user.username == self.request.user.username):
                if keyword == "ROSTER":
                    company_roster_list = company_contact.get_imis_company_relationships()
                    if company_roster_list.get("success") and not company_roster_list.get("error"):
                        context['contact_list'] = company_roster_list["data"]

                elif keyword == "SUBSCRIPTIONS":
                    pass
                    # TO DO: refactor to pull iMIS subscriptions if even
                    # company_subs = Subscription.objects.filter(contact=company_contact)
                    # context["subscriptions"] = company_subs

                elif keyword == "CONSULTANT":
                    company_roster_list = company_contact.get_imis_company_relationships()
                    # print("company_roster_list is: ", company_roster_list)
                    if company_roster_list.get("success") and not company_roster_list.get("error"):
                        context['contact_list'] = company_roster_list["data"]

            else:
                context['contact_list'] = False
        except:
            pass

        return context


class ConsultantListView(TemplateView):
    title = "Find a Consultant"
    template_name = 'consultants/newtheme/list.html'
    consultant_list = None

    def get_context_data(self, *args, **kwargs):

        context = super().get_context_data(**kwargs)

        # need to check org type and listing until date to be a valid consultant on list:
        consultant_orgs = Consultant.objects.filter(
            organizationprofile__consultant_listing_until__gt=timezone.now()
        )
        self.consultant_list = consultant_orgs
        context['consultant_list'] = self.consultant_list

        return context


#######################
## RFP/Q SUBMISSIONS ##
#######################
class RFPAdminDashboard(AuthenticateLoginMixin, TemplateView):
    """
    Dashboard to view existing RFP/Q submission records
    """
    template_name = "consultants/newtheme/rfp/admin-dashboard.html"

    def get(self, request, *args, **kwargs):

        rfp_roles = ContactRole.objects.filter(
            role_type="PROPOSER",
            contact=request.user.contact,
            content__content_type="RFP",
            publish_status__in=["SUBMISSION", "DRAFT"]
        ).select_related(
            "content__rfp",
            "content__master__content_live",
            "content__master__content_draft"
        ).order_by(
            "content__master_id",
            "-content__publish_status"
        ).distinct(
            "content__master_id"
        )

        self.rfps = [role.content.rfp for role in rfp_roles]

        # Only for template purposes
        for rfp in self.rfps:
            if rfp.master.content_live and rfp.master.content_live.status == "A":
                rfp.is_complete = True
                rfp.status_text = "Approved"
            elif rfp.master.content_draft:
                rfp.status_text = "Pending Review"
            else:
                rfp.is_editable = True
                rfp.status_text = "Not Entered"

        self.rfps = sorted(self.rfps, key=lambda r: r.deadline or r.created_time.date(), reverse=True)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["rfps"] = self.rfps
        return context


class RFPSubmissionEditFormView(AuthenticateContactRoleMixin, SubmissionEditFormView):
    """
    Form to Edit RFP/Q submission records
    """
    authenticate_role_type = "PROPOSER"
    form_class = RFPSubmissionEditForm
    template_name = "consultants/newtheme/rfp/submission-edit.html"
    home_url = reverse_lazy("consultants:rfp_dashboard")
    success_url = "/consultants/rfp/{master_id}/review/"

    def after_save(self, form):
        defaults = dict(publish_status="SUBMISSION")
        ContactRole.objects.update_or_create(
            contact=self.request.user.contact,
            content=self.content,
            role_type="PROPOSER",
            defaults=defaults
        )
        super().after_save(form)


class RFPSubmissionReviewFormView(AuthenticateContactRoleMixin, SubmissionReviewFormView):
    """
    Form to review, verify, and submit RFP/Q submission records
    """
    authenticate_role_type = "PROPOSER"
    form_class = RFPSubmissionVerificationForm
    template_name = "consultants/newtheme/rfp/submission-review.html"
    edit_url = "/consultants/rfp/{master_id}/update/"
    home_url = reverse_lazy("consultants:rfp_dashboard")
    success_url = "/consultants/rfp/{master_id}/thankyou/"

    def after_save(self, form):
        self.content.publish(publish_type="DRAFT") #publish to draft for review

        mail_context = {
            'rfp': self.content,
            'contact': self.request.user.contact,
        }
        Mail.send('RFP_SUBMISSION_CONFIRMATION', self.request.user.contact.email, mail_context)

        super().after_save(form)


class RFPSubmissionThankYou(TemplateView):
    """
    View to redirect to after an RFP/Q is successfully submitted
    """
    template_name = "consultants/newtheme/rfp/submission-thankyou.html"


class RFPPreviewView(AuthenticateContactRoleMixin, TemplateView):
    """
    View to see previously submitted RFP/Q record, 
    NOTE: We will only ever view the submission copy
    """
    authenticate_role_type = "PROPOSER"
    template_name = "consultants/newtheme/rfp/submission-preview.html"

    def set_content(self, *args, **kwargs):
        if not hasattr(self, "content"):
            master_id = kwargs.get("master_id")
            rfps = RFP.objects.filter(master_id=master_id, publish_status__in=["SUBMISSION", "DRAFT"])
            submission = next((r for r in rfps if r.publish_status == "SUBMISSION"), None)
            draft = next((r for r in rfps if r.publish_status == "DRAFT"), None)
            self.content = submission or draft

    def get(self, request, *args, **kwargs):
        self.set_content(*args, **kwargs)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["rfp"] = self.content
        return context


class RFPSearchView(LandingSearchView):
    title = "RFP/RFQ Search"
    content_url = "/consultants/rfp/search/"
    record_template = "content/newtheme/search/record_templates/rfp.html"
    filters = ["content_type:(RFP RFQ)", "-archive_time:[* TO NOW]"]
    facets = ["tags_CENSUS_REGION"]
    # rows = 10000 # shouldn't ever have this many, but want to show all results
    rows = 10 # reduced this to stop 502
    FilterFormClass = RFPSearchFilterForm

    content_types = ('RFP')


class RFPDetailsView(AppContentMixin, TemplateView):
    template_name = "consultants/newtheme/rfp/details.html"
    title = "RFP/RFQ Details"
    content_url = "/consultants/rfp/search/"

    def set_content(self, request, *args, **kwargs):
        master_id = kwargs.get("master_id")
        rfps = RFP.objects.filter(master_id=master_id, publish_status="PUBLISHED")
        self.rfp = rfps.first()
        return super().set_content(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.set_content(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["rfp"] = self.rfp
        return context



