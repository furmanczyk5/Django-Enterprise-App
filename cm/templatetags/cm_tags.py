from django import template
from cm.utils import get_eval_status

register = template.Library()


@register.inclusion_tag('cm/newtheme/templatetags/star-rating.html')
def star_rating(rating=0.0, count="N/A"):
    """
    renders the navigation for passed section code
    """
    rating = rating or 0
    count = count or 0
    ctx = {
        "rating": rating,
        "count": count,
        "width": float(rating)/0.05
    }
    return ctx


@register.inclusion_tag(
    "cm/newtheme/templatetags/evaluate-event-button.html",
    takes_context=True)
def evaluate_event_button(context, event, contact,
                          claim=None, current_log=None, extra_class=""):
    """
    inclusion tag for showing buttons to add tickets to cart
    """
    context = get_eval_status(
        event, contact, claim=claim, current_log=current_log)
    context["extra_class"] = extra_class or "btn-primary"
    return context

@register.simple_tag
def get_current_cm_log(contact=None):
    """
    Get the current cm log for a contact
    """
    return contact.cm_logs.all().filter(is_current=True).first()
