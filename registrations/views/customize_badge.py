from django.core.urlresolvers import reverse
from django.db.models import Q
from django.views.generic import FormView

from conference.models import Microsite
from content.models import MenuItem
from events.models import Event, NATIONAL_CONFERENCES
from imis.models import CustomEventRegistration
from myapa.viewmixins import AuthenticateLoginMixin
from registrations.forms import AttendeeBadgeShippingForm, AttendeeBadgeForm
from registrations.imis.badge import Badge
from store.models import Purchase


class CustomizeBadgeView(AuthenticateLoginMixin, FormView):
    form_class = AttendeeBadgeForm
    template_name = "registrations/newtheme/registration-badge.html"
    success_url = ""
    confirm_badge_text = "Confirm Badge and Mailing Address"
    is_kiosk = False
    microsite = None
    conf_menu_query = None

    def get_event(self):
        master_id = self.kwargs.get("master_id")
        return Event.objects.get(master_id=master_id, publish_status="PUBLISHED")

    def get_badge(self):
        registrations = CustomEventRegistration.objects.filter(
            id=self.user.username,
            meeting=self.event.product.imis_code
        )
        badge = Badge().get_full(self.user.username)

        try:
            registration = registrations.first().__dict__
            badge = {**badge, **registration}
        except:
            pass

        return badge

    def setup(self, *args, **kwargs):
        self.event = self.get_event()
        self.user = self.request.user
        self.badge = self.get_badge()
        self.is_npc = self.event.code in [nc[0] for nc in NATIONAL_CONFERENCES]
        if self.is_npc and not self.is_kiosk:
            self.template_name = "registrations/conference/registration-badge.html"
        self.purchase = Purchase.objects.filter(
            Q(user=self.user) | Q(contact__user__username=self.user.username),
            product__content__master_id=self.event.master_id
        ).first()

        self.has_activities = False
        if self.event.event_type == "EVENT_MULTI":
            event_multi = self.event.get_proxymodel_class().objects.get(
                master_id=self.event.master_id,
                publish_status="PUBLISHED"
            )
            self.has_activities = any(hasattr(i, "product") for i in event_multi.get_activities())

    def get(self, request, *args, **kwargs):
        self.setup(*args, **kwargs)
        self.set_microsite(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.setup(*args, **kwargs)
        self.set_microsite(request, *args, **kwargs)
        return super().post(request, *args, **kwargs)

    def get_form_class(self):
        if self.is_npc:
            return self.form_class
        else:
            return AttendeeBadgeForm

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        return {**initial, **self.badge}

    def form_valid(self, form):
        registration = form.save(commit=False)
        registration.id = self.user.username
        registration.meeting = self.event.product.imis_code
        registration.save()
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["event"] = self.event
        context["has_activities"] = self.has_activities
        context["is_npc"] = self.is_npc
        context["badge"] = self.get_full_badge_context()
        context["confirm_badge_text"] = "Confirm Badge"
        context["conference_menu"] = self.conf_menu_query
        context["microsite"] = self.microsite
        return context

    def get_full_badge_context(self):
        return {
            **self.badge,
            **dict(purchase=self.purchase),
            **{
                'member_type': self.user.contact.member_type,
                'username': self.user.username,
                'title': self.user.contact.full_title
            }
        }

    def get_success_url(self):
        if self.request.POST.get("submit_button", "just_register") == "and_add_activities":
            if self.microsite.url_path_stem and self.microsite.url_path_stem != "conference":
                return reverse("registrations:microsite_add_activities",
                               kwargs={
                                   "master_id": self.event.master_id,
                                   "microsite_url_path_stem": self.microsite.url_path_stem})
            else:
                return reverse("registrations:add_activities", kwargs={"master_id": self.event.master_id})
        else:
            return reverse("store:cart")

    def get_confirm_badge_text(self):
        return self.confirm_badge_text if self.is_npc else "Confirm Badge"

    def set_microsite(self, request, *args, **kwargs):
        microsite = Microsite.get_microsite(self.request.get_full_path())

        if microsite:
            # means we are in a conf microsite (not incl npc)
            self.conf_menu_query = MenuItem.get_root_menu(landing_code=microsite.home_page_code)
            self.microsite = microsite
        else:
            self.conf_menu_query = None
