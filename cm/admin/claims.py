import pytz
from decimal import Decimal

from django.forms import ModelForm, ChoiceField
from django.contrib import admin, messages

from content.admin_abstract import BaseContentAdmin
from content.forms import DateTimeTimezoneField
from comments.admin import CommentAdmin

from cm.models import Log, Claim, Period, CMComment


class PeriodAdmin(BaseContentAdmin):
    # this is not complete. need to incorporate webgroup check and add to
        # celery so the drop does not time out
    show_cm_period_log_drop = False
    model = Period

    list_display = ["code"]
    fieldsets = [(None, {
        "fields": (
            "title", ("code", "status",), "description",
            "begin_time", "end_time", "grace_end_time",
            "rollover_from")})]

    def change_view(self, request, object_id, form_url='', extra_context=None):

        # add check here for webgroup
        extra_context = {}
        extra_context["extra_save_options"] = {
            "show_cm_period_log_drop": self.show_cm_period_log_drop,
        }

        return super().change_view(
            request, object_id, form_url, extra_context=extra_context)

    def add_view(self, request, form_url='', extra_context=None):

        # add check here for webgroup
        extra_context = {}
        extra_context["extra_save_options"] = {
            "show_cm_period_log_drop":self.show_cm_period_log_drop,
        }

        return super().add_view(request, form_url,
            extra_context=extra_context)

    def response_add(self, request, obj):
        return_action = self.publishable_button_actions(request, obj)
        return_super = super().response_change(request, obj)
        return return_action or return_super

    def response_change(self, request, obj):
        return_action = self.publishable_button_actions(request, obj)
        return_super = super().response_change(request, obj)
        return return_action or return_super

    def publishable_button_actions(self, request, obj):
        if "_drop_cm_logs" in request.POST:
            results = obj.drop_exempt_members()
            messages.success(request,'Successfully dropped oustanding %s logs for the %s period' % (str(results), obj.code))


class ClaimAdminForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_time_fields()

    def init_time_fields(self):

        if self.data:  # when submitting data
            # to handle both single forms and formsets:
            timezone_key = ("" if not self.prefix else self.prefix) + ("-" if self.prefix else "") + "timezone"
            initial_timezone = self.data.get(timezone_key) or "US/Central"
        elif self.instance and getattr(self.instance, "timezone", None): # when viewing existing data
            initial_timezone = getattr(self.instance, "timezone")
        else:  # when new
            initial_timezone = self.initial.get("timezone", None) or "US/Central"

        self.fields["timezone"] = ChoiceField(
            label="Time Zone",
            required=False,
            choices=[(None, "")] + [(tz,tz) for tz in pytz.all_timezones],
            initial="US/Central")

        self.fields["begin_time"] = DateTimeTimezoneField(required=False, timezone_str=initial_timezone)
        self.fields["end_time"] = DateTimeTimezoneField(required=False, timezone_str=initial_timezone)

    # def clean(self):
    #     cleaned_data = super().clean()
    #     if ( cleaned_data.get("begin_time") or cleaned_data.get("end_time") ) and not cleaned_data.get("timezone"):
    #         self.add_error("timezone", "Please provide a timezone for the times specified")
    #     return cleaned_data

    class Meta:
        model = Claim
        fields = "__all__"


class ClaimAdmin(admin.ModelAdmin):
    list_display = ("contact", "get_event_master_id", "event", "submitted_time")
    model = Claim
    form = ClaimAdminForm
    raw_id_fields=["contact", "event", "log", "comment"]
    autocomplete_lookup_fields = { "fk" : ["contact", "event", "log", "comment"]}
    search_fields = ["event__master__id", "event__title"]
    # list_filter = [NationalConferenceFilter]
    fields = ("contact", "log", "event", "comment", "verified",
        "credits", "law_credits", "ethics_credits", "equity_credits", ("targeted_credits", "targeted_credits_topic"),
        "is_speaker", "is_author", "is_carryover", "self_reported", "is_pro_bono",
        "title", "provider_name",
        "begin_time", "end_time", "timezone",
        "description", "learning_objectives",
        "city", "state", "country",
        "author_type")

    def get_queryset(self, request):
        return super().get_queryset(request).exclude(is_deleted=True).select_related("event__master")

    def get_event_master_id(self, obj):
        return obj.event.master_id if obj.event else None
    get_event_master_id.short_description = "Event Master ID"

    def delete_model(self, request, obj):
        obj.is_deleted = True
        obj.save()

    def get_actions(self, request):
        """
        disable delete selected!
        """
        actions = super().get_actions(request)
        actions["no_choices_available"] = (self.no_choices_available, "no_choices_available", "No Choices Available")
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def no_choices_available(self, modeladmin, request, queryset):
        """
        Admin action to prevent grappelli from freaking out when then aren't any choices.
        """
        pass

