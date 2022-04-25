from django.contrib import admin, messages
from django import forms
from django.contrib.staticfiles.templatetags.staticfiles import static

from myapa.admin import IndividualContactAdmin
# from registrations.admin import NationalConferenceAttendeeAdmin
from store.models import Order
from content.models import TagType

from .models import Microsite, CadmiumSync, CadmiumMapping
# from .models import MicrositeAttendee

# PROGRAM_SEARCH_FILTER_CODES = [
#     "TIME_OF_DAY",
#     "SEARCH_TOPIC",
#     "CM_FILTER",
#     "EVENTS_NATIONAL_TYPE",
#     "DIVISION",
#     "EVENTS_NATIONAL_TRACK"
# ]

class ConferenceOrderInline(admin.TabularInline):
    model = Order

class MicrositeAdminForm(forms.ModelForm):
  class Meta:
    model = Microsite
    exclude = []
    widgets = {
        "home_summary_blurb":forms.Textarea(attrs={"class":"ckeditor"}),
        "program_blurb":forms.Textarea(attrs={"class":"ckeditor"}),
        "text_blurb_one": forms.Textarea(attrs={"class": "ckeditor"}),
        # "details_inclusive_blurb":forms.Textarea(attrs={"class":"ckeditor"}),
        "details_local_blurb":forms.Textarea(attrs={"class":"ckeditor"}),
        "interactive_educational_session":forms.Textarea(attrs={"class":"ckeditor"})
    }

  def __init__(self, *args, **kwargs):
    super(MicrositeAdminForm, self).__init__(*args, **kwargs)
    self.fields['program_search_filters'].queryset = TagType.objects.filter().order_by("title")
    self.fields['text_blurb_one'].label = "Recorded session html blurb"


class MicrositeAdmin(admin.ModelAdmin):
    form = MicrositeAdminForm
    list_display = ["short_title", "url_path_stem", "home_page_code"]
    # search_fields = ["user__username", "first_name", "last_name"]
    filter_horizontal = ("program_search_filters",)
    raw_id_fields = ["event_master", "home_page"]#, "search_filters"]
    autocomplete_lookup_fields = {
        "fk": ("event_master", "home_page")
    }
    list_per_page = 20
    fieldsets = [
            (None, {
                "fields": (
                    ("short_title", "url_path_stem"),
                    ("home_page_code"),
                    ("event_master", "home_page"),
                    ("status", "is_npc"),
                    ("program_search_filters"),
                    ("deactivation_date"), #"show_skip_to_dates"),
                    ("custom_color", "hero_image_path"),
                    ("home_summary_blurb"),
                    ("program_blurb"),
                    ("header_ad"),
                    ("sidebar_ad"),
                    ("footer_ad"),
                    ("interstitial_ad"),
                    ("internal_header_ad"),
                    ("internal_sidebar_ad"),
                    ("internal_footer_ad"),
                    ("internal_interstitial_ad"),
                    ("signpost_logo_image_path"),
                    ("nosidebar_breakout_image_path"),
                    ("text_blurb_one"),
                    # ("details_inclusive_blurb"),
                    ("details_local_blurb"),
                    ("interactive_educational_session"))
            })
        ]
    # readonly_fields = [
    #         "get_username", "get_fullname",
    #         "company", "chapter", "get_address", "email",
    #         "phone", "cell_phone",
    #         "member_type", "get_password_form_link", "get_attendee_filter_link"
    #         ]
    # inlines = [ConferenceAttendeeInline]
    class Media:
        # js = ['/static/content/js/tinymce/tinymce.min.js', '/static/content/js/tinymce/tinymce_setup.js',]
        js = (
            "//ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js",
            static("content/js/jquery-ui.min.js"),
            static("ckeditor/ckeditor.js")+"?v=3",
            # static("ckeditor/plugins/lite/lite-interface.js")+"?v=3",
            static("ui/modal/js/modal.js"),
            static("prettydiff/lib/language.js"),
            static("prettydiff/lib/finalFile.js"),
            static("prettydiff/lib/safeSort.js"),
            static("prettydiff/ace/ace.js"),
            static("prettydiff/api/dom.js"),
            static("prettydiff/lib/csspretty.js"),
            static("prettydiff/lib/csvpretty.js"),
            static("prettydiff/lib/diffview.js"),
            static("prettydiff/lib/jspretty.js"),
            static("prettydiff/lib/markuppretty.js"),
            static("prettydiff/prettydiff.js"),

            static("prettydiff/adminSetup.js")
        )
        css = {
             'all': (
                static("ckeditor/plugins/planning_media/admin.css"),
                static("ui/modal/css/modal.css"),
                static("prettydiff/css/global.css"),
                static("prettydiff/css/reports.css"),
                static("prettydiff/css/color_white.css"),
                static("prettydiff/css/color_canvas.css"),
                static("prettydiff/css/color_shadow.css"),
                static("prettydiff/css/page_specific.css"))
        }

