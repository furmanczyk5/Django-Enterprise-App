from django.conf.urls import url

from exam import views
from content import views as content_views

urlpatterns = [
    url(r'^certification/exam/registration/code-of-ethics/$', views.ExamCodeOfEthicsView.as_view(), name="exam_code_of_ethics"),
    url(r'^certification/exam/registration/$', views.ExamRegistrationView.as_view(), name="exam_registration"),
    url(r'^certification/pdo/exam-registration-search/$', views.ExamRegistrationSearch.as_view(), name="exam_registration_search"),

    url(r'^certification/exam/application/type/$', views.ExamApplicationTypeView.as_view(), name="exam_application_type"),
    url(r'^certification/exam/application/(?P<master_id>\d+)/type/$', views.ExamApplicationTypeView.as_view(), name="exam_application_type_edit"),
    url(r'^certification/exam/application/(?P<master_id>\d+)/job-history/$', views.ExamJobHistoryView.as_view(), name="exam_job_history"),
    url(r'^certification/exam/application/(?P<master_id>\d+)/degree-history/$', views.ExamDegreeHistoryView.as_view(), name="exam_degree_history"),
    url(r'^certification/exam/application/(?P<master_id>\d+)/criteria/$', views.ExamCriteriaView.as_view(), name="exam_criteria"),
    url(r'^certification/exam/application/(?P<master_id>\d+)/code-of-ethics/$', views.ExamApplicationCodeOfEthicsView.as_view(), name="exam_app_code_of_ethics"),
    url(r'^certification/exam/application/(?P<master_id>\d+)/summary/$', views.ExamSummaryView.as_view(), name="exam_application_summary"),
    url(r'^certification/exam/application/(?P<master_id>\d+)/degree-history/delete/$', views.degree_delete, name="degree_delete"),
    url(r'^certification/exam/application/(?P<master_id>\d+)/job-history/delete/$', views.job_delete, name="job_delete"),

    # URLs for exam application reviewers:
    url(r"^certification/exam/application/reviewer/$", views.ExamApplicationReviewerView.as_view(), name="exam_application_reviewer" ),
    url(r"^certification/exam/application/reviewer/complete/$", views.ExamApplicationReviewerCompleteView.as_view(), name="exam_application_reviewer_complete" ),
    url(r"^certification/exam/application/(?P<master_id>\d+)/reviewer/$", views.ExamApplicationReviewerEditView.as_view(), name="exam_application_reviewer_edit" ),
    url(r"^certification/exam/application/(?P<master_id>\d+)/(?P<review_round>\d+)/reviewer/$", views.ExamApplicationReviewerEditView.as_view(), name="exam_application_reviewer_edit" ),

    # OTHER APPLICATION TYPES:
    # url(r'^certification/exam/application/(?P<master_id>\d+)/mcip_submit/$', views.ExamApplicationMCIPSubmitView.as_view(), name="mcip_submit"),

    # AICP Prorated Dues
    url(r"^aicp/dues/initial/$", views.AicpProratedDuesProductView.as_view(), name="aicp_dues_prorated" ),

    # FAICP
    url(r"^faicp/$", views.FAICPListView.as_view(), name="faicp_list"),
    url(r"^faicp/faicp_statement/(?P<username>\d+)/$", views.FAICPStatementView.as_view(), name="faicp_statement"),

    # ASC
    url(r"^asc/$", views.ASCListView.as_view(), name="asc_list"),
    url(r"^asc/experience/(?P<username>\d+)/$", views.ASCExperienceView.as_view(), name="asc_experience"),

    # AICP Candidate Enrollment:
    url(r'^certification/candidate/enrollment/basic/$', views.AICPCandidateBasicInfoView.as_view(), name="candidate_basic"),
    url(r'^certification/candidate/enrollment/education/(?P<enroll_type>\w+)/$', views.AICPCandidateEducationView.as_view(), name="candidate_education"),
    url(r'^certification/candidate/enrollment/ethics/$', views.AICPCandidateCodeOfEthicsView.as_view(), name="candidate_ethics"),
    # url(r'^certification/candidate/enrollment/update/$', content_views.RenderContent.as_view(), name="update_success_page"),

    # AICP Candidate Registration
    # url(r'^certification/candidate/registration/education/$', views.AICPCandidateRegistrationEducationView.as_view(), name="candidate_registration_education"),
    url(r'^certification/candidate/registration/info/$', views.AICPCandidateRegistrationInfoView.as_view(), name="candidate_registration_info"),
    url(r'^certification/candidate/registration/ethics/$', views.AICPCandidateRegistrationCodeOfEthicsView.as_view(), name="candidate_registration_ethics"),

]
