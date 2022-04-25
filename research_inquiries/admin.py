from django import forms
from django.contrib import admin
from django.forms import modelform_factory
from django.utils import timezone

from content.mail import Mail
from content.admin import ContentAdmin, TagListFilter, TaxoTopicTagInline, \
    JurisdictionInline, CommunityTypeInline, ContentTagTypeInline, SearchTopicInline
from myapa.admin import ContactRoleInlineContact
from uploads.models import Upload

from .models import Inquiry, InquiryReview, InquiryReviewRole, REVIEW_STATUSES
from .forms import ReviewInlineForm


class InquiryUploadsInline(admin.TabularInline):
    model = Upload
    fields = ["upload_type", "uploaded_file", "resource_class", "description"]
    ordering = ["upload_type", "created_time"]
    extra = 0

    def formfield_for_foreignkey(self, db_field, *args, **kwargs):
        field = super().formfield_for_foreignkey(db_field, *args, **kwargs)
        if db_field.name == 'upload_type':
            field.queryset = field.queryset.filter(code__in=["PAS_INQUIRY", "PAS_RESPONSE"])
        return field

class InquiryReviewInline(admin.StackedInline):
    model = InquiryReview
    extra = 0
    readonly_fields = ["assigned_time", "review_time"]
    form = ReviewInlineForm
    fieldsets = [
        (None, {
            "fields":(  
                "role",
                "comments",
                ("assigned_time", "review_time"),
                "deadline_time"
            ),
        }),
    ]

    def formfield_for_foreignkey(self, db_field, *args, **kwargs):
        field = super().formfield_for_foreignkey(db_field, *args, **kwargs)
        if db_field.name == 'role':
            field.queryset = field.queryset.filter(review_type="RESEARCH_INQUIRY")
            field.required = True
        return field


