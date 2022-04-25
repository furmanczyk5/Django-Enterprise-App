import pdfkit
import nested_admin

from django.contrib import admin, messages
from django.template.loader import render_to_string
from django.conf import settings
from django.http import HttpResponse
from django.core.urlresolvers import reverse

from content.models import ContentTagType, TagType
from content.admin import ContentAdmin, TagListFilter, \
    PublishStatusListFilter, TaxoTopicTagInline, JurisdictionInline, \
    CommunityTypeInline, ContentTagTypeInline, get_FormatInline, \
    CollectionRelationshipInline, SearchTopicInline
from store.admin import ProductInline
from myapa.admin import ContactRoleAdmin, ContactRoleInlineContact
from ui.utils import get_css_path_from_less_path
from events.forms import EventAdminAuthorForm, EventAdminEditorForm

from events.utils.exports import national_export_xlsx
from events.utils.sync import harvester_sync_selected
from .models import Event, Activity, EventSingle, EventMulti, Course, \
    Speaker, NATIONAL_CONFERENCES, NATIONAL_CONFERENCE_ADMIN
from conference.models import NationalConferenceActivity, NationalConferenceContributor


class APAProviderFilter(admin.SimpleListFilter):
    """
    List filter for publish status
    """
    title = 'APA Provider Filter'
    parameter_name = 'providers'

    def lookups(self, request, model_admin):
        lookup_tuple = (
            ("APA_NAT", "APA (National)"),
            ("APA_ALL", "All APA (including chapters and divisions)"),
            ("NON_APA", "Not APA")
        )
        return lookup_tuple

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        elif self.value() == "APA_NAT":
            return queryset.filter(
                contacts__user__username__in=["119523", "050501"])
        elif self.value() == "APA_ALL":
            return queryset.filter(contacts__company_is_apa=True)
        else:
            return queryset.exclude(contacts__company_is_apa=True)


