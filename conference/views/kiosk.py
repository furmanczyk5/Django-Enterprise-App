import datetime
import pytz

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import F
from django.shortcuts import redirect, get_object_or_404, render
from django.utils import timezone
from django.views.generic import TemplateView, FormView

from conference.models import NationalConferenceAttendee
from content.solr_search import SolrSearch
from events.models import Event, EventMulti, NATIONAL_CONFERENCE_ADMIN, \
    NATIONAL_CONFERENCE_CURRENT
from myapa.viewmixins import AuthenticateLoginMixin
from registrations.forms import AttendeeBadgeForm
from registrations.models import Attendee
from registrations.views import SelectRegistrationOption, CustomizeBadgeView, \
    AddActivitiesView
from store.models import Purchase, Order
from store.views import CartView
from store.views.checkout_views import CheckoutView, FoundationDonationCartView


class ExtendsTemplateViewMixin(object):
    extends_template = None

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["extends_template"] = self.extends_template
        return context


class ConferenceKioskViewMixin(ExtendsTemplateViewMixin):
    """
    Mixin with useful methods and behavior common to many steps in the conference kiosk
    """

    previous_step_url = None
    is_kiosk = True

    def get_event(self):
        """
        Get the multipart event based on kwargs. This should already work for any multipart event...
            ...defaults to most recent npc
        """
        master_id = self.kwargs.get("master_id", None)
        query_kwargs = dict(publish_status="PUBLISHED")
        if master_id:
            query_kwargs["master_id"] = master_id
        else:
            query_kwargs["code"] = NATIONAL_CONFERENCE_ADMIN[0]
        return get_object_or_404(EventMulti, **query_kwargs)

    def user_has_registration(self):
        """
        We commonly check this in the kiosk to prevent user from purchasing multiple registrations
        """
        user = self.request.user
        return Attendee.objects.filter(
            contact__user__username=user.username,
            event__master_id=self.event.master,
            status="A"
        ).exists() if user else False

    def get_previous_step_url(self):
        """
        Most pages in the kiosk have a way to go back to the previous page
        """
        return self.previous_step_url

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["previous_step_url"] = self.get_previous_step_url()
        return context


class KioskHomeLoginView(ConferenceKioskViewMixin, FormView):
    """
    First step of the conference kiosk, all users need to log in first
    """
    title = "National Planning Conference 2016"
    template_name = "conference/newtheme/kiosk/home.html"
    form_class = AuthenticationForm
    extends_template = "conference/newtheme/kiosk/base.html"
    success_url = "kiosk:select_action"

    def setup(self):
        self.event = self.get_event()
        self.title = self.event.title

    def get(self, request, *args, **kwargs):
        logout(request) # should always logout user on home screen
        self.setup()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.setup()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        user = authenticate(username=username, password=password)
        if user:
            login(self.request, user)
            Purchase.cart_items(user).delete()  # remove everything from the user's cart
            return super().form_valid(form)
        else:
            # maybe more specific messaging
                # no matching record for username/email
                # password incorrect
            messages.error(self.request, "Your username and password didn't match. Please try again.")
            return super().form_invalid(form)

    def get_success_url(self, *args, **kwargs):
        success_url = self.success_url

        # skipping the select action step.
        # Reprints are not happending through the kiosk, so there is no choice to make
        if self.user_has_registration():
            success_url = "kiosk:add_activities"
        else:
            success_url = "kiosk:registration_options"
        return reverse(success_url, kwargs=dict(master_id=self.event.master_id))

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["event"] = self.event
        return context


class KioskSelectActionView(AuthenticateLoginMixin, ConferenceKioskViewMixin, TemplateView):
    """
    Prompts User to choose an action to make.
        This step only makes sense if we are giving the user the option to reprint throught the kiosk,
        ...otherwise we can determine where to send them based on whether or not they have registered

        CURRENTLY SKIPPING THIS STEP.
        NOTE: Reprints should still work through the kiosk if we decided to go back,
            but last year it worked well to leave out.

    """
    title = "Select Action"
    template_name = "conference/newtheme/kiosk/select-action.html"

    def get(self, request, *args, **kwargs):
        self.event = self.get_event()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["event"] = self.event
        context["register_url"] = reverse("kiosk:registration_options", kwargs={"master_id": self.event.master_id})
        context["activities_url"] = reverse("kiosk:add_activities", kwargs={"master_id": self.event.master_id})
        context["reprint_url"] = reverse("kiosk:reprint", kwargs={"master_id": self.event.master_id})
        return context


