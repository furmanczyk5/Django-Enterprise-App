from wagtail.wagtailimages.models import Image, AbstractImage, AbstractRendition

from django.db import models

class ComponentImage(AbstractImage):
    alt_text = models.TextField('Alt Text', max_length=80, default="", blank=True)
    admin_form_fields = Image.admin_form_fields + ("alt_text", )

class ComponentRendition(AbstractRendition):
    image = models.ForeignKey(ComponentImage, on_delete=models.CASCADE, related_name='renditions')

    class Meta:
        unique_together = (
            ('image', 'filter_spec', 'focal_point_key'),
        )
