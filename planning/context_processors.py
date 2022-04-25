from django.conf import settings


def root_url(request):
    """
    Pass your root_url from the settings.py
    """
    site_url = settings.PLANNING_SERVER_ADDRESS
    if site_url.endswith('/'):
        site_url = site_url[:-1]
    return {'SITE_URL': site_url}

