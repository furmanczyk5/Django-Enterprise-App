import requests

from content.utils import get_api_root, get_api_key_querystring
from myapa.models import Contact, Organization, ContactRelationship

# used with contact_queryset = Contact.objects.filter(first_name='', last_name='', contact_type="INDIVIDUAL").exclude(Q(company__isnull=True) | Q(company=''))

# from myapa.models import Contact
# from django.db.models import Q
# from _data_tools.myapa_organizations__2016_6 import *
# contact_queryset = Contact.objects.filter(first_name='', last_name='', contact_type="INDIVIDUAL").exclude(Q(company__isnull=True) | Q(company=''))
# update_contact_type(contact_queryset)

def update_contact_type(contact_queryset=[]):

    TOTAL = contact_queryset.count()
    count = 0

    print("TOTAL RECORDS: %s" % TOTAL)

    for org in contact_queryset:
        count += 1
        print(org.company, "%.2f%% complete" % ((count/TOTAL)*100.0) )
        if org.user.username:
            imis_contact = org.get_imis_contact()
            old_contact_type = org.contact_type
            contact_type = "ORGANIZATION" if imis_contact.get("company_record", False) else "INDIVIDUAL"
            if contact_type != old_contact_type:
                Contact.objects.filter(id=org.id).update(contact_type=contact_type)
                print("","%s -> %s" % (old_contact_type, contact_type))
            else:
                print("", "no change")
        else:
            print("", "------")

    print("Complete!")

def make_organization_relationships():
    """
    Script to import all company-contact relationships from imis...
    NOTES: 
        1. This only imports relationships for organizations(contacts with contact_type="ORGANIZATION") already existing in Postgres
        2. This will NOT delete records in postgres that don't exist in imis
    """

    organizations = Organization.objects.exclude(user__username__isnull=True).select_related("user")
    TOTAL = organizations.count()
    count = 0
    failures = [] # list of dicts

    print("TOTAL RECORDS: %s" % TOTAL)

    for org in organizations:

        count += 1

        print()
        print(org.user.username, org)

        api_root = get_api_root()
        path = "/organizations/%s/contacts" % org.user.username
        querystring = get_api_key_querystring()
        url = api_root + path + querystring

        r = requests.get(url)
        contacts_json = r.json()["data"]

        user_ids = [cj["webuserid"] for cj in contacts_json]
        admin_user_ids = [cj["webuserid"] for cj in contacts_json if cj.get("relation_type", "") == "ADMIN_I"]
        billing_user_ids = [cj["webuserid"] for cj in contacts_json if cj.get("relation_type", "") == "BILLING_I"]

        # update company for all user_ids
        if user_ids:

            # need to create contacts that don't exist
            try:
                contacts = Contact.objects.filter(user__username__in=user_ids).select_related("user")
                for user_id in user_ids:
                    if not user_id in [c.user.username for c in contacts]:
                        Contact.update_or_create_from_imis(user_id)
                        print("", "created contact/user", user_id)

                Contact.objects.filter(user__username__in=user_ids).update(company_fk=org)
                print("", "company contacts:", ",".join(user_ids))
            except:
                failures.append(dict(message="FAILED ADDING CONTACTS", org=org))
                print("","FAILED ADDING CONTACTS",org, contact)

            # create admin relationships for admins
            for user_id in admin_user_ids:
                try:
                    contact = Contact.objects.get(user__username=user_id)
                    admin_relationship, is_created = ContactRelationship.objects.get_or_create(target=contact, source=org, relationship_type="ADMINISTRATOR")
                    if is_created:
                        print("", "created admin:", user_id, contact)
                    else:
                        print("", "confirmed admin:", user_id, contact) # relationship already exists
                except:
                    failures.append(dict(message="FAILED ADDING ADMIN", org=org, contact=contact))
                    print("","FAILED ADDING ADMIN",org, contact)

            # create billing relationships for ... those billing people
            for user_id in billing_user_ids:
                try:
                    contact = Contact.objects.get(user__username=user_id)
                    billing_relationship, is_created = ContactRelationship.objects.get_or_create(target=contact, source=org, relationship_type="BILLING_I")
                    if is_created:
                        print("", "created billing:", user_id, contact)
                    else:
                        print("", "confirmed billing:", user_id, contact) # relationship already exists
                except:
                    failures.append(dict(message="FAILED ADDING BILLING", org=org, contact=contact))
                    print("","FAILED ADDING BILLING",org, contact)

        print("%.4f%% complete" % ((count/TOTAL)*100.0))
        print()

    print("Complete!")

    if failures:
        print()
        print()
        print("FAILURES")
        for failure in failures:
            print(failure)

