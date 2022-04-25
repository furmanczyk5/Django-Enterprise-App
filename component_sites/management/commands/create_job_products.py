import pytz
import datetime

from django.core.exceptions import MultipleObjectsReturned
from django.core.management.base import BaseCommand
from wagtail.wagtailcore.models import Site as Wagtail_Site

from store.models import Product, ContentProduct, ProductPrice
from store.models.settings import ProductTypes
from submissions.models import Period, Category
from component_sites.models import ProviderSettings

base_product_prices = [
    {
        'title': "Professional (various levels of experience) - 4 weeks online",
        'price': 0.00,
        'code': "PROFESSIONAL_4_WEEKS_0",
        'priority': 0
    },
    {
        'title': "Entry Level only (zero to one year of experience; not AICP) - 4 weeks online",
        'price': 0.00,
        'code': "ENTRY_LEVEL_0",
        'priority': 1
    },
    {
        'title': "Internship only (temporary position; no experience required) - 4 weeks online",
        'price': 0.00,
        'code': "INTERN_0",
        'priority': 2
    },
]


class Command(BaseCommand):
    help = "This command completes the backend for job posting for a wagtail site."
    requires_system_checks = False

    def add_arguments(self, parser):
        parser.add_argument('-lp', '--list_products',
                            action='store_true',
                            help='List all current job products(to see if you need to create a new one '
                                 'or update an existing one.',
                            )
        parser.add_argument('-ls', '--list_sites',
                            action='store_true',
                            help='List all current wagtail sites(for attaching to the job product).',
                            )
        parser.add_argument('-t', '--ad_title',
                            type=str,
                            help="Name of Ad Product, 'Job Ad, ______'",
                            )
        parser.add_argument('-a', '--ad_abbr',
                            type=str,
                            help="Site abbreviation for the product code, i.e. 'CHAPT_FL' or 'SUSTAIN'"
                            )
        parser.add_argument('-st', '--site_type',
                            type=str,
                            help="Declares the site type, either Chapter(c) or Division(d)",
                            )

    def handle(self, *args, **options):
        if options['list_products']:
            self.list_all_job_products()
        elif options['list_sites']:
            self.list_all_sites()
        else:
            ad_title = options['ad_title'] if options['ad_title'] else input("Please enter the title of your Job Ad "
                                                                             "w/o chpt or div; e.g. 'Florida; ")
            ad_abbr = options['ad_abbr'] if options['ad_abbr'] else input("Please enter the abbrev of your Job Ad for "
                                                                          "the code; e.g. 'CHAPT_FL' or 'SUSTAIN'; ")
            if options['site_type'] and options['site_type'].lower() == 'c':
                chapter = True
            elif options['site_type'] and options['site_type'].lower() == 'd':
                chapter = False
            else:
                chapter_in = input('You must enter a site type, either Chapter(c) or Division(d)')
                if chapter_in.lower() in ['c', 'd']:
                    chapter = True if chapter_in.lower() == 'c' else False
                else:
                    print("You've entered an invalid response.")
                    chapter = None

            if chapter is not None:
                self.title = 'Job Ad, %s %s' % (ad_title, 'Chapter' if chapter else 'Division')
                self.code = 'JOB_AD_%s' % (ad_abbr)
                proceed = input("Is %s the name of the job product you'd like to create code?(y/N)" % self.code)
                if proceed.lower() == 'y':
                    self.job_cont_prod, created = ContentProduct.objects.get_or_create(product__code=self.code,
                                                                                       publish_status='DRAFT')
                    self.job_cont_prod.title = self.title
                    self.job_cont_prod.description = self.title
                    self.job_cont_prod.save()
                    self.job_prod = self.get_or_create_product()
                    self.job_cont_prod.product = self.job_prod
                    self.job_prod.content = self.job_cont_prod
                    self.job_prod.save()
                    self.job_cont_prod.save()

                    ProductPrice.objects.filter(product=self.job_prod).delete()  # clear existing productprices
                    for price in base_product_prices:
                        self.make_job_product_price(price)
                    self.category = self.make_category()
                    self.period = self.make_period()

                    self.job_cont_prod.save()
                    self.job_prod.save()
                    self.job_cont_prod.publish()


    def get_or_create_product(self):
        prod_dict = {
            'product_type': ProductTypes.JOB_AD.value,
            'gl_account': '200954-000000',
            'imis_code': self.code,
            'code': self.code,
            'content': self.job_cont_prod
        }

        prod = Product.objects.filter(**prod_dict).first()
        if not prod:
            prod = Product.objects.create(**prod_dict)
        return prod

    def make_job_product_price(self, prod_dict=None):
        if prod_dict:
            prod_price, created = ProductPrice.objects.get_or_create(product=self.job_prod, max_quantity=1.00, **prod_dict)

    def make_category(self):
        cat_dict = {
            "title": self.title,
            "description": self.title,
            "product_master": self.job_cont_prod.master
        }
        category, created = Category.objects.update_or_create(code=self.code, defaults=cat_dict)
        return category

    def make_period(self):
        begin_time = (datetime.datetime.now() - datetime.timedelta(days=365))
        end_time = (datetime.datetime.now() + datetime.timedelta(days=10 * 365))

        period_dict = {
            'begin_time': begin_time,
            'end_time': end_time,
            'content_type': 'PAGE',
            'title': self.title
        }
        period, created = Period.objects.update_or_create(category=self.category, defaults=period_dict)
        return period

    def list_all_sites(self):
        all_sites = Wagtail_Site.objects.all()
        print("Site Title", (50 * ' '),
              ' | Site Name  ', (40 * ' '),
              ' | Chapter/Division | Job Product')
        print(160 * '-')
        for site in all_sites:
            if 'chapter' in str(site.root_page.content_type).lower():
                chapter = True
            else:
                chapter = False
            print(site.root_page.title, (int(60 - len(str(site.root_page.title))) * ' '), ' |',
                  site.site_name, (int(51 - len(str(site.site_name))) * ' '), ' |',
                  'Chapter ' if chapter else 'Division', '        |',
                  ProviderSettings.for_site(site).job_product)

        return all_sites

    def list_all_job_products(self):
        all_job_prods = ContentProduct.objects.filter(code__contains='JOB_AD_', publish_status='PUBLISHED')
        print('\n\n')
        print("Job Product                             | ProdMasterID | Job Product Code")
        print("-" * 80)

        for job_prod in all_job_prods:
            print(job_prod.title, int(38 - len(str(job_prod.title))) * ' ', '|',
                  job_prod.master.id, int(11 - len(str(job_prod.master.id))) * ' ', '|',
                  job_prod.code, int(20 - len(str(job_prod.code))) * ' ', '|',
                  )
        return all_job_prods
