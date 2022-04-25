import re

from django import template
from django.db import connections
from sentry_sdk import capture_exception

from imis import models as imis_models
from imis.db_accessor import DbAccessor
from myapa.models.constants import GENDER_CHOICES, HISPANIC_ORIGIN_CHOICES, \
    RACE_CHOICES, SALARY_CHOICES_ALL, FUNCTIONAL_TITLE_CHOICES
from myapa.models.contact import Contact
from myapa.models.profile import IndividualProfile
from myapa.models.proxies import School
from store.models import Product, Purchase

register = template.Library()


@register.filter(name="conditional_get_contact_by_id")
def conditional_get_contact_by_id(value, arg):
    try:
        if value is None or value == "":
            return Contact.objects.get(id=arg)
        else:
            return value
    except:
        return None


@register.filter(name="email_star_mask")
def email_star_mask(email):
    r1 = r'(?<=[^@]{4})([^@]*)(?=@)'
    r2 = r'(?<=@[^@]{4})([^@]*)(?=\.)'
    partially_masked = re.sub(r1,"****", email)
    fully_masked = re.sub(r2,"****", partially_masked)
    return fully_masked


@register.simple_tag
def get_school_name(value):
    school = School.objects.get(id=value)
    return school.title


@register.filter(name="get_gender_name")
def get_gender_name(code):
    return next((g[1] for g in GENDER_CHOICES if g[0] == code), "")

@register.filter(name="get_hispanic_origin_name")
def get_hispanic_origin_name(demographics):
    code = demographics.get("origin", "")
    other_options = {
        "O999":"span_hisp_latino"
    }
    name = next((g[1] for g in HISPANIC_ORIGIN_CHOICES if g[0] == code), "")
    other_input_key = other_options.get(code, None)
    if other_input_key:
        other_value = demographics.get(other_input_key)
        if other_value:
            name += ": {0}".format(other_value)
    return name

@register.filter(name="get_race_name_list")
def get_race_name_list(demographics):
    codes = (demographics.get("race", "") or "").split(",")
    other_options = {
        "E003":"ai_an",
        "E100":"asian_pacific",
        "E999":"other"
    }
    name_list = []
    for code in codes:
        name = next((g[1] for g in RACE_CHOICES if g[0] == code), "")
        other_input_key = other_options.get(code, None)
        if other_input_key:
            other_value = demographics.get(other_input_key)
            if other_value:
                name += ": {0}".format(other_value)
        if name:
            name_list.append(name)
    if demographics["ethnicity_noanswer"]:
        name_list.append("I prefer not to answer")
    return name_list

@register.filter(name="get_salary_range_name")
def get_salary_range_name(code):
    return next((g[1] for g in SALARY_CHOICES_ALL if g[0] == code), "")

@register.filter(name="get_functional_title_name")
def get_functional_title_name(code):
    return next((g[1] for g in FUNCTIONAL_TITLE_CHOICES if g[0] == code), "")


@register.filter(name="conditional_get_image_url")
def conditional_get_image_url(value, arg):
    try:
        if value is None or value == "":
            return None  #value.image_thumbnail.url
        else:
            profile = IndividualProfile.objects.get(contact=arg)
            url = profile.image.image_thumbnail.url
            return url
    except:
        return None


# THIS IS FOR THE ADMIN
@register.inclusion_tag('admin/myapa/contact/submit_line.html', takes_context=True)
def submit_row_myapa_contact(context, **kwargs):
    """
    Displays the row of buttons for delete and save.
    """
    opts = context['opts']
    change = context['change']
    is_popup = context['is_popup']
    save_as = context['save_as']

    extra_save_options = context.get('extra_save_options', {})

    show_solr_publish = extra_save_options.get('show_solr_publish', False) # for publishing to the live copy on the prod database
    show_imis_sync = extra_save_options.get('show_imis_sync', False)
    show_sync_credly = extra_save_options.get('show_sync_credly', False)

    ctx = {
        'opts': opts,
        'show_delete_link': not is_popup and context['has_delete_permission'] and change and context.get('show_delete', True),
        'show_save_as_new': not is_popup and change and save_as,
        'show_save_and_add_another': context['has_add_permission'] and not is_popup and (not save_as or context['add']),
        'show_save_and_continue': not is_popup and context['has_change_permission'],
        'is_popup': is_popup,
        'show_save': True,
        'preserved_filters': context.get('preserved_filters'),
    }

    original = context.get('original', None)
    ctx['original'] = original
    ctx['show_solr_publish'] = not is_popup and show_solr_publish
    ctx['show_imis_sync'] = not is_popup and show_imis_sync
    ctx['show_sync_credly'] = not is_popup and show_sync_credly

    return ctx

@register.simple_tag
def get_related_trans(trans):
    """
    Returns a group of "purchases" from an "order". Here trans is one trans record from set stored in "orders" in template context -- the set will have to be winnowed down to the set of "principal" trans records -- the one trans that represents the group all with the same trans_number
    :param trans: An iMIS Trans record.
    :return: purchases
    """
    purchases = []
    if trans:
        purchases = imis_models.Trans.objects.filter(trans_number=trans.trans_number)
    return purchases

