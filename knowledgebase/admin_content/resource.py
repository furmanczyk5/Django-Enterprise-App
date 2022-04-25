from .filters import CollectionFilter
from knowledgebase.admin_content.publishing import (
    publishing_for_first_time,
    PublishPermissionMixin
)
from knowledgebase.forms.admin.inlines import (
    ResourceRelationshipInline
)
from knowledgebase.mail import send_resource_published_email
from knowledgebase.models import (
    ResourceSuggestion
)
from content.admin import (
    ContentAdmin,
    TaxoTopicTagInline,
    JurisdictionInline,
    CommunityTypeInline,
    ContentTagTypeInline,
    get_FormatInline,
    TagListFilter,
    ArchivedStatusListFilter,
    CollectionRelationshipInline,
    SearchTopicInline
)
from myapa.admin import ContactRoleInlineContact
from places.admin import ContentPlaceInline


def get_submission_url(submission_type, content_id, url_title):
    return ("<a href='/admin/knowledgebase/{}/{}' "
            ">{}</a>").format(submission_type, content_id, url_title)


class ResourceAdmin(PublishPermissionMixin, ContentAdmin):
    list_filter = (
        "status",
        CollectionFilter,
        TagListFilter,
        ArchivedStatusListFilter
    )
    list_display = [
        'get_master_id', 'title', 'get_collections',
        'url', 'status', 'is_published', 'is_up_to_date'
    ]
    list_display_links = ['get_master_id', 'title']
    readonly_fields = (
        ContentAdmin.readonly_fields + ('content_type', 'get_collections')
    )
    inlines = [
        ResourceRelationshipInline,
        CollectionRelationshipInline,
        TaxoTopicTagInline,
        JurisdictionInline,
        CommunityTypeInline,
        SearchTopicInline,
        ContentTagTypeInline,
        get_FormatInline(),
        ContentPlaceInline,
        ContactRoleInlineContact
    ]

    change_form_template = 'admin/pages/page/change-form.html'
    show_sync_harvester = False

    fieldsets = [

        (None, {
            'fields': (
                ('title', 'status'),
                'text',
                'description',
                'resource_url'
            ),
        }),
        ('Advanced Content Management Settings', {
            'classes': ('grp-collapse grp-closed',),
            'fields': (
                'url',
                ('subtitle', ),
                ('overline', ),
                ('publish_status',),
                ('template'),
                ('code',),
                ('featured_image', 'featured_image_display',),
                ('thumbnail', 'thumbnail_html'),
                ('publish_time', 'make_public_time',),
                ('archive_time', 'make_inactive_time',),
                ('workflow_status', 'editorial_comments'),
                ('parent', 'slug'),
                ('permission_groups',),
                'keywords',
                ('og_title', 'og_url'),
                ('og_type', 'og_image'),
                ('og_description',)
            )
        })
    ]

    def get_collections(self, obj):
        draft_collections = [
            mc.content_draft.title
            for mc in obj.related.all()
            if mc.content_draft.content_type == 'KNOWLEDGEBASE_COLLECTION'
        ]
        return ', '.join(draft_collections)
    get_collections.short_description = 'Collections'

    def get_queryset(self, request):
        return super().get_queryset(
            request
        ).prefetch_related(
            'related__content_draft'
        )

    def save_model(self, request, obj, form, change):
        save_return = super().save_model(request, obj, form, change)

        for master_content in obj.related.all():
            content = ResourceSuggestion.objects.filter(
                master_id=master_content.id
            ).first()
            if content and publishing_for_first_time(request, obj):
                send_resource_published_email(obj, content)

        if '_publish' in request.POST:
            obj.workflow_status = 'IS_PUBLISHED'
            obj.save()

        return save_return

    class Media:
        js = (
            ContentAdmin.Media.js + ('pages/checkin/js/admin-page-checkin.js',)
        )
        css = {
            'all': (
                ContentAdmin.Media.css.get('all') +
                ('pages/checkin/css/admin-page-checkin.css',)
            )
        }