class KioskSelectRegistrationOptionView(ConferenceKioskViewMixin, SelectRegistrationOption):
    """
    Step where users select their registration option
        Registration gets added to the cart on submission.
    """

    template_name = "conference/newtheme/kiosk/registration-options.html"
    extends_template = "conference/newtheme/kiosk/base.html"

    def handle_already_purchased_registration(self):
        """
        Custom method to override what happens if user is already registered
        """
        messages.info(self.request, "Our records indicate that you have already purchased registration for %s. Please see an APA staff member if you have not purchased registration." % self.event.title)
        return redirect("kiosk:add_activities", master_id=self.event.master_id)

    def get_success_url(self):
        submit_button = self.request.POST.get("submit_button", "just_register")
        if submit_button == "and_add_activities":
            return reverse("kiosk:add_activities", kwargs={"master_id": self.event.master_id})
        elif submit_button == "edit_badge":
            return reverse("kiosk:edit_badge", kwargs={"master_id": self.event.master_id})
        else:
            return reverse("kiosk:cart", kwargs={"master_id": self.event.master_id})


class KioskCustomizeBadgeView(ConferenceKioskViewMixin, CustomizeBadgeView):
    """
    Users can customize their badge on this step.
        Shipping info should be left out, it makes no sense onsite...
    """
    template_name = "conference/newtheme/kiosk/registration-badge.html"
    extends_template = "conference/newtheme/kiosk/base.html"
    form_class = AttendeeBadgeForm
    confirm_badge_text = "Confirm Badge"

    def get_form_class(self):
        return self.form_class

    def get_previous_step_url(self):
        return reverse("kiosk:registration_options", kwargs={"master_id": self.event.master_id})

    def get_success_url(self):
        if self.request.POST.get("submit_button", "just_register") == "and_add_activities":
            return reverse("kiosk:add_activities", kwargs={"master_id": self.event.master_id})
        else:
            return reverse("kiosk:cart", kwargs={"master_id": self.event.master_id})


class KioskAddActivitiesView(ConferenceKioskViewMixin, AddActivitiesView):
    template_name = "conference/newtheme/kiosk/registration-activities.html"
    extends_template = "conference/newtheme/kiosk/base.html" #TO DO: used?
    cart_url = reverse_lazy("kiosk:cart")

    def get_previous_step_url(self):
        if self.user_has_registration():
            return None
        elif self.event.ticket_template:
            return reverse("kiosk:edit_badge", kwargs={"master_id": self.event.master_id})
        else:
            return reverse("kiosk:registration_options", kwargs={"master_id": self.event.master_id})

    def get_cart_url(self):
        return reverse("kiosk:cart", kwargs={"master_id": self.event.master_id})

    def filter_activities(self, activities):
        filtered_activities = []
        for a in activities:
            purchase_info = a.product_info.get("purchase_info", {})
            now = timezone.now()
            is_future = now < a.begin_time
            is_available = not (purchase_info.get("product_sale_status", "Regular") in ["Soldout", "Standby"])
            if is_future and is_available:
                filtered_activities.append(a)
        return filtered_activities


class KioskReprintView(AuthenticateLoginMixin, ConferenceKioskViewMixin, TemplateView):
    """
    View to allow users to reprint their badge and tickets.
        Currently left out of the kiosk process. Instead registrants simply ask an admin
        behind the counter that they need to reprint.
    """

    template_name = "conference/newtheme/kiosk/reprint.html"
    LIMIT_REPRINT_COUNT = 1

    def get(self, request, *args, **kwargs):
        self.event = self.get_event()
        attendee_query = NationalConferenceAttendee.objects.filter(status="A", event=self.event, contact=request.user.contact)
        self.attendee = attendee = attendee_query.first()
        if attendee and attendee.print_count < self.LIMIT_REPRINT_COUNT or attendee.ready_to_print:
            attendee_query.update(ready_to_print=True, print_count=F("print_count")+1)
            self.success=True
        else:
            self.success=False

        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["success"] = self.success
        context["attendee"] = self.attendee
        context["event"] = self.event
        return context


class KioskCartView(ConferenceKioskViewMixin, CartView):
    """
    Same as normal cart view with different template/context
    """
    template_name = "conference/newtheme/kiosk/cart.html"
    extends_template = "conference/newtheme/kiosk/base.html"
    url_namespace = "kiosk"
    checkout_source = "CONFERENCE_KIOSK"
    process_check_order_immediately = True

    def setup(self):
        super().setup()
        self.event = self.get_event()

    def allow_checks(self, **kwargs):
        """ Checks are allowed onsite """
        return True

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["event"] = self.event
        return context

    def get_order_confirmation_url(self, order_id):
        return reverse("{0}:order_confirmation".format(self.url_namespace), kwargs=dict(master_id=self.event.master_id, order_id=order_id))

    def get_checkout_url(self):
        return reverse("{0}:checkout".format(self.url_namespace), kwargs=dict(master_id=self.event.master_id))

    def get_previous_step_url(self):
        return reverse("kiosk:add_activities", kwargs={"master_id": self.event.master_id})


