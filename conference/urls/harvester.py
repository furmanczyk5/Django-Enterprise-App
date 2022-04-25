from django.conf.urls import url

from conference.views import harvester as views

urlpatterns = [

# Harvester integration
url(r'^presentations/add/(?P<external_key>\d+)/$', views.UpdatePresentation.as_view()),
url(r'^presentations/delete/(?P<external_key>\d+)/$', views.DeletePresentation.as_view()),
url(r'^presentations/update/(?P<external_key>\d+)/$', views.UpdatePresentation.as_view()),
url(r'^presenters/add/(?P<external_id>\d+)/$', views.UpdatePresenter.as_view()),
url(r'^presenters/update/(?P<external_id>\d+)/$', views.UpdatePresenter.as_view()),
# url(r'^sync-all/$', views.HarvesterSyncAllView.as_view()),
]
