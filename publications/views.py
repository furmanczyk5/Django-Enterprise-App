import datetime
import urllib
import requests

from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic import TemplateView
from sentry_sdk import capture_exception

from content.models import ContentTagType
from content.solr_search import SolrSearch
from content.templatetags.content_extras import datetime_from_json, is_member_or_subscription
from content.utils.utils import solr_record_to_details_path
from content.templatetags.content_extras import split_on_period
from content.views import LandingSearchView
from content.viewmixins import AppContentMixin
from myapa.viewmixins import AuthenticateWebUserGroupMixin
from publications.models import Publication

SECTION_TAGLINES = {
    "INNOVATIONS": "Preparing for a rapidly changing future",
    "TOOLS": "Knowledge you can put to work",
    "INTERSECTIONS": "Where planning and the world meet",
    "VOICES": "How people power planning",
    "DISRUPTORS": "Trends and emerging issues facing our profession"
    }


class JAPAEmailRedirect(AuthenticateWebUserGroupMixin, TemplateView):
    """
    authenticate and redirect to tanfonline based on redirect_url passed
    """
    authenticate_groups = ["JAPA"]
    authenticate_groups_message_code = "NOT_SUBSCRIBER"

    def get(self, request):
        redirect_url = request.GET.get('redirect_url', 'http://www.tandfonline.com/toc/rjpa20/current')
        print('redirect url: ' + str(redirect_url))
        return japa_archive_redirect(request, redirect_url)


def japa_archive_redirect(request, redirect_url='http://www.tandfonline.com/toc/rjpa20/current'):
    """
    get japa archive url and redirect user
    """

    url = 'http://www.tandfonline.com/tps/requestticket?ru=' + redirect_url + '&debug=true&domain=planningassoc.org'
    url = urllib.parse.unquote(url)
    print("URL UNQUOTED: " + str(url))
    r = requests.get(url)

    return HttpResponseRedirect(r.text)


def japa_journal_redirect(request):

    r = requests.get('http://www.tandfonline.com/tps/requestticket?ru=http://www.tandfonline.com/page/apa-journals&amp;debug=true&amp;domain=planningassoc.org')

    return HttpResponseRedirect(r.text)


