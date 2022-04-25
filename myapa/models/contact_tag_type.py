from django.db import models

from content.models import Publishable


# Or better to just put the Content tag code directly on Contact?
# For "Firm Specializations" on Consultant records:
class ContactTagType(Publishable):
    contact = models.ForeignKey('myapa.Contact', related_name="contacttagtype", on_delete=models.CASCADE)
    tag_type = models.ForeignKey('content.TagType', related_name="contacttagtype", on_delete=models.CASCADE)
    tags = models.ManyToManyField('content.Tag', blank=True)

    publish_reference_fields = [
        {
            "name": "tags",
            "publish": False,
            "multi": True
        }
    ]

    class Meta:
        verbose_name = "additional type of tag (contacts)"
        verbose_name_plural = "additional tagging (contacts)"
