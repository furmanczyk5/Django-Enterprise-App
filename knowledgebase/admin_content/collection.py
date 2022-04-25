from content.admin import (
    ContentAdmin,
    TaxoTopicTagInline,
    JurisdictionInline,
    CommunityTypeInline,
    ContentTagTypeInline,
    SearchTopicInline
)
from knowledgebase.admin_content.publishing import PublishPermissionMixin
from places.admin import ContentPlaceInline


class CollectionAdmin(PublishPermissionMixin, ContentAdmin):
    list_filter = [
        x for x in ContentAdmin.list_filter if x not in ['content_type']
    ]
    list_display = [
        'get_master_id', 'code', 'title', 'url',
        'status', 'is_published', 'is_up_to_date'
    ]
    readonly_fields = ContentAdmin.readonly_fields + ('content_type',)
    inlines = [
        TaxoTopicTagInline, JurisdictionInline, CommunityTypeInline,
        SearchTopicInline, ContentTagTypeInline, ContentPlaceInline
    ]
    show_sync_harvester = False
    change_form_template = 'admin/pages/page/change-form.html'

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
