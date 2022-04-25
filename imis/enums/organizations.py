from enum import Enum


class ImisOrgTypes(Enum):
    """
    table_name: ORG_TYPE
    """

    # Academia
    PR001 = "PR001"

    # Nonprofit or Non-Governmental Organization
    PR002 = "PR002"

    # Private - Consulting Firm
    PR005 = "PR005"

    # Private - Law Firm
    PR006 = "PR006"

    # Private - Other
    PR003 = "PR003"

    # Public Sector - County Government
    P002 = "P002"

    # Public Sector - Federal Government
    P005 = "P005"

    # Public Sector - Local Government
    P001 = "P001"

    # Public Sector - Other
    P999 = "P999"

    # Public Sector - Regional Government
    P003 = "P003"

    # Public Sector - State Government
    P004 = "P004"

    # Regional Entity
    PR004 = "PR004"


class SchoolAccreditationTypes(Enum):

    # Accredited Undergraduate Program
    A001 = "A001"

    # Accredited Graduate Program
    A002 = "A002"

    # Non-Accredited Undergraduate Program
    N001 = "N001"

    # Non-Planning Graduate Free Student Members Program
    N002 = "N002"

    # Non-Accredited Graduate Planning Program
    N003 = "N003"
