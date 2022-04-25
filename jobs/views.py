import pytz
import datetime

from django.contrib import messages
from django.core.urlresolvers import reverse, reverse_lazy
from django.http.response import HttpResponseRedirect, Http404
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView, View

from component_sites.models import ProviderSettings
from content.models import MessageText, ContentTagType
from content.viewmixins import AppContentMixin
from content.views import LandingSearchView
from myapa.models.contact_role import ContactRole
from myapa.models.contact import Contact
from myapa.viewmixins import AuthenticateLoginMixin, \
    AuthenticateWebUserGroupMixin
from store.models import Purchase, ProductPrice
from submissions.views import SubmissionEditFormView, SubmissionReviewFormView

from .models import Job, ENTRY_LEVEL_JOB_TYPES
from .forms import JobSubmissionTypeForm, JobSubmissionDetailsForm, \
    JobSubmissionDetailsNoAICPForm, JobSubmissionReviewForm, \
    JobSearchFilterForm


class JobSearchView(LandingSearchView):
    title = "Jobs Search"
    content_url = "/jobs/search/"

    # TO DO:
    # BAD BAD BAD... should not use lists (mutable type) as class attributes for views!!!!!!!!!!!!
    filters = ["content_type:JOB"]
    facets = ["tags_CENSUS_REGION", "tags_JOB_CATEGORY", "tags_JOB_EXPERIENCE_LEVEL", "tags_AICP_LEVEL"]

    FilterFormClass = JobSearchFilterForm

    def get_filters(self):
        """
        Returns the list of filter rstatements (like "content_type:EVENT")
        NOTE: these filtered results get cached so use for common filters e.g. content_type, event_type, conference
        """
        if getattr(self.request, "site", None):
            contact = getattr(ProviderSettings.for_site(self.request.site),"contact")
        else:
            contact = Contact.objects.get(user__username= "119523")
        return self.filters + ["contact_roles_PROVIDER:{provider_username}|*".format(provider_username=contact.id)]


class JobSubmissionFormTypeView(AuthenticateLoginMixin, SubmissionEditFormView):
    title = "Jobs Online"
    form_class = JobSubmissionTypeForm
    template_name = "jobs/newtheme/submission/type.html"

    home_url = "/jobs/admin-dashboard"
    success_url = "/jobs/post/{master_id}/details/"

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        form_kwargs["product_code"] = "JOB_AD"
        form_kwargs["category_code"] = "JOB_AD"
        return form_kwargs

    def after_save(self, form):
        ContactRole.objects.get_or_create(contact=self.request.user.contact, content=self.content, role_type="AUTHOR")

        # the organization record for this site (e.g. APA, APA Virginia, etc.)
        if getattr(self.request, 'site', None):
            site_contact = getattr(ProviderSettings.for_site(self.request.site), "contact")
        else:
            site_contact = Contact.objects.get(user__username="119523")

        ContactRole.objects.get_or_create(contact=site_contact, content=self.content, role_type="PROVIDER")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if getattr(self.request, 'site', None):
            job_post_instructions_code = getattr(ProviderSettings.for_site(self.request.site), "jobs_post_instruction_code", None)
        else:
            job_post_instructions_code = None
        if job_post_instructions_code:
            mt_obj = MessageText.objects.filter(code=job_post_instructions_code).first()
            if mt_obj:
                context['job_post_instructions_text'] = mt_obj.text
                MessageText.set_content_messages(context, [job_post_instructions_code])
        else:
            MessageText.set_content_messages(context, ["JOBS_POST_INSTRUCTIONS"])
        return context


