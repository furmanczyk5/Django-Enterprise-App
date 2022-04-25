import sys

from django import template
from django.core.urlresolvers import reverse_lazy

from learn.models.learn_course import LearnCourse
from events.models import Event
from store.models import ProductOption, Purchase, ProductDonation
from store.forms import FoundationDonationCartForm

register = template.Library()


@register.inclusion_tag("store/newtheme/templatetags/product-prices.html")
def product_option_box(product, user, radio):
    if product:
        product_option = ProductOption.objects.get(pk=radio.choice_value)
        #prices = product_option.get_price(user)
        price = product.get_price(user=user, option=product_option)
        
        return {
            "radio": radio, 
            "product_option": product_option,
            "price": price
        }

@register.inclusion_tag("store/newtheme/templatetags/cart.html")
def cart(user, remove_is_form=False):
    cart_items = Purchase.cart_items(
        user=user).select_related(
        "product__content__master", "product_price").order_by('product__content__event__begin_time')
    purchase_ids=set()

    # TO DO... a template tag is NOT the best place for this logic... this should be in a model function/utility
    # function, and then simply rendered through templates.
    for index,cart_item in enumerate(cart_items):
        try:
            item_event = Event.objects.get(id=cart_item.product.content.id)
            if item_event.event_type != "ACTIVITY": 
                continue
            if index+1 == cart_items.count():
                break
            for sub_cart_item in cart_items[index+1:]:
                sub_item_event = Event.objects.get(id=sub_cart_item.product.content.id)

                if item_event.event_type == "ACTIVITY" and sub_item_event.event_type == "ACTIVITY" and \
                (item_event.begin_time <= sub_item_event.end_time and sub_item_event.begin_time <= item_event.end_time ):
                    purchase_ids.add(cart_item.id)
                    purchase_ids.add(sub_cart_item.id)

        except:
            pass

    conflict_purchase_ids=list(purchase_ids)
    # print(conflict_purchase_ids)
        
    return {"cart_items":cart_items, "conflict_purchase_ids":conflict_purchase_ids, "remove_is_form":True}


@register.inclusion_tag('store/newtheme/foundation/donation-cart.html')
def donation_form(request, action=reverse_lazy("foundation:donation_cart"), link=reverse_lazy("foundation:donation")):

    PRODUCT_SORT_ORDER = (
        "DONATION_GENERAL",
        "DONATION_COMMUNITY",
        "DONATION_SCHOLARSHIP",
        "DONATION_RESEARCH")

    donation_products = sorted(
        ProductDonation.objects.filter(status="A", publish_status="PUBLISHED").select_related("content"),
        key=lambda dp: (PRODUCT_SORT_ORDER.index(dp.code) if (dp.code in PRODUCT_SORT_ORDER) else sys.maxsize)
    )

    initial = dict(name=request.user.contact.title)

    form = FoundationDonationCartForm(products=donation_products, initial=initial)

    return dict(
        form=form,
        action=action or "",
        link=link
    )


@register.filter(name='has_price')
def has_price(product):
    """If any option has a price then return true (product is purchaseable)"""
    for option in product.options.all():
        if option.my_price:
            return True

    return False


@register.filter(name='has_learn_course')
def has_learn_course(content):
    """Does this product have a code that corresponds to an APA Learn Course?"""
    if LearnCourse.objects.filter(code='LRN_{}'.format(content.code)).exists():
        return True
    if content.code is not None:
        npc18code = content.code.split("NPC")
        if len(npc18code) > 1:
            return LearnCourse.objects.filter(code="LRN_{}".format(npc18code[1])).exists()
    if LearnCourse.objects.filter(title__icontains=content.title).exists() and content.content_type != 'PUBLICATION':
        return True
    return False

@register.filter(name='is_od_course')
def is_od_course(content):
    """ Is this product an On-Demand Course (with some special exemptions)"""
    return content.content_type == "EVENT" and \
        (content.event_type == "COURSE" and content.master_id != 9026917)


@register.filter
def get_order_status_label(order):
    if not hasattr(order, 'order_status'):
        return ''
    if order.order_status == "NOT_SUBMITTED":
        return "Not Yet Submitted"
    elif order.order_status == "SUBMITTED":
        return "Submitted"
    elif order.order_status == "CANCELLED":
        return "Cancelled"
    elif order.order_status == "PROCESSED":
        return "Processed (archived)"
