import math

from django.contrib import messages
from django.views.generic import TemplateView

from content.forms import SearchFilterForm
from content.models import Tag, TagType
from content.solr_search import SolrSearch
from content.viewmixins import AppContentMixin


class SearchViewFacetTagsMixin(object):

    facets = []
    facets_include_unmatched_tags = False
    facets_include_unmatched_tag_types = False
    call_out_results = []
    # TO DO: this is nasty and confusing... and not clear which logic belongs here vs in the
    # SolrSearch class...
    def get_queries(self, *args, **kwargs):

        query_list = []
        tag_id_list = []
        tag_id_dict = {}
        selected_tag_ids = self.request.GET.getlist("tags")

        if self.facets and selected_tag_ids:

            for idx, tag_id in enumerate(selected_tag_ids):
                query_list.append("tags_coded:("+tag_id.strip()+".*)")
                try:
                    tag_id_int = int(tag_id.split('.* '))
                    tag_id_list.extend(tag_id_int)
                except:
                    pass # failing quietly here so that we don't get error logging from hits from bots that tend to pass invalid tag strings through the querystring  params

                selected_tag_ids[idx] = tag_id.split('.* ') # now a list of AND TERMS eg. [[TAG_1],[TAG_2,TAG_3],[TAG_4]]

            for tag in Tag.objects.filter(id__in=tag_id_list):
                tag_id_dict[str(tag.id)] = tag.title

        self.tag_list = tag_id_list
        self.tag_dict = tag_id_dict
        self.search_tag_ids = [item for sublist in selected_tag_ids for item in sublist]

        return query_list

    def get_facets(self):
        if self.facets:
            return ["tag_types"] + self.facets # need tag_type for the counts
        else:
            return self.facets

    def get_display_facets(self, solr_results):

        # MUST DO THIS HERE OR THIS LIST WILL KEEP GROWING
        call_out_results = []
        facet_results = []
        remaining_facets = self.get_facets().copy() # so that tagtypes are not duplocated when their names change, rethink this later
        if self.facets and solr_results.get('facet_counts'):
            for i in range(0, len(solr_results["facet_counts"]["facet_fields"]["tag_types"]), 2):
                tag_type_count = solr_results["facet_counts"]["facet_fields"]["tag_types"][i+1]
                tag_type_tuple = tuple(solr_results["facet_counts"]["facet_fields"]["tag_types"][i].split("."))

                if (self.facets_include_unmatched_tag_types or tag_type_count > 0) and len(tag_type_tuple) == 3:
                    tag_type_id, tag_type_code, tag_type_title = tag_type_tuple

                    if "tags_" + tag_type_code in remaining_facets:
                        # this removes duplicate
                        remaining_facets.remove("tags_" + tag_type_code)
                        facet_result = {
                            "title":tag_type_title,
                            "code":tag_type_code,
                            "id":tag_type_id,
                            "count":tag_type_count,
                            "tags":[]
                        }
                        facet_tags_list = solr_results["facet_counts"]["facet_fields"]["tags_" + tag_type_code]

                        for j in range(0, len(facet_tags_list), 2):
                            tag_count = facet_tags_list[j+1]
                            tag_tuple = tuple(facet_tags_list[j].split("."))

                            if (self.facets_include_unmatched_tags or tag_count > 0) and len(tag_tuple) >= 3:
                                tag_id, tag_code, tag_title = tag_tuple
                                tag_result = {
                                    "title":tag_title,
                                    "code":tag_code,
                                    "id":tag_id,
                                    "count":tag_count,
                                    "selected": (self.search_tag_ids and tag_id in self.search_tag_ids)
                                }
                                facet_result["tags"].append(tag_result)

                                if tag_code == 'FORMAT_APA_LEARN':
                                    self.call_out_results.append(tag_result)

                        facet_result["tags"] = sorted(facet_result["tags"], key=lambda k: k["title"])
                        facet_results.append(facet_result)

            # This allows arbitrary order controllable by sort number in Django:
            # but only for the tagtype ids in the main_search_page_ids set
            sort_numbers = self.get_facet_sort_order()
            current_filter_ids = set([d["id"] for d in facet_results])
            main_search_page_ids = set(['29','10','28','27'])

            try:
                if current_filter_ids.issubset(main_search_page_ids):
                    facet_results = sorted(facet_results, key=lambda k: sort_numbers[k["id"]])
                else:
                    # alphabetical by title for everything else
                    facet_results = sorted(facet_results, key=lambda k: k["title"])
            except:
                pass

        return facet_results

    def get_facet_sort_order(self):
        tts = TagType.objects.all()
        if tts:
            return {str(tt.id): tt.sort_number for tt in tts}
        else:
            return None

    def get_facet_context(self, *args, **kwargs):
        return {
            "facet_results": self.get_display_facets(self.facet_results),
            "tag_list": self.tag_list,
            "tag_dict": self.tag_dict,
            "selected_tag_count": len(self.tag_list) if self.tag_list else 0
        }


