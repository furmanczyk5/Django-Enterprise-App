from decimal import Decimal

from django.db.models import Avg, Max, Min, Sum
from django.contrib.admin.utils import NestedObjects

from exam.open_water_api_utils import OPEN_WATER_DETAILS_TO_PRODUCT_CODE, OPEN_WATER_COUPON_CODE
from store.models import ContentProduct, Product, ProductPrice
from imis import models as im

# SCRIPT TO CREATE DJANGO OPEN WATER PRODUCTS:

# CHANGE THIS TO CREATE DJANGO PRODUCTS FOR DIFFERENT OPEN WATER INSTANCES:
aicp_fees_dict = OPEN_WATER_DETAILS_TO_PRODUCT_CODE.get("aicp_instance", None)
gl_account = "440100-AU6202"

# IF PRICE AMOUNTS CHANGE BUT PRICE STRUCTURE STAYS THE SAME, THE AMOUNTS COULD BE CHANGED HERE
# AND UPDATED WITH METHODS BELOW
OPEN_WATER_PRICES = {
    # REGULAR PRICES
    'OW_AICP_APP_FEE': ('70.00', '0.00'),
    'OW_AICP_REG_ESS': ('220.00', '0.00'),
    'OW_AICP_EX_ESSY': ('290.00', '0.00'),
    'OW_AICP_EXAM_ST': ('220.00', '0.00'),
    'OW_AICP_TRANSFR': ('100.00', '0.00'),
    'OW_AICP_APPEAL': ('100.00', '0.00'),
    'OW_AICP_CAN_ENR': ('35.00', '0.00'),
    'OW_AICP_CAN_EX': ('100.00', '0.00'),
    'OW_AICP_CANDTRX': ('0.00', '0.00'),
    'OW_AICP_CERT_AP': ('375.00', '0.00'),
    'OW_EX_CERT_AP': ('445.00', '0.00'),
    # CANDIDATE SCHOLARSHIP
    'OW_AICP_CES_SCH': ('105.00', '0.00'),
    'OW_AICP_CXESSCH': ('175.00', '0.00'),
    # TRADITIONAL SCHOLARSHIP
    'OW_AICP_ES_SCHL': ('70.00', '0.00'),
    'OW_AICP_XES_SCH': ('140.00', '0.00'),
    # REGISTRATION SCHOLARSHIP
    'OW_AICP_CEX_SCH': ('70.00', '0.00'),
    'OW_AICP_EX_SCHL': ('70.00', '0.00')
}

# NO NOT LIKE THIS ONE IMIS PRODUCT PER OW PRICE (INCLUDING SCHOLARSHIP)
# BUT THIS COULD BE USED TO UPDATE IMIS PRICES
# def write_scholarship_prices_to_imis():
#     for imis_product_code in OPEN_WATER_PRICES.keys():
#         imis_product = im.Product.objects.get(product_code=imis_product_code)
#         prices = OPEN_WATER_PRICES[imis_product_code]
#         # IF SOMEDAY WE WANT TO UPDATE REGULAR PRICES:
#         # regular_price = prices[0]
#         # imis_product.price_1 = regular_price
#         # imis_product.save()
#         if len(prices) == 2:
#             scholarship_price = Decimal(prices[1])
#             imis_product.price_2 = scholarship_price
#             imis_product.save()
#         print("FINISHED %s" % imis_product_code)
# wspti=write_scholarship_prices_to_imis

def verify_imis_prices():
    for imis_product_code in OPEN_WATER_PRICES.keys():
        imis_product = im.Product.objects.get(product_code=imis_product_code)
        print("%s %s %s %s" % (imis_product_code, imis_product.price_1, imis_product.price_2, OPEN_WATER_PRICES[imis_product_code]))

# 3 product types: cand enroll, exam app, exam reg -- we have to align these
# content (contentproduct?) title, description, code, publish status,
# product: code, visibility, product type, imis code, gl account // pointers: content
# product price: title, price, visibility, priority, begin_time, end_time // pointers: product

