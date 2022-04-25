import datetime, pytz, uuid, django
django.setup()

from django.contrib.auth.models import Group
from store.models import Product, ProductPrice


def create_sale_prices():
    chicago=pytz.timezone("America/Chicago")
    end_2017 = datetime.datetime(2018,1,1,0,0,tzinfo=chicago)
    products = Product.objects.filter(content__contenttagtype__tags__id__in=(1392, 1394))
    member_group = Group.objects.get(name="member")
    for product in products.filter(publish_status="DRAFT"):
        old_prices = product.prices.exclude(end_time=end_2017)
        old_prices.update(status="I", include_search_results=False)

        new_prices = product.prices.filter(end_time=end_2017)
        new_prices.delete()

        member_price = ProductPrice.objects.create(
            product = product, 
            publish_status="DRAFT",
            title="APA Member",
            price = 4.99,
            option_code = "STREAMING_INDIVIDUAL",
            end_time = end_2017,
            include_search_results = True,
            priority = 0,
            )
        member_price.required_groups.set([member_group])
        member_price.publish_uuid = uuid.uuid4()
        # member_price.

        nonmember_price= ProductPrice.objects.create(
            product = product, 
            publish_status="DRAFT",
            title="List",
            price = 24.99,
            option_code = "STREAMING_INDIVIDUAL",
            end_time = end_2017,
            include_search_results = True,
            priority = 1,
            )
        nonmember_price.publish_uuid = uuid.uuid4()
        print(product.content.master.id, product.content.title)
        product.content.publish()
        product.content.solr_publish()