class CMCommentAdmin(CommentAdmin):
    model = CMComment


class ClaimInline(admin.StackedInline):
    model = Claim
    form = ClaimAdminForm
    # TO DO... MAKE A CUSTOM FORM THAT CAN ALSO SHOW THE RELATED COMMENT

    # fields = ["rating_understood_audience", "rating_quality_content", "rating_presented_well", "rating_present_again"]
    # fields = ["role_type","sort_number",("invitation_sent","confirmed"),"special_status",("permission_content","permission_av"),"content_rating"]
    extra = 0
    raw_id_fields=["contact", "event"]
    readonly_fields = ["contact", "comment"] # TO DO... remove this in order to make comment an inline
    fields = ("contact", "log", "event", "comment", "verified",
        "credits", "law_credits", "ethics_credits", "equity_credits", ("targeted_credits", "targeted_credits_topic"),
        "is_speaker", "is_author", "is_carryover", "self_reported", "is_pro_bono",
        "title", "provider_name",
        "begin_time", "end_time", "timezone",
        "description", "learning_objectives",
        "city", "state", "country",
        "author_type")

    # classes=( "grp-collapse grp-open",)
    # list_display = ["contactrole__contact__first_name"]

    def get_queryset(self, request):
        return super().get_queryset(request).exclude(is_deleted=True)


class LogAdminForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["equity_credits_required"].initial = Decimal("0.00")


class LogAdmin(admin.ModelAdmin):
    model = Log
    form = LogAdminForm
    inlines = (ClaimInline,)
    change_list_template = "admin/change_list_filter_sidebar.html"
    change_list_filter_template = "admin/filter_listing.html"

    search_fields = ("contact__user__username", "contact__first_name", "contact__last_name")

    fields = ("contact", "period", "status", "is_current", "credits_required", "law_credits_required",
            "ethics_credits_required", "equity_credits_required", ("targeted_credits_required", "targeted_credits_topic"),
            "begin_time", "end_time", "reinstatement_end_time", "get_credits_overview")

    readonly_fields = ("get_credits_overview",)

    # filter_horizontal = ()

    list_display = ["contact", "period", "status", "reinstatement_end_time"]

    list_filter = ("period", "status")

    raw_id_fields = ["contact"]
    autocomplete_lookup_fields = { "fk" : ["contact"] }


    def get_credits_overview(self, obj):
        credits_overview = obj.credits_overview()
        targeted_topic = credits_overview["targeted_credits_topic"]
        targeted_topic = targeted_topic or "TARGETED"
        return ( "TOTAL: " + str(credits_overview["general"]) +
                "<br/>LAW : " + str(credits_overview["law"]) +
                "<br/>ETHICS: " + str(credits_overview["ethics"]) +
                "<br/>EQUITY: " + str(credits_overview["equity"]) +
                "<br/>" + targeted_topic + ": " + str(credits_overview["targeted"]) +
                "<br/>SELF REPORTED : " + str(credits_overview["self_reported"]) +
                "<br/>AUTHORED: " + str(credits_overview["is_author"]))
    get_credits_overview.short_description = "Total credits earned"
    get_credits_overview.allow_tags = True

    def save_formset(self, request, form, formset, change):
        if formset.model == Claim:
            claims = formset.save(commit=False)
            formset.save_m2m()

            for obj in formset.deleted_objects:
                obj.is_deleted = True
                obj.save()
        else:
            super().save_formset(request, form, formset, change)


