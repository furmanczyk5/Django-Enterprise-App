from django.contrib import admin


class SuggestionReviewRoleAdmin(admin.ModelAdmin):
    list_display = ('title', 'contact')
    fields = ('title', 'contact')
    raw_id_fields = ('contact',)
    autocomplete_lookup_fields = dict(fk=['contact'])
