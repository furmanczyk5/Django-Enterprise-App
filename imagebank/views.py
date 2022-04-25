from django.shortcuts import redirect
from django.views.generic import TemplateView, View
from django.core.urlresolvers import reverse_lazy
from django.contrib import messages

from myapa.viewmixins import AuthenticateMemberMixin, \
    AuthenticateContactRoleMixin
from content.views import SearchView

from myapa.models.contact import Contact
from myapa.models.contact_role import ContactRole
from content.models import MasterContent

from submissions.views import SubmissionEditFormView, SubmissionReviewFormView

from .models import Image
from .forms import ImageLibrarySearchFilterForm, ImageSubmissionCreateForm, \
    ImageSubmissionEditForm, ImageSubmissionVerificationForm


class SearchView(AuthenticateMemberMixin, SearchView):
    """FIXME: This inherits from :class:`content.views.SearchView` and is
    re-declaring it here. This may not be working as intended"""
    title = "Image Library Search"
    template_name = "content/newtheme/search/results-imagelibrary.html"
    rows = 15
    filters = ["content_type:IMAGE"]
    facets = ["tags_SEARCH_TOPIC", "tags_COMMUNITY_TYPE", "tags_IMAGE_ORIENTATION", "tags_IMAGE_NUMBEROFPEOPLE", "tags_IMAGE_COLOR", "tags_STATE"]
    photographers = None
    FilterFormClass = ImageLibrarySearchFilterForm

    def get_queries(self, *args, **kwargs):
        query_list = super().get_queries(*args, **kwargs)

        photographers = self.request.GET.get("photographers", None)

        #filter by photographers
        if photographers is not None:
            # right now, can only filter one speaker at a time...If we ever need to change that, edit the templates as well
            photographer_filter_id = photographers.strip()
            query_list.append("contact_roles_PHOTOGRAPHER:(%s|*)" % photographer_filter_id)
            try:
                photographer_filter_title = Contact.objects.get(id=photographer_filter_id).title
                self.photographers = {"username":photographer_filter_id,"title":photographer_filter_title}
            except (Contact.DoesNotExist, ) as e:
                pass
        return query_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['photographers'] = self.photographers
        return context


class ImageDetails(AuthenticateMemberMixin, TemplateView):

    template_name = "imagebank/newtheme/image-details.html"

    def get_context_data(self, **kwargs):

        master_id = kwargs.get("master_id", None)

        image = Image.objects.get(master_id=master_id, publish_status="PUBLISHED")
        photographer_roles = ContactRole.objects.filter(content=image, role_type="PHOTOGRAPHER").select_related("contact")

        context = {
            "image":image,
            "photographer_roles":photographer_roles
        }

        return self.add_ancestors_to_context(image, context)

    def add_ancestors_to_context(self, image, context):
        if image.parent_landing_master:
            context["ancestors"] = image.get_landing_ancestors()
        else:
            try:
                image.parent_landing_master = (
                    Content.objects.filter(url="/imagelibrary/").first().master
                )
                context["ancestors"] = image.get_landing_ancestors()
            except:
                pass

        return context


class ImageSubmissionDashboard(AuthenticateMemberMixin, TemplateView):
    template_name = "imagebank/newtheme/submission/dashboard.html"

    # these statuses are only used within this view
    # STATUS_UNSUBMITTED = "Not Submitted" # no live or draft copy, submission.status = "N"
    # STATUS_PENDING  = "Pending Approval" # submission.status = "P", and no live copy, may or may not have draft (bc asyncronous publishing)
    # STATUS_APPROVED = "Approved" # live copy with status = "A"
    # Assuming we are just deleting rejected submissions? we don't want that on our servers

    def get(self, request, *args, **kwargs):

        imageroles = ContactRole.objects.filter(
            role_type="PROPOSER", contact=request.user.contact, content__content_type="IMAGE", publish_status__in=["SUBMISSION", "DRAFT"]
        ).select_related(
            "content__image", 
            "content__master__content_draft__image", 
            "content__master__content_live__image"
        ).order_by("content__master_id", "-content__publish_status").distinct("content__master_id") # secondary sory by reverse publish_status will favor the submission copy

        sorted_imageroles = sorted(imageroles, key=lambda i: i.content.submission_time or i.content.created_time, reverse=True)
        self.unsubmitted_imageroles = []
        self.pending_imageroles = []
        self.approved_imageroles = []

        for role in sorted_imageroles:
            image = role.content.image
            draft = image.master.content_draft.image if image.master.content_draft else None
            live = image.master.content_live.image if image.master.content_live else None

            if live and live.status == "A":
                self.approved_imageroles.append(role)
            elif draft or image.status in ["P","A"]: # Can't assume that draft exists yet bc asynchrnous publishing
                self.pending_imageroles.append(role)
            else: # then it was never entered, NEED TO CHANGE THIS CASE IF NOT DELETING REJECTED ENTRIES
                self.unsubmitted_imageroles.append(role)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["unsubmitted_imageroles"] = self.unsubmitted_imageroles
        context["pending_imageroles"] = self.pending_imageroles
        context["approved_imageroles"] = self.approved_imageroles
        return context


