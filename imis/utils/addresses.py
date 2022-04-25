from django.db.models.functions import Length

from imis.models import NameAddress


def get_primary_address(username, purpose="Work Address"):
    """
    Determine the best iMIS address to use as the primary address for a
    :class:`myapa.models.contact.Contact`

    :param username: str, user ID (username in Django)
    :param purpose: str, the value of :attr:`imis.models.NameAddress.purpose` to use as
                         the initial check
    :return: :obj:`imis.models.NameAddress`
    """

    # TODO: figure this out already FFS
    # imis_addresses = NameAddress.objects.filter(id=username, purpose=purpose)

    imis_primary_address = NameAddress.objects.annotate(
        country_length=Length('country')
    ).filter(
        id=username,
        preferred_mail=True,
        country_length__gt=0
    )
    return imis_primary_address.first()
