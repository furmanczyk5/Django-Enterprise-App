import csv

from django.core.management.base import BaseCommand

from conference.models.microsite import Microsite
from registrations.models import Attendee

HEADERS = ['ID', 'FIRST_NAME', 'LAST_NAME', 'EMAIL', 'COMPANY']


class Command(BaseCommand):
    help = """Write a CSV of Conference Attendees, based on its Microsite url path stem"""

    def add_arguments(self, parser):
        parser.add_argument(
            '-u',
            '--url-path-stem',
            dest='url_path_stem',
            nargs=1,
            required=True,
            help='The URL Path stem of the conference microsite from which to pull Attendees'
        )
        parser.add_argument(
            '-o',
            '--outfile',
            dest='outfile',
            nargs=1,
            required=True,
            help='The path of the filename to write the CSV'
        )

    def handle(self, *args, **options):
        outfile = options['outfile'][0]

        microsite = Microsite.objects.get(url_path_stem=options['url_path_stem'][0])
        event = microsite.event_master.content_live.event
        with open(outfile, 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(HEADERS)
            for x in Attendee.objects.filter(event=event):
                contact = x.contact
                row = [
                    contact.user.username,
                    contact.first_name,
                    contact.last_name,
                    contact.email,
                    contact.company
                ]
                writer.writerow(row)

        self.stdout.write(
            self.style.SUCCESS(
                "Wrote list of attendees of {} to {}".format(event, outfile)
            )
        )