class EventAdmin(nested_admin.NestedModelAdmin, ContentAdmin):
    """
    Admin for all event records (Single, Multi, Activities, Courses)
    """

    # needs provider name
    list_display = (
            "get_master_id", "code", "title",
            "get_local_begin_time", "get_local_end_time",
            "event_type", "status",
            "cm_status", "cm_approved", "has_cm_law", "has_cm_ethics", "has_cm_equity", "has_cm_targeted",
            "get_provider_name")
    list_filter = ("event_type", "status", "cm_status",
                   TagListFilter, PublishStatusListFilter, APAProviderFilter)

    search_fields = ("=master__id", "title", "code",
                     "=contacts__user__username", "contacts__title")

    list_display_links = ["get_master_id", "code", "title"]

    readonly_fields = ContentAdmin.readonly_fields + (
        "content_type", "get_local_begin_time", "get_local_end_time",
        "submission_change_form_link", "get_provider_name")

    date_hierarchy = 'begin_time'

    format_tag_defaults = []
    format_tag_choices = ["FORMAT_LIVE_IN_PERSON_EVENT", "FORMAT_ON_DEMAND_EDUCATION", "FORMAT_APA_LEARN"]
    author_form_class = EventAdminAuthorForm
    editor_form_class = EventAdminEditorForm

    inlines = [
        TaxoTopicTagInline, JurisdictionInline, CommunityTypeInline,
        SearchTopicInline, ContentTagTypeInline, #get_FormatInline(tag_codes=format_tag_choices),
        ContactRoleInlineContact, ProductInline, CollectionRelationshipInline]

    def get_local_begin_time(self, obj):
        if obj.begin_time:
            return obj.begin_time_astimezone().strftime("%a, %b %d %Y, %I:%M %p %Z")
    get_local_begin_time.short_description = "Local Begin Time"
    get_local_begin_time.admin_order_field = "begin_time"

    def get_local_end_time(self, obj):
        if obj.end_time:
            return obj.end_time_astimezone().strftime("%a, %b %d %Y, %I:%M %p %Z")
    get_local_end_time.short_description = "Local End Time"
    get_local_end_time.admin_order_field = "end_time"

    def get_provider_name(self, obj):
        return next((cr.contact.title for cr in obj.contactrole.all() if cr.role_type == "PROVIDER"), "")
    get_provider_name.short_description = "Provider"

    fieldsets = [
        (None, {
            "fields":(  "title",
                        "learning_objectives",
                        "text",
                        ("parent_landing_master", "url"),
                        "description",
                        "code",
                        ("featured_image", "featured_image_display",),
                        ("thumbnail", "thumbnail_html"),
                        # "has_xhtml", # now, everything has xhtml... we should remove this field from the model...
            ),
        }),
        ("Event Fields", {
            "fields":(("event_type"), "location", ("begin_time","end_time", "timezone"), ("city", "state", "country"),

                ("is_free", "is_online"),
                ("price_early_cutoff_time","price_regular_cutoff_time","price_late_cutoff_time"),
                 "digital_product_url", "ticket_template", "outside_vendor",

                "submission_change_form_link")
        }),
        ("Certification Maintenance",{
            "classes":("collapse","grp-collapse grp-closed",),
            "fields":("cm_status",
                        "cm_approved", "cm_law_approved", "cm_ethics_approved",
                        "cm_equity_credits", ("cm_targeted_credits", "cm_targeted_credits_topic")
                        )
        }),
        ("Advanced Content Management Settings", {
            "classes":( "grp-collapse grp-closed",),
            "fields":(
                ("template", "status"),
                ("resource_url"),
                ("publish_time", "make_public_time",),
                ("archive_time", "make_inactive_time",),
                ("workflow_status", "editorial_comments"),
                ("parent", "slug"),
                "permission_groups",
                "keywords",
                ("og_title", "og_url"),
                ("og_type", "og_image"),
                ("og_description",)
            )
        }),
    ]

    show_sync_imis = True
    show_provider_submit = True
    show_sync_harvester = True

    change_form_template = "admin/events/event/change-form.html"

    def submission_change_form_link(self, obj):
        """for quick access to the submission record"""
        if obj.publish_status != "SUBMISSION":
            submission = type(obj).objects.filter(publish_uuid=obj.publish_uuid, publish_status="SUBMISSION").first()
            submisson_admin_url = reverse("admin:{app_label}_{model_name}_change".format(app_label=obj._meta.app_label, model_name=obj._meta.model_name), args=[submission.id])
            return "<a target='_blank' href='{url}'>Edit Submission Record</a>".format(url=submisson_admin_url)
        else:
            return "<span>Currently Editing the Submission Record</span>"
    submission_change_form_link.allow_tags = True
    submission_change_form_link.short_description = "Edit Submission"

    def publishable_extra_context(self, request, extra_context=None):
        extra_context = extra_context or {}
        context = super().publishable_extra_context(request, extra_context=extra_context)

        extra_save_options = context.get("extra_save_options", {})
        extra_save_options.update(dict(
            show_provider_submit=self.show_provider_submit
        ))
        context["extra_save_options"] = extra_save_options

        return context

    def publishable_button_actions(self, request, obj):

        super_reponse = super().publishable_button_actions(request, obj)
        if super_reponse:
            return super_reponse

        if "_provider_submit" in request.POST:
            obj.provider_submit_async()
            messages.success(request, "%s was queued to be submitted." % obj)

    def get_queryset(self, request):
        return super(ContentAdmin, self).get_queryset(request).select_related("master", "master__content_live")

    def response_add(self, request, obj):
        return_action = self.change_form_button_actions(request, obj)
        return_super = super().response_add(request, obj)
        return return_action or return_super

    def response_change(self, request, obj):
        return_action = self.change_form_button_actions(request, obj)
        return_super = super().response_change(request, obj)
        return return_action or return_super

    def change_form_button_actions(self, request, obj):
        if "_sync_harvester" in request.POST:
            results = obj.sync_from_harvester(request)
            messages.success(request,'Successfully synced \"%s\" from the Harvester to Django' % (obj.title))

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['cm_status'].label = 'CM Status'
        form.base_fields['cm_approved'].label = 'CM Credits'
        form.base_fields['cm_law_approved'].label = 'CM Law Credits'
        form.base_fields['cm_ethics_approved'].label = 'CM Ethics Credits'
        form.base_fields['cm_equity_credits'].label = 'CM Equity Credits'
        form.base_fields['cm_targeted_credits'].label = 'CM Targeted Credits'
        form.base_fields['cm_targeted_credits_topic'].label = 'CM Targeted Credits Topic'
        return form

    class Media:
        js = ContentAdmin.Media.js + ("pages/checkin/js/admin-page-checkin.js",)
        css = {
            'all':ContentAdmin.Media.css.get("all") + ("pages/checkin/css/admin-page-checkin.css",)
        }


class DefaultFormatEventAdmin(EventAdmin):
    format_tag_defaults = ["FORMAT_LIVE_IN_PERSON_EVENT"]
    format_tag_choices = []
    inlines = [
        TaxoTopicTagInline, JurisdictionInline, CommunityTypeInline,
        SearchTopicInline, ContentTagTypeInline, ContactRoleInlineContact,
        ProductInline, CollectionRelationshipInline
    ]