@register.simple_tag
def get_purchases_products_list(trans):
    """
    Here orders are set of "principal" Trans records: the PAY Trans record from group that have same trans_number.
    :param orders: Set of "representative Trans records that stand for a group with same trans_number
    :return: purchases_products_list
    """
    if trans:
        purchases = imis_models.Trans.objects.filter(trans_number=trans.trans_number)
    else:
        purchases = []
    purchases_products_list = []
    for o in purchases:
        if o.transaction_type != "PAY" and o.product_code:
            p = imis_models.Product.objects.filter(product_code=o.product_code).first()
            purchases_products_list.append((o, p, o.amount))
    return purchases_products_list

@register.simple_tag
def get_total_balance(purchases):
    """
    Returns total charges/balance for one related group of trans records
    :param purchases: Set of iMIS Trans records all with same trans_number
    :return: charges_credits_tuple
    """
    total = 0
    payment = 0
    for o in purchases:
        if o.transaction_type != "PAY":
            total += o.amount
        else:
            payment = o.amount
    balance = total + payment
    total_balance_tuple = (total, balance)
    return total_balance_tuple

@register.simple_tag
def get_description(purchases):
    """
    returns a single description culled from a group of related trans records
    :param purchases: Set of iMIS Trans records all with same trans_number
    :return: description
    """
    description = None
    for o in purchases:
        if o.description:
            description = o.description.strip("|")
    return description

@register.filter
def get_dict(trans):
    return trans.__dict__

@register.filter
def is_waitlist(trans_tuple):
    trans = trans_tuple[0]
    product = trans_tuple[1]
    query = """
            SELECT OL.ADDED_TO_WAIT_LIST FROM Order_Lines as OL INNER JOIN Orders as O
            ON OL.ORDER_NUMBER = O.ORDER_NUMBER
            WHERE O.BT_ID=? AND OL.PRODUCT_CODE=? AND OL.QUANTITY_BACKORDERED > 0 --AND ORDER_DATE=?
        """
    rows = DbAccessor().get_rows(
        query,
        [
            trans.bt_id,
            product.product_code#,
            # order_date
        ]
    )
    waitlisted = [row[0] for row in rows if row[0] != None]
    return len(waitlisted) > 0

@register.filter
def is_apa_learn_purchase(product_code):
    django_product = Product.objects.filter(imis_code=product_code).first()
    content = django_product.content
    event_type = content.event.event_type
    if event_type == "LEARN_COURSE" or "LEARN_COURSE_BUNDLE":
        return True
    else:
        return False

@register.filter
def is_apa_learn_order(purchases_products_list):
    if purchases_products_list:
        for ppl_tuple in purchases_products_list:
            django_product = Product.objects.filter(imis_code=ppl_tuple[1].product_code).first()
            content = getattr(django_product, "content", None)
            event = getattr(content, "event", None)
            event_type = getattr(event, "event_type", None)
            if event_type == "LEARN_COURSE" or event_type == "LEARN_COURSE_BUNDLE":
                return True
    return False

@register.simple_tag
def get_django_purchase(imis_transaction):
    t = imis_transaction
    django_purchase = Purchase.objects.filter(
        imis_trans_number=t.trans_number,
        imis_trans_line_number=t.line_number
    )
    if not django_purchase:
        trans_amount = round(-1 * t.amount, 2)
        tokens = t.product_code.split("/")
        if tokens:
            imis_code = tokens[0]
        django_purchase = Purchase.objects.filter(
            user__username=t.bt_id,
            submitted_time__year=t.transaction_date.year,
            submitted_time__month=t.transaction_date.month,
            submitted_time__day=t.transaction_date.day,
            product__gl_account=t.gl_account,
            product__imis_code=imis_code,
            amount=trans_amount,
        )
    django_purchase = django_purchase.first() if django_purchase.count() == 1 else None
    return django_purchase


@register.simple_tag
def get_django_order(django_purchase):
    if django_purchase:
        return django_purchase.order


@register.filter(name='abs')
def abs_filter(value):
    return abs(value)


@register.filter(name='table_name_from_queryset')
def get_table_name(queryset):
    return queryset.model.__name__


MEMBER_TYPES = None


def get_member_types():
    global MEMBER_TYPES
    if MEMBER_TYPES is None:
        try:
            with connections['MSSQL'].cursor() as cursor:
                cursor.execute("SELECT MEMBER_TYPE, DESCRIPTION FROM Member_Types")
                MEMBER_TYPES = dict(cursor.fetchall())
        except Exception as e:
            capture_exception(e)


@register.filter(name='get_member_type_label')
def get_member_type_label(member_type):
    get_member_types()
    if isinstance(MEMBER_TYPES, dict):
        return MEMBER_TYPES.get(member_type, '')
    return ''

