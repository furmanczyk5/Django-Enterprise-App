import pickle

from django.contrib import admin
from django.forms.models import modelform_factory
from django.core.urlresolvers import reverse
from django.db.models import Max

from store.admin import OrderAdmin

from cm.models import Provider, ProviderApplication, \
    ProviderRegistration, CMOrder, PROVIDER_APPLICATION_REVIEW_STATUSES
from cm.tasks import start_periodic_reviews


class ProviderApplicationInline(admin.StackedInline):
    model = ProviderApplication
    extra = 0


class ProviderRegistrationInline(admin.StackedInline):
    model = ProviderRegistration
    readonly_fields = ["purchase"]
    raw_id_fields = ["shared_from_partner_registration"]
    autocomplete_lookup_fields = {"fk": ["shared_from_partner_registration"]}
    extra = 0
    # TO DO... MAKE A CUSTOM FORM THAT CAN ALSO SHOW THE RELATED COMMENT


class ProviderAdmin(admin.ModelAdmin):
    model = Provider

    raw_id_fields = ['user']
    list_display = [
        'user',
        'title',
        'city',
        'state',
        'ein_number',
        'company_is_apa',
        'application_approved_through',
        "application_review_step"
    ]
    inlines = [ProviderApplicationInline, ProviderRegistrationInline]
    readonly_fields = ["contact_type"]
    search_fields = ("user__username", "company", "city")

    actions = ["start_periodic_review_process"]

    fieldsets = [
        (None, {

            "fields": (("user", "contact_type", "company_is_apa"), ("company", "ein_number"))

        }),
        ("Contact Info", {
            "classes": ("grp-collapse grp-open",),
            "fields": ("email",
                       ("phone", "cell_phone"))
        }),
        ("MyAPA", {
            "classes": ("grp-collapse grp-closed",),
            "fields": ("bio",
                       "about_me",
                       "organization_type",
                       ("personal_url", "linkedin_url"),
                       ("facebook_url", "twitter_url"))
        })
    ]

    def application_approved_through(self, obj):
        return obj.approved_through

    application_approved_through.short_description = "Application approved through"
    application_approved_through.admin_order_field = "approved_through"

    def application_review_step(self, obj):
        review_status = next(
            (a.review_status for a in obj.applications.all() if a.review_status in ["DUE", "REVIEWING"]), None)
        if review_status:
            return next((s[1] for s in PROVIDER_APPLICATION_REVIEW_STATUSES if s[0] == review_status), "")
        else:
            return ""

    application_review_step.short_description = "Review in Progress"

    def start_periodic_review_process(modeladmin, request, queryset):
        pickled_query = pickle.dumps(queryset.query, 0).decode()
        start_periodic_reviews.apply_async(kwargs=dict(pickled_query=pickled_query))

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("applications").annotate(approved_through=Max('applications__end_date'))

    def save_formset(self, request, form, formset, change):

        super().save_formset(request, form, formset, change)

        if change and formset.model == ProviderApplication:
            for f in formset:
                if "status" in f.changed_data:
                    f.instance.send_status_update_email()


class ProviderApplicationAdmin(admin.ModelAdmin):
    model = ProviderApplication
    raw_id_fields = ["provider"]
    autocomplete_lookup_fields = {"fk": ["provider"]}

    list_display = ["id", "provider", "status", "begin_date", "end_date", "submitted_time", "review_status"]
    readonly_fields = ["submitted_time", "cm_reviews_link", "cm_admin_claims_link"]

    search_fields = ("provider__user__username", "provider__company")

    list_filter = ("status", "review_status")

    form = modelform_factory(ProviderApplication, exclude=[])

    fieldsets = [
        (None, {"fields": (
            "provider",
            ("year", "begin_date", "end_date"),
            ("status", "submitted_time"),
            "explain_topics",
            "objectives_status",
            "objectives_example_1",
            "supporting_upload_1",
            "objectives_example_2",
            "supporting_upload_2",
            "objectives_example_3",
            "supporting_upload_3",
            "how_determines_speakers",
            "evaluates_activities",
            "evaluation_procedures",
            "agree_keep_records",
        )}),
        ("Review", {"fields": (
            ("cm_reviews_link", "cm_admin_claims_link"),
            ("review_status", "review_notification_time"),
            ("review_notes",),
            ("provider_notes",))})
    ]

    def cm_reviews_link(self, obj):
        return "<a href='/cm/provider/{0}/ratings-and-comments/' target='_blank'>See Reviews</a> ".format(
            obj.provider.id)

    cm_reviews_link.short_description = "CM Reviews"
    cm_reviews_link.allow_tags = True

    def cm_admin_claims_link(self, obj):
        return "<a href='/admin/cm/claim/'>Search Claims</a>"

    cm_admin_claims_link.short_description = "CM Claims"
    cm_admin_claims_link.allow_tags = True

    def save_model(self, request, app, form, change):
        """
        overriding save_model method so that... if staff person changes application status to either approved ("A") or
        deferred ("D"), then email is sent to all admin contacts for the CM provider for this applicaton
        """
        super().save_model(request, app, form, change)

        if change and "status" in form.changed_data:
            app.send_status_update_email()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("provider")


class ProviderRegistrationAdmin(admin.ModelAdmin):
    model = ProviderRegistration
    raw_id_fields = ["provider", "purchase", "shared_from_partner_registration"]
    autocomplete_lookup_fields = {"fk": ["provider", "shared_from_partner_registration"]}
    readonly_fields = ["purchase"]

    list_display = ["id", "provider", "year", "registration_type", "purchase"]

    search_fields = ["=provider__user__username", "provider__title"]

    list_filter = ["registration_type", "year"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("provider", "purchase")


class CMOrderAdmin(OrderAdmin):
    model = CMOrder
    list_filter = ("payment__method",)

    readonly_fields = ["get_name", "get_username", "purchase_total", "payment_total", "balance",
                       "payment_process_options",
                       "order_status", "is_manual", "add_comp_tickets", "email_confirmation_link",
                       "submit_events_pending_payment_link"]

    fieldsets = [
        (None, {
            "fields": (
                ("user", "get_name", "order_status",),
                ("purchase_total", "payment_total", "balance", "is_manual",),
                ("add_comp_tickets", "payment_process_options"),
                ("email_confirmation_link", "submit_events_pending_payment_link")
            )
        }),
    ]

    def submit_events_pending_payment_link(self, obj):
        order_id = obj.id
        if order_id:
            return """
                <div style='width:575px;'>
                    <a class='grp-button' href='%s' style='display:inline;'>Submit Events with Pending Payment Status</a>
                </div>
                """ % reverse("store:admin_order_provider_submit", kwargs=dict(order_id=order_id))
        else:
            return "Add purchases and save first in order to submit events."

    submit_events_pending_payment_link.allow_tags = True
    submit_events_pending_payment_link.short_description = "Event Actions"
