import datetime

from django.db import models
from django.utils import timezone


from wagtail.wagtailcore.models import Page, Site
from wagtail.wagtailcore.fields import StreamField, RichTextField

from wagtail.wagtailcore import blocks
from wagtail.wagtailadmin.edit_handlers import FieldPanel, StreamFieldPanel, \
    MultiFieldPanel, InlinePanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel

from content.solr_search import SolrSearch
from content.models.settings import OG_TYPES
from myapa.models.contact import Contact
from .settings import ProviderSettings

from component_sites import blocks as component_blocks


class ComponentSitePage(Page):

    def correct_video_url(self, request):
        new_ac = []
        for block_dict in self.additional_content.stream_data:
            if block_dict["type"] == 'video':
                # link is a dict of Link_Text, Link_URL, Link_Style
                old_ac_video_link_dict = block_dict["value"]["link"]
                # video and heading are single values
                old_ac_video_url = block_dict["value"]["video"]
                old_ac_heading = block_dict["value"]["heading"]
                if not old_ac_video_url:
                    new_ac.append(block_dict)
                else:
                    if "watch?v=" not in old_ac_video_url:
                        new_ac.append(block_dict)
                    else:
                        old_url_parts = old_ac_video_url.split("watch?v=")
                        new_url = "https://www.youtube.com/embed/" + old_url_parts[1]
                        new_ac.append({
                            'type': 'video',
                            'value': {
                                'link': {
                                    'Link_Text': old_ac_video_link_dict['Link_Text'],
                                    'Link_URL': old_ac_video_link_dict['Link_URL'],
                                    'Link_Style': old_ac_video_link_dict['Link_Style']},
                                'video': new_url,
                                'heading': old_ac_heading}})
            else:
                new_ac.append(block_dict)
        self.additional_content.stream_data = new_ac

    def get_root_page_and_hostname(self, request):
        site_name = hostname = request.component_site_host.get("hostname")
        site = Site.objects.get(hostname=site_name)
        root_page = Page.objects.get(id=site.root_page_id)
        return (root_page, hostname)

    def get_context(self, request):
        context = super(ComponentSitePage, self).get_context(request)
        self.provider_settings = ProviderSettings.for_site(request.site)
        self.addl_providers = self.provider_settings.additional_contacts
        self.provider = self.provider_settings.contact

        if self.provider.member_type == 'CHP':
            context["component_type"] = "Chapter"
        elif self.provider.member_type == 'DVN':
            context["component_type"] = "Division"

        context["org"] = self.provider
        context["title"] = self.provider.title
        context["abs_url"] = self.url
        context["is_wagtail_site"] = True
        return context

    class Meta:
        abstract = True


class StandardPage(ComponentSitePage):
    template = "component-sites/component-theme/templates/standard.html"

    body = StreamField(component_blocks.PageBodyStreamBlock(), default=[])

    og_type = models.CharField(max_length=50, default="article", choices=OG_TYPES)
    og_description = models.TextField(blank=True, null=True, help_text="Description for shared link, at least two sentences long.")
    og_image = models.ForeignKey('component_sites.ComponentImage',
                                 related_name='+', on_delete=models.SET_NULL,
                                 blank=True, null=True, help_text="Description for shared link, at least two sentences long.")

    content_panels = Page.content_panels + [
        StreamFieldPanel("body"),

        InlinePanel('related_topics', label="Topics"),
        InlinePanel('related_communitytypes', label="Community Types"),
        InlinePanel('related_jurisdictions', label="Jurisdictions"),
        MultiFieldPanel(
            (
                FieldPanel("og_type"),
                FieldPanel("og_description"),
                ImageChooserPanel("og_image")
            ),
            heading="Page Metadata"),
    ]




