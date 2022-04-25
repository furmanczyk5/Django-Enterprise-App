from enum import Enum


class ProviderApplicationStatus(Enum):

    APPROVED = 'A'
    A_LABEL = "Approved"

    DEFERRED = 'D'
    D_LABEL = "Deferred"

    SUBMITTED = 'S'
    S_LABEL = "Submitted"

    INCOMPLETE = 'I'
    I_LABEL = "Incomplete"


class ProviderApplicationReviewStatus(Enum):

    DUE = "DUE"

    REVIEWING = "REVIEWING"

    COMPLETE = "COMPLETE"

    LOCKED = "LOCKED"


class ProviderObjectivesStatus(Enum):

    ALWAYS = "ALWAYS"

    SOMETIMES = "SOMETIMES"

    NEVER = "NEVER"


class ProviderRegistrationType(Enum):

    CM_PER_CREDIT = "CM_PER_CREDIT"
    CM_PER_CREDIT_LABEL = "Per-Credit"

    CM_UNLIMITED_1 = "CM_UNLIMITED_1"
    CM_UNLIMITED_1_LABEL = "Annual Unlimited - Government and University Rate : $1,995 + $95 registration fee"

    CM_UNLIMITED_INHOUSE = "CM_UNLIMITED_INHOUSE"
    CM_UNLIMITED_INHOUSE_LABEL = "In House Annual Unlimited (for employee training only) : $475 + $95 registration fee"

    CM_UNLIMITED_NONPROFIT_1 = "CM_UNLIMITED_NONPROFIT_1"
    CM_UNLIMITED_NONPROFIT_1_LABEL = "Annual Unlimited (nonprofit, less than $500,000) : $945 + $95 registration fee"

    CM_UNLIMITED_NONPROFIT_2 = "CM_UNLIMITED_NONPROFIT_2"
    CM_UNLIMITED_NONPROFIT_2_LABEL = "Annual Unlimited (nonprofit, $500,000 to $5M) : $1,995 + $95 registration fee"

    CM_UNLIMITED_NONPROFIT_3 = "CM_UNLIMITED_NONPROFIT_3"
    CM_UNLIMITED_NONPROFIT_3_LABEL = "Annual Unlimited (nonprofit, $5M to 15M) : $2,995 + $95 registration fee"

    CM_UNLIMITED_NONPROFIT_4 = "CM_UNLIMITED_NONPROFIT_4"
    CM_UNLIMITED_NONPROFIT_4_LABEL = "Annual Unlimited (nonprofit, over $15M) : $5,145 + $95 registration fee"

    CM_UNLIMITED_PARTNER = "CM_UNLIMITED_PARTNER"
    CM_UNLIMITED_PARTNER_LABEL = "Unlimited registration through partner organization : $95"

    CM_UNLIMITED_SMALL = "CM_UNLIMITED_SMALL"
    CM_UNLIMITED_SMALL_LABEL = "For-Profit and Not-for-Profit Providers with gross revenue < $500K : $1,254"

    CM_UNLIMITED_MEDIUM = "CM_UNLIMITED_MEDIUM"
    CM_UNLIMITED_MEDIUM_LABEL = "Universities and  Governments - For-Profit and Not-for-Profit Providers with gross revenue $500K−$5M : $2,461"

    CM_UNLIMITED_LARGE = "CM_UNLIMITED_LARGE"
    CM_UNLIMITED_LARGE_LABEL = "For-Profit and Not-for-Profit Providers with gross revenue $5M−$15M : $3,611"

    CM_UNLIMITED_LARGEST = "CM_UNLIMITED_LARGEST"
    CM_UNLIMITED_LARGEST_LABEL = "For-Profit and Not-for-Profit Providers with gross revenue > $15M : $6,084"
