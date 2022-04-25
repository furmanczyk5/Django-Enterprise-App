from datetime import timedelta

from django.utils import timezone

from jobs.models import Job
from pages.models import LandingPage
from planning.global_test_case import GlobalTestCase


class JobTestCase(GlobalTestCase):

    def setUp(self):
        # We're assuming a default Jobs LandingPage with master id 9022686 always exists
        self.page, created = LandingPage.objects.get_or_create(
            title="Jobs Page"
        )
        if not created:
            self.page = self.page.publish()
            self.page.solr_publish()

    def tearDown(self):
        self.page.solr_unpublish()

    def test_make_inactive_time(self):
        # setup
        job, j = Job.objects.get_or_create(
            title="Test Job",
            publish_status="DRAFT",
            parent_landing_master_id=self.page.master_id
        )

        # Intern
        job.make_inactive_time = None
        job.job_type = "INTERN"
        job.status = "A"
        in_four_weeks = timezone.now() + timedelta(days=28)
        job.publish()
        self.assertEqual(job.make_inactive_time.date(), in_four_weeks.date())

        # Entry Level
        job.make_inactive_time = None
        job.job_type = "ENTRY_LEVEL"
        job.status = "A"
        in_four_weeks = timezone.now() + timedelta(days=28)
        job.publish()
        self.assertEqual(job.make_inactive_time.date(), in_four_weeks.date())

        # Pro 2 weeks
        job.make_inactive_time = None
        job.job_type = "PROFESSIONAL_2_WEEKS"
        job.status = "A"
        in_two_weeks = timezone.now() + timedelta(days=14)
        job.publish()
        self.assertEqual(job.make_inactive_time.date(), in_two_weeks.date())

        # Pro 4 weeks
        job.make_inactive_time = None
        job.job_type = "PROFESSIONAL_4_WEEKS"
        job.status = "A"
        in_four_weeks = timezone.now() + timedelta(days=28)
        job.publish()
        self.assertEqual(job.make_inactive_time.date(), in_four_weeks.date())

