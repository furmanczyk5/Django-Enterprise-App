from django.core.management.base import BaseCommand

from myapa.models.constants import CONTACT_RELATIONSHIP_TYPES
from myapa.models.contact_relationship import ContactRelationship
from myapa.models.proxies import IndividualContact, Organization


class Command(BaseCommand):
    help = """Creates a ContactRelationship between a Contact and an Organization"""

    def add_arguments(self, parser):
        parser.add_argument(
            '-c',
            '--contact',
            dest='contact',
            nargs=1,
            required=True,
            help="The APA ID (i.e., username) of the Contact to relate to an Organization"
        )

        parser.add_argument(
            '-o',
            '--organization',
            dest='organization',
            nargs=1,
            required=True,
            help="The APA ID (i.e. username) of the Organization to set up as the "
                 "source of the relationship with the Contact"
        )

        parser.add_argument(
            '-t',
            '--type',
            dest='relationship_type',
            nargs=1,
            default="ADMINISTRATOR",
            choices=[x[0] for x in CONTACT_RELATIONSHIP_TYPES],
            help="The type of relationship to create"
        )

    def handle(self, *args, **options):
        org = Organization.objects.get(user__username=options["organization"][0])
        contact = IndividualContact.objects.get(user__username=options["contact"][0])
        reltype = options["relationship_type"]
        cr, _ = ContactRelationship.objects.get_or_create(
            source=org,
            target=contact,
            relationship_type=reltype
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Successfully set up a {} relationship with {} as the source and {} "
                "as the target".format(
                    reltype,
                    cr.source,
                    cr.target
                )
            )
        )
