from django.db import models
from django.db.models import Q
from django.utils import timezone

from myapa.models.contact_role import ContactRole
from content.models import Content, ContentManager, \
    ContentTagType, TagType

from content.utils import generate_filter_model_manager

class BlogCategoryContentTagType(ContentTagType):
    objects = generate_filter_model_manager(
        ParentManager=models.Manager,
        tag_type__code="BLOG_CATEGORY")()

    def save(self, *args, **kwargs):
        self.tag_type = TagType.objects.get(code="BLOG_CATEGORY")
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "blog category"
        verbose_name_plural = "blog categories"


# generic content that does not fit in a specific category
class BlogPost(Content):

    objects = generate_filter_model_manager(ParentManager=ContentManager, content_type="BLOG")() 

    def solr_format(self):
        formatted_content = super().solr_format()
        formatted_content["begin_time"] = self.resource_published_date
        return formatted_content

    def publish(self, replace=(None,None), publish_type="PUBLISHED", database_alias="default"):

        if publish_type == "PUBLISHED" and self.status == "A":
            type(self).objects.using(database_alias).filter(resource_published_date__isnull=True, publish_uuid=self.publish_uuid).update(resource_published_date=timezone.now().date())

        return_value = super().publish(replace, publish_type, database_alias)

        return return_value

    def save(self, *args, **kwargs):
        self.content_type = "BLOG" 
        super().save(*args, **kwargs)

    def details_context(self, *args, **kwargs):
        """
        Method inherited from Content to pass additional context to the details template. 
        """
        context = super().details_context()

        context["authors"] = ContactRole.objects.filter(content=self, role_type="AUTHOR").select_related("contact", "content")
        context["tags"] = [tag for ctt in ContentTagType.objects.filter(content=self, tag_type__code__in=["BLOG_CATEGORY", "SEARCH_TOPIC"]).prefetch_related("tags").select_related("tag_type") for tag in ctt.tags.all()]

        if self.resource_published_date and self.published_time:
            context["previous_blog"] = type(self).objects.filter(
                Q(resource_published_date__lt=self.resource_published_date) | Q(resource_published_date=self.resource_published_date, published_time__lt=self.published_time),
                status="A", publish_status="PUBLISHED",
            ).exclude(
                id=self.id
            ).order_by("-published_time").first()

            context["next_blog"] = type(self).objects.filter(
                Q(resource_published_date__gt=self.resource_published_date) | Q(resource_published_date=self.resource_published_date, published_time__gt=self.published_time),
                status="A", publish_status="PUBLISHED"
            ).exclude(
                id=self.id
            ).order_by("published_time").first()

        return context

    class Meta:
        proxy = True
