from myapa.permissions.conditions import *

from events.models import NATIONAL_CONFERENCE_MASTER_ID


class GroupDefinition(MultipleConditions):

    def __init__(self, description="", *args, **kwargs):

        self.description = description
        self.grants_admin_access = kwargs.pop("grants_admin_access", False)
        super().__init__(*args, **kwargs)


GROUP_DEFINITIONS = {

    "webuser": GroupDefinition(
        "Default group that everyone gets on login",  # TO CONSIDER... depreciate?
        HasAttrs("user"),
    ),

    # ------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------
    # STAFF AND ADMIN-RELATED GROUPS:

    "staff": GroupDefinition(
        """
        Is APA staff (based on link to APA's company record).
        Note that additional users may have admin ("staff admin") access in django
        for specific purposes such as chapter conference admin access.
        """,
        IsStaff(),
        HasStaffTeam("TEMP_STAFF"),
        grants_admin_access=True,
    ),

    "onsite-conference-admin": GroupDefinition(
        "Temporary limited admin access for onsite conference staffing",
        HasStaffTeam("CONFERENCE_ONSITE"),
        grants_admin_access=True,
    ),

    "staff-reviewer": GroupDefinition(
        "APA contractors who need access to confidential information in AICP applications",
        HasStaffTeam("STAFF_REVIEWER"),
        grants_admin_access=False,
    ),

    "staff-editor": GroupDefinition(
        "Staff access to the django admin editor tools",
        IsStaff(),
        HasStaffTeam("EDITOR"),
        logical="and",
    ),

    "staff-store-admin": GroupDefinition(
        "Staff access to product and shopping cart management",
        IsStaff(),
        HasStaffTeam("STORE_ADMIN"),
        logical="and",
    ),

    "staff-aicp": GroupDefinition(
        "Staff AICP team access",
        HasStaffTeam("AICP")
    ),

    "staff-marketing": GroupDefinition(
        "Staff marketing team access",
        HasStaffTeam("MARKETING"),
    ),

    "staff-membership": GroupDefinition(
        "Staff membership team access",
        HasStaffTeam("MEMBERSHIP"),
    ),

    "staff-education": GroupDefinition(
        "Staff education team access",
        HasStaffTeam("EDUCATION"),
    ),

    "staff-careers": GroupDefinition(
        "Staff careers team access",
        HasStaffTeam("CAREERS"),
    ),

    "staff-publications": GroupDefinition(
        "Staff publications team access",
        HasStaffTeam("PUBLICATIONS"),
    ),

    "staff-research": GroupDefinition(
        "Staff research team access",
        HasStaffTeam("RESEARCH"),
    ),

    "staff-communications": GroupDefinition(
        "Staff communications team access",
        HasStaffTeam("COMMUNICATIONS"),
    ),

    "staff-conference": GroupDefinition(
        "Staff conference team access",
        HasStaffTeam("CONFERENCE"),
    ),

    "staff-policy": GroupDefinition(
        "Staff policy team access",
        HasStaffTeam("POLICY"),
    ),

    "staff-leadership": GroupDefinition(
        "Staff leadership team access",
        HasStaffTeam("LEADERSHIP"),
    ),

    "staff-events-editor": GroupDefinition(
        "Staff events editor team access",
        HasStaffTeam("EVENTS_EDITOR"),
    ),

    "staff-wagtail-admin": GroupDefinition(
        "Staff that are Wagtail Admins",
        HasStaffTeam("STAFF_WAGTAIL_ADMIN"),
    ),

    # Replaces "organization-store-admin"
    "component-admin": GroupDefinition(
        "Chapter/division access to limited django admin",
        HasStaffTeam("COMPONENT_ADMIN"),
        # IsStaff(),
        grants_admin_access=True,
    ),

    "JOBS-admin": GroupDefinition(
        "Chapter/division access to django jobs admin",
        HasStaffTeam("JOBS_ADMIN"),
        grants_admin_access=True,
    ),

    "wagtail-admin": GroupDefinition(
        "Admin for All Wagtail Sites",
        HasStaffTeam("WAGTAIL_ADMIN"),
        grants_admin_access=True,
    ),

    "URBAN_DES-admin": GroupDefinition(
        "Urban Design Division Admin",
        HasStaffTeam("COMPONENT_URBAN_DES"),
        grants_admin_access=True,
    ),

    "TRANS-admin": GroupDefinition(
        "Transportation Division Admin",
        HasStaffTeam("COMPONENT_TRANS"),
        grants_admin_access=True,
    ),

    "HOUSING-admin": GroupDefinition(
        "Housing Division Admin",
        HasStaffTeam("COMPONENT_HOUSING"),
        grants_admin_access=True,
    ),

    "HMDR-admin": GroupDefinition(
        "Hazard Mitigation and Disaster Recovery Division Admin",
        HasStaffTeam("COMPONENT_HMDR"),
        grants_admin_access=True,
    ),

    "BLACK-admin": GroupDefinition(
        "Planning and the Black Community Division Admin",
        HasStaffTeam("COMPONENT_BLACK"),
        grants_admin_access=True,
    ),

    "WOMEN-admin": GroupDefinition(
        "APA Planning and Women Division Admin",
        HasStaffTeam("COMPONENT_WOMEN"),
        grants_admin_access=True,
    ),

    "CITY-admin": GroupDefinition(
        "APA City Planning & Management Division Admin",
        HasStaffTeam("COMPONENT_CITY"),
        grants_admin_access=True,
    ),

    "COUNTY-admin": GroupDefinition(
        "APA County Planning & Management Division Admin",
        HasStaffTeam("COMPONENT_COUNTY"),
        grants_admin_access=True,
    ),

    "ECON-admin": GroupDefinition(
        "APA Economic Development Division Admin",
        HasStaffTeam("COMPONENT_ECON"),
        grants_admin_access=True,
    ),

    "ENVIRON-admin": GroupDefinition(
        "APA Economic Development Division Admin",
        HasStaffTeam("COMPONENT_ENVIRON"),
        grants_admin_access=True,
    ),

    "FED_PLAN-admin": GroupDefinition(
        "APA Federal Planning Division Admin",
        HasStaffTeam("COMPONENT_FEDERAL"),
        grants_admin_access=True,
    ),

    "INTL-admin": GroupDefinition(
        "APA International Division Admin",
        HasStaffTeam("COMPONENT_INTL"),
        grants_admin_access=True,
    ),

    "LGBTQ-admin": GroupDefinition(
        "APA LGBTQ and Planning Division Admin",
        HasStaffTeam("COMPONENT_LGBTQ"),
        grants_admin_access=True,
    ),

    "PRIVATE-admin": GroupDefinition(
        "APA Private Practice Division Admin",
        HasStaffTeam("COMPONENT_PRIVATE"),
        grants_admin_access=True,
    ),

    "SUSTAIN-admin": GroupDefinition(
        "APA Sustainable Communities Division Admin",
        HasStaffTeam("COMPONENT_SUSTAIN"),
        grants_admin_access=True,
    ),

    "TECH-admin": GroupDefinition(
        "APA Technology Division Admin",
        HasStaffTeam("COMPONENT_TECH"),
        grants_admin_access=True,
    ),

    "CHAPT_AZ-admin": GroupDefinition(
        "Arizona Chapter Admin",
        HasStaffTeam("COMPONENT_CHAPT_AZ"),
        grants_admin_access=True,
    ),

    "CHAPT_CA-admin": GroupDefinition(
        "California Chapter Admin",
        HasStaffTeam("COMPONENT_CHAPT_CA"),
        grants_admin_access=True,
    ),

    "CHAPT_CO-admin": GroupDefinition(
        "Colorado Chapter Admin",
        HasStaffTeam("COMPONENT_CHAPT_CO"),
        grants_admin_access=True,
    ),

    "CHAPT_CT-admin": GroupDefinition(
        "Connecticut Chapter Admin",
        HasStaffTeam("COMPONENT_CHAPT_CT"),
        grants_admin_access=True,
    ),

    "CHAPT_FL-admin": GroupDefinition(
        "Florida Chapter Admin",
        HasStaffTeam("COMPONENT_CHAPT_FL"),
        grants_admin_access=True,
    ),

    "CHAPT_HI-admin": GroupDefinition(
        "Hawaii Chapter Admin",
        HasStaffTeam("COMPONENT_CHAPT_HI"),
        grants_admin_access=True,
    ),

    "CHAPT_IA-admin": GroupDefinition(
        "Iowa Chapter Admin",
        HasStaffTeam("COMPONENT_CHAPT_IA"),
        grants_admin_access=True,
    ),

    "CHAPT_IN-admin": GroupDefinition(
        "Indiana Chapter Admin",
        HasStaffTeam("COMPONENT_CHAPT_IN"),
        grants_admin_access=True,
    ),

    "CHAPT_KS-admin": GroupDefinition(
        "Kansas Chapter Admin",
        HasStaffTeam("COMPONENT_CHAPT_KS"),
        grants_admin_access=True,
    ),

    "CHAPT_MN-admin": GroupDefinition(
        "Minnesota Chapter Admin",
        HasStaffTeam("COMPONENT_CHAPT_MN"),
        grants_admin_access=True,
    ),

    "CHAPT_MO-admin": GroupDefinition(
        "Missouri Chapter Admin",
        HasStaffTeam("COMPONENT_CHAPT_MO"),
        grants_admin_access=True,
    ),

    "CHAPT_NC-admin": GroupDefinition(
        "North Carolina Chapter Admin",
        HasStaffTeam("COMPONENT_CHAPT_NC"),
        grants_admin_access=True,
    ),

    "CHAPT_NCAC-admin": GroupDefinition(
        "National Capital Area Chapter Admin",
        HasStaffTeam("COMPONENT_CHAPT_NCAC"),
        grants_admin_access=True,
    ),

    "CHAPT_NE-admin": GroupDefinition(
        "Nebraska Chapter Admin",
        HasStaffTeam("COMPONENT_CHAPT_NE"),
        grants_admin_access=True,
    ),

    "CHAPT_NNE-admin": GroupDefinition(
        "Northern New England Chapter Admin",
        HasStaffTeam("COMPONENT_CHAPT_NNE"),
        grants_admin_access=True,
    ),

    "CHAPT_NV-admin": GroupDefinition(
        "Nevada Chapter Admin",
        HasStaffTeam("COMPONENT_CHAPT_NV"),
        grants_admin_access=True,
    ),

    "CHAPT_OR-admin": GroupDefinition(
        "Oregon Chapter Admin",
        HasStaffTeam("COMPONENT_CHAPT_OR"),
        grants_admin_access=True,
    ),

    "CHAPT_TN-admin": GroupDefinition(
        "Tennessee Chapter Admin",
        HasStaffTeam("COMPONENT_CHAPT_TN"),
        grants_admin_access=True,
    ),

    "CHAPT_TX-admin": GroupDefinition(
        "Texas Chapter Admin",
        HasStaffTeam("COMPONENT_CHAPT_TX"),
        grants_admin_access=True,
    ),

    "CHAPT_VA-admin": GroupDefinition(
        "Virginia Chapter Admin",
        HasStaffTeam("COMPONENT_CHAPT_VA"),
        grants_admin_access=True,
    ),

    "CHAPT_WCC-admin": GroupDefinition(
        "Western Central Chapter Admin",
        HasStaffTeam("COMPONENT_CHAPT_WCC"),
        grants_admin_access=True,
    ),

    "CHAPT_WI-admin": GroupDefinition(
        "Wisconsin Chapter Admin",
        HasStaffTeam("COMPONENT_CHAPT_WI"),
        grants_admin_access=True,
    ),

    # ------------------------------------------------------------------------------------------
    # membership related groups:

    "member": GroupDefinition(
        "APA member access to planning.org",
        IsMember(),
        IsStaff(),
    ),

    "aicpmember": GroupDefinition(
        "Is an AICP member",
        IsAICP(),
    ),

    "nonmember": GroupDefinition(
        "Not a member",  # NOTE, maybe can delete eventually, but for now it's convenient and used a lot
        NotCondition(IsMember()),
        NotCondition(IsStaff()),
        logical="and"
    ),

    "new-member": GroupDefinition(
        "APA member access to planning.org",
        IsMember(),
        HasAttrs("is_new_member"),
        logical="and"
    ),

    # TO DO: confirm still used? (with Ralph/Roberta)
    "member-media": GroupDefinition(
        "Active APA member or Media",
        IsMember(),
        HasSubscription("PRESS")
    ),

    "studentmember": GroupDefinition(
        "Is a student member",
        IsMember(),
        HasMemberType("STU", "FSTU"),
        logical="and",
    ),

    "aicp-cm": GroupDefinition(
        "AICP members set up for CM logging",
        MultipleConditions(
            HasRelatedRecord("cm_logs", is_current=True),
            IsAICP(),
            logical="and"
        ),
        HasStaffTeam("AICP"),
    ),

    "candidate-cm": GroupDefinition(
        "Access to log CM credits AICP Candidate Program",
        HasRelatedRecord("cm_logs", is_current=True, period__code="CAND")
    ),

    "reinstatement-cm": GroupDefinition(
        "Members set up for AICP reinstatement",
        HasRelatedRecord(
            "cm_logs",
            is_current=True,
            status__in=("R", "RA"),
            reinstatement_end_time__gte=timezone.now()
        )
    ),

    "advocacy-network": GroupDefinition(
        "Members who have signed up for the advocacy network",
        IsMember(),
        HasAttrs("grassrootsmember")
    ),

    "lifemember": GroupDefinition(
        "Is a life member",
        IsMember(),
        HasMemberType("LIFE"),
        logical="and",
    ),

    "retiredmember": GroupDefinition(
        "Is a retired member",
        IsMember(),
        HasMemberType("RET"),
        logical="and",
    ),

    "foreignmember": GroupDefinition(
        "Is a member outside of the US",
        IsMember(),
        NotCondition(HasAttrs("_cached_imis_name_address", country="United States")),
        NotCondition(HasAttrs("_cached_imis_name_address", country="United States Territories")),
        NotCondition(HasAttrs("_cached_imis_name_address", country="United States Military")),
        logical="and",
    ),

    "foreignnonmember": GroupDefinition(
        "Is a non-member outside of the US",
        NotCondition(IsMember()),
        NotCondition(IsStaff()),
        NotCondition(HasAttrs("_cached_imis_name_address", country="United States")),
        NotCondition(HasAttrs("_cached_imis_name_address", country="United States Territories")),
        NotCondition(HasAttrs("_cached_imis_name_address", country="United States Military")),
        logical="and",
    ),

    # ------------------------------------------------------------------------------------------
    # NPC-RELATED GROUPS:

    "17CONF": GroupDefinition(
        "Registered for 2017 APA National Planning Conference",
        IsAttending("17CONF/M001"),
        IsAttending("17CONF/M002"),
    ),

    "18CONF": GroupDefinition(
        "Registered for 2018 APA National Planning Conference",
        IsAttending("18CONF/M001"),
        IsAttending("18CONF/M002"),
    ),

    "19CONF": GroupDefinition(
        "Registered for 2019 APA National Planning Conference",
        IsAttending("19CONF/M001"),
        IsAttending("19CONF/M002"),
    ),

    "NPC20-digital": GroupDefinition(
        "Registered for 2020 at Home",
        IsAttending("NPC20HOME/M001"),
        HasActivityProduct("LRN_NPC20_COL"),
    ),

    "PAC20": GroupDefinition(
        "Registered for APA 2020 Policy and Advocacy Conference",
        IsAttending("POL20/PAC"),
    ),

    "NPC21": GroupDefinition(
        "Registered for NPC21",
        IsAttending("21CONF/M001"),
        IsAttending("21CONF/M002"),
        IsAttending("21CONF/M003"),
    ),

    "NPC21-access": GroupDefinition(
        "Registered for the APA Professional Development Subscription with NPC21",
        # FLAGGED FOR REFACTORING: PROFESSIONAL DEVELOPMENT SUBSCRIPTION TRIAL REMOVE
        # IsAttending("21CONF/M001"),
        # HasActivityProduct("NPC21SUBADD"),
        MultipleConditions(
            IsAttending("21CONF/M002"),
            IsLeadership(),
            logical="and"
        ),
    ),

    # TO DO: confirm with Rose that this is still used
    "cldr": GroupDefinition(
        "Comp leadership for conference",
        HasCommittee("AICP_COMM", "BOARD"),
    ),

    # TO DO: confirm still used with Rose (assume yes), if so, confirm logic
    "planningboardmember": GroupDefinition(
        "Planning board member (for conference reg rate)",
        MultipleConditions(
            IsMember(),
            HasMemberType("PBM", "GPBM", "ALUM"),
            logical="and",
        ),
        HasSubscription("PCA"),
    ),

    "planningboard-nonmember": GroupDefinition(
        "Planning board NON-member (for conference reg rate)",
        NotCondition(IsMember()),
        HasAttrs(functional_title="F899"),
        logical="and"
    ),

    "speaker": GroupDefinition(
        "Conference speakers (for conference reg rate)",
        HasRelatedRecord(
            related_name="contactrole",
            role_type__in=(
                "SPEAKER",
                'ORGANIZER&SPEAKER',
                'MODERATOR',
                'ORGANIZER&MODERATOR'
            ),
            content__parent__id=NATIONAL_CONFERENCE_MASTER_ID
        )
    ),

    "LEG_LIAIS": GroupDefinition(
        "Members of the Legislative Liaison Committee",
        HasCommittee("LEG LIAIS")
    ),

    "LEGIS_POLICY": GroupDefinition(
        "Members of the Legislative and Policy Committee",
        HasCommittee("LEGIS POLICY")
    ),


    # ------------------------------------------------------------------------------------------
    # SUBSCRIPTIONS-RELATED GROUPS:

    "planning": GroupDefinition(
        "Access to Planning Magazine (including members)",
        IsMember(),
        IsStaff(),

        # TO DO: confirm these with Karl
        HasSubscription("PLANNING", "PCA","PRESS"),
        HasMemberType("PBM", "GPBM"),
        HasCompanyMemberType("DVN", "CHP", "AGC"),

        # TO DO... check with Ralph/Meghan/Kelly on keeping around USC_Purchase requirement for products starting with PLANNING_E_
    ),

    "commissioner": GroupDefinition(
        "The Commissioner access",
        IsMember(),

        # TO DO: confirm these with Karl
        # Removing CMSR5 per Karl
        HasSubscription("CMSR", "CMSR10", "PCA"),
        HasMemberType("PBM", "GPBM"),
        HasCompanySubscription("CMSR10"),
    ),

    "PAS": GroupDefinition(
        "PAS subscriber or linked to a PAS subscribing agency",
        HasSubscription("PAS", "PRESS"),
        HasCompanySubscription("PAS"),
    ),

    "ZONING": GroupDefinition(
        "Receives Zoning Practice (subscriber or press)",
        HasSubscription("ZONING", "PRESS", "EZP"),
        HasCompanySubscription("ZONING"),
        HasMemberType("STU"),
    ),

    "JAPA": GroupDefinition(
        "Receives JAPA (subscriber or free student)",
        HasSubscription("JAPA", "FREE_JAPA", "JOUR", "FREE_JOUR", "EJOUR", "FREE_EJOUR"),
        HasCompanySubscription("JAPA", "FREE_JAPA", "JOUR", "FREE_JOUR", "EJOUR", "FREE_EJOUR"),

        # TO DO: confirm all students get JAPA online (with Karl)
        HasMemberType("FCLTI", "FCLTS", "STU"),
    ),

    # NEW SUBSCRIPTION FOR PROFESSIONAL DEV SUBSCRIPTION
    "PROF_DEV_ACCESS": GroupDefinition(
        "Subscribed to the Professional Development unlimited subscription",
        # HasSubscription("PROF_DEV_ACCESS"),
        HasSubscription("EDU_SUB"),
    ),

    # ------------------------------------------------------------------------------------------
    # DIVISION-RELATED GROUPS:

    "HMDR": GroupDefinition(
        "Member of Hazard Mitigation and Disaster Recovery division",
        HasSubscription("HMDR"),
        IsLeadership(),
    ),

    "PLAN_BLACK": GroupDefinition(
        "Member of Planning and the Black Community Division",
        HasSubscription("PLAN_BLACK"),
        IsLeadership(),
    ),

    "PRIVATE": GroupDefinition(
        "Member Private Practive of division",
        HasSubscription("PRIVATE"),
        IsLeadership(),
    ),

    "RESORT": GroupDefinition(
        "Member of Resort and Tourism division",
        HasSubscription("RESORT"),
        IsLeadership(),
    ),

    "HOUSING": GroupDefinition(
        "Member Housing and Community Development division",
        HasSubscription("HOUSING"),
        IsLeadership(),
    ),

    "ENVIRON": GroupDefinition(
        "Member of Environment, National Resources, and Energy division",
        HasSubscription("ENVIRON"),
        IsLeadership(),
    ),

    "FED_PLAN": GroupDefinition(
        "Member of Federal Planning division",
        HasSubscription("FED_PLAN"),
        IsLeadership(),
    ),

    "GALIP": GroupDefinition(
        "Member of Gay & Lesbians in planning division",
        HasSubscription("GALIP"),
        IsLeadership(),
    ),

    "INTER_GOV": GroupDefinition(
        "Member of Intergovernmental Affairs division",
        HasSubscription("INTER_GOV"),
        IsLeadership(),
    ),

    "CITY_PLAN": GroupDefinition(
        "Member of city planning and management division",
        HasSubscription("CITY_PLAN"),
        IsLeadership(),
    ),

    "CPD": GroupDefinition(
        "Member of County Planning division",
        HasSubscription("CPD"),
        IsLeadership(),
    ),

    "LAP": GroupDefinition(
        "Member of Latinos and Planning division",
        HasSubscription("LAP"),
        IsLeadership(),
    ),

    "LAW": GroupDefinition(
        "Member of Planning and Law division",
        HasSubscription("LAW"),
        IsLeadership(),
    ),

    "NEW_URB": GroupDefinition(
        "Member of New Urbanism division",
        HasSubscription("NEW_URB"),
        IsLeadership(),
    ),

    "INTL": GroupDefinition(
        "Member of International division",
        HasSubscription("INTL"),
        IsLeadership(),
    ),

    "ECON": GroupDefinition(
        "Member of Economic Development division",
        HasSubscription("ECON"),
        IsLeadership(),
    ),

    "INFO_TECH": GroupDefinition(
        "Member of Information and Technology division",
        HasSubscription("INFO_TECH"),
        IsLeadership(),
    ),

    "SMALL_TOWN": GroupDefinition(
        "Member of Small Town and Rural Planning division",
        HasSubscription("SMALL_TOWN"),
        IsLeadership(),
    ),

    "URBAN_DES": GroupDefinition(
        "Member of Urban Design and Preservation division",
        HasSubscription("URBAN_DES"),
        IsLeadership(),
    ),

    "TRANS": GroupDefinition(
        "Member of Transportation Planning division",
        HasSubscription("TRANS"),
        IsLeadership(),
    ),

    "WOMEN": GroupDefinition(
        "Member of Planning and Women division",
        HasSubscription("WOMEN"),
        IsLeadership(),
    ),

    "SCD": GroupDefinition(
        "Sustainable Communities Division",
        HasSubscription("SCD"),
        IsLeadership(),
    ),

    # ------------------------------------------------------------------------------------------
    # CHAPTER-MEMBERSHIP RELATED GROUPS:

    "member-chapter": GroupDefinition(
        "Is an APA or chapter only member",
        IsMember(),
        HasSubscriptionProductType("CHAPT"),
    ),

    "CHAPT_AK": GroupDefinition(
        "Alaska Chapter member",
        HasSubscription("CHAPT/AK"),
    ),

    "CHAPT_FL": GroupDefinition(
        "Florida Chapter member",
        HasSubscription("CHAPT/FL"),
    ),

    "CHAPT_MD": GroupDefinition(
        "MD Chapter member",
        HasSubscription("CHAPT/MD"),
    ),

    "CHAPT_NCAC": GroupDefinition(
        "Kansas Chapter member",
        HasSubscription("CHAPT/KS"),
    ),

    "CHAPT_NE": GroupDefinition(
        "NE Chapter member",
        HasSubscription("CHAPT/NE"),
    ),

    "CHAPT_NV": GroupDefinition(
        "Nevada Chapter member",
        HasSubscription("CHAPT/NV"),
    ),

    "CHAPT_KS": GroupDefinition(
        "Kansas Chapter member",
        HasSubscription("CHAPT/KS"),
    ),

    "CHAPT_VA": GroupDefinition(
        "Virginia Chapter member",
        HasSubscription("CHAPT/VA"),
    ),

    # ------------------------------------------------------------------------------------------
    # LEADERSHIP / COMMITTEE RELATED GROUPS

    "leadership": GroupDefinition(
        "Is leadership",
        IsLeadership(),
    ),

    "PDO": GroupDefinition(
        "Access to PDO services (PDOs and some leadership groups)",
        HasCommittee("PDO", "AICP_COMM", "CHAP_PRES", "BOARD")
    ),

    # TO DO: confirm still in use
    "PUDS_BOARD": GroupDefinition(
        "On the PUDS review board",
        HasCommittee("PUDS_BOARD")
    ),

}

