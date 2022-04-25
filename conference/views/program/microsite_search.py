import json

import pdfkit
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.http import Http404, HttpResponse
from django.template.loader import render_to_string
from sentry_sdk import capture_exception, capture_message

from conference.forms.program import ConferenceSearchFilterForm
from conference.models.microsite import Microsite
from content.models import MenuItem, Tag
from content.viewmixins import AppContentMixin
from content.views import SearchView
from events.models import Event
from imis.event_tickets import ACTIVE
from imis.models import CustomEventSchedule
from myapa.models.contact import Contact
from myapa.viewmixins import AuthenticateLoginMixin
from pages.models import Page
from store.models import ProductCart
from ui.utils import get_css_path_from_less_path


class MicrositeSearchView(AuthenticateLoginMixin, AppContentMixin, SearchView):
    """
    Search view for Microsites. This will search all content that has a
    parent of the Microsite.

    For conference program-specific searching, use MicrositeConferenceSearchView.

    Attributes:
        content_url (str): url to use in :meth:`content.viewmixins.AppContentMixin.set_content`
        template_name (str): template to use
        visible_tagtype_codes (list): for PDF searching
        FilterFormClass (:obj:`django.forms.Form`): Form class to use
        has_pagination (bool): whether or not to paginate the search results
        rows (int): Number of results to fetch per page if paginating
        sort (str): Comma-separated string of sort columns to use
        prompt_login (bool): whether or not this view requires a user to be logged in to function
        show_content_type (bool): Whether or not to show the type of content in the search result,
            passed in as a keyword argument to template context
    """

    FilterFormClass = ConferenceSearchFilterForm
    content_url = "/conference/search/"
    template_name = "conference/newtheme/program/search-general.html"
    visible_tagtype_codes = ["NPC_TOPIC", "DIVISION", "NPC_TRACK_2016", "EVENTS_NATIONAL_TYPE"]
    has_pagination = True
    rows = 50
    sort = "begin_time asc, end_time asc, title_string asc"

    return_type = "html"
    prompt_login = False
    show_content_type = False

    def dispatch(self, request, *args, **kwargs):
        self.microsite = Microsite.get_microsite(request.get_full_path())
        if not self.microsite:
            raise Http404('Microsite not found')
        self.title = "{} Program".format(self.microsite.short_title)
        self.pdf_filename = "{}-program.pdf".format(self.microsite.short_title)
        if self.microsite.url_path_stem and self.microsite.url_path_stem != 'conference':
            self.content_url = "/conference/{}/search/".format(self.microsite.url_path_stem)
        self.conference_menu = MenuItem.get_root_menu(
            landing_code=self.microsite.home_page_code
        )
        # TODO: Implement a caching mechanism
        self.page_ids = find_children(self.microsite.home_page, [])
        return super().dispatch(request, *args, **kwargs)

    def setup(self, request, *args, **kwargs):
        self.return_type = kwargs.get('return_type', 'html')
        if self.return_type in ['pdf','pdf-inline']:
            self.rows=1000
        # so we know which activities are already scheduled
        if self.is_authenticated:
            username = self.request.user.username
            # this is where we pull user scheduled sessions
            self.scheduled = get_scheduled_events(self.microsite.event_master, username)
            scheduled_ids = get_master_ids_for_scheduled_events(self.scheduled)
            self.scheduled_solr_ids = ['CONTENT.' + str(i) for i in scheduled_ids]
        return super().setup(request, *args, **kwargs)

    def get_queries(self, ignore_facets=False, *args, **kwargs):
        query = super().get_queries(*args, **kwargs)

        # THIS IS A LITTLE MORE COMPLEX THAN THE OTHER FILTERS, STILL COULD THIS BE MOVED TO THE FORM USING A SPECIAL WIDGET?
        # Filter results by tags that are passed
        tags = self.filter_form.cleaned_data.get("tags", "")
        tag_code_list = []
        tag_code_dict = {}
        if tags:
            tag_query_list = tags.split(",")

            for idx, tag_code in enumerate(tag_query_list):
                query.append("tags_coded:(*.%s.*)" % tag_code.strip())
                tag_code_list.extend(tag_code.split(".* *."))

                # now a list of AND TERMS eg. [[TAG_1],[TAG_2,TAG_3],[TAG_4]]
                tag_query_list[idx] = tag_code.split(".* *.")

            for tag in Tag.objects.filter(code__in=tag_code_list):
                tag_code_dict[tag.code] = tag.title

            self.tag_lists = tag_query_list
            self.tag_dict = tag_code_dict

        dynamic_tag_code_list = []
        for filter_field in self.filter_form.filter_field_list:
            dynamic_tag_code = self.filter_form.cleaned_data.get(filter_field.label, "")
            if dynamic_tag_code:
                dynamic_tag_code_list.append(dynamic_tag_code)

        other_tag_code_list = [
                          self.filter_form.cleaned_data.get("topics", ""),
                          self.filter_form.cleaned_data.get("tracks", ""),
                          self.filter_form.cleaned_data.get("activity_types", ""),
                          self.filter_form.cleaned_data.get("divisions", ""),
                      ] + dynamic_tag_code_list
        other_tags = ",".join([s for s in other_tag_code_list if s != ""])
        print(other_tag_code_list)

        if other_tags:
            for tag_code in other_tags.split(","):
                query.append("tags_coded:(*.%s.*)" % tag_code.strip())

        self.tag_descriptions = [
            t for t in Tag.objects.filter(
                code__in=tag_code_list + other_tag_code_list
            ).values(
                "title", "description"
            ) if t["description"] and t["description"].strip()
        ]

        # filter by speakers
        speaker_filter_id = self.filter_form.cleaned_data.get("speakers", "").strip()
        if speaker_filter_id:
            query.append("contact_roles_SPEAKER:(%s|*)" % speaker_filter_id)
            speaker = Contact.objects.filter(id=speaker_filter_id).first()
            if speaker is not None:
                self.speaker = {"username": speaker_filter_id, "title": speaker.title}
            else:
                capture_message(
                    "No Contact record found for speaker id {}".format(speaker_filter_id)
                )
        return query

    def get_filters(self):
        content_types = ('PAGE', 'RFP', 'KNOWLEDGEBASE_COLLECTION', 'IMAGE', "PUBLICATION", "BLOG", "JOB")
        event_types = ("EVENT_SINGLE", "EVENT_MULTI", "COURSE", "ACTIVITY")
        filters = [
            "(content_type:({}) OR event_type:({}))".format(
                " ".join(content_types),
                " ".join(event_types)
            ),
            "-archive_time:[* TO NOW]",
            "(parent:({}) OR id:({}))".format(
                self.microsite.event_master.pk,
                " ".join(self.page_ids)
            )
        ]

        return filters

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.microsite.event_master.content_live.event
        context.update({
            "event": event,
            "tag_lists": getattr(self, "tag_lists", None),
            "tag_dict": getattr(self, "tag_dict", None),
            "speaker": getattr(self, "speaker", None),
            "scheduled_solr_ids": getattr(self, "scheduled_solr_ids", []),
            "is_authenticated": self.is_authenticated,
            "tag_descriptions": getattr(self, "tag_descriptions", []),
            "title": event.title,
            "microsite": getattr(self, "microsite", None),
            "conf_menu_query": getattr(self, "conf_menu_query", None),
            "search_url": self.microsite.search_url,
            "show_session_filter_form": True,
            "conference_menu": self.conference_menu,
            # FLAGGED FOR REFACTORING: NPC21
            "show_schedule_stuff": False,
        })

        return context

    def render_to_response(self, context, **response_kwargs):
        if self.return_type == "json":
            # Used primarily for the mobile app

            # remove unnecessary data from response
            del context["view"]
            del context["filter_form"]
            del context["event"]
            del context["microsite"]

            return HttpResponse(json.dumps(context, cls=DjangoJSONEncoder), content_type='application/json')

        elif self.return_type == "pdf" or self.return_type == "pdf-inline":

            # Used for the printed pdf program
            the_css = get_css_path_from_less_path(["/static/content/css/newtheme_style.css",
                                                   "/static/content/css/search-pdf.less"
                                                ])

            context["request"] = self.request # TO DO... remove
            the_html = render_to_string("conference/newtheme/program/search-pdf.html", context)
            the_options = {
                "page-size": "Letter",
                "margin-top": "0.5in",
                "margin-right": "0.5in",
                "margin-bottom": "0.5in",
                "margin-left": "0.5in",
                "footer-font-size": "8",
                "footer-left": "APA",
                "footer-center": self.title,
                "footer-right": "Page [page]",
            }

            config = pdfkit.configuration(wkhtmltopdf=settings.WKHTMLTOPDF_PATH)
            the_pdf = pdfkit.from_string(the_html, False, css=the_css, options=the_options, configuration=config)

            response = HttpResponse(the_pdf, content_type='application/pdf')
            disposition = "inline" if self.return_type == "pdf-inline" else "attachment"
            response['Content-Disposition'] = '%s; filename="%s"' % (disposition, self.pdf_filename)
            return response

        else:
            # Regular html response
            return super().render_to_response(context, **response_kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["conference"] = self.microsite.event_master.content_live.event
        return kwargs


def get_scheduled_events(parent_event, username):
    if not hasattr(parent_event.content_live, 'product'):
        return []
    meeting = parent_event.content_live.product.imis_code
    return CustomEventSchedule.objects.filter(
        id=username,
        meeting=meeting,
        status=ACTIVE
    )


def get_master_ids_for_scheduled_events(scheduled_events, product_codes=None):

    if not product_codes and scheduled_events:
        product_codes = [se.product_code for se in scheduled_events]

    # product_codes = [se.product_code.replace(
    #     '_SBY', '') for se in scheduled_events]
    master_ids = []

    try:
        products = ProductCart.objects.filter(
            publish_status="PUBLISHED",
            imis_code__in=product_codes
        ).select_related("content")

        events_with_products_codes = [p.imis_code for p in products]

        events = Event.objects.filter(
            publish_status="PUBLISHED",
            code__in=product_codes
        ).exclude(code__in=events_with_products_codes
        ).values("master_id")

        for product in products:
            master_ids.append(product.content.master_id)

        for event in events:
            master_ids.append(event["master_id"])

    except Exception as e:
        capture_exception(e)
        pass

    return master_ids


class MicrositePDFExportView(MicrositeSearchView):
    has_pagination=False
    rows=9999999


def find_children(root, page_ids):
    """
    Recursive function to find all ids (in our Solr format) of all child landing pages
    starting from `root`.
    :param root: :class:`pages.models.LandingPageMasterContent`
    :param page_ids: list, to contain page ids
    :return: list
    """
    children = Page.objects.filter(
        parent_landing_master=root,
        publish_status="PUBLISHED",
        status='A'
    ).exclude(
        url__contains="/app/"  # old mobile app pages still showing up
    )
    page_ids.extend([x.solr_id for x in children])
    for child in children:
        find_children(child.master, page_ids)
    return page_ids

