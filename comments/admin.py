from django.contrib import admin
from django.db.models import F

from .models import Comment


class CommentAdmin(admin.ModelAdmin):

    list_display = ["id", "contact", "comment_type", "rating_for", "rating", "submitted_time"]
    list_filter = ["comment_type", "rating", "submitted_time"]
    search_fields = ["=id", "=contact__user__username", "=content__master_id", "=contactrole__content__master_id", "=contactrole__contact__user__username"]
    list_display_links = ["id"]

    readonly_fields = ["rating_for"]

    raw_id_fields = ["contact", "content",  "contactrole"]
    autocomplete_lookup_fields = { "fk" : ["contact", "content", "contactrole"] }

    ordering = ("-submitted_time",)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm("{app}.delete_{model}".format(app=self.model._meta.app_label, model=self.model._meta.model_name))
        # return (obj is None) or (obj.comment_type != "CM") # cannot delete cm claims, deleting comment tied to claim will delete the claim

    def get_queryset(self, request):
        return super().get_queryset(request).exclude(is_deleted=True).annotate(
            list_master_id=F("content__master_id"),
            list_title=F("content__title"),
            list_cr_user_id=F("contactrole__contact__user__username"),
            list_cr_contact=F("contactrole__contact__title"),
            list_cr_master_id=F("contactrole__content__master_id"),
            list_cr_title=F("contactrole__content__title"),
        ).select_related("contact__user")

    def rating_for(self,obj):
        if obj.list_master_id:
            return "<b>{master_id}: {title}</b>".format(master_id=obj.list_master_id, title=obj.list_title)
        elif obj.list_cr_master_id:
            return "<b>{user_id}: {contact}</b><br/><span style='font-size:0.8em;'>{master_id}: {title}</span>".format(
                user_id=obj.list_cr_user_id,
                contact=obj.list_cr_contact,
                master_id=obj.list_cr_master_id,
                title=obj.list_cr_title)
        else:
            return " -- "
    rating_for.short_description = "Rating For"
    rating_for.allow_tags = True

    def delete_model(self, request, obj):
        obj.is_deleted = True
        obj.save()

admin.site.register(Comment,CommentAdmin)