def create_open_water_django_products(fees_dict):
    for fee in fees_dict.items():
        fee_name_details = fee[0]
        imis_product_code = fee[1]
        imis_product = im.Product.objects.get(product_code=imis_product_code)
        # print(fee_name_details)
        if type(fee_name_details) is str:
            fee_name_django = fee_name_details.split(',')[0]
        else:
            fee_name_django = None
        if fee_name_django:
            print("fee name: ", fee_name_django)
            print("fee imis product code: ", imis_product_code)
            # 1. create Content 2. create Product 3. create ProductPrice
            fee_content_product, fee_cp_created = ContentProduct.objects.get_or_create(
                title=fee_name_django,
                description=fee_name_django,
                code=imis_product_code,
                publish_status="DRAFT")
            # product: code, product type, imis code, gl account, publish status // pointers: content
            print("Content Product: ", fee_content_product)
            print("CP created: ", fee_cp_created)
            fee_product, fee_p_created = Product.objects.get_or_create(
                code=imis_product_code,
                content=fee_content_product,
                # this hooks it up to the store product proxy checkout code that runs at purchase time
                # we might have to make a new product type, or else is there a default that won't run any code?
                product_type='EXAM_APPLICATION',
                imis_code=imis_product_code,
                gl_account=gl_account,
                max_quantity=Decimal('1.00'),
                publish_status="DRAFT")
            print("fee product: ", fee_product)
            print("fp created: ", fee_p_created)
            django_prices = OPEN_WATER_PRICES[imis_product_code]
            print("django_prices is ", django_prices)
            print("imis price equals django price? ", imis_product.price_1 == django_prices[0])
            for i, price in enumerate(django_prices):
                print("django price in price loop is: ", price)
                print("priority: ", i + 1)
                print("fee name django in price loop is ", fee_name_django)
                full_price_title = fee_name_django + ', Coupon' if (i == 1 and Decimal(price) == 0) else fee_name_django
                print("full price title is ", full_price_title)
                fee_product_price, fee_pp_created = ProductPrice.objects.get_or_create(
                    title=full_price_title,
                    # price=imis_product.price_1,
                    price=price,
                    product=fee_product,
                    publish_status="DRAFT")
                # TEST THIS FIX FOR THE CAND TRANSFER PRODUCT WITH TWO 0 PRICES:
                if fee_pp_created:
                    if price == 0 and full_price_title.find(", Coupon") >= 0:
                        fee_product_price.code = OPEN_WATER_COUPON_CODE
                    fee_product_price.priority = i + 1
                    fee_product_price.save()
                print("fee product price: ", fee_product_price)
                print("fee product price title: ", fee_product_price.title)
                print("fee pp created: ", fee_pp_created)
            fee_content_product.publish()
cowdp = create_open_water_django_products
# CALL LIKE THIS:
# cowdp(aicp_fees_dict)


# _data_tools/candidate.py has good example script for creating products
def delete_open_water_django_products(fees_dict):
    for fee in fees_dict.items():
        queryset = ContentProduct.objects.filter(code=fee[1])
        print("queryset is ", queryset)
        collector = NestedObjects(using='default') # or specific database
        for obj in queryset:
            collector.collect([obj])
            to_delete = collector.nested()
            print("IF WE DELETE django contentproduct THIS WILL BE DELETED: ")
            print(to_delete)
        num_objs_deleted, num_deletions_per_obj_dict = queryset.delete()
        # queryset.delete()
        print("code is ", fee[1])
        print("num_objs_deleted is ", num_objs_deleted)
        print("num_deletions_per_obj_dict is ", num_deletions_per_obj_dict)
        print()
dowdp=delete_open_water_django_products
# CALL LIKE THIS:
# dowdp(aicp_fees_dict)

def verify_open_water_django_products():
    for imis_product_code in OPEN_WATER_PRICES.keys():
        try:
            product = Product.objects.get(imis_code=imis_product_code, publish_status="PUBLISHED")
            # print("%s %s %s %s" % (product.content.title, imis_product_code, product.prices.all(), OPEN_WATER_PRICES[imis_product_code]))
            print(product.content.title,[ppri.price for ppri in product.prices.all()],
                imis_product_code, OPEN_WATER_PRICES[imis_product_code], "\n")
        except Exception as e:
            print(e,imis_product_code,"\n")
vowdp=verify_open_water_django_products

