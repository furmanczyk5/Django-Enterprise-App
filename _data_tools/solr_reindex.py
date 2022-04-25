
from content.models import Content
from content.solr_search import SolrUpdate
from events.models import Event, EventMulti, Course, NATIONAL_CONFERENCES
from pages.models import Page, LandingPage
from jobs.models import Job
from blog.models import BlogPost
from imagebank.models import Image as ImageBankImage
from media.models import Media
from publications.models import Publication
from knowledgebase.models import Resource, Collection
# from component_sites.models import Page as WagtailPage, NewsPage
from component_sites.models import NewsPage
from component_sites.wagtail_hooks import WagtailSolrPublish

def scrub_dict(d):
    if type(d) is dict:
        return dict((k, scrub_dict(v)) for k, v in d.items() if v and scrub_dict(v))
    elif type(d) is list:
        return [scrub_dict(v) for v in d if v and scrub_dict(v)]
    else:
        return d

def reindex_all(with_delete=False):
    """
    reindex standard content types, in order of priority with optional deletion prior
    """
    if with_delete:
        reindex(delete_kwargs={"query":"*"}, exclude_kwargs={"master__id__gt":0})

    reindex_landing_pages()
    reindex_jobs()
    reindex_nationalconferenceactivities()
    reindex_pages()
    reindex_blog()
    reindex_imagebank()
    reindex_publications()
    reindex_knowledgebase_collections()
    # reindex_media() ... necessary?
    reindex_cm_events()



def reindex_cm_events():
    """
    For reindexing all events excluding activities
    """
    # delete all events with {"content_type":"EVENT", "event_type":"EVENT_SINGLE EVENT_MULTI COURSE"}
    delete_query_kwargs = {"delete":{"query":"content_type:EVENT AND event_type:(EVENT_SINGLE EVENT_MULTI COURSE)"}}
    SolrUpdate(delete_query_kwargs).publish()

    base_query = Event.objects.filter(publish_status="PUBLISHED", status="A", event_type__in=["EVENT_SINGLE", "EVENT_MULTI", "COURSE"])
    all_years = [x.year for x in base_query.datetimes("begin_time", "year")]
    all_years.sort(reverse=True)
    all_years += [None]

    optimized_query = base_query.select_related("master").prefetch_related("permission_groups", "tag_types", "contactrole", "contactrole__contact", "contenttagtype__tag_type", "contenttagtype__tags")

    GROUP_SIZE = 100

    for year in all_years:

        if year is not None:
            total_for_year = base_query.filter(begin_time__year=year).count()
            year_query = optimized_query.filter(begin_time__year=year)
        else:
            total_for_year = base_query.filter(begin_time__isnull=True).count()
            year_query = optimized_query.filter(begin_time__isnull=True)
            year = "None"

        print("starting publishing for year {0}, ({1} total)".format(year,total_for_year))

        total_count = 0
        group_count = 0
        pub_data = []

        for event in year_query:

            pub_data.append(event.solr_format())
            group_count += 1
            total_count += 1

            if group_count >= GROUP_SIZE or total_count >= total_for_year:
                scrubbed_pub_data = scrub_dict(pub_data)
                solr_response = SolrUpdate(scrubbed_pub_data).publish()

                if solr_response.status_code == 200:
                    group_count = 0
                    pub_data = []
                    print("published {0} of {1} for year {2}".format(total_count, total_for_year, year))
                else:
                    raise ValueError("Publish to solr failed")

    print("Flawless Victory")


def reindex(ContentClass=Content, delete_kwargs=None, exclude_kwargs={}, **filter_kwargs):
    """
    Performs solr reindex for all published records that match query combination of ContentClass and filter_kwargs
    e.g. for conference activities in 2016 ... reindex(ContentClass=NationalConferenceActivity, delete_kwargs={"query":"content_type:EVENT AND event_type:ACTIVITY AND parent:9000321"), parent__content_live__code="EVENT_16CONF" )
    """
    GROUP_SIZE = 100

    print("starting solr reindex")

    if delete_kwargs:
        print("Removing old solr results matching passed delete_kwargs:")
        print(delete_kwargs)
        delete_query_kwargs = {"delete":delete_kwargs}
        SolrUpdate(delete_query_kwargs).publish()

    base_query = ContentClass.objects.filter(publish_status="PUBLISHED", status="A", **filter_kwargs).exclude(**exclude_kwargs)
    optimized_query = base_query.select_related("master").prefetch_related("permission_groups", "tag_types", "contactrole", "contactrole__contact", "contenttagtype__tag_type", "contenttagtype__tags")
    total_records = base_query.count()

    total_count = 0
    group_count = 0
    pub_data = []

    print("starting publishing for {0} total records".format(total_records))

    for record in optimized_query:
        pub_data

        pub_data.append(record.solr_format())
        group_count += 1
        total_count += 1

        if group_count >= GROUP_SIZE or total_count >= total_records:
            scrubbed_pub_data = scrub_dict(pub_data)

            solr_response = SolrUpdate(scrubbed_pub_data).publish()

            if solr_response.status_code == 200:
                group_count = 0
                pub_data = []
                print("published {0} of {1}".format(total_count, total_records))
            else:
                raise ValueError("Publish to solr failed")

    print("Flawless Victory")


# IMPORTANT NOTE: For below methods, should have at least one methods for every ContentClass that has a unique solr_format() - solr_publish() method combination

