from datetime import timedelta

from django.contrib.sitemaps import Sitemap
from django.utils import timezone

from content.models.settings import DEFAULT_SITEMAP_KWARGS
from events.models import Event, EventMulti, Activity


class EventSitemap(Sitemap):

    changefreq = "never"
    limit = 1000
    priority = 0.7

    cutoff = timezone.now() - timedelta(days=365*2)

    model = Event

    def items(self):
        return self.model.objects.filter(
            begin_time__gte=self.cutoff,
            **DEFAULT_SITEMAP_KWARGS
        ).order_by(
            '-begin_time'
        )

    def lastmod(self, obj):
        return obj.updated_time


class EventMultiSitemap(EventSitemap):

    model = EventMulti


class ActivitySitemap(EventSitemap):

    model = Activity

