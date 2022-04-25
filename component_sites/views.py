from django.http import Http404
from django.views.generic import TemplateView

from directories.views import DivisionChapterDirectoryView
from myapa.models.contact import Contact
from myapa.viewmixins import AuthenticateLoginMixin
from events.forms import CalendarSearchForm
from events.models import Event, NATIONAL_CONFERENCES
from content.views import SearchView
from content.models import Tag
from jobs.models import Job
from jobs.views import JobSearchView, JobAdminDashboard, JobSubmissionFormDetailsView, \
    JobSubmissionFormTypeView, JobSubmissionFormReviewView, JobSubmissionFormDeleteView, \
    JobDetailsView

from submissions.models import Category
from component_sites.models import NewsPage, ProviderSettings
from component_sites.viewmixins import ComponentSitesMixin, ComponentSitesNavMixin



class ComponentDirectoryView(ComponentSitesNavMixin, DivisionChapterDirectoryView):

    template_name = "component-sites/component-theme/templates/component-directory.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)

    def setup(self, request, *args, **kwargs):
        # TO DO: we will want something like this
        self.directory = getattr(ProviderSettings.for_site(self.request.site),"directory")
        super().setup(request, *args, **kwargs)


class ChapterJobAdminDashboardView(ComponentSitesMixin, JobAdminDashboard):
    title = "Jobs Online"
    template_name = "component-sites/component-theme/templates/jobs/submission/dashboard.html"


class ChapterJobSearchView(JobSearchView):
    pass


class ChapterJobSubmissionFormTypeView(ComponentSitesMixin, JobSubmissionFormTypeView):
    template_name = "component-sites/component-theme/templates/jobs/submission/type.html"
    submission_category = None
    submission_category_code = None

    def set_submission_category(self, request, *args, **kwargs):
        cat_code = getattr(ProviderSettings.for_site(self.request.site), "jobs_submission_category_code")
        if cat_code:
            sub_cat = Category.objects.filter(code=cat_code).first()
            self.submission_category = sub_cat
            self.submission_category_code = cat_code

        return super().set_submission_category(request, *args, **kwargs)

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        form_kwargs["product_code"] = getattr(ProviderSettings.for_site(self.request.site), "job_product", "JOB_AD")
        form_kwargs["category_code"] = getattr(ProviderSettings.for_site(self.request.site), "jobs_submission_category_code", "JOB_AD")
        return form_kwargs



class ChapterJobSubmissionFormDetailsView(ComponentSitesMixin, JobSubmissionFormDetailsView):
    template_name = "component-sites/component-theme/templates/jobs/submission/edit.html"
    submission_category = None
    submission_category_code = None

    def set_submission_category(self, request, *args, **kwargs):
        cat_code = getattr(ProviderSettings.for_site(request.site),"jobs_submission_category_code")
        if cat_code:
            sub_cat = Category.objects.filter(code=cat_code).first()
            self.submission_category = sub_cat
            self.submission_category_code = cat_code

        return super().set_submission_category(request, *args, **kwargs)


class ChapterJobSubmissionFormDeleteView(JobSubmissionFormDeleteView):
    pass


class ChapterJobSubmissionFormReviewView(ComponentSitesMixin, JobSubmissionFormReviewView):
    template_name = "component-sites/component-theme/templates/jobs/submission/review.html"
    submission_category = None
    submission_category_code = None

    def set_submission_category(self, request, *args, **kwargs):
        cat_code = getattr(ProviderSettings.for_site(request.site),"jobs_submission_category_code")
        if cat_code:
            sub_cat = Category.objects.filter(code=cat_code).first()
            self.submission_category = sub_cat
            self.submission_category_code = cat_code

        return super().set_submission_category(request, *args, **kwargs)


class ChapterJobDetailsView(ComponentSitesMixin, JobDetailsView):
    template_name = "component-sites/component-theme/templates/jobs/details.html"
    submission_category = None
    submission_category_code = None

    def set_submission_category(self, request, *args, **kwargs):
        cat_code = getattr(ProviderSettings.for_site(request.site), "jobs_submission_category_code")
        if cat_code:
            sub_cat = Category.objects.filter(code=cat_code).first()
            self.submission_category = sub_cat
            self.submission_category_code = cat_code

        return super().set_submission_category(request, *args, **kwargs)


