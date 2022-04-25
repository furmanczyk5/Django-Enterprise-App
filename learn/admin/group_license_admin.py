from django.contrib import admin

from learn.utils.wcw_api_utils import WCWContactSync
from learn.models import GroupLicense


class GroupLicenseAdmin(admin.ModelAdmin):
    """
    Admin for APA Learn Group License Codes
    """
    list_display = ("purchase", "license_code", "redemption_date")

    fieldsets = [
        (None, {
            "fields": ("purchase", "license_code", "redemption_date", "redemption_contact")
        })
    ]

    readonly_fields = ["purchase", "license_code", "redemption_date", "redemption_contact"]


    def change_view(self, request, object_id, form_url='', extra_context=None):

        try:
            gl=GroupLicense.objects.get(id=object_id)
            order=gl.purchase.order
            wcw_contact_sync = WCWContactSync(order.user.contact)
            wcw_contact_sync.pull_licenses_redeemed_from_wcw(order)
        except:
            pass

        return super(GroupLicenseAdmin, self).change_view(
            request, object_id, form_url, extra_context=extra_context)


admin.site.register(GroupLicense, GroupLicenseAdmin)
