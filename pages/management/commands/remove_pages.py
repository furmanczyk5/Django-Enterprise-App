from django.core.management.base import BaseCommand, CommandError

from pages.models import Page


class Command(BaseCommand):
    help = """Remove Published Pages without Drafts"""

    def add_arguments(self, parser):
        parser.add_argument('page_list', nargs = '+', type = str)
        parser.add_argument(
            '--force',
            action = 'store_true',
            dest = 'force',
            help = 'Do not prompt the user before removing a matching lone Page.',
            )

    def handle(self, *args, **options):
        count = 0
        urls = str(options['page_list'][0]).split(', ')
        
        print(urls)
        for url in urls:
            qs = Page.objects.filter(url=url)       
            lone_page = None 
            if qs.count() == 1:
                lone_page = qs.first()
            elif qs.count() == 3:
                if qs[0].title == qs[1].title:
                    lone_page = qs[2]
                elif qs[1].title == qs[2].title:
                    lone_page = qs[0]
                elif qs[0].title == qs[2].title:
                    lone_page = qs[1]
            else:
                self.stdout.write("%s has %s Entries. None Removed" % (url, qs.count()))

            if lone_page:        
                if options['force']:  
                    self.stdout.write("Deleting %s" % lone_page)
                    lone_page.delete()
                    count += 1    
                else:
                    rm = input("Would you like to delete "+ lone_page.title+ "?(Y/n)")
                    if rm == 'Y':
                        lone_page.delete()
                        count += 1
                    else:        
                        self.stdout.write("Did not Delete")
        self.stdout.write("Deleted %s Pages" % count)
        return count
        