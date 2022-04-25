from decimal import Decimal

from django.apps import apps
from django.utils import timezone

from imis.utils import sql as sql_utils
# from events.models import Event
from imis.models import CustomEventSchedule
from registrations.imis import DbAccessor

ACTIVITY_TICKET = 'ACTIVITY_TICKET'
EVENT_REGISTRATION = 'EVENT_REGISTRATION'
NOT_PAID = 'I'
ACTIVE = 'A'
CANCELLED = 'C'


def is_event_ticket(purchase):
    return purchase.product.product_type in [
        EVENT_REGISTRATION, ACTIVITY_TICKET
    ]


def delete_event_tickets(purchase):
    meeting_code = get_meeting_code(purchase)
    product_code = get_product_code(purchase, meeting_code)
    like_product_code = "{}%".format(product_code)

    query = """
        DELETE FROM Custom_Event_Schedule
        WHERE ID=? AND MEETING=? AND PRODUCT_CODE LIKE ? AND STATUS=?
        """

    DbAccessor().execute(
        query,
        [
            purchase.user.username,
            meeting_code,
            like_product_code,
            NOT_PAID
        ]
    )


def get_meeting_code(purchase):
    EventModel = apps.get_model('events.Event')
    query = EventModel.objects.filter(product=purchase.product)
    return query.first().get_meeting_code()


def get_product_code(purchase, meeting_code):
    product_code = purchase.product.imis_code

    if meeting_code == product_code:
        option_code = purchase.option.code
        product_code += '/' + option_code

    return product_code


def save_tickets_to_imis(purchase):
    meeting_code = get_meeting_code(purchase)
    product_code = get_product_code(purchase, meeting_code)

    ticket_fields = {
        'id': purchase.user.username,
        'meeting': meeting_code,
        'registrant_class': purchase.product_price.imis_reg_class or '',
        'product_code': product_code,
        'status': NOT_PAID,
        'unit_price': purchase.product_price.price#,
    }

    scheduled_tickets = list(
        CustomEventSchedule.objects.filter(**ticket_fields))

    difference = int(purchase.quantity) - len(scheduled_tickets)

    if needs_ticket_added(difference):
        for _ in range(difference):
            CustomEventSchedule.objects.create_schedule_entry(ticket_fields)

    if needs_ticket_removed(difference):
        for index in range(abs(difference)):
            scheduled_tickets[index].delete()


def needs_ticket_added(ticket_difference):
    return ticket_difference > 0


def needs_ticket_removed(ticket_difference):
    return ticket_difference < 0


def save_activity_to_schedule(activity, username, api=False):
    EventModel = apps.get_model('events.Event')
    if api:
        update_cadmium_mobile(activity, username, "Add")
    parent_event = EventModel.objects.filter(
        master=activity.parent
    ).first()
    meeting = parent_event.get_meeting_code()
    product_code = activity.code
    try:
        activity = CustomEventSchedule.objects.get(
            id=username,
            meeting=meeting,
            product_code=product_code
        )
        activity.update_status(ACTIVE)
    except Exception as e:
        CustomEventSchedule.objects.create_schedule_entry(
            {
                'id': username,
                'meeting': meeting,
                'product_code': product_code,
                'status': ACTIVE,
                'unit_price': Decimal('0.00')
            }
        )
        return e

def add_to_waitlist(activity, username, *args, **kwargs):
    EventModel = apps.get_model('events.Event')
    parent_event = EventModel.objects.filter(
        master=activity.parent
    ).first()
    meeting = parent_event.get_meeting_code()
    product_code = activity.product.imis_code
    now = timezone.now()
    query = """
            SELECT OrderNumber FROM vCsRegistration
            WHERE BillToId=? AND EventCode=?
        """
    row = DbAccessor().get_row(query,[username, meeting])
    try:
        OrderNumber = row[0]
    except:
        OrderNumber = None
    query = """
	    SELECT ISNULL(MAX(LINE_NUMBER),0) AS LAST_LINE_NUMBER FROM Order_Lines WHERE ORDER_NUMBER = ?
    """
    line_number_row = DbAccessor().get_row(query, [OrderNumber])
    try:
        line_number = line_number_row[0] + 1
    except:
        line_number = None
    description = product_code + " | " + activity.title
    income_account = activity.product.gl_account
    if OrderNumber and line_number and product_code:
        cursor = insert_waitlist_order_lines(OrderNumber, line_number, product_code, 1, now, description, income_account)
    else:
        cursor = -1
    query = """
    UPDATE Orders
    SET NUMBER_LINES = (SELECT TOP 1 LINE_NUMBER FROM Order_Lines WHERE ORDER_NUMBER = ? ORDER BY LINE_NUMBER DESC)
    WHERE ORDER_NUMBER = ?
    """
    if cursor != -1:
        cursor = DbAccessor().execute(query, [OrderNumber,OrderNumber])
    return cursor

