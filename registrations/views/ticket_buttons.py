from django.db.models import Q
from django.views.generic import TemplateView

from events.models import Activity
from store.models import Purchase, ProductCart
from store.utils import PurchaseInfo


class TicketButtonsView(TemplateView):
    template_name = "registrations/newtheme/includes/ticket-buttons.html"
    http_method_names = ["get"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        activity = Activity.objects.get(publish_status="PUBLISHED", master_id=kwargs.get("master_id"))
        user = self.request.user
        registration = Purchase.objects.filter(
            Q(user=user) | Q(contact__user__username=user.username),
            product__content__master_id=activity.parent.id)
        context["event"] = add_product_info(activity, self.request.user, registration)
        return context


def add_product_info(activity, user, registration):
    product = activity.product
    product_cart = ProductCart.objects.get(
        content=product.content
    )

    activity.product_info = {
        'product': product,
        'price': product_cart.get_price(
            contact=user.contact,
            purchases=registration
        ),
        'purchase_info': PurchaseInfo(product, user).get(),
        'content': product.content
    }
    return activity
