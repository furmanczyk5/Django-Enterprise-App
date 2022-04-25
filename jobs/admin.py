from django.contrib import admin

from content.models import ContentTagType
from content.admin import ContentAdmin
from component_sites.sites_config import COMPONENT_SITES
from component_sites.models import ProviderSettings

from .models import Job, WagtailJob


class JobsAdmin(ContentAdmin):

    list_display = ("get_master_id", "id", "title", "company", "city", "state", "country", "get_aicp_req",
                    "post_time", "make_inactive_time", "is_published", "is_up_to_date", "status")
    show_sync_harvester = False

    fieldsets = [

        (None, {
            "fields": (("title", "status"),
                       "text",
                       ("url"),
                       "description",
                       "has_xhtml",  # now, everything has xhtml... we should remove this field from the model...
                       ),
        }),
        ("Job Fields", {
            "fields": (
                ("company", "job_type"),
                ("editorial_comments"),
                ("salary_range"),
                ("address1"),
                ("address2"),
                ("city", "state"),
                ("zip_code", "country"),
                "display_contact_info",
                ("contact_us_first_name", "contact_us_last_name"),
                ("contact_us_email", "contact_us_phone"),
                "contact_us_user_address_num",
                "contact_us_address1",
                "contact_us_address2",
                ("contact_us_city", "contact_us_state"),
                ("contact_us_zip_code", "contact_us_country"),
                "resource_url",
            )
        }),
        ("Advanced Content Management Settings", {
            "classes": ("grp-collapse grp-closed",),
            "fields": (
                ("subtitle", ),
                ("overline", ),
                ("publish_status",),
                ("template"),
                ("code",),  # NOTE: resource URL removed for now....
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

    def get_queryset(self, request):
        qs = super(JobsAdmin, self).get_queryset(request)
        if any(group.name == 'staff' for group in request.user.groups.all()):
            return qs.filter(contactrole__contact__user_id=115054)
        return qs.none()

    def get_form(self, request, obj=None, **kwargs):
        form = super(JobsAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['editorial_comments'].help_text = """
        How/Where to apply for the job.
        """
        form.base_fields['editorial_comments'].label = "How to apply"
        return form

    def response_add(self, request, obj):
        obj.census_region_tag_save()
        return super().response_add(request, obj)

    def response_change(self, request, obj):
        obj.census_region_tag_save()
        return super().response_change(request, obj)

    def get_aicp_req(self, obj):
        aicp_req = ContentTagType.objects.filter(content=obj, tag_type__code="AICP_LEVEL").first()

        if aicp_req and aicp_req.tags.all():
            return aicp_req.tags.first().title
        else:
            return " -- "
    get_aicp_req.short_description = "AICP Requirement"


class WagtailJobsAdmin(JobsAdmin):

    def get_queryset(self, request):
        qs = super(JobsAdmin, self).get_queryset(request)
        wt_admin_groups = [(info.get('admin_group'), info.get('username')) for site, info in COMPONENT_SITES.items()]
        provider_list = []
        for group in request.user.groups.all():
            # excludes jobs with Provider = APA
            if group.name == 'staff':
                return qs.exclude(contactrole__contact__user_id=115054)
            else:
                # creates list of admin groups
                for wt_admin in wt_admin_groups:
                    if wt_admin[0] == group.name:
                        provider_list.append(wt_admin[1])
        return qs.filter(contacts__user__username__in=provider_list)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['wagtail_job_post'] = True
        return super().change_view(request, object_id, form_url, extra_context=extra_context)


admin.site.register(Job, JobsAdmin)
admin.site.register(WagtailJob, WagtailJobsAdmin)
