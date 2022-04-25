import os

import yaml
from django.conf import settings
from django.contrib.auth.models import User, Group, Permission, ContentType
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand

CONFIG_DIR = os.path.join(settings.BASE_DIR, "myapa/management/commands/login_group_config")


class Command(BaseCommand):
    help = """Fix inconsistent Group names"""

    def add_arguments(self, parser):
        parser.add_argument(
            '-i',
            '--invalidate-sessions',
            help='Whether or not to invalidate all staff sessions to force them to log in again',
            action='store_true',
            dest='invalidate',
            default=False
        )

    def handle(self, *args, **options):
        # self.fix_group_names()
        # self.delete_obsolete_groups()
        self.adjust_group_user_sets()
        # self.create_new_groups()
        # self.clear_all_staff_perms()
        self.adjust_group_permissions(clear_existing=True)
        if options['invalidate']:
            self.invalidate_staff_sessions()
        # self.jeffsoule()
        # self.add_staff_cms_editor()

    def fix_group_names(self):
        Group.objects.filter(name='aicp_cm').update(name='aicp-cm')
        Group.objects.filter(name='candidate_cm').update(name='candidate-cm')
        Group.objects.filter(name='reinstatement_cm').update(name='reinstatement-cm')
        Group.objects.filter(name='CITY-admin').update(name='CITY_PLAN-admin')
        Group.objects.filter(name='organization-store-admin').update(name='component-admin')
        self.stdout.write(
            self.style.SUCCESS(
                "Renamed groups!"
            )
        )

    def invalidate_staff_sessions(self):
        """
        Clear staff sessions to force them to log in again in an attempt to
        head off the avalanche of complaints from staff about
        "I LOST ALL MY DJANGO PERMISSIONS WTF"
        """
        self.stdout.write(
            self.style.WARNING(
                "Clearing all staff sessions"
            )
        )
        staff_user_ids = [str(x.id) for x in User.objects.filter(is_staff=True)]
        for ses in Session.objects.all():
            if str(ses.get_decoded().get('_auth_user_id')) in staff_user_ids:
                ses.delete()

    def delete_obsolete_groups(self):

        with open(os.path.join(CONFIG_DIR, "group_names_to_delete.yml")) as data:
            group_names_to_delete = yaml.load(data)["group_names_to_delete"]
        Group.objects.filter(name__in=group_names_to_delete).delete()
        self.stdout.write(
            self.style.SUCCESS(
                "Deleted obsolete groups!"
            )
        )

    def remove_perm_from_group(self, group_name, perm_codename):
        group = Group.objects.get(name=group_name)
        perms = Permission.objects.filter(codename=perm_codename)
        for perm in perms:
            group.permissions.remove(perm)
            self.stdout.write(
                self.style.NOTICE(
                    "Removed {} permission from {}".format(perm.codename, group.name)
                )
            )

    def clear_all_staff_perms(self):
        """Helper method for testing"""
        for group in Group.objects.filter(name__startswith='staff'):
            group.permissions.clear()
            group.user_set.clear()
        oca = Group.objects.get(name='onsite-conference-admin')
        oca.permissions.clear()
        oca.user_set.clear()

    def add_perm_to_group(self, group_name, perm_codename, clear_existing=False):
        group = Group.objects.get(name=group_name)
        if clear_existing:
            group.permissions.clear()
        perms = Permission.objects.filter(codename=perm_codename)
        for perm in perms:
            # only superusers can delete things
            if perm.codename.startswith('delete'):
                continue
            if perm not in group.permissions.all():
                group.permissions.add(perm)
                self.stdout.write(
                    self.style.NOTICE(
                        "Added {} permission to {}".format(perm.codename, group.name)
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "{} already has {}".format(group.name, perm.codename)
                    )
                )

    def load_yaml_file(self, relpath):
        with open(os.path.join(CONFIG_DIR, relpath)) as yamlfile:
            config = yaml.load(yamlfile)
            return config

    def grant_permissions(self, group_name, model_list):
        """
        Grant add/change permissions on the model list
        :param model_list: models to grant permission
        :return:
        """
        perm_codenames = []
        for model in model_list:
            perm_codenames.append("add_{}".format(model.split("_")[1]))
            perm_codenames.append("change_{}".format(model.split("_")[1]))
        for perm_code in perm_codenames:
            self.add_perm_to_group(group_name, perm_code)

    def adjust_group_permissions(self, clear_existing=False):
        group_configs = [
            ("component-admin", "staff_groups/component-admin.yml"),
            ("onsite-conference-admin", "staff_groups/onsite-conference-admin.yml"),
            ("staff", "staff_groups/staff.yml"),
            ("staff-aicp", "staff_groups/staff-aicp.yml"),
            ("staff-careers", "staff_groups/staff-careers.yml"),
            ("staff-communications", "staff_groups/staff-communications.yml"),
            ("staff-conference", "staff_groups/staff-conference.yml"),
            ("staff-editor", "staff_groups/staff-editor.yml"),
            ("staff-education", "staff_groups/staff-education.yml"),
            ("staff-events-editor", "staff_groups/staff-events-editor.yml"),
            ("staff-leadership", "staff_groups/staff-leadership.yml"),
            ("staff-marketing", "staff_groups/staff-marketing.yml"),
            ("staff-membership", "staff_groups/staff-membership.yml"),
            ("staff-policy", "staff_groups/staff-policy.yml"),
            ("staff-publications", "staff_groups/staff-publications.yml"),
            ("staff-research", "staff_groups/staff-research.yml"),
            ("staff-store-admin", "staff_groups/staff-store-admin.yml"),
            ("staff-wagtail-admin", "staff_groups/staff-wagtail-admin.yml"),
            ("JOBS-admin", "staff_groups/jobs-admin.yml")

        ]
        for group in group_configs:
            group_perms = self.load_yaml_file(group[1])
            if clear_existing:
                self.stdout.write(
                    self.style.WARNING(
                        "Clearing existing permissions for {}".format(group[0])
                    )
                )
                grp = Group.objects.get(name=group[0])
                grp.permissions.clear()
            self.grant_permissions(group[0], group_perms["app_models_granted"])
            self.add_users_to_group(group[0], *group_perms["staff_users"])

    # def adjust_staff_groups_perms(self):

    def remove_users_from_group(self, group_name, *usernames):
        users = User.objects.filter(username__in=usernames)
        self.stdout.write(
            self.style.WARNING(
                '-----------------{}: REMOVAL-------------------'.format(group_name)
            )
        )
        for user in users.order_by('username'):
            self.stdout.write(
                self.style.NOTICE(
                    "Removing {} | {} {} from the {} group".format(
                        user.username,
                        user.first_name,
                        user.last_name,
                        group_name
                    )
                )
            )
        Group.objects.get(name=group_name).user_set.remove(*users)

    def add_users_to_group(self, group_name, *usernames):

        users = User.objects.filter(username__in=usernames)
        self.stdout.write(
            self.style.SUCCESS(
                '-----------------{}: ADDITION-------------------'.format(group_name)
            )
        )
        for user in users.order_by('username'):
            self.stdout.write(
                self.style.SUCCESS(
                    "Adding {} | {} {} to the {} group".format(
                        user.username,
                        user.first_name,
                        user.last_name,
                        group_name
                    )
                )
            )
        group = Group.objects.get(name=group_name)
        if group_name.startswith('staff') or group_name == 'onsite-conference-admin':
            group.user_set.clear()
        group.user_set.add(*users)

    def adjust_group_user_sets(self):

        # clear out existing staff group
        # will get re-added on login if appropriate
        # usernames = [x.username for x in Group.objects.get(name='staff').user_set.all()]
        # self.remove_users_from_group('staff', *usernames)

        superusers = [
            '143742',  # Randall West
            '322218',  # Tim Johnson
            '352236',  # Cory Mollet
            '228416',  # Mark Ferguson
            '166306',  # Roy Carrington
            '358821',  # Michael Sullivan
            '275301',  # Andy Krakos
            '261337',  # Phillip Lowe
            '362663',  # Uriel Saenz
            '384472',  # Marylu Granja
        ]
        self.stdout.write(
            self.style.NOTICE(
                "Updating superusers..."
            )
        )
        User.objects.update(is_superuser=False)
        User.objects.filter(username__in=superusers).update(is_superuser=True)
        self.stdout.write(
            self.style.SUCCESS("Done!")
        )

    def jeffsoule(self):
        # https://americanplanning.atlassian.net/browse/DEV-5459
        self.stdout.write(
            self.style.WARNING(
                "Adding About APA page access for Department-of-One Jeffery Soule, AICP"
            )
        )
        jsoule = User.objects.get(username='006987')
        perms = Permission.objects.filter(codename__in=('add_aboutpage', 'change_aboutpage'))
        for perm in perms:
            if jsoule not in perm.user_set.all():
                perm.user_set.add(jsoule)

    def create_new_groups(self):
        """
        Create the new staff-events-editor group. Same as staff-conference but with publish permissions
        :meth:`content.admin_publishable.AdminPublishableMixin.user_has_publish_permission`
        :return:
        """
        Group.objects.get_or_create(name='staff-events-editor')

    def add_staff_cms_editor(self):
        grp, _ = Group.objects.get_or_create(name='staff-cms-editor')
        editor_usernames = (
            "081605",  # Ralph Jassen
            "119585",  # Cynthia Cheski
            "288069"   # Kelly Wilson
        )
        editors = User.objects.filter(username__in=editor_usernames)
        grp.user_set.clear()
        grp.user_set.add(*editors)
        for user in editors:
            self.stdout.write(
                self.style.SUCCESS(
                    "Added {} | {} {} to the staff-cms-editor group".format(
                        user.username,
                        user.first_name,
                        user.last_name
                    )
                )
            )


def print_models(app_label):
    """
    Utility function for printing YAML-friendly ContentTypes by app_label
    :param app_label: str
    :return:
    """
    for i in ContentType.objects.filter(app_label=app_label).order_by('model'):
        print('- {}_{}'.format(app_label, i.model))