# GOES AWAY WITH EVENT REG IN IMIS:
# class ConferenceAttendeeInline(admin.TabularInline):
#     model = MicrositeAttendee
#     verbose_name_plural = "Attendance/tickets"
#     verbose_name = "Reg/ticket"
#     fields = ["event", "status", "purchase", "last_printed_time"]
#     readonly_fields = ["last_printed_time"]
#     raw_id_fields = ["event", "purchase"]
#     autocomplete_lookup_fields = {'fk': ['event', 'purchase']}
#     extra = 0

#     def save_model(self, request, attendee, form, change):
#         if not attendee.purchase:
#             # TO DO... set purchase to some dummy purchase?
#             pass
#         super().save_model(request, attendee, form, change)
#         messages.info(request, "saved attendee inline")


# class MicrositeAttendeeAdmin(NationalConferenceAttendeeAdmin):
#     list_display = ["get_username", "contact", "purchase", "status","get_purchase_submitted_time","get_member_type"]
#     list_per_page = 20

#     def get_actions(self, request):
#         """
#         disable delete selected!
#         """
#         actions = super().get_actions(request)
#         if "delete_selected" in actions:
#             del actions["delete_selected"]
#         return actions


class CadmiumMappingForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['from_string'].label = 'FROM Field or Datum'
        self.fields['to_string'].label = 'TO Field or Datum'

    class Meta:
        model = CadmiumMapping
        exclude = []


class SyncMappingRoleInline(admin.TabularInline):
    model = CadmiumSync.mappings.through
    extra = 0
    title = "Harvester Speaker Role Mappings"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "mapping":
            kwargs["queryset"] = CadmiumMapping.objects.filter(
                mapping_type="HARVESTER_ROLE_TO_DJANGO_ROLE")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            mapping__mapping_type="HARVESTER_ROLE_TO_DJANGO_ROLE").order_by(
            "mapping__from_string", "mapping__to_string")

class SyncMappingSessionTypeInline(admin.TabularInline):
    model = CadmiumSync.mappings.through
    extra = 0
    title = "Harvester Session Type Mappings"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "mapping":
            kwargs["queryset"] = CadmiumMapping.objects.filter(
                mapping_type="HARVESTER_SESSION_TYPE_TO_ACTIVITY_TYPE")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            mapping__mapping_type="HARVESTER_SESSION_TYPE_TO_ACTIVITY_TYPE").order_by(
            "mapping__from_string", "mapping__to_string")

class SyncMappingTrackInline(admin.TabularInline):
    model = CadmiumSync.mappings.through
    extra = 0
    title = "Harvester Track Mappings"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "mapping":
            kwargs["queryset"] = CadmiumMapping.objects.filter(
                mapping_type="HARVESTER_TRACK_TO_APA_CODE")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            mapping__mapping_type="HARVESTER_TRACK_TO_APA_CODE").order_by(
            "mapping__from_string", "mapping__to_string")

