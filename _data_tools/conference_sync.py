import django
django.setup()

import warnings
warnings.filterwarnings('ignore')

from registrations.models import Attendee


def sync_attendees():
    attendees = Attendee.objects.filter(purchase__product__code="EVENT_16CONF", status="A")

    for a in attendees:

        # print(imis_contact)
        try:
            imis_contact, address_list = a.contact.sync_from_imis()
            if "informal" in imis_contact and imis_contact["informal"]:
                a.badge_name = imis_contact["informal"]
            print("UPDATED: " + a.contact.user.username + " | " + str(a.contact) )
        except Exception as e:
            print("===============================================================================")
            print("ERROR - COULD NOT SYNC: " + a.contact.user.username + " | " + str(a.contact))
            print(str(e))
            print("===============================================================================")