class InquiryRoleFilter(admin.SimpleListFilter):

    title = 'Assigned To'
    parameter_name = 'role'

    def lookups(self, request, model_admin):
        return [("UNASSIGNED", "Unassigned")] + [(irr.id, irr) for irr in InquiryReviewRole.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            if self.value() == "UNASSIGNED":
                return queryset.filter(review_assignments__isnull=True)
            else:
                return queryset.filter(review_assignments__role_id=self.value())


class InquiryAdmin(ContentAdmin):

    list_display = ["get_master_id", "title", "review_status", "organization", "contact_name", "contact_email", "reviewers", "submission_time"]
    list_display_links = ["get_master_id", "title"]
    list_filter =  ["review_status", InquiryRoleFilter, TagListFilter]
    search_fields = ["=master__id", "title", "=contactrole__contact__user__username", "contactrole__contact__title"]

    readonly_fields = ["organization_link", "contact_name", "contact_email", "featured_image_display", "thumbnail_html", "publish_status"]

    date_hierarchy = "submission_time"
    show_sync_harvester = False

    fieldsets = [
        (None, {
            "fields":(  
                "title",
                "text", 
                ( "organization_link", 
                    "contact_name", 
                    "contact_email"
                    ),
            ),
        }),
        ("Response", {
            "fields":(
                ("review_status", "hours"),
                "response_text",
            ),
        }),
        ("Advanced Content Management Settings", {
            "classes":( "grp-collapse grp-closed",),
            "fields":(  
                ("subtitle", ),
                ("overline", ),
                ("publish_status",),
                ("template", "status"),
                ("code",), # NOTE: resource URL removed for now....
                ("featured_image", "featured_image_display",),
                ("thumbnail", "thumbnail_html"),
                ("publish_time", "make_public_time",), 
                ("archive_time", "make_inactive_time",), 
                ("workflow_status", "editorial_comments"),
                ("parent", "slug"), 
                ("permission_groups",),
                "keywords",
                ("og_title", "og_url"),
                ("og_type", "og_image"),
                ("og_description",)
            )
        })
    ]

    inlines = [
        TaxoTopicTagInline, JurisdictionInline, CommunityTypeInline,
        SearchTopicInline, ContentTagTypeInline, ContactRoleInlineContact,
        InquiryUploadsInline, InquiryReviewInline,
    ]

    def organization(self, obj):
        return next((cr.contact for cr in obj.contactrole.all() if cr.role_type == "PROPOSER"), None)

    def organization_link(self, obj):
        organization = self.organization(obj)
        return ("<a href='/admin/myapa/organization/{organization_id}' target='_blank'>{organization}</a>".format(organization_id=organization.id, organization=organization.title))
    organization_link.short_description = "Organization link"
    organization_link.allow_tags = True
    organization_link.admin_order_field = "contact__title" # Reliable only if there is one contactrole per inquiry

    def contact_name(self, obj):
        return next(((cr.first_name or "") + " " + (cr.last_name or "") for cr in obj.contactrole.all() if cr.role_type == "PROPOSER"), None)
    contact_name.short_description = "Contact name"
    contact_name.admin_order_field = "contactrole__last_name" # Cannot sort by multiple fields

    def contact_email(self, obj):
        return next((cr.email for cr in obj.contactrole.all() if cr.role_type == "PROPOSER"), None)
    contact_email.short_description = "Contact email"
    contact_email.admin_order_field = "contactrole__email"

    def reviewers(self, obj):
        return ", ".join(["%s (%s)" % (str(r.role.contact), r.role.title) for r in obj.review_assignments.all()]) or "Unassigned"
    reviewers.short_description = "Assigned to"
    reviewers.admin_order_field = "review_assignments__role__contact__last_name" # Reliable only if there is one reviewer per inquiry

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("contactrole__contact__user", "review_assignments__role")

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['response_text'].widget = forms.Textarea(attrs={"class":"ckeditor"})
        return form

    def save_model(self, request, obj, form, change):

        obj.submission_time = obj.submission_time or timezone.now()

        super().save_model(request, obj, form, change)

        review_status = form.cleaned_data.get("review_status")
        review_status_changed = "review_status" in form.changed_data
        inquiry_contact = next((cr for cr in obj.contactrole.all() if cr.role_type == "PROPOSER"), None)

        if review_status_changed and review_status == "COMPLETED" and inquiry_contact:

            mail_context = {
                'inquiry':obj,
                'inquiry_contact':inquiry_contact, # is really the proposer contactrole
            }
            Mail.send('PAS_RESPONSE_COMPLETE', inquiry_contact.email, mail_context)

    def save_formset(self, request, form, formset, change):

        # Seemingly the only way to have on-save events for the review inline, 
        # Could also use a method on the ModelForm class, but this has the benefit of also detecting changes on the inquiry form
        if formset.model == InquiryReview: 

            review_status = form.cleaned_data.get("review_status")
            review_status_changed = "review_status" in form.changed_data
            # datetime_now = datetime.datetime.now(pytz.timezone("Etc/UTC"))
            datetime_now = timezone.now()

            reviews = formset.save(commit=False)
            for review in reviews:
                review.assigned_time = review.assigned_time or datetime_now
                review.contact = review.role.contact
                if review_status_changed and review_status == "COMPLETED":
                    review.review_time = datetime_now
                review.save()
            formset.save_m2m()
        else:
            super().save_formset(request, form, formset, change)


class InquiryReviewRoleFilter(admin.SimpleListFilter):

    title = 'Assigned To'
    parameter_name = 'role'

    def lookups(self, request, model_admin):
        return [(irr.id, irr) for irr in InquiryReviewRole.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(role_id=self.value())

class InquiryReviewAdmin(admin.ModelAdmin):

    readonly_fields = ["inquiry_link", "assigned_time", "review_time", "get_submission_time", "get_review_status"]
    list_display = ["id", "inquiry_link", "get_review_status", "get_submission_time", "role", "assigned_time", "deadline_time", "review_time"]
    raw_id_fields = ["content"]
    search_fields = ["=content__master__id", "content__title", "=role__contact__user__username", "role__contact__title"]
    list_filter = ["content__inquiry__review_status", InquiryReviewRoleFilter]

    date_hierarchy = "deadline_time"

    autocomplete_lookup_fields = dict(fk=["content"])
    form = modelform_factory(InquiryReview, 
        exclude=[],
        labels=dict(role="Assigned to"))

    fieldsets = [
        (None, {
            "fields":(  
                ("content", "inquiry_link"),
                "role", 
                "comments",
                ("deadline_time", "assigned_time", "review_time")
            ),
        }),
    ]

    def get_submission_time(self, obj):
        if obj:
            return obj.content.submission_time
        else:
            return "None"
    get_submission_time.short_description = "Submission time"
    get_submission_time.admin_order_field = "content__inquiry__submission_time"

    def get_review_status(self, obj):
        return next((rs[1] for rs in REVIEW_STATUSES if rs[0] == obj.content.inquiry.review_status), "None")
    get_review_status.short_description = "Review status"
    get_review_status.admin_order_field = "content__inquiry__review_status"

    def inquiry_link(self, obj):
        if obj:
            return "<a href='/admin/research_inquiries/inquiry/{content_id}' target='_blank'>{content}</a>".format(content_id=obj.content_id, content=obj.content)
        else:
            return "None"
    inquiry_link.short_description = "Inquiry link"
    inquiry_link.allow_tags = True
    inquiry_link.admin_order_field = "content__inquiry__title"

    def save_model(self, request, obj, form, change):
        obj.contact = obj.role.contact
        super().save_model(request, obj, form, change)


class InquiryReviewRoleAdmin(admin.ModelAdmin):
    list_display = ("title", "contact")
    fields = ("title", "contact")
    raw_id_fields = ("contact",)
    autocomplete_lookup_fields = dict(fk=["contact"])



admin.site.register(Inquiry, InquiryAdmin)
admin.site.register(InquiryReview, InquiryReviewAdmin)
admin.site.register(InquiryReviewRole, InquiryReviewRoleAdmin)


