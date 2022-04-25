import django
django.setup()

from events.models import Event

from _data_tools.cm_claims__2016_4 import event_credits_null_to_zero

event_credits_null_to_zero(None,False)
