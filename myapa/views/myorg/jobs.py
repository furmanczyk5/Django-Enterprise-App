from content.models.settings import ContentType, PublishStatus
from myapa.views.myorg.dashboard import MyOrganizationDashboardView
from store.models.purchase import Purchase
from django.utils import timezone


class OrgJobsView(MyOrganizationDashboardView):

    template_name = "myorg/jobs.html"

    def get(self, request, *args, **kwargs):
        super().set_org_roles()
        self.set_org_jobs()
        return super().get(request, *args, **kwargs)

    def set_org_jobs(self):
        now = timezone.now()
        self.jobs = self.roles.filter(
            content__content_type=ContentType.JOB.value,
            content__make_inactive_time__gt=now,
            content__publish_status=PublishStatus.PUBLISHED.value
        ).order_by(
            'content__make_inactive_time'
        )
        for job in self.jobs:
            purchase = Purchase.objects.select_related(
                "order"
            ).filter(
                content_master=job.content.master
            ).first()

            setattr(job.content, "purchase", purchase)

    def get_context_data(self, **kwargs):
        return dict(
            company=self.organization.company,
            jobs=self.jobs
        )
