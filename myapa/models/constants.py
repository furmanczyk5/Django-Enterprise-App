"""constants.py

Defines field choices on :mod:`myapa.models`
"""

from enum import Enum


CONTACT_TYPES = (
    ('INDIVIDUAL', 'Individual'),
    ('ORGANIZATION', 'Organization'),
)


class DjangoContactTypes(Enum):

    INDIVIDUAL = "INDIVIDUAL"
    ORGANIZATION = "ORGANIZATION"


ADDRESS_TYPES = (
    ('HOME', 'Home Address'),
    ('WORK', 'Work Address'),
)


ORGANIZATION_TYPES = (
    # ('NONPROFIT', 'Non-profit Organization'),
    # ('TRAINING', 'Professional Training Service'),
    # ('GOV', 'Government Entity'),
    # ('PRIVATE', 'Private Firm'),
    # ('ACADEMIC', 'University/Academic Institution'),
    # ('CONSULTANT', 'Consultant'),
    ('PR001', 'Academia'),
    ('PR002', 'Nonprofit or Non-Governmental Organization'),
    ('PR005', 'Private - Consulting Firm'),
    ('PR006', 'Private - Law Firm'),
    ('PR003', 'Private - Other'),
    ('P001', 'Public Sector - Local Government'),
    ('P002', 'Public Sector - County Government'),
    ('P003', 'Public Sector - Regional Government'),
    ('P004', 'Public Sector - State Government'),
    ('P005', 'Public Sector - Federal Government'),
    ('P999', 'Public Sector - Other'),
    ('PR004', 'Regional Entity')
)


class DjangoOrganizationTypes(Enum):

    # Maintaining these for backwards compatibility and human-friendliness
    NONPROFIT = "PR002"
    TRAINING = "PR003"
    GOV = "P999"
    PRIVATE = "PR003"
    ACADEMIC = "PR001"
    CONSULTANT = "PR005"

    PR001 = "PR001"
    PR001_LABEL = "Academia"

    PR002 = "PR002"
    PR002_LABEL = "Nonprofit or Non-Governmental Organization"

    PR005 = "PR005"
    PR005_LABEL = "Private - Consulting Firm"

    PR006 = "PR006"
    PR006_LABEL = "Private - Law Firm"

    PR003 = "PR003"
    PR003_LABEL = "Private - Other"

    P001 = "P001"
    P001_LABEL = "Public Sector - Local Government"

    P002 = "P002"
    P002_LABEL = "Public Sector - County Government"

    P003 = "P003"
    P003_LABEL = "Public Sector - Regional Government"

    P004 = "P004"
    P004_LABEL = "Public Sector - State Government"

    P005 = "P005"
    P005_LABEL = "Public Sector - Federal Government"

    P999 = "P999"
    P999_LABEL = "Public Sector - Other"

    PR004 = "PR004"
    PR004_LABEL = "Regional Entity"


IMIS_ORGANIZATION_TYPES = (
    ('PUBLIC_LOCAL', 'Public Sector - Local Government'),
    ('PUBLIC_COUNTY', 'Public Sector - County Government'),
    ('PUBLIC_REGIONAL', 'Public Sector - Regional Government'),
    ('PUBLIC_STATE', 'Public Sector - State Government'),
    ('PUBLIC_FEDERAL', 'Public Sector - Federal Government'),
    ('PUBLIC_OTHER', 'Public Sector - Other'),
    ('ACADEMIC', 'Academia'),
    ('NONPROFIT', 'Nonprofit or Non-Governmental Organization'),
    ('PRIVATE_CONSULTING', 'Private - Consulting Firm'),
    ('PRIVATE_LAW', 'Private - Law Firm'),
    ('PRIVATE_OTHER', 'Private - Other'),
    ('REGIONAL', 'Regional Entity'),
)


# Mapping our IMIS_ORGANIZATION_TYPES to the CODE value in iMIS
# iMIS query:
# SELECT * FROM Gen_Tables WHERE TABLE_NAME = 'ORG_TYPE'; go
IMIS_ORGANIZATION_TYPES_CODES = {
    'PUBLIC_LOCAL': 'P001',
    'PUBLIC_COUNTY': 'P002',
    'PUBLIC_REGIONAL': 'P003',
    'PUBLIC_STATE': 'P004',
    'PUBLIC_FEDERAL': 'P005',
    'PUBLIC_OTHER': 'P999',
    'ACADEMIC': 'PR001',
    'NONPROFIT': 'PR002',
    'PRIVATE_CONSULTING': 'PR005',
    'PRIVATE_LAW': 'PR006',
    'PRIVATE_OTHER': 'PR003',
    'REGIONAL': 'PR004'
}