class PlanningMagazineHome(AppContentMixin, TemplateView):
    """
    Planning Magazine main landing page.
    """
    template_name = "publications/newtheme/planning-mag-home.html"
    content_url = "/planning/"
    title = "Planning Magazine"

    hero = None
    recent = None
    innovations = None
    tools = None
    intersections = None
    voices = None

    def get(self, request, *args, **kwargs):

        self.get_hero()
        self.get_recent()
        self.get_innovations()
        self.get_tools()
        self.get_intersections()
        self.get_voices()

        return super().get(request, *args, **kwargs)


    def get_context_data(self, *args, **kwargs):

        context = super().get_context_data(*args, **kwargs)
        context.update({
            "hero":self.hero,
            "recent":self.recent,
            "innovations":self.innovations,
            "tools":self.tools,
            "intersections":self.intersections,
            "voices":self.voices
        })

        return context


    def get_hero(self, *args, **kwargs):
    # try:
        data = SolrSearch(
            q="*",
            filters=[
                "(content_type:PUBLICATION AND resource_type:ARTICLE) AND tags_PLANNING_MAG_FEATURED:*.FEATURED_HERO.*"
            ],
            sort="sort_time desc",
            rows=1
        ).get_results()
        self.hero = data
        # print("HERO RESULTS: ")
        # print(self.hero)
    # except Exception as exc:
    #     capture_exception(exc)

    def get_recent(self, *args, **kwargs):
    # try:
        data = SolrSearch(
            q="*",
            filters=["(content_type:PUBLICATION AND resource_type:ARTICLE) AND tags_PLANNING_MAG_FEATURED:*.FEATURED_RECENT.*"],
            sort="sort_time desc",
            rows=4
        ).get_results()
        self.recent = data
        # print("RECENT FROM SOLR:")
        # print(self.recent)
    # except Exception as exc:
    #     capture_exception(exc)

    # THESE SHOULD NOT BE LOOKING FOR FEATURED SECTION TAGS -- THAT TAG IS FOR THE TWO FEATURED ARTICLES ON THE SECTION PAGES
    # HERE ALL WE ARE LOOKING FOR IS 5 MOST RECENT FROM A GIVEN SECTION
    def get_innovations(self, *args, **kwargs):
    # try:
        data = SolrSearch(
            q="*",
            filters=[
                "(content_type:PUBLICATION AND resource_type:ARTICLE) AND tags_PLANNING_MAG_FEATURED:*.FEATURED_SECTION.* AND tags_PLANNING_MAG_SECTION:*.INNOVATIONS.*"
            ],
            sort="sort_time desc",
            rows=5
        ).get_results()
        # print("INNOVATIONS SEARCH RESULTS -------------------------------------------------------------")
        # print(data)
        self.innovations = data
    # except Exception as exc:
    #     capture_exception(exc)

    def get_tools(self, *args, **kwargs):
    # try:
        data = SolrSearch(
            q="*",
            filters=[
                "(content_type:PUBLICATION AND resource_type:ARTICLE) AND tags_PLANNING_MAG_FEATURED:*.FEATURED_SECTION.* AND tags_PLANNING_MAG_SECTION:*.TOOLS.*"
            ],
            sort="sort_time desc",
            rows=5
        ).get_results()
        self.tools = data
    # except Exception as exc:
    #     capture_exception(exc)

    def get_intersections(self, *args, **kwargs):
    # try:
        data = SolrSearch(
            q="*",
            filters=[
                "(content_type:PUBLICATION AND resource_type:ARTICLE) AND tags_PLANNING_MAG_FEATURED:*.FEATURED_SECTION.* AND tags_PLANNING_MAG_SECTION:*.INTERSECTIONS.*"
            ],
            sort="sort_time desc",
            rows=5
        ).get_results()
        self.intersections = data
    # except Exception as exc:
    #     capture_exception(exc)

    def get_voices(self, *args, **kwargs):
    # try:
        data = SolrSearch(
            q="*",
            filters=[
                "(content_type:PUBLICATION AND resource_type:ARTICLE) AND tags_PLANNING_MAG_FEATURED:*.FEATURED_SECTION.* AND tags_PLANNING_MAG_SECTION:*.VOICES.*"
            ],
            sort="sort_time desc",
            rows=5
        ).get_results()
        self.voices = data
    # except Exception as exc:
    #     capture_exception(exc)


class PlanningMagazineSection(AppContentMixin, TemplateView):
    """
    Planning Magazine section or series page.
    """
    template_name = "publications/newtheme/planning-mag-section.html"
    content_url = "/planning/section/"
    # Can we update this from the section string in the url?
    title = "Planning Magazine Section"

    featured = None
    recent = None
    magazine_section = None

    # WE MIGHT NEED A "SECTION TAGLINE", E.G. "Where Planning and the World Meet" I BELIEVE IS THE TAGLINE
    # FOR THE "Intersections" section page... are there four "taglines"?
    section_tagline = None

    def get(self, request, *args, **kwargs):

        self.magazine_section = kwargs.get("mag_section")
        self.magazine_section = self.magazine_section.upper() if self.magazine_section else None
        self.section_tagline = SECTION_TAGLINES.get(self.magazine_section, None)
        self.get_featured()
        self.get_recent()

        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):

        context = super().get_context_data(*args, **kwargs)
        context.update({
            "featured":self.featured,
            "recent":self.recent,
            "magazine_section": self.magazine_section,
            "section_title":self.magazine_section,
            "section_tagline":self.section_tagline
        })

        return context

    def get_featured(self, *args, **kwargs):
    # try:
        data = SolrSearch(
            q="*",
            filters=[
                "(content_type:PUBLICATION AND resource_type:ARTICLE) AND (tags_PLANNING_MAG_SECTION:*.{0}.* OR tags_PLANNING_MAG_SERIES:*.{0}.*)".format(self.magazine_section)
            ],
            sort="sort_time desc",
            start=1,
            rows=2
        ).get_results()
        self.featured = data
        # print("FEATURED RESULTS: ")
        # print(self.featured)
    # except Exception as exc:
    #     capture_exception(exc)

    def get_recent(self, *args, **kwargs):
    # try:
        data = SolrSearch(
            q="*",
            filters=[
                "(content_type:PUBLICATION AND resource_type:ARTICLE) AND (tags_PLANNING_MAG_SECTION:*.{0}.* OR tags_PLANNING_MAG_SERIES:*.{0}.*)".format(self.magazine_section)
                ],
            sort="sort_time desc",
            start=3,
            rows=15
        ).get_results()
        self.recent = data
        # print("RECENT FROM SOLR:")
        # print(self.recent)
    # except Exception as exc:
    #     capture_exception(exc)

