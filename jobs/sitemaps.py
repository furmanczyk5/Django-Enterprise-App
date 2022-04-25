from datetime import timedelta

from django.contrib.sitemaps import Sitemap
from django.utils import timezone

from jobs.models import Job
from content.models.settings import DEFAULT_SITEMAP_KWARGS


class JobSitemap(Sitemap):

    changefreq = 'never'
    priority = 0.9

    cutoff = timezone.now() - timedelta(days=28)

    def items(self):
        return Job.objects.filter(
            published_time__gte=self.cutoff,
            **DEFAULT_SITEMAP_KWARGS
        )

    def lastmod(self, obj):
        return obj.updated_time
