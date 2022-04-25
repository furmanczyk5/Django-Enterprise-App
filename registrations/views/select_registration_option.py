from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect
from django.views.generic import FormView

from conference.models import Microsite
from content.models import MenuItem
from events.models import Event, EventMulti, NATIONAL_CONFERENCES
from imis import models as imis_models
from myapa.permissions.utils import update_user_groups
from myapa.viewmixins import AuthenticateLoginMixin
from store.models import Purchase, ProductCart
from ..forms import RegistrationOptionForm

FORM_EXCLUDES = (
    'race', 'hispanic_origin', 'gender',
    'gender_other', 'ai_an', 'asian_pacific',
    'other', 'span_hisp_latino')
# Can this view be even simpler by inheriting from a different View Class
class SelectRegistrationOption(AuthenticateLoginMixin, FormView):
    """
    View for registering for an event

    STILL NEED TO:
        - redirect for get_success_url
        - no option to add activities if event multi has no activities to add?
    """

    # TODO: Add "nonmember" and "webuser" to this list when registration opens for all
    # Currently scheduled for 2019-01-09
    # authenticate_groups = [
    #     "cldr",
    #     "member",
    #     "speaker",
    #     "staff",
    # ]
    # authenticate_groups_message_code = "NOT_APA_MEMBER"

    form_class = RegistrationOptionForm
    template_name = "registrations/newtheme/registration-options.html"
    is_kiosk = False
    microsite = None
    conf_menu_query = None

    def dispatch(self, request, *args, **kwargs):
        # An email was sent to VIPs with the normal (cancelled) NPC20 registration URL, instead of the
        # digital NPC20 microsite URL.
        # The powers that be determined this to be preferable to sending a correction email.
        master_id = kwargs.get('master_id')
        npc20home_master_id = '9198677'
        path = self.request.get_full_path()
        if master_id == npc20home_master_id and '/digital/' not in path:
            path = path.replace('/registrations/', '/registrations/digital/')
            return redirect(path)
        return super().dispatch(request, *args, **kwargs)


    def get_event(self):
        self.master_id = self.kwargs.get("master_id")
        event = Event.objects.filter(master_id=self.master_id, publish_status="PUBLISHED").first()
        if event is None:
            raise Http404("Event not found")
        return event

    def setup(self):
        self.event = self.get_event()
        self.is_npc = self.event.code in [nc[0] for nc in NATIONAL_CONFERENCES]
        self.product = ProductCart.objects.get(id=self.event.product.id)
        self.user = self.request.user
        update_user_groups(self.user)
        self.code = self.request.GET.get("code", None)

    def get(self, request, *args, **kwargs):

        self.setup()
        self.set_microsite(request, *args, **kwargs)

        contact_previous_order_lines = self.request.contact.get_imis_order_lines()

        self.already_purchased_registration = False
        
        if contact_previous_order_lines is not None:
            self.already_purchased_registration = next(
                (True for ol in contact_previous_order_lines 
                    if ol.PRODUCT_CODE[:len(self.product.imis_code)]==self.product.imis_code), 
                False
                )

        if self.already_purchased_registration: 
            return self.handle_already_purchased_registration()

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.setup()
        self.set_microsite(request, *args, **kwargs)
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()

        try:
            # if there is an existing purchase for this event in the cart
            purchase = Purchase.objects.get(
                Q(contact__user__username=self.user.username) | Q(user=self.user),
                product=self.product, order__isnull=True
            )
        except:
            purchase = None

        form_kwargs.update(
            {"product": self.product, "user": self.user, "event": self.event, "instance": purchase, "code": self.code})

        return form_kwargs

    def form_valid(self, form):
        if form.is_valid():
            form.save()
            self.post_data_to_imis(form)
            self.after_save(form)

            return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event"] = self.event
        context["product"] = self.product
        context["user"] = self.user
        context["code"] = self.code
        context["conference_menu"] = self.conf_menu_query
        context["microsite"] = self.microsite
        context["form_excludes"] = FORM_EXCLUDES
        if self.event and self.event.event_type == 'EVENT_MULTI':
            event_multi = EventMulti.objects.get(id=self.event.id)
            context["has_ticketed_activities"] = event_multi.has_ticketed_activities()

        return context

    def get_success_url(self):
        submit_action = self.request.POST.get("submit_button", "just_register")
        if submit_action == "edit_badge":
            if self.microsite.url_path_stem and self.microsite.url_path_stem != "conference":
                return reverse("registrations:microsite_edit_badge",
                               kwargs={
                                   "master_id": self.event.master_id,
                                   "microsite_url_path_stem": self.microsite.url_path_stem})
            else:
                return reverse("registrations:edit_badge", kwargs={"master_id": self.event.master_id})
        elif submit_action == "and_add_activities":
            if self.microsite.url_path_stem and self.microsite.url_path_stem != "conference":
                return reverse("registrations:microsite_add_activities",
                               kwargs={
                                   "master_id": self.event.master_id,
                                   "microsite_url_path_stem": self.microsite.url_path_stem})
            else:
                return reverse("registrations:add_activities", kwargs={"master_id": self.event.master_id})
        else:
            return reverse("store:cart")

    def handle_already_purchased_registration(self):
        """
        Custom method to override what happens if user is already registered
        """
        return self.render_to_response({
            "already_purchased_registration": self.already_purchased_registration,
            "event": self.event,
            "microsite": self.microsite})

    def set_microsite(self, request, *args, **kwargs):
        microsite = Microsite.get_microsite(self.request.get_full_path())

        if microsite:
            # means we are in a conf microsite (not incl npc)
            self.conf_menu_query = MenuItem.get_root_menu(landing_code=microsite.home_page_code)
            self.microsite = microsite
        else:
            self.conf_menu_query = None

    def get_initial(self):

        self.contact = self.request.user.contact
        self.demographics = self.contact.get_imis_demographics_legacy()
        if self.demographics.get('success', False):
            self.demographics = self.demographics['data']
        else:
            self.demographics = {}

        initial = super().get_initial()

        initial.update({
            "race": (self.demographics.get("race", "") or "").split(","),
            "hispanic_origin": self.demographics.get("origin", ""),
            "gender": self.demographics.get("gender", None),
            "gender_other": self.demographics.get("gender_other", None),

            "ai_an": self.demographics.get("ai_an", None),
            "asian_pacific": self.demographics.get("asian_pacific", None),
            "other": self.demographics.get("other", None),
            "span_hisp_latino": self.demographics.get("span_hisp_latino", None),

        })

        return initial

    def post_data_to_imis(self, form):
        self.demographics.update({
            "ethnicity_noanswer": bool("NO_ANSWER" in form.cleaned_data.get("race", [])),
            "race_noanswer": bool("NO_ANSWER" in form.cleaned_data.get("race", [])),
            "origin_noanswer": bool(form.cleaned_data.get("hispanic_origin", "") == "O000"),
            "ethnicity": ",".join(form.cleaned_data.get("race", [])),
            "origin": form.cleaned_data.get("hispanic_origin"),
            "gender": form.cleaned_data.get("gender", ""),
            "gender_other": form.cleaned_data.get("gender_other", ""),

            "ai_an": form.cleaned_data.get("ai_an", ""),
            "asian_pacific": form.cleaned_data.get("asian_pacific", ""),
            "ethnicity_other": form.cleaned_data.get("other", ""),
            "span_hisp_latino": form.cleaned_data.get("span_hisp_latino", ""),
        })

        self.update_ind_demographics()
        self.update_race_origin()

    def update_race_origin(self):
        # Can't do `get_or_create` on just the id - the table (like many in iMIS) allows
        # empty strings but not nulls...
        race_origin = imis_models.RaceOrigin.objects.filter(
            id=self.contact.user.username
        ).first()

        if race_origin is None:
            race_origin = imis_models.RaceOrigin(id=self.contact.user.username)

        race_origin.span_hisp_latino = self.demographics['span_hisp_latino']
        race_origin.origin = self.demographics['origin']
        race_origin.race = self.demographics['ethnicity']
        race_origin.ai_an = self.demographics['ai_an']
        race_origin.asian_pacific = self.demographics['asian_pacific']
        race_origin.other = self.demographics['ethnicity_other']
        race_origin.ethnicity_noanswer = self.demographics['ethnicity_noanswer']
        race_origin.origin_noanswer = self.demographics['origin_noanswer']
        race_origin.ethnicity_verifydate = self.contact.getdate()
        race_origin.origin_verifydate = self.contact.getdate()
        race_origin.save()

    def update_ind_demographics(self):
        ind_demo = self.contact.get_imis_ind_demographics()
        ind_demo.gender = self.demographics['gender']
        if ind_demo.gender == "S":
            ind_demo.gender_other = self.demographics['gender_other']
        ind_demo.save()

    def after_save(self, form):
        """hook for doing additional things after all saving is done"""
        pass
