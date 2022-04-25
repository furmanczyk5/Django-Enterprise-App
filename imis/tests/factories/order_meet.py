import factory

from imis.models import OrderMeet


class ImisOrderMeetFactory(factory.Factory):

    order_number = factory.Sequence(lambda n: n + 1000000)
    meeting = ''
    registrant_class = ''
    arrival = None
    departure = None
    hotel = ''
    lodging_instructions = ''
    booth = ''
    guest_first = ''
    guest_middle = ''
    guest_last = ''
    guest_is_spouse = False
    additional_badges = ''
    delegate = ''
    uf_1 = False
    uf_2 = False
    uf_3 = False
    uf_4 = False
    uf_5 = False
    uf_6 = ''
    uf_7 = ''
    uf_8 = 'DJANGO_TEST_FACTORY'
    share_status = 0
    share_order_number = 0
    room_type = ''
    room_quantity = 0
    room_confirm = False
    uf_9 = ''
    uf_10 = ''
    arrival_time = None
    departure_time = None
    comp_registrations = 0
    comp_reg_source = 0
    total_square_feet = 0
    comp_registrations_used = 0
    parent_order_number = 0
    registered_by_id = ''

    class Meta:
        model = OrderMeet
