
from django.db import models

from planning.models_subclassable import SubclassableModel
from .publishable_mixin import Publishable
from .master_content import MasterContent

CONTENT_RELATIONSHIPS = (
    ("RELATED", "Related"),
    ("KNOWLEDGEBASE_COLLECTION", "Belongs to knowledgebase collection"),
    ("LEARN_COURSE", "Learn course derived from conference activity"),
    ("LINKED_PUBLICATION", "Publication whose content is related to another publication")
)


class ContentRelationship(SubclassableModel, Publishable):
    content = models.ForeignKey('Content', related_name="contentrelationship_from", on_delete=models.CASCADE)
    content_master_related = models.ForeignKey(
        MasterContent,
        related_name="contentrelationship_to",
        on_delete=models.CASCADE
    )
    relationship = models.CharField(max_length=50, choices=CONTENT_RELATIONSHIPS)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
