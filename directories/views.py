import datetime
import functools
import operator
from calendar import monthrange

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import Http404
from django.utils import timezone
from django.views.generic import TemplateView

from content.models import MessageText
from content.viewmixins import AppContentMixin
from myapa.models.contact import Contact
from myapa.models.educational_degree import EducationalDegree
from myapa.models.profile import IndividualProfile
from myapa.viewmixins import AuthenticateLoginMixin
from store.models import Purchase
from .forms import DirectoryForm, PASDirectoryForm, ResumeSearchForm
from .models import Directory

MEMBER_LOGIN_GROUPS = ['member', 'planning']
PAN_LOGIN_GROUPS = ("PAN",)
AICP_LOGIN_GROUPS = ['aicpmember']
SUBSCRIBER_LOGIN_GROUPS = ['PAS', 'ZONING', 'JAPA']
REGISTRATION_LOGIN_GROUPS = ['16CONF']
DIVISION_LOGIN_GROUPS = ["CITY_PLAN", "LAP", "SMALL_TOWN", "TRANS",
                         "URBAN_DES", "WOMEN", "LAW", "NEW_URB", "PLAN_BLACK",
                         "PRIVATE", "SCD", "CPD", "ECON", "FED_PLAN", "GALIP",
                         "HMDR", "HOUSING", "INFO_TECH", "INTER_GOV", "INTL",
                         "ENVIRON"]
CHAPTER_LOGIN_GROUPS = ["chapter", "CHAPT_AK", "CHAPT_KS", "CHAPT_MD",
                        "CHAPT_NV", "CHAPT_VA"]


# TO DO... refactor these!
# - business logic moved to models as much as possible
# - lots of logic duplicated in views below, does not need to repeat
class DirectoryView(AuthenticateLoginMixin, AppContentMixin, TemplateView):
    content_url = "/members/directory/"
    directory = None
    template_name = "directories/newtheme/directory.html"
    form_class = DirectoryForm
    model_class = IndividualProfile
    results = None
    school = None

    def setup(self, request, *args, **kwargs):
        try:
            self.directory = Directory.objects.prefetch_related("permission_groups").get(code=kwargs.get("code", None))
            self.required_group = self.directory.permission_groups.all()[0]
        except Directory.DoesNotExist:
            raise Http404("Directory does not exist")

    def get(self, request, *args, **kwargs):
        self.setup(request, *args, **kwargs)
        self.is_aicp = request.user.groups.filter(name="aicp-cm").exists()
        page = request.GET.get('page', None)
        if not page:
            request.session["search_query"] = request.GET
        self.create_pagination(request)
        return super().get(request, *args, **kwargs)

    def create_pagination(self, request):
        self.form = self.form_class(request.session.get("search_query"))  
        if request.GET.get('submit') == "Search" or int(request.GET.get('page', 0)) > 1:
            filter_kwargs = self.form.get_query_map()
            keyword = filter_kwargs.pop("keyword", None)
            self.school = filter_kwargs.pop("school", None)
            search_results = []
            if self.school:
                school_search_results = []
                school_results = EducationalDegree.objects.filter(school__company__icontains=self.school)
                if keyword:
                    keyword = keyword.split()
                    keyword_qset = functools.reduce(operator.__or__, [Q(contact__first_name__icontains=word) | Q(contact__last_name__icontains=word) for word in keyword])
                    school_results = school_results.filter(keyword_qset).distinct("contact__last_name","contact__first_name")
                if filter_kwargs:
                    school_results = school_results.filter(**filter_kwargs).filter(contact__user__groups__name = "member")
                    if "contact__individualprofile__slug__isnull" in filter_kwargs:
                        school_results = school_results.exclude(contact__individualprofile__slug="")
                search_results = school_results.filter(contact__user__groups__name = "member").exclude(contact__individualprofile__share_profile="PRIVATE").order_by("contact__last_name","contact__first_name") #removing the PRIVATE users and results are order by last name
            else:
                search_results = self.model_class.objects.filter(**filter_kwargs).filter(contact__user__groups__name = "member")
                if "slug__isnull" in filter_kwargs:
                    search_results = search_results.exclude(slug="")
                if keyword:
                    keyword = keyword.split()
                    keyword_qset = functools.reduce(operator.__or__, [Q(contact__first_name__icontains=word) | Q(contact__last_name__icontains=word) for word in keyword])
                    search_results = (search_results or self.model_class.objects).filter(keyword_qset).distinct()
                search_results = search_results.exclude(share_profile="PRIVATE").order_by("contact__last_name","contact__first_name") #removing the PRIVATE users and results are order by last name
            page = request.GET.get('page', 1)
            paginator = Paginator(search_results or [], 10) # Shows only 10 records per page
            try:
                self.results = paginator.page(page)
            except PageNotAnInteger: # If page is not an integer, deliver first page
                self.results = paginator.page(1)
            except EmptyPage:  # If page is out of range, deliver last page of results
                self.results = paginator.page(paginator.num_pages)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        context["code"] = kwargs.get("code", None)
        context["results"] = self.results
        context["search"] = self.request.GET.get('submit', None)
        context["page"] = self.request.GET.get('page', None)
        context["is_aicp"] = self.is_aicp
        context["school"] = self.school

        perm_grps_set = set(self.directory.permission_groups.all())
        user_grps_set = set(self.request.user.groups.all())
        has_perms = (perm_grps_set <= user_grps_set) or self.request.user.is_staff or self.request.user.groups.filter(name="staff").exists()
        if not has_perms:
            lacked_perms = [str(x) for x in perm_grps_set if x not in user_grps_set]
            try:
                if bool(set(lacked_perms).intersection(MEMBER_LOGIN_GROUPS)):
                    msg = MessageText.objects.get(code="NOT_APA_MEMBER")
                elif bool(set(lacked_perms).intersection(AICP_LOGIN_GROUPS)):
                    msg = MessageText.objects.get(code="NOT_AICP_MEMBER")
                elif bool(set(lacked_perms).intersection(SUBSCRIBER_LOGIN_GROUPS)):
                    msg = MessageText.objects.get(code="NOT_SUBSCRIBER")
                elif bool(set(lacked_perms).intersection(REGISTRATION_LOGIN_GROUPS)):
                    msg = MessageText.objects.get(code="NOT_REGISTERED")
                elif bool(set(lacked_perms).intersection(DIVISION_LOGIN_GROUPS)):
                    msg = MessageText.objects.get(code="NOT_DIVISION_MEMBER")
                elif bool(set(lacked_perms).intersection(CHAPTER_LOGIN_GROUPS)):
                    msg = MessageText.objects.get(code="NOT_CHAPTER_MEMBER")
                elif bool(set(lacked_perms).intersection(PAN_LOGIN_GROUPS)):
                    msg = MessageText.objects.get(code="NOT_PAN_MEMBER")
                else:
                    msg = MessageText.objects.get(code="AUTO_LOGIN_DENIAL")
            except:
                msg, m = MessageText.objects.get_or_create(code="AUTO_LOGIN_DENIAL", text='<p>You are logged in but do not have access to this page </p>\r\n')
            context["access_denied_message"] = msg.text

        context["access_denied"] = not has_perms
        context["required_groups"] = perm_grps_set
        return context

