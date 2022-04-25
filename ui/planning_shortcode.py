from django.template.loader import get_template

from content.models import Content
from content.solr_search import SolrSearch
from directories.models import Directory

DEFAULT_RESOURCE_TEMPLATE = 'ui/planning_shortcode/resources-two-column.html'


def advertisements():
    t = get_template("ui/planning_shortcode/advertisements.html")
    return t.render({})


def blog(tag_id=None, template_name="ui/planning_shortcode/blogs.html", max=None):
    filters = ["content_type:BLOG"]
    _append_tag_id_query(filters, tag_id)
    rows = max or 10000
    results = SolrSearch(filters=[" AND ".join(filters)], rows=rows, sort="sort_time desc").get_results()
    t = get_template(template_name)
    return t.render({"results": results})


def book_carousel():
    results = SolrSearch(filters=["tags_BOOKS_PROMO:*.BOOKS_FEATURED.*"]).get_results()
    t = get_template("ui/planning_shortcode/book-carasol.html")
    return t.render({"results": results})


def search_bar(search_url="/search/"):
    t = get_template("ui/planning_shortcode/search-bar.html")
    return t.render({"search_url": _format_search_url(search_url)})


def research_resource_list(template_name=DEFAULT_RESOURCE_TEMPLATE, collection_id=None, tag_id=None, master_id_list="",
                           knowledgebase_type='', max=None):
    filters = _set_content_type_filter(knowledgebase_type)
    _append_tag_id_query(filters, tag_id)
    _append_master_id_list_query(filters, master_id_list)
    _append_collection_id_query(filters, collection_id)
    rows = max or 10000
    results = SolrSearch(custom_q="*", filters=filters, rows=rows, sort="title_string asc").get_results()
    if template_name != DEFAULT_RESOURCE_TEMPLATE:
        _add_places_to_results(results)
    t = get_template(template_name)
    return t.render({"results": results})


def research_collection_list(template_name=DEFAULT_RESOURCE_TEMPLATE, tag_id=None, master_id_list=""):
    filters = ["content_type:KNOWLEDGEBASE_COLLECTION"]
    _append_tag_id_query(filters, tag_id)
    _append_master_id_list_query(filters, master_id_list)
    results = SolrSearch(custom_q="*", filters=filters, sort="title_string asc").get_results()
    t = get_template(template_name)
    return t.render({"results": results})


def featured_content(template_name="ui/planning_shortcode/featured-well-standard.html", master_id=None):
    content = Content.objects.filter(master_id=master_id, publish_status="PUBLISHED").first()
    t = get_template(template_name)
    return t.render({"content": content})


def directory_roster(code=None):
    try:
        directory = Directory.objects.get(code=code) if code else None
        directory_committee_codes = () if not directory.committees else directory.committees.split(",")
        contacts = directory.get_contacts() if directory else None
        context = {"results": contacts, "directory": directory, "directory_committee_codes": directory_committee_codes}
    except Directory.DoesNotExist:
        context = {"directory": None}
    t = get_template("ui/planning_shortcode/directory-roster.html")
    return t.render(context)


def events_list(parent_id=None, master_id_list="", tag_id_list=""):
    filters = ["content_type:EVENT"]
    if parent_id:
        filters.append("parent:{0}".format(parent_id))
    if master_id_list:
        solr_ids = " ".join(["CONTENT.{0}".format(m.strip()) for m in master_id_list.split(",")])
        filters.append("id:({0})".format(solr_ids))
    if tag_id_list:
        solr_tags = " ".join(["{0}.*".format(t.strip()) for t in tag_id_list.split(",")])
        filters.append("tags_coded:({0})".format(solr_tags))
    results = SolrSearch(filters=[" AND ".join(filters)], sort="begin_time asc, title asc").get_results()
    context = dict(results=results, record_template="content/newtheme/search/record_templates/event.html")
    t = get_template("ui/planning_shortcode/events-list.html")
    return t.render(context)


