from django.db.models import Q
from functools import reduce
from sentry_sdk import capture_exception

from conference.views.program.microsite_search import MicrositeSearchView
from conference.forms.program import ConferenceSearchFilterForm
from content.models import Tag
from imis.models import CustomEventSchedule
from myapa.models.contact import Contact
from store.models import ProductOption


class MicrositeConferenceSearchView(MicrositeSearchView):
    """Search view for a microsite's conference sessions and acitivties.

    Restricts the Solr query to only Event and Activities
    """

    template_name = "conference/newtheme/program/search.html"
    FilterFormClass = ConferenceSearchFilterForm

    def get_queries(self, *args, **kwargs):
        query = super().get_queries(*args, **kwargs)

        # THIS IS A LITTLE MORE COMPLEX THAN THE OTHER FILTERS, STILL COULD THIS BE MOVED TO THE FORM USING A SPECIAL WIDGET?
        # Filter results by tags that are passed
        tags = self.filter_form.cleaned_data.get("tags","")
        tag_code_list = []
        tag_code_dict = {}
        if tags:
            tag_query_list = tags.split(",")

            for idx, tag_code in enumerate(tag_query_list):
                query.append("tags_coded:(*.%s.*)" % tag_code.strip() )
                tag_code_list.extend(tag_code.split(".* *."))
                tag_query_list[idx] = tag_code.split(".* *.") # now a list of AND TERMS eg. [[TAG_1],[TAG_2,TAG_3],[TAG_4]]

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

        if other_tags:
            for tag_code in other_tags.split(","):
                query.append("tags_coded:(*.%s.*)" % tag_code.strip() )

        self.tag_descriptions = [t for t in Tag.objects.filter(code__in=tag_code_list+other_tag_code_list).values("title", "description") if t["description"] and t["description"].strip()]

        #filter by speakers
        speaker_filter_id = self.filter_form.cleaned_data.get("speakers", "").strip()
        if speaker_filter_id:
            query.append("contact_roles_SPEAKER:(%s|*)" % speaker_filter_id)
            try:
                speaker_filter_title = Contact.objects.get(id=speaker_filter_id).title
                self.speaker = {"username":speaker_filter_id, "title":speaker_filter_title}

            except:pass
        return query

    def get_filters(self):
        """Create Solr filters that restrict the content and event types appropriately

        Returns:
             dict
        """
        return ["content_type:EVENT", "event_type:ACTIVITY", "parent:{}".format(
            self.microsite.event_master.pk
        )]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["conference"] = self.microsite.event_master.content_live.event
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_session_filter_form"] = True
        # FLAGGED FOR REFACTORING: NPC21
        # context["title"] = "Full Program"
        context["title"] = "Program"
        context['is_registered'] = self.is_registered()
        return context

    def is_registered(self):
        try:
            event = self.microsite.event_master.content_live.event
            meeting = event.product.imis_code
            product_options = ProductOption.objects.filter(
                product=event.product).exclude(code='M004')  # To remove Badge Only

            query = reduce(
                lambda x, y: x | y,
                [Q(product_code=meeting + '/' + option.code)
                    for option in product_options])
            query.add(Q(id=self.request.user.username), Q.AND)
            query.add(Q(status='A'), Q.AND)

            return bool(CustomEventSchedule.objects.filter(query))
        except Exception as e:
            capture_exception(e)
            return False
