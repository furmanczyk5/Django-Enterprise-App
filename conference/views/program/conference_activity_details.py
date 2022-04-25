from django.conf import settings

from conference.models.settings import JOIN_WAITLIST_URL
from content.models import ContentTagType, Tag, TagType
from content.views import RenderContent
from myapa.viewmixins import AuthenticateLoginMixin
from registrations.models import Attendee


class ConferenceActivityDetailsView(AuthenticateLoginMixin, RenderContent):
    """
    Render Content View for National Conference activities
    """
    prompt_login = False

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        tag_types = self.content.contenttagtype.all()

        # TO DO... this adds unnecessary extra queries:
        contenttagtype_transit = tag_types.filter(
            tag_type__code="TRANSIT").first()
        contenttagtype_room = tag_types.filter(
            tag_type__code="ROOM").first()
        contenttagtype_type = tag_types.filter(
            tag_type__code="EVENTS_NATIONAL_TYPE").first()

        if contenttagtype_type:
            context["activity_type"] = contenttagtype_type.tags.first()

        context["is_authenticated"] = self.is_authenticated
        context["product"] = self.content.get_product()

        context["is_apa_learn_product"] = (
                self.content.digital_product_url is not None and
                self.content.digital_product_url != 'https://learn.planning.org/catalog/' and
                (
                    settings.LEARN_DOMAIN in self.content.digital_product_url
                    or "learn.planning.org" in self.content.digital_product_url
                ))

        if self.request.user.is_authenticated():

            context["attendee"] = Attendee.objects.filter(
                contact=self.request.contact,
                event__master=self.content.master).first()
            # this is the attendee record for the individual activity
            # (for adding/removing to schedule)
            context["event_attendee"] = Attendee.objects.filter(
                contact=self.request.contact,
                event__master=self.content.parent).first()
            # this is the attendee record for the overall event

        context["has_downloads"] = ((self.content.resource_url and
                                     context.get("event_attendee", None)) or
                                    self.content.digital_product_url)

        if contenttagtype_transit:
            context["mobile_workshop_codes"] = [
                t.code
                for t in contenttagtype_transit.tags.all()
            ]

        if contenttagtype_room:
            context["room"] = next(
                (t.title for t in contenttagtype_room.tags.all()),
                None)

        # Add local/inclusive text/links if event has those tags
        local_tag = Tag.objects.get(code="LOCAL")
        # inclusiveness_tag = Tag.objects.get(code="INCLUSIVENESS")
        interactive_tag = Tag.objects.get(code="INTERACTIVE")
        recorded_tag = Tag.objects.get(code="RECORDED_SESSION")
        context["is_local"] = False
        # context["is_inclusive"] = False
        context["is_interactive"] = False
        context["is_recorded"] = False
        npc_category_tag_type = TagType.objects.get(code='NPC_CATEGORY')
        npc_ctt = ContentTagType.objects.filter(
            tag_type=npc_category_tag_type,
            content=self.content).first()
        if npc_ctt:
            npc_cat_tags = npc_ctt.tags.all()
            if local_tag in npc_cat_tags:
                context["is_local"] = True
            # if inclusiveness_tag in npc_cat_tags:
            #     context["is_inclusive"] = True
            if interactive_tag in npc_cat_tags:
                context["is_interactive"] = True
            if recorded_tag in npc_cat_tags:
                context["is_recorded"] = True

        context["join_waitlist_url"] = JOIN_WAITLIST_URL
        return context