# Mapping our existing ORGANIZATION_TYPES to IMIS_ORGANIZATION_TYPES
# for use in a bulk update script
DJANGO_IMIS_ORG_TYPES = {
    'NONPROFIT': 'PR002',
    'TRAINING': 'PR003',
    'GOV': 'P999',  # This one will probably need manual inspection...
    'PRIVATE': 'PR003',  # also this one
    'ACADEMIC': 'PR001',
    'CONSULTANT': 'PR005'
}


PAS_TYPES = (
    ("A", "Municipal under 25,000"),
    ("B", "Municipal 25,000 - 99,999"),
    ("C", "Municipal 100,000 - 249,999"),
    ("D", "Municipal 250,000- 750,000"),
    ("E", "Municipal over 750,000"),
    ("F", "Areawide under 100,000"),
    ("G", "Areawide 100,000 - 249,999"),
    ("H", "Areawide 250,000 - 499,999"),
    ("I", "Areawide 500,000 - 1 Million"),
    ("J", "Areawide over 1 Million"),
    ("K", "State or Federal"),
    ("L", "NonProfit under $1 Million"),
    ("M", "NonProfit $1  - $10 Million"),
    ("N", "NonProfit over $10 Million"),
    ("O", "Private Firm Staff Size under 5"),
    ("P", "Private Firm Staff Size 5 - 50"),
    ("Q", "Private Firm Staff Size over 50"),
    ("R", "University or Library"),
    ("S", "Complimentary/Exchange"),
)

ROLE_TYPES = (
    # conference proposals
    ('AUTHOR', 'Author'),
    ('SPEAKER', 'Speaker'),
    ('ORGANIZER', 'Organizer / Coordinator'),
    ('PROPOSER', 'Proposer / Nominator'),
    ('PUBLISHER', 'Publisher'),
    ('PROVIDER', 'Provider'),
    ('PHOTOGRAPHER', 'Photographer'),
    ('ORGANIZER&SPEAKER', 'Organizer and Speaker'),
    ('MOBILEWORKSHOPGUIDE', 'Mobile Workshop Guide'),
    ('MODERATOR', 'Moderator'),
    ('ORGANIZER&MODERATOR', 'Session Organizer and Moderator'),
    ('LEADPOSTERPRESENTER', 'Lead Poster Presenter'),
    ('POSTERPRESENTER', 'Poster Presenter'),
    ('MOBILEWORKSHOPCOORDINATOR', 'Mobile Workshop Coordinator'),
    ('LEADMOBILEWORKSHOPCOORDINATOR', 'Lead Mobile Workshop Coordinator'),

    # awards
    # ('JURY','Awards Jury'),
    # ('CONTACT','Additional Contact'),
    # ('COORD','Coordinator'),
    # ('NOM','Nominator/Coordinator'),
    # ('GP_CONTACT1','Additional Contact'),
    # ('GP_PLANNER','Planner Contact'),
    # ('GP_PROVIDER','Suggestion Provider'),
    # ('GP_RECIPIENT','Designation Recipent'),
    # ('STUDENT_CONTACT','Project Content'),
    # ('STUDENT_COORD','Coordinator'),
    # ('STUDENT_NOM','Nominator'),
)