class SearchView(SearchViewFacetTagsMixin, TemplateView):
    title = "Search"
    template_name = "content/newtheme/search/results.html"
    record_template = "content/newtheme/search/record_templates/generic.html"
    solr_search = None  # to be set to an instance of SolrSearch

    FilterFormClass = SearchFilterForm
    filter_form = None
    facets = [] # TO DO.... no lists here!
    filters = [] # TO DO... no lists here!

    return_type = "html" #default unless passed in querystring (not implemented, conference program does custom implementation...)
    has_pagination = True
    show_content_type = True
    rows = 50
    sort = None
    start = 0

    def get(self, request, *args, **kwargs):

        self.setup(request, *args, **kwargs)

        self.request.session["last_search"] = request.get_full_path()

        if self.has_pagination:
            try:
                self.page_1 = int(request.GET.get("page", 1))
            except (TypeError, ValueError):
                self.page_1 = 1
            self.page   = self.page_1 - 1
            self.start  = self.page * self.rows

        self.keyword = request.GET.get("keyword", None) or "*"

        self.solr_search = SolrSearch(
            keyword=self.keyword,
            facets=self.get_facets(),
            filters=self.get_filters(),
            boosts=self.get_boosts(),
            queries=self.get_queries(),
            fl=None,  # TO DO: rename to fields?
            start=self.start,
            rows=self.rows,
            sort=self.get_sort(),
            )

        self.results = self.solr_search.get_results()

        # sets a separate results for facet, since this result set should ignore
        # the facet search itself
        self.facet_results = SolrSearch(
            keyword=self.keyword,
            filters=self.get_filters(),
            facets=self.get_facets(),
            boosts=self.get_boosts(),
            queries=self.get_queries(ignore_facets=True),
            fl=None, # TO DO: rename to fields?
        ).get_results()

        return super().get(request, *args, **kwargs)

    def setup(self, request, *args, **kwargs):
        # hook for additional setup
        pass

    def get_form_kwargs(self):
        return {}

    def get_queries(self, ignore_facets=False, *args, **kwargs):
        """
        Returns additional queries to be included in solr's q paramater (if needed beyond standard queries)
        """
        if self.FilterFormClass:
            self.filter_form = self.FilterFormClass(self.request.GET, **self.get_form_kwargs())
            self.filter_form.is_valid()
            query_list = self.filter_form.to_query_list()
        else:
            query_list = []

        if ignore_facets:
            return query_list
        else:
            return query_list + super().get_queries(*args, **kwargs)

    def get_filters(self):
        """
        Returns the list of filter statements (like "content_type:EVENT")
        NOTE: these filtered results get cached so use for common filters e.g. content_type, event_type, conference
        """
        from events.models import NATIONAL_CONFERENCE_MASTER_ID
        # TO DO: do we want to include media videos/audio here?
        content_types = ('PAGE', 'RFP', 'KNOWLEDGEBASE_COLLECTION', 'IMAGE', "PUBLICATION", "BLOG")
        event_types = ("EVENT_SINGLE", "EVENT_MULTI", "COURSE", "LEARN_COURSE", "LEARN_COURSE_BUNDLE")
        return self.filters or [
            '(content_type:(%s) OR event_type:(%s) OR parent:%s OR '
            '(content_type:JOB AND contact_roles_PROVIDER:"99562|American Planning Association"))'
                    % (" ".join(content_types), " ".join(event_types), NATIONAL_CONFERENCE_MASTER_ID),
            "-archive_time:[* TO NOW]",
            ]

    def get_boosts(self):
        """returns a list of multiplier boost statements"""
        return []

    def get_sort(self):
        return self.sort or self.filter_form.get_sort() if self.filter_form else None

    def get_pagination(self, **kwargs):
        """
        returns pagination and other display-able information about the search
        """

        page_range = 4

        if "response" not in self.results:
            # TO DO... better support these characeters in search, then update this msg
            messages.error(self.request, "Your search could not be completed. Please avoid special characters such as apostropes, quotes, and ampersands.")
            return {"pages": []}
        else:

            numFound = self.results["response"]["numFound"]

            # pagination_logic
            pagination                      = {"pages":[]}
            pagination["start"]             = self.start + 1
            pagination["end"]               = min(self.start + self.rows, numFound)
            pagination["total"]             = numFound
            pagination["page"]              = self.page_1
            pagination["first_page"]        = max(self.page_1 - page_range, 1)
            pagination["last_page"]         = min(self.page_1 + page_range, math.ceil(numFound/self.rows) )
            pagination["more_before_first"] = self.page_1 - page_range > 1
            pagination["more_after_last"]   = math.ceil(numFound/self.rows) > self.page_1 + page_range
            pagination["keyword"]           = self.keyword if self.keyword != "*" else None

            for i in range(pagination["first_page"],pagination["last_page"]+1,1):
                pagination["pages"].append(i)

            return pagination

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context.update(self.get_facet_context()) # from facet mixin

        context["call_out_results"] = self.call_out_results
        context["keyword"] = self.keyword
        context["title"] = self.title
        context["filter_form"] = self.filter_form
        context["results"] = self.results
        context["record_template"] = self.record_template
        context["show_content_type"] = self.show_content_type
        context["tags"] = self.search_tag_ids

        if self.has_pagination:
            context["pagination"] = self.get_pagination(**kwargs)

        return context


