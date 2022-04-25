from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from exam.open_water_api_utils import OpenWaterAPICaller


class Command(BaseCommand):
    help = """Overnight pull of current AICP process status from Open Water into MyAPA"""

    def handle(self, *args, **options):
        print("START OF OPEN WATER MYAPA SYNC HANDLER")
        now = timezone.now()
        self.stdout.write(
            self.style.NOTICE("Started Open Water MyAPA Sync at: {}".format(now))
        )
        if settings.ENVIRONMENT_NAME != "PROD":
            open_water_test = OpenWaterAPICaller(instance="test_instance")
            open_water_test.sync_open_water_to_myapa()
        else:
            open_water_aicp = OpenWaterAPICaller(instance="aicp_instance")
            open_water_aicp.sync_open_water_to_myapa()
        now = timezone.now()
        self.stdout.write(
            self.style.NOTICE("Finished Open Water MyAPA Sync at: {}".format(now))
        )
