

from content.models.settings import DEFAULT_SITEMAP_KWARGS
from content.sitemaps import ContentSitemap
from publications.models import Publication, Report, PublicationDocument, Article, PlanningMagArticle


class PublicationSitemap(ContentSitemap):

    changefreq = "monthly"
    limit = 1000
    priority = 0.8

    model = Publication

    def items(self):
        return self.model.objects.filter(
            **DEFAULT_SITEMAP_KWARGS
        ).order_by(
            '-updated_time'
        )

    def lastmod(self, obj):
        return obj.updated_time


class ReportSitemap(PublicationSitemap):

    model = Report


class PublicationDocumentSitemap(PublicationSitemap):

    model = PublicationDocument


class ArticleSitemap(PublicationSitemap):

    model = Article


class PlanningMagArticleSitemap(PublicationSitemap):

    model = PlanningMagArticle
