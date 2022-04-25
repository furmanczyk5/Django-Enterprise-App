from django.conf.urls import url
from django.views.generic.base import TemplateView
from . import views


urlpatterns = [
    url(r'^(?P<media_id>\d+)/html/$', views.GetMediaHtmlView.as_view(), name='admin_search'),
    url(r'^media/(?P<master_id>\d+)/file/', views.GetFile.as_view(), name='get_file'),
    url(r'^media/(?P<master_id>\d+)/last-updated/json/', views.GetFileLastUpdated.as_view(), name='get_file'),


        # google auth for MJ - should be able to delete once he's done with it
    url(r'^google1a042d700e2a61dc.html', TemplateView.as_view(template_name='google1a042d700e2a61dc.html')),
   
]
