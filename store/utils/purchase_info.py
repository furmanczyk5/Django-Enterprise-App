import logging

from imis.event_function import EventFunction


logger = logging.getLogger(__name__)

REGULAR = 'Regular'
SOLDOUT = 'Soldout'
WAITLIST = 'Waitlist'


class PurchaseInfo(object):
    def __init__(self, product, user, function=None):
        self.imis_code = product.imis_code
        self.username = user.username
        self.function = self.set_function(function)

    def set_function(self, function):
        return function if function else EventFunction(self.username, self.imis_code)

    def get(self):
        return {
            'max_quantity': self.regular_capacity(),
            'regular_remaining': self.regular_remaining(),
            'total_remaining': self.total_remaining(),
            'user_total_purchased': self.user_tickets_purchased(),
            'user_total_in_cart': self.user_tickets_in_cart(),
            'user_total': self.total_user_tickets(),
            'user_allowed_to_add': self.user_allowed_to_add(),
            'user_allowed_to_purchase': self.user_allowed_to_purchase(),
            'max_quantity_per_person': self.function.regular_max_quantity_per_registrant,
            'product_sale_status': self.product_sale_status(),
        }

    def allows_waitlist(self):
        return self.function.regular_capacity > 0

    def regular_capacity(self):
        return self.function.regular_capacity

    def product_sale_status(self):
        # LOGIC IS DIFFERENT NOW. SOLDOUT MEANS WAIT LIST KICKS IN
        if self.soldout():
            return WAITLIST

        if self.regular_remaining():
            return REGULAR
        else:
            return WAITLIST

    def total_remaining(self):
        return self.regular_remaining()

    def regular_remaining(self):
       return max(
           0,
           self.regular_capacity() - self.function.total_regular_purchased)

    def user_allowed_to_purchase(self):
        if self.regular_remaining():
            return self.regular_user_allowed_to_purchase()
        else:
            return 0

    def regular_user_allowed_to_purchase(self):
        return min(
            self.function.regular_max_quantity_per_registrant,
            self.regular_remaining()
        )

    def user_allowed_to_add(self):
        return max(0, self.user_allowed_to_purchase() - self.total_user_tickets())

    def soldout(self):
        max_tickets = (
            self.function.regular_capacity
        )
        tickets_sold = self.tickets_sold()
        return tickets_sold >= max_tickets

    def tickets_sold(self):
        return (
            self.function.total_regular_purchased# +
        )

    def total_user_tickets(self):
        return self.user_tickets_purchased() + self.user_tickets_in_cart()

    def user_tickets_in_cart(self):
        return self.function.user_regular_in_cart

    def user_tickets_purchased(self):
        return self.function.user_regular_purchased
