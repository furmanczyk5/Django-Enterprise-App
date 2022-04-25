from .db_accessor import DbAccessor


def get_value(row, field):
    return int(getattr(row, field, 0))


class EventFunction(object):

    def __init__(self, user_id, imis_code, row=None):
        row = self.set_row(user_id, imis_code, row)
        self.event_function_id = imis_code
        self.regular_capacity = get_value(row, 'RegularCapacity')
        # self.standby_capacity = get_value(row, 'StandbyCapacity')
        self.regular_max_quantity_per_registrant = get_value(row, 'RegularMaxQuantityPerRegistrant')
        # self.standby_max_quantity_per_registrant = get_value(row, 'StandbyMaxQuantityPerRegistrant')

        self.total_regular_purchased = get_value(row, 'TotalRegularPurchased')

        # self.total_standby_purchased = get_value(row, 'TotalStandbyPurchased')
        self.user_regular_purchased = get_value(row, 'UserRegularPurchased')
        # self.user_standby_purchased = get_value(row, 'UserStandbyPurchased')
        self.user_regular_in_cart = get_value(row, 'UserRegularInCart')
        # self.user_standby_in_cart = get_value(row, 'UserStandbyInCart')
        # NOT SURE IF WE ADD user_registered here or not ?? depends how we get it
        # we need to look at Orders - Order_Lines or Order_Meet in imis

    def set_row(self, user_id, imis_code, row):
        if not row:
            try:
                query = 'EXEC django_event_function @Code=?, @WebUserID=?'
                row = DbAccessor().get_row(query, [imis_code, user_id])
            except:
                row = {}

        return row


class EventFunctions(object):
    def __init__(self, user_id, meeting):
        query = 'EXEC django_event_function @Code=?, @WebUserID=?'
        rows = DbAccessor().get_rows(query, [meeting + '%', user_id])
        self.functions = [
            EventFunction(user_id, row.ProductCode, row)
            for row in rows
        ]

    def get(self):
        return self.functions