class LandingPage(ComponentSitePage):
    template = "component-sites/component-theme/templates/landing.html"

    featured_image = models.ForeignKey(
        'component_sites.ComponentImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+')

    featured_content = StreamField([('feature', component_blocks.FeatureBlock()), ], default=[])

    body = RichTextField()  # Should this be stream field?

    additional_content = StreamField(blocks.StreamBlock(
        [
            ("features_section", component_blocks.ColumnFeaturesStreamBlock(
                [
                    ("video", component_blocks.FeaturedVideoBlock()),
                    ("photo_gallery", component_blocks.FeaturedPhotoGalleryBlock()),
                    ("photo_gallery_no_link", component_blocks.NoLinkPhotoGalleryBlock()),
                    ("tiled_images", component_blocks.FeaturedImageTilesBlock()),
                    ("text", component_blocks.FeaturedTextBlock()),
                    ("feature_list", component_blocks.FeaturedListBlock()),
                    ("events", component_blocks.FeaturedEventsBlock()),
                    ("news", component_blocks.FeaturedNewsBlock()),
                    ("npc_activities", component_blocks.FeaturedNPCActivitiesBlock())],
                cols=2,
                stack="row"
            )),
            ("columns_of_links_section", component_blocks.FeaturedListBlock(
                template="component-sites/component-theme/blocks/feature-link-list-section.html")),
        ],
        template="component-sites/component-theme/blocks/stream-block.html"),
        default=[])

    og_type = models.CharField(max_length=50, default="article", choices=OG_TYPES)
    og_description = models.TextField(blank=True, null=True, help_text="Description for shared link, at least two sentences long.")
    og_image = models.ForeignKey('component_sites.ComponentImage',
                                 related_name='+', on_delete=models.SET_NULL,
                                 blank=True, null=True, help_text="Description for shared link, at least two sentences long.")

    # then column of links? everyone has this?

    content_panels = Page.content_panels + [
        ImageChooserPanel("featured_image"),
        StreamFieldPanel("featured_content"),
        FieldPanel("body", classname="full"),
        StreamFieldPanel("additional_content"),

        InlinePanel('related_topics', label="Topics"),
        InlinePanel('related_communitytypes', label="Community Types"),
        InlinePanel('related_jurisdictions', label="Jurisdictions"),
        MultiFieldPanel(
            (
                FieldPanel("og_type"),
                FieldPanel("og_description"),
                ImageChooserPanel("og_image")
            ),
            heading="Page Metadata")
    ]

    def get_events(self, provider):
        # TO DO: Query from Solr?
        now = timezone.now()
        datetime_now_json = datetime.datetime.strftime(now, "%Y-%m-%dT%H:%M:%SZ")
        addl_provider_str = ''
        if self.addl_providers:
            for addl_provider in Contact.objects.filter(user__username__in=self.addl_providers):
                addl_provider_str += str(addl_provider.id) + " "

        filters = [
            "event_type:(EVENT_SINGLE EVENT_MULTI EVENT_INFO)",
            "begin_time:[{0} TO *]".format(datetime_now_json),
            "contact_roles_PROVIDER:({0}* {1})".format(getattr(provider, "id", "0"),
                                                       addl_provider_str.replace(' ', '    ss* '))]
        return SolrSearch(
            filters=filters,
            sort="begin_time asc",
            rows=4
        ).get_results()

    def get_context(self, request):
        context = super(LandingPage, self).get_context(request)
        self.correct_video_url(request)
        root_page, hostname = self.get_root_page_and_hostname(request)
        context["org"] = self.provider
        context["hostname"] = hostname
        return context