class ImageSubmissionCreateFormView(AuthenticateMemberMixin, AuthenticateContactRoleMixin, SubmissionEditFormView):
    """
    Form View to create a new Image record. This step only includes the file upload and the submission_verified checkbox
    NOTE: Not a typical submission view in that this is only used when initially creating the submission
        We don't want users to fill in other info until they have uploaded the image
    """
    template_name = "imagebank/newtheme/submission/create.html"
    authenticate_role_type = "PROPOSER"
    form_class = ImageSubmissionCreateForm
    success_url = "/imagelibrary/submissions/{master_id}/update/"
    home_url = reverse_lazy("imagebank:submissions_dashboard")

    def after_save(self, form):
        # IF PROPOSER RECORD DOES NOT EXIST YET, THEN CREATE ONE
        ContactRole.objects.get_or_create(contact=self.request.user.contact, content=self.content, role_type="PROPOSER")
        super().after_save(form)


class ImageSubmissionEditFormView(AuthenticateMemberMixin, AuthenticateContactRoleMixin, SubmissionEditFormView):
    """
    Form View to edit existing Image records. This step includes all fields that the user needs for uploading images
    NOTE: Not a typical submission view in that this is only used for editing existing submissions
    """
    template_name = "imagebank/newtheme/submission/edit.html"
    authenticate_role_type = "PROPOSER"
    form_class = ImageSubmissionEditForm
    success_url = "/imagelibrary/submissions/{master_id}/review/"
    home_url = reverse_lazy("imagebank:submissions_dashboard")

    def after_save(self, form):
        messages.success(self.request, "You have successfully saved this image: %s!" % self.content.title)


# DO we even need review step?
class ImageSubmissionReviewFormView(AuthenticateMemberMixin, AuthenticateContactRoleMixin, SubmissionReviewFormView):
    title = "Review and Submit Image"
    template_name = "imagebank/newtheme/submission/review.html"
    authenticate_role_type = "PROPOSER"
    form_class = ImageSubmissionVerificationForm
    edit_url = "/imagelibrary/submissions/{master_id}/update/"
    home_url = reverse_lazy("imagebank:submissions_dashboard")
    success_url = reverse_lazy("imagebank:submissions_dashboard")

    def after_save(self, form):
        self.content.publish(publish_type="DRAFT")
        messages.success(self.request, """Thank you for your contribution to the APA Image Library. 
            Please allow one week for staff to review your submission. If it is accepted, you will 
            receive a confirmation email and the image will appear in the "Accepted Images" section 
            of your APA Image Library Uploads Dashboard.""")
        super().after_save(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["photographer_roles"] = ContactRole.objects.filter(content=self.content, role_type="PHOTOGRAPHER").select_related("contact")
        return context

class ImageSubmissionPreviewView(AuthenticateMemberMixin, AuthenticateContactRoleMixin, TemplateView):
    template_name = "imagebank/newtheme/submission/preview.html"
    authenticate_role_type = "PROPOSER"

    def set_content(self, *args, **kwargs):
        if not hasattr(self, "content"):
            master_id = kwargs.get("master_id")
            images = Image.objects.prefetch_related("contactrole__contact").filter(master_id=master_id)
            draft = next((i for i in images if i.publish_status == "DRAFT"), None)
            self.image = self.content = draft or None

    def get(self, request, *args, **kwargs):
        self.set_content(*args, **kwargs)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["image"] = self.image
        context["photographer_roles"] = [role for role in self.image.contactrole.all() if role.role_type == "PHOTOGRAPHER"]
        return context

class ImageSubmissionDeleteView(AuthenticateMemberMixin, AuthenticateContactRoleMixin, View):

    authenticate_role_type = "PROPOSER"
    http_method_names = [u'post']

    def set_content(self, *args, **kwargs):
        if not hasattr(self, "content"):
            self.master_id = kwargs.get("master_id")
            images = Image.objects.prefetch_related("contactrole__contact").filter(master_id=self.master_id)
            submission = next((i for i in images if i.publish_status == "SUBMISSION"), None)
            draft = next((i for i in images if i.publish_status == "DRAFT"), None)
            published = next((i for i in images if i.publish_status == "PUBLISHED"), None)
            self.image = self.content = published or draft or submission or None

    def post(self, request, *args, **kwargs):

        if self.image:
            if self.image.publish_status == "SUBMISSION":
                # Deleting the master content records will also delete the content records by cascade deletion
                MasterContent.objects.filter(id=self.master_id).delete()
                messages.success(request, "Successfully deleted your image submission")
            else:
                messages.error(request, """You cannot delete records that you have already submitted for review. 
                    Please contact customer service if you would like to delete this image.""")
        else:
            messages.error(request, "The Image record you want to delete does not exist.")

        return redirect("imagebank:submissions_dashboard")




