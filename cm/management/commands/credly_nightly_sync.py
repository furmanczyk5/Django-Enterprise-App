from django.core.management.base import BaseCommand
from django.utils import timezone

from cm.credly_api_utils import CredlyAPICaller


class Command(BaseCommand):
    help = """Pushes all members with a changed designation in iMIS to Credly"""

    def handle(self, *args, **options):
        print("START OF CREDLY HANDLER")
        now = timezone.now()
        self.stdout.write(
            self.style.NOTICE("Started Credly Sync at: {}".format(now))
        )
        credly_api_caller = CredlyAPICaller()
        credly_api_caller.credly_nightly_sync()
        now = timezone.now()
        self.stdout.write(
            self.style.NOTICE("Finished Credly Sync at: {}".format(now))
        )