class JobSubmissionFormDetailsView(AuthenticateLoginMixin, SubmissionEditFormView):
    title = "Jobs Online"
    form_class = JobSubmissionDetailsForm
    template_name = "jobs/newtheme/submission/edit.html"
    home_url = "/jobs/admin-dashboard"
    success_url = "/jobs/post/{master_id}/review/"

    def get_form_class(self):
        product_master = getattr(self.submission_category, "product_master", None)
        job_product = product_master.content_live.product if product_master else None
        price_code = self.content.job_type
        product_price = ProductPrice.objects.filter(code=price_code, product=job_product).first()
        price = product_price.price if product_price else None

        if (self.content.job_type in ENTRY_LEVEL_JOB_TYPES) or price == 0:
            return JobSubmissionDetailsNoAICPForm
        else:
            return super().get_form_class()

    def form_invalid(self, form):
        messages.error(self.request, """Your submission record did not save correctly. \
            Please check that the values you have provided are valid and try again.""")
        return super().form_invalid(form)

    def after_save(self, form):
        super().after_save(form)
        # to avoid duplicate contactRole, use Draft content when possible
        if self.content.publish_status != 'DRAFT' and self.content.master.content_draft:
            draft_content = self.content.master.content_draft
        else:
            draft_content = self.content
        ContactRole.objects.get_or_create(contact=self.request.user.contact, content=draft_content, role_type="AUTHOR")

        # the organization record for this site (e.g. APA, APA Virginia, etc.)
        if getattr(self.request, 'site', None):
            site_contact = getattr(ProviderSettings.for_site(self.request.site), "contact")
        else:
            site_contact = Contact.objects.get(user__username="119523")
        ContactRole.objects.get_or_create(contact=site_contact, content=draft_content, role_type="PROVIDER")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if getattr(self.request, 'site', None):
            job_post_instructions_code = getattr(ProviderSettings.for_site(self.request.site), "jobs_post_instruction_code", None)
        else:
            job_post_instructions_code = None
        if job_post_instructions_code:
            mt_obj = MessageText.objects.filter(code=job_post_instructions_code).first()
            if mt_obj:
                context['job_post_instructions_text'] = mt_obj.text
                MessageText.set_content_messages(context, [job_post_instructions_code])
        else:
            MessageText.set_content_messages(context, ["JOBS_POST_INSTRUCTIONS"])
        return context