class ContactRoleTypes(Enum):
    AUTHOR = "AUTHOR"
    AUTHOR_LABEL = "Author"

    SPEAKER = "SPEAKER"
    SPEAKER_LABEL = "Speaker"

    ORGANIZER = "ORGANIZER"
    ORGANIZER_LABEL = "Organizer / Coordinator"

    PROPOSER = "PROPOSER"
    PROPOSER_LABEL = "Proposer / Nominator"

    PUBLISHER = "PUBLISHER"
    PUBLISHER_LABEL = "Publisher"

    PROVIDER = "PROVIDER"
    PROVIDER_LABEL = "Provider"

    PHOTOGRAPHER = "PHOTOGRAPHER"
    PHOTOGRAPHER_LABEL = "Photographer"

    ORGANIZER_AND_SPEAKER = "ORGANIZER&SPEAKER"
    ORGANIZER_AND_SPEAKER_LABEL = "Organizer and Speaker"

    MOBILEWORKSHOPGUIDE = "MOBILEWORKSHOPGUIDE"
    MOBILEWORKSHOPGUIDE_LABEL = "Mobile Workshop Guide"

    MODERATOR = "MODERATOR"
    MODERATOR_LABEL = "Moderator"

    ORGANIZER_AND_MODERATOR = "ORGANIZER&MODERATOR"
    ORGANIZER_AND_MODERATOR_LABEL = "Session Organizer and Moderator"

    LEADPOSTERPRESENTER = "LEADPOSTERPRESENTER"
    LEADPOSTERPRESENTER_LABEL = "Lead Poster Presenter"

    POSTERPRESENTER = "POSTERPRESENTER"
    POSTERPRESENTER_LABEL = "Poster Presenter"

    MOBILEWORKSHOPCOORDINATOR = "MOBILEWORKSHOPCOORDINATOR"
    MOBILEWORKSHOPCOORDINATOR_LABEL = "Mobile Workshop Coordinator"

    LEADMOBILEWORKSHOPCOORDINATOR = "LEADMOBILEWORKSHOPCOORDINATOR"
    LEADMOBILEWORKSHOPCOORDINATOR_LABEL = "Lead Mobile Workshop Coordinator"


CONTENT_ADDED_TYPES = (
    ('SCHEDULE', 'Conference Schedule'),
    # ('WATCHED', 'Watched'),
    ('BOOKMARK', 'My APA Bookmark'),
    ('EVENT_LOGGED', 'Logged/Evaluated Event or Activity'),
    ('WISHLIST', 'Wishlist'),  # ... for the future once the shopping cart is added into django
    # question... do we want to include CM logging as a type here?
)


ROLE_SPECIAL_STATUSES = (
    ('GUEST_NOT_REQUESTED', 'No Request'),
    ('GUEST_REQUESTED', 'Conference Guest Registration Requested'),
    ('GUEST_APPROVED', 'Conference Guest Registration Approved'),
    ('GUEST_DENIED', 'Conference Guest Registration Denied')
)


PERMISSION_STATUSES = (
    ('NO_RESPONSE', '--'),
    ('PERMISSION_AUTHORIZED', 'Permission Authorized'),
    ('PERMISSION_DENIED', 'Permission Denied')
)


# TODO: Synchronize this with iMIS Relationship_Types?
# query: select count(a.ID), a.RELATION_TYPE, b.DESCRIPTION FROM Relationship as a JOIN Relationship_Types as b ON a.RELATION_TYPE = b.RELATION_TYPE group by b.DESCRIPTION, a.RELATION_TYPE order by 1 desc;
"""
7320,BILLING_I,Is the billing contact for their company
5294,ADMIN_I,Is the administrative contact for their company
2678,CM_I,Is the CM Contact for the Company
1843,FACULTY_I,Is a faculty member in the faculty db for this school
1582,PAS_I,Is the PAS receiver for their company
1580,ZONING_I,Is the Zoning Pract receiver for their company
1424,JOUR_I,Is the JAPA receiver for their company
1339,PEL_I,Is the PEL receiver for their company
1034,PLANNING_I,Is the Planning receiver for their company
660,PCENEWS_I,Is the company's receiver of the e-newsletter for planning c
296,CMSR10_I,Is the 10pak Commis. receiver for their company
161,FSMA,is the free student admin for the school
76,PCENEWS_C,Has as the company's receiver of the e-newsletter for planni
53,CMSR_I,Is the Commissioner receiver for their company
46,ADMIN_C,"Has as the company's administrative contact, this individual"
42,CMSR5_I,Is the 5pak Commis. receiver for their company
29,PAS_C,"Has as the company's PAS receiver, this individual"
23,BILLING_C,"Has as the company's billing contact, this individual"
23,CM_C,"Has as the company's CM contact, this individual"
17,CMSR_C,"Has as the company's Commissioner receiver, this individual"
15,DN_I,Is the DN receiver for their company
9,A_FSMA,"has as the school's FSMA, this individual"
5,PEL_C,"Has as the company's PEL receiver, this individual"
3,PLANNING_C,"Has as the company's Planning receiver, this individual"
3,CMSR10_C,"Has as the company's 10pak Commis. receiver, this individual"
3,ZONING_C,"Has as the company's Zoning Pract receiver, this individual"
2,PEL_E_I,is the PEL receiver for their company
2,PEL_E_C,"Has as the company's PEL Online receiver, this individual"
1,PEL_P_I,Is the PEL receiver for their company
1,JOUR_C,"Has as the company's JAPA receiver, this individual"
1,FACULTY_C,A faculty member contected thru the faculty database
1,CMSR5_C,"Has as the company's 5pak Commis. receiver, this individual"
1,CHR-PRES_I,Is the president/chair for the chapter or division
1,TOP250_I,is the Top250 contact person for their city or county
"""
CONTACT_RELATIONSHIP_TYPES = (
    ('ADMINISTRATOR', 'Organization admin'),
    ('BILLING_I', 'Organization billing contact'),  # imis code
    ('FSMA', 'Free Student Admin'),
)


