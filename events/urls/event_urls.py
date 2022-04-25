from django.conf.urls import include, url

from events.views import speaker_confirmation, ticket_views, \
    events_reports_views, submission_views, search_views
from comments.views import EventEvaluationFormView, EventEvaluationDeleteView, \
    EventEvaluationConfirmationView, CadmiumEventEvaluationRedirectView

urlpatterns = [
    # Disabling for APA Learn Launch
    # url(r'^ondemand/$', search_views.OnDemandSearchView.as_view(), name='ondemand_search'),
    # url(r'^ondemand/sale/$', search_views.OnDemandSaleSearchView.as_view(), name='ondemand_sale_search'),
    # url(r'^ondemand/npc17/$', search_views.OnDemandNPC17SearchView.as_view(), name='ondemand_npc17_search'),
    # url(r'^events/course/(?P<master_id>\d+)/$', search_views.OnDemandDetailsView.as_view(), name="ondemand_details"),
    url(r'^events/course/(?P<master_id>\d+)/activate/$', search_views.OnDemandActivateView.as_view(), name="ondemand_activate"),
    url(r"^events/$", search_views.CalendarSearchView.as_view()),
    url(r"^access/$", search_views.ProfessionalDevelopmentSearchView.as_view()),
    url(r'^events/speaker/confirm/(?P<confirm_role_id>\d+)/$', speaker_confirmation.contactrole_confirm),             # Participant Confirmation
    url(r'^events/speaker/confirm/update_bio/$', speaker_confirmation.contactrole_confirm_bio),
    url(r'^events/manage/(?P<master_id>\d+)/reports/$', events_reports_views.EventReports.as_view()),
    url(r'^events/manage/(?P<master_id>\d+)/downloadreport/$', events_reports_views.ReportsDownload.as_view(), name= "reports_download"),



    url(r'^events/tickets/$', ticket_views.PrintPurchasesView.as_view()),

    url(r'^events/submissions/speaker_formset/display_record/(?P<speaker_id>\d+)/$', submission_views.SubmissionSpeakerRecordDisplay.as_view()),

    url(r"^events/cadmium/(?P<cadmium_key>\d+)/evaluation/$", CadmiumEventEvaluationRedirectView.as_view(), name="cadmium_evaluation_redirect"),
    url(r"^events/(?P<master_id>\d+)/evaluation/$", EventEvaluationFormView.as_view(), name="event_evaluation_form"),
    url(r"^events/(?P<master_id>\d+)/evaluation/delete/$", EventEvaluationDeleteView.as_view(), name="event_evaluation_delete"),
    url(r"^events/(?P<master_id>\d+)/evaluation/confirmation/$", EventEvaluationConfirmationView.as_view(), name="event_evaluation_confirmation"),

    url(r'^events/speakers/', include('events.urls.speaker_urls')),

    url(
        r'^events/eventmulti/(?P<master_id>\d+)/$',
        search_views.EventMultiDetailsView.as_view(),
        name='eventmulti_details'
    )
]
