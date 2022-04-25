import os
import uuid

from django.db import models

from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill

from content.models import BaseContent, Content, Publishable


COPYRIGHT_TYPES = (
    ("COPYRIGHT_FREE","This resource is copyright free and may be used by APA. "),
    #("CC_BY","Creative Commons copyright (CC BY 2.0)"),
    ("COPYRIGHT_RESERVED","This resource is copyrighted."),
)

class FileType(models.Model):
    """
    Stores a possible system filetype dor an uploaded file (pdf, ppt, docx, etc.). Used to associated upload types with allowed filetypes.
    """
    extension = models.CharField("Extension", max_length=10)
    title = models.CharField("Title", max_length=200)

    def __str__(self):
        return self.title if self.title is not None else self.extension

# Create your models here.
class UploadType(BaseContent):
    """
    Stores a possible type of upload (such as "Supplemental Materials")
    """
    allowed_types = models.ManyToManyField(FileType)
    allowed_min = models.IntegerField(null=True, blank=True)
    allowed_max = models.IntegerField(null=True, blank=True)
    max_file_size = models.IntegerField(null=True, blank=True, help_text="# of kb")
    folder = models.CharField("Upload To Folder", max_length=200)


class Upload(BaseContent, Publishable):
    """
    Stores info about individually uploaded files, including reference to the file, the related content,
    upload type, creator info, and copyright info
    """
    def generate_file_path(self, filename):
        ext = filename.split('.')[-1]
        filename = "%s.%s" % (uuid.uuid4(), ext)
        return "uploads/%s/%s" % (self.upload_type.code, filename)

    upload_type = models.ForeignKey(UploadType, related_name="uploads")
    url = models.URLField("External Url", max_length=255, blank=True, null=True)
    content = models.ForeignKey(Content, blank=True, null=True, related_name="uploads", on_delete=models.SET_NULL)
    copyright_type = models.CharField("Copyright", choices=COPYRIGHT_TYPES, max_length=50, blank=True, null=True)
    copyright_first_name = models.CharField(max_length=20, blank=True, null=True)
    copyright_last_name = models.CharField(max_length=30, blank=True, null=True)
    copyright_email = models.CharField(max_length=100, blank=True, null=True)
    copyright_phone = models.CharField(max_length=20, blank=True, null=True)
    creator_full_name = models.CharField(max_length=80, blank=True, null=True)
    creator_company = models.CharField(max_length=80, blank=True, null=True)
    resource_class = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Materials may be newspaper article, presentation, promotional item, plan or plan element, or other (please describe)"
    )

    uploaded_file = models.FileField(upload_to=generate_file_path, null=True, blank=True)
    image_file = models.ImageField(
        upload_to=generate_file_path,
        height_field="height",
        width_field="width",
        max_length=100,
        blank=True,
        null=True
    )

    height = models.IntegerField(blank=True, null=True)
    width = models.IntegerField(blank=True, null=True)
    image_thumbnail = ImageSpecField(
        source="image_file",
        processors=[ResizeToFill(205, 205)],
        format='JPEG',
        options={'quality': 60}
    )

    @property
    def is_image(self):
        return self.image_file and not self.uploaded_file

    def get_file(self):
        return self.uploaded_file or self.image_file

    def __str__(self):
        myfile = self.get_file()
        if myfile:
            return os.path.basename(myfile.name)
        elif self.url is not None:
            return self.url
        else:
            return "UPLOAD_%s" % self.id

class ImageUpload(Upload):
    # TO DO: add manager here to filter by images
    class Meta:
        proxy = True

class DocumentUpload(Upload):
    # TO DO: add manager here to filter by docs
    class Meta:
        proxy = True