class EventMultiAdmin(DefaultFormatEventAdmin):
    """
    Admin for Multi Part Event Records
    """
    readonly_fields = EventAdmin.readonly_fields + ('event_type',)
    list_filter = [x for x in EventAdmin.list_filter if x not in ["event_type"]] # removes event_type from filters

class EventSingleAdmin(DefaultFormatEventAdmin):
    """
    Admin for Single Event Records
    """
    readonly_fields = EventAdmin.readonly_fields + ('event_type',)
    list_filter = [x for x in EventAdmin.list_filter if x not in ["event_type"]] # removes event_type from filters

    def assign_default_format_tags(self, obj):
        """
        method to assign default format tags, in most cases just use the format_tag_defaults attribute,
        but for more complex cases override this method
        """
        default_tags = None
        if obj.is_online:
            default_tags = ["FORMAT_LIVE_ONLINE_EVENT"] if obj.is_online else self.format_tag_defaults
            remove_tags = ["FORMAT_LIVE_ONLINE_EVENT"] if not obj.is_online else self.format_tag_defaults

        if default_tags:
            format_tagtype = TagType.objects.prefetch_related("tags").get(code="FORMAT")
            format_contenttagtype, is_created = ContentTagType.objects.get_or_create(content=obj, tag_type=format_tagtype)
            format_contenttagtype.tags.remove(*[t for t in format_tagtype.tags.all() if t.code in remove_tags])
            format_contenttagtype.tags.add(*[t for t in format_tagtype.tags.all() if t.code in default_tags])


