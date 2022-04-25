from content.utils import generate_filter_model_manager
from content.models import MasterContent
from events.models import Activity, EventManager, NATIONAL_CONFERENCE_DEFAULT, NATIONAL_CONFERENCES, NATIONAL_CONFERENCE_NEXT
from .microsite import Microsite

# from events.models import Activity

class MicrositeActivity(Activity):
    class_queryset_args = {"content_type":"EVENT", "event_type":"ACTIVITY"}

    objects = generate_filter_model_manager(
                ParentManager=EventManager,
                event_type="ACTIVITY",
                # parent__in=[ m.event_master for m in Microsite.objects.all() ] # TO DO... this adds a query... should refactor
                )()

    def save(self, *args, **kwargs):
        if not self.template:
            self.template = "events/newtheme/conference-details.html"
        super().save(*args, **kwargs)

    def sync_to_imis(self):
        Activity.sync_to_imis(self)

    class Meta:
        verbose_name="Microsite Activity"
        verbose_name_plural="Microsite Activities"
        proxy = True

class NationalConferenceActivity(MicrositeActivity):
# class NationalConferenceActivity(Activity):

    # TO DO: should refactor so as not to hard-code NATIONAL_CONFERENCES / NATIONAL_CONFERENCE_DEFAULT
    objects = generate_filter_model_manager(ParentManager=EventManager, event_type="ACTIVITY", parent__content_live__code__in=[x[0] for x in NATIONAL_CONFERENCES])()

    def save(self, *args, **kwargs):

        # TEMPORARY - TO GET DATA ONTO STAGING - REMOVE BEFORE PROD DEPLOY
        # self.parent = MasterContent.objects.get(content_live__code=NATIONAL_CONFERENCE_NEXT[0])

        if not self.parent:
            self.parent = MasterContent.objects.get(content_live__code=NATIONAL_CONFERENCE_NEXT[0])
            # self.parent = MasterContent.objects.get(content_live__code=NATIONAL_CONFERENCE_DEFAULT[0])
        super().save(*args, **kwargs)

    def sync_to_imis(self):
        Activity.sync_to_imis(self)

    class Meta:
        verbose_name="NPC Activity"
        verbose_name_plural="NPC Activities"
        proxy = True
