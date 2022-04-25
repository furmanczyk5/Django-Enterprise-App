from django.contrib.auth.models import Group
from django.db import models
from django.utils import timezone

from content.solr_search import SolrUpdate
from content.tasks import publish_content_task
from content.utils import force_utc_datetime, html_to_text
from .base_content import BaseContent
from .master_content import MasterContent
from .publishable_mixin import Publishable
from .settings import *
from .tagging import ContentTagType, Tag, TagType


class ContentManager(models.Manager):
    """
    Model manager for Content
    """
    def with_details(self):
        """
        Use to query for extra data that is useful when viewing content records
        e.g. Content.objects.with_details().get(master_id=.....)
        """
        active_tags_prefetch = models.Prefetch(
            "tags",
            queryset=Tag.objects.filter(status="A"),
            to_attr="active_tags")

        active_contenttagtypes_prefetch = models.Prefetch(
            "contenttagtype",
            queryset=ContentTagType.objects.filter(tag_type__status="A", tags__status="A").prefetch_related(active_tags_prefetch).distinct(),
            to_attr="active_contenttagtypes"
        )

        qs = self.get_queryset().select_related("master").prefetch_related(active_contenttagtypes_prefetch)
        return qs

# TO DO... get rid of this??? move to publications app?
class SerialPub(BaseContent):
    issn = models.CharField(max_length=50, null=True, blank=True)


