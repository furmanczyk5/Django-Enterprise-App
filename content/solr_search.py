import requests
import json
import re

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from sentry_sdk import add_breadcrumb, capture_message


TIMEOUT = 10

# The maximum length of a keyword search, as a sanity check/denial of service safeguard
MAX_KEYWORD_LENGTH = 1000

EMPTY_RESULTS = {
    'response': {
        'numFound': 0,
        'start': 0,
        'maxScore': 0.0,
        'docs': []
    }
}

STOP_CHARS = ("'", "&", "%", ")", "(", "^", "#") # cause syntax errors ... always remove from keyword
STOP_WORDS = (" a ", " the ", " or ", " of ") # remove unless inside of quotes

Q_FIELDS = (
    #("field_name", exact_match_weight, fuzzy_match_weight, format_string)
    ("title", 8, 2),
    ("subtitle", 2.4, 1.5), # NOTE: subtitle is currently a string field in solr... should be changed to text_general
    # ("text", 2.3, 1.4),
    ("description", 2.2, 1.3),
    ("contacts", 2.1, 1.2),
    ("code", 4, 0),
    ("keywords", 4, 1.1),

    # NOTE: these are odd... they are string (case-sensative) on solr to begin with... and
    # not sure the bump is warranted
    # ("tags_TAXO_MASTERTOPIC", 0, 2, "*%s*"), # <- WHY? wildcard match makes no sense here
    # ("tags", 0, 1, "*%s*"),
    # ("tags_TAXO_MASTERTOPIC", 1.5, 1)

    ("text_search", 2, 1),
    ("id", 1, 0, "*.%s"),
    )

# NOTES FOR GROUP:
# - title from 10, 4 to 8,2
#
# words/characters to be removed from the search query:
# note the whitespace around words (to prevent removing these from the middle
# of other words):

# TO DO: consider something like this...
# class QueryTerm(object):
#     pass


