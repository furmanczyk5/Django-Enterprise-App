from django.db import models

from content.models import Content, MasterContent, ContentManager

from content.utils import generate_filter_model_manager


class Page(Content):
    class_queryset_args = {"content_type": "PAGE"}
    objects = generate_filter_model_manager(ParentManager=ContentManager, content_type="PAGE")()

    # TO DO... a little hacky to hard-code master ids... maybe use codes instead?
    default_parent_landing_master_id = None

    # TO DO... this is a little odd (used for "create page under this one" button)... any way to prevent having to do this?
    # and maybe redundant given logic in save() method???
    @classmethod
    def subclass_from_code(cls, content_area, content_type):
        if content_type == "PAGE_JOTFORM":
            return JotFormPage
        elif content_area == "KNOWLEDGE_CENTER" and content_type=="PAGE_AUDIO":
            return AudioPage
        elif content_area == "KNOWLEDGE_CENTER" and content_type=="PAGE_VIDEO":
            return VideoPage
        elif content_area == "KNOWLEDGE_CENTER" and content_type=="PAGE":
            return KnowledgeCenterPage
        elif content_area=="MEMBERSHIP":
            return MembershipPage
        elif content_area == "CONFERENCES":
            return ConferencesPage
        elif content_area == "AICP":
            return AICPPage
        elif content_area == "POLICY":
            return PolicyPage
        elif content_area == "CAREER":
            return CareerPage
        elif content_area == "OUTREACH":
            return OutreachPage
        elif content_area == "CONNECT":
            return ConnectPage
        elif content_area == "ABOUT":
            return AboutPage
        else:
            return UncategorizedPage

    # def get_two_crumb_breadcrumb(self):
    #     """ gets two page breadcrumb: the site root, and the parent page """
    #     site_root = "https://www.planning.org"
    #     breadcrumb = [dict(text="planning.org", href=site_root)]
    #     if self.parent_landing_master:
    #         parent_page = self.parent_landing_master.content_live
    #         if parent_page and parent_page.url != "/":
    #             breadcrumb.append(dict(text=parent_page.title, href="{0}{1}".format(site_root, parent_page.url)))
    #     return breadcrumb

    def save(self, *args, **kwargs):
        if self.content_type is None or "PAGE" not in self.content_type:
            self.content_type = "PAGE"

        if not self.parent_landing_master and self.default_parent_landing_master_id:
            try:
                self.parent_landing_master = LandingPageMasterContent.objects.get(id=self.default_parent_landing_master_id)
            except LandingPageMasterContent.DoesNotExist:
                pass

        if self.content_area == "NONE" \
                and self.parent_landing_master \
                and self.parent_landing_master.content_draft:
            self.content_area = self.parent_landing_master.content_draft.content_area

        return super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name_plural = "all pages"


# -------------------------------------------------------------------------
# NOTE... LandingPage is NOT a proxy because additional fields included

LANDING_SEARCH_SORT_CHOICES = (
    ("published_time desc", "Newest to Oldest"),
    ("published_time asc", "Oldest to Newest"),
    ("title asc", "Title"),
    ("", "Relevancy"),
)


class LandingPageMasterContentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            content__content_type="PAGE",
            content__landingpage__isnull=False
        ).distinct("id")


class LandingPageMasterContent(MasterContent):
    objects = LandingPageMasterContentManager()

    class Meta:
        proxy = True


class LandingPage(Content):
    """
    For both overview landing pages (e.g. L1, L2 pages in sitemap), as well as marketing promo landing pages. These pages
    can define search criteria for including a search or search results on the page.
    Landing pages can have menu items and sub-pages.
    """
    # class_queryset_args = {"content_type":"PAGE", "content_area":"LANDING"}
    prevent_auto_class_assignment = True
    objects = generate_filter_model_manager(ParentManager=ContentManager, content_type="PAGE")()

    show_search_results = models.BooleanField(
        default=False,
        help_text="Include dynamic search results on this landing page?"
    )
    search_query = models.TextField(
        blank=True,
        null=True,
        help_text="The query to pull records from the search. Work with IT to populate this field appropriately."
    )
    sort_field = models.CharField(
        max_length=50,
        default="sort_time desc",
        choices=LANDING_SEARCH_SORT_CHOICES,
        blank=True
    )
    search_max = models.IntegerField(default=20)
    # TO DO... is it possible to filter (parent) by other other landing pages in the admin?

    publish_reference_fields = Content.publish_reference_fields + [
        {"name": "child_menuitems",
            "publish": True,
            "multi": True,
            "replace_field": "parent_landing_page"}
    ]

    def get_child_add_url(self):
        return Page.subclass_from_code(self.content_area).get_admin_add_url() + "?parent_landing_master=" + str(self.master.id)

    def save(self, *args, **kwargs):
        self.content_type = "PAGE"
        super().save(*args, **kwargs)

    class Meta:
        proxy = False
        verbose_name = "landing page"

    @staticmethod
    def autocomplete_search_fields():
        return ("id__iexact", "title__icontains", "code__icontains")

# ------------------------------------------------------------------------------
# proxy models for specific content types (also see other apps for more):