DEMOGRAPHIC_TITLE_CHOICES = (
    ("NEED_OPTIONS", "WHERE DO WE FIND THESE"),
)


RACE_CHOICES = (
    ("E001", "White"),
    ("E002", "Black or African American"),
    ("E003", "American Indian or Alaska Native"),
    ("E004", "Asian Indian"),
    ("E005", "Japanese"),
    ("E006", "Chinese"),
    ("E007", "Korean"),
    ("E008", "Vietnamese"),
    ("E009", "Native Hawaiian"),
    ("E010", "Filipino"),
    ("E011", "Guamanian or Chamorro"),
    ("E012", "Samoan"),
    ("E100", "Other Asian or Pacific Islander"),
    ("E999", "Some other race"),
)


HISPANIC_ORIGIN_CHOICES = (
    ("O001", "Not Spanish, Hispanic, Latino"),
    ("O002", "Mexican, Mexican American, Chicano"),
    ("O003", "Puerto Rican"),
    ("O004", "Cuban"),
    ("O999", "Other Spanish, Hispanic, Latino"),
    ("O000", "I prefer not to answer")
)


GENDER_CHOICES = (
    ("M", "Male"),
    ("F", "Female"),
    ("S", "I prefer to self-describe"),
    ("X", "I prefer not to answer")
)


OCCUPATION_CHOICES = (
    ("NEED_OPTIONS", "NEED OPTIONS"),
)

# TODO: More than 1500 records in iMIS (DEV) have "F000" - should that be in here too?
# Looks like a grab bag of Job Titles - maybe just "Uncategorized"?
FUNCTIONAL_TITLE_CHOICES = (
    ("F001", "Executive Director / Director / Owner / CEO / President or Chancellor (University)"),
    ("F002", "Deputy Director / Assistant Director / Partner / Principal (Firm) / Dean (University)"),
    ("F003", "Manager / Supervisor / Associate Planner / Professor"),
    ("F004", "Principal Planner / Planner III / Project Manager / Assistant Professor"),
    ("F005", "Senior Planner / Planner II / Associate / Instructor"),
    ("F006", "Assistant Planner / Planner I"),
    ("F007", "Planning Intern"),
    ("F008", "Retired"),
    ("F899", "Planning Commissioner / Elected official / Appointed Official"),
    ("F950", "Employed Outside of the Planning Profession"),
    ("F960", "Unemployed"),
    ("F999", "Student / Other / Not Applicable")
)

# TODO: more than 8,000 records in iMIS (DEV) Ind_Demographics have a
# SALARY_RANGE of "B" - should that be in here too?
SALARY_CHOICES = (
    ("A", "Under $42,000"),
    ("C", "$42,000 - $49,999"),
    ("D", "$50,000 - $59,999"),
    ("E", "$60,000 - $69,999"),
    ("F", "$70,000 - $79,999"),
    ("G", "$80,000 - $89,999"),
    ("H", "$90,000 - $99,999"),
    ("I", "$100,000 - $119,999"),
    ("P", "$120,000 and above"),
    ("J", "Undisclosed")
)


