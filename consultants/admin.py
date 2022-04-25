import datetime

import pytz
from django.contrib import admin
from django.contrib.staticfiles.templatetags.staticfiles import static

from content.admin import ContentAdmin
from content.forms import ContentTagTypeAdminForm
from content.mail import Mail
from content.models.tagging import TagType
from myapa.admin import OrganizationAdmin, OrganizationProfileInline, \
    IndividualContactRelationshipInline
from myapa.models.contact_relationship import ContactRelationship
from myapa.models.contact_tag_type import ContactTagType
from .models import Consultant, RFP, BranchOffice

rfp_status_to_email_code = {
    "A": "RFP_APPROVAL_CONFIRMATION",
}


class BranchOfficeInline(admin.StackedInline):
    model = BranchOffice
    extra = 0
    classes = ("grp-collapse grp-closed",)
    fields = ["user_address_num", "address1", "address2",
              ("city", "state", "zip_code",), "country",
              "phone", "cell_phone", "email", "website"]

    readonly_fields = []


class ContactTagTypeInline(admin.TabularInline):
    model = ContactTagType
    extra = 0
    classes = ("grp-collapse grp-closed",)

    form = ContentTagTypeAdminForm

    filter_horizontal = ('tags',)
    readonly_fields = []

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        to remove the option to add search_topics and taxo_mastertopics through this Inline
        """
        if db_field.name == "tag_type":
            kwargs["queryset"] = TagType.objects.exclude(code__in=["SEARCH_TOPIC", "TAXO_MASTERTOPIC", "JURISDICTION", "COMMUNITY_TYPE", "FORMAT"])
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        return super().get_queryset(request).exclude(tag_type__code__in=["SEARCH_TOPIC","TAXO_MASTERTOPIC", "JURISDICTION", "COMMUNITY_TYPE", "FORMAT"])


class ConsultantAdmin(OrganizationAdmin):

    readonly_fields=['get_imis_company_legacy', 'get_branch_offices']

    fieldsets = [
        ("Company Profile", {
            "classes":( "grp-collapse grp-open",),
            "fields":(  ("company"),
            			"get_imis_company_legacy",
            			# "organizationprofile",
            			("contact_type", "organization_type",),
            			# ( "user", "id"),
                        "about_me",
                        "bio",
                        "slug",
                        "address1",
                        "address2",
                        ("city", "state",),
                        "zip_code",
                        "country",
                        ("email",),
                        ("phone","cell_phone"),
                        # "parent_organization",
                        "get_branch_offices",
                        ("personal_url", "linkedin_url"),
                        ("facebook_url", "twitter_url")     )
        })
    ]

    # This only works for Organizations not Consultants: , IndividualContactRelationshipInline
    inlines=[OrganizationProfileInline, ContactTagTypeInline, BranchOfficeInline,IndividualContactRelationshipInline]

    show_solr_publish = True


class RFPAdmin(ContentAdmin):
    list_filter = [x for x in ContentAdmin.list_filter if x not in ["content_type"]] # removes content_type from filters
    list_display = ("get_master_id", "title", "company", "email", "deadline",
                    "submission_time", "status", "is_published",
                    "is_up_to_date")
    readonly_fields = ContentAdmin.readonly_fields + ('content_type',)
    show_sync_harvester = False

    fieldsets = [
        (None, {
            "fields":(  ("title", "rfp_type"),
                        ("company", "deadline"),
                        ("country", "state", "city"),
                        ("email", "website"),
                        "text",
                        ("parent_landing_master", "url"),
                        "description",
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

    def response_add(self, request, obj):
        obj.census_region_tag_save()
        return super().response_add(request, obj)

    def response_change(self, request, obj):
        obj.census_region_tag_save()
        return super().response_change(request, obj)

    def button_publish(self, request, obj):

        send_email = obj.status == "A" and (not obj.master.content_live or obj.master.content_live.status != "A")

        super().button_publish(request, obj)

        contact = next((cr.contact for cr in obj.contactrole.all() if cr.role_type == "PROPOSER"), None)
        if send_email and contact:
            mail_context = {
                'rfp':obj,
                'contact':contact,
            }
            Mail.send('RFP_APPROVAL_CONFIRMATION', contact.email, mail_context)


    def save_model(self, request, obj, form, change):
        """
        If staff changes application_status of RFP/RFQ, an appropriate email is generated.
        """
        # loop through the admins for the organization and make a list
        # send an email to each admin on the list

        # NOTE... this throws an exception ... need to revisit
        emails = []
        for c in Consultant.objects.all():
            if hasattr(c, "organizationprofile") and c.organizationprofile.consultant_listing_until:
                if c.organizationprofile.consultant_listing_until > datetime.datetime.now(tz=pytz.utc):
                    emails = emails + [ s.target.email for s in ContactRelationship.objects.filter(source=c) ]

        if change and "status" in form.changed_data and obj.status == 'A':
            email_template_code = rfp_status_to_email_code[obj.status]
            mail_to = emails
            Mail.send(email_template_code, mail_to)

        return super().save_model(request, obj, form, change)


    class Media:
        js = (
            "//ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js",
            static("ckeditor/ckeditor.js"),
            # static("ckeditor/plugins/lite/lite-interface.js")
        )
        css = {
             'all': ( static("ckeditor/plugins/planning_media/admin.css"), )
        }


admin.site.register(Consultant, ConsultantAdmin)
admin.site.register(RFP, RFPAdmin)
