import os

from django.db import models
from django.template import loader, Context
from django.apps import apps

from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill

from content.models import Content, ContentManager, MasterContent
from content.utils import generate_filter_model_manager

MEDIA_FORMATS = (
    ("DOCUMENT", "Document"),
    ("IMAGE", "Image"),
    ("VIDEO", "Video"),
    ("AUDIO", "Audio")
    )
FILE_TYPES = (
    ("NA", "Not Applicable"),
    ("JPG", "Jpg"),
    )
URL_SOURCES = (
    ("NA", "Not Applicable"),
    ("YOUTUBE", "Youtube Video"),
    ("SOUNDCLOUD", "Soundcloud Audio"),
    ("STITCHER", "Stitcher")
    )


class MediaImageMasterContentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(content__media__media_format="IMAGE").distinct("id")


class MediaImageMasterContent(MasterContent):
    objects = MediaImageMasterContentManager()

    class Meta:
        proxy = True

    def img_thumbnail_html(self):
        try:
            if self.content_live:
                return u'<img style="max-height:229px" src="%s" />' % (self.content_live.media.image_thumbnail.url)
            elif self.content_draft:
                return u'<img style="max-height:229px" src="%s" />' % (self.content_draft.media.image_thumbnail.url)
            else:
                return ""
        except:pass

    img_thumbnail_html.short_description = "Thumbnail"
    img_thumbnail_html.allow_tags = True

    def to_html(self, **kwargs):
        try:
            if self.content_live:
                return u'<img style="max-width:100%" src="%s" />' % (self.content_live.media.image_file.url)
            elif self.content_draft:
                return u'<img style="max-width:100%" src="%s" />' % (self.content_draft.media.image_file.url)
            else:
                return ""
        except:pass
    to_html.short_description = "Image"
    to_html.allow_tags = True


class MediaManager(ContentManager):
    """
    Model manager for Content
    """
    def get_queryset(self):
        return super().get_queryset().filter(content_type="MEDIA")


