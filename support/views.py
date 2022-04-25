from django.core.urlresolvers import reverse_lazy
from django.forms.models import model_to_dict
from django.views.generic import FormView

from content.mail import Mail
from myapa.viewmixins import AuthenticateLoginMixin
from .forms import ContactUsForm


class ContactUsView(AuthenticateLoginMixin, FormView):
    template_name = "support/newtheme/contact-us.html"
    form_class = ContactUsForm
    success_url = reverse_lazy("support:contact_us_success")
    prompt_login = False
    category = None

    def get(self, request, *args, **kwargs):
        self.category = kwargs.pop("category", None)
        return super().get(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        if self.is_authenticated:
            contact = self.request.user.contact
            initial.update({
                "apa_id": self.username,
                "full_name": contact.full_title(),
                "email": contact.email,
                "phone": contact.phone,
                "contact": contact,
                "created_by": self.request.user
            })
        initial["category"] = self.category
        return initial

    def form_valid(self, form):
        ticket = form.save(commit=False)
        support_email = ticket.get_support_email()
        ticket.save()

        Mail.send("CUSTOMER_SERVICE_REQUEST", support_email, model_to_dict(ticket))
        Mail.send("CUSTOMER_SERVICE_REQUEST_CONFIRMED", ticket.email, model_to_dict(ticket))
        return super().form_valid(form)
