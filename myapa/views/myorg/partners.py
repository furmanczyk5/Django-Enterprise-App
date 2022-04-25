from copy import copy

from cm.models.providers import Provider
from myapa.views.myorg.dashboard import MyOrganizationDashboardView


class OrgPartnersView(MyOrganizationDashboardView):

    template_name = "myorg/partners-table.html"
    partners = None

    def setup(self):
        self.provider = copy(self.organization)
        self.provider.__class__ = Provider
        self.partners = []
        self.set_org_partners()

    def get_context_data(self, **kwargs):
        return dict(
            company=self.organization.company,
            partners=self.partners
        )
