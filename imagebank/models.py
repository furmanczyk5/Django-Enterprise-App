import os
import re
import datetime

from django.db import models
from django.dispatch.dispatcher import receiver

from content.models import Content, ContentManager
from content.utils import force_utc_datetime

from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, Transpose


class ImageManager(ContentManager):
    """
    Model manager for Content
    """
    def get_queryset(self):
        return super().get_queryset().filter(content_type="IMAGE")


# New model for Images, inherits Content model found in "planning/content/models.py"
class Image(Content):
    objects = ImageManager()

    resolution = models.IntegerField("DPI", blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
    width = models.IntegerField(blank=True, null=True)
    image_file = models.ImageField(upload_to="imagebank", height_field="height", width_field="width", max_length=100, blank=True, null=True)
    image_thumbnail = ImageSpecField(source="image_file",
            processors=[Transpose(),ResizeToFill(229, 229)],
            format='JPEG',
            options={'quality': 60})

    def img_thumbnail_html(self):
        try:
            return u'<img style="width:100%%;max-width:229px" src="%s" />' % (self.image_thumbnail.url)
        except:
            return None

    def description_truncated(self):
        if not self.description:
            return None
        else:
            return self.description[:25] + (self.description[25:] and "...")

    def img_year(self):
        if not self.copyright_date:
            return None
        else:
            return self.copyright_date.strftime('%Y')

    def published_year(self):
        if not self.resource_published_date:
            return None
        else:
            return self.resource_published_date.strftime('%Y')

    def get_file_extension(self):
        if not self.image_file:
            return None
        else:
            return os.path.splitext(self.image_file.url)[1]

    def user_friendly_file_size(self):
        megabyte = 1024 * 1024
        kilobyte = 1024

        try:
            if self.image_file.size > megabyte:
                return "%.2f MB" % float(self.image_file.size / megabyte)
            elif self.image_file.size > 1024:
                return "%.2f kB" % float(self.image_file.size / kilobyte)
            else:
                return "%s bytes" % self.image_file.size
        except:
            return None

    img_thumbnail_html.allow_tags = True
    img_thumbnail_html.short_description = "Thumbnail"
    description_truncated.short_description = "Description"
    img_year.short_description = "Year Taken"
    img_year.admin_order_field = "copyright_date"
    published_year.short_description = "Year Published"
    published_year.admin_order_field = "resource_published_date"
    get_file_extension.short_description = "Extension"
    user_friendly_file_size.short_description = "File Size"
    user_friendly_file_size.admin_order_field = "image_file_size"

    def solr_format(self):
        formatted_content = super(Image, self).solr_format()
        copyright_time = datetime.datetime.combine(self.copyright_date, datetime.datetime.min.time()) if self.copyright_date is not None else None

        # RUNNING INTO ERRORS PUBLISHING SOME IMAGES...
        try:
            thumbnail_url = self.image_thumbnail.url
        except:
            print(">>>>>>>> THUMBNAIL ERROR", self.id)
            thumbnail_url = None

        # NOTE: resource_pu
        formatted_content_additional = {
            "resolution":self.resolution,
            "thumbnail_url":thumbnail_url,
            "copyright_date":force_utc_datetime(copyright_time),
            "image_file_size":self.image_file.size,
            "keywords":self.keywords,
            "is_apa":self.is_apa
        }
        if self.resource_published_date:
            formatted_content_additional["resource_published_date"] = force_utc_datetime(datetime.datetime.combine(self.resource_published_date, datetime.datetime.min.time()))
        formatted_content.update(formatted_content_additional);
        return formatted_content

    def get_filename_wo_path(self):
        try:
            return re.findall(r'.*/(.+)\..+', self.image_file.name)[0]
        except:
            return None

    def save(self, *args, **kwargs):
        self.content_type = 'IMAGE'

        generate_title = not self.title
        if not self.title:
            self.title = "New Image" # need to save with a title

        super().save(*args, **kwargs)

        if generate_title:
            self.title = self.get_filename_wo_path() # This needs to be done after we have the file
            self.save()


# Receive the pre_delete signal and delete the file associated with the model instance.
@receiver(models.signals.pre_delete, sender=Image)
def mymodel_delete(sender, instance, **kwargs):

    filename = instance.image_file.name if instance.image_file else None

    if filename and not Image.objects.filter(image_file=filename).exclude(id=instance.id):
        # Only delete files if no other records use it

        if instance.image_file:
            instance.image_file.delete(False)

        # This doesn't work for thumbnails, how do we delete them?
        # if instance.image_thumbnail: 
        #     print(">", instance.image_thumbnail.url)
        #     instance.image_thumbnail.delete(False)
