import logging
from decimal import Decimal
from urllib.parse import urlencode

from django.conf import settings
from django.db import connections
from django.utils import timezone
from psycopg2.extensions import QuotedString
from sentry_sdk import capture_message

from content.mail import Mail
from content.models import ContentStatus
from imis.models import Trans
from myapa.models.contact import Contact
from myapa.permissions.utils import update_user_groups
from store.models import Order, OrderStatuses, Payment
from store.models.settings import AutodraftBillPeriod

logger = logging.getLogger(__name__)


class PaymentProcessor:

    def __init__(self, user_id: str, payment_data: dict, checkout_source="CART"):
        self.user_id = user_id
        self.payment_data = payment_data
        self.checkout_source = checkout_source
        self.contact = Contact.objects.get(user__username=self.user_id)

        # whether or not to call submit_to_imis when calling Order.process
        self.submit_to_imis = False

        self.user = self.contact.user
        self.order = None
        self.payment = None
        self.trans = None

    def is_annual(self) -> bool:
        return str(self.payment_data.get('bill_period')) == str(AutodraftBillPeriod.ANNUAL)

    def get_purchase_total(self) -> Decimal:
        purchase_total = self.order.purchase_total()
        if self.is_annual():
            return Decimal(purchase_total).quantize(Decimal('1.00'))
        else:
            purchase_total = Decimal(purchase_total) * Decimal(self.payment_data.get('bill_frequency', 1))
            return Decimal(purchase_total).quantize(Decimal('1.00'))

    def get_monthly_payment_amount(self, context: dict):
        try:
            divisor = int(context['number_of_payments'])
        except (TypeError, ValueError):
            capture_message('number_of_payments is not an integer: {}'.format(context['number_of_payments']), level='error')
            divisor = 1
        return self.order.purchase_total() / divisor

    def get_mail_context(self) -> dict:
        context = {
            'order': self.order,
            'number_of_payments': self.payment_data.get('bill_period'),
            'purchase_total': self.get_purchase_total(),
            'monthly_payment_amount': Decimal('0.00'),
            'balance': Decimal('0.00')
        }
        if not self.is_annual():
            monthly_payment_amount = self.get_monthly_payment_amount(context)
            context['monthly_payment_amount'] = Decimal(monthly_payment_amount).quantize(Decimal('1.00'))
            context['balance'] = context['purchase_total'] - context['monthly_payment_amount']
        return context

    def create_order(self):
        self.order = Order.objects.create(
            user=self.user,
            submitted_user_id=self.user_id,
            order_status=OrderStatuses.SUBMITTED.value,
            submitted_time=timezone.now()
        )
        self.order.add_from_cart(self.user)

    def create_payment(self):
        self.payment = Payment.objects.create(
            status=ContentStatus.PENDING.value,
            order=self.order,
            user=self.user,
            contact=self.contact,
            amount=self.get_amount(),
            method="CC",
            pn_ref=self.get_pn_ref(),
            submitted_time=timezone.now()
        )

    def process(self):
        self.payment.process()
        for purchase in self.order.get_purchases():
            purchase.process(checkout_source=self.checkout_source)
            purchase.send_confirmation()

        self.order.process(submit_to_imis=self.submit_to_imis)
        self.order.send_confirmation(recurring=True)

    def get_trans_number(self):
        purchase = self.order.purchase_set.first()
        if purchase is None:
            logger.error("No Purchase record found for Order: {}".format(self.order))
            return
        if purchase.imis_trans_number:
            return purchase.imis_trans_number
        else:
            logger.debug("Searching for Trans record in iMIS for Order: {}".format(self.order))
            order_date = self.order.submitted_time.date()
            trans = Trans.objects.filter(
                bt_id=purchase.user.username,
                product_code__startswith=purchase.product.imis_code,
                transaction_date__year=order_date.year,
                transaction_date__month=order_date.month,
                transaction_date__day__in=(order_date.day - 1, order_date.day)
            ).first()
            if trans is not None:
                return trans.trans_number
            else:
                logger.error("No Trans record found for Order: {}".format(self.order))

    def get_redirect_url(self) -> str:
        trans_number = self.get_trans_number()
        if trans_number is None:
            url = "/myapa/orderhistory/"
            data = {"msg": "Thank you for your order!"}
        else:
            url = "/store/order_confirmation/"
            data = {"order_id": trans_number}
        return "{0}?{1}".format(url, urlencode(data))

    def update_user(self):
        self.contact.sync_from_imis()
        update_user_groups(self.user)

    def get_pn_ref(self) -> str:
        raise NotImplementedError()

    def get_amount(self) -> Decimal:
        raise NotImplementedError()

    def run(self):
        self.create_order()
        self.create_payment()
        self.process()
        self.update_user()


