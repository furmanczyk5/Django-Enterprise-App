from wagtail.wagtailadmin import urls as wagtailadmin_urls
from wagtail.wagtaildocs import urls as wagtaildocs_urls
from wagtail.wagtailcore import urls as wagtail_urls

from django.views import defaults
from django.conf import settings
from django.conf.urls.static import static
# from django.contrib.auth import views as auth_views

from django.conf.urls import include, url
from .views import ComponentSearchView
# from myapa.views import ComponentUserLogin

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
else:
    urlpatterns = []

# url(r"^", include("jobs.urls", namespace="jobs") ),
urlpatterns += [
    url(r'^admin/', include(wagtailadmin_urls)),
    url(r'^documents/', include(wagtaildocs_urls)),

    url(r'^404/$', defaults.page_not_found, ),
    url(r'^500/$', defaults.server_error ),

    url(r'^members/', include("component_sites.urls_1.members_urls", namespace="members")),
    url(r'^jobs/', include("component_sites.urls_1.jobs_urls", namespace="jobs")),
    url(r'^', include("component_sites.urls_1.login_urls", namespace="login")),
    url(r'^events/', include("component_sites.urls_1.events_urls", namespace="events")),
    # url(r'^blog/', include("component_sites.urls_1.blog_urls", namespace="component_blog")),
    url(r'^news/', include("component_sites.urls_1.news_urls", namespace="news")),
    url(r"^store/", include("store.urls", namespace="store")),
    # url(r'^store/', include("component_sites.urls_1.jobs_urls", namespace="store")),
    url(r"^foundation/", include("store.urls_foundation", namespace="foundation")),
    url(r"^registrations/", include("registrations.urls", namespace="registrations")),
    # url(r'^login/$', ComponentUserLogin.as_view()),
    # url(r'^logout/$', auth_views.logout, {'next_page': '/login/'}),
    url(r'^search/$', ComponentSearchView.as_view()),
    # url(r"^", include("myapa.urls")),
    # url(r"^", include("blog.urls", namespace="blog") ),

    url(r'', include(wagtail_urls))

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