class MembershipPage(Page):
    class_queryset_args = {"content_type": "PAGE", "content_area": "MEMBERSHIP"}
    objects = generate_filter_model_manager(
        ParentManager=ContentManager,
        content_type="PAGE",
        content_area="MEMBERSHIP"
    )()
    default_parent_landing_master_id = 9022797

    class Meta:
        proxy = True


class KnowledgeCenterPage(Page):
    class_queryset_args = {"content_type": "PAGE", "content_area": "KNOWLEDGE_CENTER"}
    objects = generate_filter_model_manager(
        ParentManager=ContentManager,
        content_type="PAGE",
        content_area="KNOWLEDGE_CENTER"
    )()

    class Meta:
        proxy = True
        verbose_name = "Knowledge center page"


class ConferencesPage(Page):
    class_queryset_args = {"content_type": "PAGE", "content_area": "CONFERENCES"}
    objects = generate_filter_model_manager(
        ParentManager=ContentManager,
        content_type="PAGE",
        content_area="CONFERENCES"
    )()

    class Meta:
        proxy = True
        verbose_name = "Conferences/meetings page"
        verbose_name_plural = "Conferences and meetings pages"


class AICPPage(Page):
    class_queryset_args = {"content_type": "PAGE", "content_area": "AICP"}
    objects = generate_filter_model_manager(
        ParentManager=ContentManager,
        content_type="PAGE",
        content_area="AICP"
    )()
    default_parent_landing_master_id = 9021558

    class Meta:
        proxy = True
        verbose_name = "AICP page"


class PolicyPage(Page):
    class_queryset_args = {"content_type": "PAGE", "content_area": "POLICY"}
    objects = generate_filter_model_manager(
        ParentManager=ContentManager,
        content_type="PAGE",
        content_area="POLICY"
    )()

    class Meta:
        proxy = True
        verbose_name = "Policy/advocacy page"
        verbose_name_plural = "Policy and advocacy pages"


class CareerPage(Page):
    class_queryset_args = {"content_type": "PAGE", "content_area": "CAREER"}
    objects = generate_filter_model_manager(
        ParentManager=ContentManager,
        content_type="PAGE",
        content_area="CAREER"
    )()

    class Meta:
        proxy = True
        verbose_name = "Career center page"


class OutreachPage(Page):
    class_queryset_args = {"content_type": "PAGE", "content_area": "OUTREACH"}
    objects = generate_filter_model_manager(
        ParentManager=ContentManager,
        content_type="PAGE",
        content_area="OUTREACH"
    )()

    class Meta:
        proxy = True
        verbose_name = "Community outreach page"


class ConnectPage(Page):
    class_queryset_args = {"content_type": "PAGE", "content_area": "CONNECT"}
    objects = generate_filter_model_manager(
        ParentManager=ContentManager,
        content_type="PAGE",
        content_area="CONNECT"
    )()

    class Meta:
        proxy = True
        verbose_name = "Connect with APA page"


class AboutPage(Page):
    class_queryset_args = {"content_type": "PAGE", "content_area": "ABOUT"}
    objects = generate_filter_model_manager(
        ParentManager=ContentManager,
        content_type="PAGE",
        content_area="ABOUT"
    )()

    class Meta:
        proxy = True
        verbose_name = "About APA page"

class AudioPage(Page):
    class_queryset_args = {"content_type":"PAGE_AUDIO", "content_area":"KNOWLEDGE_CENTER"}
    objects = generate_filter_model_manager(ParentManager=ContentManager,
            content_type="PAGE_AUDIO", content_area="KNOWLEDGE_CENTER")()
    default_parent_landing_master_id = 9022798

    class Meta:
        proxy = True
        verbose_name = "Searchable Media - Audio page"

    def save(self, *args, **kwargs):
        self.content_type = "PAGE_AUDIO"
        return super().save(*args, **kwargs)


class VideoPage(Page):
    class_queryset_args = {"content_type":"PAGE_VIDEO", "content_area":"KNOWLEDGE_CENTER"}
    objects = generate_filter_model_manager(ParentManager=ContentManager,
            content_type="PAGE_VIDEO", content_area="KNOWLEDGE_CENTER")()
    default_parent_landing_master_id = 9022798

    class Meta:
        proxy = True
        verbose_name = "Searchable Media - Video page"

    def save(self, *args, **kwargs):
        self.content_type = "PAGE_VIDEO"
        return super().save(*args, **kwargs)

class JotFormPage(Page):
    default_template = 'pages/newtheme/jotform.html'
    class_queryset_args = {"content_type": "PAGE_JOTFORM"}
    objects = generate_filter_model_manager(
        ParentManager=ContentManager,
        content_type="PAGE_JOTFORM",
    )()

    def save(self, *args, **kwargs):
        self.content_type = "PAGE_JOTFORM"
        return super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "JotForm page"


class UncategorizedPage(Page):
    class_queryset_args = {"content_type": "PAGE", "content_area": "NONE"}
    objects = generate_filter_model_manager(
        ParentManager=ContentManager,
        content_type="PAGE",
        content_area="NONE"
    )()

    class Meta:
        proxy = True
        verbose_name = "**Uncategorized page"
