import random
import datetime
import pytz

from django.contrib.auth.models import User
from content.imis import *
from myapa.models import *
from myapa.templatetags.myapa_tags import get_django_purchase
from content.models import *
from store.models import *
from imis import models as im

def add_batch_to_imis(imis_batch_time):
    """
    attempt to write the missing transaction records to iMIS
    NOTE: THIS IS SET TO FIX ONLY THE MARCH TRANSACTIONS
    """

    # only attempt to write to imis if there is a transaction number.
    no_trans_number_errors = []
    other_errors = {}
    orders = Order.objects.filter(imis_batch_time=imis_batch_time)

    print('attempting to write imis orders transactions for orders with a count of: {0}'.format(orders.count()) )
    for order in orders:
        for purchase in order.purchase_set.all():
            try:
                # attempt to re-write the payment first
                payment = Payment.objects.filter(order=purchase.order).first()

                if payment:
                    ImisOrder(payment_instance=payment, payment_json=payment.imis_format()).publish_payment()

                # why was this built like this
                purchase_json = purchase.imis_format()
                purchase_instance = purchase

                ImisOrder(purchase_instance=purchase_instance, purchase_json=purchase_json).publish_purchase()

                print('imis payment/purchase written for user_id: {0} | purchase id: {1}'.format(purchase.user.username, purchase.id))
            except Exception as e:
                other_errors[purchase.order.id] = str(e)

    print('******** add_batch_to_imis completed *****')

    print('other errors: ' + str(other_errors))

def add_purchases_to_imis(product_code):
    """
    attempt to write the missing transaction records to iMIS
    NOTE: THIS IS SET TO FIX ONLY THE MARCH TRANSACTIONS
    """

    # only attempt to write to imis if there is a transaction number.
    no_trans_number_errors = []
    other_errors = {}
    purchases = Purchase.objects.filter(product__code=product_code, order__submitted_time__gte='2016-03-01', order__submitted_time__lte='2016-04-01').exclude(order__isnull=True)

    print('attempting to write imis purchase transactions for {0} with a count of: {1}'.format(product_code, purchases.count()) )

    for purchase in purchases:
        try:
            if not purchase.order.imis_trans_number:
                no_trans_number_errors.append(purchase.order.id)
                print('no imis_trans_number found for purchase id {0}'.format(purchase.order.id))
                pass

            # # attempt to re-write the payment first
            # payment = Payment.objects.filter(order=purchase.order).first()

            # if payment:
            # 	ImisOrder(payment_instance=payment, payment_json=payment.imis_format()).publish_payment()

            # why was this built like this
            purchase_json = purchase.imis_format()
            purchase_instance = purchase

            ImisOrder(purchase_instance=purchase_instance, purchase_json=purchase_json).publish_purchase()

            print('imis purchase written for user_id: {0} | purchase id: {1}'.format(purchase.user.username, purchase.id))
        except Exception as e:
            other_errors[purchase.order.id] = str(e)

    print('******** add_missing_products completed *****')
    print('purchases without a imis trans number: ' + str(no_trans_number_errors))

    print('other errors: ' + str(other_errors))

def reprocess_order(order_id):
    """
    submit the order to iMIS based on the order id passed
    NOTE: imis batch is statically set here.
    """

    try:
        order = Order.objects.get(id=order_id)

        order.imis_trans_number = None
        order.imis_batch_time = order.submitted_time.date()
        order.imis_batch = '_US160315'
        order.save()

        order = Order.objects.get(id=order.id)

        for purchase in order.purchase_set.all():
            purchase.process()

        for payment in order.payment_set.all():
            payment.process()

        print('puchase written no exceptions')
    except Exception as e:
        print(e)


# *************************************************************************************
# ************* BACK POPULATE IMIS TRANS NUMBERS TO DJANGO PURCHASES ******************
# *************************************************************************************

# GLOBALS
# These are the transaction_type whose Trans record will not have a product_type
NO_TRANS = ["PAY", "AR", "TR", "PP", '']
date = datetime.datetime(year=2016, month=7, day=1)
tz = pytz.timezone('UTC')
jul12016 = tz.localize(date)


