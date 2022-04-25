def harvester_sync_selected(modeladmin, request, queryset):
	for obj in queryset:
		obj.sync_from_harvester(request)
harvester_sync_selected.short_description = "Harvester Sync Selected"