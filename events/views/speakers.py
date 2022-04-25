import datetime

from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import View

from content.views import SearchView
from content.viewmixins import AppContentMixin

from myapa.viewmixins import AuthenticateMemberMixin, AuthenticateStaffMixin
from myapa.models.contact import Contact

from events.models import Event, NATIONAL_CONFERENCES
from events.forms import SpeakerSearchFilterForm


class SpeakerSearchView(AppContentMixin, SearchView):
    title = "Speaker Search"
    template_name = "events/newtheme/speakers/search.html"
    filters = ("record_type:CONTACT", "speaker_events:*")
    facets = []
    FilterFormClass = SpeakerSearchFilterForm
    

class NPCSpeakerSearchView(AuthenticateMemberMixin, SpeakerSearchView):
    """
    Speaker Database for browsing and searching speakers from past and present NPC sessions
    """
    content_url = "/events/speakers/search/"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.npc_master_ids = [str(m) for m in self.get_npc_master_ids()]

    def get_npc_master_ids(self):
        return Event.objects.filter(
            status="A", 
            publish_status="PUBLISHED", 
            code__in=[nc[0] for nc in NATIONAL_CONFERENCES]
        ).values_list("master_id", flat=True).distinct()

    def get_filters(self):
        npc_filter = "({npc_term})".format(npc_term=" OR ".join(["speaker_events:(*|ACTIVITY|*|*|{0})".format(master_id) for master_id in self.npc_master_ids]))
        return self.filters + (npc_filter,)

    def get_boosts(self):
        super_boosts = super().get_boosts()

        # adjust these to get the right balance
        speaker_boosts = [
            "if(exists(sort_time),recip(abs(ms(NOW,sort_time)),1.057e-11,1,1), 0.75)", # boosts closer dates
            "if(exists(query({!v='member_type:(MEM STU)'})), 1.1, 0.9)", # boost members
            "if(exists(query({!v='designation:(FAICP AICP)'})), 1.05, 0.95)", # boost AICP
            "if(exists(query({!v='designation:(FAICP)'})), 1.05, 0.95)", # boost FAICP even
            "if(exists(query({!v='url:*'})), 1.1, 0.9)" # boost those with profiles
        ]
        
        return super_boosts + speaker_boosts

    def get_results(self):
        results = super().get_results()
        self.process_results(results)
        return results

    def process_results(self, results):
        """returns processed search results, attributes easy to display in the template"""
        response = results.get("response", {})
        docs = response.get("docs", [])

        if self.request.user.is_authenticated():
            user_is_member = next((True for g in self.request.user.groups.all() if g.name == "member"), False)
        else:
            user_is_member = False

        for result in docs:
            speaker_events = []
            for se in result.get("speaker_events", []):
                se_list = se.split("|")
                if se_list[4] in self.npc_master_ids:
                    event_datetime = datetime.datetime.strptime(se_list[3][:19], '%Y-%m-%d %H:%M:%S')
                    event = dict(
                        id=se_list[0], event_type=se_list[1], title=se_list[2], date=event_datetime.date(), parent=se_list[4])
                    speaker_events.append(event)

            result["speaker_events"] = speaker_events

            contact_permission = result.get("contact_permission", "PRIVATE")
            result["user_has_contact_permission"] = contact_permission == "PUBLIC" or (contact_permission == "MEMBER" and user_is_member)


class NPCSpeakerAdminPublishView(AuthenticateStaffMixin, View):
    """ Updates contact's solr record if contact is a speaker for any published event
            removes contact's solr record if contact is not a speaker"""

    def get(self, request, *args, **kwargs):

        username = kwargs.get("username")
        speaker = Contact.objects.prefetch_related("contactrole__content__event__contenttagtype__tags").get(user__username=username)

        if next((True for cr in speaker.contactrole.all() if cr.role_type == "SPEAKER" and cr.publish_status == "PUBLISHED"), False):
            speaker.solr_publish()
            messages.success(request, "Updated record for {0} in the speaker database".format(speaker))
        else:
            speaker.solr_unpublish()
            messages.info(request, "Removed {0} from the speaker database (user is not a speaker for any published event)".format(speaker))

        return redirect(request.META.get('HTTP_REFERER'))
