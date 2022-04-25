from django.core.management.base import BaseCommand
from myapa.models.proxies import Organization
from myapa.models.constants import DJANGO_IMIS_ORG_TYPES
from imis.models import OrgDemographics


class Command(BaseCommand):
    help = """Fix Organization.organization_type values for consistency"""

    def add_arguments(self, parser):
        parser.add_argument(
            '-n',
            '--dry-run',
            help='Show output of what the script would do but do not actually do it',
            dest='dry-run',
            action='store_true',
            default=False
        )

    def handle(self, *args, **options):
        # self.stdout.write(self.style.NOTICE(options['dry-run']))
        self.reconcile_org_types(dry_run=options['dry-run'])
        self.fill_in_blank_org_types(dry_run=options['dry-run'])
        self.change_django_types_to_imis(dry_run=options['dry-run'])

    def fill_in_blank_org_types(self, dry_run=False):
        """Fill in iMIS Org_Demographics records that have blank org_type
        values if those values in exist in Django"""
        limit = 1000
        offset = 0
        imis_records = OrgDemographics.objects.filter(org_type='')
        count = imis_records.count()
        while limit < count:
            ids = [x.id for x in imis_records[offset:limit]]
            orgs = Organization.objects.filter(organization_type__isnull=False, user__username__in=ids)
            for org in orgs:
                if not dry_run:
                    # print('bleep bloop')
                    od = OrgDemographics.objects.filter(id=org.user.username).update(
                        org_type=DJANGO_IMIS_ORG_TYPES.get(org.organization_type, '')
                    )
                else:
                    self.stdout.write(
                        self.style.NOTICE(
                            "Setting {} to org_type {} from Django type {}".format(
                                org.company,
                                DJANGO_IMIS_ORG_TYPES.get(org.organization_type, ''),
                                org.organization_type
                            )
                        )
                    )
            offset += 1000
            limit += 1000
            remaining = limit if limit < count else count
            self.stdout.write(
                self.style.NOTICE(
                    "Updated {} of {} blank iMIS Org_Demographics.org_type records with "
                    "corresponding Django Organization.organization_type record".format(
                        remaining, count
                    )
                )

            )

    def reconcile_org_types(self, dry_run=False):
        """Fix inconsistenceis with our Django Organization.organization_type values"""
        self.stdout.write(
            self.style.NOTICE(
                "Reconciling inconsistent Organization.organization_type values\n"
                "DRY RUN: {}".format(dry_run)
            )
        )

        q = Organization.objects.filter(organization_type='')
        self.stdout.write(
            self.style.NOTICE(
                "Changing {} empty strings records to None".format(q.count())
            )
        )
        if not dry_run:
            q.update(organization_type=None)

        q = Organization.objects.filter(organization_type="NP")
        self.stdout.write(
            self.style.NOTICE(
                "Changing {} NP records to NONPROFIT".format(q.count())
            )
        )
        if not dry_run:
            q.update(organization_type="NONPROFIT")

        q = Organization.objects.filter(organization_type="PR")
        self.stdout.write(
            self.style.NOTICE(
                "Changing {} PR records to PRIVATE".format(q.count())
            )
        )
        if not dry_run:
            q.update(organization_type="PRIVATE")

        q = Organization.objects.filter(organization_type="GV")
        self.stdout.write(
            self.style.NOTICE(
                "Changing {} GV records to GOV".format(q.count())
            )
        )
        if not dry_run:
            q.update(organization_type="GOV")

        q = Organization.objects.filter(organization_type="ED")
        self.stdout.write(
            self.style.NOTICE(
                "Changing {} ED records to ACADEMIC".format(q.count())
            )
        )
        if not dry_run:
            q.update(organization_type="ACADEMIC")

    def change_django_types_to_imis(self, dry_run=False):
        """Alter Django Organization.organization_type to reflect iMIS types"""
        for key, value in DJANGO_IMIS_ORG_TYPES.items():
            q = Organization.objects.filter(organization_type=key)
            self.stdout.write(
                self.style.NOTICE(
                    "Changing {} {} records to {}".format(q.count(), key, value)
                )
            )
            if not dry_run:
                q.update(organization_type=value)
