from django.conf.urls import url

from ..views import (
    ConferenceScheduleView,
    MicrositeConferenceSearchView,
    MicrositeSearchView
)


urlpatterns = [
    # program urls
    # FLAGGED FOR REFACTORING: NPC DISABLE PROGRAM VIEWS/SEARCH
    # url(
    #     r'^search/$',
    #     MicrositeSearchView.as_view(),
    #     name='conference_microsite_search'),
    # url(
    #     r"^search/(?P<return_type>pdf|pdf-inline|json)/$",
    #     MicrositeSearchView.as_view()),
    # url(
    #     r"^program/search/$",
    #     MicrositeConferenceSearchView.as_view()),

    # my schedule urls
    url(
        r"^schedule/",
        ConferenceScheduleView.as_view()),
    url(
        r"^schedule/(?P<return_type>pdf|pdf-inline|json)/$",
        ConferenceScheduleView.as_view()),
]
