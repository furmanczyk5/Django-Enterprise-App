import datetime

from django.db import models

from content.models import BaseContent, Content, MasterContent, \
    ContentManager, SerialPub, Tag, TagType, ContentTagType

from content.utils import generate_filter_model_manager, force_utc_datetime

# TO DO: consider removing comletely as bookstore is no more
PUBLICATION_FORMATS = (
    ("ONLINE", "Online"),
    ("BOOK_PAPERBACK", "Paperback"),
    ("BOOK_HARDCOVER", "Hardcover"),
    ("DOWNLOAD_PDF", "Adobe PDF"),
    ("DOWNLOAD_EPUB", "EPUB"),
    ("DOWNLOAD_MOBI", "MOBI"),
    ("OTHER", "Other format"),
    ("CD", "CD"), # is this still used?
)


class Publication(Content):
    """
    for both overview landing pages (e.g. L1, L2 pages in sitemap), as well as marketing promo landing pages. These pages
    can define search criteria for including a search or search results on the page.
    """

    def generate_file_path(self, filename):
        return "publication/%s/%s" % (self.publication_format.lower(), filename)


    objects = generate_filter_model_manager(ParentManager=ContentManager, content_type="PUBLICATION")()

    # ---------------------------------------------------------------------
    # TO DO: MOVE THE FOLLOWING INFO FROM CONTENT TO HERE
    # WARNING... when that happens, media will document uploads will be affected...
    # will require data move/refactoring form content table to this one

    #taxo fields;
    # abstract = models.TextField(blank=True, null=True)

    #should this just be a tag?
    # resource_type = models.CharField(blank = True, null=True, max_length=50, choices=RESOURCE_TYPES)

    # serial_pub = models.ForeignKey("SerialPub", null=True, blank=True)
    # volume_number = models.IntegerField(null=True, blank=True)
    # issue_number = models.IntegerField(null=True, blank=True)

    # resource_published_date = models.DateField(blank=True, null=True)
    # copyright_date = models.DateField(blank=True, null=True)
    # copyright_statement = models.CharField(max_length=1000, blank=True, null=True)
    # isbn = models.CharField(max_length=20, null=True, blank=True)
    page_count = models.IntegerField(null=True, blank=True)
    edition = models.CharField(max_length=100, null=True, blank=True)

    # TO DO... link to item in other formats
    table_of_contents = models.TextField(blank=True, null=True)

    # TO DO: consider removing completely as bookstore is no more
    publication_format = models.CharField(max_length=50, choices=PUBLICATION_FORMATS, default="Paperback")
    publication_download = models.FileField(upload_to=generate_file_path, null=True, blank=True)

    sort_time = models.DateTimeField("Sort date and time", blank=True, null=True)
    date_text = models.TextField("Editable publication date", blank=True, null=True)
    author_bios = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        self.content_type = "PUBLICATION"
        super().save(*args, **kwargs)
        # updates format tag based on resource_type if this is a draft record being saved
        if self.publish_status == "DRAFT":
            format_tag_type = TagType.objects.get(code="FORMAT")
            format_contenttagtype, is_created = ContentTagType.objects.get_or_create(content=self, tag_type=format_tag_type)
            try:
                format_tag = Tag.objects.get(tag_type=format_tag_type, code="FORMAT_"+self.resource_type)
                format_contenttagtype.tags.clear()
                format_contenttagtype.tags.add(format_tag)
                format_contenttagtype.save()
            except Tag.DoesNotExist:
                pass

    def solr_format(self):
        formatted_content = super().solr_format()
        sorting_date = force_utc_datetime(self.sort_time) if self.sort_time and type(self.sort_time) == datetime.datetime else self.resource_published_date
        formatted_content_additional = {
            "date_text": self.date_text,
            "author_bios": self.author_bios, # NOT IN SCHEMA YET
            "sort_time": sorting_date,
            # on Content resource_published_date is written to sort_time in solr; here we need it like this:
            "resource_published_date": self.resource_published_date
        }
        formatted_content.update(formatted_content_additional);

        to_remove = []
        for i in formatted_content.items():
            if type(i[0]) == type('') and i[0].find('contact_roles_') >= 0:
                to_remove.append(i[0])
        for k in to_remove:
            del formatted_content[k]
        self.get_solr_format_contacts(formatted_content)

        return formatted_content

    def get_solr_format_contacts(self, formatted_content):

        is_apa = False

        for x in [y for y in self.contactrole.all()]:
            x_key = "contact_roles_" + x.role_type
            contact_id = x.contact.id if x.contact else ""

            # FIRST TWO CONDITIONS HERE FLIPPED FROM content.get_solr_format_contacts()
            if x.first_name or x.last_name:
                contact_title = str(x.first_name) + " " + str(x.last_name)  # then non-linked individual
            elif x.contact:
                contact_title = x.contact.title  # then linked to imis
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

    class Meta:
        verbose_name = "Publication"
        verbose_name_plural = "All publications"

