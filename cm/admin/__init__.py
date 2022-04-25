from django.contrib import admin

from cm.models import Log, Claim, Period, CMComment, \
    Provider, ProviderApplication, ProviderRegistration, CMOrder

from .claims import PeriodAdmin, LogAdmin, ClaimAdmin, CMCommentAdmin

from .providers import ProviderAdmin, ProviderApplicationAdmin, ProviderRegistrationAdmin, CMOrderAdmin

admin.site.register(Period, PeriodAdmin)
admin.site.register(Log, LogAdmin)
admin.site.register(Claim, ClaimAdmin)
admin.site.register(CMComment, CMCommentAdmin)

admin.site.register(Provider, ProviderAdmin)
admin.site.register(ProviderApplication, ProviderApplicationAdmin)
admin.site.register(ProviderRegistration, ProviderRegistrationAdmin)
admin.site.register(CMOrder, CMOrderAdmin)