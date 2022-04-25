from store.models import ContentProduct, Product, ProductPrice
from django.db.models import Q

def get_newmember_price(product):
    if product.code == "MEMBERSHIP_MEM":
        price = 75.00
    elif product.code == "MEMBERSHIP_AICP":
        price = 70.00
    elif product.product_type == "CHAPTER":
        price = 20.00
    elif product.product_type == "DIVISION":
        price = 10.00
    elif product.code == "SUB_EJOUR":
        price = 18.00
    elif product.code == "SUB_ZONING":
        price = 47.50
    else:
        price = 0.95
    return price
        
def create_join_product_pricing():
    """
    Creates student and new member pricing for join/renew products
        For July 2017 role out
    """
    
    # these get K, KK, and L pricing  
    student_products = ContentProduct.objects.filter(
        Q(product__product_type__in=["CHAPTER", "DIVISION"]) | Q(product__code__in=["MEMBERSHIP_AICP"]),
        publish_status="DRAFT")

    for content_product in student_products:
        
        print(content_product.product.code)
        
        published_product_id = Product.objects.only("id").get(
            publish_status="PUBLISHED", 
            content__publish_uuid=content_product.publish_uuid).id

        for salary_code in ["K", "KK"]:
            draft_price, created = ProductPrice.objects.update_or_create(
                product=content_product.product,
                code=salary_code,
                defaults={"price":0.00, "publish_status":"DRAFT"})
            
            draft_price.publish(replace=("product_id", published_product_id))
            
        draft_price, created = ProductPrice.objects.update_or_create(
            product=content_product.product,
            code="L",
            defaults={"price":get_newmember_price(content_product.product), "publish_status":"DRAFT"})
            
        draft_price.publish(replace=("product_id", published_product_id))


    # this gets K, and KK pricing
    student_only_products = ContentProduct.objects.filter(
        product__code__in=["MEMBERSHIP_STU","MEMBERSHIP_AICP_PRORATE"],
        publish_status="DRAFT")
    
    for content_product in student_only_products:
    
        print(content_product.product.code)

        published_product_id = Product.objects.only("id").get(
            publish_status="PUBLISHED", 
            content__publish_uuid=content_product.publish_uuid).id

        for salary_code in ["K", "KK"]:
            draft_price, created = ProductPrice.objects.update_or_create(
                product=content_product.product,
                code=salary_code,
                defaults={"price":0.00, "publish_status":"DRAFT"})

            draft_price.publish(replace=("product_id", published_product_id))
        
    
    # this gets L pricing
    newmember_products = ContentProduct.objects.filter(
        product__code__in=["MEMBERSHIP_MEM", "SUB_EJOUR", "SUB_ZONING"],
        publish_status="DRAFT")
    
    for content_product in newmember_products:
        
        print(content_product.product.code)

        published_product_id = Product.objects.only("id").get(
            publish_status="PUBLISHED", 
            content__publish_uuid=content_product.publish_uuid).id

        draft_price, created = ProductPrice.objects.update_or_create(
            product=content_product.product,
            code="L",
            defaults={"price":get_newmember_price(content_product.product), "publish_status":"DRAFT"})

        draft_price.publish(replace=("product_id", published_product_id))
    
    # NOTE: NEED NEW pricing logic for aicp prorated dues MEMBERSHIP_AICP_PRORATE
    #  8(?) tiered prices for newmembers (salary code L)
    #  2 $0.00 prices for students (salary codes K and KK, already done above) 
    
    
