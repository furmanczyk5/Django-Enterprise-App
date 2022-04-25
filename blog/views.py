from content.viewmixins import AppContentMixin
from content.views import SearchView, LandingSearchView

from .forms import BlogSearchFilterForm


class BlogSearchView(AppContentMixin, SearchView):
    content_url = "/blog/"
    title = "Blogs"
    filters = ["content_type:BLOG", "-tags_BLOG_CATEGORY:*.APA_NEWS.*"]
    template_name = "content/newtheme/search/results-blog.html"
    facets = ["tags_SEARCH_TOPIC"]
    facets_include_unmatched_tags = True
    facets_include_unmatched_tag_types = True
    FilterFormClass = BlogSearchFilterForm


class APANewsSearchView(LandingSearchView):
    content_url = "/apanews/"
    title = "Search APA News"
    filters = ["content_type:BLOG AND tags_BLOG_CATEGORY:*.APA_NEWS.*"]
    facets = ["tags_BLOG_CATEGORY", "tags_SEARCH_TOPIC", "tags_COMMUNITY_TYPE",
              "tags_JURISDICTION"]
    FilterFormClass = BlogSearchFilterForm