SALARY_CHOICES_OTHER = (
    ("K", "US Student Member"),
    ("L", "US New Professional"),
    ("M", "US Planning Brd Member"),
    ("N", "US Retired Member"),
    ("O", "US Life Member"),
    ("AA", "INT AA"),
    ("BB", "INT BB"),
    ("CC", "INT CC"),
    ("KK", "INT Student Member"),
    ("LL", "INT New Professional"),
    ("NN", "INT Retired Member"),
    ("OO", "INT Life Member"),
)


SALARY_CHOICES_ALL = SALARY_CHOICES + SALARY_CHOICES_OTHER


DEGREE_TYPE_CHOICES = (
    ("Planning", "Planning"),
    ("Architecture", "Architecture"),
    ("Engineering", "Engineering"),
    ("Environmental Science", "Environmental Science"),
    ("Geography", "Geography"),
    ("International Studies", "International Studies"),
    ("Landscape Architecture", "Landscape Architecture"),
    ("Political Science", "Political Science"),
    ("Public Administration", "Public Administration"),
    ("Public Health", "Public Health"),
    ("Social Work", "Social Work"),
    ("Sociology", "Sociology"),
    ("Urban Studies", "Urban Studies")
)


DEGREE_LEVELS = (
    ("B", "Undergraduate"),
    ("M", "Graduate"),
    ("P", "PhD/J.D."),
    ("N", "Other Degree"),
)


SHARE_CHOICES = (
    ("PRIVATE", "Private"),
    ("PUBLIC", "Public"),
    ("MEMBER", "Visible only to other members")
)


CHAPTER_CHOICES = (
    ("AK", "Alaska Chapter"),
    ("AL", "Alabama Chapter"),
    ("AR", "Arkansas Chapter"),
    ("AZ", "Arizona Chapter"),
    ("CAC", "California Central Section"),
    ("CACC", "California Central Coast Section"),
    ("CAIE", "California Inland Empire Section"),
    ("CAL", "California Los Angeles Section"),
    ("CAN", "California Northern Section"),
    ("CAO", "California Orange Section"),
    ("CAS", "California Sacramento Valley Section"),
    ("CASD", "California San Diego Section"),
    ("CO", "Colorado Chapter"),
    ("CT", "Connecticut Chapter"),
    ("DE", "Delaware Chapter"),
    ("FL", "Florida Chapter"),
    ("GA", "Georgia Chapter"),
    ("HI", "Hawaii Chapter"),
    ("IA", "Iowa Chapter"),
    ("ID", "Idaho Chapter"),
    ("IL", "Illinois Chapter"),
    ("IN", "Indiana Chapter"),
    ("KS", "Kansas Chapter"),
    ("KY", "Kentucky Chapter"),
    ("LA", "Louisiana Chapter"),
    ("MA", "Massachusetts Chapter"),
    ("MD", "Maryland Chapter"),
    ("MI", "Michigan Chapter"),
    ("MN", "Minnesota Chapter"),
    ("MO", "Missouri Chapter"),
    ("MS", "Mississippi Chapter"),
    ("NATC", "National Capital Chapter"),
    ("NC", "North Carolina Chapter"),
    ("NE", "Nebraska Chapter"),
    ("NJ", "New Jersey Chapter"),
    ("NM", "New Mexico Chapter"),
    ("NNE", "Northern New England Chapter"),
    ("NV", "Nevada Chapter"),
    ("NYM", "New York Metro Chapter"),
    ("NYU", "New York Upstate Chapter"),
    ("OH", "Ohio Chapter"),
    ("OK", "Oklahoma Chapter"),
    ("OR", "Oregon Chapter"),
    ("PA", "Pennsylvania Chapter"),
    ("RI", "Rhode Island Chapter"),
    ("SC", "South Carolina Chapter"),
    ("TN", "Tennessee Chapter"),
    ("TX", "Texas Chapter"),
    ("UT", "Utah Chapter"),
    ("VA", "Virginia Chapter"),
    ("WA", "Washington Chapter"),
    ("WC", "Western Central Chapter"),
    ("WI", "Wisconsin Chapter"),
    ("WV", "West Virginia Chapter"),
)

