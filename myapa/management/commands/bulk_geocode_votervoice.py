import random
import time
from math import ceil

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db.models.functions import Length

from imis.models import NameAddress, CustomAddressGeocode
from imis.utils.addresses import get_primary_address
from myapa.models.constants import UNITED_STATES
from myapa.models.proxies import IndividualContact
from ui.utils import NORTH_AMERICAN_GEONAME_CODES


def address_equal(django_address, imis_address):
    """
    Test if a Django address and iMIS address are "equal"
    :param django_address: :class:`content.models.base_address.BaseAddress`
    :param imis_address: :class:`imis.models.NameAddress`
    :return: bool
    """
    django_fields = ['address1', 'city', 'state', 'zip_code']
    imis_fields = ['address_1', 'city', 'state_province', 'zip']
    django_address = {k: v or '' for (k, v) in django_address.__dict__.items() if k in django_fields}
    imis_fields = {k: v or '' for (k, v) in imis_address.__dict__.items() if k in imis_fields}
    return django_address['address1'] == imis_fields['address_1'] \
        and django_address['city'] == imis_fields['city'] \
        and django_address['state'] == imis_fields['state_province'] \
        and django_address['zip_code'] == imis_fields['zip']


class Command(BaseCommand):
    help = """Bulk geocode contacts with VoterVoice and save their district info
    to iMIS Name table"""

    def add_arguments(self, parser):
        parser.add_argument(
            '-m',
            '--method',
            help='Which method to run, validate_addresses or write_districts',
            dest='method'
        )
        parser.add_argument(
            '-s',
            '--state-half',
            help='Which half of states (first or second) to split up the amount of addresses'
                 'to validate/get districts',
            dest='half',
            choices=('first', 'second')
        )
        parser.add_argument(
            '-c',
            '--cleanup',
            action='store_true',
            help='Run the one-time cleanup script that populates the new CustomAddressGeocode '
                 'iMIS table',
            default=False,
            dest='cleanup'
        )
        parser.add_argument(
            '--max-changed',
            help='The maximum number of changed iMIS CustomAddressGeocode records to try to update at once',
            type=int,
            default=1000,
            dest='max-changed'
        )

    def get_state_halves(self):
        self.states = sorted([x for x in NORTH_AMERICAN_GEONAME_CODES.values() if x not in
                              ('AB', 'BC', 'MB', 'NB', 'NL', 'NT', 'NS', 'NU', 'ON', "PE", 'QC', 'SK', 'YT')])
        midpoint = ceil(len(self.states) / 2)
        self.states_first_half = self.states[:midpoint]
        self.states_second_half = self.states[midpoint:]

    def generate_contacts(self):
        contacts = IndividualContact.objects.select_related(
            'user'
        ).filter(
            status='A',
            country=UNITED_STATES,
            voter_voice_checksum__isnull=True,
            user__username__isnull=False,
            user__groups=Group.objects.get(name='member')
        )
        if self.half:
            contacts = contacts.filter(state__in=getattr(self, 'states_{}_half'.format(self.half)))
        return contacts.iterator()

    def validate_addresses(self):
        for contact in self.generate_contacts():
            time.sleep(1)
            self.stdout.write(
                self.style.NOTICE(
                    "Validating {} | {}".format(contact.user.username, contact.get_full_street_address())
                )
            )
            contact.validate_address()

    def validate_addresses_imis(self):
        cags = CustomAddressGeocode.objects.annotate(
            checksum_length=Length('votervoice_checksum')
        ).filter(
            checksum_length=0
        )
        for cag in cags.all():
            self.stdout.write(
                self.style.NOTICE(
                    "Updating {}".format(cag.id)
                )
            )
            name_address = NameAddress.objects.filter(id=cag.id, address_num=cag.address_num).first()
            if name_address is None or name_address.country != 'United States':
                continue
            geocode = name_address.validate_address()
            if geocode is not None:
                geocode.get_districts()

    def handle_imis_changed(self, **options):
        changed_records = CustomAddressGeocode.objects.filter(changed=True)
        for record in changed_records[:options['max-changed']]:
            name_address = NameAddress.objects.filter(address_num=record.address_num).first()
            if name_address is None or name_address.country.upper() != 'UNITED STATES':
                self.stderr.write(
                    self.style.WARNING(
                        "No NameAddress record found with address_num {} or address is not in the United States".format(record.address_num)
                    )
                )
                continue
            self.stdout.write(
                self.style.NOTICE(
                    "Updating {} | {}".format(name_address.id, name_address.address_num)
                )
            )
            geocode = name_address.validate_address()
            if geocode is not None and geocode.votervoice_checksum:
                geocode.get_districts()

    def bulk_geocode_imis(self):
        name_addresses = NameAddress.objects.filter(country='United States')
        if self.half:
            name_addresses = name_addresses.filter(
                state_province__in=getattr(self, 'states_{}_half'.format(self.half))
            )
        for name_address in name_addresses.all():
            if CustomAddressGeocode.objects.filter(address_num=name_address.address_num).exists():
                self.stdout.write(
                    self.style.WARNING(
                        "{} | {} already exists; skipping".format(name_address.id, name_address.address_num)
                    )
                )
                continue
            self.stdout.write(
                self.style.NOTICE(
                    "Updating {} | {}".format(name_address.id, name_address.address_num)
                )
            )
            geocode = name_address.validate_address()
            if geocode is not None:
                geocode.get_districts()

    def write_districts(self):
        contacts = IndividualContact.objects.filter(voter_voice_checksum__isnull=False)
        if self.half:
            contacts = contacts.filter(state__in=getattr(self, 'states_{}_half'.format(self.half)))
        for contact in contacts.iterator():
            time.sleep(1)
            self.stdout.write(
                self.style.NOTICE(
                    "Getting district information for {} | {}".format(
                        contact.user.username,
                        contact.get_full_street_address()
                    )
                )
            )
            contact.get_districts()

    def write_districts_imis(self):
        #for cag in CustomAddressGeocode.objects.exclude(votervoice_checksum='').iterator():
        for cag in random.sample(list(CustomAddressGeocode.objects.exclude(votervoice_checksum='').all()), 100):
            self.stdout.write(
                self.style.NOTICE(
                    "Updating district info for {} | {}".format(cag.id, cag.address_num)
                )
            )
            time.sleep(0.5)
            cag.get_districts()

    def cleanup(self):
        contacts = IndividualContact.objects.filter(
            voter_voice_checksum__isnull=False
        ).select_related(
            'user'
        )
        for contact in contacts.iterator():
            addr = get_primary_address(contact.user.username)
            if addr is None:
                continue
            geocode = CustomAddressGeocode.objects.filter(
                address_num=addr.address_num,
                id=contact.user.username
            ).first()
            if geocode and (geocode.latitude and geocode.longitude):
                continue
            if address_equal(contact, addr):
                name = contact.get_imis_name()
                if geocode is not None and name is not None:
                    geocode.longitude = contact.longitude or 0
                    geocode.latitude = contact.latitude or 0
                    geocode.votervoice_checksum = contact.voter_voice_checksum or ''
                    geocode.us_congress = name.us_congress or ''
                    geocode.state_senate = name.state_senate or ''
                    geocode.state_house = name.state_house or ''
                    geocode.changed = False
                    geocode.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            "Updated {} in Custom_Address_Geocode".format(contact)
                        )
                    )

    def handle(self, *args, **options):
        if options['cleanup']:
            self.cleanup()
        else:
            self.half = options.get('half')
            self.get_state_halves()
            getattr(self, options['method']).__call__(**options)
