from content.utils import generate_filter_model_manager
from events.models import EventMulti, EventManager, NATIONAL_CONFERENCE_DEFAULT, NATIONAL_CONFERENCES

from .microsite import Microsite

class MicrositeEvent(EventMulti):
    class_queryset_args = {"content_type":"EVENT", "event_type":"EVENT_MULTI"}

    objects = generate_filter_model_manager(
                ParentManager=EventManager, 
                event_type="EVENT_MULTI", 
                # master__in=[ m.event_master for m in Microsite.objects.all() ] # TO DO... this adds a query... should refactor
                )()

    class Meta:
        verbose_name="Microsite event"
        verbose_name_plural="Microsite events"
        proxy = True


class NationalConferenceEvent(MicrositeEvent):
    class_queryset_args = {"content_type":"EVENT", "event_type":"EVENT_MULTI"}

    # TO DO: this causes issues... why???
    objects = generate_filter_model_manager(
        ParentManager=EventManager,
        event_type="EVENT_MULTI",
        code__in=[x[0] for x in NATIONAL_CONFERENCES]
        )()

    class Meta:
        verbose_name="National Planning Conference"
        verbose_name_plural="National Planning Conferences"
        proxy = True

