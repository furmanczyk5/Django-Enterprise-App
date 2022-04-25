from datetime import timedelta

from django.utils import timezone

from blog.models import BlogPost
from content.sitemaps import ContentSitemap
from content.models.settings import DEFAULT_SITEMAP_KWARGS


class BlogPostSitemap(ContentSitemap):

    changefreq = 'never'
    priority = 0.5

    cutoff = timezone.now() - timedelta(days=90)

    def items(self):
        return BlogPost.objects.filter(
            published_time__gte=self.cutoff,
            **DEFAULT_SITEMAP_KWARGS
        )

    def lastmod(self, obj):
        return obj.updated_time
