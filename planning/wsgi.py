"""
WSGI config for planning project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

try:
    import newrelic.agent
    newrelic.agent.initialize('/srv/sites/apa/etc/newrelic.ini')
except Exception as e:
    print("Newrelic not configured: {}".format(str(e)))


import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "planning.settings")

application = get_wsgi_application()
