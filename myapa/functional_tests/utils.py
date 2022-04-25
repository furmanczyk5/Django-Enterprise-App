import factory
from imis.enums.members import ImisMemberStatuses as MemStatus, ImisMemberTypes as MemTypes
from imis.tests.factories.name import ImisNameFactoryBlank


def build_imis_org_and_admin():
    """
    Build iMIS Name records for an organization and person
    with a co_id of the organization
    :return: tuple, (org, admin)
    """
    org = ImisNameFactoryBlank(
        id=factory.Sequence(lambda n: str(n + 1000000)),
        member_type=MemTypes.AGC.value,
        member_record=False,
        company_record=True,
        company=factory.Faker('company'),
        status=MemStatus.ACTIVE.value,
        updated_by='DJANGO_TEST_FACTORY'
    )

    org_admin = ImisNameFactoryBlank(
        id=factory.Sequence(lambda n: str(n + 2000000)),
        first_name=factory.Faker('first_name'),
        last_name=factory.Faker('last_name'),
        member_type=MemTypes.NOM.value,
        member_record=True,
        company_record=False,
        co_id=org.id,
        status=MemStatus.ACTIVE.value,
        updated_by='DJANGO_TEST_FACTORY'
    )

    return org, org_admin
