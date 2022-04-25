
from django.contrib.sitemaps import Sitemap


class ContentSitemap(Sitemap):

    def location(self, obj):
        """Default Sitemap location() method is to use the model's
        get_absolute_url() method. Since :meth:`content.models.content.Content.get_absolute_url`
        injects "https://www.planning.org" into everything, we end up with sitemap
        <loc> elements that look like "https://planning.orghttps://www.planning.org/leadership
        I figured it's safer to override here than mess with that."""
        return obj.get_absolute_url().replace("https://www.planning.org", '')
