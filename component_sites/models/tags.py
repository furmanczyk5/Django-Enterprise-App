from wagtail.wagtailcore.models import Orderable
from modelcluster.fields import ParentalKey

from django.db import models
from wagtail.wagtailcore.models import Page
from wagtail.wagtailadmin.edit_handlers import FieldPanel, PageChooserPanel


class ComponentSiteTag(Page):

    class Meta:
        abstract = True


class ComponentSiteTagRelationship(Orderable, models.Model):

    class Meta:
        abstract = True


class TopicTag(ComponentSiteTag):
    related_tag = models.ForeignKey("content.tag", related_name="wagtail_topic_tag",
                                    blank=True, null=True, on_delete=models.SET_NULL)

    content_panels = Page.content_panels + [
        FieldPanel("related_tag")
    ]


class TopicTagRelationship(ComponentSiteTagRelationship):
    tag = models.ForeignKey(
        'component_sites.TopicTag',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    page = ParentalKey('wagtailcore.Page', related_name='related_topics')

    panels = [
        PageChooserPanel('tag'),
    ]


class CommunityTypeTag(ComponentSiteTag):
    related_tag = models.ForeignKey("content.tag", related_name="wagtail_communitytype_tag",
                                    blank=True, null=True, on_delete=models.SET_NULL)

    content_panels = Page.content_panels + [
        FieldPanel("related_tag")
    ]


class CommunityTypeTagRelationship(ComponentSiteTagRelationship):
    tag = models.ForeignKey(
        'component_sites.CommunityTypeTag',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    page = ParentalKey('wagtailcore.Page', related_name='related_communitytypes')

    panels = [
        PageChooserPanel('tag'),
    ]


class JurisdictionTag(ComponentSiteTag):
    related_tag = models.ForeignKey("content.tag", related_name="wagtail_jurisdiction_tag",
                                    blank=True, null=True, on_delete=models.SET_NULL)

    content_panels = Page.content_panels + [
        FieldPanel("related_tag")
    ]


class JurisdictionTagRelationship(ComponentSiteTagRelationship):
    tag = models.ForeignKey(
        'component_sites.JurisdictionTag',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    page = ParentalKey('wagtailcore.Page', related_name='related_jurisdictions')

    panels = [
        PageChooserPanel('tag'),
    ]