# New model for Images, inherits Content model found in "planning/content/models.py"
class Media(Content):
    def generate_file_path(self, filename):
        return "%s/%s" % (self.media_format.lower(), filename)

    objects = MediaManager()
    media_format = models.CharField(max_length=20, choices=MEDIA_FORMATS, default="DOCUMENT")
    url_source = models.CharField(max_length=20, choices=URL_SOURCES, default="NA")
    file_type = models.CharField(max_length=20, choices=FILE_TYPES, default="NA")

    resolution = models.IntegerField("DPI", blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
    width = models.IntegerField(blank=True, null=True)

    image_file = models.ImageField(upload_to=generate_file_path, height_field="height", width_field="width", max_length=100, blank=True, null=True)
    uploaded_file=models.FileField(upload_to=generate_file_path, null=True, blank=True)

    image_thumbnail = ImageSpecField(source="image_file",
            processors=[ResizeToFill(229, 229)],
            format='JPEG',
            options={'quality': 60})

    default_template = "media/newtheme/details.html"

    def get_file(self):
        return (self.image_file if self.media_format == "IMAGE" else self.uploaded_file) or None

    def get_featured_image(self):
        """The featured image of an image should be itself"""
        return self.master if self.image_file else super().get_featured_image()

    def img_thumbnail_html(self):
        try:
            return u'<img style="max-height:229px" src="%s" />' % (self.image_thumbnail.url)
        except:
            return None
    img_thumbnail_html.short_description = "Thumbnail"
    img_thumbnail_html.allow_tags = True

    def img_thumbnail_html_small(self):
        try:
            return u'<img style="max-height:100px" src="%s" />' % (self.image_thumbnail.url)
        except:
            return None
    img_thumbnail_html_small.short_description = "Thumbnail"
    img_thumbnail_html_small.allow_tags = True

    def get_media_proxy_class(self):
        """
        returns the proxy model class that fits this record
        """
        mediaformat_modelname_dict = {
            "DOCUMENT":"document",
            "IMAGE":"image",
            "VIDEO":"video",
            "AUDIO":"audio"
        }
        return apps.get_model(app_label="media", model_name=mediaformat_modelname_dict[self.media_format])

    def to_html(self, **kwargs):
        proxy_class = self.get_media_proxy_class()
        self.__class__ = proxy_class
        return self.to_html()

    def get_file_extension(self):
        if self.uploaded_file:
            url = self.uploaded_file.url
        elif self.image_file:
            url = self.image_file.url
        else:
            return None
        return os.path.splitext(url)[1].lstrip(".")

    def __str__(self):
        the_file = self.get_file()
        if the_file:
            return os.path.basename(the_file.name)
        elif self.url is not None:
            return self.url
        else:
            return "MEDIA_%s" % self.id

    def put_files_to_staging(self):
        if getattr(settings, "PLANNING_PW", ""):
            if self.uploaded_file:
                MediaFileSftp(relative_media_path=self.uploaded_file.name).put()
            if self.image_file:
                MediaFileSftp(relative_media_path=self.image_file.name).put()
            if self.image_thumbnail:
                MediaFileSftp(relative_media_path=self.image_thumbnail.name).put()

    def solr_format(self):
        formatted_content = super().solr_format()
        formatted_content.update({
            "thumbnail":self.image_thumbnail.url if self.image_thumbnail else "",
            "media_format":self.media_format
        })
        return formatted_content

    def save(self, *args, **kwargs):
        self.content_type = "MEDIA"
        super().save(*args,**kwargs)

    class Meta:
        verbose_name_plural = "All Media"

class Document(Media):

    objects = generate_filter_model_manager(ParentManager=MediaManager, media_format="DOCUMENT")()

    def to_html(self, **kwargs):
        """
        For downloads this renders to a link to the document details page
        """
        t = loader.get_template("media/includes/embed/document.html")
        c = { 'media': self }
        return t.render(c)

    def save(self, *args, **kwargs):
        self.media_format = "DOCUMENT"
        return super().save(*args, **kwargs)

    class Meta:
        proxy = True

class Image(Media):

    objects = generate_filter_model_manager(ParentManager=MediaManager, media_format="IMAGE")()

    is_solr_publishable = False # Images are not searchable on solr

    def to_html(self, **kwargs):

        t = loader.get_template("media/includes/embed/image.html")
        c = { 'media': self }
        return t.render(c)

    def save(self, *args, **kwargs):
        self.media_format = "IMAGE"
        return super().save(*args, **kwargs)

    class Meta:
        proxy = True

class Video(Media):

    objects = generate_filter_model_manager(ParentManager=MediaManager, media_format="VIDEO")()

    def img_thumbnail_html_small(self):
        """
        Example of how we can reder different things for thumbnails
        """
        try:
            return self.to_html()
        except:
            return None
    img_thumbnail_html_small.short_description = "Thumbnail"
    img_thumbnail_html_small.allow_tags = True

    def to_html(self, **kwargs):

        if self.uploaded_file:
            template_name = "media/includes/embed/video/native.html"
        elif self.resource_url and self.url_source == "YOUTUBE":
            template_name = "media/includes/embed/video/youtube.html"
        else:
            return ""

        t = loader.get_template(template_name)
        c = { 'media': self }
        return t.render(c)

    def save(self, *args, **kwargs):
        self.media_format = "VIDEO"
        return super().save(*args, **kwargs)

    class Meta:
        proxy = True


class Audio(Media):

    objects = generate_filter_model_manager(ParentManager=MediaManager, media_format="AUDIO")()

    def to_html(self, **kwargs):

        if self.uploaded_file:
            template_name = "media/includes/embed/audio/native.html"
        elif self.resource_url and self.url_source == "SOUNDCLOUD":
            template_name = "media/includes/embed/audio/soundcloud.html"
        elif self.resource_url and self.url_source == "STITCHER":
            template_name = "media/includes/embed/audio/stitcher.html"

        t = loader.get_template(template_name)
        c = { 'media': self }
        return t.render(c)

    def save(self, *args, **kwargs):
        self.media_format = "AUDIO"
        return super().save(*args, **kwargs)

    class Meta:
        proxy = True