class JobSubmissionFormReviewView(AuthenticateLoginMixin, SubmissionReviewFormView):
    title = "Jobs Online"
    template_name = "jobs/newtheme/submission/review.html"
    form_class = JobSubmissionReviewForm
    home_url = reverse_lazy("jobs:admin_dashboard")
    edit_url = "/jobs/post/{master_id}/details/"
    success_url = reverse_lazy("jobs:admin_dashboard")

    def get_checkout_required(self):
        if self.content.master.published_time:
            return False
        try:
            product_master = getattr(self.submission_category, "product_master", None)
            job_product = product_master.content_live.product if product_master else None
            price_code = self.content.job_type
            product_price = ProductPrice.objects.filter(code=price_code, product=job_product).first()
            price = product_price.price if product_price else None
            return product_master and job_product.status == "A" and price != 0
        except:
            return False

        # requires_checkout = super().get_checkout_required()
        # return requires_checkout and self.content.job_type != "INTERN" and not self.content.master.content_draft

    def after_save(self, form):
        if not self.requires_checkout:
            self.content.ad_publish()
            messages.success(self.request, mark_safe('The job post {0} has been successfully posted to <a href="https://www.planning.org/jobs/search/">www.planning.org/jobs/search/</a>').format(self.content))
        return super().after_save(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["job_experience_level"] = next((ctt.tags.first().title for ctt in self.content.contenttagtype.all() if ctt.tag_type.code == "JOB_EXPERIENCE_LEVEL"), None)
        context["job_specialty"] = next((ctt.tags.first().title for ctt in self.content.contenttagtype.all() if ctt.tag_type.code == "JOB_CATEGORY"), None)
        context["job_aicp_level"] = next((ctt.tags.first().title for ctt in self.content.contenttagtype.all() if ctt.tag_type.code == "AICP_LEVEL"), None)
        return context

    def update_cart(self, *args, **kwargs):
        kwargs.update(dict(code=self.content.job_type))
        super().update_cart(*args, **kwargs)

    def form_invalid(self, form):
        messages.error(self.request, """We could not proceed with your submission. \
            Please check that the values you have provided are valid and try again.""")
        return super().form_invalid(form)

class JobAdminDashboard(AuthenticateLoginMixin, TemplateView):
    title = "Jobs Online"
    template_name="jobs/newtheme/submission/dashboard.html"

    def get(self, request, *args, **kwargs):

        self.contact = self.request.user.contact

        filter_kwargs = {
            "contact":self.contact,
            "role_type":"AUTHOR",
        }

        if getattr(self.request, 'site', None):
            self.site_contact = getattr(ProviderSettings.for_site(self.request.site), "contact")
        else:
            self.site_contact = Contact.objects.get(user__username="119523")

        job_roles = ContactRole.objects.select_related(
            "content", "content__job", "content__master"
        ).filter(
            **filter_kwargs
        ).order_by(
            "content__master", "-content__id"
        )

        self.jobs = []
        last_master_id = ""
        for role in job_roles:
            job = role.content
            provider_role = ContactRole.objects.filter(contact=self.site_contact, content=job, role_type='PROVIDER').first()
            if provider_role:

                is_past = False # how to tell if a job has expired?
                is_published = False

                purchase = Purchase.objects.select_related("order").filter(content_master=job.master).first()

                if job.master.content_live:
                    is_published = True

                if last_master_id != job.master_id:
                    self.jobs.append({
                    "master_id":job.master_id,
                    "status": job.status,
                    "publish_status": job.publish_status,
                    "title":job.title,
                    "is_past":is_past,
                    "is_published":is_published,
                    "has_changes":False,
                    "purchase":purchase,
                    "make_inactive_time":job.make_inactive_time,
                    "editable":job.job.editable(),
                    })

                    last_master_id = job.master_id

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contact"] = self.contact
        context["jobs"] = self.jobs
        context["title"] = self.title
        if getattr(self.request, 'site', None):
            job_post_instructions_code = getattr(ProviderSettings.for_site(self.request.site),
                                                 "jobs_post_instruction_code", None)
        else:
            job_post_instructions_code = None
        if job_post_instructions_code:
            mt_obj = MessageText.objects.filter(code=job_post_instructions_code).first()
            if mt_obj:
                context['job_post_instructions_text'] = mt_obj.text
                MessageText.set_content_messages(context, [job_post_instructions_code])
        else:
            MessageText.set_content_messages(context, ["JOBS_POST_INSTRUCTIONS"])
        return context


class JobSubmissionFormDeleteView(View):

    def dispatch(self,request,*args,**kwargs):

        master_id = kwargs.get('master_id', None)
        job = Job.objects.filter(master__id=master_id, publish_status="SUBMISSION").first()
        title = job.title

        purchase = Purchase.objects.filter(content_master = master_id).delete()
        job.delete()

        messages.success(request,"Job Ad: {0} has been removed".format(title))
        return HttpResponseRedirect(reverse('jobs:admin_dashboard'))


# worry about render content later... for now get info to show up
class JobDetailsView(AuthenticateLoginMixin, AppContentMixin, TemplateView):
    """
    Render Content View for Jobs
    """
    content_url="/jobs/search/"
    title = "Jobs Online"
    prompt_login = False
    template_name = "jobs/newtheme/details.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        master_id = kwargs.get("master_id")
        self.content = Job.objects.get(master=master_id, publish_status="PUBLISHED")

        # code to auto-update the status if job is expired
        if self.content.status == 'I':
            raise Http404("Job listing has expired.")

        self.content_draft = Job.objects.get(master=master_id, publish_status="DRAFT")

        if self.content.status == 'A' and self.content.make_inactive_time < datetime.datetime.now(pytz.utc):
            self.content_draft.status = 'I'
            self.content_draft.save()
            self.content_draft.publish()
            self.content_draft.solr_publish()
            raise Http404("Job listing has expired.")
        elif self.content.status == 'CA':
            raise Http404("Job listing has been cancelled.")

        contenttagtype_job_experience = ContentTagType.objects.filter(content=self.content, tag_type__code="JOB_EXPERIENCE_LEVEL").first()
        contenttagtype_job_category = ContentTagType.objects.filter(content=self.content, tag_type__code="JOB_CATEGORY").first()
        contenttagtype_aicp_level = ContentTagType.objects.filter(content=self.content, tag_type__code="AICP_LEVEL").first()

        context["is_authenticated"] = self.is_authenticated
        context["content"] = self.content

        if contenttagtype_job_experience and contenttagtype_job_experience.tags.first():
            context["job_experience_level"] = contenttagtype_job_experience.tags.first().title

        if contenttagtype_job_category and contenttagtype_job_category.tags.first():
            context["job_category"] = contenttagtype_job_category.tags.first().title

        if contenttagtype_aicp_level and contenttagtype_aicp_level.tags.first():
            context["job_aicp_level"] = contenttagtype_aicp_level.tags.first().title
        context["title"] = self.title

        return context


class JobSalaryWorksheetView(AuthenticateWebUserGroupMixin, TemplateView):
    authenticate_groups = ["member-media"]
    template_name = "jobs/newtheme/salary-worksheet.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        MessageText.set_content_messages(context, ["SALARY_WORKSHEET"])
        return context
