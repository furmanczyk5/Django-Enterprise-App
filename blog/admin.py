from django.contrib import admin
from blog.models import BlogCategoryContentTagType, BlogPost
from content.admin import ContentAdmin, CollectionRelationshipInline
from reversion.admin import VersionAdmin

from blog.forms import BlogCategoryContentTagTypeAdminForm


class BlogCategoryInline(admin.TabularInline):
    model = BlogCategoryContentTagType
    extra = 1
    max_num = 1
    filter_horizontal = ('tags',)
    form = BlogCategoryContentTagTypeAdminForm
    classes = ("grp-collapse grp-closed",)


class BlogPostAdmin(ContentAdmin, VersionAdmin):
    model = BlogPost
    format_tag_defaults = ["FORMAT_BLOGPOST"]
    inlines = (BlogCategoryInline, CollectionRelationshipInline) + ContentAdmin.inlines
    change_form_template = "admin/pages/page/change-form.html"
    show_sync_harvester = False

    class Media:
        js = ("pages/checkin/js/admin-page-checkin.js",)
        css = {
            'all': ("pages/checkin/css/admin-page-checkin.css",)
        }

admin.site.register(BlogPost, BlogPostAdmin)