class GeneralSearch(SearchView):
    """ the global general search for planning.org """
    facets = ["tags_FORMAT", "tags_SEARCH_TOPIC", "tags_COMMUNITY_TYPE", "tags_JURISDICTION", "tags_ADDRESS_STATE"]

    def get_boosts(self):
        # this line means that we will ALWAYS favor later dates
        return [
        # TO DO re above: CHANGED FROM 0.75 to 0.4 for final value here in order to weight older events lower... BUT NEED TO CONFIRM THIS!!!

        "if(exists(query({!v='content_area:LANDING'})), 1.25, 0.9)",
        "if(exists(query({!v='content_type:KNOWLEDGEBASE_COLLECTION'})), 1.25, 0.9)",
        "if(exists(query({!v='content_type:EVENT'})), 0.2, 1)",
        "if(exists(query({!v='content_type:IMAGE'})), 0.2, 1)",
        ]

    def get_filters(self):
        """ exclude things that have site defined and are not are not planning.org"""
        filters = super().get_filters() + ["(-site:[* TO *] AND *:*) OR site:planning.org"]
        return filters


class LandingSearchView(AppContentMixin, SearchView):
    """
    For searches on landing/overview and similar pages that show a search form below landing page or other content.
    This can be the standard view to inherit from for most "specialized" search views.
    """
    content_url = None  # would be overridden in base class (AppContentMixin) with specific url
    record_template = "content/newtheme/search/record_templates/generic.html"
    template_name = "content/newtheme/search/results-landing.html"
    hide_content = False

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        # hide the content if the user
        if self.hide_content or "page" in self.request.GET or "keyword" in self.request.GET:
            context["hide_content"] = True
        return context
