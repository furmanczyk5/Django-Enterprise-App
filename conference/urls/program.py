from django.conf.urls import url

from ..views import (
    ConferenceActivityDetailsView,
    ConferenceScheduleView,
    MicrositeConferenceSearchView,
    MicrositeSearchView,
)

from conference.views.program.join_waitlist import JoinWaitListView
from conference.views.program.microsite_pdf import MicrositePDFExportView

urlpatterns = [
    # program urls
    # using the Program search view (with filters and program search template)
    # FLAGGED FOR REFACTORING: NPC DISABLE PROGRAM VIEWS/SEARCH
    # url(
    #     r'^search/$',
    #     MicrositeSearchView.as_view(),
    #     name="conference_search"
    # ),
    # url(
    #     r"^search/(?P<return_type>pdf|pdf-inline|json)/$",
    #     MicrositePDFExportView.as_view()),
    # url(
    #     r"^program/search/$",
    #     MicrositeConferenceSearchView.as_view()
    # ),
    # url(
    #     r"^program/search/(?P<conference_year>\d{4})/$",
    #     MicrositeConferenceSearchView.as_view()
    # ),

    # npc activity details
    url(
        r'^nationalconferenceactivity/(?P<master_id>\d+)/$',
        ConferenceActivityDetailsView.as_view()
    ),
    url(
        r'^nationalconferenceactivity/(?P<master_id>\d+)/details/$',
        ConferenceActivityDetailsView.as_view()
    ),

    # my schedule urls
    url(
        r"^schedule/$",
        ConferenceScheduleView.as_view()
    ),
    url(
        r"^schedule/(?P<return_type>pdf|pdf-inline|json)/$",
        ConferenceScheduleView.as_view()
    ),
    url(
        r"^join-wait-list/$",
        JoinWaitListView.as_view()
    ),
]
