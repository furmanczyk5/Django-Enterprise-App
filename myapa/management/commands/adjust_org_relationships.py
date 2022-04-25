from collections import Counter as coll_counter

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.test import Client
from django.utils import timezone

from imis.models import Relationship, Counter
from myapa.models.contact_relationship import ContactRelationship


class Command(BaseCommand):
    help = """Adjust Organization relationship records by moving or deleting data to/from iMIS and Django"""

    def add_arguments(self, parser):
        # parser.add_argument('', nargs='+', type=int)
        pass

    def delete_cm_admins_from_imis(self):
        query = Relationship.objects.filter(
            relation_type__in=("CM_C", "CM_I")
        ).exclude(
            updated_by="DJANGO"
        )
        self.stdout.write(
            self.style.WARNING(
                "Preparing to delete {} CM_C/CM_I records from iMIS Relationship".format(query.count())
            )
        )
        query.delete()
        self.stdout.write(
            self.style.SUCCESS(
                "Done!"
            )
        )

    def copy_existing_billing_admins_to_imis(self):

        query = get_contact_relationships("BILLING_I")
        self.stdout.write(
            self.style.WARNING(
                "Preparing to copy {} BILLING_I records from Django to iMIS as ADMIN_I relation types".format(len(query))
            )
        )
        # Django records source/targets are incorrectly reversed,
        # so when copying to iMIS we flip them back
        imis_records = [
            Relationship(
                id=x.target.user.username,
                relation_type="ADMIN_I",
                target_id=x.source.user.username,
                target_name='',
                target_relation_type="ADMIN_C",
                title='',
                functional_title='',
                status='',
                last_string='',
                date_added=timezone.now(),
                updated_by='DJANGO',
                seqn=Counter.create_id('Relationship'),
                group_code=''
            )
            for x in query
        ]
        Relationship.objects.bulk_create(imis_records)

        self.stdout.write(
            self.style.SUCCESS(
                "Done!"
            )
        )

    def copy_existing_administrators_to_imis(self):
        query = get_contact_relationships("ADMINISTRATOR")
        self.stdout.write(
            self.style.WARNING(
                "Preparing to copy {} ADMINISTRATOR records from Django to iMIS as "
                "CM_I relation types".format(len(query))
            )
        )
        imis_records = []
        for x in query:
            # ADMIN_I
            # rel_admin = Relationship(
            #     id=x.target.user.username,
            #     relation_type="ADMIN_I",
            #     target_id=x.source.user.username,
            #     target_name='',
            #     target_relation_type="ADMIN_C",
            #     title='',
            #     functional_title='',
            #     status='',
            #     last_string='',
            #     date_added=timezone.now(),
            #     updated_by='DJANGO',
            #     seqn=Counter.create_id('Relationship'),
            #     group_code=''
            # )
            # imis_records.append(rel_admin)
            # CM_I
            rel_cm = Relationship(
                id=x.target.user.username,
                relation_type="CM_I",
                target_id=x.source.user.username,
                target_name='',
                target_relation_type="CM_C",
                title='',
                functional_title='',
                status='',
                last_string='',
                date_added=timezone.now(),
                updated_by='DJANGO',
                seqn=Counter.create_id('Relationship'),
                group_code=''
            )
            imis_records.append(rel_cm)

        Relationship.objects.bulk_create(imis_records)

        self.stdout.write(
            self.style.SUCCESS(
                "Done!"
            )
        )

    def handle(self, *args, **options):
        self.delete_cm_admins_from_imis()
        self.copy_existing_billing_admins_to_imis()
        self.copy_existing_administrators_to_imis()


def get_existing_admins_from_imis():
    """Try to prevent duplicate ADMIN_I/ADMIN_C records
    from being created"""

    imis_admins = Relationship.objects.filter(
        relation_type="ADMIN_I",
        target_relation_type="ADMIN_C"
    ).exclude(
        Q(id='') | Q(target_id='')
    )
    return imis_admins


def flip_contactrelationships(relationship_type, delete=True):
    """
    Flip the ContactRelationship source/targets in Django
    :param relationship_type: str, choice of :const:`myapa.models.constants.CONTACT_RELATIONSHIP_TYPES`
    :param delete: bool, whether to delete the old records after they've been flipped
    :return:
    """
    crs = ContactRelationship.objects.filter(relationship_type=relationship_type)

    flipped_admin_crs = [ContactRelationship(
        source=x.target,
        target=x.source,
        relationship_type=relationship_type
    ) for x in crs]

    ContactRelationship.objects.bulk_create(flipped_admin_crs)
    if delete:
        crs.delete()


def get_contact_relationships(relationship_type):
    query = ContactRelationship.objects.filter(
        relationship_type=relationship_type,
        target__user__isnull=False,
        source__user__isnull=False
    )
    # filter out those that already exist in iMIS with ADMIN_I/ADMIN_C relationship types
    existing_imis_admins = get_existing_admins_from_imis()
    source_ids = [x.id for x in existing_imis_admins]
    crs = [x for x in query if x.target.user.username not in source_ids]
    return crs


def get_cr_member_types():
    query = ContactRelationship.objects.filter(relationship_type="BILLING_I")
    data = {
        'source': coll_counter([x.source.member_type for x in query]),
        'target': coll_counter([x.target.member_type for x in query])
    }
    return data


def test_existing_authenticate_provider_mixin():
    """
    Test if existing records of "ADMINISTRATOR" in ContactRelationship
    can still access views inheriting from AuthenticateProviderMixin
    given the new setup (querying the Relationships table in iMIS instead)
    """
    client = Client()
    crs = ContactRelationship.objects.filter(relationship_type="ADMINISTRATOR")
    contacts_losing_access = []
    for c in crs:
        target = c.target
        if not target.user:
            continue
        client.force_login(target.user)
        resp = client.get('/cm/provider/')
        if hasattr(resp, "template_name"):
            if 'cm/newtheme/provider/dashboard.html' not in resp.template_name:
                print("{} as a CR TARGET unable to access existing provider dashboard".format(target))
                contacts_losing_access.append(target)
        elif "Create a New Provider Account" in resp.content.decode('utf-8'):
            print("{} Does not have ADMIN_I relationship in iMIS".format(target))
            contacts_losing_access.append(target)

        client.logout()

    with open('contacts_losing_access.txt', 'w') as outfile:
        outfile.writelines(contacts_losing_access)


def get_mistmatches():
    distinct_admins = set()
    candidates = []
    crs = ContactRelationship.objects.filter(relationship_type="ADMINISTRATOR").order_by('-target__created_time')
    for x in crs:
        if x.target.user:
            if x.target.user.username not in distinct_admins:
                distinct_admins.add(x.target.user.username)
                candidates.append(x)
    mismatches = []
    for x in candidates:
        rel = Relationship.objects.filter(id=x.target.user.username, relation_type__in=("ADMIN_I", "CM_I")).last()
        if rel:
            if x.source.user:
                if x.source.user.username != rel.target_id:
                    mismatches.append(x)
    return mismatches


def write_mismatches(mismatches, path):
    headers = ['admin', 'django_org', 'imis_org']
    with open(path, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        for x in mismatches:
            rel = Relationship.objects.filter(id=x.target.user.username, relation_type__in=('ADMIN_I', 'CM_I')).last()
            name = Name.objects.filter(id=rel.target_id).first()
            if name is not None:
                row = [x.target, x.source, '{} | {}'.format(name.id, name.company)]
            else:
                row = [x.target, x.source, 'NO IMIS ORG RECORD for {}'.format(rel.target_id)]
            writer.writerow(row)
