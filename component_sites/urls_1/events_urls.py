from wagtail.wagtailadmin import urls as wagtailadmin_urls
from wagtail.wagtaildocs import urls as wagtaildocs_urls
from wagtail.wagtailcore import urls as wagtail_urls

from django.views import defaults
from django.conf import settings
from django.conf.urls.static import static

from django.conf.urls import include, url
from component_sites.views import ComponentSitesEventsSearch, DivisionNPCEventsSearch
from content import views as content_views
from store.views import checkout_views

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
else:
    urlpatterns = []

# url(r"^", include("jobs.urls", namespace="jobs") ),
urlpatterns += [
    
    url(r'^search/$', ComponentSitesEventsSearch.as_view(), name='search'),
    url(r'^search/npc/$', DivisionNPCEventsSearch.as_view(), name='search_npc'),
    url(r'^(eventinfo|eventmulti|eventsingle|activity)/(?P<master_id>\d+)/$', content_views.RenderContent.as_view(), name='event_details'),
]