DEPRECIATED_GROUPS = [

    # TO DO: confirm division no longer exists
    "INDG_PLAN",

    "PEL",
    "PAS-promo",
    "purchase-BOOK_A00811",
    "purchase-BOOK_P589",

    "speaker",
    "mwc",
    "webuser",
    "POLICY_ADVOCACY", # TO DO update any products/prices/content records to "advocacy-network" instead of "POLICY_ADVOCACY"
    "PAN", # TO DO update any products/prices/content records to "advocacy-network" instead of "POLICY_ADVOCACY"
    "reset_password",
    "aicp_cm_OLD",

    # TO DO: confirm not used in directories
    "CHAP_NEWS_ED",
    "PDO-list"

    "mentor",
    "resumesearch",

    "chapterconferencerep", # TO DO: replace with "compenont-admin"

    "student-np", # TO DO:  (check/update codebase & products/prices/content records) ... replace with "new-member"/"studentmember"
    "npmember", # TO DO:  (check/update codebase & products/prices/content records) ... replace with "new-member"

    "member-pas" # TO DO add "member" and "PAS" groups to any products/prices/content

    "practicingplanner",

    # TO DO:  (check/update codebase & products/prices/content records)
    "nonmember-nonchapter"
    "nonmember-foryear",
    "nonmember-women",
    "nonzoning" ,
    "nonmember-nonzoning",
    "foreign-nonmember",
    "member-nonaicp",
    "nonaicp",
    "paidstudent",
    "freestudent",
    "FAICP",
    "division",
    "PLAN_BLACK-nonmember",
    "INTER_GOV-nonmember",
    "ENVIRON-nonmember",
    "CPD-nonmember",
    "LAW-nonmember",
    "chapter",
    "chapter-only",
    "15CONF-M001",
    "15CONF-P013",
    "awc-customer-nonaicp",
    "awc-customer-aicp"

    # component leadership groups... originally thought would be used for directories, but not used
    "LEADERSHIP_AK",
    "LEADERSHIP_KS",
    "LEADERSHIP_NE",
    "LEADERSHIP_VA",
    "LEADERSHIP_PLAN_BLACK",
    "LEADERSHIP_CITY_PLAN",
    "LEADERSHIP_CPD",
    "LEADERSHIP_ECON",
    "LEADERSHIP_ENVIRON",
    "LEADERSHIP_FED_PLAN",
    "LEADERSHIP_GALIP",
    "LEADERSHIP_HMDR",
    "LEADERSHIP_HOUSING",
    "LEADERSHIP_INTL",
    "LEADERSHIP_LAP",
    "LEADERSHIP_NEW_URB",
    "LEADERSHIP_LAW",
    "LEADERSHIP_WOMEN",
    "LEADERSHIP_PRIVATE",
    "LEADERSHIP_INTER_GOV",
    "LEADERSHIP_SMALL_TOWN",
    "LEADERSHIP_SCD",
    "LEADERSHIP_INFO_TECH",
    "LEADERSHIP_TRANS",
    "LEADERSHIP_URBAN_DES",

]

POSSIBLE_GROUPS_TO_DEPRECIATE = [
    "nonmember",
    "cldr",
    "member-media",
    "member-chapter",
    "PUDS_BOARD"
]
