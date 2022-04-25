from django.contrib import admin
from .models import Directory


# Register your models here.
class DirectoryAdmin(admin.ModelAdmin):
    fields = (
        'title',
        ('code', 'subscription_product'),
        'permission_groups',
        'committees',
        'directory_group',
        'description'
        )
    list_display = (
                'title', 
                'code', 
                'committees',
                'permission_groups_names',
                'subscription_product')
    search_fields = ('code', 'committees', 'title')
    raw_id_fields = ('subscription_product',)
    autocomplete_lookup_fields = ('subscription_product',)
    filter_horizontal = ('permission_groups',)

    def permission_groups_names(self, obj):
        return "\n".join([p.name for p in obj.permission_groups.all()])

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("permission_groups")

admin.site.register(Directory, DirectoryAdmin)
