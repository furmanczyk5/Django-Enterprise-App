try:
    from planning.settings.local import *
except ImportError:
    from planning.settings.base import *

try:
    configure_sentry()
except NameError:
    pass
