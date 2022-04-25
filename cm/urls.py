from django.conf.urls import url

from events.views import submission_views
from . import views

urlpatterns = [

    url(r"^provider/$", views.redirect_to_myorg, name="provider_dashboard"),
    url(r"^provider/(?P<provider_id>\w+)/details/$", views.ProviderDetails.as_view(), name="provider_details"),

    url(r"^provider/application/$", views.ProviderApplicationView.as_view()),
    url(r"^provider/application/(?P<application_id>\d+)/$", views.ProviderPastApplicationView.as_view()),

    url(r"^provider/application/new/$", views.ProviderApplicationView.as_view(), name="provider_application_new"),
    url(r"^provider/application/(?P<application_id>\d+)/edit/$", views.ProviderApplicationView.as_view(), name="provider_application_edit"),
    url(r"^provider/application/(?P<application_id>\d+)/review/$", views.ProviderApplicationSubmissionReviewView.as_view(), name="provider_application_review"),
    url(r"^provider/application/(?P<application_id>\d+)/submission-confirmation/$", views.ProviderApplicationSubmissionConfirmationView.as_view(), name="provider_application_confirm"),

    url(r"^provider/registration/$", views.ProviderRegistrationView.as_view()),
    url(r"^provider/registration2015/$", views.ProviderRegistration2015View.as_view()),
    url(r"^provider/newrecord/$", views.ProviderNewRecord.as_view(), name ="provider_newrecord"),
    url(r"^provider/events/(?P<single_type>single|online)/add/$", submission_views.SingleEventSubmissionEditView.as_view() ),
    url(r"^provider/events/multi/add/$", submission_views.MultiEventSubmissionEditView.as_view() ),
    url(r"^provider/events/course/add/$", submission_views.CourseSubmissionEditView.as_view() ),
    url(r"^provider/events/info/add/$", submission_views.InfoEventSubmissionEditView.as_view() ),
    url(r"^provider/events/(?P<master_id>\d+)/update/$", submission_views.SubmissionFormRouteUpdateView.as_view() ),
    url(r"^provider/events/(?P<master_id>\d+)/speakers/$", submission_views.SubmissionFormRouteSpeakerView.as_view() ),
    url(r"^provider/events/(?P<master_id>\d+)/delete/$", submission_views.SubmissionFormRouteDeleteView.as_view() ),
    url(r"^provider/events/(?P<master_id>\d+)/review/$", submission_views.SubmissionFormRouteReviewView.as_view(), name="event_submission_review"),
    url(r"^provider/events/(?P<master_id>\d+)/activity/list/$", submission_views.MultiEventSubmissionActivitiesView.as_view(), name="multi_event_activities_view"),
    url(r"^provider/events/(?P<parent_master_id>\d+)/activity/add/$", submission_views.ActivitySubmissionEditView.as_view()),
    url(r'^provider/event/(?P<event_master_id>\d+)/comments/$', views.ProviderEventComments.as_view()),
    url(r'^provider/event/(?P<master_id>\d+)/ratings-and-comments/$', views.ProviderCommentsView.as_view(), name="provider_event_comments"),
    url(r'^provider/(?P<provider_id>\d+)/ratings-and-comments/$', views.ProviderCommentsView.as_view(), name="provider_comments"),

	url(r"^search/providers/$", views.ProviderSearchView.as_view() ),

    url(r'^search/$', views.CMSearchView.as_view()),
    url(r'^search/live/$', views.CMLiveEventSearchView.as_view()),
    url(r'^search/course/$', views.CMOnDemandSearchView.as_view()),

    url(r"^events/speaker/confirm/(?P<contact_role_id>\d+)/$", views.SpeakerConfirmRole.as_view() ),

    url(r"^log/claim/selfreport/(?P<claim_id>\d+)/$", views.SelfReportClaimFormView.as_view()),
    url(r"^log/claim/selfreport/$", views.SelfReportClaimFormView.as_view()),
    url(r"^log/claim/author/(?P<claim_id>\d+)/$", views.AuthorClaimFormView.as_view()),
    url(r"^log/claim/author/$", views.AuthorClaimFormView.as_view()),
    url(r"^log/claim/event/(?P<master_id>\d+)/$", views.EventClaimFormView.as_view()),
    url(r"^log/claim/delete/(?P<claim_id>\d+)/$", views.ClaimDeleteView.as_view()), # TO DO... this would be better handled through a REST api call

    url(r"^log/$", views.LogView.as_view(), name="log"),

    url(r"^log/(?P<period_code>\w+)/$", views.LogView.as_view(), name = "log_view"),

    url(r"^log/claim/(?P<claim_id>\d+)/$", views.ClaimDetailsView.as_view()),

    # used for the mobile app
    url(r"^log/claim/event/(?P<master_id>\d+)/confirmation/$", views.EventClaimConfirmationView.as_view(), name="event_claim_confirmation")


]
