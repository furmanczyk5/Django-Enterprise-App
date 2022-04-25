import datetime

from django.contrib import messages
from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import redirect
from django.views.generic import TemplateView

from conference.models import Microsite
from conference.models.settings import JOIN_WAITLIST_URL
from content.models import MenuItem
from events.models import EventMulti, NATIONAL_CONFERENCES
from imis.event_function import EventFunctions
from imis.models import CustomEventRegistration
from myapa.viewmixins import AuthenticateLoginMixin
from store.models import Purchase
from store.utils import PurchaseInfo


class AddActivitiesView(AuthenticateLoginMixin, TemplateView):
    """
    View for adding tickets for multi event activities to cart

    STILL NEED TO:
        - filter activities (client side) -- by something other than day?
        - what happens if registration is not in cart? -- I believe this is handled now
    """
    template_name = "registrations/newtheme/registration-activities.html"
    cart_url = reverse_lazy("store:cart")
    is_kiosk = False
    microsite = None
    conf_menu_query = None
    has_registration = False
    user = None
    event = None
    is_npc = False
    activities = []

    def get_event(self):
        master_id = self.kwargs.get("master_id")
        return EventMulti.objects.get(master_id=master_id, publish_status="PUBLISHED")

    def get_user(self):
        return self.request.user

    def get(self, request, *args, **kwargs):

        self.event = self.get_event()
        self.user = self.get_user()
        self.is_npc = self.event.code in [nc[0] for nc in NATIONAL_CONFERENCES]
        if self.is_npc and not self.is_kiosk:
            self.template_name = "registrations/conference/registration-activities.html"
        master_id = self.event.master_id

        registration = CustomEventRegistration.objects.filter(
            id=self.user.username,
            meeting=self.event.product.imis_code
        )



        # registration = Purchase.objects.filter(
        #     user=self.user,
        #     product__content__master_id=master_id
        # )
        # using the Q(user=self.user) | Q(contact__user__username=self.user.username)
        # as the query for Purchases for the logged-in user was a huge performance bottleneck
        # To mitigate, we run the first query for user foreign key on Purchase,
        # trying again on the Contact foreign key as a second query only if the first one
        # returns no results.
        # if not registration.exists():
        #     registration = Purchase.objects.filter(
        #         contact__user__username=self.user.username,
        #         product__content__master_id=master_id
        #     )

        self.has_registration = registration.exists()
        self.set_microsite(request, *args, **kwargs)

        # REDIRECT TO
        if self.has_registration:
            badge_only_purchase = Purchase.objects.filter(user=self.user, product=self.event.product, code='BSPKR')
            if badge_only_purchase.exists():
                return redirect(self.get_cart_url())

        # REDIRECT TO SELECT REGISTRATION IF DOES NOT HAVE REGISTRATION
        if not self.has_registration:
            messages.info(
                request,
                "To purchase additional tickets you must first register for %s" % self.event.title
            )
            if self.is_kiosk:
                return redirect("kiosk:registration_options", master_id=self.event.master_id)
            else:
                if self.microsite.url_path_stem and self.microsite.url_path_stem != "conference":
                    rev_url = reverse(
                        "registrations:microsite_select_registration",
                        kwargs={
                            "master_id": master_id,
                            "microsite_url_path_stem": self.microsite.url_path_stem
                        }
                    )
                    return redirect(rev_url)
                else:
                    return redirect("registrations:select_registration", master_id=master_id)
#  SEND TO CART IF BADGE-ONLY
        elif badge_only_purchase:
            return redirect(self.get_cart_url())

        activities = self.event.get_activities_with_product_cart()
        functions = EventFunctions(self.user.username, self.event.product.imis_code).get()

        purchases = Purchase.objects.filter(user=self.request.user, product__content__master_id=master_id)

        for activity in activities:
            add_product_info(activity, self.user, purchases, functions)

        self.activities = self.filter_activities(activities)

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.set_microsite(request, *args, **kwargs)
        return super().post(request, *args, **kwargs)

    def filter_activities(self, activities):
        return activities

    def get_filter_dates(self):
        # SHOULD MOVE ALL THESE FILTERS TO A FORM?
        filter_dates = []
        begin_time_as_date = self.event.begin_time_astimezone().date()
        end_time_as_date = self.event.end_time_astimezone().date()
        date_difference = end_time_as_date - begin_time_as_date

        for i in range(date_difference.days + 1):
            filter_dates.append(begin_time_as_date + datetime.timedelta(days=i))

        return filter_dates

    def get_cart_url(self):
        return self.cart_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event"] = self.event
        context["activities"] = self.activities
        context["filter_dates"] = self.get_filter_dates()
        context["has_registration"] = self.has_registration
        context["is_npc"] = self.is_npc
        context["cart_url"] = self.get_cart_url()
        context["conference_menu"] = self.conf_menu_query
        context["microsite"] = self.microsite
        context["join_waitlist_url"] = JOIN_WAITLIST_URL
        context["is_waitlist"] = False
        context["is_ordered"] = False
        # FLAGGED FOR REFACTORING: NPC21
        # context["show_schedule_stuff"] = False
        return context

    def set_microsite(self, request, *args, **kwargs):
        microsite = Microsite.get_microsite(self.request.get_full_path())

        if microsite:
            # means we are in a conf microsite (not incl npc)
            self.conf_menu_query = MenuItem.get_root_menu(landing_code=microsite.home_page_code)
            self.microsite = microsite
        else:
            self.conf_menu_query = None


def add_product_info(activity, user, registration=[], functions=[]):
    product = activity.product
    price = None

    function = next(
        filter(
          lambda function: function.event_function_id == product.imis_code,
          functions),
        None)

    if activity.product_cart:
        price = activity.product_cart.get_price(
            contact=user.contact,
            purchases=registration)

    purchase_info = PurchaseInfo(product, user, function).get() if price else {}

    activity.product_info = {
        'product': product,
        'price': price,
        'purchase_info': purchase_info,
        'content': product.content
    }

    return activity
