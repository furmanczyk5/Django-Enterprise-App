from django.contrib import admin
from component_sites.models import BuildSettings
from django.core import management

def build_site(modeladmin, request, queryset):
    for obj in queryset:
        management.call_command('create_wagtail_sites', environment=obj.env, admin=True, site=obj.title,
                                domain=obj.domain, type=obj.type, group=obj.admin_group.name, provider=obj.provider.user.username)

class BuildSettingsAdmin(admin.ModelAdmin):
    actions = [build_site]



admin.site.register(BuildSettings, BuildSettingsAdmin)
