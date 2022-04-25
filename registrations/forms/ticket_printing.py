from django import forms
from django.contrib.admin import widgets as admin_widgets

from events.models import EVENT_TICKET_TEMPLATES


class CustomTicketPrintingForm(forms.Form):
    ticket_template = forms.ChoiceField(
        choices=EVENT_TICKET_TEMPLATES,
        required=True, label="Template")

    badge_name = forms.CharField(required=False, label="Badge Name")
    badge_fullname = forms.CharField(required=False, label="Full Name")
    badge_company = forms.CharField(required=False, label="Company")
    badge_location = forms.CharField(required=False, label="Location")
    badge_membertype = forms.CharField(required=False, label="Member Type")
    badge_userid = forms.CharField(required=False, label="User ID")
    badge_regclass = forms.CharField(required=False, label="Registration Class Code")

    session_code = forms.CharField(required=False, label="Session Code")
    session_title = forms.CharField(required=False, label="Session Title")
    session_standby = forms.BooleanField(required=False, label="Is this a Standby Ticket?")
    session_begintime = forms.SplitDateTimeField(
        widget=admin_widgets.AdminSplitDateTime(),
        required=False, label="Session Begin Date and Time")
    session_location = forms.CharField(required=False, label="Session Location/Room")
    session_price = forms.CharField(required=False, label="Ticket Price")
    session_description = forms.CharField(required=False, label="Session Description")

    nonbadge_fullname = forms.CharField(required=False, label="User Full Name")
    nonbadge_userid = forms.CharField(required=False, label="User ID")
    nonbadge_membertype = forms.CharField(required=False, label="Member Type Code")
    nonbadge_regclass = forms.CharField(required=False, label="User Registration Class Code")
