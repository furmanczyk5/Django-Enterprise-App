

from knowledgebase.models import Collection, Resource, Story
from content.sitemaps import ContentSitemap
from content.models.settings import DEFAULT_SITEMAP_KWARGS


class KnowledgebaseSitemap(ContentSitemap):

    changefreq = 'never'
    priority = 0.8

    def lastmod(self, obj):
        return obj.updated_time


class KnowledgebaseCollectionSitemap(KnowledgebaseSitemap):

    def items(self):
        return Collection.objects.filter(
            **DEFAULT_SITEMAP_KWARGS
        )


class KnowledgebaseResourceSitemap(KnowledgebaseSitemap):

    def items(self):
        return Resource.objects.filter(
            **DEFAULT_SITEMAP_KWARGS
        )


class KnowledgebaseStorySitemap(KnowledgebaseSitemap):

    def items(self):
        return Story.objects.filter(
            **DEFAULT_SITEMAP_KWARGS
        )
