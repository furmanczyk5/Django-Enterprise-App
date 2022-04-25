from decimal import Decimal, getcontext, ROUND_HALF_UP

from django.conf import settings
from django.db import connections
from django.urls import reverse

from api.clients.bluepay import BluePay
from myapa.models.contact import Contact
from store.models.purchase import Purchase
from store.models import settings as store_settings

getcontext().rounding = ROUND_HALF_UP

ENVIRONMENT_NAME = getattr(settings, "ENVIRONMENT_NAME")


class UnsupportedEnvironment(Exception):
    pass


class MembershipPaymentDispatcher:

    def __init__(self, contact: Contact):
        self.contact = contact
        self._bill_frequency = None

        self.bill_period = self.get_bill_period()

        self.cart_items = None
        self._remove_non_membership_products_from_cart()

    def get_payment_gateway_client(self):
        raise NotImplementedError()

    def get_bill_frequency_choices(self):
        raise NotImplementedError()

    @property
    def bill_frequency(self):
        return self._bill_frequency

    @bill_frequency.setter
    def bill_frequency(self, value: int):
        self._bill_frequency = value

    def get_bill_period(self):
        query = """\
                DECLARE @BillPeriod INT
                SET @BillPeriod = dbo.fn_apa_imis_autodraft_billperiod(%s)
                SELECT @BillPeriod;
                """
        with connections['MSSQL'].cursor() as cursor:
            cursor.execute(query, [self.contact.user.username])
            return cursor.fetchone()[0]

    def _remove_non_membership_products_from_cart(self) -> None:
        Purchase.cart_items(self.contact.user).exclude(product__product_type__in=(
            store_settings.ProductTypes.CHAPTER.value,
            store_settings.ProductTypes.DIVISION.value,
            store_settings.ProductTypes.DUES.value,
            store_settings.ProductTypes.PUBLICATION_SUBSCRIPTION.value
        )).delete()
        self.cart_items = Purchase.cart_items(self.contact.user)

    def get_return_url(self) -> str:
        raise NotImplementedError()

    def get_dispatch_url_params(self) -> dict:
        return {}

    def get_dispatch_url(self) -> str:
        raise NotImplementedError()


class BluepayMembershipPaymentDispatcher(MembershipPaymentDispatcher):

    def get_payment_gateway_client(self):
        return BluePay(
            account_id=settings.BLUEPAY_ACCOUNT_ID,
            secret_key=settings.BLUEPAY_SECRET_KEY,
            mode=store_settings.BluePayMode.LIVE
            if ENVIRONMENT_NAME == 'PROD'
            else store_settings.BluePayMode.TEST
        )

    def get_bill_frequency_choices(self):
        return store_settings.AutodraftBillFrequency()

    def get_return_url(self) -> str:
        if ENVIRONMENT_NAME == 'STAGING':
            domain = 'https://staging.planning.org'
        elif ENVIRONMENT_NAME == 'PROD':
            domain = 'https://planning.org'
        else:
            raise UnsupportedEnvironment(ENVIRONMENT_NAME)
        path = reverse(
            'store:bluepay_return',
            kwargs=dict(
                username=self.contact.user.username,
                bill_frequency=self.bill_frequency,
                bill_period=self.bill_period
            )
        )
        return '{0}{1}'.format(domain, path)

    def get_dispatch_url_params(self) -> dict:
        return {
            'merchant_name': 'American Planning Association',
            'transaction_type': 'SALE',
            'accept_discover': 'Yes',
            'accept_amex': 'Yes',
            'protect_amount': 'Yes',
            'custom_id': self.contact.user.username,
            'rebilling': 'No',
            'return_url': self.get_return_url(),
        }

    def get_cart_total(self) -> int:
        cart_total = Purchase.cart_total(self.contact.user, self.cart_items)
        if cart_total is None:
            cart_total = 0
        return cart_total

    def get_initial_bill_amount(self) -> Decimal:
        query = """\
            DECLARE @ADAmount MONEY
            SET @ADAmount = dbo.[es_Calc_AD_Amount](%s, %s, %s)
            SELECT @ADAmount
        """
        total = Decimal('0.00')
        with connections['MSSQL'].cursor() as cursor:
            for item in self.cart_items:
                cursor.execute(query, [item.product_price.price, self.bill_frequency, self.bill_period])
                total += cursor.fetchone()[0]
        return total.quantize(Decimal("1.00"))

    def get_dispatch_url(self) -> str:
        client = self.get_payment_gateway_client()
        amount = str(self.get_initial_bill_amount())
        client.sale(amount=amount)
        client.receipt_url = self.get_return_url()
        params = self.get_dispatch_url_params()
        return client.generate_url(**params)