class DivisionChapterDirectoryView(AuthenticateLoginMixin, AppContentMixin, TemplateView):
    directory = None
    template_name = "directories/newtheme/division-chapter-directory.html"
    form_class = DirectoryForm
    model_class = IndividualProfile
    results = None
    school = None
    code = None

    def setup(self, request, *args, **kwargs):
        try:
            self.code = self.code or kwargs.get("code", None)
            self.directory = Directory.objects.prefetch_related("permission_groups").get(code=self.code)
            self.required_group = self.directory.permission_groups.all()[0]
            self.content_url = request.path.replace("form/", "")
        except Directory.DoesNotExist:
            raise Http404("Directory does not exist")

    def get(self, request, *args, **kwargs):
        self.setup(request, *args, **kwargs)
        self.is_aicp = request.user.groups.filter(name="aicp-cm").exists()
        page = request.GET.get('page', None)
        if not page: 
            request.session["search_query"] = request.GET
        self.create_pagination(request)
        return super().get(request, *args, **kwargs)

    def create_pagination(self, request):
        self.form = self.form_class(request.session.get("search_query"))
        if request.GET.get('submit') == "Search" or int(request.GET.get('page', 0)) > 1:
            filter_kwargs = self.form.get_query_map()
            keyword = filter_kwargs.pop("keyword", None)
            self.school = filter_kwargs.pop("school", None)
            search_results = []
            if self.school:
                school_search_results = []
                school_results = EducationalDegree.objects.filter(school__company__icontains=self.school)
                if keyword:
                    keyword = keyword.split()
                    keyword_qset = functools.reduce(operator.__or__, [Q(contact__first_name__icontains=word) | Q(contact__last_name__icontains=word) for word in keyword])
                    school_results = school_results.filter(keyword_qset).distinct("contact__last_name","contact__first_name")
                if filter_kwargs:
                    school_results = school_results.filter(**filter_kwargs)
                    if "contact__individualprofile__slug__isnull" in filter_kwargs:
                        school_results = school_results.exclude(contact__individualprofile__slug="")
                search_results = school_results.filter(contact__user__groups__name=self.required_group).exclude(contact__individualprofile__share_profile="PRIVATE").order_by("contact__last_name") #removing the PRIVATE users and results are order by last name
            else:
                search_results = self.model_class.objects.filter(**filter_kwargs).filter(contact__user__groups__name=self.required_group)
                if "slug__isnull" in filter_kwargs:
                    search_results = search_results.exclude(slug="")
                if keyword:
                    keyword = keyword.split()
                    keyword_qset = functools.reduce(operator.__or__, [Q(contact__first_name__icontains=word) | Q(contact__last_name__icontains=word) for word in keyword])
                    search_results = (search_results or self.model_class.objects).filter(keyword_qset).distinct()
                search_results = search_results.exclude(share_profile="PRIVATE").order_by("contact__last_name") #removing the PRIVATE users and results are order by last name
            page = request.GET.get('page', 1)
            paginator = Paginator(search_results or [], 10) # Shows only 10 records per page
            try:
                self.results = paginator.page(page)
            except PageNotAnInteger: # If page is not an integer, deliver first page
                self.results = paginator.page(1)
            except EmptyPage:  # If page is out of range, deliver last page of results
                self.results = paginator.page(paginator.num_pages)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["directory"] = self.directory
        context["form"] = self.form
        context["code"] = kwargs.get("code", None)
        context["results"] = self.results
        context["search"] = self.request.GET.get('submit', None)
        context["page"] = self.request.GET.get('page', None)
        context["is_aicp"] = self.is_aicp
        context["school"] = self.school

        perm_grps_set = set(self.directory.permission_groups.all())
        user_grps_set = set(self.request.user.groups.all())
        has_perms = (perm_grps_set <= user_grps_set) or self.request.user.is_staff or self.request.user.groups.filter(name="staff").exists()
        if not has_perms:
            lacked_perms = [str(x) for x in perm_grps_set if x not in user_grps_set]
            try:
                if bool(set(lacked_perms).intersection(MEMBER_LOGIN_GROUPS)):
                    msg = MessageText.objects.get(code="NOT_APA_MEMBER")
                elif bool(set(lacked_perms).intersection(AICP_LOGIN_GROUPS)):
                    msg = MessageText.objects.get(code="NOT_AICP_MEMBER")
                elif bool(set(lacked_perms).intersection(SUBSCRIBER_LOGIN_GROUPS)):
                    msg = MessageText.objects.get(code="NOT_SUBSCRIBER")
                elif bool(set(lacked_perms).intersection(REGISTRATION_LOGIN_GROUPS)):
                    msg = MessageText.objects.get(code="NOT_REGISTERED")
                elif bool(set(lacked_perms).intersection(DIVISION_LOGIN_GROUPS)):
                    msg = MessageText.objects.get(code="NOT_DIVISION_MEMBER")
                elif bool(set(lacked_perms).intersection(CHAPTER_LOGIN_GROUPS)):
                    msg = MessageText.objects.get(code="NOT_CHAPTER_MEMBER")
                else:
                    msg = MessageText.objects.get(code="AUTO_LOGIN_DENIAL")
            except:
                msg, m = MessageText.objects.get_or_create(code="AUTO_LOGIN_DENIAL", text='<p>You are logged in but do not have access to this page </p>\r\n')
            context["access_denied_message"] = msg.text

        context["access_denied"] = not has_perms
        context["required_groups"] = perm_grps_set
        return context