class ActivityAdmin(DefaultFormatEventAdmin):
    """
    Admin for Activity Records
    """
    from learn.admin.learn_course_admin import ContentRelationshipInline, LearnCourseInfoInline

    readonly_fields = EventAdmin.readonly_fields + ('event_type',)
    list_filter = [x for x in EventAdmin.list_filter if x not in ["event_type"]] # removes event_type from filters
    search_fields = ["=master__id", "title", "code", "=parent__content_live__code", "=parent__content_draft__code"]

    actions = ["print_unsold_tickets"]
    inlines = DefaultFormatEventAdmin.inlines + [ContentRelationshipInline,] + [LearnCourseInfoInline,]


    def print_unsold_tickets(modeladmin, request, queryset):

        activities = queryset.exclude(master__content_live__product__isnull=True).prefetch_related("master__content_live__product__prices")
        activities = [a.master.content_live.event for a in activities if a.master.content_live]

        unsold_tickets = []
        for activity in activities:
            if activity.product.max_quantity: # don't print extra tickets unless there is a limit?
                purchase_info = activity.product.get_purchase_info()
                num_unsold = purchase_info.get("regular_remaining", 0)
                unsold_ticket = {
                    "unsold_ticket":True,
                    "title":activity.title,
                    "begin_time":activity.begin_time,
                    "price":next((p.price for p in activity.product.prices.all() if p.status == "A"), 0.00),
                }
                for i in range(0,int(num_unsold)):
                    ticket_copy = unsold_ticket.copy()
                    ticket_copy["number"] = i + 1 # int starting at 1
                    unsold_tickets.append(ticket_copy)

        grouped_unsold_tickets = [unsold_tickets[i:i+6] for i in range(0, len(unsold_tickets), 6)]

        the_css = get_css_path_from_less_path(["/static/content/css/style.less","/static/registrations/css/tickets.less"])
        the_html = render_to_string("registrations/tickets/chapter-registrations.html", {"grouped_attendees":grouped_unsold_tickets})

        the_options = {
            "page-size": "Letter",
            "margin-top": "0.0in",
            "margin-right": "0.0in",
            "margin-bottom": "0.0in",
            "margin-left": "0.0in"
        }
        config = pdfkit.configuration(wkhtmltopdf=settings.WKHTMLTOPDF_PATH)
        the_pdf  = pdfkit.from_string(the_html, False, css=the_css, options=the_options, configuration=config)

        response = HttpResponse(the_pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="badges-and-sessions.pdf"'

        return response

    class Media:
        js = (
            "//ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js",
            # "/static/registrations/js/admin.js"
        )


class CourseAdmin(DefaultFormatEventAdmin):
    """
    Admin for Activity Records
    """
    readonly_fields = EventAdmin.readonly_fields + ('event_type',)
    list_filter = [x for x in EventAdmin.list_filter if x not in ["event_type"]] # removes event_type from filters
    format_tag_defaults = ["FORMAT_ON_DEMAND_EDUCATION"]


class NationalConferenceFilter(admin.SimpleListFilter):

    title = 'National Conference Year'
    parameter_name = 'conference_year'
    default_choice = NATIONAL_CONFERENCE_ADMIN

    def lookups(self, request, model_admin):
        lookup_list = sorted(NATIONAL_CONFERENCES, reverse=True)
        index_of_default = [y[0] for y in lookup_list].index(self.default_choice[0])
        lookup_list[index_of_default] = (None, self.default_choice[1])
        return lookup_list

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() is None: # default to most recent conference
            return queryset.filter(parent__content_live__code=self.default_choice[0])
        else:
            return queryset.filter(parent__content_live__code=self.value())


class ParticipantNationalConferenceFilter(NationalConferenceFilter):

    def queryset(self, request, queryset):
        if self.value() is None: # default to most recent conference
            return queryset.filter(content__parent__content_live__code=NATIONAL_CONFERENCE_ADMIN[0])
        else:
            return queryset.filter(content__parent__content_live__code=self.value())


class NationalConferenceActivityAdmin(ActivityAdmin):
    """
    Admin for NPC Activity Records
    """
    from learn.admin.learn_course_admin import ContentRelationshipInline, LearnCourseInfoInline

    actions = [national_export_xlsx, harvester_sync_selected]
    list_filter = ActivityAdmin.list_filter + [NationalConferenceFilter]

    readonly_fields = ActivityAdmin.readonly_fields + (
        "get_local_begin_time", "get_local_end_time")

    list_display = ("get_master_id", "title", "code", "get_local_begin_time",
                    "get_local_end_time", "status", "get_year", "get_track",
                    "cm_approved", "cm_law_approved", "cm_ethics_approved") # needs has_draft
    list_display_links = ("get_master_id", "title")
    inlines = DefaultFormatEventAdmin.inlines + [ContentRelationshipInline,]

    def get_local_begin_time(self, obj):
        if obj.begin_time:
            return obj.begin_time_astimezone().strftime("%a, %b %d %Y, %I:%M %p %Z")
    get_local_begin_time.short_description = "Local Begin Time"
    get_local_begin_time.admin_order_field = "begin_time"

    def get_local_end_time(self, obj):
        if obj.end_time:
            return obj.end_time_astimezone().strftime("%a, %b %d %Y, %I:%M %p %Z")
    get_local_end_time.short_description = "Local End Time"
    get_local_end_time.admin_order_field = "end_time"

    def get_year(self, obj):
        parent_code = obj.parent.content_live.code
        for conf in sorted(NATIONAL_CONFERENCES, reverse=True):
            if conf[0] == parent_code:
                return conf[1]
        return ""
    get_year.short_description = "Year"

    def get_category(self, obj):
        if obj.submission_category:
            return obj.submission_category.title
        else:
            return ""
    get_category.short_description = "Category"
    get_category.admin_order_field = "submission_category__title"

    def get_track(self, obj):
        ctt=ContentTagType.objects.filter(content=obj, tag_type__code__contains="TRACK").first()
        track = ctt.tags.first() if ctt else None
        return track if track else "None"
    get_track.short_description = "Program Area (formerly Track)"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("parent__content_live", "master", "submission_category")



# Only if we want a separate section for Participants
class NationalConferenceContributorAdmin(ContactRoleAdmin):
    fields = ContactRoleAdmin.fields

    readonly_fields=['id','contact_link','content_link','get_username',]

    list_display = ContactRoleAdmin.list_display + ["confirmed", "invitation_sent"]
    list_filter = ["confirmed", "invitation_sent", "role_type","content__content_type", "content__status", ParticipantNationalConferenceFilter]

    def get_username(self, obj):
        if not obj.contact:
            return None
        if not obj.contact.user:
            return None
        return obj.contact.user.username
    get_username.short_description = "User ID"
    get_username.admin_order_field = "contact__user__username"

    def get_user_email(self, obj):
        if not obj.contact:
            return None
        return obj.contact.email
    get_user_email.short_description = "Email"
    get_user_email.admin_order_field = "contact__email"

    def get_queryset(self, request):
        # also only events with parent NPC! or some tag?
        return super().get_queryset(request).select_related("content__parent__content_live")


class SpeakerAdmin(ContactRoleAdmin):
    pass
    # TO DO...???

admin.site.register(Event, EventAdmin)
admin.site.register(Activity, ActivityAdmin)
admin.site.register(EventSingle, EventSingleAdmin)
admin.site.register(EventMulti, EventMultiAdmin)
admin.site.register(Course, CourseAdmin)

admin.site.register(NationalConferenceActivity,NationalConferenceActivityAdmin)
admin.site.register(NationalConferenceContributor,NationalConferenceContributorAdmin)

admin.site.register(Speaker, SpeakerAdmin)