# Used for setting prices in :meth:`store.models.product_price.ProductPrice.price_applies`
# iMIS query: SELECT * FROM Gen_Tables WHERE TABLE_NAME = 'COUNTRY_CODES'
# TODO: No longer needed?
COUNTRY_CATEGORY_CODES = (
    ("AA", "Afghanistan"),
    ("AA", "Albania"),
    ("BB", "Algeria"),
    ("CC", "American Samoa"),
    ("CC", "Andorra"),
    ("AA", "Angola"),
    ("BB", "Antigua and Barbuda"),
    ("BB", "Antilles"),
    ("BB", "Argentina"),
    ("AA", "Armenia"),
    ("CC", "Australia"),
    ("CC", "Austria"),
    ("AA", "Azerbaijan"),
    ("CC", "Bahamas"),
    ("BB", "Bahrain"),
    ("AA", "Bangladesh"),
    ("BB", "Barbados"),
    ("AA", "Belarus"),
    ("CC", "Belgium"),
    ("AA", "Belize"),
    ("AA", "Benin"),
    ("AA", "Bermuda"),
    ("AA", "Bhutan"),
    ("AA", "Bolivia"),
    ("AA", "Bosnia and Herzegovina"),
    ("BB", "Botswana"),
    ("BB", "Brazil"),
    ("CC", "Brunei Darussalam"),
    ("AA", "Bulgaria"),
    ("AA", "Burkina Faso"),
    ("AA", "Burundi"),
    ("AA", "Cambodia"),
    ("AA", "Cameroon"),
    ("CC", "Canada"),
    ("AA", "Cape Verde"),
    ("AA", "Cayman Islands"),
    ("AA", "Central African Republic"),
    ("AA", "Chad"),
    ("CC", "Chile"),
    ("AA", "China"),
    ("CC", "Colombia"),
    ("AA", "Comoros"),
    ("AA", "Costa Rica"),
    ("AA", "Croatia"),
    ("AA", "Cuba"),
    ("CC", "Cyprus"),
    ("BB", "Czech Republic"),
    ("AA", "Democratic Republic of the Congo"),
    ("CC", "Denmark"),
    ("AA", "Djibouti"),
    ("AA", "Dominica"),
    ("AA", "Dominican Republic"),
    ("AA", "Ecuador"),
    ("AA", "Egypt"),
    ("AA", "El Salvador"),
    ("CC", "England"),
    ("AA", "Equatorial Guinea"),
    ("AA", "Eritrea"),
    ("AA", "Estonia"),
    ("AA", "Ethiopia"),
    ("CC", "Fed. States of Micronesia"),
    ("AA", "Fiji"),
    ("CC", "Finland"),
    ("CC", "France"),
    ("AA", "Gabon"),
    ("AA", "Gambia"),
    ("AA", "Georgia"),
    ("CC", "Germany"),
    ("AA", "Ghana"),
    ("CC", "Greece"),
    ("AA", "Grenada"),
    ("CC", "Guam"),
    ("AA", "Guatemala"),
    ("AA", "Guinea-Bissau"),
    ("AA", "Guyana"),
    ("AA", "Haiti"),
    ("CC", "Holland"),
    ("AA", "Honduras"),
    ("CC", "Hong Kong"),
    ("AA", "Hungary"),
    ("CC", "Iceland"),
    ("AA", "India"),
    ("AA", "Indonesia"),
    ("BB", "Iran"),
    ("AA", "Iraq"),
    ("CC", "Ireland"),
    ("CC", "Israel"),
    ("CC", "Italy"),
    ("AA", "Ivory Coast"),
    ("AA", "Jamaica"),
    ("CC", "Japan"),
    ("AA", "Jordan"),
    ("AA", "Kazakhstan"),
    ("AA", "Kenya"),
    ("AA", "Kiribati"),
    ("CC", "Kuwait"),
    ("AA", "Kyrgyzstan"),
    ("AA", "Laos"),
    ("AA", "Latvia"),
    ("BB", "Lebanon"),
    ("AA", "Lesotho"),
    ("AA", "Liberia"),
    ("AA", "Libya"),
    ("CC", "Liechtenstein"),
    ("AA", "Lithuania"),
    ("CC", "Luxembourg"),
    ("AA", "Macedonia"),
    ("AA", "Madagascar"),
    ("AA", "Malawi"),
    ("BB", "Malaysia"),
    ("AA", "Maldives"),
    ("AA", "Mali"),
    ("CC", "Malta"),
    ("AA", "Marshall Islands"),
    ("AA", "Mauritania"),
    ("BB", "Mauritius"),
    ("BB", "Mexico"),
    ("AA", "Micronesia"),
    ("AA", "Moldova"),
    ("CC", "Monaco"),
    ("AA", "Mongolia"),
    ("AA", "Morocco"),
    ("AA", "Mozambique"),
    ("AA", "Myanmar"),
    ("AA", "Namibia"),
    ("AA", "Nauru"),
    ("AA", "Nepal"),
    ("CC", "Netherlands"),
    ("CC", "New Zealand"),
    ("AA", "Nicaragua"),
    ("AA", "Niger"),
    ("AA", "Nigeria"),
    ("AA", "North Korea"),
    ("CC", "Northern Ireland"),
    ("CC", "Northern Mariana Islands"),
    ("CC", "Norway"),
    ("BB", "Oman"),
    ("AA", "Pakistan"),
    ("BB", "Palau"),
    ("AA", "Palestinian Territory"),
    ("AA", "Panama"),
    ("AA", "Papua New Guinea"),
    ("BB", "Paraguay"),
    ("AA", "Peru"),
    ("AA", "Philippines"),
    ("AA", "Poland"),
    ("CC", "Portugal"),
    ("BB", "Puerto Rico"),
    ("CC", "Qatar"),
    ("AA", "Republic of the Congo"),
    ("AA", "Romania"),
    ("AA", "Russia"),
    ("AA", "Rwanda"),
    ("BB", "Saint Kitts and Nevis"),
    ("AA", "Saint Lucia"),
    ("AA", "Saint Vincent and the Grenadines"),
    ("AA", "San Marino"),
    ("AA", "Sao Tome and Principe"),
    ("CC", "Saudi Arabia"),
    ("CC", "Scotland"),
    ("AA", "Senegal"),
    ("BB", "Seychelles"),
    ("AA", "Sierra Leone"),
    ("CC", "Singapore"),
    ("AA", "Slovakia"),
    ("BB", "Slovenia"),
    ("AA", "Solomon Islands"),
    ("AA", "Somalia"),
    ("BB", "South Africa"),
    ("AA", "South Korea"),
    ("CC", "Spain"),
    ("AA", "Sri Lanka"),
    ("AA", "Sudan"),
    ("AA", "Suriname"),
    ("CC", "Sweden"),
    ("CC", "Switzerland"),
    ("BB", "Syrian"),
    ("BB", "Taiwan"),
    ("AA", "Tajikistan"),
    ("AA", "Tanzania"),
    ("BB", "Thailand"),
    ("AA", "Togo"),
    ("AA", "Tonga"),
    ("AA", "Trinidad and Tobago"),
    ("BB", "Tunisia"),
    ("BB", "Turkey"),
    ("AA", "Turkmenistan"),
    ("AA", "Tuvalu"),
    ("CC", "U.S. military bases"),
    ("AA", "Uganda"),
    ("AA", "Ukraine"),
    ("CC", "United Arab Emirates"),
    ("CC", "United Kingdom"),  # (No. Ireland, Scotland, and Wales)
    ("BB", "Uruguay"),
    ("AA", "Uzbekistan"),
    ("AA", "Vanuatu"),
    ("BB", "Venezuela"),
    ("AA", "Vietnam"),
    ("CC", "Virgin Islands"),
    ("AA", "W. Samoa"),  # not here
    ("CC", "Wales"),
    ("AA", "Yemen")
)