class PASDirectoryView(AuthenticateLoginMixin, TemplateView):
    directory = None
    template_name = "directories/newtheme/pas-directory.html"
    form_class = PASDirectoryForm
    model_class = IndividualProfile
    results = None

    def setup(self, request, *args, **kwargs):
        try:
            self.directory = Directory.objects.prefetch_related("permission_groups").get(code=kwargs.get("code", None))
            self.required_group = self.directory.permission_groups.all()[0]
        except Directory.DoesNotExist:
            raise Http404("Directory does not exist")

    def get(self, request, *args, **kwargs):
        self.setup(request, *args, **kwargs)
        page = request.GET.get('page', None)
        if not page: 
            request.session["search_query"] = request.GET
        self.create_pagination(request)
        return super().get(request, *args, **kwargs)

    def create_pagination(self, request):
        self.form = self.form_class(request.session.get("search_query"))
        if request.GET.get('submit') == "Search" or int(request.GET.get('page', 0)) > 1:
            filter_kwargs = self.form.get_query_map()
            search_results = []
            if filter_kwargs:
                search_results = self.model_class.objects.filter(**filter_kwargs).filter(contact__contact_type="ORGANIZATION")
            search_results = search_results.exclude(share_profile="PRIVATE").order_by("company") # removing the PRIVATE users and results are order by last name   
            page = request.GET.get('page', 1)
            paginator = Paginator(search_results or [], 10) # Shows only 10 records per page
            try:
                self.results = paginator.page(page)
            except PageNotAnInteger: # If page is not an integer, deliver first page
                self.results = paginator.page(1)
            except EmptyPage:  # If page is out of range, deliver last page of results
                self.results = paginator.page(paginator.num_pages)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        context["code"] = kwargs.get("code", None)
        context["results"] = self.results
        context["search"] = self.request.GET.get('submit', None)
        context["page"] = self.request.GET.get('page', None)
        perm_grps_set = set(self.directory.permission_groups.all())
        user_grps_set = set(self.request.user.groups.all())
        has_perms = (perm_grps_set <= user_grps_set) or self.request.user.is_staff or self.request.user.groups.filter(name="staff").exists()
        if not has_perms:
            lacked_perms = [str(x) for x in perm_grps_set if x not in user_grps_set]
            try:
                if bool(set(lacked_perms).intersection(MEMBER_LOGIN_GROUPS)):
                    msg = MessageText.objects.get(code="NOT_APA_MEMBER")
                elif bool(set(lacked_perms).intersection(AICP_LOGIN_GROUPS)):
                    msg = MessageText.objects.get(code="NOT_AICP_MEMBER")
                elif bool(set(lacked_perms).intersection(SUBSCRIBER_LOGIN_GROUPS)):
                    msg = MessageText.objects.get(code="NOT_SUBSCRIBER")
                elif bool(set(lacked_perms).intersection(REGISTRATION_LOGIN_GROUPS)):
                    msg = MessageText.objects.get(code="NOT_REGISTERED")
                elif bool(set(lacked_perms).intersection(DIVISION_LOGIN_GROUPS)):
                    msg = MessageText.objects.get(code="NOT_DIVISION_MEMBER")
                elif bool(set(lacked_perms).intersection(CHAPTER_LOGIN_GROUPS)):
                    msg = MessageText.objects.get(code="NOT_CHAPTER_MEMBER")
                else:
                    msg = MessageText.objects.get(code="AUTO_LOGIN_DENIAL")
            except:
                msg, m = MessageText.objects.get_or_create(code="AUTO_LOGIN_DENIAL", text='<p>You are logged in but do not have access to this page </p>\r\n')
            context["access_denied_message"] = msg.text
        context["access_denied"] = not has_perms
        context["required_groups"] = perm_grps_set
        return context