def delete_scholarship_prices_from_django_products():
    products = Product.objects.filter(imis_code__startswith="OW_")
    print("num products: ", products.count())
    for p in products:
        prices = p.prices.all()
        if prices.count() > 1:
            print("More than 1 price: ", p.imis_code)
            print("BOTH PRICES: ",prices)
            # delete the lower productprice
            amounts = prices.values('id', 'price')
            lowest = amounts[0]
            for a in amounts:
                lowest = a if a['price'] < lowest['price'] else lowest
            lowest_obj = prices.get(id=lowest['id'])
            print("lowest price obj is ", lowest_obj)
            collector = NestedObjects(using='default') # or specific database
            collector.collect([lowest_obj])
            to_delete = collector.nested()
            print("IF WE DELETE PRODUCTPRICE THIS WILL BE DELETED: ")
            print(to_delete)
            lowest_obj.delete()
    return products
dpfd=delete_scholarship_prices_from_django_products

def fix_zero_dollar_price_titles():
    products = Product.objects.filter(imis_code__startswith="OW_", publish_status="DRAFT")
    print("num products: ", products.count())
    for p in products:
        prices = p.prices.all()
        for pri in prices:
            if pri.price == 0:
                if pri.title.find(', Coupon') < 0:
                    print("price amount is: ", pri.price)
                    print("old price title: ", pri.title)
                    pri.title = pri.title + ', Coupon'
                    pri.save()
                    print("new price title: ", pri.title)
                    p.content.publish()
                    print("\n")

def fix_zero_dollar_price_codes():
    products = Product.objects.filter(imis_code__startswith="OW_", publish_status="DRAFT")
    print("num products: ", products.count())
    for p in products:
        prices = p.prices.all()
        for pri in prices:
            if pri.price == 0:
                if not pri.code or pri.code.find('aicpcode') < 0:
                    print("price amount is: ", pri.price)
                    print("price title: ", pri.title)
                    print("price code: ", pri.code)
                    pri.code = 'aicpcode'
                    pri.save()
                    print("new price code: ", pri.code)
                    p.content.publish()
                    print("\n")

def mark_dupe_product_prices_for_deletion():
    products = Product.objects.filter(imis_code__startswith="OW_")#, publish_status="DRAFT")
    print("num products: ", products.count())
    for p in products:
        print("product is ", p)
        print(p.prices.all())
        prices = p.prices.filter(price=0).order_by('id')
        print("length of $0 prices is ", prices.count())
        for i,pri in enumerate(prices):
            # print(pri.id)
            # print(pri)
            if i == 1:
                print("price title is: ", pri.title)
                print("price amount is: ", pri.price)
                print("price status: ", pri.status)
                pri.status = 'X'
                pri.save()
                print("new status is ", pri.status)
                # p.content.publish()
        print("\n")
mdppfd=mark_dupe_product_prices_for_deletion

def what_will_be_deleted(some_instance):
    if some_instance:
        collector = NestedObjects(using='default') # or specific database
        collector.collect([some_instance])
        to_delete = collector.nested()
        print(to_delete)
    else:
        print("object is none -- nothing deleted")

def delete_dupe_product_prices():
    products = Product.objects.filter(imis_code__startswith="OW_")#, publish_status="DRAFT")
    print("num products: ", products.count())
    for p in products:
        print("product is ", p)
        prices = p.prices.filter(price=0, status="X").order_by('id')
        for pri in prices:
            print("WHAT WILL BE DELETED: ")
            what_will_be_deleted(pri)
            pri.delete()
        print("\n")
ddpp=delete_dupe_product_prices

def flip_ow_price_priorities():
    products = Product.objects.filter(imis_code__startswith="OW_", publish_status="DRAFT")
    print("num products: ", products.count())
    for p in products:
        print("product is ", p)
        prices = p.prices.filter(price=0, title__contains=", Coupon")
        for pri in prices:
            pri.priority = 3
            pri.save()
        prices = p.prices.exclude(price=0, title__contains=", Coupon")
        for pri in prices:
            pri.priority = 2
            pri.save()
        prices = p.prices.filter(price=0, title__contains=", Coupon")
        for pri in prices:
            pri.priority = 1
            pri.save()
        p.content.publish()
        print("\n")
fopp=flip_ow_price_priorities
