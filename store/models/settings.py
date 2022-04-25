from enum import Enum


# TO DO... alphabetize!
PRODUCT_TYPES = (
    ('PRODUCT', 'Default Product Type'),
    ('CANCELLATION', 'Cancellation/Refund'),
    ('CANCELLATION_FEE', 'Cancellation Fee($50)'),
    ('EVENT_REGISTRATION', 'Event Registration'),
    ('PUBLICATION_SUBSCRIPTION', 'Publication/Subscription'),
    ('ACTIVITY_TICKET', 'Event Activity Ticket'),
    ('CM_REGISTRATION', 'CM Annual Registrations'),
    ('CM_PER_CREDIT', 'CM Per-Credit Payments'),
    ('DUES', 'Membership Dues'),
    ('DIGITAL_PUBLICATION', 'Digital Publications'),
    ('CHAPTER', 'Chapter'),
    ('DIVISION', 'Division'),
    ('BOOK', 'Book'),  # consider removing now that bookstore gone
    ('DONATION', 'Donation'),
    ('EBOOK', 'E-book'), # consider removing now that bookstore gone
    ('STREAMING', 'Streaming'),
    ('AICP_CANDIDATE_ENROLLMENT', 'AICP Candidate Enrollment'),
    ('EXAM_APPLICATION', 'Exam Application'),
    ('EXAM_REGISTRATION', 'Exam Registration'),
    ('SHIPPING', 'Shipping'), # consider removing now that bookstore gone
    ('TAX', 'Tax'), # consider removing now that bookstore gone
    ('AWARD', 'Awards'),
    ('ADJUSTMENT', 'Adjustment'),
    ('JOB_AD', 'Job Ad'),
    ('RESEARCH_INQUIRY', 'Research Inquiry'),
    ('LEARN_COURSE', 'APA Learn Course'),
)


class ProductCode:
    MEMBERSHIP_MEM = "MEMBERSHIP_MEM"
    MEMBERSHIP_AICP = "MEMBERSHIP_AICP"
    MEMBERSHIP_AICP_PRORATE = "MEMBERSHIP_AICP_PRORATE"


class ProductTypes(Enum):

    ACTIVITY_TICKET = "ACTIVITY_TICKET"
    ACTIVITY_TICKET_LABEL = "Event Activity Ticket"

    ADJUSTMENT = "ADJUSTMENT"
    ADJUSTMENT_LABEL = "Adjustment"

    AICP_CANDIDATE_ENROLLMENT = "AICP_CANDIDATE_ENROLLMENT"
    AICP_CANDIDATE_ENROLLMENT_LABEL = "AICP Candidate Enrollment"

    AWARD = "AWARD"
    AWARD_LABEL = "Award"

    CANCELLATION = "CANCELLATION"
    CANCELLATION_LABEL = "Cancellation/Refund"

    CANCELLATION_FEE = "CANCELLATION_FEE"
    CANCELLATION_FEE_LABEL = "Cancellation Fee ($50)"

    CHAPTER = "CHAPTER"
    CHAPTER_LABEL = "Chapter"

    CM_PER_CREDIT = "CM_PER_CREDIT"
    CM_PER_CREDIT_LABEL = "CM Per-Credit Payment"

    CM_REGISTRATION = "CM_REGISTRATION"
    CM_REGISTRATION_LABEL = "CM Annual Registration"

    DIGITAL_PUBLICATION = "DIGITAL_PUBLICATION"
    DIGITAL_PUBLICATION_LABEL = "Digital Publication"

    DIVISION = "DIVISION"
    DIVISION_LABEL = "Division"

    DONATION = "DONATION"
    DONATION_LABEL = "Donation"

    DUES = "DUES"
    DUES_LABEL = "Membership Dues"

    EVENT_REGISTRATION = "EVENT_REGISTRATION"
    EVENT_REGISTRATION_LABEL = "Event Registration"

    EXAM_APPLICATION = "EXAM_APPLICATION"
    EXAM_APPLICATION_LABEL = "Exam Application"

    EXAM_REGISTRATION = "EXAM_REGISTRATION"
    EXAM_REGISTRATION_LABEL = "Exam Registration"

    JOB_AD = "JOB_AD"
    JOB_AD_LABEL = "Job Ad"

    LEARN_COURSE = "LEARN_COURSE"
    LEARN_COURSE_LABEL = "APA Learn Course"

    PRODUCT = "PRODUCT"
    PRODUCT_LABEL = "Default Product Type"

    PUBLICATION_SUBSCRIPTION = "PUBLICATION_SUBSCRIPTION"
    PUBLICATION_SUBSCRIPTION_LABEL = "Publication/Subscription"

    RESEARCH_INQUIRY = "RESEARCH_INQUIRY"
    RESEARCH_INQUIRY_LABEL = "Research Inquiry"

    STREAMING = "STREAMING"
    STREAMING_LABEL = "Streaming"


