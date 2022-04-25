from datetime import datetime, timedelta

from django.contrib.auth.models import Group
from django.utils import timezone
import pytz

from myapa.models import Contact
from myapa.permissions.groups import GROUP_DEFINITIONS


# TO DO... maybe this should all just move to the imis sync module????

def get_contact_for_groups(user):
    """
    Returns a myapa.models.Contact instance, with the the necessary related models pre-queried
    for checking group conditions.
    """
    contact = Contact.objects.filter(user=user) \
        .select_related("company_fk__user") \
        .prefetch_related("purchases_received") \
        .prefetch_related("purchases_received__product") \
        .prefetch_related("contactrelationship_as_target") \
        .prefetch_related("contactrole") \
        .prefetch_related("contactrole__content__contenttagtype__tags").first()

    contact._set_cached_subscription_attributes()

    setattr(contact, "_cached_imis_activities", [
            a for a in contact.get_imis_activities()
        ])

    setattr(contact, "_cached_imis_order_lines", contact.get_imis_order_lines())

    setattr(contact, "_cached_imis_name", contact.get_imis_name())

    setattr(contact, "_cached_imis_name_address", contact.get_imis_name_address())

    functional_title = getattr(contact._cached_imis_name, "functional_title", None)

    setattr(contact, "functional_title", functional_title)

    advocacy = contact.get_imis_advocacy()
    grassrootsmember = getattr(advocacy, "grassrootsmember", False)
    setattr(contact, "grassrootsmember", grassrootsmember)

    return contact


def update_user_groups(user):
    """
    Updates a particular user's groups based on matching conditions in GROUP_DEFINITIONS
    """
    contact = get_contact_for_groups(user)
    contact_group_names = []
    user.is_staff = False
    for name, definition in GROUP_DEFINITIONS.items():
        if definition.has_group(contact):
            contact_group_names.append(name)
            if definition.grants_admin_access:
                user.is_staff = True
    contact_groups = Group.objects.filter(name__in=contact_group_names)
    user.groups.set(contact_groups)
    user.save()
    contact.user = user
    contact.save()  # TO DO... yet another contact save here! Refactor?
    return contact


def update_groups():
    """
     - Updates the django group and permission records to match the groups defined in GROUP_DEFINITIONS.
    """
    all_groups = Group.objcts.all()
    for g in all_groups:
        if not g.name in GROUP_DEFINITIONS:
            g.delete()

    # TO DO... implement grants admin access
    # TO DO... implement permissions (including auto-adding permissions for proxy models if they don't alredy exist)
    # .... see _data_tools/permissions.py
