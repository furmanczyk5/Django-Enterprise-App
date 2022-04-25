import datetime

from importlib import import_module

from django.conf import settings
from django.db.models import F
from django.utils import timezone

from imis.models import Name, Activity
from store.models import Product


def get_cart(view, session_key=None):

    if session_key is None:
        request = view.request
        try:
            cart = Cart.objects.get(session_key=request.session.session_key)
        except Cart.DoesNotExist:
            cart = Cart.objects.create(session_key=request.session.session_key)
    else:
        cart = Cart.objects.get(session_key=session_key)

    return cart


def restore_product_qty(cartitem):
    product = cartitem.product
    qty = cartitem.qty
    Product.objects.filter(id=product.id).update(current_quantity_taken=F('current_quantity_taken')-qty)
    cartitem.delete()


def restore_inventory_from_cart(cart):
    for cartitem in cart.cartitem_set.all():
        restore_product_qty(cartitem)


def restore_inventory_from_abandoned_carts():
    current_time_minus_lifespan = timezone.now() - datetime.timedelta(minutes=settings.CART_LIFESPAN_MIN)
    for cart in Cart.objects.filter(last_updated__lt=current_time_minus_lifespan):
        restore_inventory_from_cart(cart)
        destroy_checkout_session_variables(cart.session_key)
        cart.delete()


def destroy_checkout_session_variables(request):
    session_key = request.session.session_key
    engine = import_module(settings.SESSION_ENGINE)
    session_store = engine.SessionStore(session_key)

    # cleanup the session keys
    try:
        del session_store['event_id']
        del request.session["event_id"]
    except KeyError:
        pass

    try:
        del session_store['question_responses']
        del request.session["question_responses"]
    except KeyError:
        pass

    try:
        del session_store['order_id']
        del request.session["order_id"]
    except KeyError:
        pass

    try:
        del session_store['session_product_prices']
        del request.session["session_product_prices"]
    except KeyError:
        pass

    try:
        del session_store['registration_option_id']
        del request.session["registration_option_id"]
    except KeyError:
        pass

    try:
        del session_store['main_product_quantity']
        del request.session["main_product_quantity"]
    except KeyError:
        pass

    try:
        del session_store["checkout_type"]
        del request.session["checkout_type"]
    except KeyError:
        pass

    try:
        del session_store["content_master_id"]
        del request.session["content_master_id"]
    except KeyError:
        pass

    try:
        del session_store["submission_category_code"]
        del request.session["submission_category_code"]
    except KeyError:
        pass

    try:
        del session_store["final_amount"]
        del request.session["final_amount"]
    except KeyError:
        pass

    try:
        del session_store["content_master_id"]
        del request.session["content_master_id"]
    except KeyError:
        pass
    session_store.save()

def rows_distributed(thelist, n):
    """
    Break a list into ``n`` rows, distributing columns as evenly as possible
    across the rows. For example::

        >>> l = range(10)

        >>> rows_distributed(l, 2)
        [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9]]

        >>> rows_distributed(l, 3)
        [[0, 1, 2, 3], [4, 5, 6], [7, 8, 9]]

        >>> rows_distributed(l, 4)
        [[0, 1, 2], [3, 4, 5], [6, 7], [8, 9]]

        >>> rows_distributed(l, 5)
        [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9]]

        >>> rows_distributed(l, 9)
        [[0, 1], [2], [3], [4], [5], [6], [7], [8], [9]]

        # This filter will always return `n` rows, even if some are empty:
        >>> rows(range(2), 3)
        [[0], [1], []]
    """
    try:
        n = int(n)
        thelist = list(thelist)
    except (ValueError, TypeError):
        return [thelist]
    list_len = len(thelist)
    split = list_len // n

    remainder = list_len % n
    offset = 0
    rows = []
    for i in range(n):
        if remainder:
            start, end = (split+1)*i, (split+1)*(i+1)
        else:
            start, end = split*i+offset, split*(i+1)+offset
        rows.append(thelist[start:end])
        if remainder:
            remainder -= 1
            offset += 1
    return rows


def get_merge_code_and_tributee(donor):
    note_string = donor["note"]
    tokens = note_string.split(';') if note_string else []
    merge_code = honoree = memoree = recognized = ""

    for token in tokens:
        if token.find("Merge Code") >= 0:
            merge_code_parts = token.split("=")
            if merge_code_parts and len(merge_code_parts) > 1:
                merge_code = merge_code_parts[1]
            else:
                merge_code = None
        elif token.find("In Honor Of") >= 0:
            honoree = token.replace("In Honor Of", "").strip()
        elif token.find("In Memory Of") >= 0:
            memoree = token.replace("In Memory Of", "").strip()
        elif token.find("In Recognition Of") >= 0:
            recognized = token.replace("In Recognition Of", "")

        # elif token.find("@") >= 0:
        #     recognition_name_email_token = token
        # elif token.find("Comments") >= 0:
        #     comments_token = token
        # elif token.find("A tribute email was sent to ") >= 0:
        #     tribute_email = token.replace("A tribute email was sent to ", "")

    tributee = honoree or memoree or recognized

    if not tributee:
        memorial_name_text = donor["memorialnametext"]
        if memorial_name_text:
            tributee = memorial_name_text
        else:
            tributee = donor["tributee_name"] if donor["tributee_name"] else ""

    return (merge_code, tributee)


def get_donor_reference(donor):
    merge_code = donor["merge_code"]
    tributee = donor["tributee_name"]
    tribute_word = "honor"

    if merge_code:
        if merge_code == "HONOROF":
            tribute_word = "honor"
        elif merge_code == "MEMORYOF":
            tribute_word = "memory"
        elif merge_code == "RECOGNITIONOF" or merge_code == "RECOGNOF":
            tribute_word = "recognition"
        else:
            tribute_word = "appreciation"

    is_anonymous = (donor["listas"] == "Anonymous")

    if is_anonymous:
        donor_name = "Anonymous"
    else:
        donor_name = donor["full_name"] if donor["full_name"].strip() else donor["company"]

    if not tributee:
        return "%s" % donor_name
    elif not is_anonymous:
        return "%s in %s of %s" % (donor_name, tribute_word, tributee)
