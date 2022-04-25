from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps import views as sitemaps_views
from django.views import defaults
from django.views.generic.base import RedirectView


from blog.sitemaps import BlogPostSitemap
from knowledgebase.sitemaps import (
    KnowledgebaseCollectionSitemap
)
from learn.sitemaps import LearnCourseSitemap
from pages.sitemaps import (AboutPageSitemap, AICPPageSitemap, AudioPageSitemap,
                            CareerPageSitemap, ConferencesPageSitemap, ConnectPageSitemap,
                            KnowledgeCenterPageSitemap, MembershipPageSitemap, OutreachPageSitemap,
                            PolicyPageSitemap)
from publications.sitemaps import (ReportSitemap, PublicationDocumentSitemap,
                                   ArticleSitemap, PlanningMagArticleSitemap)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
else:
    urlpatterns = []

sitemaps = dict(
    blog=BlogPostSitemap,
    knowledgebase_collection=KnowledgebaseCollectionSitemap,
    learncourse=LearnCourseSitemap,
    aboutpage=AboutPageSitemap,
    aicppage=AICPPageSitemap,
    audiopage=AudioPageSitemap,
    careerpage=CareerPageSitemap,
    conferencespage=ConferencesPageSitemap,
    connectpage=ConnectPageSitemap,
    knowledgecenterpage=KnowledgeCenterPageSitemap,
    membershippage=MembershipPageSitemap,
    outreachpage=OutreachPageSitemap,
    policypage=PolicyPageSitemap,
    report=ReportSitemap,
    publicationdocument=PublicationDocumentSitemap,
    article=ArticleSitemap,
    planningmagarticle=PlanningMagArticleSitemap,
)


urlpatterns += [
    # Examples:
    # url(r"^$", "planning.views.home", name="home"),
    # url(r"^blog/", include("blog.urls")),

    url(r"^grappelli/", include("grappelli.urls")),
    url(r"^grappelli/", include("grappelli.urls")), # grappelli URLS
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r"^admin/", include(admin.site.urls)),
    url(r"^_nested_admin/", include("nested_admin.urls")),
    url(r"^store/", include("store.urls", namespace="store")),
    url(r"^conference/", include("conference.urls")),
    url(r"^ui/", include("ui.urls")),
    url(r"^cm/", include("cm.urls", namespace="cm")),

    url(r"^imagelibrary/", include("imagebank.urls", namespace="imagebank")),
    url(r"^awards/", include("awards.urls", namespace="awards")),
    url(r"^registrations/", include("registrations.urls", namespace="registrations")),
    url(r"^medialibrary/", include("media.urls", namespace="media") ),
    url(r"^template_app/", include("template_app.urls", namespace="template_app")),
    url(r"^consultants/", include("consultants.urls", namespace="consultants") ),
    url(r"^inquiry/", include("research_inquiries.urls", namespace="inquiry") ),
    url(r"^customerservice/", include("support.urls", namespace="support") ),
    url(r"^free-students/", include("free_students.urls", namespace="free_students") ),
    url(r"^pages/", include("pages.urls", namespace="pages") ),
    url(r"^foundation/", include("store.urls_foundation", namespace="foundation")),
    url(r"^", include("jobs.urls", namespace="jobs") ),
    url(r"^", include("blog.urls", namespace="blog") ),
    url(r"^", include("learn.urls")),
    url(r"^", include("myapa.urls")),
    url(r"^", include("publications.urls")),
    url(r"^", include("events.urls.event_urls")),
    url(r"^", include("directories.urls")),
    url(r"^", include("exam.urls")),
    url(r"^", include("knowledgebase.urls", namespace="knowledgebase")),
    url(r"^", include("media.urls")),

    url(r'^404/$', defaults.page_not_found, ),
    url(r'^500/$', defaults.server_error ),
    url(r"^", include("content.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# SOME WAY TO REDIRECT / PROXY STATIC URLS?
# urlpatterns = static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + urlpatterns
urlpatterns = [url(r"^mobile/", include(urlpatterns, namespace="mobile"))] + urlpatterns

if getattr(settings, 'ENVIRONMENT_NAME', None) == 'PROD':
    urlpatterns.insert(
        0,
        url(
            r"^sitemap\.xml$",
            sitemaps_views.index,
            {'sitemaps': sitemaps},
        )
   )
    urlpatterns.insert(
        1,
        url(
            r'^sitemap-(?P<section>.+)\.xml$',
            sitemaps_views.sitemap,
            {'sitemaps': sitemaps},
            name='django.contrib.sitemaps.views.sitemap'
        )
    )

