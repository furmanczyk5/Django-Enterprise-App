from imis.models import Product as ImisProduct
from store.models import Product as DjangoProduct, ProductPrice


def imis_learn_product_import(django_code="LRN_198", gl_account="470130-AF6301"):
    """
    This function is used to mass upload APA Learn products from Django into iMIS that follow the given code convention.
    Used on an annual basis

    :param code:
    :return:
    """
    apa_learn_products = DjangoProduct.objects.filter(code__istartswith = django_code)

    products_created = []

    for learn_product in apa_learn_products:


        # title = Member
        # title = Nonmember

        if not ImisProduct.objects.filter(product_code = learn_product.code).exists():
            # For the iMIS product:
            # price_1 = member pricing
            # price_2 = default pricing

            member_pricing = ProductPrice.objects.get(product = learn_product, title = "Member").price
            nonmember_pricing = ProductPrice.objects.get(product = learn_product, title = "Nonmember").price

            ImisProduct.objects.create(product_code = learn_product.code, product_major = learn_product.code, prod_type = "SALES",
                                       category = "APA_LEARN", title_key = learn_product.title[:60], title = learn_product.title[:60],
                                       description = learn_product.description, status = "A", unit_of_measure = "Each",
                                       price_1 = member_pricing, price_2 = nonmember_pricing, org_code = "APA", catalog_desc = learn_product.description,
                                       web_desc = learn_product.description, other_desc = learn_product.description, location = "DEFAULT",
                                       web_option = 2, promote = 0, income_account = gl_account)

            products_created.append(learn_product.code)


    return products_created



# dues use web_option = 1
# Insert into Product  ( Product.PRODUCT_CODE,Product.PRODUCT_MAJOR,Product.PROD_TYPE,Product.TITLE_KEY,Product.TITLE,Product.DESCRIPTION,Product.INCOME_ACCOUNT,Product.PRICE_1,Product.PRICE_2,Product.WEB_OPTION )
# values ( 'TEST','TEST','DUES','TEST DUES PRODUCT','TEST DUES PRODUCT','TEST DUES PRODUCT SETUP','410100-IM4010',5.00,10.00,1 )
