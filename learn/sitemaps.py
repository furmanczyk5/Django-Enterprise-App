from datetime import timedelta

from django.utils import timezone

from content.models.settings import DEFAULT_SITEMAP_KWARGS
from content.sitemaps import ContentSitemap
from learn.models.learn_course import LearnCourse


class LearnCourseSitemap(ContentSitemap):

    changefreq = "never"
    limit = 1000
    priority = 1.0

    cutoff = timezone.now() - timedelta(days=365*2)

    def items(self):
        return LearnCourse.objects.filter(
            begin_time__gte=self.cutoff,
            **DEFAULT_SITEMAP_KWARGS
        ).order_by(
            '-begin_time'
        )

    def lastmod(self, obj):
        return obj.updated_time
