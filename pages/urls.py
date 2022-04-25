from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^admin/(?P<content_id>\d+)/(?P<action>checkin|checkout)/$', views.AdminPageCheckinView.as_view(), name='checkin')
]