class DivisionHomePage(ComponentSitePage):
    template = "component-sites/component-theme/templates/division-home.html"
    featured_image = models.ForeignKey(
        'component_sites.ComponentImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    featured_content = StreamField([
        ('feature', component_blocks.FeatureBlock()),
        ('secondary_features', component_blocks.SecondaryFeaturePairBlock()),
    ], default=[])

    additional_content = StreamField(component_blocks.ColumnFeaturesStreamBlock(
        [
            ("video", component_blocks.FeaturedVideoBlock()),
            ("photo_gallery", component_blocks.FeaturedPhotoGalleryBlock()),
            ("photo_gallery_no_link", component_blocks.NoLinkPhotoGalleryBlock()),
            ("tiled_images", component_blocks.FeaturedImageTilesBlock()),
            ("text", component_blocks.FeaturedTextBlock()),
            ("feature_list", component_blocks.FeaturedListBlock()),
            ("events", component_blocks.FeaturedEventsBlock()),
            ("news", component_blocks.FeaturedNewsBlock()),
            ("npc_activities", component_blocks.FeaturedNPCActivitiesBlock())],
        cols=3,
        stack="col"
    ), default=[])

    og_type = models.CharField(max_length=50, default="article", choices=OG_TYPES)
    og_description = models.TextField(blank=True, null=True, help_text="Description for shared link, at least two sentences long.")
    og_image = models.ForeignKey('component_sites.ComponentImage',
                                 related_name='+', on_delete=models.SET_NULL,
                                 blank=True, null=True, help_text="Description for shared link, at least two sentences long.")

    content_panels = Page.content_panels + [
        ImageChooserPanel("featured_image"),
        StreamFieldPanel("featured_content"),
        StreamFieldPanel("additional_content"),

        InlinePanel('related_topics', label="Topics"),
        InlinePanel('related_communitytypes', label="Community Types"),
        InlinePanel('related_jurisdictions', label="Jurisdictions"),

        MultiFieldPanel(
            (
                FieldPanel("og_type"),
                FieldPanel("og_description"),
                ImageChooserPanel("og_image")
            ),
            heading="Page Metadata"),
    ]

    def get_context(self, request):
        context = super(DivisionHomePage, self).get_context(request)
        self.correct_video_url(request)
        root_page, hostname = self.get_root_page_and_hostname(request)
        context["tag"] = getattr(self.provider_settings, 'tag')
        context["hostname"] = hostname
        return context