def load_more_articles(request, **kwargs):#, page=None):
    """
    A simple functional view. jquery will hit this endpoint to get a payload of search results from solr
    The browser never leaves planning/section/<mag_section>/
    """
    INITIAL_LOAD = 17
    page = int(kwargs.get("page", 1))
    magazine_section = request.GET.get("magazine_section", "INTERSECTIONS")
    magazine_section = magazine_section.upper() if magazine_section else "INTERSECTIONS"
    DT_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
    rows = 5
    start = (page - 1) * rows + INITIAL_LOAD + 1
    datetime_now_json = datetime.datetime.strftime(datetime.datetime.utcnow(), DT_FORMAT)
    data = SolrSearch(
        q="*",
        filters=[
            "(content_type:PUBLICATION AND resource_type:ARTICLE) AND (tags_PLANNING_MAG_SECTION:*.{0}.* OR tags_PLANNING_MAG_SERIES:*.{0}.*)".format(magazine_section)
        ],
        sort="begin_time asc",
        start=start,
        rows=rows
    ).get_results()

    docs = data.get("response").get("docs")
    inner_html = ''
    top =  '''
    <div class="row addtl_articles layout-tracery">

        <div class="layout-column" style="border: none;">

            <div class="row ">
    '''
    bottom = '''
            </div>

        </div>

    </div>
    '''

    for result in docs:
        details_url = solr_record_to_details_path(result)
        # img_src = "//placehold.it/198x132"
        # img_alt = "recent article image"
        img_src = result.get("thumbnail_2")
        img_alt = result.get("featured_image_caption")
        member_only = is_member_or_subscription(result.get("permission_groups"))
        sponsored_tags = result.get("tags_SPONSORED")
        sponsored_title = split_on_period(sponsored_tags[0],2) if sponsored_tags else ''
        slug_tags = result.get("tags_PLANNING_MAG_SLUG")
        slug_title = split_on_period(slug_tags[0], 2) if slug_tags else ''
        title = result.get("title")
        a = '''
        <div class="col-lg-2 col-md-3 col-sm-4 col-xs-6 ss-col">
          <a href="{}" class="content-preview-item">
            <div class="content-preview-item-image-block">
              <img src="{}" alt="{}" class="img-responsive" />
            </div>
            <div class="content-preview-item-headline">'''.format(details_url, img_src, img_alt)
        m = '<div class="members-only">APA Member Content</div>' if member_only else ''
        sp = '<div class="members-only sponsored-content">{}</div>'.format(sponsored_title) if sponsored_title else ''
        sl = '<h6 class="content-preview-item-superheadline">{}</h6>'.format(slug_title) if slug_title else ''
        t = '<div class="content-preview-item-title">{}</div>'.format(title)
        z = '''
            </div>
          </a>
        </div>
        '''
        inner_html = inner_html + a + m + sp + sl + t + z

    html = top + inner_html + bottom if docs else ''
    return HttpResponse(html)
