from planning.settings.base import *

## Set your secret key here
SECRET_KEY = "`%7~KrR~K`=/=1&SChlBlwET\]g-wc3+y/c=^laqy.34JGF>]c>q9*.SK~B]Lb.Z"

# This requires that the WebUserId cookie be set.
# If it is not, the user will be logged out. 
# True for Prod / False for Dev
REQUIRE_WEBUSERID_COOKIE_FOR_ACCESS = False

INTERNAL_IPS = ["127.0.0.1"]


TEST_RUNNER = 'planning.test_runner.UseLiveDatabaseTestRunner'

INSTALLED_APPS += (
    "django_extensions",
)
###################################################################
## DATABASE CONFIGURATION
## Use this for single server (staging, or development)

## disable for staging / prod
DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'apa',
        'USER': 'planning',
        'HOST': 'localhost',
        'PORT': '5432',
    },
    'MSSQL': {
        'NAME': 'imis_live',
        'ENGINE': 'sql_server.pyodbc',
        'USER': 'django',
        'PORT': '1433',
        'OPTIONS': {
            'driver': 'FreeTDS',
            'host_is_server': True,
            'unicode_results': True,
            'extra_params': 'TDS_VERSION=7.4',
        },
        'TEST': {
            'NAME': 'imis_live',
            },
        'USE_LIVE_FOR_TESTS': True
    }
}

DATABASE_ROUTERS = ['planning.database_routers.MasterSlaveRouter']

GRAPH_MODELS = {
  'all_applications': True,
  'group_models': True,
}


PAYPAL_PARTNER = "PayPal"
PAYPAL_MODE = "TEST" # or "LIVE"
PAYPAL_USER = ""
PAYPAL_VENDOR = ""
PAYPAL_PASSWORD = ""

# can be set to "PROD", "STAGING", or "LOCAL"
ENVIRONMENT_NAME = 'LOCAL'


## Comment out for staging / prod
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

SESSION_COOKIE_DOMAIN = 'local-development.planning.org'


ALLOWED_HOSTS += ['127.0.0.1', 'testserver']

ENVIRONMENT_NAME = 'LOCAL'
