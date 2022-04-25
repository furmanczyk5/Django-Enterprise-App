from django.conf.urls import url
from . import views

urlpatterns = [

    url(r"^search/$", views.SearchView.as_view() ),
    url(r"^details/(?P<master_id>\d+)/$", views.ImageDetails.as_view(), name="image-details" ),

    url(r"^submissions/dashboard/$", views.ImageSubmissionDashboard.as_view(), name="submissions_dashboard" ),
    url(r"^submissions/add/$", views.ImageSubmissionCreateFormView.as_view(), name="submissions_add" ),
    url(r"^submissions/(?P<master_id>\d+)/update/$", views.ImageSubmissionEditFormView.as_view(), name="submissions_edit" ),
    url(r"^submissions/(?P<master_id>\d+)/review/$", views.ImageSubmissionReviewFormView.as_view(), name="submissions_review" ),
    url(r"^submissions/(?P<master_id>\d+)/preview/$", views.ImageSubmissionPreviewView.as_view(), name="submissions_preview" ),
    url(r"^submissions/(?P<master_id>\d+)/delete/$", views.ImageSubmissionDeleteView.as_view(), name="submissions_delete" ),

]
