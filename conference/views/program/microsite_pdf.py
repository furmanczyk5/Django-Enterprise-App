import json
import logging
import pdfkit
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.http import Http404, HttpResponse
from django.template.loader import render_to_string

from conference.models.microsite import Microsite

from content.forms import SearchFilterForm
from content.models import MenuItem, Content
from content.viewmixins import AppContentMixin
from events.models import Event
from content.views import SearchView
from imis.event_tickets import ACTIVE
from imis.models import CustomEventSchedule
from myapa.viewmixins import AuthenticateLoginMixin
from pages.models import LandingPage
from store.utils import PurchaseInfo

# TO DO: import ProductCart instead of Product and refactor based on new pricing logic
from store.models import Product, ProductCart
from ui.utils import get_css_path_from_less_path

from conference.views.program.microsite_search import MicrositeSearchView

class MicrositePDFExportView(MicrositeSearchView):
    has_pagination=True
    rows=75

    def get_filters(self):
        event_types = ("EVENT_SINGLE", "EVENT_MULTI", "COURSE", "ACTIVITY")
        filters = [
            "(event_type:({}))".format(" ".join(event_types)),
            "-archive_time:[* TO NOW]",
            "(parent:({}))".format(self.microsite.event_master.pk)
            ]
        return filters
