from django.db import models
from myapa.models.contact_role import ContactRole
from events.models import NATIONAL_CONFERENCE_MASTER_ID

class MicrositeContributorManager(models.Manager):
    def get_queryset(self):
        #also only events with parent NPC! or some tag?
        return super().get_queryset().filter(
            role_type__in = ("SPEAKER", "ORGANIZER","PROPOSER","ORGANIZER&SPEAKER","MOBILEWORKSHOPGUIDE",
                "MODERATOR", "ORGANIZER&MODERATOR", "LEADPOSTERPRESENTER", "POSTERPRESENTER",
                "MOBILEWORKSHOPCOORDINATOR", "LEADMOBILEWORKSHOPCOORDINATOR", "AUTHOR"),
            content__parent__in=[ m.event_master for m in Microsite.objects.all() ] 
            )

class MicrositeContributor(ContactRole):
    objects = MicrositeContributorManager()
    # saving as this is the same as saving a Contact Role. The only difference is the queryset

    # ASSUME NO LONGER NEEDED SINCE SPEAKERS MANAGED IN CADMIUM
    # def content_link(self):
    #     return '<a href="%s">%s</a>' % (reverse("admin:events_nationalconferenceactivity_change", args=(self.content.id,)) , escape(self.content))
    # content_link.allow_tags = True
    # content_link.short_description = "Content"
    # content_link.admin_order_field = "content"
    class Meta:
        verbose_name="Microsite Event Contributor"
        proxy = True

class NationalConferenceContributorManager(models.Manager):
    def get_queryset(self):
        #also only events with parent NPC! or some tag?
        return super().get_queryset().filter(
                role_type__in=("SPEAKER", "ORGANIZER","PROPOSER","ORGANIZER&SPEAKER","MOBILEWORKSHOPGUIDE",
                    "MODERATOR", "ORGANIZER&MODERATOR", "LEADPOSTERPRESENTER", "POSTERPRESENTER",
                    "MOBILEWORKSHOPCOORDINATOR", "LEADMOBILEWORKSHOPCOORDINATOR", "AUTHOR"), 
                content__parent__id=NATIONAL_CONFERENCE_MASTER_ID
                )

class NationalConferenceContributor(ContactRole):
    objects = NationalConferenceContributorManager()
    # saving as this is the same as saving a Contact Role. The only difference is the queryset

    # def content_link(self):
    #     return '<a href="%s">%s</a>' % (reverse("admin:events_nationalconferenceactivity_change", args=(self.content.id,)) , escape(self.content))
    # content_link.allow_tags = True
    # content_link.short_description = "Content"
    # content_link.admin_order_field = "content"
    class Meta:
        verbose_name="Conference Participant"
        proxy = True