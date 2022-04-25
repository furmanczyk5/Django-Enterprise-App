from django.utils import timezone

from myapa.models.constants import ContactRoleTypes
from myapa.views.myorg.dashboard import MyOrganizationDashboardView


class OrgEventsView(MyOrganizationDashboardView):

    template_name = "myorg/events-table.html"
    events = None

    def setup(self):
        self.roles = []
        self.set_org_roles()

        self.events = []
        self.upcoming_events = []
        self.recent_events = []
        self.set_org_events()

        now = timezone.now()

        # include incomplete (i.e. unpublished) events in upcoming events
        # we don't want to include duplicate DRAFT copies of recent events
        upcoming_draft_events = self.roles.filter(
            content__content_type='EVENT',
            content__event__begin_time__isnull=False,
            content__event__master__content_live__isnull=True,
            role_type=ContactRoleTypes.PROVIDER.value
        ).exclude(
            content__event__event_type__in=self.exclude_event_types
        )
        self.upcoming_events += [x.content.event for x in upcoming_draft_events]

        self.events = self.upcoming_events + self.recent_events

        # don't sort if an event somehow doesn't have a begin_time
        try:
            self.events.sort(key=lambda x: x.begin_time, reverse=True)
        except TypeError:
            pass

    def get_context_data(self, **kwargs):
        return dict(
            company=self.organization.company,
            events=self.events
        )