class ComponentSitesEventsSearch(ComponentSitesMixin, SearchView):
    title = "Search Calendar"
    page_url = "/"
    filters = ["content_type:EVENT", "event_type:(EVENT_SINGLE EVENT_MULTI EVENT_INFO)"]
    FilterFormClass = CalendarSearchForm

    # reduces all events search pages to results for the particular chapter or division as provider
    def get_filters(self):
        self.addl_providers = getattr(ProviderSettings.for_site(self.request.site), 'additional_contacts')
        self.provider = getattr(ProviderSettings.for_site(self.request.site), 'contact')

        addl_provider_str = ''
        if self.addl_providers:
            for addl_provider in self.addl_providers.all():
                addl_provider_str += str(addl_provider.id) + " "
        return self.filters + ["contact_roles_PROVIDER:({0}* {1})".format(self.provider.id,
                                                                          addl_provider_str.replace(' ', '* '))]


class DivisionNPCEventsSearch(ComponentSitesMixin, SearchView):
    title = "Division-related NPC Events"
    page_url = "/"
    filters = []
    sort = "begin_time desc"
    FilterFormClass = CalendarSearchForm

    def get_filters(self):
        recent_conf_codes = [conf[0] for conf in NATIONAL_CONFERENCES]
        most_recent_conf_code = recent_conf_codes[len(recent_conf_codes) - 1]
        most_recent_conf = Event.objects.get(code=most_recent_conf_code, publish_status='PUBLISHED')
        # taking begin time out for now -- it will show most recent past events until new conf is set up
        filters = ["content_type:EVENT",
                   "parent:{0}".format(most_recent_conf.master.id)]

        tag = getattr(ProviderSettings.for_site(self.request.site), "tag")
        if tag:
            escaped_title = "\ ".join(tag.title.split(" "))
            filters.append("tags_DIVISION:{0}.{1}.{2}".format(tag.id, tag.code, escaped_title))
        return filters


# UNNECESSARY??:
class NewsDetailsView(AuthenticateLoginMixin, TemplateView):
    """
    View for Chapter News Post
    """
    title = "News Details"
    prompt_login = False
    template_name = "component-sites/component-theme/templates/news.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        django_id = kwargs.get("id")
        self.news_page = NewsPage.objects.get(id=django_id, live=True)

        if self.news_page.expired:
            raise Http404("News post has expired.")

        context["is_authenticated"] = self.is_authenticated
        context["news_page"] = self.news_page
        context["title"] = self.news_page.title

        return context


class NewsPostsView(AuthenticateLoginMixin, ComponentSitesMixin, SearchView):
    """
    View for Chapter News Posts
    """
    title = "News Posts"
    prompt_login = False
    template_name = "component-sites/component-theme/templates/news/posts.html"
    filters = ["content_type:newspage"]
    sort = "published_time desc"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        host = self.request.get_host()
        # winnow down the results to just the chapter or division in question
        for response_parts in self.results.items():
            if response_parts[0] == 'response':
                docs_list = response_parts[1]["docs"]
                docs_list[:] = [result for result in docs_list if result.get("code", None) == host]

        context["solr_news_page_results"] = self.results
        context["is_authenticated"] = self.is_authenticated

        return context


class JobsPostsView(AuthenticateLoginMixin, ComponentSitesMixin, SearchView):
    """
    View for Chapter Jobs Posts
    """
    title = "Jobs Posts"
    prompt_login = False
    template_name = "component-sites/component-theme/templates/jobs/posts.html"
    filters = ["content_type:JOB"]

    def get_filters(self):
        provider = getattr(ProviderSettings.for_site(self.request.site), "contact")
        print(provider.id, provider.user.username)
        return self.filters + ["contact_roles_PROVIDER:{0}|*".format(getattr(provider, "id"))]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["solr_jobs_page_results"] = self.results
        context["is_authenticated"] = self.is_authenticated

        return context


class JobsDetailsView(AuthenticateLoginMixin, TemplateView):
    """
    View for Chapter News Post
    """
    title = "Job Details"
    prompt_login = False
    template_name = "component-sites/component-theme/templates/jobs/details.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        django_id = kwargs.get("id")
        self.job = Job.objects.get(master_id=django_id, publish_status='PUBLISHED')

        if self.job.status != 'A':
            raise Http404("Jobs post is not current.")

        context["is_authenticated"] = self.is_authenticated
        context["job"] = self.job
        context["title"] = self.job.title
        context["is_wagtail_site"] = True

        return context


class ComponentSearchView(ComponentSitesMixin, SearchView):
    extends_template = "component-sites/component-theme/templates/base.html"

    def get_filters(self):
        site = self.request.site.hostname
        provider = getattr(ProviderSettings.for_site(self.request.site), "contact")
        site_query_term = "(site:{site} OR contact_roles_PROVIDER:{provider_id}|*)".format(
            site=site,
            provider_id=provider.id)
        return self.filters + [site_query_term]
