from django.conf.urls import url

from .views import log as log_views

from cm.views import EventClaimFormView

from comments.views import EventEvaluationFormView, EventEvaluationDeleteView, \
    EventEvaluationConfirmationView


urlpatterns = [

    url(r'^learn/apa-learn-courses/$', log_views.LearnCourseCompletedView.as_view(), name="completed_courses"),
    url(r'^learn/hidden-pending-courses/$', log_views.LearnCourseHiddenView.as_view(), name="hidden_courses"),
    url(r"^courses/(?P<master_id>\d+)/evaluation/$", EventEvaluationFormView.as_view(), name="event_evaluation_form"),
    url(r"^courses/(?P<master_id>\d+)/evaluation/delete/$", EventEvaluationDeleteView.as_view(), name="event_evaluation_delete"),
    url(r"^courses/(?P<master_id>\d+)/evaluation/confirmation/$", EventEvaluationConfirmationView.as_view(), name="event_evaluation_confirmation"),

]
