import datetime
import uuid
import re

from django.utils import timezone

from wagtail.wagtailcore import blocks
from wagtail.wagtailimages.blocks import ImageChooserBlock
from wagtail.contrib.table_block.blocks import TableBlock

from content.solr_search import SolrSearch
from events.models import Event, NATIONAL_CONFERENCE_CURRENT

from myapa.models.contact import Contact


class LinkBlock(blocks.StructBlock):
    Link_Text = blocks.CharBlock(required=True)
    Link_URL = blocks.URLBlock()


class ButtonBlock(LinkBlock):
    pass


class ReadMoreLinkBlock(LinkBlock):
    pass


class StyledLinkBlock(LinkBlock):
    Link_Style = blocks.ChoiceBlock(
        choices=[
            ("REGULAR", "Regular Link"),
            ("BUTTON", "Button"),
            ("FANCY", "Fancy Link")],
        default="REGULAR")

    class Meta:
        template = "component-sites/component-theme/blocks/link.html"


class LinkedImageBlock(blocks.StructBlock):
    image = ImageChooserBlock()
    url = blocks.URLBlock()

    class Meta:
        template = "component-sites/component-theme/blocks/image-linked.html"


class FeatureBlock(blocks.StructBlock):
    # overline
    Featured_Text = blocks.CharBlock(required=True, help_text="Help text for Featured Text/Overline")
    # heading
    Headline = blocks.CharBlock(required=True)
    # paragraph
    Intro_Text = blocks.RichTextBlock()
    # image
    Inset_Image = ImageChooserBlock()
    link = StyledLinkBlock()

    class Meta:
        template = "component-sites/component-theme/blocks/feature.html"


class SecondaryFeatureBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=True)
    paragraph = blocks.RichTextBlock()
    link = StyledLinkBlock()

    def __init__(self, *args, **kwargs):
        self.classname = kwargs.pop("classname", "")
        super().__init__(*args, **kwargs)

    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)
        context["classname"] = self.classname
        return context

    class Meta:
        template = "component-sites/component-theme/blocks/feature-secondary.html"


class SecondaryFeaturePairBlock(blocks.StructBlock):
    feature1 = SecondaryFeatureBlock()
    feature2 = SecondaryFeatureBlock()

    class Meta:
        template = "component-sites/component-theme/blocks/feature-secondary-pair.html"


class SecondaryFeaturePairChapterBlock(SecondaryFeaturePairBlock):
    feature1 = SecondaryFeatureBlock(classname="chapter-homepage-featured-content-secondary-1")
    feature2 = SecondaryFeatureBlock(classname="chapter-homepage-featured-content-secondary-2")

    class Meta:
        template = "component-sites/component-theme/blocks/feature-secondary-pair.html"


class FeaturedVideoBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=True)
    video = blocks.URLBlock(help_text="url for youtube video")
    link = StyledLinkBlock()

    class Meta:
        template = "component-sites/component-theme/blocks/feature/column/video.html"


class FeaturedPhotoGalleryBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=True)
    photos = blocks.ListBlock(ImageChooserBlock)
    link = StyledLinkBlock(required=False)

    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)
        context["gallery_identifier"] = uuid.uuid4()
        return context

    class Meta:
        template = "component-sites/component-theme/blocks/feature/column/gallery.html"

class NoLinkPhotoGalleryBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=True)
    photos = blocks.ListBlock(ImageChooserBlock)

    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)
        context["gallery_identifier"] = uuid.uuid4()
        return context

    class Meta:
        template = "component-sites/component-theme/blocks/feature/column/gallery.html"


class FeaturedImageTilesBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=True)
    images = blocks.ListBlock(LinkedImageBlock)
    link = StyledLinkBlock()

    class Meta:
        template = "component-sites/component-theme/blocks/feature/column/image-tiles.html"


class FeaturedImageWithLinks(blocks.StructBlock):
    heading = blocks.CharBlock(required=True)
    image = LinkedImageBlock()
    listed_links = blocks.ListBlock(LinkBlock)
    link = StyledLinkBlock()

    class Meta:
        template = "component-sites/component-theme/blocks/feature/column/image-with-links.html"


# DIVISION BLOCKS
class FeaturedTextBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=True)
    paragraph = blocks.RichTextBlock()
    link = StyledLinkBlock()

    class Meta:
        template = "component-sites/component-theme/blocks/feature/column/text.html"


class FeaturedListBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=True)
    listed_links = blocks.ListBlock(LinkBlock)
    link = StyledLinkBlock()

    class Meta:
        template = "component-sites/component-theme/blocks/feature/column/list.html"


class FeaturedEventsBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=True)

    def get_events(self, provider, addl_providers):
        # TO DO: Query from Solr?
        now = timezone.now()
        datetime_now_json = datetime.datetime.strftime(now, "%Y-%m-%dT%H:%M:%SZ")
        addl_provider_str = ''
        if addl_providers:
            for addl_provider in Contact.objects.filter(user__username__in=addl_providers.split(',')):
                addl_provider_str += str(addl_provider.id) + " "
        filters = [
            "event_type:(EVENT_SINGLE EVENT_MULTI EVENT_INFO)",
            "begin_time:[{0} TO *]".format(datetime_now_json),
            "contact_roles_PROVIDER:({0}* {1})".format(getattr(provider, "id", "0"),
                                                       addl_provider_str.replace(' ', '* '))]
        return SolrSearch(
            filters=filters,
            sort="begin_time asc",
            rows=4).get_results()

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        if parent_context:
            context["hostname"] = parent_context.get("hostname")
        provider = context.get("org")
        addl_providers = context.get("addl_providers")
        context["events"] = self.get_events(provider, addl_providers)
        return context

    class Meta:
        template = "component-sites/component-theme/blocks/feature/column/events.html"


class FeaturedNewsBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=True)

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        host = None
        if parent_context:
            host = parent_context["request"].get_host()
        filters = [
            "content_type:newspage",
            "code:\"{0}\"".format(host)]

        context["news"] = SolrSearch(
            filters=filters,
            sort="published_time desc",
            rows=4).get_results()

        return context

    class Meta:
        template = "component-sites/component-theme/blocks/feature/column/news.html"


class FeaturedNPCActivitiesBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=True)

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        if parent_context:
            context["hostname"] = parent_context.get("hostname")


        most_recent_conf = Event.objects.get(code=NATIONAL_CONFERENCE_CURRENT[0], publish_status='PUBLISHED')

        # this still needs to be limited by being a child of upcomin NPC

        fq = ["content_type:EVENT",
              "parent:{0}".format(most_recent_conf.master.id)]

        if parent_context.get('tag'):
            tag = parent_context.get("tag")
            escaped_title = "\ ".join(tag.title.split(" ")) if tag else ''
            fq.append("tags_DIVISION:{0}.{1}.{2}".format(tag.id, tag.code, escaped_title))

        context["activities"] = SolrSearch(
            filters=fq,
            sort="begin_time asc",
            rows=4).get_results()

        return context

    class Meta:
        template = "component-sites/component-theme/blocks/feature/column/npc-activities.html"


class ColumnFeaturesStreamBlock(blocks.StreamBlock):
    """
    Stream Block for rendering items into columns
        left-to-right, then top-to-bottom
    Use cols argument to specify the number of columns (default 2)
    Use stack arument to specify if items are stacked by "row", or "col" (default "row")
    """

    def __init__(self, *args, **kwargs):
        self.cols = kwargs.pop("cols", 2)
        self.stack = kwargs.pop("stack", "row")
        super().__init__(*args, **kwargs)

    def render(self, *args, **kwargs):
        if self.stack == "col":
            # only way for conditional template using view logic, could also use template logic instead
            self.meta.template = "component-sites/component-theme/blocks/feature-columns-stream/stacked-cols.html"
        return super().render(*args, **kwargs)

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)

        rows = []
        for i, item in enumerate(value):
            col_index = i % self.cols
            if (i == 0) or (self.stack != "col" and col_index == 0):
                columns = [[] for _ in range(self.cols)]
                rows.append(columns)
            columns[col_index].append(item)

        context["rows"] = rows
        return context

    class Meta:
        template = "component-sites/component-theme/blocks/feature-columns-stream/stacked-rows.html"


class HeaderBlock(blocks.StructBlock):
    text = blocks.CharBlock(required=True)

    class Meta:
        template = "component-sites/component-theme/blocks/body/header.html"


class CallOutBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=True)
    subheading = blocks.CharBlock(required=False)
    body = blocks.RichTextBlock()

    class Meta:
        template = "component-sites/component-theme/blocks/body/call-out.html"


class BioBlock(blocks.StructBlock):
    # BIO LIST? or SINGLE BIO ?
    detail = blocks.CharBlock(required=False)
    name = blocks.CharBlock(required=False)
    description = blocks.RichTextBlock()
    image = ImageChooserBlock(required=False)

    class Meta:
        template = "component-sites/component-theme/blocks/body/bio.html"


class ImageWithCaptionBlock(blocks.StructBlock):
    image = ImageChooserBlock(required=True)
    caption = blocks.CharBlock(required=False)

    class Meta:
        template = "component-sites/component-theme/blocks/body/image-with-caption.html"


class ImageWithTextBlock(ImageWithCaptionBlock):
    image_style = blocks.ChoiceBlock(
        choices=(("image-block-float-right", "Float Right"), ("image-block-float-left", "Float Left")),
        required=True)
    body = blocks.RichTextBlock()

    class Meta:
        template = "component-sites/component-theme/blocks/body/image-with-text.html"


class PullQuoteBlock(blocks.StructBlock):
    body = blocks.RichTextBlock()

    class Meta:
        template = "component-sites/component-theme/blocks/body/pull-quote.html"


class ResponsiveTableBlock(TableBlock):

    class Meta:
        template = "component-sites/component-theme/blocks/body/responsive-table.html"


class PageBodyStreamBlock(blocks.StreamBlock):
    header = HeaderBlock()
    rich_text = blocks.RichTextBlock()
    link = StyledLinkBlock()
    call_out = CallOutBlock()
    bio = BioBlock()
    pull_quote = PullQuoteBlock()
    image_with_caption = ImageWithCaptionBlock()
    image_with_text = ImageWithTextBlock()
    photo_gallery = FeaturedPhotoGalleryBlock()
    photo_gallery_no_link = NoLinkPhotoGalleryBlock()
    table = ResponsiveTableBlock()

    class Meta:
        template = "component-sites/component-theme/blocks/stream-block.html"


