from django.contrib import admin

from .models import Upload, UploadType, FileType, ImageUpload


class FileUploadInline(admin.StackedInline):
    model = Upload
    extra = 0
    classes = ( "grp-collapse grp-open",)
    fieldsets = [
        (None, {
            "fields":(  "title",
                        ("creator_full_name", "creator_company"),
                        ( "upload_type", "uploaded_file"),
                        "url",
                        "description",
                        "copyright_type",
                        ("copyright_first_name", "copyright_last_name"),
                        ("copyright_email", "copyright_phone"),
                        "resource_class"
            ),
        }),
    ]

    readonly_fields = []


class ImageUploadInline(admin.StackedInline):
    model = Upload
    extra = 0
    classes = ( "grp-collapse grp-open",)
    fieldsets = [
        (None, {
            "fields":(  "title",
                        ("creator_full_name", "creator_company"),
                        ("image_thumbnail_html", "upload_type", "image_file"),
                        "url",
                        "description",
                        "copyright_type",
                        ("copyright_first_name", "copyright_last_name"),
                        ("copyright_email", "copyright_phone"),
                        "resource_class"
            ),
        }),
    ]

    readonly_fields = ["image_thumbnail_html"]

    def image_thumbnail_html(self, obj):
        try:
            return u'<img style="max-width:229px" src="%s" />' % (obj.image_thumbnail.url)
        except:
            return None


class UploadTypeAdmin(admin.ModelAdmin):

    fields = (("code", "title", "status"), "description", ("folder", "allowed_types"), ("allowed_min", "allowed_max", "max_file_size"))


class FileTypeAdmin(admin.ModelAdmin):

    fields = ("title", "extension")


admin.site.register(UploadType, UploadTypeAdmin)
admin.site.register(FileType, FileTypeAdmin)
admin.site.register(ImageUpload)

