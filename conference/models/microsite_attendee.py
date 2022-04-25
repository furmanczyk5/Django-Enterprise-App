# THIS ALL WILL GO AWAY WITH EVENT REG IN IMIS:

from django.db import models
from events.models import NATIONAL_CONFERENCES, NATIONAL_CONFERENCE_ADMIN
from registrations.models import Attendee

class MicrositeAttendeeManager(models.Manager):

    def get_queryset(self):
        # add more codes
        microsite_events = [ m.event_master for m in Microsite.objects.all() ]
        return super().get_queryset().filter( Q(event__parent in microsite_events | event__master in microsite_events ) )
        # return super().get_queryset()


class MicrositeAttendee(Attendee):

    objects = MicrositeAttendeeManager()

    class Meta:
        verbose_name="Microsite Attendee"
        verbose_name_plural = "Microsite Attendees"
        proxy = True


class NationalConferenceAttendeeManager(models.Manager):

    def get_queryset(self):
        # add more codes
        return super().get_queryset().filter(event__code__in=[x[0] for x in NATIONAL_CONFERENCES])
        # return super().get_queryset()


class NationalConferenceAttendee(Attendee):

    objects = NationalConferenceAttendeeManager()

    def save(self, *args, **kwargs):
        if not hasattr(self, "event"):
            # TO DO... it's odd to link to draft event here... NEED TO RETHINK THIS...
            self.event = Event.objects.get(code=NATIONAL_CONFERENCE_ADMIN[0], publish_status="DRAFT") 
        super().save(*args, **kwargs)

    class Meta:
        verbose_name="NPC Attendee"
        verbose_name_plural = "NPC Attendees"
        proxy = True