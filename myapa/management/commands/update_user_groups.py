import csv
import os

from django.contrib.auth.models import User
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from myapa.permissions.utils import update_user_groups



class Command(BaseCommand):

    help = "Update user groups for a given CSV file of user IDs. The CSV file should have the "
    "user IDs in the first column, with no header row."

    def add_arguments(self, parser):

        parser.add_argument(
            '-c',
            '--csv',
            help="Absolute path to a CSV file containing user IDs",
            required=True,
            dest='csvfile'
        )

    def handle(self, *args, **options):
        with open(options['csvfile']) as f:
            reader = csv.reader(f)
            for row in reader:
                try:
                    user_id = row[0]
                    user = User.objects.get(username=user_id)
                except (IndexError, User.DoesNotExist):
                    continue
                self.stdout.write(self.style.NOTICE("Updating groups for {}".format(user)))
                update_user_groups(user)