class SolrSearch(object):
    """
    a helper for communicating with the solr server
    """

    def __init__(self, **kwargs):
        self.keyword = kwargs.get("keyword", "*")

        for stop_char in STOP_CHARS:
            self.keyword = self.keyword.replace(stop_char, " ")

        self.keyword_stopped = ""

        # remove all stop words from outside of quotes, and ensure an even number of quotes
        for i, keyword_term in enumerate(self.keyword.split('"')):
            if i % 2 == 0:
                my_escaped_term = keyword_term
                for stop_word in STOP_WORDS:
                    reg_compile = re.compile(re.escape(stop_word), re.IGNORECASE)
                    my_escaped_term = reg_compile.sub(" ", my_escaped_term)
                self.keyword_stopped += my_escaped_term
            else:
                self.keyword_stopped += '"%s"' % keyword_term

        self.params = {} # dictionary of the querystring params to be sent via querystring to solr
        self.params["custom_q"] = str(kwargs.get("custom_q", "")) or "" # use to override q

        try:
            self.params["rows"] = int(kwargs.get("rows", 10000))
        except (TypeError, ValueError):
            self.params["rows"] = 10000

        try:
            self.params["start"] = int(kwargs.get("start", 0))
        except (TypeError, ValueError):
            self.params["start"] = 0

        self.params["sort"] = kwargs.get("sort", "") or ""
        self.params["fl"] = kwargs.get("fl", "*,score") or "*,score" # for returning specific fields
        self.params["defType"] = "edismax"
        self.params["wt"] = "json"

        self.queries = kwargs.get("queries", [])
        self.facets = kwargs.get("facets", [])
        self.filters = kwargs.get("filters", [] )  # for filtering query (put common filters in here because these get Cached, e.g. content_type, event_type, parent relationship for multievents)
        self.boosts = kwargs.get("boosts", [])
        self.boosts.append(
            "if(exists(sort_time),recip(abs(ms(NOW,sort_time)),1.057e-11,1,1), 0.4)"
            )

        self.base_url = kwargs.get("solr_base", None) or settings.SOLR
        self.search_url = self.base_url + '/solr/planning/select/'

    @property
    def exact_match(self):
        return '"' in self.keyword

    def get_q_field(self, name, exact_priority, fuzzy_priority, format_string="%s"):
        def format_q(*args):
            return '({0}:({2}))^{1} '.format(*args)

        return_string = format_q(name, exact_priority,
            (format_string % (self.keyword_stopped if self.exact_match else '"' + self.keyword + '"' ))
            )

        if fuzzy_priority > 0 and not self.exact_match:
            return_string += format_q(name, fuzzy_priority, format_string % self.keyword_stopped)

        return return_string

    def get_q(self):
        if self.params["custom_q"] == "":
            q = ""
            for field_args in Q_FIELDS:
                q += self.get_q_field(*field_args)
            q = " AND ".join(["(" + q + ")"] + self.queries )
        else:
            q = self.params["custom_q"]

        return q.strip()

    def get_url(self, q=None):

        def get_param(name, value):
            return "&{}={}".format(name, value)

        def get_list_params(name, values):
            return "".join([get_param(name, v) for v in values])

        my_url = "{}?q={}".format(self.search_url, q or self.get_q())

        for name, value in self.params.items():
            my_url += get_param(name, value)

        if self.facets:
            my_url += get_param("facet", "true")
            my_url += get_list_params("facet.field", self.facets)

        my_url += get_list_params("fq", self.filters)

        my_url += get_list_params("boost", self.boosts)

        my_url += get_param("pf", "text_search")

        # THIS IS NASTY, but boosts future over past, see:
        # https://stackoverflow.com/questions/21315138/how-do-i-write-a-solr-functionquery-to-boost-documents-with-future-dates
        # my_url += "".join(("&timediff=ms(sort_time,NOW/HOUR)",
        #         "&future=sum($timediff,abs($timediff))",
        #         "&futureboost=recip($timediff,1,36000000,36000000)",
        #         "&pastboost=recip($timediff,1,3600000,3600000)",
        #         "&finalboost=if($future,$futureboost,$pastboost)"
        #         "&boost=$finalboost&fl=_DATE_BOOST_:$finalboost&boost=$finalboost"))

        return my_url

    def has_sql_words(self):
        """Try to prevent Russian hackers from DoS-ing/SQL injecting us. This is extremely
        simple and won't stop any determined malicious actor. We really need to configure Solr/Jetty
        better and figure out why keyword queries like )/**/UNION/**/ALL/**/SELECT/**/NULL,NULL,NULL...
        causes Solr to crash."""
        text_to_check = self._get_text_to_check()
        if 'NULL' in text_to_check:
            return True
        if 'FROM' in text_to_check and ('SELECT' in text_to_check or 'DELETE' in text_to_check):
            return True
        if 'UNION' in text_to_check and ('ALL' in text_to_check or 'SELECT' in text_to_check):
            return True
        return False

    def _get_text_to_check(self):
        text_to_check = ''
        text_to_check += self.keyword.upper()
        text_to_check += self.keyword_stopped.upper()
        for elem in self.filters:
            if isinstance(elem, str):
                text_to_check += elem.upper()
        for val in self.params.values():
            if isinstance(val, str):
                text_to_check += val.upper()
        for query in self.queries:
            if isinstance(query, str):
                text_to_check += query.upper()
        return text_to_check

    def get_results(self, q=None):
        if len(self.keyword) > MAX_KEYWORD_LENGTH:
            capture_message("Maximum keyword length exceeded: {}".format(self.keyword[:MAX_KEYWORD_LENGTH]))
            return EMPTY_RESULTS

        if self.has_sql_words():
            add_breadcrumb(
                data=dict(
                    keyword=self.keyword,
                    params=self.params
                ),
                level='warning'
            )
            capture_message('Possible SQL injection attempt detected', level='warning')
            return EMPTY_RESULTS

        my_url = self.get_url(q)
        self.results = {}

        try:
            response_obj = requests.get(my_url, timeout=TIMEOUT)
        except requests.exceptions.Timeout:
            add_breadcrumb({'q': q})
            capture_message(
                "Request to {} timed out after {} seconds".format(my_url, TIMEOUT),
                level='error'
            )
            results = EMPTY_RESULTS.copy()
            results['responseHeader'] = {'timeout': True}
            return results
        try:
            self.results = response_obj.json()
            return self.results
        except json.JSONDecodeError:
            add_breadcrumb({'q': q})
            capture_message(
                'Error response from Solr: {}'.format(getattr(response_obj, 'text', None)),
                level='warning'
            )
            return EMPTY_RESULTS


# TO DO: move this into the class above
# ALSO TO DO: move solr utils into here (like clearing results)
class SolrUpdate(object):
    """
    class for publishing searchable content to solr
    """

    headers = {'content-type': 'application/json'}

    def __init__(self, data, **kwargs):

        if not data:
            self.data = []
        elif isinstance(data, list):
            self.data = data
        else:
            self.data = data

        self.base_url = kwargs.get("solr_base", None) or settings.SOLR
        self.url = self.base_url + '/solr/planning/update/json?commit=true'

    def publish(self):

        result = requests.post(
            self.url,
            headers=self.headers,
            data=json.dumps(
                self.data,
                cls=DjangoJSONEncoder)
            )
        return result
