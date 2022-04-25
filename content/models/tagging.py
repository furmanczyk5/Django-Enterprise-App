from django.db import models

from .base_content import BaseContent
from .publishable_mixin import Publishable

from content.utils import generate_filter_model_manager


class ContentTagType(Publishable):
    content = models.ForeignKey('Content', related_name="contenttagtype", on_delete=models.CASCADE)
    tag_type = models.ForeignKey('TagType', related_name="contenttagtype", on_delete=models.CASCADE)
    tags = models.ManyToManyField('Tag', blank=True)

    publish_reference_fields = [
        {
            "name": "tags",
            "publish": False,
            "multi": True
        }
    ]

    class Meta:
        verbose_name = "additional type of tag"
        verbose_name_plural = "additional tagging"


class TagType(BaseContent):
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    min_allowed = models.IntegerField(null=True, blank=True)
    max_allowed = models.IntegerField(null=True, blank=True)
    submission_only = models.BooleanField(default=False)
    sort_number = models.IntegerField(null=True, blank=True)


# TO DO? add object manager for Tag so that we always pull related TagType at the same time?
class Tag(BaseContent):
    tag_type = models.ForeignKey('TagType', related_name="tags", on_delete=models.CASCADE)
    sort_number = models.IntegerField(null=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    related = models.ManyToManyField('self', blank=True) #symmetrical=True by default
    taxo_term = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        ordering = ["title"]

    @staticmethod
    def autocomplete_search_fields():
        return "code__icontains", "title__icontains"


class TaxoTopicTagManager(models.Manager):
    def get_queryset(self):
        return super(TaxoTopicTagManager, self).get_queryset().filter(tag_type__code="TAXO_MASTERTOPIC")


class TaxoTopicTag(Tag):
    objects = TaxoTopicTagManager()

    def __str__(self):
        return self.title if self.status == 'A' else "(Inactive): " + self.title

    def save(self, *args, **kwargs):
        self.tag_type = TagType.objects.using(kwargs.get("using")).get(code='TAXO_MASTERTOPIC')
        super(Tag, self).save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "Topic Tagging"
        verbose_name_plural = "Topic Tagging"


class TaxoTopicTagFlat(Tag):
    objects = TaxoTopicTagManager()

    def save(self, *args, **kwargs):
        self.tag_type = TagType.objects.get(code='TAXO_MASTERTOPIC')
        super(Tag, self).save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "TaxoTopicTag (Flat)"
        verbose_name_plural = "TaxoTopicTags (Flat)"


class JurisdictionContentTagType(ContentTagType):
    objects = generate_filter_model_manager(ParentManager=models.Manager, tag_type__code="JURISDICTION")()

    def save(self, *args, **kwargs):
        self.tag_type = TagType.objects.get(code="JURISDICTION")
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "jurisdiction tagging"
        verbose_name_plural = "jurisdiction tagging"


class CommunityTypeContentTagType(ContentTagType):
    objects = generate_filter_model_manager(ParentManager=models.Manager, tag_type__code="COMMUNITY_TYPE")()

    def save(self, *args, **kwargs):
        self.tag_type = TagType.objects.get(code="COMMUNITY_TYPE")
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "community type tagging"
        verbose_name_plural = "community type tagging"


class FormatContentTagType(ContentTagType):
    objects = generate_filter_model_manager(ParentManager=models.Manager, tag_type__code="FORMAT")()

    def save(self, *args, **kwargs):
        self.tag_type = TagType.objects.get(code="FORMAT")
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "format tagging"
        verbose_name_plural = "format tagging"

