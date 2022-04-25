import django
django.setup()

from cm.models import Claim

from _data_tools.cm_claims__2016_4 import claim_credits_null_to_zero

claim_credits_null_to_zero(None,False)
