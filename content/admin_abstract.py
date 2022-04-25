from reversion.admin import VersionAdmin

from django.contrib import admin

from planning.models_subclassable import SubclassableModelAdminMixin

# NOTE: VersionAdmin and nested admin don't play nicely together... for now, disabling version admin except for Page models in page
# class BaseContentAdmin(SubclassableModelAdminMixin, VersionAdmin):


class BaseContentAdmin(SubclassableModelAdminMixin, admin.ModelAdmin):

    readonly_fields = ("id", "created_by", "created_time", "updated_by", "updated_time")

    fieldsets = [
        (None, {
            "fields": ("title", ("code", "status",), "description")
        }),
    ]

    history_latest_first = True

    def save_model(self, request, content, form, change):
        if not change:
            content.created_by = request.user
        content.updated_by = request.user
        return super().save_model(request, content, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)

        for instance in instances:
            # if instance.created_by is None:
            # TO DO... THIS WILL ALWAYS UPDATE THE CREATED BY... WE NEED SOME WAY TO TELL IF INSTANCE/CREATED_BY EXISTS AND THEN RESET
            # IF IT DOESN'T ... PERHAPS NEED TO USE TRY/EXCEPT BLOCK?
            instance.created_by = request.user
            instance.updated_by = request.user
            instance.save()

        # as of django 1.7, deletions need to be handled manually when you use formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()

        formset.save_m2m()


class BaseAddressAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Address Info",{
            "classes":( "grp-collapse grp-closed",),
            "fields": ( "user_address_num",
                        "address1",
                        "address2",
                        ("city","state"),
                        ("country","zip_code")  )
        })
    ]
