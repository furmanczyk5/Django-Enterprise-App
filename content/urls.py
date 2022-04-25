from django.conf.urls import url
from django.views.generic import RedirectView

from content import views
from media import views as media_views

urlpatterns = [

    url(r"^(|/)$", views.HomePageView.as_view()),

    url(r'^search/$', views.GeneralSearch.as_view()),
    url(r'^content/(?P<master_id>\d+)/(?P<return_type>json)/', views.content_json),

    url(r'^admin/django_errors/$', views.admin_django_errorlog),
    url(r'^podcast/podcast.xml$', media_views.GetMediaRssXml.as_view()),
    url(r"^home/$", views.PlanningHomePageView.as_view(), name="planning_home"),

    url(r'^planificacion/.*$', RedirectView.as_view(url="/publications/document/9149225/")),
    url(r'^growingsmart/guidebook/.*$', RedirectView.as_view(url="/publications/document/9148731/")),

    url(r'^.*$', views.RenderContent.as_view()),
]
