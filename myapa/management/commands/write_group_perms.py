import csv
import os

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from imis.models import Name


class Command(BaseCommand):
    help = """Output a CSV of current user groups and their permissions"""

    def add_arguments(self, parser):
        # parser.add_argument(
        #     '-f, --outfile',
        #     nargs=1,
        #     type=str,
        #     help='The full path and filename of the CSV to write'
        # )
        parser.add_argument(
            '-d',
            nargs=1,
            type=str,
            help="A directory to write all django admin group names with their users "
                 "(one CSV file per group name)"
        )

    def write_all_perms(self, **options):
        header = ['GROUP_NAME', 'USER_COUNT', 'DJANGO_ADMIN_PERMISSIONS']
        with open(options['--outfile'][0], 'w') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(header)
            for group in Group.objects.order_by('name'):
                writer.writerow([group.name, group.user_set.count(), ''])
                for perm in group.permissions.order_by('content_type__app_label'):
                    writer.writerow(
                        [
                            '',
                            '',
                            '{} >> {} >> {}'.format(
                                perm.content_type.app_label,
                                perm.content_type,
                                perm.name
                            )
                        ]
                    )

    def write_admin_perms(self, **options):
        """Write out a list of users with Django admin permissions"""
        header = ['ID', 'FIRST_NAME', 'LAST_NAME', 'EMAIL', 'COMPANY']
        for group in Group.objects.order_by('name'):
            if group.permissions.exists():
                with open(
                        os.path.join(
                            options['d'][0], '{}.csv'.format(group.name)
                        ), 'w') as outfile:
                    writer = csv.writer(outfile)
                    writer.writerow(header)
                    for user in group.user_set.order_by('username'):
                        writer.writerow(
                            [
                                user.username,
                                user.first_name,
                                user.last_name,
                                user.email,
                                user.contact.company
                            ]
                        )

    def write_current_staff_perms(self, **options):
        header = ['ID', 'FIRST_NAME', 'LAST_NAME', 'CURRENT_PERMS']
        staff = Group.objects.get(name='staff')
        with open(
            os.path.join(
                options['d'][0], 'current_staff_perms.csv'
            ), 'w') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(header)
            for u in staff.user_set.all():
                writer.writerow([u.username, u.first_name, u.last_name, ''])
                for perm in u.get_all_permissions():
                    writer.writerow(
                        [
                            '',
                            '',
                            '',
                            '{} >> {} >> {}'.format(
                                perm.content_type.app_label,
                                perm.content_type,
                                perm.name
                            )
                        ]
                    )


    def handle(self, *args, **options):
        # self.write_all_perms(**options)
        # self.write_admin_perms(**options)
        self.write_current_staff_perms(**options)


def write_current_staff_perms(path):
    header = ['ID', 'FIRST_NAME', 'LAST_NAME', 'CURRENT_PERMS']
    imis_staff = Name.objects.only('id').filter(co_id__in=('050501', '119523'))
    staff = User.objects.filter(username__in=[x.id for x in imis_staff])
    with open(
        os.path.join(
            path, 'current_staff_perms.csv'
            ), 'w') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(header)
        for u in staff:
            writer.writerow([u.username, u.first_name, u.last_name, ''])
            for perm in sorted(u.get_all_permissions()):
                writer.writerow(
                    [
                        '',
                        '',
                        '',
                        perm
                    ]
                )