class ChapterHomePage(ComponentSitePage):
    template = "component-sites/component-theme/templates/chapter-home.html"
    featured_image = models.ForeignKey(
        'component_sites.ComponentImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    featured_content = StreamField([
        ('feature', component_blocks.FeatureBlock()),
        ('secondary_features', component_blocks.SecondaryFeaturePairChapterBlock()),
    ])

    include_events = models.BooleanField(default=True)
    events_image = models.ForeignKey(
        'component_sites.ComponentImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    include_news = models.BooleanField(default=True)
    news_image = models.ForeignKey(
        'component_sites.ComponentImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    include_jobs = models.BooleanField(default=False)
    jobs_image = models.ForeignKey(
        'component_sites.ComponentImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    additional_content = StreamField(component_blocks.ColumnFeaturesStreamBlock(
        [
            ("video", component_blocks.FeaturedVideoBlock()),
            ("photo_gallery", component_blocks.FeaturedPhotoGalleryBlock()),
            ("photo_gallery_no_link", component_blocks.NoLinkPhotoGalleryBlock()),
            ("image_with_links", component_blocks.FeaturedImageWithLinks()),
            ("tiled_images", component_blocks.FeaturedImageTilesBlock())],
        cols=2,
        stack="row"
    ), default=[])

    og_type = models.CharField(max_length=50, default="article", choices=OG_TYPES)
    og_description = models.TextField(blank=True, null=True, help_text="Description for shared link, at least two sentences long.")
    og_image = models.ForeignKey('component_sites.ComponentImage',
                                 related_name='+', on_delete=models.SET_NULL,
                                 blank=True, null=True, help_text="Image for shared link. Facebook recommends 1200 x 630 pixels.")

    content_panels = Page.content_panels + [
        ImageChooserPanel("featured_image"),
        StreamFieldPanel("featured_content"),
        MultiFieldPanel(
            (
                FieldPanel("include_events"),
                ImageChooserPanel("events_image")
            ),
            heading="Events Section"
        ),
        MultiFieldPanel(
            (
                FieldPanel("include_news"),
                ImageChooserPanel("news_image")
            ),
            heading="News Section"
        ),
        MultiFieldPanel(
            (
                FieldPanel("include_jobs"),
                ImageChooserPanel("jobs_image")
            ),
            heading="Jobs Section"
        ),
        StreamFieldPanel("additional_content"),

        MultiFieldPanel(
            (
                FieldPanel("og_type"),
                FieldPanel("og_description"),
                ImageChooserPanel("og_image")
            ),
            heading="Page Metadata"),
        InlinePanel('related_topics', label="Topics"),
        InlinePanel('related_communitytypes', label="Community Types"),
        InlinePanel('related_jurisdictions', label="Jurisdictions"),

    ]

    def get_events(self, provider):
        # TO DO: Query from Solr?
        now = timezone.now()
        datetime_now_json = datetime.datetime.strftime(now, "%Y-%m-%dT%H:%M:%SZ")
        addl_provider_str = ''
        if self.addl_providers:
            for addl_provider in self.addl_providers.all():
                addl_provider_str += str(addl_provider.id) + " "

        filters = [
            "event_type:(EVENT_SINGLE EVENT_MULTI EVENT_INFO)",
            "begin_time:[{0} TO *]".format(datetime_now_json),
            "contact_roles_PROVIDER:({0}* {1})".format(provider, addl_provider_str.replace(' ', '* '))]
        return SolrSearch(
            filters=filters,
            sort="begin_time asc",
            rows=4
        ).get_results()

    def get_news(self, request):
        hostname = request.get_host()
        filters = [
            "content_type:newspage",
            "code:\"{0}\"".format(hostname)]
        return SolrSearch(
            filters=filters,
            sort="published_time desc",
            rows=4
        ).get_results()

    def get_jobs(self, provider):
        now = timezone.now()
        datetime_now_json = datetime.datetime.strftime(now, "%Y-%m-%dT%H:%M:%SZ")
        filters = [
            "content_type:JOB",
            "begin_time:[* TO {0}]".format(datetime_now_json),
            "end_time:[{0} TO *]".format(datetime_now_json),
            "contact_roles_PROVIDER:{0}|*".format(provider)]
        return SolrSearch(
            filters=filters,
            sort="sort_time desc",
            rows=4
        ).get_results()

    def get_context(self, request):
        context = super(ChapterHomePage, self).get_context(request)
        root_page, hostname = self.get_root_page_and_hostname(request)

        context["events"] = self.get_events(provider=self.provider.id)
        context["news"] = self.get_news(request)
        context["jobs"] = self.get_jobs(provider=self.provider.id)
        context["hostname"] = hostname

        return context


class NewsPage(ComponentSitePage):
    post_time = models.DateTimeField("post time", blank=True, null=True)
    template = "component-sites/component-theme/templates/news.html"
    # tags = ClusterTaggableManager(through=NewsPageTag, blank=True)

    body = StreamField(component_blocks.PageBodyStreamBlock(), default=[])

    og_type = models.CharField(max_length=50, default="article", choices=OG_TYPES)
    og_description = models.TextField(blank=True, null=True, help_text="Description for shared link, at least two sentences long.")
    og_image = models.ForeignKey('component_sites.ComponentImage',
                                 related_name='+', on_delete=models.SET_NULL,
                                 blank=True, null=True, help_text="Description for shared link, at least two sentences long.")

    content_panels = Page.content_panels + [
        StreamFieldPanel("body"),

        InlinePanel('related_topics', label="Topics"),
        InlinePanel('related_communitytypes', label="Community Types"),
        InlinePanel('related_jurisdictions', label="Jurisdictions"),
        MultiFieldPanel(
            (
                FieldPanel("og_type"),
                FieldPanel("og_description"),
                ImageChooserPanel("og_image")
            ),
            heading="Page Metadata"),
    ]