# WHEN TESTING THIS LOCALLY THERE COULD BE AN APPLE TO ORANGES PROBLEM
# LOCAL POSTGRES <-> STAGING IMIS
def trans_numbers_to_django_purchases(trans_records=None, batch_num=0):
    i=0
    for t in trans_records:
        django_purchase = None
        i+=1
        print("BATCH NUM IS %s" % batch_num)
        print("Loop num is %s" % i)
        django_product = Product.objects.filter(
            imis_code=t.product_code, publish_status="PUBLISHED").first()
        print("django product is ", django_product)
        if django_product:
            print("django product id is ", django_product.id)
        try:
            user = User.objects.get(username=t.bt_id)
            print("user is ", user)
        except Exception as e:
            user = None
            print("Could not pull user with bt_id: %s" % t.bt_id)
            print("Exception: ", e)
        if django_product and user:
            django_purchase = Purchase.objects.filter(
                imis_trans_number__isnull=True,
                user=user,
                product=django_product,
                submitted_time__year=t.transaction_date.year,
                submitted_time__month = t.transaction_date.month,
                submitted_time__day=t.transaction_date.day
            ).exclude(order__isnull=True).exclude(quantity__lt=0)
        if not django_purchase:
            django_purchase = get_django_purchase(t)
            if django_purchase and django_purchase.imis_trans_number:
                django_purchase = None
            elif django_purchase:
                django_purchase = Purchase.objects.filter(
                    id=django_purchase.id
                )
        print("imis year is ", t.transaction_date.year)
        print("imis month is ", t.transaction_date.month)
        print("imis day is ", t.transaction_date.day)
        print("BEFORE django purchase is ", django_purchase)
        if django_purchase:
            django_purchase = django_purchase.first() if django_purchase.count() == 1 else None
        print("AFTER django purchase is ", django_purchase)
        if django_purchase:
            django_purchase.imis_trans_number = t.trans_number
            django_purchase.imis_trans_line_number = t.line_number
            django_purchase.imis_batch = t.batch_num
            django_purchase.imis_batch_date = t.transaction_date
            print("new trans number: ", django_purchase.imis_trans_number)
            django_purchase.save()
        print("******************************")
    print("---------------- END ----------------")
    print("###################################\n")
tnt=trans_numbers_to_django_purchases


def batch_trans_run(trans_queryset=None):
    if not trans_queryset:
        # lower=random.randint(501000,503373)
        # upper = lower+100
        print("\n**************** START ********************")
        trans_queryset=im.Trans.objects.filter(
            transaction_date__gte=jul12016).exclude(
            product_code='')#[lower:upper]
    batch_num = 0
    count = trans_queryset.count()
    step_size = 100
    for lim in range(0, count, step_size):
        lower = lim
        if (lim + step_size) < count:
            upper = lim + step_size
        else:
            upper = count
        batch = trans_queryset[lower:upper]
        batch_num+=1
        trans_numbers_to_django_purchases(batch, batch_num)
btr=batch_trans_run

def test_batch_limits():
    count = 51
    step_size = 100
    for lim in range(0, count, step_size):
        lower = lim
        if (lim + step_size) < count:
            upper = lim + step_size
        else:
            upper = count
        print("lower is ", lower)
        print("upper is ", upper)
tbl=test_batch_limits


def test_getting_purchases(num):
    # trans = im.Trans.objects.filter(transaction_type="PAY")
    trans = im.Trans.objects.exclude(
        # transaction_type__in=NO_TRANS).exclude(
        product_code='')
    count = trans.count()
    for i in range(0,num):
        index=random.randint(0,count-1)
        print("index is ", index)
        trans_record=trans[index]
        print("trans record trans num is ", trans_record.trans_number)
        print("trans record product code is ", trans_record.product_code)
        dp = get_django_purchase(trans_record)
        print("dp is ", dp)
        print("\n")
tgp=test_getting_purchases
