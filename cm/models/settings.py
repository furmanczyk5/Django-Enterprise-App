# CM GLOBALS
# import datetime
from decimal import Decimal
# from enum import Enum
# LOOKS LIKE THIS CAUSES CIRCULAR IMPORT ERROR:
# from cm.models import LOG_STATUSES

# tuples, enums, dicts

TOTAL_CREDITS_REQUIRED = Decimal("32.00")
REDUCED_TOTAL_CREDITS_REQUIRED = Decimal("16.00")

REDUCED_TOTAL_CREDITS_REQUIRED_STATUSES = ('E_13',)
NO_CREDITS_REQUIRED_STATUSES = ('E_01',)
# HAVE one global for the old amount, the logic will grab this instead of the specific global (e.g.
# LAW_CREDITS_REQUIRED) if the reporting period is < jan2024
OLD_CREDITS_REQUIRED = Decimal("1.5")

LAW_CREDITS_REQUIRED = Decimal("1.0")
ETHICS_CREDITS_REQUIRED = Decimal("1.0")
EQUITY_CREDITS_REQUIRED = Decimal("1.0")
TARGETED_CREDITS_REQUIRED = Decimal("1.0")
TARGETED_CREDITS_TOPIC = "SUSTAINABILITY_AND_RESILIENCE"

# the period from which members start seeing new reporting system: ??
# FIRST_NEW_REPORTING_PERIOD = "JAN2024"
# REPORTING_PERIOD_CUTOFF_DATE = datetime.datetime(2023,12,31)

# Formalize the rules that tie log status to data, in a dict?
# e.g. status E_13 means 16 required credits ... ?
# each relationship will be its own dict
# def get_total_credits_required(key):
#     if key in REDUCED_TOTAL_CREDITS_REQUIRED_STATUSES:
#         return REDUCED_TOTAL_CREDITS_REQUIRED
#     elif key in NO_CREDITS_REQUIRED_STATUSES:
#         return Decimal("0.00")
#     else:
#         return TOTAL_CREDITS_REQUIRED

# gtcr=get_total_credits_required

# TOTAL_CREDITS_REQUIRED = dict(zip(LOG_STATUSES.keys(), list_of_values))
# LOG_STATUS_TO_TOTAL_CREDITS_REQUIRED = dict((key, gtcr(key)) for key in [s[0] for s in LOG_STATUSES])
# print("--------------------------------------- ")
# print(LOG_STATUS_TO_TOTAL_CREDITS_REQUIRED)
