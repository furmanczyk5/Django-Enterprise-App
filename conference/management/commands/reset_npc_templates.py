from django.core.management.base import BaseCommand
from conference.models import Microsite, NationalConferenceActivity

class Command(BaseCommand):
    help = "Reset NPC Activity templates to generic"

    def handle(self, **options):
        """Reset NPC Activity templates to generic if they are not associated with a Microsite"""
        event_details_template = "events/newtheme/event-details.html"
        conference_details_template = "events/newtheme/conference-details.html"
        npc_microsite = Microsite.objects.get(is_npc=True)
        npc_activities = NationalConferenceActivity.objects.exclude(
            parent=npc_microsite.event_master,
        ).filter(
            publish_status="DRAFT",
            template=conference_details_template
        )
        self.stdout.write("npc microsite is %s" % npc_microsite)
        self.stdout.write("number of non-microsite npc activities is %s" % npc_activities.count())
        self.stdout.write("\n")
        total = npc_activities.count()
        for i,npca in enumerate(npc_activities):
            npca.template = event_details_template
            npca.save()
            published_activity = npca.publish()
            published_activity.solr_publish()
            self.stdout.write("%s of %s Done." % (i,total))
        self.stdout.write("All Done!")