class KioskCheckoutView(ConferenceKioskViewMixin, CheckoutView):
    """
    Same as normal checkout view, with additional context to identify order as a kiosk order
    """
    template_name = "conference/newtheme/kiosk/checkout.html"
    extends_template = "conference/newtheme/kiosk/base.html"

    def get_context_data(self, *args, **kwargs):
        self.event = self.get_event()
        context = super().get_context_data(*args, **kwargs)
        context["USER3"] = "CONFERENCE_KIOSK"
        context["event"] = self.event
        return context

    def get_previous_step_url(self):
        # We are not able to display it though... the iframe...
        return reverse("kiosk:cart", kwargs={"master_id": self.event.master_id})


class KioskOrderConfirmation(AuthenticateLoginMixin, ConferenceKioskViewMixin, TemplateView):
    """
    Order confirmation. Final step of the kiosk
    """
    template_name = "conference/newtheme/kiosk/order-confirmation.html"

    def get(self, request, *args, **kwargs):
        order_id = kwargs.get("order_id")
        self.order = Order.objects.get(id=order_id)
        all_payments = self.order.payment_set.all()
        self.payment_method = all_payments[0].method if all_payments else "NONE"
        self.payment_amount = self.order.payment_total()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            "order": self.order,
            "payment_amount": self.payment_amount,
            "payment_method": self.payment_method,
            "event": self.get_event()
        })
        return context


class KioskFoundationDonationCartView(ConferenceKioskViewMixin, FoundationDonationCartView):

    def get_success_url(self):
        event = self.get_event()
        return reverse("kiosk:cart", kwargs=dict(master_id=event.master_id))


class TicketsAvailablePreviewView(KioskAddActivitiesView):
    template_name = "conference/newtheme/kiosk/available-tickets-screen.html"
    prompt_login = False

    def get_user(self):
        # THIS IS NASTY AND GROSS
        # Ran's ID:
        return User.objects.select_related("contact").get(username="143742")

# THIS IS SIMILAR TO THE UPNEXT SCREEN IN THE MOBILE APP
def upnext_screen(request, **kwargs):
    """
    View to display on Conference screens. Shows which activities are up next
    """

    context = dict()

    try:
        npc_event = Event.objects.get(
            code=NATIONAL_CONFERENCE_CURRENT[0],
            publish_status="PUBLISHED")
        npc = npc_event.master_id
    except:
        npc_event = None
        npc = None

    if npc_event:
        utc = pytz.timezone('UTC')
        now = utc.localize(datetime.datetime.utcnow())
        timezone_string = npc_event.timezone
        time_zone = pytz.timezone(timezone_string)
        local_time = now.astimezone(time_zone)
        utc_local_hours_diff = now.hour - local_time.hour
        # THIS DOES NOT TAKE DAYLIGHT SAVINGS INTO ACCOUNT:
        # utc_local_hours_diff = 24 - time_zone._utcoffset.seconds//3600
        UTC_LOCAL_DIFFERENCE = datetime.timedelta(hours=utc_local_hours_diff)
    else:
        UTC_LOCAL_DIFFERENCE = datetime.timedelta(hours=5)

    current_utc_time = datetime.datetime.utcnow()
    utc_15min_ago = current_utc_time - datetime.timedelta(seconds=15*60)
    utc_15min_ago_json = utc_15min_ago.strftime('%Y-%m-%dT%H:%M:%SZ')
    # chagne to local time
    context["current_time"] = current_utc_time - UTC_LOCAL_DIFFERENCE
    context["time_diff"] = UTC_LOCAL_DIFFERENCE

    first_query = 'parent:%s AND content_type:EVENT AND event_type:ACTIVITY AND begin_time:[%s TO *] AND -(tags_EVENTS_NATIONAL_TYPE:*.POSTER.*)' % (npc, utc_15min_ago_json)
    sort        = 'begin_time asc, end_time asc'
    rows        = '10'

    first_results = SolrSearch(custom_q=first_query, sort=sort, rows=rows).get_results()

    if first_results["response"]["numFound"] > int(rows):

        # another query if there are more than ten left

        first_results_docs  = first_results["response"]["docs"]
        last_begin_time     = first_results_docs[-1]["begin_time"]

        second_query = 'parent:%s AND content_type:EVENT AND event_type:ACTIVITY AND begin_time:[%s TO %s] AND -(tags_EVENTS_NATIONAL_TYPE:*.POSTER.*)' % (npc, utc_15min_ago_json, last_begin_time)
        final_results = SolrSearch(custom_q=second_query, sort=sort).get_results()
    else:

        final_results = first_results

    # QUICK HACK TO FIX TIME ZONE:
    for result in final_results["response"]["docs"]:
        begin_time_adjust = datetime.datetime.strptime(result["begin_time"], '%Y-%m-%dT%H:%M:%SZ') - UTC_LOCAL_DIFFERENCE
        result["begin_time_weekday"] = begin_time_adjust.strftime("%A")
        result["begin_time_month"] = begin_time_adjust.strftime("%B")
        result["begin_time_day"] = begin_time_adjust.day
        result["begin_time_time"] = begin_time_adjust.strftime("%I:%M %p")

    context["results"] = final_results

    upnext_template = "conference/newtheme/kiosk/upnext-screen.html"

    return render(request, upnext_template, context)