class BluepayPaymentProcessor(PaymentProcessor):

    def get_pn_ref(self) -> str:
        return self.payment_data['RRNO']

    def get_amount(self) -> Decimal:
        return Decimal(self.payment_data['AMOUNT'])

    def get_django_autodraft_cart_submit_parameters(self):
        return [
            self.user_id,
            self.get_amount(),
            self.payment_data['CARD_TYPE'],
            self.payment_data['PAYMENT_ACCOUNT'][-4:],
            self.payment_data['CARD_EXPIRE'],
            self.payment_data['RRNO'],
            self.payment_data['bill_frequency'],
            self.payment_data['bill_period'],
            self.payment_data['AUTH_CODE'],
        ]

    def get_django_purchases_table_values(self):
        return [(
            getattr(x.product, 'imis_code', ''),
            getattr(x.option, 'code', ''),
            x.product_price.imis_reg_class or '',
            x.quantity,
            x.product_price.price,
            x.agreement_response_1 or '',
            x.agreement_response_2 or '',
            x.agreement_response_3 or ''
        )
            for x in self.order.get_purchases()]

    def get_django_purchases_sql(self):
        # XXX: This could be vulnerable to SQL injection. Make sure nothing that gets entered here ever comes
        #  from user input.
        values = self.get_django_purchases_table_values()
        sql = ''
        for line in values:
            sql += '('
            count = len(line)
            for index, item in enumerate(line):
                item = QuotedString(str(item))
                if index < (count - 1):
                    sql += '{}, '.format(item)
                else:
                    sql += '{}'.format(item)
            sql += '),'
        sql = sql[:-1] + ';'
        return sql

    def get_django_autodraft_cart_submit_query(self):

        django_purchases_sql = self.get_django_purchases_sql()

        # https://github.com/mkleehammer/pyodbc/issues/808

        query = """\
        DECLARE @DjangoPurchases AS DjangoPurchasesTable;
        INSERT INTO @DjangoPurchases (ProductCode, ProductOption, RegistrantClass, Quantity, Price, AgreementResponse1, AgreementResponse2, AgreementResponse3) VALUES {0}

        EXEC [dbo].[django_autodraft_cart_submit]
            @WebUserID=%s,
            @PaymentAmount=%s,
            @PaymentCardType=%s,
            @PaymentLastFour=%s,
            @PaymentExpirationDate=%s,
            @PaymentMethodKey=%s,
            @BillFrequency=%s,
            @BillPeriod=%s,
            @PaymentAuthCode=%s,
            @DjangoPurchases=@DjangoPurchases;

        """.format(django_purchases_sql)
        return query

    def exec_django_autodraft_cart_submit(self):
        query = self.get_django_autodraft_cart_submit_query()
        parameters = self.get_django_autodraft_cart_submit_parameters()
        if settings.ENVIRONMENT_NAME != 'PROD':
            capture_message("Autodraft query: {}\nAutodraft parameters: {}".format(query, parameters), level='debug')
        with connections['MSSQL'].cursor() as cursor:
            cursor.execute(query, parameters)

    def send_auto_renewal_confirmation_email(self):
        if self.is_annual():
            mail_code = "AUTO_RENEWAL_CONFIRMATION_ANNUAL"
        else:
            mail_code = "AUTO_RENEWAL_CONFIRMATION_MONTHLY"
        Mail.send(mail_code, self.contact.email, self.get_mail_context())

    def run(self):
        super().run()
        self.exec_django_autodraft_cart_submit()
        self.send_auto_renewal_confirmation_email()
