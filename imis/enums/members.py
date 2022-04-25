from enum import Enum


class ImisMemberStatuses(Enum):
    """
    query:
    SELECT * FROM Gen_Tables WHERE TABLE_NAME = 'MEMBER_STATUS'
    """

    ACTIVE = 'A'

    MARKED_FOR_DELETION = 'D'

    INACTIVE = 'I'

    SUSPENDED = 'S'


class ImisMemberTypes(Enum):
    """
    table name: Member_Types
    """

    ADM = "ADM"
    ADM_LABEL = "Conf Admin Online"

    ADMIN = "ADMIN"
    ADMIN_LABEL = "Administrator"

    AGC = "AGC"
    AGC_LABEL = "Agency"

    ALUM = "ALUM"
    ALUM_LABEL = "Alumni Planning Board Member"

    CHO = "CHO"
    CHO_LABEL = "Chapter Only"

    CHP = "CHP"
    CHP_LABEL = "Chapter Office"

    DEC = "DEC"
    DEC_LABEL = "Deceased Individual"

    DIV = "DIV"
    DIV_LABEL = "Division Only"

    DVN = "DVN"
    DVN_LABEL = "Division Office"

    EXC = "EXC"
    EXC_LABEL = "Exchange Subscriber"

    FCLTI = "FCLTI"
    FCLTI_LABEL = "Faculty: Pays Own AICP Dues"

    FCLTS = "FCLTS"
    FCLTS_LABEL = "Faculty: School Pays AICP Dues"

    FSTU = "FSTU"
    FSTU_LABEL = "Free Student Membership"

    GPBM = "GPBM"
    GPDM_LABEL = "Group Planning Board Member"

    LIB = "LIB"
    LIB_LABEL = "Library"

    LIFE = "LIFE"
    LIFE_LABEL = "Life Member"

    MEDIA = "MEDIA"
    MEDIA_LABEL = "Media/Press"

    MEM = "MEM"
    MEM_LABEL = "Regular Member"

    NOM = "NOM"
    NOM_LABEL = "Non Member"

    NP = "NP"
    NP_LABEL = "New Professional"

    PAGC = "PAGC"
    PAGC_LABEL = "Agency: Parent"

    PBM = "PBM"
    PBM_LABEL = "Planning Board Member"

    PPRI = "PPRI"
    PPRI_LABEL = "Private Firm: Parent"

    PRI = "PRI"
    PRI_LABEL = "Private Firm"

    PRO = "PRO"
    PRO_LABEL = "Prospect"

    PSCH = "PSCH"
    PSCH_LABEL = "School: Parent"

    PSTU = "PSTU"
    PSTU_LABEL = "Pending Student"

    RET = "RET"
    RET_LABEL = "Retired Member"

    SCH = "SCH"
    SCH_LABEL = "School"

    STF = "STF"
    STF_LABEL = "APA Staff"

    STU = "STU"
    STU_LABEL = "Student Member"

    SUB = "SUB"
    SUB_LABEL = "Subscription Agency"

    WEB = "WEB"
    WEB_LABEL = "Web Sign-Up"

    XALUM = "XALUM"
    XALUM_LABEL = "Ex-Alumni Planning Board Member"

    XCHO = "XCHO"
    XCHO_LABEL = "Ex-Chapter Only"

    XDIV = "XDIV"
    XDIV_LABEL = "Ex-Division Only"

    XFCLI = "XFCLI"
    XFCLI_LABEL = "Ex-Faculty: Pays Own AICP Dues"

    XFCLS = "XFCLS"
    XFCLS_LABEL = "Ex-Faculty: School Pays AICP Dues"

    XFCLT = "XFCLT"
    XFCLT_LABEL = "Ex-Faculty"

    XFSTU = "XFSTU"
    XFSTU_LABEL = "Ex-Free Student Member"

    XGPBM = "XGPBM"
    XGPBM_LABEL = "Ex-Group Planning Board Member"

    XLIFE = "XLIFE"
    XLIFE_LABEL = "Ex-Life Member"

    XMEM = "XMEM"
    XMEM_LABEL = "Ex-Regular Member"

    XNP = "XNP"
    XNP_LABEL = "Ex-New Professional"

    XPBM = "XPBM"
    XPBM_LABEL = "Ex-Planning Board Member"

    XRET = "XRET"
    XRET_LABEL = "Ex-Retired Member"

    XSTF = "XSTF"
    XSTF_LABEL = "Ex-APA Staff"

    XSTU = "XSTU"
    XSTU_LABEL = "Ex-Student Member"


class ImisMemberCategories(Enum):
    """
    query:
    SELECT * FROM Gen_Tables WHERE TABLE_NAME = 'CATEGORY'
    """

    # Chapter Only Member
    Chapt = "Chapt"

    # New Member: First Year
    NM1 = "NM1"

    # New Member: Second Year
    NM2 = "NM2"


class ImisNameAddressPurposes(Enum):

    HOME_ADDRESS = "Home Address"

    WORK_ADDRESS = "Work Address"

    OTHER_ADDRESS = "Other Address"