# Members with entries in iMIS Activity table with a product code of
# COMMITTEE/{one of the following} as a test for "Leadership"
LEADERSHIP_COMMITTEE_PRODUCT_CODES = (
    'AICP COLLEGE F',
    'AICP STUD AW',
    'AICP_COMM',
    'AMICUS CURIAE',
    'APA MEMBERSHIP',
    'APA_NOMINATING',
    'AUDIT',
    'AWARDS JURY',
    'AWARDS TF',
    'BCP PARTNERS',
    'BCP WORK TEAM',
    'BIG CITY PLN DI',
    'BOARD',
    'CAPS_CMTE',
    'CATF',
    'CH ADMIN',
    'CH COMMUNS',
    'CH WEBMASTERS',
    'CHAP NEWS ED',
    'CHAP PDO',
    'CHAP PROXIES',
    'CHAP TREAS',
    'CHAP/DIV WEB DE',
    'CHAP_PRES',
    'CHAPT AK',
    'CHAPT AL',
    'CHAPT AR',
    'CHAPT AZ',
    'CHAPT CA',
    'CHAPT CO',
    'CHAPT CT',
    'CHAPT DE',
    'CHAPT FL',
    'CHAPT GA',
    'CHAPT HI',
    'CHAPT IA',
    'CHAPT IL',
    'CHAPT IN',
    'CHAPT KS',
    'CHAPT KY',
    'CHAPT LA',
    'CHAPT MA',
    'CHAPT MD',
    'CHAPT MI',
    'CHAPT MN',
    'CHAPT MO',
    'CHAPT MS',
    'CHAPT NC',
    'CHAPT NCAC',
    'CHAPT NE',
    'CHAPT NJ',
    'CHAPT NM',
    'CHAPT NME',
    'CHAPT NV',
    'CHAPT NYM',
    'CHAPT NYU',
    'CHAPT OH',
    'CHAPT OK',
    'CHAPT OR',
    'CHAPT PA',
    'CHAPT RI',
    'CHAPT SC',
    'CHAPT TN',
    'CHAPT TX',
    'CHAPT UT',
    'CHAPT VA',
    'CHAPT WA',
    'CHAPT WCC',
    'CHAPT WI',
    'CHAPT WV',
    'CMTY PORTAL',
    'CPA TF',
    'CPC COMMUNICAT',
    'CPC EDUCATION',
    'CPC EXEC CMTE',
    'CPC MEMBERSHIP',
    'CPC POLICY',
    'CPC PRESIDENTS',
    'DC BYLAWS',
    'DC COMM',
    'DC EDUCATION',
    'DC FIN TF',
    'DC GRANTS',
    'DC IG TF',
    'DC MEMBERSHIP',
    'DC NEWMEM TF',
    'DC NOM',
    'DC PERF',
    'DC POLICY',
    'DESIGN AND POLI',
    'DEV PLAN BUDGET',
    'DIV COUNCIL',
    'DIV PROXIES',
    'DIV SEC',
    'DIV TREAS',
    'DIV WEBMGRS',
    'DIV-CPD LDR',
    'DIV-CPM LDR',
    'DIV-EDD LDR',
    'DIV-ENRE LDR',
    'DIV-FED LDR',
    'DIV-GALIP LDR',
    'DIV-HCD LDR',
    'DIV-HMDR LDR',
    'DIV-INTL LDR',
    'DIV-LAP LDR',
    'DIV-NEW-LDRS',
    'DIV-NUD LDR',
    'DIV-PBCD LDR',
    'DIV-PLD LDR',
    'DIV-PPD LDR',
    'DIV-PRIV LDR',
    'DIV-PWD LDR',
    'DIV-RIPD LDR',
    'DIV-SCD LDR',
    'DIV-STAR LDR',
    'DIV-TECH LDR',
    'DIV-TPD LDR',
    'DIV-URB LDR',
    'DIV_COUNCIL_EXE',
    'DIVERSITY TF',
    'EDUCATION C',
    'GOVERNANCE',
    'GP IN A',
    'ETHICS',
    'EXAM',
    'EXEC CMTE',
    'EXECUTIVE',
    'FOUNDATION',
    'FOUNDATION FC',
    'FOUNDATION GC',
    'FOUNDATION NC',
    'INCOMING PRES',
    'INFRA WG',
    'INTERNATIONAL',
    'LDRSHP DEVP TF',
    'LEG LIAIS',
    'LEGIS POLICY',
    'MEMBER CHAIR',
    'MEMBERSHIP',
    'NATL PLAN CMM',
    'PDO',
    'POC',
    'PSO STUREPS',
    'SITE',
    'SRC C',
    'WPN CONTENT AND',
    'WPN EDUCATION',
    'WPN STEERING'
)


# APA Company IDs in iMIS Name
APA_COMPANY_IDS = ("119523", "050501")


class APACompanyIDs(Enum):

    CHICAGO_OFFICE = "119523"

    DC_OFFICE = "050501"


class MyAPAMessages(Enum):

    ADDRESS_CHANGE_SUCCESS = "You've successfully updated your address information."


class MyOrgMessages(Enum):

    ADDRESS_CHANGE_SUCCESS = "You've successfully updated your organization's address information."
    CONTACT_INFO_CHANGE_SUCCESS = "You've successfully updated your organization's contact information."


UNITED_STATES = "United States"
