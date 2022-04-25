from myapa.views.myorg.dashboard import MyOrganizationDashboardView


class OrgOrdersView(MyOrganizationDashboardView):

    template_name = "myorg/orders-table.html"

    def setup(self):

        self.purchases = []
        self.set_org_purchases()

    def get_context_data(self, **kwargs):
        return dict(
            company=self.organization.company,
            purchases=self.purchases
        )
