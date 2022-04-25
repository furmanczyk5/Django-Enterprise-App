import datetime
import json
import os

from django.conf import settings
from django.views.generic import TemplateView
from sentry_sdk import capture_exception

from content.models import Content, MessageText
from content.solr_search import SolrSearch
from media.models import Video

CACHE_DIR = os.path.join(settings.BASE_DIR, '_cache')
CACHE_VALID_TIME = 60 * 30
DT_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


def make_cached_filename(component_name):
    return '{}__{}.json'.format(component_name, datetime.datetime.strftime(datetime.datetime.utcnow(), DT_FORMAT))


def get_cached_file_time(filename):
    if not isinstance(filename, str):
        return
    parts = filename.split('__')
    if len(parts) != 2:
        return
    dt = parts[1][:-5]
    try:
        return datetime.datetime.strptime(dt, DT_FORMAT)
    except (TypeError, ValueError):
        pass


def cache_valid(filename):
    cache_time = get_cached_file_time(filename)
    if cache_time is None:
        return False
    try:
        delta = (datetime.datetime.utcnow() - cache_time).seconds
    except AttributeError:
        return False
    return delta < CACHE_VALID_TIME


def write_cached_file(filename, data):
    full_path = os.path.join(CACHE_DIR, filename)
    with open(full_path, 'w') as outfile:
        json.dump(data, outfile)
    return full_path


def get_or_create_cache_file(component_name):
    existing_file = next((x for x in os.listdir(CACHE_DIR) if x.split('__')[0] == component_name), None)
    if existing_file is None:
        return make_cached_filename(component_name), True
    elif not cache_valid(existing_file):
        os.unlink(os.path.join(CACHE_DIR, existing_file))
        return make_cached_filename(component_name), True
    else:
        with open(os.path.join(CACHE_DIR, existing_file)) as cached_file:
            return json.load(cached_file), False


class HomePageView(TemplateView):
    template_name = "content/newtheme/home.html"
    most_shared = None
    upcoming_events = None
    learn_courses = None
    blogs = None
    blogs_news = None
    featured_video = None
    most_popular = None
    content = None

    def get(self, request, *args, **kwargs):

        self.content = Content.objects.filter(
            publish_status="PUBLISHED", code="ROOT"
        ).select_related(
            "featured_image__content_live__media"
        ).first()

        self.get_upcoming_events()
        self.get_learn_courses()
        self.get_blogs()
        self.get_blogs_news()
        self.get_most_popular()
        self.get_most_shared()
        self.get_featured_video()
        MessageText.add_message(request, "HOME_ALERT")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["content"] = self.content
        context["upcoming_events"] = self.upcoming_events
        context["learn_courses"] = self.learn_courses

        context["blogs"] = self.blogs
        context["blogs_news"] = self.blogs_news
        context["most_popular"] = self.most_popular
        context["most_shared"] = self.most_shared
        context["featured_video"] = self.featured_video
        context["home"] = True
        return context

    def get_upcoming_events(self, *args, **kwargs):
        component_name = 'upcoming_events'
        cache, created = get_or_create_cache_file(component_name)
        if not created:
            self.upcoming_events = cache
        else:
            try:
                datetime_now_json = datetime.datetime.strftime(datetime.datetime.utcnow(), DT_FORMAT)
                data = SolrSearch(
                    q="*",
                    filters=[
                        "(event_type:EVENT_MULTI OR event_type:EVENT_SINGLE) AND is_apa:true AND begin_time:[{0} TO *]".format(datetime_now_json)
                    ],
                    sort="begin_time asc",
                    rows=5
                ).get_results()
                self.upcoming_events = data
                write_cached_file(make_cached_filename(component_name), data)
            except Exception as exc:
                capture_exception(exc)

    def get_learn_courses(self, *args, **kwargs):
        # datetime_now_json = datetime.datetime.strftime(datetime.datetime.utcnow(), DT_FORMAT)

        # self.learn_courses = SolrSearch(q="*", filters=["(event_type:LEARN_COURSE OR event_type:LEARN_COURSE_BUNDLE) AND begin_time:[{0} TO *]".format(datetime_now_json)], sort="begin_time asc", rows=5).get_results()
        component_name = 'learn_courses'
        cache, created = get_or_create_cache_file(component_name)
        if not created:
            self.learn_courses = cache
        else:
            data = SolrSearch(
                q="*",
                filters=["(event_type:LEARN_COURSE OR event_type:LEARN_COURSE_BUNDLE)"],
                sort="updated_time desc",
                rows=5
            ).get_results()
            self.learn_courses = data
            write_cached_file(make_cached_filename(component_name), data)

        for course in self.learn_courses['response']['docs']:
            tags = []
            if 'tags_SEARCH_TOPIC' in course:
                for tag in course['tags_SEARCH_TOPIC']:
                    tags.append(tag.split('.')[-1])
            course['search_topics'] = tags
            # or condensed
            # course['search_topics']=[tag.split('.')[-1] for tag in course['tags_SEARCH_TOPIC']] if 'tags_SEARCH_TOPIC' in course else []

    def get_blogs(self, *args, **kwargs):
        component_name = 'blogs'
        cache, created = get_or_create_cache_file(component_name)
        if not created:
            self.blogs = cache
        else:
            try:
                data = SolrSearch(
                    q="*",
                    filters=[
                        "content_type:BLOG AND -tags_BLOG_CATEGORY:*.APA_NEWS.*"
                    ],
                    sort="sort_time desc",
                    rows=5
                ).get_results()
                self.blogs = data
                write_cached_file(make_cached_filename(component_name), data)
            except Exception as exc:
                capture_exception(exc)

    def get_blogs_news(self, *args, **kwargs):
        component_name = 'blogs_news'
        cache, created = get_or_create_cache_file(component_name)
        if not created:
            self.blogs_news = cache
        else:
            try:
                data = SolrSearch(
                    q="*",
                    filters=[
                        "content_type:BLOG AND tags_BLOG_CATEGORY:*.APA_NEWS.*"
                    ],
                    sort="sort_time desc",
                    rows=5
                ).get_results()
                self.blogs_news = data
                write_cached_file(make_cached_filename(component_name), data)
            except Exception as exc:
                capture_exception(exc)

    def get_most_popular(self, *args, **kwargs):
        component_name = 'most_popular'
        cache, created = get_or_create_cache_file(component_name)
        if not created:
            self.most_popular = cache
        else:
            try:
                data = SolrSearch(
                    q="*",
                    filters=[
                        "tags_CONTENT_FEATURED:*.MOST_POPULAR.*"
                    ],
                    rows=5
                ).get_results()
                self.most_popular = data
                write_cached_file(make_cached_filename(component_name), data)
            except Exception as exc:
                capture_exception(exc)

    def get_most_shared(self, *args, **kwargs):
        component_name = 'most_shared'
        cache, created = get_or_create_cache_file(component_name)
        if not created:
            self.most_shared = cache
        else:
            try:
                data = SolrSearch(
                    q="*",
                    filters=[
                        "tags_CONTENT_FEATURED:*.MOST_SHARED.*"
                    ],
                    rows=5
                ).get_results()
                self.most_shared = data
                write_cached_file(make_cached_filename(component_name), data)
            except Exception as exc:
                capture_exception(exc)

    def get_featured_video(self, *args, **kwargs):
        self.featured_video = Video.objects.filter(
            contenttagtype__tags__code="HOMEPAGE_VIDEO",
            publish_status="PUBLISHED"
        ).first()