def reindex_pages():
    """Publish all pages to solr (minus landing pages)"""
    reindex(
        ContentClass=Page,
        delete_kwargs={"query":"content_type:PAGE AND -content_area:LANDING"},
        exclude_kwargs={"content_area":"LANDING"}
    )

def reindex_landing_pages():
    """
    Publish all landing pages to solr
    NOTE: Not a unique combination but these would hold priority over other pages to be published first
    """
    reindex(
        ContentClass=LandingPage,
        delete_kwargs={"query":"content_type:PAGE AND content_area:LANDING"}
    )

def reindex_jobs():
    """Publish all jobs to solr"""
    reindex(
        ContentClass=Job,
        delete_kwargs={"query":"content_type:JOB"},
    )

def reindex_blog():
    """Publish all blogs to solr"""
    reindex(
        ContentClass=BlogPost,
        delete_kwargs={"query":"content_type:BLOG"}
    )

def reindex_imagebank():
    """Publish all imagebank images to solr"""
    reindex(
        ContentClass=ImageBankImage,
        delete_kwargs={"query":"content_type:IMAGE"}
    )

def reindex_media():
    """Publish all media to solr (minus images because we don't want to publish those at all)"""
    reindex(
        ContentClass=Media,
        delete_kwargs={"query":"content_type:MEDIA"},
        exclude_kwargs={"media_format":"IMAGE"}
    )

def reindex_nationalconferenceactivities():
    """
    Publish all National Conference Activities to solr
    Necessary because these are not included in the cm_events reindex
    """
    conferences = EventMulti.objects.filter(code__in=[conf[0] for conf in NATIONAL_CONFERENCES], publish_status="PUBLISHED")
    conference_parent_terms = ["parent:%s" % c.master_id for c in conferences]
    conference_parent_query = " ".join(conference_parent_terms)

    reindex(
        ContentClass=NationalConferenceActivity,
        delete_kwargs={"query":"content_type:EVENT AND event_type:ACTIVITY AND %s" % conference_parent_query}
    )

def reindex_publications():
    """
    Pubish all publications (Other than books) to solr
    """
    reindex(
        ContentClass=Publication,
        delete_kwargs={"query":"content_type:PUBLICATION AND -resource_type:BOOK"}
    )

def reindex_knowledgebase_collections():
    """
    Publish all knowledgebase resources to solr
    """
    reindex(
        ContentClass=Collection,
        delete_kwargs={"query":"content_type:KNOWLEDGEBASE_COLLECTION"}
    )

## OTHER
def reindex_courses():
    """
    Publish all Courses to solr
    Note: Already included in the reindex_cm_events() function,
        but if you only want to publish courses...
    """
    reindex(
        ContentClass=Course,
        delete_kwargs={"query":"content_type:EVENT AND event_type:COURSE"}
    )

# should be no longer needed since we want these REMOVED from search...
def reindex_knowledgebase_resources():
    """
    Publish all knowledgebase resources to solr
    """
    reindex(
        ContentClass=Resource,
        delete_kwargs={"query":"content_type:KNOWLEDGEBASE"}
    )


# IDEA: For any of the above, if these start to take too long to publish because the number of results, here are a couple of things to try:
    # 1. break up by end id digits, ****1, ****2, ****3, etc.
    # 2. prefetch_related on data used in solr_format()

# should be no longer needed since we want these REMOVED from search...
def reindex_events():
    """
    Publish all EVENTS to solr
    """
    reindex(
        ContentClass=Event,
        delete_kwargs={"query":"content_type:EVENT"}
    )


def reindex_wagtail(environment='staging', Class=NewsPage,
    delete_kwargs={"query":"record_type:WAGTAIL_PAGE"}, exclude_kwargs={}, **filter_kwargs):
    """
    delete Wagtail pages and republish to solr
    """
    GROUP_SIZE = 100

    print("starting wagtail solr reindex")

    if delete_kwargs:
        print("Removing old solr results matching passed delete_kwargs:")
        print(delete_kwargs)
        delete_query_kwargs = {"delete":delete_kwargs}
        SolrUpdate(delete_query_kwargs).publish()

    base_query = Class.objects.filter(**filter_kwargs).exclude(**exclude_kwargs)
    optimized_query = base_query
    total_records = base_query.count()

    total_count = 0
    group_count = 0
    pub_data = []

    print("starting publishing for {0} total records".format(total_records))

    for record in optimized_query:

        request = environment
        publish_object = WagtailSolrPublish(record, request)

        pub_data
        pub_data.append(publish_object.solr_format())

        group_count += 1
        total_count += 1

        if group_count >= GROUP_SIZE or total_count >= total_records:
            scrubbed_pub_data = scrub_dict(pub_data)

            solr_response = SolrUpdate(scrubbed_pub_data).publish()

            if solr_response.status_code == 200:
                group_count = 0
                pub_data = []
                print("published {0} of {1}".format(total_count, total_records))
            else:
                raise ValueError("Publish to solr failed")

    print("Flawless Victory")


def reindex_wagtail_news_pages(environment):
    """remove deleted news pages from solr"""
    reindex_wagtail(
        Class=NewsPage,
        environment=environment,
        delete_kwargs={"query":"record_type:WAGTAIL_PAGE AND content_type:newspage"},
    )






