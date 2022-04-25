# DATA NEEDED

# TODO

# - maybe... mark is_leadership on contact record for convenience? (also a new field)
# Could it be a property instead? How will it auto-update if changed in iMIS?

# MODELS THAT USE PERMISSION GROUPS:
# - content - permission_groups
# - product - future_groups
# - product price - required_groups
# - product price - exclude_groups
# - directory - who can see the directory
# - directory - who is included in the directory (to depreciate)

# NEXT UP: 
# - set staff team data
# - return to fix IsConferenceContact
# - update directories based on committees?
# - cm logging group conditions
# - check with Rose for chapter conference admin access
# - look at PAS products for various scenarios

from django.utils import timezone

from myapa.models.constants import APA_COMPANY_IDS, LEADERSHIP_COMMITTEE_PRODUCT_CODES


class GroupCondition(object):
    condition_args = ()
    condition_kwargs = None

    def __init__(self, *args, **kwargs):
        self.condition_args = args or self.condition_args
        self.condition_kwargs = kwargs or self.condition_kwargs or {}

    def has_group(self, contact):
        return False


class NotCondition(GroupCondition):
    sub_condition = None

    def __init__(self, sub_condition, *args, **kwargs):
        self.sub_condition = sub_condition or self.sub_condition
        super().__init__(*args, **kwargs)

    def has_group(self, contact):
        return not self.sub_condition.has_group(contact)


class HasMemberType(GroupCondition):
    def has_group(self, contact):
        try:
            return contact._cached_imis_name.member_type in self.condition_args
        # This should theoretically only happen when bulk-updating users
        # in a script, and not when anyone actually tries to log in...
        except AttributeError:
            return False


# TO DO: should look at iMIS COMPANY (not django contact company)
# Update: Refactored imis sync now creates the company_fk if the
# user has CO_ID set in iMIS Name table
# TODO: is that good/reliable enough? Is CO_ID manually set by membership?
class HasCompanyMemberType(GroupCondition):
    def has_group(self, contact):
        company = contact.company_fk
        if company is None:
            return False
        return company.member_type in self.condition_args


class HasSubscription(GroupCondition):
    def has_group(self, contact):
        contact_product_codes = [
            s.product_code for s in contact._cached_imis_subscriptions
        ]
        return any(x in contact_product_codes for x in self.condition_args)


class HasPaidSubscription(GroupCondition):
    """
    TIL that status='A' by itself is not a valid test for an active member.
    They can still be 'A' but we have to check the paid_thru date as well.
    """
    def has_group(self, contact):
        contact_product_codes = [
            s.product_code for s in contact._cached_imis_paid_subscriptions
        ]
        return any(x in contact_product_codes for x in self.condition_args)


# TO DO pull from iMIS Subscription table (for the related COMPANY subscriptions) instead of django
# ALSO TODO: What does this do/is intended to do differently than HasSubscription?
class HasCompanySubscription(GroupCondition):
    def has_group(self, contact):
        company = contact.company_fk
        if not company:
            return False
        else:
            company_product_codes = [s.product_code for s in company.get_imis_subscriptions(status='A')]
            return any(x in company_product_codes for x in self.condition_args)


class HasSubscriptionProductType(GroupCondition):
    def has_group(self, contact):
        contact_product_types = [s.prod_type for s in contact._cached_imis_paid_subscriptions]
        return any(x in contact_product_types for x in self.condition_args)


class HasCommittee(GroupCondition):
    def has_group(self, contact):
        committees = [
            s.product_code.replace('COMMITTEE/', '') for s in contact._cached_imis_activities
            if s.product_code[:10] == 'COMMITTEE/'
            and (isinstance(s.thru_date, timezone.datetime) and s.thru_date > timezone.now())
        ]
        return any(x in committees for x in self.condition_args)


class HasActivityProduct(GroupCondition):
    def has_group(self, contact):
        product_codes = [s.product_code for s in contact._cached_imis_activities]
        return any(x in product_codes for x in self.condition_args)


class HasUsername(GroupCondition):
    def has_group(self, contact):
        return contact.user.username in self.condition_args


# TO DO pull company CO_ID from iMIS instead of django
# ALSO (to confirm with Karl)... maybe should look at STF member type as well?
# Update: Refactored imis sync now creates the company_fk if the
# user has CO_ID set in iMIS Name table
# TODO: is that good/reliable enough? Is CO_ID manually set by membership?
# UPDATE: Karl indicated this is probably the best choice; will proceed
# under this assumption
class IsStaff(GroupCondition):
    def has_group(self, contact):
        name = contact._cached_imis_name
        if name is None:
            return False
        return name.co_id in APA_COMPANY_IDS


# TO DO: update to pull from new STAFF_TEAMS field to be added to iMIS (assume on Name table)
class HasStaffTeam(GroupCondition):
    def has_group(self, contact):
        if contact.staff_teams:
            return self.condition_args[0] in contact.staff_teams.split(',')
        else:
            return False


class HasAttrs(GroupCondition):
    """
    tests whether contact has particular attributes, and/or for specific attribute values.
    ... args used to test whether an attribute exists and doesn't evaluate as false (e.g. not None or empty string)
    ... kwargs used to test specific attribute values
    """

    def has_group(self, contact):
        for name in self.condition_args:
            value = getattr(contact, name, None)
            if not value:
                return False
        for name, value in self.condition_kwargs.items():
            if getattr(contact, name, None) is None or getattr(contact, name, None) != value:
                return False
        return True


# TO DO... change to not use filter statement, or remove entirely
# TODO re: above - Why?
class HasRelatedRecord(GroupCondition):
    """
    for querying django-db related table info (e.g. if a contact has a CM log with certain properties)
    """
    related_name = None

    def __init__(self, related_name, *args, **kwargs):
        self.related_name = related_name or self.related_name
        super().__init__(*args, **kwargs)

    def has_group(self, contact):
        return getattr(contact, self.related_name).filter(**self.condition_kwargs).exists()


class IsLeadership(HasCommittee):
    """
    Group condition for APA leadership. Just a specific case of HasCommitee for a bunch of
    committee codes... but it's used repeatedly it's useful to have its own pre-defined condition.
    """

    def __init__(self, **kwargs):
        super().__init__(*LEADERSHIP_COMMITTEE_PRODUCT_CODES, **kwargs)


class IsAttending(GroupCondition):
    def has_group(self, contact):
        # UPDATE: This is now querying iMIS, by looking at the
        # Orders and Order_Lines table
        order_lines = contact._cached_imis_order_lines
        if not order_lines:
            return False
        product_codes = [x.PRODUCT_CODE for x in order_lines]
        return any(x in product_codes for x in self.condition_args)


class MultipleConditions(GroupCondition):
    conditions = ()
    logical = "or"

    def __init__(self, *args, **kwargs):
        self.conditions = args or self.conditions
        self.logical = kwargs.pop("logical", "or")
        super().__init__(*args, **kwargs)

    def has_group(self, contact):
        return_value = False
        for condition in self.conditions:
            condition_met = condition.has_group(contact)
            if self.logical == "or" and condition_met:
                return True
            elif self.logical == "and" and not condition_met:
                return False
            elif self.logical == "and" and condition_met:
                return_value = True
        return return_value


class IsMember(MultipleConditions):
    conditions = (
        HasPaidSubscription("APA"),
        HasCompanyMemberType("DVN"),  # TO DO.. confirm DVN access with Karl, also, include CHP?
    )


class IsAICP(HasSubscription):
    condition_args = ("AICP", "AICP_PRORATE")
