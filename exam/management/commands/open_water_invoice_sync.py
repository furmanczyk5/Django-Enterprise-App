from django.core.management.base import BaseCommand
from django.utils import timezone

from exam.open_water_api_utils import OpenWaterAPICaller
from planning.settings import ENVIRONMENT_NAME



class Command(BaseCommand):
    help = """Pulls all Open Water invoices from 'window' hours ago until now
    and writes them to iMIS"""

    def add_arguments(self, parser):
        parser.add_argument(
            '-w',
            '--window',
            help='The size of the time window in hours back from now from which to pull invoices.',
            type=float,
            default=0.5,
            dest='window'
        )

    def handle(self, *args, **options):
        print("START OF HANDLER")
        window = options.get('window')
        window = float(window) if window else 0.5
        print("WINDOW IS ", window)

        if ENVIRONMENT_NAME != "PROD":
            ow = OpenWaterAPICaller(instance="test_instance")
        else:
            ow = OpenWaterAPICaller(instance="aicp_instance")

        now = timezone.now()
        self.stdout.write(
            self.style.NOTICE("START INVOICE PULL: {}".format(now))
        )
        # PUT BACK AFTER TESTING
        ow.pull_open_water_invoices(window_in_hours=window)
        now = timezone.now()
        self.stdout.write(
            self.style.NOTICE("INVOICE PULL ENDED: {}".format(now))
        )

