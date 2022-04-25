from django.conf.urls import url

from consultants import views

urlpatterns = [

    url(r'^dashboard/$', views.ConsultantDashboard.as_view(), name="consultant_dashboard"),
    url(r'^profile/preview/(?P<org_id>\d+)/$', views.ConsultantPreviewView.as_view(), name="consultant_preview"),
    url(r'^profile/display/(?P<org_id>\d+)/$', views.ConsultantDisplayView.as_view(), name="consultant_display"),
    url(r'^profile/confirmation/(?P<org_id>\d+)/$', views.ConsultantConfirmationView.as_view(), name="consultant_submit"),
    url(r'^profile/create/$', views.ConsultantProfileView.as_view(), name="profile_create"),
    url(r'^profile/update/(?P<org_id>\d+)/$', views.ConsultantProfileView.as_view(), name="profile_update"),
    url(r'^list/$', views.ConsultantListView.as_view(), kwargs={"code":"CONSULTANT"}, name="consultant_list"),
    url(r'^profile/branch/$', views.ConsultantBranchView.as_view(), kwargs={"code":"CONSULTANT"}, name="manage_branch_offices"),
    url(r'^profile/branch/(?P<org_id>\d+)/$', views.ConsultantBranchView.as_view(), name="manage_branch_offices"),    
    url(r'^profile/branch/(?P<org_id>\d+)/delete/$', views.branch_delete, name="branch_delete"),

    url(r'^rfp/admin-dashboard/$', views.RFPAdminDashboard.as_view(), name="rfp_dashboard"),
    url(r'^rfp/create/$', views.RFPSubmissionEditFormView.as_view(), name="rfp_create"),
    url(r'^rfp/(?P<master_id>\d+)/update/$', views.RFPSubmissionEditFormView.as_view(), name="rfp_update"),
    url(r'^rfp/(?P<master_id>\d+)/review/$', views.RFPSubmissionReviewFormView.as_view(), name="rfp_review"),
    url(r'^rfp/(?P<master_id>\d+)/thankyou/$', views.RFPSubmissionThankYou.as_view(), name="rfp_thankyou"),
    url(r'^rfp/(?P<master_id>\d+)/preview/$', views.RFPPreviewView.as_view(), name="rfp_preview"),

    url(r'^rfp/search/$', views.RFPSearchView.as_view(), name="rfp_search"),
    url(r'^rfp/(?P<master_id>\d+)/$', views.RFPDetailsView.as_view(), name="rfp_details")

]
