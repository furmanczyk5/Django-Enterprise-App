from django.conf.urls import url

from awards import views

urlpatterns = [
    url(r"^mynominations/$", views.MyNominations.as_view(), name="mynominations" ),
    url(r"^mynominations/categories/$", views.SelectAwardsCategory.as_view(), name="select_submission_category"),
    url(r"^mynominations/submission/add/$", views.AwardsSubmissionEditFormView.as_view(), name="submission_new" ),
    url(r"^mynominations/submission/(?P<master_id>\d+)/update/$", views.AwardsSubmissionEditFormView.as_view(), name="submission_update" ),
    url(r"^mynominations/submission/(?P<master_id>\d+)/uploads/$", views.AwardsSubmissionUploadsView.as_view(), name="submission_uploads" ),
    url(r"^mynominations/submission/(?P<master_id>\d+)/review/$", views.AwardsSubmissionReviewFormView.as_view(), name="submission_review" ),
    url(r"^mynominations/submission/(?P<master_id>\d+)/complete/$", views.AwardsSubmissionCompletedRedirectView.as_view(), name="submission_complete" ),
    url(r"^mynominations/submission/(?P<master_id>\d+)/preview/$", views.AwardsSubmissionPreviewView.as_view(), name="submission_preview" ),

    url(r"^jury/myreviews/$", views.JurorMyListView.as_view(), name="juror_list" ),
    url(r'^jury/myreviews/(?P<master_id>\d+)/view/$', views.AwardDetailsView.as_view(), name="submission_view"),
    url(r"^jury/myreviews/(?P<master_id>\d+)/review/$", views.AwardJurorDetailsView.as_view(), name="juror_review"),

]
