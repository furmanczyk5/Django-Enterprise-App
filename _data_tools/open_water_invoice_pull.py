import django
django.setup()
import time
from django.utils import timezone
from exam.open_water_api_utils import OpenWaterAPICaller
from planning.settings import ENVIRONMENT_NAME

def open_water_manual_invoice_pull():
    if ENVIRONMENT_NAME != "PROD":
        ow = OpenWaterAPICaller(instance="test_instance")
    else:
        ow = OpenWaterAPICaller(instance="aicp_instance")

    while True:
        now = timezone.now()
        print("WAKING UP TO START INVOICE PULL: ", now)
        ow.pull_open_water_invoices(window_in_hours=.5)
        now = timezone.now()
        print("INVOICE PULL ENDED AT: ", now)
        time.sleep(900)
owmip=open_water_manual_invoice_pull
