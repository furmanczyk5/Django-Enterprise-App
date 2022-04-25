import django
django.setup()

from cm.credly_api_utils import CredlyAPICaller

cr=CredlyAPICaller()
# TO RUN FULL MASS CREDLY SYNC: (must be called on None explicitly)
cr.credly_mass_sync(None)
