from wagtail.wagtailadmin import urls as wagtailadmin_urls
from wagtail.wagtaildocs import urls as wagtaildocs_urls
from wagtail.wagtailcore import urls as wagtail_urls

from django.views import defaults
from django.conf import settings
from django.conf.urls.static import static

from django.conf.urls import include, url
# from component_sites.views import *
# from store.views import checkout_views
from django.contrib.auth import views as auth_views
from myapa.views import ComponentUserLogin


if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
else:
    urlpatterns = []

# url(r"^", include("jobs.urls", namespace="jobs") ),
urlpatterns += [
    url(r'^login/$', ComponentUserLogin.as_view()),
    url(r'^logout/$', auth_views.logout, {'next_page': '/login/'}),

    # url(r'^cart/$', checkout_views.CartView.as_view(), name='cart'), 
]
