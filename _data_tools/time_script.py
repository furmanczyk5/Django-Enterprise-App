import django
django.setup()
from _data_tools.timezone_fixes import *
# update_claims_by_month()
# update_events_by_year()
update_claims_from_events()