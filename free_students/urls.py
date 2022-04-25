from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^admin-dashboard/$', views.FreeStudentAdminDashboard.as_view(), name='student_dashboard'),
    url(r'^student/create/$', views.FreeStudentEditFormView.as_view(), name='student_create'),
    url(r'^student/(?P<student_id>\d+)/edit/$', views.FreeStudentEditFormView.as_view(), name='student_edit'),
    url(r'^student/(?P<student_id>\d+)/delete/$', views.FreeStudentDeleteView.as_view(), name='student_delete'),
    url(r'^student/(?P<student_id>\d+)/details/$', views.FreeStudentDetailsView.as_view(), name='student_details'),
]
