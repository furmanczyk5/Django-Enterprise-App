from django.views.generic import TemplateView
from django.core.urlresolvers import reverse_lazy

from content.mail import Mail
from submissions.views import SubmissionEditFormView, \
    SubmissionReviewFormView, SubmissionUploadsView
from myapa.models.contact_role import ContactRole
from myapa.viewmixins import ContactOrganizationMixin, \
    AuthenticateOrganizationContactRoleMixin

from .models import Inquiry, REVIEW_STATUSES
from .forms import InquirySubmissionEditForm, InquirySubmissionVerificationForm


###############################
# # PAS Inquiry SUBMISSIONS # #
###############################
class InquiryAdminDashboard(ContactOrganizationMixin, TemplateView):
    """
    Dashboard for users to view their existing Inquiries submission records
    """
    template_name = "research_inquiries/newtheme/submission/dashboard.html"

    def get(self, request, *args, **kwargs):

        self.get_organization()

        inquiries = ContactRole.objects.filter(
            role_type="PROPOSER", contact=self.organization, content__content_type="RESEARCH_INQUIRY", publish_status__in=["SUBMISSION", "DRAFT"]
        ).select_related("content__inquiry", "content__master__content_draft__inquiry").order_by("content__master_id", "-content__publish_status").distinct("content__master_id") # secondary sory by reverse publish_status will favor the submission copy

        for inquiry_role in inquiries:
            inquiry = inquiry_role.content.inquiry
            draft = inquiry.master.content_draft.inquiry if inquiry.master.content_draft else None
            
            if draft:
                inquiry.status_text = next((s[1] for s in REVIEW_STATUSES if s[0] == draft.review_status), "--")
                inquiry.show_edit = False
                inquiry.is_complete = draft.review_status == "COMPLETED"
            else: # then it was never entered
                inquiry.status_text = "Not Entered"
                inquiry.show_edit = True

        self.inquiries = sorted(inquiries, key=lambda i: i.content.submission_time or i.content.created_time, reverse=True)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["inquiries"] = self.inquiries
        context["organization"] = self.organization
        return context


class InquirySubmissionEditFormView(AuthenticateOrganizationContactRoleMixin, SubmissionEditFormView):
    """
    Form to Edit Inquiry submission records
    """
    authenticate_role_type = "PROPOSER"
    form_class = InquirySubmissionEditForm
    template_name = "research_inquiries/newtheme/submission/edit.html"
    home_url = reverse_lazy("inquiry:inquiry_dashboard")
    success_url = "/inquiry/{master_id}/uploads/"

    def get_initial(self):
        initial = super().get_initial()
        inquiry_contact = next((cr for cr in self.content.contactrole.all() if cr.role_type == "PROPOSER"), None) if self.content else None
        contact = self.request.user.contact
        initial["contact_first_name"] = getattr(inquiry_contact, "first_name", contact.first_name)
        initial["contact_last_name"] = getattr(inquiry_contact, "last_name", contact.last_name)
        initial["contact_email"] = getattr(inquiry_contact, "email", contact.email)
        return initial

    def after_save(self, form):
        defaults = dict(
            first_name=form.cleaned_data.get("contact_first_name"),
            last_name=form.cleaned_data.get("contact_last_name"),
            email=form.cleaned_data.get("contact_email"),
            publish_status="SUBMISSION")
        ContactRole.objects.update_or_create(contact=self.organization, content=self.content, role_type="PROPOSER", defaults=defaults)
        super().after_save(form)


class InquirySubmissionUploadsFormView(AuthenticateOrganizationContactRoleMixin, SubmissionUploadsView):
    """
    View to submit uploads along with the Inquiry
    """
    authenticate_role_type = "PROPOSER"
    template_name = "research_inquiries/newtheme/submission/uploads.html"
    modelClass = Inquiry
    home_url = reverse_lazy("inquiry:inquiry_dashboard")
    success_url = "/inquiry/{master_id}/review/"


class InquirySubmissionReviewFormView(AuthenticateOrganizationContactRoleMixin, SubmissionReviewFormView):
    """
    Form to review, verify, and submit Inquiry submission records
    """
    title = "Submission Review - PAS Research Inquiry"
    authenticate_role_type = "PROPOSER"
    form_class = InquirySubmissionVerificationForm
    template_name = "research_inquiries/newtheme/submission/review.html"
    edit_url = "/inquiry/{master_id}/update/"
    home_url = reverse_lazy("inquiry:inquiry_dashboard")
    success_url = "/inquiry/{master_id}/thankyou/"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.inquiry_contact = next(cr for cr in self.content.contactrole.all() if cr.role_type == "PROPOSER")

    def after_save(self, form):
        self.content.publish(publish_type="DRAFT")

        mail_context = {
            'inquiry': self.content,
            'inquiry_contact': self.inquiry_contact,  # is really the proposer contactrole
        }
        Mail.send('PAS_INQUIRY_CONFIRMATION', self.inquiry_contact.email, mail_context)

        super().after_save(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["inquiry_uploads"] = self.content.uploads.all()
        context["inquiry_contact"] = self.inquiry_contact
        return context


class InquirySubmissionThankYou(TemplateView):
    """
    View to redirect to after an Inquiry is successfully submitted
    """
    template_name = "research_inquiries/newtheme/submission/thankyou.html"


class InquiryPreviewView(AuthenticateOrganizationContactRoleMixin, TemplateView):
    """
    View to see previously submitted Inquiry record
    """
    authenticate_role_type = "PROPOSER"
    template_name = "research_inquiries/newtheme/inquiry-details.html"

    def set_content(self, *args, **kwargs):
        if not hasattr(self, "content"):
            master_id = kwargs.get("master_id")
            inquiries = Inquiry.objects.prefetch_related("contactrole__contact", "uploads__upload_type", "review_assignments__role__contact").filter(master_id=master_id)
            complete_draft = next((i for i in inquiries if i.publish_status == "DRAFT" and i.review_status == "COMPLETED"), None)
            submission = next((i for i in inquiries if i.publish_status == "SUBMISSION"), None)
            self.inquiry = self.content = complete_draft or submission or inquiries.first()

    def get(self, request, *args, **kwargs):
        self.set_content(*args, **kwargs)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["inquiry"] = self.inquiry
        context["inquiry_contact"] = next((cr for cr in self.inquiry.contactrole.all() if cr.role_type == "PROPOSER"), None)
        context["inquiry_uploads"] = [u for u in self.inquiry.uploads.all() if u.upload_type.code == "PAS_INQUIRY"]
        context["response_uploads"] = [u for u in self.inquiry.uploads.all() if u.upload_type.code == "PAS_RESPONSE"]
        context["reviewers"] = [r.role.contact for r in self.inquiry.review_assignments.all()]
        return context
