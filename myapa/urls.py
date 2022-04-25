from django.conf.urls import url

from django.contrib.auth import views as auth_views

import myapa.utils
import myapa.views.myorg.addresses
import myapa.views.myorg.contacts
import myapa.views.myorg.dashboard
import myapa.views.myorg.jobs
import myapa.views.myorg.admins
import myapa.views.myorg.profile
import myapa.views.myorg.events
import myapa.views.myorg.orders
import myapa.views.myorg.partners
from . import forms
from . import views

urlpatterns = [

    # STANDARD LOGIN/LOGOUT
    url(r'^login/$', views.UserLogin.as_view()),
    url(r'^logout/$', auth_views.logout, {'next_page': '/login/'}),
    url(r'^auto_login_via_mobile/$', views.AutoLoginViaMobile.as_view()),

    # ADMIN ACTIONS
    url(r'^admin/(?P<username>[0-9]+)/auto_login/$', views.login_as_user,),

    url(r'^admin/resend_invite/(\d+)/$', views.resend_mail_invite),
    url(r'^admin/update_groups/$', views.admin_update_groups),

    # sends the email
    url(r"^password_reset/$", views.ResetPasswordView.as_view(), name="password_reset"),

    # shows success message for the above
    url(r'^password_reset_done/$', auth_views.password_reset_done, dict(
        template_name="myapa/newtheme/password/reset-done.html"), name="password_reset_done"),
    # checks the link the user clicked and prompts for a new password

    # shows a success message for the above
    url(r'^password_reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$', auth_views.password_reset_confirm, dict(
                template_name="myapa/newtheme/password/reset-confirm.html",
                post_reset_redirect="/password_done",
                set_password_form=forms.MyapaSetPasswordForm),
        name='password_reset_confirm'),
        # shows a success message for the above
    url(r'^password_done/$', auth_views.password_reset_complete, dict(
        template_name="myapa/newtheme/password/reset-complete.html")),

    # CHANGING PASSWORD, is this for users or admins?
    url(r'^myapa/password_change/$', auth_views.password_change, dict(
        template_name="myapa/newtheme/password/change-form.html",
        post_change_redirect="/myapa/password_change_done/"),  name="password_change"),
    url(r'^myapa/password_change_done/$', auth_views.password_change_done, dict(
        template_name="myapa/newtheme/password/change-done.html"), name="password_change_done"),

    # PLANNING MAGAZINE
    url(r'^api/0.1/planning_mag_access/$', views.planning_mag_access),

    # OVERDRIVE
    # url(r'^myapa/overdrive/(?P<LibraryCard>\d+)&(?P<PIN>\d+)', views.overdrive_access),
    url(r'^api/0.2/overdrive/authenticate/$', views.overdrive_access),

    # NON MEMBER CREATE ACCOUNT
    url(r'^myapa/account/create/$', views.NonMemberJoinView.as_view(), name="nonmember_join"),
    # NON MEMBER CREATE ACCOUNT FOR ADMINS
    url(
        r'myapa/account/create/admin/$',
        views.join.NonMemberJoinViewAdmin.as_view(),
        name="nonmember_join_admin"
    ),

    # JOIN PROCESS
    url(r'^join/account/$', views.JoinAccountView.as_view(), name="join_account"),
    url(r'^join/personal-information/$', views.JoinPersonalInformationView.as_view(), name="join_personal_info"),
    url(r'^join/enhance-membership/$', views.JoinEnhanceMembershipView.as_view(), name="join_subscriptions"),
    url(r'^join/summary/$', views.JoinMembershipSummaryView.as_view(), name="join_summary"),

    # JOIN PROCESS FOR STUDENTS
    url(r'^join/student/account/$', views.StudentJoinAccountView.as_view(), name="join_student_account"),
    url(r'^join/student/school-information/$', views.StudentJoinSchoolInformationView.as_view(), name="join_student_school_information"),
    url(r'^join/student/personal-information/$', views.StudentJoinPersonalInformationView.as_view(), name="join_student_personal_info"),
    url(r'^join/student/enhance-membership/$', views.StudentJoinEnhanceMembershipView.as_view(), name="join_student_subscriptions"),
    url(r'^join/student/summary/$', views.StudentJoinMembershipSummaryView.as_view(), name="join_student_summary"),
    url(r'^join/student/confirmation/$', views.StudentJoinConfirmationView.as_view(), name="join_student_confirmation"),

    # FREESTUDENT ADMINS
    url(r'^freestudents/admin/dashboard/$', views.FreeStudentAdminRouteSchool.as_view(), name="freestudents_admin_dashboard"),
    url(r'^freestudents/(?P<school_id>\d+)/admin/dashboard/$', views.FreeStudentAdminDashboard.as_view(), name="freestudents_school_admin_dashboard"),
    url(r'^freestudents/(?P<school_id>\d+)/admin/student/create/$', views.FreeStudentAdminEditStudentFormView.as_view(), name="freestudents_admin_student_create"),
    url(r'^freestudents/(?P<school_id>\d+)/admin/student/(?P<student_id>\d+)/edit/$', views.FreeStudentAdminEditStudentFormView.as_view(), name="freestudents_admin_student_edit"),
    url(r'^freestudents/(?P<school_id>\d+)/admin/student/(?P<student_id>\d+)/delete/$', views.FreeStudentAdminDeleteStudentFormView.as_view(), name="freestudents_admin_student_delete"),
    # url(r'^freestudents/(?P<school_id>\d+)/admin/student/(?P<student>\d+)/view/$', views.FreeStudentAdminRouteSchool.as_view(), name="freestudents_admin_student_view"),

    # MYAPA INFO
    url(r'^myapa/$', views.MyapaOverviewView.as_view(), name="myapa"),

    url(r'^myapa/account/$', views.MyapaAccountFormView.as_view(), name="update_account"),
    url(r'^myapa/addresses/$', views.MyapaAddressesFormView.as_view(), name="update_addresses"),
    url(r'^myapa/personal-information/$', views.MyapaPersonalInformationFormView.as_view(), name="update_personal_info"),
    # url(r'^myapa/password/$', views.MyapaChangePasswordView.as_view(), name="update_addresses"),

    url(r'^myapa/profile/bio/$', views.UpdateBioAndAboutMe.as_view()),
    url(r'^myapa/profile/image/update/$', views.UpdateProfileImageView.as_view(), name="profile_image_update"),
    url(r'^myapa/social_links/update/$', views.UpdateSocialLinksView.as_view()),
    url(r'^myapa/education/update/$', views.EducationView.as_view()),
    url(r'^myapa/job_history/update/$', views.JobHistoryView.as_view()),
    url(r'^myapa/additional_address/delete/$', views.del_additional_address, name="additional_address_del"),
    url(r'^myapa/events/$', views.EventsAttendedView.as_view()),
    url(r'^myapa/details/delete/$', myapa.utils.details_delete, name="details_delete"),
    url(r'^myapa/orderhistory/$', views.OrderHistoryView.as_view(), name="order_history"),
    url(r'^myapa/bookmark/(?P<master_id>\d+)/$', myapa.utils.bookmark),
    url(r'^myapa/bookmarks/$', views.BookmarksView.as_view()),
    url(r'^myapa/aicp-status/$', views.AICPStatusView.as_view()),

    url(r'^myapa/contactpreferences/update/$', views.ContactPreferencesUpdateView.as_view(), name="contactpreferences_update"),

    url(r'^myapa/student/freedivisions/$', views.StudentUpdateDivisionsView.as_view(), name="myapa_student_freedivisions"),

    # MYAPA INFO FOR STUDENTS
        # do we need separate urls for students, what's the difference?
    url(r'^myapa/account/student/$', views.JoinAccountView.as_view(), name="update_student_account"),
    url(r'^myapa/personal_information/student/$', views.JoinPersonalInformationView.as_view(), name="update_student_personal_info", kwargs={"join_type":"student"}),
    # url(r'^myapa/addresses/student/$', views.JoinAddressesView.as_view(), name="update_student_addresses"),

    # MYAPA PROFILE
    url(r'^myapa/profile/sharing/$', views.ProfileShareView.as_view(), name='edit_profile_sharing'),
    url(r'^myapa/profile/generate_url/$', views.generate_url, name="url_generator"),
    url(r'^myapa/profile/$', views.EditProfileView.as_view(), name='edit_profile'),
    url(r'^profile/(?P<slug>[0-9A-Za-z_\-]+)/$', views.PublicProfileView.as_view(), name="public_profile"),
    url(r'^myapa/profile/resume/$', views.ResumeUploadView.as_view(), name="resume_upload"),


    url(r'^conference/admin/create-django-user/$', views.CreateDjangoUserView.as_view()),
    url(r'^merge-check/$', views.MergeCheckView.as_view(), name="merge_check"),

    url(r'^authentication/npc-proposals/sso/$', views.ProposalsSsoView.as_view(), name="npcproposals_sso"),
    url(r'^authentication/npc-proposals/sso/login/$', views.ProposalsSsoLoginView.as_view() ,name="npcproposals_login"),
    url(r'^authentication/npc-proposals/user/$', views.ProposalsSsoUserDataView.as_view(), name="npcproposals_user"),

    url(r'^engage/$', views.EngageSsoLoginView.as_view(), name="engage_sso"),
    url(r'^learn/sso/$', views.LearnSsoView.as_view(), name="learn_sso"),

    # CONTACT API (for LMS and eventually others...)
    url(r'^api/0.4/contact/(?P<token>[0-9A-Za-z_\-]+)/$', views.ApiGetContactView.as_view(), name="api_contact"),
    url(r'^api/0.4/search_contacts/$', views.ApiSearchContactsView.as_view(), name="api_search_contacts"),
    url(r'^api/0.4/conference/schedule/$', views.ApiGetScheduleView.as_view(), name="api_get_schedule_view"),
    url(r'^api/0.4/conference/schedule/update/$', views.ApiUpdateScheduleView.as_view(), name="api_get_update_view"),
    url(r'^api/0.4/login/$', views.ApiLoginView.as_view(), name="api_login_view"),
    url(r'^login/sso/$', views.MobileSsoView.as_view(), name="mobile_sso_view"),
    url(r'^login/higher_logic/$', views.HigherLogicApiLoginView.as_view(), name="higher_logic_api_login_view"),
    url(r'^openwater/create-cm-tracker/$', views.ApiCMTrackerCreateView.as_view(), name="create_cm_tracker_view"),

    # My Org
    url(r'^myorg/$', myapa.views.myorg.dashboard.MyOrganizationDashboardView.as_view(), name="myorg"),
    url(r'^myorg/addresses/$', myapa.views.myorg.addresses.MyOrganizationAddressesView.as_view(), name="myorg_addresses"),
    url(r'^myorg/contacts/$', myapa.views.myorg.contacts.MyOrganizationContactsView.as_view(), name="myorg_contacts"),
    url(r'^myorg/jobs/$', myapa.views.myorg.jobs.OrgJobsView.as_view(), name='myorg_jobs'),
    url(r'^myorg/admins/delete/$', myapa.views.myorg.admins.AdminDeleteView.as_view()),
    url(r'^myorg/admins/add/$', myapa.views.myorg.admins.AdminAddView.as_view(), name='myorg_admin_add'),
    url(r'^myorg/admins/autocomplete/$', myapa.views.myorg.admins.AdminSearchAutocompleteView.as_view()),
    url(r'^myorg/logo/$', myapa.views.myorg.profile.OrgLogoView.as_view(), name='myorg_logo'),
    url(
        r'^myorg/employer_bio/$',
        myapa.views.myorg.profile.OrgEmployerBioView.as_view(),
        name='myorg_employer_bio'
    ),
    url(
        r'^myorg/org_bio/$',
        myapa.views.myorg.profile.OrgBioView.as_view(),
        name='myorg_org_bio'
    ),
    url(
        r'^myorg/events/$',
        myapa.views.myorg.events.OrgEventsView.as_view(),
        name='myorg_events'
    ),
    url(
        r'^myorg/orders/$',
        myapa.views.myorg.orders.OrgOrdersView.as_view(),
        name='myorg_orders'
    ),
    url(
        r'^myorg/partners/$',
        myapa.views.myorg.partners.OrgPartnersView.as_view(),
        name='myorg_partners'
    ),
    url(
        r'^myorg/logo/delete/$',
        myapa.views.myorg.profile.OrgLogoDeleteView.as_view(),
        name='org_logo_delete'
    ),
    url(
        r'^eval-data-download/$',
        myapa.views.myorg.eval_data.MyOrganizationEvalDataDownloadView.as_view(),
        name='eval_data_download'
    ),

    url(r'^sbs/vote/$', views.SurveyBallotSystemsRedirectView.as_view(), name="sbs_redirect"),

    # Open Water
    url(r'^openwater/$', views.OpenWaterSsoLoginView.as_view(), name="open_water_sso"),
    url(r'^openwater/sso/$', views.OpenWaterSsoLoginPart2View.as_view(), name="open_water_sso2"),

]
