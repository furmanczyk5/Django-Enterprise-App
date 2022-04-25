from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'^admin-dashboard/$', views.InquiryAdminDashboard.as_view(), name="inquiry_dashboard"),
    url(r'^create/$', views.InquirySubmissionEditFormView.as_view(), name="inquiry_create"),
    url(r'^(?P<master_id>\d+)/update/$', views.InquirySubmissionEditFormView.as_view(), name="inquiry_update"),
    url(r'^(?P<master_id>\d+)/uploads/$', views.InquirySubmissionUploadsFormView.as_view(), name="inquiry_uploads"),
    url(r'^(?P<master_id>\d+)/review/$', views.InquirySubmissionReviewFormView.as_view(), name="inquiry_review"),
    url(r'^(?P<master_id>\d+)/thankyou/$', views.InquirySubmissionThankYou.as_view(), name="inquiry_thankyou"),
    url(r'^(?P<master_id>\d+)/preview/$', views.InquiryPreviewView.as_view(), name="inquiry_preview"),

]