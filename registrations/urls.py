from django.conf.urls import url
from django.views.decorators.cache import never_cache

from . import views

urlpatterns = [

    url(r'^(?P<master_id>\d+)/$', views.SelectRegistrationOption.as_view(), name="select_registration"),
    url(r'^(?P<master_id>\d+)/badge/$', views.CustomizeBadgeView.as_view(), name="edit_badge"),
    url(r'^(?P<master_id>\d+)/activities/$', never_cache(views.AddActivitiesView.as_view()), name="add_activities"),

    # MICROSITE REGISTRATIONS /registations/<url_stem>/<master_id>/...
    url(r'^(?P<microsite_url_path_stem>\w+)/(?P<master_id>\d+)/$', views.SelectRegistrationOption.as_view(), name="microsite_select_registration"),
    url(r'^(?P<microsite_url_path_stem>\w+)/(?P<master_id>\d+)/badge/$', views.CustomizeBadgeView.as_view(), name="microsite_edit_badge"),
    url(r'^(?P<microsite_url_path_stem>\w+)/(?P<master_id>\d+)/activities/$', views.AddActivitiesView.as_view(), name="microsite_add_activities"),

    url(r'^admin/cancel/(?P<attendee_id>[0-9]+)/(?P<event_id>[0-9]+)/$', views.AdminCancelAttendeeView.as_view(), name="cancel"),

    # url(r'^admin/transfer_attendance/(?P<attendee_id>[0-9]+)/(?P<event_id>[0-9]+)/$', views.TransferAttendanceView.as_view(), name="transfer_attendance"),

    url(r'^option/(?P<event_id>[0-9]+)/$', views.RedirectOldRegistrationLinksView.as_view(),
        name='registration'),

    url(r'^includes/ticket-buttons/(?P<master_id>\d+)/$', views.TicketButtonsView.as_view(), name="ticket_buttons" ),

    # TO DO: delete
    # url(r'^confirmation/(?P<master_id>[0-9]+)/$', views.RegistrationConfirmationView.as_view(),
    #     name='registration_conformation'),

    url(r'^refunds/(?P<event_id>[0-9]+)/(?P<attendee_id>[0-9]+)/$', views.RefundCancelAttendeeView.as_view(), name="cancel_refund"),
    # url(r'^questions/(?P<event_id>[0-9]+)/$', views.EventQuestionsView.as_view(),
    #     name='event-questions'),
    # url(r'^sessions/(?P<event_id>[0-9]+)/$', views.EventSessionsView.as_view(),
    #     name='event-sessions'),

    url(r'^(?P<master_id>\d+)/ticket_printing/$', views.KioskTicketPrintingView.as_view(), name="admin_ticket_printing"),
    url(r'^(?P<master_id>\d+)/ticket_printing/refresh/$', views.KioskTicketPrintingAttendeesRefreshView.as_view(), name="admin_ticket_printing_refresh"),
    # url(r'^(?P<master_id>\d+)/ticket_printing/dismiss/$', views.kioskAdminDismissAttendees.as_view(), name="admin_ticket_printing_dismiss"),
    url(r'^(?P<master_id>\d+)/ticket_printing/print/$', views.KioskAdminPrintTickets.as_view(), name="admin_ticket_printing_print"),

    url(r'^staff/custom-tickets/$', views.CustomTicketPrintingFormView.as_view(), name="admin_adhoc_tickets"),

    url(r'^task/poll/$', views.PollTaskProgressView.as_view(), name="poll_task_progress"),
    url(r'^task/revoke/$', views.RevokeTaskView.as_view(), name="revoke_task"),
    url(r'^task/pdf/$', views.GetTaskPdfResult.as_view(), name="get_tickets_pdf"),
    url(r'^task/result/$', views.GetTaskResult.as_view(), name="get_task_result"),

    url(r'^(?P<master_id>\d+)/badge-and-tickets/(?P<paper_size>letter|sato|letter_time_correction)/$', views.PreviewMyBadgeAndTicketsView.as_view(), name="preview_badge_and_tickets"),

    url(r'^admin/attendee/(?P<attendee_id>[0-9]+)/$', views.RefundAttendeeView.as_view(), name="refund_attendee"),

    url(r'^admin/event-registration-sync/$', views.event_registration_sync),

]