class Report(Publication):
    objects = generate_filter_model_manager(ParentManager=ContentManager,
            content_type="PUBLICATION", resource_type="REPORT")()

    def save(self, *args, **kwargs):
        self.content_type = "PUBLICATION"
        self.content_area = "KNOWLEDGE_CENTER"
        self.resource_type = "REPORT"
        super().save(*args, **kwargs)

    class Meta:
        proxy = True


class PublicationDocument(Publication):
    objects = generate_filter_model_manager(ParentManager=ContentManager,
            content_type="PUBLICATION", resource_type="PUBLICATION_DOCUMENT")()

    def save(self, *args, **kwargs):
        self.content_type = "PUBLICATION"
        if not self.template:
            self.template = "publications/newtheme/publication-document.html"
        if not self.content_area:
            self.content_area = "KNOWLEDGE_CENTER"
        self.resource_type = "PUBLICATION_DOCUMENT"
        super().save(*args, **kwargs)

    class Meta:
        proxy = True


class Article(Publication):
    objects = generate_filter_model_manager(ParentManager=ContentManager,
            content_type="PUBLICATION", resource_type="ARTICLE")()

    def save(self, *args, **kwargs):
        self.content_type = "PUBLICATION"
        self.content_area = "KNOWLEDGE_CENTER"
        self.resource_type = "ARTICLE"
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "Specialty publication article"


class PlanningMagArticle(Article):

    objects = generate_filter_model_manager(ParentManager=ContentManager,
            content_type="PUBLICATION", resource_type="ARTICLE", serial_pub__code="PLANNING")()

    def save(self, *args, **kwargs):
        self.content_type = "PUBLICATION"
        self.resource_type = "ARTICLE"
        if not self.template:
            self.template = "publications/newtheme/planning-mag-article.html"
        # self.template = "publications/newtheme/planning-mag.html"
        if not self.serial_pub:
            self.serial_pub = SerialPub.objects.get(code="PLANNING")
        super().save(*args, **kwargs)

    def get_two_crumb_breadcrumb(self):
        """ gets two page breadcrumb: the site root, and the parent page """
        site_root = "https://www.planning.org"
        breadcrumb = [dict(text="Planning Magazine", href="{0}/planning/".format(site_root))]
        if self.parent_landing_master:
            parent_page = self.parent_landing_master.content_live
            if parent_page and parent_page.url != "/":
                breadcrumb.append(dict(text=parent_page.title, href="{0}{1}".format(site_root, parent_page.url)))
        return breadcrumb

    class Meta:
        proxy = True
        verbose_name = "Planning magazine article"

# TO DO EVENTUALLY: remove?
class MultipleFormatsRelated(BaseContent):
    related_content = models.ManyToManyField(MasterContent, related_name="multiple_formats")

    class Meta:
        verbose_name = "publication with multiple formats for sale"
        verbose_name_plural = "publications with multiple formats for sale"

class PlanningMagFeaturedContentTagType(ContentTagType):
    objects = generate_filter_model_manager(ParentManager=models.Manager, tag_type__code="PLANNING_MAG_FEATURED")()

    def save(self, *args, **kwargs):
        self.tag_type = TagType.objects.get(code="PLANNING_MAG_FEATURED")
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "Article Featured Zone"
        verbose_name_plural = "Article Featured Zones"

class PlanningMagSectionContentTagType(ContentTagType):
    objects = generate_filter_model_manager(ParentManager=models.Manager, tag_type__code="PLANNING_MAG_SECTION")()

    def save(self, *args, **kwargs):
        self.tag_type = TagType.objects.get(code="PLANNING_MAG_SECTION")
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "Article Section"
        verbose_name_plural = "Article Sections"

class PlanningMagSeriesContentTagType(ContentTagType):
    objects = generate_filter_model_manager(ParentManager=models.Manager, tag_type__code="PLANNING_MAG_SERIES")()

    def save(self, *args, **kwargs):
        self.tag_type = TagType.objects.get(code="PLANNING_MAG_SERIES")
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "Article Series"
        verbose_name_plural = "Article Series"

class PlanningMagSlugContentTagType(ContentTagType):
    objects = generate_filter_model_manager(ParentManager=models.Manager, tag_type__code="PLANNING_MAG_SLUG")()

    def save(self, *args, **kwargs):
        self.tag_type = TagType.objects.get(code="PLANNING_MAG_SLUG")
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "Article Slug"
        verbose_name_plural = "Article Slugs"

class PlanningMagSponsoredContentTagType(ContentTagType):
    objects = generate_filter_model_manager(ParentManager=models.Manager, tag_type__code="SPONSORED")()

    def save(self, *args, **kwargs):
        self.tag_type = TagType.objects.get(code="SPONSORED")
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "Sponsored Article"
        verbose_name_plural = "Sponsored Articles"
