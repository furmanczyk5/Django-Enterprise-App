from django.core.management.base import BaseCommand, CommandError

import requests
from sentry_sdk import capture_message


class Command(BaseCommand):
    help = """Ping Google that the sitemap for the current site has been updated.
    The built-in Django ping_google management command expects a SITE_ID value in
    settings, but who knows how adding that will probably blow up in our face? This
    sends a hardcoded https://planning.org/sitemap.xml value to Google"""

    def handle(self, *args, **options):
        try:
            requests.get(
                url="https://www.google.com/webmasters/tools/ping",
                params={'sitemap': 'https://www.planning.org/sitemap.xml'}
            )
        except Exception as e:
            capture_message(e.__str__(), level='error')
