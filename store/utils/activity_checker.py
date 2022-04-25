from django.apps import apps

# from events.models import Event
# from imis.event_tickets import ACTIVITY_TICKET, EVENT_REGISTRATION
from .parent_event_result import ParentEventResult


ACTIVITY_TICKET = 'ACTIVITY_TICKET'
EVENT_REGISTRATION = 'EVENT_REGISTRATION'

class ActivityChecker(object):
    def __init__(self, purchases):
        self.purchases = purchases
        self.result = ParentEventResult()

    def parent_event_deleted(self, purchase_to_remove):
        EventModel = apps.get_model('events.Event')
        activity_purchases = self._get_activity_tickets()
        event_to_remove = EventModel.objects.filter(
                master=purchase_to_remove.product.content.master
            ).first()

        for activity in activity_purchases:
            parent_event = self._get_activity_parent_event(activity)
            if parent_event.master_id == event_to_remove.master_id:
                return True

        return False

    def get_missing_parent_event(self):
        activity_purchases = self._get_activity_tickets()

        if activity_purchases:
            event_purchases_content = self._get_purchase_events_content(self.purchases)

            for activity in activity_purchases:
                parent_event = self._get_activity_parent_event(activity)

                match = self._find_event_match_in_purchases(
                    parent_event,
                    event_purchases_content
                )

                if not match:
                    self.result.set_parent_event(parent_event)

        return self.result

    def _get_activity_tickets(self):
        return filter(
            lambda purchase: purchase.product.product_type == ACTIVITY_TICKET,
            self.purchases
        )

    def _get_activity_parent_event(self, activity):
        EventModel = apps.get_model('events.Event')
        content = activity.product.content
        event = EventModel.objects.filter(
            master=content.master
        ).first()

        return event.parent.content_live

    def _get_purchase_events_content(self, purchases):
        EventModel = apps.get_model('events.Event')
        event_purchases = filter(
            lambda purchase: purchase.product.product_type == EVENT_REGISTRATION,
            purchases
        )
        events_content = []

        for event in event_purchases:
            events_content += EventModel.objects.filter(
                master=event.product.content.master
            )

        return events_content

    def _find_event_match_in_purchases(self, parent_event, events):
        return [
            event
            for event in events
            if parent_event.master_id == event.master_id
        ]