PAYMENT_METHODS = (
    ('CC', 'Credit Card'),
    ('CC_REFUND', 'Credit Card Refund'),
    ('CHECK', 'Check'),
    ('CHECK_REFUND', 'Check Refund'),
    ('REBATE', 'Chapter or division rebate'),
    ('CASH', 'Cash'),
)


class PaymentMethods(Enum):

    CASH = "CASH"
    CASH_LABEL = "Cash"

    CC = "CC"
    CC_LABEL = "Credit Card"

    CC_REFUND = "CC_REFUND"
    CC_REFUND_LABEL = "Credit Card Refund"

    CHECK = "CHECK"
    CHECK_LABEL = "Check"

    CHECK_REFUND = "CHECK_REFUND"
    CHECK_REFUND_LABEL = "Check Refund"

    REBATE = "REBATE"
    REBATE_LABEL = "Chapter or division rebate"


CARD_TYPES = (
    ('VISA', 'Visa'),
    ('MC', 'Mastercard'),
    ('AMEX', 'American Express'),
)

# TO DO: naming convention... this should be plural
ORDER_STATUS = (
    ('NOT_SUBMITTED', 'Not Yet Submitted'),
    ('SUBMITTED', 'Submitted'),
    # ('PENDING', 'Pending'), # should we use this....?
    ('PROCESSED', 'Processed (archived)'), # what to do with these old orders?
    ('CANCELLED', 'Cancelled'), # used for order import
    ('SUBMITTED_FAILED', 'Submitted, not in iMIS'), # payment accepted, in django, but did not write to iMIS.
)


class OrderStatuses(Enum):

    CANCELLED = "CANCELLED"
    CANCELLED_LABEL = "Cancelled"

    NOT_SUBMITTED = "NOT_SUBMITTED"
    NOT_SUBMITTED_LABEL = "Not Yet Submitted"

    PROCESSED = "PROCESSED"
    PROCESSED_LABEL = "Processed (archived)"

    SUBMITTED = "SUBMITTED"
    SUBMITTED_LABEL = "Submitted"

    SUBMITTED_FAILED = "SUBMITTED_FAILED"
    SUBMITTED_FAILED_LABEL = "Submitted, not in iMIS"


SUBSCRIPTION_STATUSES = (
    ("A", "Active"),
    ("I", "Inactive"),
    # TO DO... more statuses?
)

# the order that product_types are processed (imis api calls)

PRODUCT_TYPE_PRIORITY = ['DUES','CHAPTER','EVENT_REGISTRATION','EXAM_REGISTRATION','EXAM_APPLICATION','AICP_CANDIDATE_ENROLLMENT','JOB_AD','PUBLICATION_SUBSCRIPTION','CM_REGISTRATION','CM_PER_CREDIT','LEARN_COURSE','DIVISION','ACTIVITY_TICKET','ADJUSTMENT','AWARD','BOOK', 'STREAMING', 'DIGITAL_PUBLICATION','EBOOK', 'CANCELLATION', 'CANCELLATION_FEE','SHIPPING','TAX','DONATION','RESEARCH_INQUIRY']

# DUPLICATED IN EXAM/ADMIN BECAUSE OF CIRCULAR IMPORT
CAND_ENROLL_EMAIL_TEMPLATES = {
    "A": "APPROVED_CANDIDATE",
    "EN": "ENROLLED_CANDIDATE",
    "I": "EXAM_APPLICATION_AICP_INCOMPLETE",
    "P": "PENDING_CANDIDATE",
}

EVENT_PRICING_CUTOFF_TYPES = (
    ("EARLY", "Early"),
    ("REGULAR", "Regular"),
    ("LATE", "Late"),
)

DONOR_RANGES = (
    (5000, 5000000, "Visionary"),
    (2500, 4999, "Benefactor"),
    (1000, 2499, "Advocate"),
    (500, 999, "Partner"),
    (250, 499, "Leader"),
    (100, 249, "Friend"),
    (1, 99, "Supporter"),
)

GENERIC_IMIS_PRODUCTS = (
    "BOOK",
    "STREAM_LMS"
)


class AutodraftBillFrequency:

    ANNUAL = 12
    SEMIANNUAL = 6
    QUARTERLY = 3
    MONTHLY = 1
    WEEKLY = -4

    def get_divisor(self, frequency: int) -> int:
        divisors = {
            self.ANNUAL: 1,
            self.SEMIANNUAL: 2,
            self.QUARTERLY: 4,

            # According to the APA Membership department, there are 10 months in a year
            self.MONTHLY: 10,

            self.WEEKLY: 52
        }
        return divisors[frequency]


class AutodraftBillPeriod:

    ANNUAL = 12
    MONTHLY = 10

    MIN_PERIOD = 6
    MAX_PERIOD = 12

    @staticmethod
    def is_valid_range(period):
        return AutodraftBillPeriod.MIN_PERIOD <= period <= AutodraftBillPeriod.MAX_PERIOD


class BluePayMode:

    LIVE = "LIVE"
    TEST = "TEST"
