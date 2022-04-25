"""
Django settings for planning project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# SEE THIS LIST FOR DJANGO DEPLOYMENT CHECKLIST...
# https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Allow override of defaults using environment variables
dotenv_path = os.path.join(BASE_DIR, '.env')
# load_dotenv(dotenv_path)

django_debug = os.environ.get("APA_DEBUG", 'false')
DEBUG = True if django_debug.lower() == 'true' else False
# ???? TO DO... check up on the above environ setting
DEBUG = False

SITE_DIR = os.environ.get(
    "APA_SITE_DIR",
    os.path.abspath(os.path.join(BASE_DIR, '..', '..')))

LOG_DIR = os.environ.get(
    "APA_LOG_DIR",
    os.path.abspath(os.path.join(SITE_DIR, "var", "log")))

HTDOCS_DIR = os.path.abspath(os.path.join(SITE_DIR, 'htdocs'))

PACKAGE_DIR = os.path.abspath(os.path.join(SITE_DIR, 'envs','planning','lib','python3.5','site-packages'))

REQUIRE_WEBUSERID_COOKIE_FOR_ACCESS=True

# Admins will be emailed errors on prod (DEBUG=False)
ADMINS = (
)

SERVER_EMAIL = 'it@planning.org'
#SERVER_EMAIL = 'django@planning.org'

# Managers receive emails for broken links (requires referer for 404 page)
# Andy, Cindy, Ralph...
MANAGERS = ()

EMAIL_HOST = 'localhost'
EMAIL_PORT = 25

SITE_DOMAIN="https://www.planning.org"
# for the Django sites framework:
# SITE_ID = 2

# NOTE: this is included in base, not local because we publish to the staging solr from multiple environments:
SOLR_STAGING = "http://192.241.167.78:8983"


BROKER_URL = "amqp://myuser:mypassword@localhost:5672/myvhost"
CELERY_ACCEPT_CONTENT = ['json', 'pickle']
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'
# Was 'UTC'
CELERY_TIMEZONE = 'America/Chicago'
CELERY_RESULT_BACKEND = 'django-db'
CELERYBEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# users who should be notified if any transactions fail writing to the store
STORE_STAFF = ['plowe@planning.org','akrakos@planning.org','moconnor@planning.org']

# ALLOWED_HOSTS
ALLOWED_HOSTS = ['.planning.org','localhost']

# DATABASES
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'apa',
        'USER': 'apa',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}


# CSRF_COOKIE_SECURE
CSRF_COOKIE_SECURE = True

# SESSION_COOKIE_SECURE
SESSION_COOKIE_SECURE = True
# this doesn't work locally so it will have to go in the local.py of staging and prod
SESSION_COOKIE_DOMAIN = ".planning.org"

# ---------------------------------------------------------------------------------------------


# Application definition
INSTALLED_APPS = (
    "django.contrib.contenttypes",
    "grappelli.dashboard",
    "grappelli",  # admin package to make it look cool and add features like autocomplete
    'django_celery_beat',
    'django_celery_results',
    "django.contrib.admin",
    "django.contrib.admindocs",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.sites",
    "django.contrib.redirects",
    "django.contrib.humanize",
    "django.contrib.postgres",


    # raven used for Sentry issue tracking:
    # "raven.contrib.django.raven_compat",

    # wagtail apps:
    "wagtail.wagtailforms",
    "wagtail.wagtailredirects",
    "wagtail.wagtailembeds",
    "wagtail.wagtailsites",
    "wagtail.wagtailusers",
    "wagtail.wagtailsnippets",
    "wagtail.wagtaildocs",
    "wagtail.wagtailimages",
    "wagtail.wagtailsearch",
    "wagtail.wagtailadmin",
    "wagtail.wagtailcore",
    "wagtail.contrib.table_block",
    'wagtail.contrib.settings',
    "modelcluster",
    "taggit",
    "treebeard",
    "colorful",
    "hcaptcha",

    "nested_admin",
    "storages",
    "content",
    "pages",
    "publications",
    "places",
    "blog",
    "knowledgebase",
    "myapa",
    "media",
    "comments",
    "jobs",
    "conference",
    "research_inquiries",
    "store.apps.StoreAppConfig",
    "events",
    "cm",
    "consultants",
    "support",
    "directories",
    "registrations",
    "imagebank",
    "submissions",
    "uploads",
    "ui",
    "exam",
    "awards",
    "learn",
    "cron",
    "compressor",  # for compiling less
    "braces",
    "cities_light",
    "django_crontab",
    # WHERE NEEDED... maybe add to local??
    # "django_extensions",
    "reversion",
    "template_app",
    "free_students",
    "component_sites",
    "imis",
    "rest_framework",
    "rest_framework.authtoken",
    "api",
)

#  custom APA authentication back-end:
AUTHENTICATION_BACKENDS = (
    'myapa.authentication.AuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
)

MIDDLEWARE = (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.common.BrokenLinkEmailsMiddleware',
    'django.contrib.redirects.middleware.RedirectFallbackMiddleware',
    'wagtail.wagtailcore.middleware.SiteMiddleware',
    'wagtail.wagtailredirects.middleware.RedirectMiddleware',
    'planning.middleware.PlanningMiddleware',
    'component_sites.middleware.ComponentSitesMiddleware'
)

# added for grappelli
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'compressor.finders.CompressorFinder'
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR + '/template_app/templates/', PACKAGE_DIR + '/treebeard/templates/'],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.request",
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'planning.context_processors.root_url',
            ],
        },
    },
]


COMPRESS_PRECOMPILERS = (
    ('text/less', 'lessc {infile} {outfile}'),
)

ROOT_URLCONF = 'planning.urls'

WSGI_APPLICATION = 'planning.wsgi.application'

SOLR = "http://localhost:8983/solr/"

# Grappelli Custom Settings
GRAPPELLI_ADMIN_TITLE = "Planning.org Django Admin | FALL '18: PRESIDIO"
GRAPPELLI_INDEX_DASHBOARD = 'planning.admin_dashboard.CustomIndexDashboard'

# URL where requests are redirected for login when using login_required() decorator (password_change)
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/myapa/'

DEFAULT_FROM_EMAIL = 'customerservice@planning.org'

# Django Auth default redirect URL # TO DO: still used?

CITIES_LIGHT_TRANSLATION_LANGUAGES = ['en']

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

# was 'UTC'
TIME_ZONE = 'America/Chicago'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/
# STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(HTDOCS_DIR, "static")

#MEDIA_ROOT = os.path.join(BASE_DIR, "static", "_media/")
MEDIA_URL = "/static/media/"
MEDIA_ROOT = os.path.join(HTDOCS_DIR, "media")

# Additional locations of static files
STATICFILES_DIRS = [
   os.path.join(BASE_DIR, "../planning_static_uploads"),
]

AWS_S3_ACCESS_KEY_ID = ''
AWS_S3_SECRET_ACCESS_KEY = ''
AWS_STORAGE_BUCKET_NAME = 'planning-org-uploaded-media'
AWS_STATIC_STORAGE_BUCKET_NAME = 'planning-org-static-media'
AWS_QUERYSTRING_AUTH = False


# AWS_LOCATION = "static"
# STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
DEFAULT_FILE_STORAGE = 'planning.s3utils.MediaS3BotoStorage'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
STATIC_URL = "/static/"

# COMPRESS_URL = "https://%s.s3.amazonaws.com:443/" % AWS_STATIC_STORAGE_BUCKET_NAME
# COMPRESS_STORAGE = 'planning.s3utils.CachedS3BotoStorage'
COMPRESS_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
COMPRESS_CSS_HASHING_METHOD = None
COMPRESS_URL = STATIC_URL

# RAVEN_CONFIG = {
#     'dsn': 'https://793836e286fb4d7bac37ff8f61029791:4d9d4bacd22a4024b49f771792ee8954@sentry.io/190932',
#     # If you are using git, you can also automatically configure the
#     # release based on the git info.
#
#     # # NOTE: adding this below creates 502 errors on the staging/prod servers... not sure why:
#     # 'release': raven.fetch_git_sha(os.path.dirname(os.pardir)),
# }

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': True,
#     'root': {
#         'level': 'WARNING',
#         'handlers': ['sentry'],
#     },
#     'formatters': {
#         'verbose': {
#             'format': '%(levelname)s %(asctime)s %(module)s '
#                       '%(process)d %(thread)d %(message)s'
#         },
#     },
#     'handlers': {
#         'sentry': {
#             'level': 'ERROR',  # To capture more than ERROR, change to WARNING, INFO, etc.
#             'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
#             'tags': {'custom-tag': 'x'},
#         },
#         # Log Celery tasks to sentry at the DEBUG level
#         'sentry_tasks': {
#             'level': 'DEBUG',
#             'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
#             'tags': {'custom-tag': 'celery'}
#         },
#         'console': {
#             'level': 'DEBUG',
#             'class': 'logging.StreamHandler',
#             'formatter': 'verbose'
#         },
#     },
#     'loggers': {
#         # Silence SuspiciousOperation.DisallowedHost exception ('Invalid
#         # HTTP_HOST' header messages). Set the handler to 'null' so we don't
#         # get those annoying emails.
#         'django.security.DisallowedHost': {
#                 'handlers': ['console'],
#                 'level': 'CRITICAL',
#                 'propagate': False,
#             },
#         'django.db.backends': {
#             'level': 'ERROR',
#             'handlers': ['console'],
#             'propagate': False,
#         },
#         'raven': {
#             'level': 'DEBUG',
#             'handlers': ['console'],
#             'propagate': False,
#         },
#         'sentry.errors': {
#             'level': 'DEBUG',
#             'handlers': ['console'],
#             'propagate': False,
#         },
#         'store': {
#             'handlers': ['sentry'],
#             'level': 'DEBUG',
#             'propagate': True,
#         },
#         'content': {
#             'handlers': ['sentry'],
#             'level': 'DEBUG',
#             'propagate': True,
#         },
#         'events': {
#             'handlers': ['sentry_tasks'],
#             'level': 'DEBUG',
#             'propagate': True
#         },
#         'learn': {
#             'handlers': ['sentry'],
#             'level': 'DEBUG',
#             'propagate': True
#         },
#         'conference': {
#             'handlers': ['sentry'],
#             'level': 'DEBUG',
#             'propagate': True
#         },
#         'myapa': {
#             'handlers': ['sentry'],
#             'level': 'DEBUG',
#             'propagate': True
#         }
#     },
# }


# Settings for the cron job that runs to clear abondoned carts"
CART_LIFESPAN_MIN = 2

# TO DO... remove this inventory function...? Don't think we're using it...
CRONJOBS = [
    ("*/1 * * * *", "store.functions.restore_inventory_from_abandoned_carts")
]

RESTIFY_SERVER_ADDRESS = ""



SERVER_ADDRESS = "https://www.planning.org"

WKHTMLTOPDF_PATH = bytes('/usr/bin/wkhtmltopdf', 'utf-8')

PROMETRIC_USERNAME = ""
PROMETRIC_PASSWORD = ""

BLUE_TOAD_USERNAME = ""
BLUE_TOAD_PASSWORD = ""

AICP_TEAM_EMAILS = ['eroach@planning.org', 'jrolla@planning.org', 'akrakos@planning.org','plowe@planning.org','tjohnson@planning.org', 'wfrench@planning.org']
DATA_UPLOAD_MAX_NUMBER_FIELDS = 5000

# Wagtail-specific settings:
WAGTAIL_SITE_NAME = "Planning.org Website Admin"

AUTHORITATIVE_FACTOR    = 0.25
CATEGORY_FACTOR         = 0.25
LIKE_TYPE_FACTOR        = 0.25
TAG_FACTOR              = 0.25
# WAGTAILADMIN_NOTIFICATION_FROM_EMAIL = 'wagtail@myhost.io'
WAGTAILADMIN_NOTIFICATION_USE_HTML = True

WAGTAIL_FRONTEND_LOGIN_URL = '/login/'
WAGTAILIMAGES_IMAGE_MODEL = 'component_sites.ComponentImage'

HCAPTCHA_DEFAULT_CONFIG = {
    'render': 'explicit'
}