class ResumeSearchView(AuthenticateLoginMixin, TemplateView):
    template_name = "directories/newtheme/resume-search.html"
    form_class = ResumeSearchForm
    model_class = IndividualProfile
    results = None
    school = None
    valid_job_ad = True

    def setup(self, request, *args, **kwargs):
        job_ad_purchase = Purchase.objects.filter(user=request.user, product__product_type="JOB_AD")

        if job_ad_purchase:
            created_date = job_ad_purchase[0].created_time.replace(tzinfo=None)
            current_date = timezone.now().replace(tzinfo=None)

            min_year = current_date.year
            min_month = current_date.month - 3

            if min_month<0:
                min_month = 12-abs(min_month)
            elif min_month==0:
                min_month = 12
                min_year = current_date.year - 1

            min_month_lastday = monthrange(min_year, min_month)[1]
            if current_date.day > min_month_lastday:
                min_date = datetime.datetime(year=int(min_year), month=int(min_month), day=int(min_month_lastday)).replace(tzinfo=None)
            else:
                min_date = datetime.datetime(year=int(min_year), month=int(min_month), day=int(current_date.day)).replace(tzinfo=None)

            if not min_date < created_date < current_date:
                self.valid_job_ad = False
        else:
            self.valid_job_ad = False

    def get(self, request, *args, **kwargs):
        self.setup(request, *args, **kwargs)
        self.is_aicp = request.user.groups.filter(name="aicp-cm").exists()
        page = request.GET.get('page', None)
        if not page:
            request.session["search_query"] = request.GET
        self.create_pagination(request)
        return super().get(request, *args, **kwargs)

    def create_pagination(self, request):
        self.form = self.form_class(request.session.get("search_query"))
        if request.GET.get('submit') == "Search" or int(request.GET.get('page', 0)) > 1:
            filter_kwargs = self.form.get_query_map()
            keyword = filter_kwargs.pop("keyword", None)
            self.school = filter_kwargs.pop("school", None)
            search_results = self.model_class.objects.filter(resume__isnull=False).filter(~Q(share_profile="HIDDEN"))
            if self.school:
                school_results = EducationalDegree.objects.filter(school__company__icontains=self.school).filter(contact__individualprofile__resume__isnull=False)
                if keyword:
                    keyword = keyword.split()
                    keyword_qset = functools.reduce(operator.__or__, [Q(contact__first_name__icontains=word) | Q(contact__last_name__icontains=word) for word in keyword])
                    school_results = school_results.filter(keyword_qset).distinct()
                if filter_kwargs:
                    school_results = school_results.filter(**filter_kwargs)
                    if "contact__individualprofile__slug__isnull" in filter_kwargs:
                        school_results = school_results.exclude(contact__individualprofile__slug="")
                search_results = school_results.exclude(contact__individualprofile__share_profile="PRIVATE").order_by("contact__last_name") # removing the PRIVATE users and results are order by last name
            else:
                if filter_kwargs:
                    search_results = search_results.filter(**filter_kwargs)
                if keyword:
                    keyword = keyword.split()
                    keyword_qset = functools.reduce(operator.__or__, [Q(contact__first_name__icontains=word) | Q(contact__last_name__icontains=word) for word in keyword])
                    search_results = (search_results or self.model_class.objects).filter(keyword_qset).distinct()
                search_results = search_results.order_by("contact__last_name") # removing the PRIVATE users and results are order by last name
            page = request.GET.get('page', 1)
            paginator = Paginator(search_results or [], 10) # Shows only 10 records per page
            try:
                self.results = paginator.page(page)
            except PageNotAnInteger: # If page is not an integer, deliver first page
                self.results = paginator.page(1)
            except EmptyPage:  # If page is out of range, deliver last page of results
                self.results = paginator.page(paginator.num_pages)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        context["code"] = "resume"
        context["results"] = self.results
        context["search"] = self.request.GET.get('submit', None)
        context["page"] = self.request.GET.get('page', None)
        context["is_aicp"] = self.is_aicp
        context["school"] = self.school
        if self.valid_job_ad == False:
            try:
                msg = MessageText.objects.get(code="NO_VALID_JOB_AD")
            except:
                msg, m = MessageText.objects.get_or_create(code="NO_VALID_JOB_AD", text='<p>Resume search is accessible to members for 3 months after the start date of their job posting. Please contact APA Customer Service for more details at <a href="mailto:customerservice@planning.org">customerservice@planning.org</a>.</p>')
            context["access_denied"] = True
            context["access_denied_message"] = msg.text
        return context


