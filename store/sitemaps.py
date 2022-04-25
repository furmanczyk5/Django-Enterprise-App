
from django.contrib.sitemaps import Sitemap

from content.models.settings import DEFAULT_SITEMAP_KWARGS

from store.models.content_product import ContentProduct


class ContentProductSitemap(Sitemap):

    changefreq = "monthly"
    limit = 1000
    priority = 1.0

    def items(self):
        return ContentProduct.objects.filter(
            **DEFAULT_SITEMAP_KWARGS
        ).order_by(
            '-updated_time'
        )

    def lastmod(self, obj):
        return obj.updated_time

