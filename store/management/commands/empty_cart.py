from django.core.management.base import BaseCommand, CommandError

from store.models.product import Product
from store.models.purchase import Purchase


DIVISION_PRODUCT_CODES = [
    i.code for i in Product.objects.filter(
        product_type="DIVISION",
        publish_status="PUBLISHED"
    )
]


class Command(BaseCommand):
    help = """Remove erroneous new-member-priced pending Purchases from regular members' carts"""

    def add_arguments(self, parser):
        # parser.add_argument('', nargs='+', type=int)
        pass

    def handle(self, *args, **options):
        ids_to_delete = self.get_purchase_ids_to_delete()
        Purchase.objects.filter(id__in=ids_to_delete).delete()

    def get_division_products(self):
        division_prods = Product.objects.filter(
            publish_status="PUBLISHED",
            code__in=DIVISION_PRODUCT_CODES
        )

        return division_prods

    def get_purchase_ids_to_delete(self):
        ids_to_delete = []
        div_prods = self.get_division_products()
        for prod in div_prods:
            purchases = prod.purchases.filter(order__isnull=True, product_price__price=10)
            for purch in purchases:
                if not purch.contact.is_new_membership_qualified:
                    self.stdout.write(self.style.NOTICE(purch))
                    ids_to_delete.append(purch.id)
        return ids_to_delete
