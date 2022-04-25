from django.core.management.base import BaseCommand
from store.models import Product


class Command(BaseCommand):
    help = 'Deactivates all LEARN_COURSE products and associated content'

    def handle(self, *args, **options):

        lc_products = Product.objects.filter(product_type="LEARN_COURSE")
        for prod in lc_products:
            try:
                self.stdout.write(
                    self.style.NOTICE(
                        "Deactivating {}: {} and associated content".format(prod.code, prod.title)
                    )
                )
                prod.status = 'I'
                prod.save()
                prod.options.update(status='I')
                prod.prices.update(status='I')
                prod.content.status = 'I'
                prod.content.save()
                prod.content.publish()
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(
                        "Error deactivating {}: {}\n{}".format(prod.code, prod.title, exc)
                    )
                )
