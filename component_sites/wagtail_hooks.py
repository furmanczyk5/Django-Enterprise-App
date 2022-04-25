import json
from datetime import datetime

from django.contrib import messages
from wagtail.wagtailcore import hooks

from content.solr_search import SolrUpdate
from content.utils import force_utc_datetime


class WagtailSolrPublish(object):

    obj = None
    wagtail_json = None

    def __init__(self, *args, **kwargs):
        super(WagtailSolrPublish, self).__init__()
        self.obj = args[0] if args else None
        self.request = args[1] if args else None

        if self.obj:
            self.wagtail_json = json.loads(self.obj.to_json())

    @property
    def solr_id(self):
        return "WAGTAIL_PAGE." + str(self.obj.revisions.first().id)

    def solr_publish(self, **kwargs):
        """
        method for publishing individual records to solr, will unpublish from solr if 'live' is False,
        returns the status code if successful, raises an exception if not
        """
        solr_base = kwargs.pop("solr_base", None)

        pub_data = [self.solr_format()]
        solr_response = SolrUpdate(pub_data, solr_base=solr_base).publish()

        if solr_response.status_code != 200:
            raise Exception("An error occured while trying to publish this event to Search. Status Code: %s" % solr_response.status_code)
        else:
            return solr_response.status_code

    def solr_unpublish(self, **kwargs):
        """
        method for removing individual records from solr
        returns the status code if successful, raises an exception if not
        """
        solr_base = kwargs.pop("solr_base", None)
        pub_data = {"delete": {"id": self.solr_id}}
        solr_response = SolrUpdate(pub_data, solr_base=solr_base).publish()

        if solr_response.status_code != 200:
            raise Exception("An error occured while trying to remove results from Search. Status Code: %s"
                            % solr_response.status_code)

        return solr_response.status_code

    def solr_format(self):
        if type(self.request) != str:
            request_host = self.request.META['HTTP_HOST']
        else:
            request_host = ""

        site_name = None

        component_site_params = getattr(self.request, 'component_site_host', None)

        if component_site_params:
            site_name = component_site_params.get('site', None)

        if self.request == 'staging' or request_host.find('staging') > -1:
            host_insert = '-staging'
        elif self.request == 'local' or request_host.find('local') > -1:
            host_insert = '-local-development'
        else:
            host_insert = ''

        tokens = site_name.split('.')
        tokens[0] = tokens[0] + host_insert
        host = ".".join(tokens)

        formatted_content = {
            "id": self.solr_id,
            "record_type": "WAGTAIL_PAGE",
            "site": site_name,
            "code": host,  # use chapter/division host name
            "title": self.obj.title.strip(),  # strip so that spaces don't show first alphabetically
            "description": self.wagtail_json["search_description"],
            "slug": self.obj.slug,
            "content_type": self.obj.content_type.model,  # django content type -- need string no spaces
            # "content_area": host, # use chapter/division host name
            # "subtitle": self.subtitle,
            # "text": html_to_text(page_html_string),
            "url": self.obj.url_path,
            # "resource_url": self.resource_url,
            "parent": self.obj.get_parent().id,
            "has_product": False,
            "thumbnail": "",
            "featured_image": "",
            # "sort_time":self.obj.latest_revision_created_at,

            "archive_time": force_utc_datetime(self.obj.expire_at),
            "published_time": force_utc_datetime(self.obj.first_published_at),
            "updated_time": force_utc_datetime(self.obj.latest_revision_created_at),

            # "permission_groups": [x.name for x in self.obj.group_permissions.all()],
            # "resource_type": self.resource_type,
            # "keywords": [rt.related_tag.title for rt in self.obj.related_topics.all()],
            # "related": ["{0}|{1}".format(rf.relationship, str(rf.content_master_related_id)) for rf in self.contentrelationship_from.all()]
        }

        formatted_content["tags"] = []
        formatted_content["tag_types"] = []
        # dynamic fields are special... tags_* and contact_roles_*
        # sort by sort_number then title
        # translating related tag page into a tag type, even though a related tag page only has one tag

        formatted_content["tags_FORMAT"] = ["1242.FORMAT_WEBPAGE.Web Page"]

        sorted_topics = sorted((rtp for rtp in self.obj.related_topics.all() if rtp.tag and rtp.tag.live
                                ), key=lambda rtp: (9999 if rtp.sort_order is None else rtp.sort_order, rtp.tag.title)
                               )
        sorted_communitytypes = sorted((rtp for rtp in self.obj.related_communitytypes.all() if rtp.tag and rtp.tag.live
                                        ), key=lambda rtp: (9999 if rtp.sort_order is None else rtp.sort_order, rtp.tag.title)
                                       )
        sorted_jurisdictions = sorted((rtp for rtp in self.obj.related_jurisdictions.all() if rtp.tag and rtp.tag.live
                                       ), key=lambda rtp: (9999 if rtp.sort_order is None else rtp.sort_order, rtp.tag.title)
                                      )

        for rtp in sorted_topics:
            formatted_content["tags_" + "taxonomy_topics"] = "{0}.{1}.{2}".format(
                str(rtp.tag.id), rtp.tag.slug, rtp.tag.title)
            formatted_content["tags"] += [rtp.tag.title]

        for rtp in sorted_communitytypes:
            formatted_content["tags_" + "community"] = "{0}.{1}.{2}".format(
                str(rtp.tag.id), rtp.tag.slug, rtp.tag.title)
            formatted_content["tags"] += [rtp.tag.title]

        for rtp in sorted_jurisdictions:
            formatted_content["tags_" + "jurisdiction"] = "{0}.{1}.{2}".format(
                str(rtp.tag.id), rtp.tag.slug, rtp.tag.title)
            formatted_content["tags"] += [rtp.tag.title]

        formatted_content["is_apa"] = False

        # breadcrumb
        ancestors_and_self = list(self.obj.get_ancestors()) + [self.obj]
        homepage = ancestors_and_self[1]
        # this is the wagtail site record
        site = homepage.sites_rooted_here.first()
        formatted_content["breadcrumb"] = ["https://{0}|{0}".format(site.hostname)]
        if len(ancestors_and_self) > 3:
            parent_page = ancestors_and_self[-2]
            formatted_content["breadcrumb"].append("https://{site}{path}|{name}".format(
                site=site.hostname,
                path=parent_page.url_path,
                name=parent_page.title))

        return formatted_content


def wagtail_solr_publish(request, page):
    if page.live and (not page.has_unpublished_changes or not page.first_published_at):
        if not page.first_published_at:
            page.first_published_at = datetime.now()
        publish_object = WagtailSolrPublish(page, request)
        publish_object.solr_publish()
        if request and type(request) != str:
            messages.success(request, "Page '%s' has been published to search." % page.title)
    elif not page.live:
        publish_object = WagtailSolrPublish(page, request)
        publish_object.solr_unpublish()


@hooks.register('after_create_page')
def wagtail_solr_publish_after_create(request, page):
    wagtail_solr_publish(request, page)


@hooks.register('after_edit_page')
def wagtail_solr_publish_after_edit(request, page):
    wagtail_solr_publish(request, page)

# @hooks.register('construct_image_chooser_queryset')
# def show_my_uploaded_images_only(images, request):
#     # Only show uploaded images
#     images = images.filter(collection=request.site.collection)
#
#     return images
