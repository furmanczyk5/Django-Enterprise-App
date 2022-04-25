from django.views.generic import TemplateView

from content.viewmixins import AppContentMixin
from content.models import MenuItem


class PlanningHomePageView(AppContentMixin, TemplateView):
    template_name = "content/newtheme/planning_home.html"
    content_url = "/home/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        logged_in_user = self.request.user if self.request.user.is_authenticated() else None
        context["logged_in_user"] = logged_in_user

        self.conf_menu_query = MenuItem.get_root_menu(landing_code='PLANNING_HOME')
        context["conference_menu"] = self.conf_menu_query

        return context
