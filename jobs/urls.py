from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^jobs/search/$', views.JobSearchView.as_view(), name='search'),
    url(r'^jobs/admin-dashboard/$', views.JobAdminDashboard.as_view(), name='admin_dashboard'),
    url(r'^jobs/post/type/$', views.JobSubmissionFormTypeView.as_view(), name='submission_type'),
    url(r'^jobs/post/(?P<master_id>\d+)/type/$', views.JobSubmissionFormTypeView.as_view(), name='submission_type_edit'),   
    url(r'^jobs/post/(?P<master_id>\d+)/details/$', views.JobSubmissionFormDetailsView.as_view(), name='submission_details'),
    url(r'^jobs/post/(?P<master_id>\d+)/delete/$', views.JobSubmissionFormDeleteView.as_view(), name='submission_delete'),
    url(r'^jobs/post/(?P<master_id>\d+)/review/$', views.JobSubmissionFormReviewView.as_view(), name='submission_review'),

    url(r'^jobs/ad/(?P<master_id>\d+)/$', views.JobDetailsView.as_view(), name='job_details'),
    url(r'^salary/worksheet/$', views.JobSalaryWorksheetView.as_view(), name='salary_worksheet'),
]