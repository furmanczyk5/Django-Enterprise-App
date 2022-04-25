import datetime
from functools import reduce

import pytz
from django import template
from django.core.urlresolvers import reverse
from django.db.models import Q

from content.models.settings import ContentStatus, PublishStatus
from content.templatetags.content_extras import submit_row_content_content
from events.models import Event, EventType
from imis.models import CustomEventSchedule
from imis.utils.labels import get_label_for_enum
from myapa.models.constants import ContactRoleTypes
from registrations.models import Attendee
from store.models import Purchase, ProductCart, ProductOption
from store.utils import PurchaseInfo

register = template.Library()


def get_event_from_context(context):
    if "event" in context and context["event"] is not None:
        event = context["event"]
    elif "event_id" in context and context["event_id"] is not None:
        event = Event.objects.get(id=context["event_id"])
    elif "event_master_id" in context and context["event_master_id"] is not None:
        event = Event.objects.get(master__id=context["event_master_id"])
    else:
        event = None
    return event


# should be moved to registrations once proved to work
@register.inclusion_tag("events/newtheme/templatetags/registration-buttons.html", takes_context=True)
def event_register_link(context, register_url=None, activities_url=None, reprint_url=None, location="WEB"):
    """
    inclusion tag for registration link
    """
    # try:
    event = context["event"]
    product = None
    if hasattr(event, "product"):
        try:
            product = ProductCart.objects.get(id=event.product.id)
        except:
            pass
    if product:
        user = context["request"].user.__class__.objects.prefetch_related("groups").get(id=context["request"].user.id) if context["request"].user.is_authenticated() else None
        # NOTE - TO DO... it's screwy that attendee records linked to draft copies of events... but since they are, we need to compare
        # this event's master with the attendeee event's master to see if the user is already registered... should rethink in the future
        # once product publising works out OK...
        has_registration = Attendee.objects.filter(contact__user__username=user.username, event__master_id=event.master, status="A").exists() if user else False
        has_activities = event.event_type == "EVENT_MULTI"
        # this line fails because user is undefined if no one is logged in:
        # this determines whether the event is within the registration period
        # by seeing if a price is returned. This doesn't work for the not logged
        # in case -- we should test against the date/time in a price and set
        # registration_is_open to a boolean
        # registration_is_open = product.get_price(user=user)

        registration_is_open = False
        for p in product.prices.all():
            now = datetime.datetime.now(pytz.utc)
            if p.begin_time and p.end_time and now >= p.begin_time and now <= p.end_time:
                registration_is_open = True

        microsite = event.master.event_microsite.first()
        if microsite and microsite.url_path_stem and microsite.url_path_stem != "conference":
            reg_url = reverse("registrations:microsite_select_registration",
                kwargs=dict(master_id=event.master_id, microsite_url_path_stem=microsite.url_path_stem))
            act_url = reverse("registrations:microsite_add_activities",
                kwargs=dict(master_id=event.master_id, microsite_url_path_stem=microsite.url_path_stem))
        else:
            reg_url = reverse("registrations:select_registration", kwargs=dict(master_id=event.master_id))
            act_url = reverse("registrations:select_registration", kwargs=dict(master_id=event.master_id))

        return {
            "has_registration":has_registration,
            "registration_is_open":registration_is_open,
            "event":event,
            "product":product,
            "has_activities":has_activities,
            "user":user,
            # "register_url":register_url or reverse("registrations:select_registration", kwargs=dict(master_id=event.master_id)),
            # "add_activities_url":activities_url or reverse("registrations:add_activities", kwargs=dict(master_id=event.master_id)),
            "register_url":register_url or reg_url,
            "add_activities_url":activities_url or act_url,
            "reprint_url":reprint_url,
            "location":location,
        }
    else:
        return {}
    # except:
    #     return {}


def is_registered(event=None, user=None):
    """
    FIXME: This duplicates code found in :meth:`conference.views.program.conference_search.MicrositeConferenceSearchView.is_registered`
    :param event:
    :param user:
    :return:
    """
    try:
        meeting = event.product.imis_code
        product_options = ProductOption.objects.filter(
            product=event.product
        )

        query = reduce(
            lambda x, y: x | y,
            [Q(product_code=meeting + '/' + option.code)
                for option in product_options]
        )
        query.add(Q(id=user.username), Q.AND)
        query.add(Q(status='A'), Q.AND)

        return CustomEventSchedule.objects.filter(query).exists()
    except Exception as e:
        return False


