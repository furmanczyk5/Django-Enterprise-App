import django
django.setup()

from conference.cadmium_api_utils import CadmiumAPICaller
cadmium_api_caller = CadmiumAPICaller()
cadmium_api_caller.harvester_sync_all(test=False, event_key="DNWVMSSJ")
