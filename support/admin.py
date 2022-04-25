from django.contrib import admin
from django.forms.models import model_to_dict

from content.mail import Mail
from content.admin import BaseContentAdmin

from .models import Ticket


class SpamListFilter(admin.SimpleListFilter):
    """
    List filter for Spam
    """
    title = 'Spam'
    parameter_name = 'spam'

    def lookups(self, request, model_admin):
        return (

            (None, "Hide Spam"),
            ("SHOW_SPAM","Show Spam"),
        )

    def choices(self, changelist):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == str(lookup),
                'query_string': changelist.get_query_string({self.parameter_name: lookup}),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() == None:
            return queryset.exclude(ticket_status='SP')
        else:
            return queryset

def make_spam(modeladmin, request, queryset):
    queryset.update(ticket_status='SP')
make_spam.short_description = "Set selected support tickets as SPAM"


class TicketAdmin(BaseContentAdmin):
    list_display = ["id", "get_title", "category", "apa_id", "full_name", "email", "ticket_status", "created_time"]
    list_display_links = ["id", "get_title"]
    search_fields = ["id", "apa_id", "full_name", "email", "title", "description"]
    list_filter = ["category", "ticket_status", SpamListFilter]
    actions = [make_spam]

    raw_id_fields = ["contact"]
    autocomplete_lookup_fields = {'fk': ["contact"]}

    fieldsets = [
        (None, {
            "fields": (
                "id",
                ("title", "category", "ticket_status"),
                ("contact", "apa_id", "full_name"),
                ("email", "phone"),
                "description",
                "staff_comments",
                "created_time")
        }),
    ]

    def get_title(self, obj):
        return obj.title
    get_title.short_description = "subject"

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def save_model(self, request, obj, form, change):

        if not change:
            Mail.send("CUSTOMER_SERVICE_REQUEST_CONFIRMED", obj.email, model_to_dict(obj))

        if not change or "category" in form.changed_data:
            Mail.send("CUSTOMER_SERVICE_REQUEST", obj.get_support_email(), model_to_dict(obj))

        return super().save_model(request, obj, form, change)




admin.site.register(Ticket, TicketAdmin)
