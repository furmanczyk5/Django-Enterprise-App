from django.conf.urls import include, url

from events.views import speakers as speaker_views

urlpatterns = [

	url(r'^search/$', speaker_views.NPCSpeakerSearchView.as_view(), name="speakers_npc_search"),
	url(r'^admin/speaker/(?P<username>\d+)/publish/$', speaker_views.NPCSpeakerAdminPublishView.as_view(), name="speakers_admin_publish")

]