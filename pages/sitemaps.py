

from content.models.settings import DEFAULT_SITEMAP_KWARGS
from content.sitemaps import ContentSitemap
from pages.models import (AudioPage, ConferencesPage, AICPPage, MembershipPage, VideoPage,
                          KnowledgeCenterPage, PolicyPage, CareerPage, OutreachPage,
                          AboutPage, ConnectPage)


class PageSitemap(ContentSitemap):

    changefreq = "monthly"
    limit = 1000
    priority = 0.9

    model = None

    def items(self):
        return self.model.objects.filter(
            **DEFAULT_SITEMAP_KWARGS
        ).order_by(
            '-updated_time'
        )

    def lastmod(self, obj):
        return obj.updated_time


class AboutPageSitemap(PageSitemap):

    model = AboutPage


class AICPPageSitemap(PageSitemap):

    model = AICPPage


class AudioPageSitemap(PageSitemap):

    model = AudioPage


class CareerPageSitemap(PageSitemap):

    model = CareerPage


class ConferencesPageSitemap(PageSitemap):

    model = ConferencesPage


class ConnectPageSitemap(PageSitemap):

    model = ConnectPage


class KnowledgeCenterPageSitemap(PageSitemap):

    model = KnowledgeCenterPage


class MembershipPageSitemap(PageSitemap):

    model = MembershipPage


class OutreachPageSitemap(PageSitemap):

    model = OutreachPage


class PolicyPageSitemap(PageSitemap):

    model = PolicyPage


class VideoPageSitemap(PageSitemap):

    model = VideoPage