class RosterView(AuthenticateLoginMixin, AppContentMixin, TemplateView):
    template_name = "directories/newtheme/roster.html"
    model_class = Contact
    results = None
    directory = None
    count_per_page = 10

    def dispatch(self, request, *args, **kwargs):

        # TO DO... separate content urls for each division, chapter...
        if not getattr(self, "content_url", None):
            self.content_url = "/leadership/committees/"

        return super().dispatch(request, *args, **kwargs)

    def get_results_qs(self, request, *args, **kwargs):
        return Contact.objects.filter(user__groups__name=self.directory.directory_group.name).order_by("last_name")

    def get(self, request, *args, **kwargs):
        code = kwargs.get("code", None)
        # this cleans up codes from urls...
        if code:
            code = code.replace("-", "_").upper() # WTF? THis is really hacky.
        self.directory = Directory.objects.get(code=code)
        self.results = self.get_results_qs(request, *args, **kwargs)

        page = request.GET.get('page', 1)
        paginator = Paginator(self.results or [], self.count_per_page) # Shows only 10 records per page
        try:
            self.results = paginator.page(page)
        except PageNotAnInteger: # If page is not an integer, deliver first page
            self.results = paginator.page(1)
        except EmptyPage:  # If page is out of range, deliver last page of results
            self.results = paginator.page(paginator.num_pages)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["results"] = self.results
        context["directory"] = self.directory
        return context

class PDOsView(RosterView):
    content_url="/chapters/pdo/"
    template_name = "directories/newtheme/pdo.html"
    count_per_page = 100

    def get_results_qs(self, request, *args, **kwargs):
        return super().get_results_qs(request, *args, **kwargs).order_by("chapter")