class SyncMappingTopicInline(admin.TabularInline):
    model = CadmiumSync.mappings.through
    extra = 0
    title = "Harvester Topic Mappings"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "mapping":
            kwargs["queryset"] = CadmiumMapping.objects.filter(
                mapping_type="HARVESTER_TOPICS_TO_APA_TAXO")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            mapping__mapping_type="HARVESTER_TOPICS_TO_APA_TAXO").order_by(
            "mapping__from_string", "mapping__to_string")


class SyncMappingPresentationInline(admin.TabularInline):
    model = CadmiumSync.mappings.through
    extra = 0
    title = "Harvester Presentation Field Mappings"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "mapping":
            kwargs["queryset"] = CadmiumMapping.objects.filter(
                mapping_type="PRESENTATION_FIELD_TO_POSTGRES_FIELD")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            mapping__mapping_type="PRESENTATION_FIELD_TO_POSTGRES_FIELD").order_by(
            "mapping__from_string", "mapping__to_string")


class SyncMappingPresenterInline(admin.TabularInline):
    model = CadmiumSync.mappings.through
    extra = 0
    title = "Harvester Presenter Field Mappings"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "mapping":
            kwargs["queryset"] = CadmiumMapping.objects.filter(
                mapping_type="PRESENTER_FIELD_TO_POSTGRES_FIELD")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            mapping__mapping_type="PRESENTER_FIELD_TO_POSTGRES_FIELD").order_by(
            "mapping__from_string", "mapping__to_string")



class SyncMappingCustomPresentationInline(admin.TabularInline):
    model = CadmiumSync.mappings.through
    extra = 0
    title = "Custom Presentation Field Mappings"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "mapping":
            kwargs["queryset"] = CadmiumMapping.objects.filter(
                mapping_type="CUSTOM_PRES_FIELD_TO_POSTGRES_FIELD")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            mapping__mapping_type="CUSTOM_PRES_FIELD_TO_POSTGRES_FIELD").order_by(
            "mapping__from_string", "mapping__to_string")

class SyncMappingCustomPresenterInline(admin.TabularInline):
    model = CadmiumSync.mappings.through
    extra = 0
    title = "Custom Presenter Field Mappings"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "mapping":
            kwargs["queryset"] = CadmiumMapping.objects.filter(
                mapping_type="PRESENTER_CUSTOM_FIELD_TO_POSTGRES_FIELD")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            mapping__mapping_type="PRESENTER_CUSTOM_FIELD_TO_POSTGRES_FIELD").order_by(
            "mapping__from_string", "mapping__to_string")


class CadmiumSyncAdmin(admin.ModelAdmin):
    list_display = ["cadmium_event_key", "get_microsite_name", "endpoint"]
    raw_id_fields = ["microsite"]
    list_per_page = 20
    readonly_fields = ["get_microsite_name"]
    inlines = (SyncMappingRoleInline, SyncMappingSessionTypeInline,
               SyncMappingTrackInline, SyncMappingTopicInline,
               SyncMappingPresentationInline, SyncMappingPresenterInline,
               SyncMappingCustomPresentationInline, SyncMappingCustomPresenterInline)

    def get_microsite_name(self, obj):
        return "<h3>%s</h3>" % (obj.microsite.event_master)
    get_microsite_name.allow_tags = True
    get_microsite_name.short_description = 'Microsite Name'


class CadmiumMappingAdmin(admin.ModelAdmin):
    form = CadmiumMappingForm
    list_display = ["mapping_type", "from_string", "to_string"]
    list_per_page = 20

# admin.site.register(MicrositeAttendee, MicrositeAttendeeAdmin)
admin.site.register(Microsite, MicrositeAdmin)
admin.site.register(CadmiumSync, CadmiumSyncAdmin)
admin.site.register(CadmiumMapping, CadmiumMappingAdmin)