def planning_mag_ad(ad_slot=None):
    context = {}
    if int(ad_slot) == 1:
        t = get_template("ui/planning_shortcode/planning-mag-ad-slot-1.html") or ""
    elif int(ad_slot) == 2:
        t = get_template("ui/planning_shortcode/planning-mag-ad-slot-2.html") or ""
    else:
        return ""
    return t.render(context)


SHORTCODES = [
    {
        "title": "Advertisements",
        "shortcode": "ADS",
        "method": advertisements,
    },

    {
        "title": "List - Blog Posts",
        "shortcode": "BLOG_LIST",
        "method": blog,
        "params": ["tag_id", "template_name", "max"]
    },
    {
        "title": "Carousel - Books",
        "shortcode": "BOOK_CAROUSEL",
        "method": book_carousel,
        "params": []
    },
    {
        "title": "Search Bar",
        "shortcode": "SEARCH_BAR",
        "method": search_bar,
        "params": ["search_url"]
    },
    {
        "title": "Research Resource List",
        "shortcode": "RESEARCH_RESOURCE_LIST",
        "method": research_resource_list,
        "params": ["template_name", "collection_id", "tag_id", "master_id_list", "knowledgebase_type", "max"]
    },
    {
        "title": "Research Collection List",
        "shortcode": "RESEARCH_COLLECTION_LIST",
        "method": research_collection_list,
        "params": ["template_name", "tag_id", "master_id_list"]
    },
    {
        "title": "Featured Content",
        "shortcode": "FEATURED_CONTENT",
        "method": featured_content,
        "params": ["template_name", "master_id"]
    },
    {
        "title": "Directory Roster",
        "shortcode": "DIRECTORY_ROSTER",
        "method": directory_roster,
        "params": ["code"]
    },
    {
        "title": "Event List",
        "shortcode": "EVENTS_LIST",
        "method": events_list,
        "params": ["parent_id", "master_id_list", "tag_id_list"]
    },
    {
        "title": "Planning Mag Ad",
        "shortcode": "PLANNING_MAG_AD",
        "method": planning_mag_ad,
        "params": ["ad_slot"]
    },
]


def route_shortcode(shortcode="", **kwargs):

    shortcode = next((sc for sc in SHORTCODES if sc.get("shortcode", None) and sc["shortcode"] == shortcode), None)

    if shortcode:
        shortcode_kwargs = dict()
        for p in shortcode.get("params", []):
            shortcode_kwargs[p] = kwargs.get(p, None)
        return shortcode.get("method")(**shortcode_kwargs)
    else:
        return None


def _format_search_url(search_url):
    if not search_url.startswith('/'):
        search_url = '/' + search_url
    if not search_url.endswith('/'):
        search_url = search_url + '/'

    return search_url


def _set_content_type_filter(knowledgebase_type):
    if knowledgebase_type == 'resources':
        return ['content_type:KNOWLEDGEBASE']
    elif knowledgebase_type == 'stories':
        return ['content_type:KNOWLEDGEBASE_STORY']
    else:
        return [
            '(content_type:KNOWLEDGEBASE OR content_type:KNOWLEDGEBASE_STORY)'
        ]


def _append_tag_id_query(filters, tag_id):
    if tag_id:
        filters.append("tags_coded:(" + tag_id.strip() + ".*)")


def _append_master_id_list_query(filters, master_id_list):
    if master_id_list:
        solr_ids = " ".join(["CONTENT.%s" % m for m in master_id_list.split(",")])
        filters.append("id:(%s)" % solr_ids)


def _append_collection_id_query(filters, collection_id):
    if collection_id:
        filters.append("related:KNOWLEDGEBASE_COLLECTION|%s" % collection_id.strip())


def _add_places_to_results(results):
    for result in results['response']['docs']:
        if not result.get('places'):
            master_id = result['id'].split('.')[-1]
            content = Content.objects.filter(master_id=master_id, publish_status='PUBLISHED').first()
            content_places = content.contentplace.all()
            places = []

            if content_places:
                for content_place in content_places:
                    place = content_place.place
                    place_descriptor_name = place.place_descriptor_name
                    if place_descriptor_name == 'state':
                        places.append(place.title)
                    else:
                        places.append('{}, {}'.format(place.title, place.state_code))

            result['places'] = sorted(places)
