# Mixins to handle access and permissions
# Define custom logic in different mixins for particular admin models

from content.models import Content
from pages.models import LandingPage
from myapa.models.proxies import Bookmark
from events.models import Event


class AppContentMixin(object):
    """Mixin to override get_queryset from Model.Admin, changed to inherit
    from object to make it more generalizable (instead of admin.ModelAdmin)

    Attributes:
        content (:obj:`content.Content`): Content model class
        content_url (str): content.models.Content.url
        content_allow_bookmark (bool): whether or not this Content can be bookmarked in MyAPA
    """
    content = None
    content_url = None
    content_allow_bookmark = False

    def set_content(self, request, *args, **kwargs):
        if self.content_url:

            # TO DO.. this duplicates code in content.views.RenderContent... should simplify and refactor
            content_generic = Content.objects.filter(
                publish_status="PUBLISHED", url=self.content_url).only("id", "published_time", "content_type", "content_area").order_by("published_time").last() # CAREFULL, don't access anything thats not in "only()"

            # second try this
            if content_generic:
                ContentModelClass = LandingPage if content_generic.content_type == "PAGE" and content_generic.content_area == "LANDING" else Content # NOTE: LATER MAKE FUNCTION TO RETURN ANY CLASS
                if content_generic.content_type == "EVENT":
                    ContentModelClass = Event
                # TO DO... could models_subclassable be used here to avoid the requery????
                self.content = ContentModelClass.objects.with_details()\
                    .select_related("parent_landing_master__content_live__landingpage__parent_landing_master__content_live__landingpage__parent_landing_master__content_live__landingpage__parent_landing_master__content_live__landingpage")\
                    .get(id=content_generic.id) # requery with correct class

    def dispatch(self, request, *args, **kwargs):
        self.set_content(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.content:
            context["title"] = getattr(self, "title", None) or self.content.title
            context["content"] = self.content
            context["parent_landing"] = self.content.get_parent_landing_page()
            context["ancestors"] = self.content.get_landing_ancestors()
            if self.content_allow_bookmark:
                context["bookmarked"] = self.request.user.is_authenticated() and Bookmark.objects.filter(contact=self.request.user.contact, content=self.content).exists()
        return context