@register.inclusion_tag("events/newtheme/templatetags/ticket-buttons.html", takes_context=True)
def activity_ticket_link(context, activity, product=None, product_price=None,
                         purchase_info=None, has_registration=None, kiosk=False):
    """
    Inclusion tag for showing buttons to add tickets to cart.

    :param context: :obj:`django.template.context.RequestContext`, the template context
    :param activity: :obj:`events.models.Activity`
    :param product: :obj:`store.models.Product`
    :param product_price: :obj:`store.models.ProductPrice`
    :param purchase_info: dict
    :param has_registration: bool

    :return: dict
    """
    if context["request"].user.is_authenticated():
        user = context["request"].user
    else:
        user = None

    activity = activity
    parent = None
    parent_product = None
    product = product or activity.get_product()
    kiosk = kiosk

    if product:
        parent_master = activity.parent
        parent = parent_master.content_live
        parent_product = parent.product

        product_price = product.prices.first() if product_price is None else product_price
        purchase_info = PurchaseInfo(product, user).get() if purchase_info is None and user else purchase_info

        if has_registration is None:
            has_registration = has_registration if has_registration is not None \
            else Purchase.objects.filter(
                user=user,
                product__id=parent.product.id
            ).exists()

            # has_registration = has_registration if has_registration is not None \
            #     else is_registered(
            #         event=parent_master.content_live.event,
            #         user=user
            #     )

    if product and parent_product:
        return {
            "activity": activity,
            "parent": parent,
            "product": product,
            "user": user,
            "has_parent_event_registration": has_registration,
            "price": product_price and product_price.price,
            "is_open": product_price is not None,
            "purchase_info": purchase_info,
            "join_waitlist_url": context["join_waitlist_url"],
            "is_waitlist": context["is_waitlist"],
            "is_ordered": context["is_ordered"],
            "kiosk": kiosk
        }
    else:
        return {}

@register.inclusion_tag('admin/content/content/submit-line.html', takes_context=True)
def submit_row_events_event(context, **kwargs):

    opts = context['opts']
    change = context['change']
    is_popup = context['is_popup']
    save_as = context['save_as']
    original = context.get('original', None)

    ctx = submit_row_content_content(context, **kwargs)

    extra_save_options = context.get('extra_save_options', {})
    show_provider_submit = extra_save_options.get('show_provider_submit', False) # for publishing to the draft copy on the prod database
    if original and getattr(original, 'publish_status', "") == "SUBMISSION":
        ctx["show_provider_submit"] = not is_popup and show_provider_submit

    return ctx


@register.simple_tag(takes_context=True)
def add_product_info(context, activity):

    user = context["request"].user

    if not user.is_authenticated():
        return

    purchases = Purchase.objects.filter(user=user)
    if not purchases.exists():
        purchases = Purchase.objects.filter(contact=user.contact)

    product = context['product']

    if hasattr(activity, 'parent'):
        purchases = purchases.filter(
            product__content__master_id=activity.parent.id
        )

    activity.product_info = {
        'product': product,
        'price': product.get_price(
            contact=user.contact,
            purchases=purchases
        ),
        'purchase_info': PurchaseInfo(product, user).get(),
        'content': product.content
    }
    return activity


@register.filter
def get_event_type_label(event):
    if event.event_type == "EVENT_SINGLE":
        return "Single Event"
    elif event.event_type == "EVENT_MULTI":
        return "Multipart Event"
    elif event.event_type == "EVENT_INFO":
        return "Information-Only Event"
    elif event.event_type == "LEARN_COURSE":
        return "APA Learn Course"
    elif event.event_type == "ACTIVITY":
        return "Event Activity"
    elif event.event_type == "COURSE":
        return "On-Demand"
    else:
        return "Event"


@register.filter
def get_event_status_label(event):
    if event.is_cancelled:
        return "Cancelled"
    elif event.is_pending_payment:
        return "Pending Payment"
    elif event.has_changes:
        return "Entered and Edited"
    elif event.is_published:
        return "Entered"
    elif event.status == ContentStatus.ACTIVE.value and event.publish_status != PublishStatus.SUBMISSION.value:
        return "Processing your entered event"
    else:
        return "Not Entered"


@register.filter
def get_event_details_link(event):
    """This somewhat duplicates code found in :meth:`content.utils.utils.solr_record_to_details_path`,
    but that function is meant for a Solr search doc, not a Postgres record"""
    if getattr(event, "event_type", None) is not None and getattr(event, "is_published"):
        if event.event_type == EventType.EVENT_SINGLE.value:
            return "/events/eventsingle/{}/".format(event.master_id)
        elif event.event_type == EventType.EVENT_MULTI.value:
            return "/events/eventmulti/{}/".format(event.master_id)
        elif event.event_type == EventType.EVENT_INFO.value:
            return "/events/eventinfo/{}/".format(event.master_id)
        elif event.event_type == EventType.LEARN_COURSE.value:
            return "/learn/course/{}/".format(event.master_id)
        elif event.event_type == EventType.ACTIVITY.value:
            return "/events/activity/{}/".format(event.master_id)
        elif event.event_type == EventType.COURSE.value:
            return "/events/course/{}/".format(event.master_id)
    return '#'


@register.filter
def get_role_type_label(role_type):
    """
    Get the human-friendly label for a :attr:`myapa.models.contact_role.ContactRole.role_type`
    :param role_type: str
    :return: str
    """

    # We obviously can't have a & in a symbol, so we have some special cases
    # for the ContactRoleTypes Enum class
    if role_type == "ORGANIZER&SPEAKER":
        role_type = "ORGANIZER_AND_SPEAKER"
    elif role_type == "ORGANIZER&MODERATOR":
        role_type = "ORGANIZER_AND_MODERATOR"

    return get_label_for_enum(ContactRoleTypes, role_type)
