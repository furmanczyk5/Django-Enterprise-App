from django.contrib import admin

from content.models import ContentTagType, TagType, Content
from content.mail import Mail
from content.forms import ContentTagTypeAdminForm
from content.admin import ContentAdmin, TagListFilter, PublishStatusListFilter, CollectionRelationshipInline
from myapa.admin import ContactRoleInlineContact

from imagebank.models import Image
from imagebank.forms import ImageBankAdminForm


class NonTaxoTopicContentTagTypeInline(admin.TabularInline):
    model = ContentTagType
    extra = 0
    classes = ("grp-collapse grp-closed",)
    title = "Tagging"
    form = ContentTagTypeAdminForm

    filter_horizontal = ('tags',)
    readonly_fields = []

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        to remove the option to add search_topics and taxo_mastertopics through this Inline
        """
        if db_field.name == "tag_type":
            kwargs["queryset"] = TagType.objects.exclude(code__in=["TAXO_MASTERTOPIC"])
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        return super().get_queryset(request).exclude(tag_type__code__in=["TAXO_MASTERTOPIC"])


class ImageAdmin(ContentAdmin):
    list_display = ["get_master_id", "title", "img_thumbnail_html", "description_truncated", "img_year", "published_year",
                    "width", "height", "resolution", "get_file_extension", "user_friendly_file_size", "is_published", "is_up_to_date"]
    list_filter = ["status", "resolution", "copyright_date", "resource_published_date", TagListFilter, PublishStatusListFilter, "is_apa"]
    search_fields = ["master__id", "copyright_date", "resource_published_date", "resolution", "description"]

    list_display_links = ["get_master_id", "img_thumbnail_html"]

    readonly_fields = ["description_truncated", "height", "width", "get_file_extension", "user_friendly_file_size", "img_thumbnail_html"]

    format_tag_defaults = ["FORMAT_IMAGE"]
    show_sync_harvester = False

    inlines = [NonTaxoTopicContentTagTypeInline, ContactRoleInlineContact, CollectionRelationshipInline]

    fieldsets = [
        (None, {
            "fields": (
                "title",*
                ("img_thumbnail_html", "image_file"),
                "description",
                "keywords",
                "abstract",  # Taxonomy abstract field
                ("width", "height", "resolution"),
                ("get_file_extension", "user_friendly_file_size"),
                ("copyright_date", "resource_published_date"),
                "copyright_statement",
                "is_apa"
            ),
        }),
        ("Advanced Content Management Settings", {
            "classes": ("grp-collapse grp-closed",),
            "fields": (
                ("template", "status"),
                ("code",),  # NOTE: resource URL removed for now....
                ("publish_time", "make_public_time",),
                ("archive_time", "make_inactive_time",),
                ("workflow_status", "editorial_comments"),
                ("parent", "slug"),
                ("permission_groups",),
                ("og_title", "og_url"),
                ("og_type", "og_image"),
                ("og_description",)

            )
        })
    ]

    form = ImageBankAdminForm

    actions = []

    def get_queryset(self, request):
        return super(ContentAdmin, self).get_queryset(request).select_related("master", "master__content_live")

    def button_publish(self, request, obj):
        send_approval_email = False
        if not obj.is_apa and obj.status == "A" and not Image.objects.filter(status="A", master_id=obj.master_id, publish_status="PUBLISHED").exists():
            send_approval_email = True

        super().button_publish(request, obj)

        if send_approval_email:
            proposer_role = obj.contactrole.filter(role_type="PROPOSER").select_related("contact").first()
            if proposer_role and proposer_role.contact:
                mail_context = {
                    'contact': proposer_role.contact,
                    'image': obj,
                }
                Mail.send('IMAGELIBRARY_SUBMISSION_APPROVED', proposer_role.contact.email, mail_context)

    def has_delete_permission(self, request, obj=None):
        return next((True for g in request.user.groups.all() if g.name == "staff"), False) # DO we want to narrow this list?

    def delete_model(self, request, obj):
        proposer_role = obj.contactrole.filter(role_type="PROPOSER").select_related("contact").first()
        if proposer_role and proposer_role.contact:
            mail_context = {
                'contact':proposer_role.contact,
                'image':obj,
            }
            Mail.send('IMAGELIBRARY_SUBMISSION_DELETED', proposer_role.contact.email, mail_context)
        super().delete_model(request, obj)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        try:
            obj.parent_landing_master = (
                Content.objects.filter(url="/imagelibrary/").first().master
            )
            obj.save()
        except:
            pass


admin.site.register(Image, ImageAdmin)
