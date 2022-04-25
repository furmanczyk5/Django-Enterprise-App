from django.conf.urls import url

from myapa import views as myapa_views
from conference.views import api as api_views

urlpatterns = [
    ##################################
    # conference mobile app api urls #
    ##################################
    # Use this regex to match any version (?P<version>\d+(\.\d+)*)
    # Version currently includes 0.0(2015), 0.1(2016), and 0.2(2017)
    url(r"^login/$", myapa_views.login_mobile ),
    url(r"^logout/$", myapa_views.logout_mobile ),
    url(r"^contact/$", myapa_views.get_contact_mobile ),
    url(r"^activities/$", api_views.MobileAppMicrositeSearchView.as_view(), kwargs=dict(return_type="json")),
    url(r"^schedule/$", api_views.ScheduleIdsView.as_view() ),
    url(r"^schedule/update/$", api_views.ScheduleUpdate.as_view() ),
    url(r"^schedule/add/(?P<master_id>\d+)/$", api_views.ScheduleAdd.as_view() ),
    url(r"^schedule/remove/(?P<master_id>\d+)/$", api_views.ScheduleRemove.as_view() ),
    url(r"^attendees/$", api_views.ConferenceAttendeesJsonView.as_view() ),

]