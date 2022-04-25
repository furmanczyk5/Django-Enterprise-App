from wagtail.wagtailadmin import urls as wagtailadmin_urls
from wagtail.wagtaildocs import urls as wagtaildocs_urls
from wagtail.wagtailcore import urls as wagtail_urls

from django.views import defaults
from django.conf import settings
from django.conf.urls.static import static

from django.conf.urls import include, url
from component_sites.views import *
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
    url(r'^admin-dashboard/$', ChapterJobAdminDashboardView.as_view(), name='admin_dashboard'),
    url(r'^search/$', ChapterJobSearchView.as_view(), name='search'),
    url(r'^post/type/$', ChapterJobSubmissionFormTypeView.as_view(), name='submission_type'),
    url(r'^post/(?P<master_id>\d+)/type/$', ChapterJobSubmissionFormTypeView.as_view(), name='submission_type_edit'),   
    url(r'^post/(?P<master_id>\d+)/details/$', ChapterJobSubmissionFormDetailsView.as_view(), name='submission_details'),
    url(r'^post/(?P<master_id>\d+)/delete/$', ChapterJobSubmissionFormDeleteView.as_view(), name='submission_delete'),
    url(r'^post/(?P<master_id>\d+)/review/$', ChapterJobSubmissionFormReviewView.as_view(), name='submission_review'),
    url(r'^ad/(?P<master_id>\d+)/$', ChapterJobDetailsView.as_view(), name='job_details'),
    url(r'^posts/$', JobsPostsView.as_view(), name='jobs_posts'),
    # url(r'^ad/(?P<master_id>\d+)/$', JobsDetailsView.as_view(), name='job_details'),
    # url(r'^cart/$', checkout_views.CartView.as_view(), name='cart'), 
]
