import logging

from celery import chain, shared_task

from content.mail import Mail
from imis.models import NameAddress
from imis.utils.addresses import get_primary_address
from myapa.utils import OrgDupeCheck

logger = logging.getLogger(__name__)


NEW_ORG_RECORD_TO_EMAILS = [
    'akrakos@planning.org',
    'cmollet@planning.org',
    'klennon@planning.org',
    'amoore@planning.org'
]


@shared_task(name='org_dupe_check', bind=True)
def org_dupe_check(self, org, contact):
    """
    Celery task to run a duplicate check of existing Organizations
    and send emails to staff members (defined above) notifying
    them that a new Org record has been created and if there
    are any potential duplicates.

    :param self: instance of this task (because we specify bind=True); not passed in by the caller
    :param org: :class:`myapa.models.proxies.Organization`
    :param contact: :class:`myapa.models.contact.Contact`
    :return: None
    """
    org_id = None
    if hasattr(org, 'user'):
        org_id = getattr(org.user, 'username', '')
    dc = OrgDupeCheck(
        company=org.company,
        personal_url=org.personal_url,
        address1=org.address1,
        city=org.city,
        state=org.state,
        zip_code=org.zip_code,
        id=org_id,
        ein_number=org.ein_number
    )

    Mail.send(
        mail_code="MYORG_NEW_ORG_RECORD",
        mail_to=NEW_ORG_RECORD_TO_EMAILS,
        mail_context=dict(
            org=org,
            contact=contact,
            dupe_candidates=dc.get_all_candidates(),
            ein_candidates=dc.ein_candidates
        )
    )


@shared_task(name='vv_validate_address')
def vv_validate_address(contact):
    contact.validate_address()
    return contact


@shared_task(name='vv_write_districts')
def vv_write_districts(contact):
    contact.get_districts()
    return contact


@shared_task(name='vv_validate_write')
def vv_validate_write(contact):
    """
    Chain together the results of validating addresses and writing districts
    to iMIS. ``chain`` will pass the return value of the preceding function
    to the next function in the chain, so because ``vv_validate_address``
    returns the Contact record, it will pass that in when
    calling ``vv_write_districts``
    :param contact:
    :return:
    """
    return chain(vv_validate_address.s(contact), vv_write_districts.s())()


@shared_task(name='vv_validate_address_imis')
def vv_validate_address_imis(base_address, address_num=None):
    name_address = None
    if address_num is not None:
        name_address = NameAddress.objects.filter(address_num=address_num).first()
    else:
        user = getattr(base_address, 'user', None)
        if user is not None and getattr(user, 'username', None) is not None:
            username = user.username
            name_address = get_primary_address(username)

    if name_address is not None:
        geocode = name_address.validate_address()
        if geocode is not None:
            geocode.get_districts()
    else:
        logger.error('No NameAddress record found for: {}'.format(base_address))