def insert_waitlist_order_lines(order_number, line_number, product_code, quantity_backordered,
                                added_to_wait_list, description, income_account):
    order_lines_data = {
        'order_number': order_number,
        'line_number': line_number,
        'product_code': product_code,
        'quantity_backordered': quantity_backordered,
        'added_to_wait_list': added_to_wait_list,
        'description': description,
        'income_account': income_account
    }
    order_lines_insert = sql_utils.make_insert_statement(
        'Order_Lines',
        order_lines_data,
        exclude_id_field=False
    )
    return sql_utils.do_insert(order_lines_insert, order_lines_data)

def cancel_activity_on_schedule(activity, username, api=False):
    if api:
        update_cadmium_mobile(activity, username, "Remove")

    try:
        activity = CustomEventSchedule.objects.get(
            id=username,
            product_code=activity.code
        )
        activity.update_status(CANCELLED)
    except Exception as e:
        return e

def is_waitlist_in_imis(purchase=None, *, username=None, product_code=None):
    if purchase:
        username = purchase.user.username
        meeting_code = get_meeting_code(purchase)
        product_code = get_product_code(purchase, meeting_code)
    else:
        username = username
        product_code = product_code

    query = """
            SELECT OL.ADDED_TO_WAIT_LIST FROM Order_Lines as OL INNER JOIN Orders as O
            ON OL.ORDER_NUMBER = O.ORDER_NUMBER
            WHERE O.BT_ID=? AND OL.PRODUCT_CODE=? AND OL.QUANTITY_BACKORDERED > 0
        """
    rows = DbAccessor().get_rows(query,[username,product_code])
    try:
        waitlisted = [row[0] for row in rows if row[0] != None]
    except:
        waitlisted = []
    return len(waitlisted) > 0

def is_ordered_in_imis(purchase=None, *, username=None, product_code=None):
    """
    here ordered means that staff "registered from waitlist" in staff site
    if staff removes user from waitlist (pure remove) then they can rejoin
    :param purchase:
    :param username:
    :param product_code:
    :return:
    """
    if purchase:
        username = purchase.user.username
        meeting_code = get_meeting_code(purchase)
        product_code = get_product_code(purchase, meeting_code)
    else:
        username = username
        product_code = product_code

    query = """
            SELECT OL.QUANTITY_ORDERED FROM Order_Lines as OL INNER JOIN Orders as O
            ON OL.ORDER_NUMBER = O.ORDER_NUMBER
            WHERE O.BT_ID=? AND OL.PRODUCT_CODE=? AND OL.QUANTITY_ORDERED > 0
        """
    rows = DbAccessor().get_rows(query,[username,product_code])
    try:
        ordered = [row[0] for row in rows if row[0] != None and row[0] > 0]
    except:
        ordered = []
    return len(ordered) > 0

def update_cadmium_mobile(activity=None, username=None, action=None):
    from conference.utils_harvester import add_or_remove_eventscribe_favorites
    from store.models.product import Product

    if activity and activity.external_key:
        cadmium_id = activity.external_key
        product = Product.objects.filter(content=activity).first()
        ticketed = True if product else None
    else:
        cadmium_id = ticketed = None

    add_or_remove_eventscribe_favorites(username=username, add_or_remove=action,
    cadmium_id=cadmium_id, ticketed=ticketed)

