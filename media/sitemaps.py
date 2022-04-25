
from django.contrib.sitemaps import Sitemap

from content.models.settings import DEFAULT_SITEMAP_KWARGS
from media.models import Audio, Document, Image, Video


class MediaSitemap(Sitemap):

    changefreq = "never"
    limit = 1000
    priority = 0.5

    model = None

    def items(self):
        return self.model.objects.filter(
            **DEFAULT_SITEMAP_KWARGS
        ).order_by(
            '-updated_time'
        )

    def lastmod(self, obj):
        return obj.updated_time


class AudioSitemap(MediaSitemap):

    model = Audio


class DocumentSitemap(MediaSitemap):

    model = Document


class ImageSitemap(MediaSitemap):

    model = Image


class VideoSitemap(MediaSitemap):

    model = Video