# TO DO... this single model definition is nearly 700 lines of code long!!!! clean it up...
class Content(BaseContent, Publishable):

    # TO DO... consider: should content_type be specified on MasterContent instead of/in addtion to here??
    content_type = models.CharField(max_length=50, choices=CONTENT_TYPES, default="PAGE")


    master = models.ForeignKey('MasterContent', related_name="content", blank=True, null=True)

    workflow_status = models.CharField(max_length=50, choices=WORKFLOW_STATUSES, default='DRAFT_IN_PROGRESS',
        help_text="For future use.")

    content_area = models.CharField(max_length=50, choices=CONTENT_AREAS, default="NONE")

    parent_landing_master = models.ForeignKey(
        "pages.LandingPageMasterContent",
        verbose_name="Parent landing page",
        related_name="sub_content",
        blank=True,
        null=True,
        help_text="""The landing page under which this content belongs within the overall sitemap.
        This determines the side menu (if applicable) and breadcrumb links.""",
        on_delete=models.SET_NULL
    )

    # note, this field duplicates data... but may make our lives easier!
    # publish_status = models.CharField(max_length=50, choices=PUBLISH_STATUSES, default='DRAFT')

    template = models.CharField(max_length=50, choices=TEMPLATES, blank=True, null=True)

    subtitle = models.CharField(max_length=1000, blank=True, null=True)
    overline = models.CharField(max_length=1000, null=True, blank=True)

    text = models.TextField("Full text/body of content", blank=True, null=True)

    #adding unique=True created issues when url left blank... any way to make it unique ONLY if not null?
    #better to call this path...?
    url = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='The url for the content, starting with "/".',
        db_index=True
    )
    resource_url =models.URLField(max_length=255, blank=True, null=True)
    file_path = models.CharField(max_length=255, blank=True, null=True, help_text="the path of the htm file (if content is coming from file instead of db)") # the path of the htm file (if content is coming from file instead of db)

    # QUESTION... remove this? we're basically ALWAYS assuming that this is true...
    has_xhtml = models.BooleanField(default=True)
    # increasing to 2550 to accomodate staff aicp exam administrators
    editorial_comments = models.CharField(max_length=2550, blank=True, null=True,
        help_text="Comments to author")
    archive_time = models.DateTimeField('archive time', blank=True, null=True)
    make_public_time = models.DateTimeField('make public time', blank=True, null=True)
    make_inactive_time = models.DateTimeField('make inactive time', blank=True, null=True)

    parent = models.ForeignKey(MasterContent, related_name='children', blank=True, null=True, on_delete=models.SET_NULL)

    # submission related stuff:
    submission_category = models.ForeignKey(
        "submissions.Category",
        related_name="content",
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )
    submission_period = models.ForeignKey(
        "submissions.Period",
        related_name="content",
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )
    submission_verified = models.BooleanField(default=False)
    submission_time = models.DateTimeField("submitted on", blank=True, null=True)
    submission_approved_time = models.DateTimeField("approved on", blank=True, null=True)
    thumbnail = models.ImageField(upload_to="thumbnail", max_length=100, blank=True, null=True)
    thumbnail_2 = models.ImageField(upload_to="thumbnail", max_length=100, blank=True, null=True)

    is_apa = models.BooleanField(default=False) # to differentiate apa content vs other content (e.g. member submitted events, images, etc.)

    # how to deal with custom tags for specific pieces of content (outside of taxonomy)?
    tag_types = models.ManyToManyField('TagType', through="ContentTagType", blank=True)
    taxo_topics = models.ManyToManyField("TaxoTopicTag", blank=True)

    permission_groups = models.ManyToManyField(Group, blank=True, null=True)
    show_content_without_groups = models.BooleanField(default=False, help_text="""
        Enable if content should be displayed (e.g. as marketing material), even if the user does not have the required permission groups.
        Generally used for media/resources where the media download may be restricted to certain groups, but we always want to show
        the content text for marketing purposes.
        """)

    #taxo fields;
    abstract = models.TextField(blank=True, null=True)

    #should this just be a tag?
    resource_type = models.CharField(blank = True, null=True, max_length=50, choices=RESOURCE_TYPES,
        help_text="A subset of the APA format facet, used for publications.")
    serial_pub = models.ForeignKey('SerialPub', null=True, blank=True, on_delete=models.SET_NULL)
    volume_number = models.IntegerField(null=True, blank=True)
    issue_number = models.IntegerField(null=True, blank=True)
    language = models.CharField(max_length=50, choices=LANGUAGES, null=True, blank=True)
    resource_published_date = models.DateField(blank=True, null=True)
    copyright_date = models.DateField(blank=True, null=True)
    copyright_statement = models.CharField(max_length=1000, blank=True, null=True)
    isbn = models.CharField(max_length=20, null=True, blank=True)

    related = models.ManyToManyField(MasterContent, through="ContentRelationship", related_name='related_from', symmetrical=False, blank=True)

    keywords = models.TextField(help_text="keywords that users don't see", blank=True, null=True)

    featured_image = models.ForeignKey(
        "media.MediaImageMasterContent",
        related_name="featured_image_content",
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )
    featured_image_caption = models.CharField(max_length=2000, blank=True, null=True)

    # These are updated for content when a related comment is saved
    rating_average  = models.DecimalField(decimal_places=2, max_digits=4, editable=False, blank=True, null=True)
    rating_count    = models.IntegerField(editable=False, blank=True, null=True)

    # For checkin/checkout system, internal use only
    checkin_username = models.CharField(max_length=10, blank=True, null=True)
    checkin_time = models.DateTimeField(blank=True, null=True)

    # og metadata
    og_url = models.URLField(max_length=255, blank=True, null=True)
    og_title = models.CharField(max_length=200, blank=True, null=True)
    og_type = models.CharField(max_length=50, blank=True, null=True, choices=OG_TYPES)
    og_description = models.TextField(blank=True, null=True)
    og_image = models.ForeignKey(
        "media.MediaImageMasterContent",
        related_name="og_image_content",
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )

    # Structured Data Markup
    structured_data_markup = models.TextField(blank=True, null=True)

    # class attribute to tell that the model inherits/is content. (this method is prefered rather than using isinstance)
    is_content = True

    # default template used for details page
    default_template = "pages/newtheme/default.html"

    objects = ContentManager()

    def is_published(self):
        return self.master.content_live is not None
    is_published.boolean = True
    is_published.short_description = 'Published?'

    def is_up_to_date(self):
        return self.is_published() and self.master.published_time is not None and self.master.published_time >= self.updated_time
    is_up_to_date.boolean = True
    is_up_to_date.short_description = 'Up to Date?'

    #COULD BE USED FOR DEBUGGING:
    # def is_published_to_solr(self):
    #     r = SolrSearch(query="id:CONTENT."+str(self.master_id)).get_results()
    #     return r['response']['numFound'] == 1
    # is_published_to_solr.boolean = True
    # is_published_to_solr.short_description = 'Published to Solr?'

    def solr_format(self):

        featured_image = self.get_featured_image_media()

        formatted_content = {
            "id": self.solr_id,
            "record_type": "CONTENT",
            "code": self.code,
            "title": self.title.strip() if self.title else "", #strip so that spaces don't show first alphabetically
            "description": self.description,
            "slug": self.slug,
            "content_type": self.content_type,
            "content_area": self.content_area,
            "subtitle": self.subtitle,
            "text": html_to_text(self.text),
            "url": self.url,
            "resource_url": self.resource_url,
            "parent": self.parent_id,
            "has_product": self.get_product() is not None,
            "thumbnail": self.thumbnail.url if self.thumbnail else "",
            "thumbnail_2": self.thumbnail_2.url if self.thumbnail_2 else "",
            "featured_image": featured_image.image_file.url if featured_image else "",
            "sort_time": self.resource_published_date,

            # "publish_time":force_utc_datetime(self.publish_time), # NOT IN SCHEMA YET
            "archive_time": force_utc_datetime(self.archive_time),
            "published_time": force_utc_datetime(self.master.published_time),
            "updated_time": force_utc_datetime(self.updated_time),

            "permission_groups": [x.name for x in self.permission_groups.all()],
            "resource_type": self.resource_type,
            "keywords": self.keywords,

            "related": [
                "{0}|{1}".format(
                    rf.relationship,
                    str(rf.content_master_related_id)
                ) for rf in self.contentrelationship_from.all()
            ],
            "tags": [],
            "tag_types": [],
            "contacts": []
        }

        self.get_solr_format_tags(formatted_content)

        self.get_solr_format_contacts(formatted_content)

        self.get_solr_format_prices(formatted_content)

        # two-crumb-max breadcrumb
        breadcrumb = self.get_two_crumb_breadcrumb()
        formatted_content["breadcrumb"] = ["{0}|{1}".format(
            crumb.get("href"), crumb.get("text")
        ) for crumb in breadcrumb]

        return formatted_content

    def get_solr_format_prices(self, formatted_content):
        # prices
        product = getattr(self, "product", None)
        if product:
            formatted_content["prices"] = [
                "%.2f|@|%s" % (price["price"], price["title"])
                for price in product.prices.values(
                    "id", "priority", "title", "price"
                ).filter(
                    include_search_results=True, status="A"
                ).order_by(
                    "-priority"
                )
            ]

    def get_solr_format_contacts(self, formatted_content):

        is_apa = False

        for x in [y for y in self.contactrole.all()]:
            x_key = "contact_roles_" + x.role_type
            contact_id = x.contact.id if x.contact else ""

            if x.contact:
                contact_title = x.contact.title  # then linked to imis
            elif x.first_name or x.last_name:
                contact_title = str(x.first_name) + " " + str(x.last_name)  # then non-linked individual
            else:
                contact_title = str(x.company)  # then non-linked company is the last thing we try

            formatted_content["contacts"].append(contact_title)
            if x_key in formatted_content:
                formatted_content[x_key].append(str(contact_id) + '|' + contact_title)
            else:
                formatted_content[x_key] = [str(contact_id) + '|' + contact_title]

            if x.contact and x.contact.company_is_apa:
                is_apa = True
        if is_apa:
            formatted_content["is_apa"] = True

    def get_solr_format_tags(self, formatted_content):
        # dynamic fields are special... tags_* and contact_roles_*
        for x in sorted(
            (ctt for ctt in self.contenttagtype.filter(tag_type__status='A')),
            # sort by sort_number then title
            key=lambda ctt: (
                9999 if ctt.tag_type.sort_number is None else ctt.tag_type.sort_number,
                ctt.tag_type.title
            )
        ):
            sorted_active_tags = sorted(
                (t for t in x.tags.filter(status='A')),
                # sort by sort number then title
                key=lambda t: (
                    9999 if t.sort_number is None else t.sort_number, t.title
                )
            )
            if sorted_active_tags:
                formatted_content["tag_types"].append(
                    "{0}.{1}.{2}".format(str(x.tag_type.id), x.tag_type.code, x.tag_type.title))
                formatted_content["tags_" + x.tag_type.code] = [
                    "{0}.{1}.{2}".format(str(tag.id), tag.code, tag.title)
                    for tag in sorted_active_tags
                ]
                formatted_content["tags"] += [tag.title for tag in sorted_active_tags]

    #####################
    # PUBLISHABLE STUFF #
    #####################
    is_publish_root = True # must start from this model when publishing
    is_solr_publishable = True # assume that everything inheriting from Content is solr publishable

    publish_reference_fields = [
        {
            "name": "permission_groups",
            "publish": False,
            "multi": True
        },
        {
            "name": "taxo_topics",
            "publish": False,
            "multi": True
        },
        {
            "name": "contacts",
            "publish": True,
            "multi": True,
            "through_name": "contactrole",
            "replace_field": "content"
        },
        {
            "name": "tag_types",
            "publish": True,
            "multi": True,
            "through_name": "contenttagtype",
            "replace_field": "content"
        },
        {
            "name": "related",
            "publish": True,
            "multi": True,
            "through_name": "contentrelationship_from",
            "replace_field": "content"
        },

        {
            "name": "places",
            "publish": True,
            "multi": True,
            "through_name": "contentplace",
            "replace_field": "content"
        },

        {
            "name": "product",
            "publish": True,
            "multi": False,
            "replace_field": "content"
        },
        {
            "name": "uploads",
            "publish": True,
            "multi": True,
            "replace_field": "content"
        }
    ]

    def publish(self, replace=(None, None), publish_type="PUBLISHED", database_alias="default", versions=None):

        if versions is None:
            versions = self.get_versions()

        the_master, master_is_created = MasterContent.objects.using(database_alias).get_or_create(id=self.master_id)

        published_instance = super().publish(replace=("master_id", the_master.id), publish_type=publish_type, database_alias=database_alias, versions=versions)

        if publish_type == "PUBLISHED":
            the_master.content_live = published_instance
            the_master.published_time = timezone.now()
            the_master.save(using=database_alias)
        elif publish_type == "DRAFT":
            the_master.content_draft = published_instance
            the_master.save(using=database_alias)
        elif publish_type in("SUBMISSION", "EARLY_RESUBMISSION"):
            the_master.content_submission = published_instance
            the_master.save(using=database_alias)
        return published_instance

    def deep_copy(self, replace=dict()):

        replace["master"] = None
        instance = super().deep_copy(replace=replace)
        if instance.publish_status == "PUBLISHED":
            the_master = instance.master
            the_master.content_live = instance
            the_master.published_time = timezone.now()
            the_master.save()
        elif instance.publish_status == "DRAFT":
            the_master = instance.master
            the_master.content_draft = instance
            the_master.save()
        return instance

    def publish_async(self, **kwargs):
        """
        PUBLISHING ASYNCHRONOUSLY
        """
        args = (
                self.__class__,
                self.id,
                kwargs.get("solr_publish", False),
                kwargs.get("publish_type", "PUBLISHED"),
                kwargs.get("database_alias", "default"),
                kwargs.get("solr_base", None),
            )
        eta = kwargs.get("eta", None)
        publish_content_task.apply_async(args=args, eta=eta)

    @property
    def solr_id(self):
        return "CONTENT." + str(self.master_id)

    def solr_publish(self, **kwargs):
        """
        method for publishing individual records to solr, will unpublish from solr if status is not "A",
        returns the status code if successful, raises an exception if not
        """
        solr_base = kwargs.pop("solr_base", None)
        if self.status == "A" and self.is_solr_publishable:
            pub_data = [self.solr_format()]
            solr_response = SolrUpdate(pub_data, solr_base=solr_base).publish()

            if solr_response.status_code != 200:
                raise Exception("An error occured while trying to publish this event to Search. Status Code: %s" % solr_response.status_code)
            else:
                return solr_response.status_code
        else:
            # if it shouldn't be on solr, then remove it
            self.solr_unpublish(solr_base=solr_base)

    def solr_unpublish(self, **kwargs):
        """
        method for removing individual records from solr
        returns the status code if successful, raises an exception if not
        """
        solr_base = kwargs.pop("solr_base", None)
        pub_data = {"delete":{"id": self.solr_id }}
        solr_response = SolrUpdate(pub_data, solr_base=solr_base).publish()

        if solr_response.status_code != 200:
            raise Exception("An error occured while trying to remove results from Search. Status Code: %s" % solr_response.status_code)

        return solr_response.status_code

    def taxo_topic_tags_save(self):
        """
        saves all tags in the taxo_topics field and all their related search topic tags
        in the contentagtype/tagtype/tag structure
        """
        # updating contenttagtype records based off of taxo master topics
        if self.taxo_topics.all():
            taxo_tag_type = TagType.objects.get(code="TAXO_MASTERTOPIC")
            taxo_contenttagtype, is_created = ContentTagType.objects.get_or_create(content=self, tag_type=taxo_tag_type)
            taxo_contenttagtype.tags.clear()
            taxo_contenttagtype.tags.add(*self.taxo_topics.all())
            taxo_contenttagtype.save()

            search_tag_type = TagType.objects.get(code="SEARCH_TOPIC")
            search_contenttagtype, is_created = ContentTagType.objects.get_or_create(content=self, tag_type=search_tag_type)

            search_contenttagtype.tags.clear()
            for taxo_tag in taxo_contenttagtype.tags.all():
                related_search_tags = Tag.objects.filter(id__in=taxo_tag.related.all(), tag_type__code="SEARCH_TOPIC")
                search_contenttagtype.tags.add(*related_search_tags)

            if not search_contenttagtype.tags.all():
                ContentTagType.objects.filter(content=self, tag_type__code="SEARCH_TOPIC").delete()
            else:
                search_contenttagtype.save()

        else:
            ContentTagType.objects.filter(content=self, tag_type__code="TAXO_MASTERTOPIC").delete()
            # We don't want to wipe out the search topic if there is no taxo topic, many submissions only tag with the search topic
            # ContentTagType.objects.filter(content=self, tag_type__code="SEARCH_TOPIC").delete()

        return self

    def sync_to_imis(self, **kwargs):
        """
        This is a hook for syncing data to iMIS
        """
        pass

    def make_public(self):
        """
        removes all permission groups on draft record, saves and publishes to live and to search
        """
        perm_grps = self.permission_groups.all()
        for groo in perm_grps:
            self.permission_groups.remove(groo)
        self.permission_groups.clear()
        self.save()
        self.publish()
        # Publishing to solr disabled for now because of:
        # Exception('An error occured while trying to publish this event to Search. Status Code: 404'
        self.solr_publish()

    def make_inactive(self):
        """
        changes status to 'I' saves and publishes to live and to search
        """
        self.status = 'I'
        self.save()
        self.publish()
        # Publishing to solr disabled for now because of:
        # Exception('An error occured while trying to publish this event to Search. Status Code: 404'
        self.solr_publish()

    def recalculate_rating(self):
        """
        method for recalculating the rating_average and rating_count
        """
        rating_stats = self.comments.exclude(is_deleted=True).aggregate(rating_average=models.Avg("rating"), rating_count=models.Count("rating"))
        self.rating_average = rating_stats.get("rating_average", 0.00)
        self.rating_count = rating_stats.get("rating_count", 0)

    def get_parent_landing_page(self):
        """
        Returns the parent landing page record (either draft or published), based on whether the self is draft or published
        """
        if self.parent_landing_master:
            if self.publish_status=="DRAFT":
                content = self.parent_landing_master.content_draft
            else:
                content = self.parent_landing_master.content_live
            if content:
                try:
                    # just in case parent_landing_master is not properly set to landing page instance
                    return content.landingpage
                except:
                    pass

    def get_landing_ancestors(self, landing_heirarchy=None, publish_status="DRAFT", recursion_left=5):

        if not landing_heirarchy:
            is_landingpage = self._meta.model_name == "landingpage"  # prevent unnecessary db query
            if is_landingpage:
                landing_heirarchy = [self]
            elif getattr(self, "landingpage", None):
                landing_heirarchy = [self.landingpage]
            else:
                landing_heirarchy = []

        # TO DO: hard-coding CONFERENCE_HOME here is janky
        if recursion_left > 0 and self.parent_landing_master and self.code != "CONFERENCE_HOME":

            parent_landing_page = self.get_parent_landing_page()
            if parent_landing_page and parent_landing_page != self:
                landing_heirarchy.insert(0, parent_landing_page)

                return parent_landing_page.get_landing_ancestors(
                    landing_heirarchy=landing_heirarchy,
                    publish_status=publish_status,
                    recursion_left=recursion_left-1)

        return landing_heirarchy

    def get_landing_ancestors_admin_links(self):
        def get_admin_link(landing):
            return "<a href='/admin/pages/landingpage/%s/'>%s</a>" % (landing.id, landing.title)
        links_string = ""
        for l in self.get_landing_ancestors():
            links_string += get_admin_link(l) + " -> "
        return links_string
    get_landing_ancestors_admin_links.short_description = "Location in Sitemap"
    get_landing_ancestors_admin_links.allow_tags = True

    def get_absolute_url(self):
        if self.url:
            return "https://www.planning.org{0}".format(self.url)
        else:
            my_app = self._meta.app_label
            my_model = self._meta.model_name
            my_id = self.master_id
            # TO DO: these hardcoded exceptions are wonky...
            # should come up with a better way to associate url paths with model names
            if my_app == "learn" and my_model == "learncourse":
                my_model = "course"
            if my_app == "learn" and my_model == "learncoursebundle":
                my_model = "bundle"
            elif my_app == "publications" and my_model == "publicationdocument":
                my_model = "document"
            return "https://www.planning.org/{0}/{1}/{2}/".format(my_app, my_model, my_id)

    def get_two_crumb_breadcrumb(self):
        """hook for controlling how models construct the breadcrumbs published to solr"""
        ancestors = self.get_landing_ancestors()
        ancestors.reverse()
        breadcrumbs = []
        for i,a in enumerate(ancestors):
            if i < 2:
                url = a.url if a.url else ""
                breadcrumbs.append(dict(text=a.title, href="{0}".format(url)))
        breadcrumbs.reverse()
        return breadcrumbs

    def save(self, *args, **kwargs):
        # saving is NOT required until the end... django figures out the ID references OK without calling save twice
        # super().save(*args,**kwargs)
        resave_master = False

        if not self.template:
            if getattr(self, "product", None):
                self.template = "store/newtheme/product/details.html"
            else:
                self.template = self.default_template

        if self.master is None:
            resave_master = True
            mc_new = MasterContent.objects.using(kwargs.get("using")).create() # In all cases this should be created if master is None
            self.master = mc_new

        # default values for og meta tags
        self.og_title = self.og_title or self.title
        self.og_description = self.og_description or self.description
        self.og_type = self.og_type or "article"
        self.og_url = self.og_url or self.get_absolute_url()
        self.og_image = self.og_image or self.get_featured_image()

        if not self.pk:
            content_code = self.code
            if content_code and Content.objects.filter(code=content_code).exclude(master_id=self.master_id).exists():
                raise Exception(
                    "Error: Attempt to create new Content record with code that already exists: %s"
                    % content_code
                )

            product = getattr(self, "product", None)

            if product:
                product_code = product.code
                imis_code = product.imis_code
                first_code = content_code or product_code or imis_code
                if not first_code:
                    pass
                else:
                    if not (content_code == product_code == imis_code):
                        self.code = first_code
                        self.product.code = first_code
                        self.product.imis_code = first_code
                    if self.parent:
                        self.product.imis_code = self.parent.content_draft.code + "/" + self.product.imis_code

        if self.archive_time and self.archive_time.year < MINIMUM_YEAR:
            self.archive_time = self.archive_time.replace(year=MINIMUM_YEAR)

        super().save(*args,**kwargs)

        # for newly created records, the content_draft foreign key for the master needs to be set and the master resaved
        if resave_master:
            if self.publish_status == "DRAFT": # don't want to do this for every content that is saved...only for DRAFT
                mc_new.content_draft = self
            elif self.publish_status == "PUBLISHED":
                mc_new.content_live = self
            mc_new.save()


        # ... add appropriate place and place_data data/tags here (region, population range and density)

    def get_product(self):
        """
        gets the product tied to the content, without raise an error in it doesn't exist
        """
        try:
            return self.product
        except:
            return None

    def get_featured_image(self):
        """Simple for normal content, different of inherited class (e.i. Images)"""
        return self.featured_image

    def get_featured_image_media(self):
        try:
            return self.get_featured_image().content_live.media
        except:
            return None

    def thumbnail_html(self):
        try:
            return u'<img style="max-width:229px" src="%s" />' % (self.thumbnail.url)
        except:
            return None
    thumbnail_html.allow_tags = True
    thumbnail_html.short_description = ""

    def thumbnail_2_html(self):
        try:
            return u'<img style="max-width:229px" src="%s" />' % (self.thumbnail_2.url)
        except:
            return None
    thumbnail_2_html.allow_tags = True
    thumbnail_2_html.short_description = ""

    def details_context(self):
        return {}

    def get_draft_preview_path(self):
        if self.url:
            return "%s?publish_status=DRAFT" % self.url
        else:
            return "/%s/%s/%s/?publish_status=DRAFT" % (self._meta.app_label, self._meta.model_name, self.master_id)

    @staticmethod
    def autocomplete_search_fields():
        return ("id__iexact", "master__id__iexact", "title__icontains")

    class Meta:
        verbose_name = "Content Record"
        verbose_name_plural = "All Content Records"
