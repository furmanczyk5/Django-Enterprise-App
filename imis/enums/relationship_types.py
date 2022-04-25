from enum import Enum


class ImisRelationshipTypes(Enum):
    """
    table name: Relationship_Types
    """

    # Has as the company's administrative contact, this individual
    ADMIN_C = "ADMIN_C"
    ADMIN_C_RECIPROCAL = "ADMIN_I"

    # Is the administrative contact for their company
    ADMIN_I = "ADMIN_I"
    ADMIN_I_LABEL = "General Admin"
    ADMIN_I_RECIPROCAL = "ADMIN_C"

    # Has as the company's billing contact, this individual
    BILLING_C = "BILLING_C"
    BILLING_C_RECIPROCAL = "BILLING_I"

    # Is the billing contact for their company
    BILLING_I = "BILLING_I"
    BILLING_I_RECIPROCAL = "BILLING_C"

    # Has as the company's CM contact, this individual
    CM_C = "CM_C"
    CM_C_RECIPROCAL = "CM_I"

    # Is the CM Contact for the Company
    CM_I = "CM_I"
    CM_I_LABEL = "CM Admin"
    CM_I_RECIPROCAL = "CM_C"

    BLANK_LABEL = ''
