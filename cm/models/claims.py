# FLAGGED FOR REFACTORING: CM CONSOLIDATION
# import datetime
import pytz
import requests
from django.db import models
from django.db.models import Sum, F, Q
from django.db.models.functions import Coalesce
from django.utils import timezone

# FLAGGED FOR REFACTORING: CM CONSOLIDATION
from cm.models import settings as cm_settings
from content.models.settings import TARGETED_CREDITS_TOPICS
from comments.models import Comment
from content.models import BaseContent
from imis.models import Name, Subscriptions
from myapa.models.contact_role import ContactRole
from planning.models_subclassable import SubclassableModel

LOG_STATUSES = (
    ("A", "Active"),
    ("G","In Grace Period"),
    ("R","Reinstatement"),
    ("C","Completed and Closed"),
    ("I","Inactive"), # Unavailable to AICP Candidate until enrollment is approved
    ("E_01","Exempt - Retired;"),
    ("E_02","Exempt - Unemployed members"),
    ("E_03","Exempt - Planners practicing outside of U.S."),
    ("E_06","Exempt - Parental leave"),
    ("E_07","Exempt - Military service leave"),
    ("E_09","Exempt - Health leave"),
    ("E_10","Exempt - Care leave"),
    ("E_11","Exempt - Foreign residency"),
    ("E_12","Exempt - Other (case-by-case)"),
    ("E_13","Exempt - Voluntary Life option"),
    ("E_14","Exempt - COVID Extreme Hardship"),
    ("D", "Dropped"),
    ("RA","Reinstatement Amnesty"),
)

SPEAKER_RATING_LEVELS = (
    (1, "1 star"),
    (2, "2 stars"),
    (3, "3 stars"),
    (4, "4 stars"),
    (5, "5 stars")
)

AUTHOR_TYPES = (
    ("PLANNING_ARTICLE", "Planning-related Article"),
    ("PLANNING_JOURNAL_ARTICLE", "Planning-related Journal Article"),
    ("PLANNING_BOOK", "Planning-related Non-fiction Book")
)


class Period(BaseContent):
    """
    stores each 2-year CM reporting period during which AICP members
    are required to log credits.
    """
    begin_time = models.DateTimeField("begin time", null=True, blank=True)
    end_time = models.DateTimeField("end time", null=True, blank=True)
    grace_end_time = models.DateTimeField("grace period end time", null=True, blank=True)
    rollover_from = models.OneToOneField(
        "cm.Period",
        related_name="rollover_to",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )


    def rollover_exempt_assign_grace_status(self, user_ids = []):
        """

        NOTE: THERE NEEDS TO BE AN ETHICS AND LAW CREDIT CHECK ADDED TO THE ROLLOVER METHOD IN LOG! DOING THESE CHECKS MANUALLY FOR NOW!
            ALSO SHOULD GET CREDITS REQUIRED IN THE ROLLOVER  METHOD

        Rollover into the given passed reporting period with exception status and credit requirements met.
        Retired (E_01) will be given a 0 CM requirement.
        Unemployed (E_O2) will not be manually moved. They will be moved into grace period if credit requirements not met.
        Voluntary Life (E_13) will be given a 16 CM credit requirement.
        Outside US (E_03) will be given a 32 CM requirement and will no longer have the exemption.
        Active (A) will give given a 32 CM requirement.

        New methods should be created by log status (e.g. rollover e_01, rollover E_02, etc.) The current setup is hard to follow.
        """
        if user_ids:
            logs = Log.objects.filter(period=self, status__in=("E_01", "E_02", "E_03", "E_13", "E_14", "A"), is_current= True, contact__user__username__in = user_ids)
        else:
            logs = Log.objects.filter(period=self, status__in=("E_01", "E_02", "E_03", "E_13", "E_14", "A"), is_current= True)

        for log in logs:

            try:
                # per William - check DESIGNATION for creating new logs. This is change from changing the PAID_THRU date
                designation = Name.objects.get(id=log.contact.user.username).designation

                credits_overview = log.credits_overview()
                credits_needed = credits_overview.get("general_needed")
                law_credits_needed = credits_overview.get("law_needed")
                ethics_credits_needed = credits_overview.get("ethics_needed")

                # FLAGGED FOR REFACTORING: CM CONSOLIDATION
                credits_required = 32
                law_credits_required = 1.5
                ethics_credits_required = 1.5
                # if log.period.end_time >= cm_settings.REPORTING_PERIOD_CUTOFF_DATE:
                #     law_credits_required = cm_settings.LAW_CREDITS_REQUIRED
                #     ethics_credits_required = cm_settings.ETHICS_CREDITS_REQUIRED
                # else:
                #     law_credits_required = cm_settings.OLD_CREDITS_REQUIRED
                #     ethics_credits_required = cm_settings.OLD_CREDITS_REQUIRED

                if log.status == "E_01":
                    credits_required = 0
                    law_credits_required = 0
                    ethics_credits_required = 0

                elif log.status == "E_13":
                    credits_required = 16

                # all log status should transfer over for all users who rollover / go into grace period EXCEP for E_03.
                # E_03 gets regular AICP status.
                new_log_status = log.status if log.status != "E_03" else "A"

                # rollover exempt logs who have met credit requirements
                if "AICP" in designation and credits_needed == 0 and law_credits_needed == 0 and ethics_credits_needed == 0 and log.status in ("E_01","E_03","E_13"):

                    new_log = log.close_and_rollover()
                    new_log.credits_required = credits_required
                    new_log.law_credits_required = law_credits_required
                    new_log.ethics_credits_required = ethics_credits_required
                    new_log.status = new_log_status
                    new_log.save()

                    print("ID: {0} has been rolled over into period: {1}".format(log.contact.user.username, new_log.period.code))

                # grace period for everyone else
                elif "AICP" in designation and (credits_needed != 0 or law_credits_needed != 0 or ethics_credits_needed != 0):
                    log.status = "G"
                    log.end_time = log.period.grace_end_time
                    log.save()

                    print("ID: {0} has been assigned status 'G' for the current period  {1}".format(log.contact.user.username, log.period.code))

            except Exception as e:

                print("ERROR: {0}".format(str(e)))
                pass

    def auto_rollover(self, final_rollover=False, user_ids=[]):
        """

        Auto rollover members who have not closed out their logs
        Unemployed (E_O2) will be automatically moved.
        Voluntary Life (E_13) will be given a 16 CM credit requirement.
        Active (A) and Grace (G) will give given a 32 CM requirement.
        """

        # if user_ids are passed, only auto_rollover those in the list
        if user_ids:
            logs = Log.objects.filter(period=self, status__in=("E_02", "E_13", "E_14", "A", "G"), is_current=True, contact__user__username__in = user_ids)
        else:
            logs = Log.objects.filter(period=self, status__in=("E_02", "E_13", "E_14", "A", "G"), is_current=True)

        imis_member_type_designation_check = Name.objects.filter(member_type__in=("MEM","STU","STF","LIFE"), designation__icontains="AICP").values_list("id", flat=True)

        imis_aicp_check = Subscriptions.objects.filter(product_code="AICP", status="A").values_list("id", flat=True)

        rollover_count = 0

        for log in logs:

            try:

                user_id = log.contact.user.username

                credits_overview = log.credits_overview()
                credits_needed = credits_overview.get("general_needed")
                law_credits_needed = credits_overview.get("law_needed")
                ethics_credits_needed = credits_overview.get("ethics_needed")

                credits_required = 32
                law_credits_required = 1.5
                ethics_credits_required = 1.5

                if log.status == "E_13":
                    credits_required = 16

                new_log_status = log.status if log.status == "E_13" else "A"

                # rollover exempt logs who have met credit requirements
                if user_id in imis_aicp_check and user_id in imis_member_type_designation_check and credits_needed == 0 and law_credits_needed == 0 and ethics_credits_needed == 0:

                    print("rollover log for user:" + str(log.contact.user.username))
                    rollover_count += 1

                    if final_rollover:
                        new_log = log.close_and_rollover()
                        new_log.credits_required = credits_required
                        new_log.law_credits_required = law_credits_required
                        new_log.ethics_credits_required = ethics_credits_required
                        new_log.status = new_log_status
                        new_log.save()

                        print("ID: {0} has been rolled over into period: {1}".format(log.contact.user.username,
                                                                                     new_log.period.code))

            except Exception as e:

                print("ERROR: {0}".format(str(e)))
                pass

        return "User rollover count:{0}".format(str(rollover_count))

    def drop_exempt_members(self, final_drop=False):
        """
        Drops members who have the grace/exempt status for the given period

        set final_drop=True to complete the drop.
        """

        drop_count = 0

        #now = datetime.datetime.now()

        imis_member_type_check = Name.objects.filter(member_type__in=("MEM","STU","STF","LIFE"), designation__icontains="AICP").values_list("id", flat=True)

        imis_aicp_check = Subscriptions.objects.filter(product_code="AICP", status="A").values_list("id", flat=True)


        logs_to_drop = Log.objects.filter(period=self, status__in=("G", "A", "E_02", "E_13", "E_14"), is_current=True).annotate(credit_total=Coalesce(Sum("claims__credits"), 0), law_total=Coalesce(Sum("claims__law_credits"), 0), ethics_total=Coalesce(Sum("claims__ethics_credits"), 0)).filter(Q(credits_required__gt=F("credit_total")) | Q(law_credits_required__gt=F("law_total")) | Q(ethics_credits_required__gt=F("ethics_total")))

        for x in logs_to_drop:
            user_id = x.contact.user.username

            if user_id in imis_member_type_check and user_id in imis_aicp_check:
                print("dropping log for user:" + str(x.contact.user.username))
                drop_count += 1

                if final_drop:
                    x.status = "D"
                    x.save()
                    x.imis_drop()


        return "Users dropped:{0}".format(str(drop_count))

    def __str__(self):
        return self.code if self.code is not None else "[no code]"

class Log(SubclassableModel):
    """
    stores particular logs for each member for each period, including the status and whether
    the log is the current one for which the member is reporting
    """
    contact = models.ForeignKey("myapa.Contact", related_name="cm_logs", on_delete=models.PROTECT)
    period = models.ForeignKey(Period, on_delete=models.PROTECT)
    status = models.CharField(max_length=50, choices=LOG_STATUSES, default="A")
    is_current = models.BooleanField(default=False)
    credits_required = models.DecimalField(decimal_places=2, max_digits=6, default=32)
    law_credits_required = models.DecimalField(decimal_places=2, max_digits=6, default=1.5)
    ethics_credits_required = models.DecimalField(decimal_places=2, max_digits=6, default=1.5)
    equity_credits_required = models.DecimalField(decimal_places=2, max_digits=6, blank=True, null=True)
    targeted_credits_required = models.DecimalField(decimal_places=2, max_digits=6, blank=True, null=True)
    targeted_credits_topic = models.CharField(max_length=100, choices=TARGETED_CREDITS_TOPICS, null=True, blank=True)
    begin_time = models.DateTimeField("begin time", null=True, blank=True)
    end_time = models.DateTimeField("end time", null=True, blank=True)
    reinstatement_end_time = models.DateTimeField("reinstatement end time", null=True, blank=True)
    # QUESTION... should we store a copy of the total credits claimed? Or add them up every time (as below)?

    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    def credits_overview(self):

        # note: issue with passing bit values to SQL with tedious. convert value to int:
        is_current = 1

        if not self.is_current:
            is_current = 0

        # TO DO: refactor:
        overview_dict = {}
        overview_dict["general"] = 0
        overview_dict["law"] = 0
        overview_dict["ethics"] = 0
        overview_dict["equity"] = 0
        overview_dict["targeted"] = 0
        overview_dict["self_reported"] = 0
        overview_dict["is_author"] = 0
        overview_dict["general_without_carryover"] = 0

        # additional fields for publishing to imis
        overview_dict["status"] = self.status
        overview_dict["begin_time"] = self.begin_time
        overview_dict["end_time"] = self.end_time
        overview_dict["reinstatement_end_time"] = self.reinstatement_end_time
        overview_dict["period_iscurrent"] = is_current
        overview_dict["credits_required"] = self.credits_required
        all_credits = Claim.objects.filter(log=self, is_deleted=False)

        for c in all_credits:
            overview_dict["law"] += c.law_credits or 0
            overview_dict["ethics"] += c.ethics_credits or 0
            overview_dict["equity"] += c.equity_credits or 0
            overview_dict["targeted"] += c.targeted_credits or 0
            if c.self_reported:
                overview_dict["self_reported"] += c.credits or 0
            elif c.is_author:
                overview_dict["is_author"] += c.credits or 0
            else:
                # we're only adding the credit to the total if not self-report or author... we add that later with the maximum restriction taken into account
                overview_dict["general"] += c.credits or 0
                if c.is_carryover != True:
                    overview_dict["general_without_carryover"] += c.credits or 0

        overview_dict["law_needed"] = self.law_credits_required - overview_dict["law"]
        if overview_dict["law_needed"] < 0:
            overview_dict["law_needed"] = 0
        overview_dict["ethics_needed"] = self.ethics_credits_required - overview_dict["ethics"]
        if overview_dict["ethics_needed"] < 0:
            overview_dict["ethics_needed"] = 0
        overview_dict["equity_needed"] = self.equity_credits_required or 0 - overview_dict["equity"]
        if overview_dict["equity_needed"] < 0:
            overview_dict["equity_needed"] = 0
        overview_dict["targeted_needed"] = self.targeted_credits_required or 0 - overview_dict["targeted"]
        if overview_dict["targeted_needed"] < 0:
            overview_dict["targeted_needed"] = 0
        overview_dict["targeted_credits_topic"] = self.targeted_credits_topic
        if overview_dict["self_reported"] > 8:
            overview_dict["self_reported"] = 8
        if overview_dict["is_author"] > 16:
            overview_dict["is_author"] = 16
        overview_dict["general"] += overview_dict["self_reported"]
        overview_dict["general"] += overview_dict["is_author"]
        overview_dict["general_needed"] = self.credits_required - overview_dict["general"]
        if overview_dict["general_needed"] < 0:
            overview_dict["carry_over"] = 0 - overview_dict["general_needed"]
            if overview_dict["carry_over"] > 16:
                overview_dict["carry_over"] = 16
            overview_dict["general_needed"] = 0
        else:
            overview_dict["carry_over"] = 0
        return overview_dict


    # def credits_needed(self):
    #     needed_dict = {}
    #     needed_dict["general"] = 0
    #     needed_dict["law"] = 0
    #     needed_dict["ethics"] = 0
    #     return needed_dict

    def __str__(self):
        return str(self.contact) + " | " + self.period.code if self.period.code is not None else "[no period]"

    def credits_for_carryover(self):
        return 0

    def is_active(self):
        now = timezone.now()
        # reinstatement - use the log end time to determine if this is active

        if self.status in ["G","R"]:
            log_end_time = self.reinstatement_end_time or self.end_time
            log_date_check = log_end_time>=now
        else:
            log_date_check = True

        return self.is_current and self.status not in ["D","C"] and log_date_check

    def is_complete(self):
        # TO DO: this should be implemented!
        return False

    # FLAGGED FOR REFACTORING: CM CONSOLIDATION
    # THIS MUST BE ADAPTED TO HANDLE POST-CONSOLIDATION ROLLOVERS (can use consolidation_close_and_rollover as guide)
    def close_and_rollover(self, contact=None, overview=None):
        """
        "closes" this log for the given reporting period, creates new reporting period record for the
        next reporting period, makes the new reporting period the current one, and
        rolls over credits into that reporting period
        """
        # precaution to prevent repeated closing:
        if self.credits_overview()["general_needed"] == 0:
            self.is_current = False
            self.status="C"
            self.save()

            log_contact = contact or self.contact # prevents additional query of the contact if contact has already been queried


            # TO DO... if this method were called twice for the same user/period, we would get duplicate log entries for a member
            # ... error checking needed?
            new_log = Log.objects.create(contact=log_contact, period=self.period.rollover_to, is_current=True)

            # Life members get different log status and credits required
            if Name.objects.get(id=log_contact.user.username).member_type == "LIFE":
                new_log.status = "E_13"
                new_log.credits_required = 16
                new_log.law_credits_required = 1.5
                new_log.ethics_credits_required = 1.5
                new_log.save()


            log_overview = overview or self.credits_overview() # prevents having to run credits_overview again if already run
            if log_overview["carry_over"] > 0:
                claim_carry_over_from = Claim.objects.create(contact=log_contact, log=self, verified=True,
                            is_carryover = True, title="Credits Carried Over To Following Period", credits=0-log_overview["carry_over"])
                claim_carry_over_to = Claim.objects.create(contact=log_contact, log=new_log, verified=True,
                            is_carryover = True, title="Credits Carried Over From Previous Period", credits=log_overview["carry_over"])

            return new_log
        else:
            return self


    # FLAGGED FOR REFACTORING: CM CONSOLIDATION
    def consolidation_close_and_rollover(self, contact=None, overview=None):
        """
        Special purpose method to handle one-time consolidation rollovers; after use adapt this to be new close_and_rollover()?
        """
        log_contact = contact or self.contact # prevents additional query of the contact if contact has already been queried
        current_period_code = self.period.code
        jan2022 = Period.objects.get(code="JAN2022")
        # FOR LOCAL TESTING COMMENT THIS OUT:
        jan2024 = Period.objects.get(code="JAN2024")
        # jan2024 = None

        if current_period_code == "JAN2021":
            new_period = jan2022
        elif current_period_code == "JAN2023":
            new_period = jan2024
        else:
            raise Exception("THIS LOG SHOULD NOT BE ROLLED OVER: %s" % (self))

        new_log, new_created = Log.objects.get_or_create(contact=log_contact, period=new_period, is_current=True)

        if current_period_code == "JAN2021":
            new_log.end_time = self.end_time.replace(year=2021,month=12,day=31)
            new_log.law_credits_required = cm_settings.OLD_CREDITS_REQUIRED
            new_log.ethics_credits_required = cm_settings.OLD_CREDITS_REQUIRED
            new_log.equity_credits_required = 0
            new_log.targeted_credits_required = 0
        if current_period_code == "JAN2023":
            new_log.end_time = self.end_time.replace(year=2023,month=12,day=31)
            new_log.law_credits_required = cm_settings.LAW_CREDITS_REQUIRED
            new_log.ethics_credits_required = cm_settings.ETHICS_CREDITS_REQUIRED
            new_log.equity_credits_required = cm_settings.EQUITY_CREDITS_REQUIRED
            new_log.targeted_credits_required = cm_settings.TARGETED_CREDITS_REQUIRED
            new_log.targeted_credits_topic = cm_settings.TARGETED_CREDITS_TOPIC

        if self.status in cm_settings.NO_CREDITS_REQUIRED_STATUSES:
            new_log.status = self.status
            new_log.credits_required = 0
            new_log.law_credits_required = 0
            new_log.ethics_credits_required = 0
            new_log.equity_credits_required = 0
            new_log.targeted_credits_required = 0
        elif Name.objects.get(id=log_contact.user.username).member_type == "LIFE":
            new_log.status = "E_13"
            new_log.credits_required = cm_settings.REDUCED_TOTAL_CREDITS_REQUIRED
        else:
            new_log.status = self.status
            new_log.credits_required = self.credits_required

        new_log.save()

        log_overview = overview or self.credits_overview() # prevents having to run credits_overview again if already run

        if log_overview["carry_over"] > 0:
            claim_carry_over_from, from_created = Claim.objects.get_or_create(contact=log_contact, log=self, verified=True,
                        is_carryover = True, title="Credits Carried Over To Following Period", credits=0-log_overview["carry_over"],
                        is_deleted=False)
            claim_carry_over_to, to_created = Claim.objects.get_or_create(contact=log_contact, log=new_log, verified=True,
                        is_carryover = True, title="Credits Carried Over From Previous Period", credits=log_overview["carry_over"],
                        is_deleted=False)

        # Make sure the old log doesn't show new requirements:
        self.equity_credits_required = 0
        self.targeted_credits_required = 0
        self.is_current = False
        self.status="C"
        self.save()

        return new_log

    def imis_drop(self):
        """
        Removes designation, and inactivates AICP subscription
        """

        Subscriptions.aicp_drop(user_id=self.contact.user.username, period_code=self.period.code)

        return None

    def save(self, *args, **kwargs):
        if not self.begin_time or not self.end_time:
            self.begin_time = self.period.begin_time
            self.end_time = self.period.end_time

        super(Log, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "CM log"


class CMCommentsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(comment_type__in=("CM", "LEARN_COURSE"))


class CMComment(Comment):
    objects = CMCommentsManager()

    def __str__(self):
        return self.content.title if self.content.title is not None else "[no title]"

    def save(self, *args, **kwargs):
        self.comment_type = "CM"
        super().save(*args, **kwargs)

    class Meta:
        verbose_name="CM Rating/Comment"
        proxy = True


class Claim(models.Model):
    """
    stores each cm claim that a member submits for a particular activity
    """
    contact = models.ForeignKey("myapa.Contact", related_name="cm_claims", blank=True, on_delete=models.PROTECT)
    log = models.ForeignKey(Log, related_name="claims", on_delete=models.PROTECT)

    # QUESTION... BETTER TO REFERENCE EVENT HERE OR CONTENT? ...WILL ALL e-Learning continue to be "events???"
    event = models.ForeignKey("events.Event", related_name="cm_claims", null=True, blank=True, on_delete=models.SET_NULL)

    comment = models.OneToOneField(CMComment, related_name="cm_claim", null=True, blank=True, on_delete=models.SET_NULL)
    verified = models.BooleanField(default=False)
    # CAN WE DO THIS? OR DO WE NEED TO CREATE NEW FIELDS AND MIGRATE THE DATA?
    credits = models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True, default=0) # or default to 0?
    law_credits = models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True, default=0) # or default to 0?
    ethics_credits = models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True, default=0) # or default to 0?
    equity_credits = models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True, default=0)
    targeted_credits = models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True, default=0)
    targeted_credits_topic = models.CharField(max_length=100, choices=TARGETED_CREDITS_TOPICS, null=True, blank=True)

    is_speaker = models.BooleanField(default=False)
    is_author = models.BooleanField(default=False)
    is_carryover = models.BooleanField(default=False)
    self_reported = models.BooleanField(default=False)
    is_pro_bono = models.BooleanField(default=False)
    submitted_time = models.DateTimeField(editable=False) # needed?

    title = models.CharField(max_length=200, null=True, blank=True)
    provider_name = models.CharField(max_length=80, blank=True, null=True)
    # MAYBE... also create foreign key reference to the provider?

    begin_time = models.DateTimeField(null=True, blank=True) # THIS IS THE KEY DATE FOR DETERMINING WHERE THE CREDIT FALLS
    end_time = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, null=True, blank=True, help_text="The timezone for the location of the event")

    description = models.TextField(blank=True, null=True)
    learning_objectives = models.TextField(blank=True, null=True) # For Pro Bono Learning Objectives
    city = models.CharField(max_length=40, blank=True, null=True)
    state = models.CharField(max_length=15, blank=True, null=True)
    country = models.CharField(max_length=20, blank=True, null=True)

    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    author_type = models.CharField(max_length=50, choices=AUTHOR_TYPES, null=True, blank=True)

    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return str(self.contact.user.username) + " |  "+ self.title if self.title is not None else self.contact.user.username

    def timezone_object(self):
        if self.timezone:
            return pytz.timezone(self.timezone)
        else:
            return pytz.timezone("America/Chicago")

    def begin_time_astimezone(self):
        if self.begin_time:
            return self.begin_time.astimezone(self.timezone_object())
        else:
            return None

    def end_time_astimezone(self):
        if self.end_time:
            return self.end_time.astimezone(self.timezone_object())
        else:
            return None

    def save(self, *args, **kwargs):
        """
        Saves CM claim, including for use on CM claim form ... auto-updates time, credits, and law/ethics from the event
        if not self-reported authored. If a speaker, then does NOT update overall credits from the event (since speaker selects manually).
        """
        if not hasattr(self, "contact"):
            self.contact = self.log.contact
        if not self.submitted_time:
            # this is a first-time claim submission, so copy data from event to the claim, if event exists
            self.submitted_time = timezone.now()
        if hasattr(self, "event"):
            event = self.event
            if event:
                try:
                    contact_role = ContactRole.objects.filter(content=event, role_type = 'PROVIDER', publish_status='PUBLISHED').first()
                    company = None
                    if contact_role:
                        company = contact_role.contact.company
                    self.provider_name = self.provider_name or company
                    # self.provider_name = self.provider_name or ContactRole.objects.get(content=event, role_type = 'PROVIDER').contact.company
                except ContactRole.DoesNotExist:
                    self.provider_name = "CM_PROVIDER"

                # SHOULD WE BE UPDATING THESE EVERYTIME THE CLAIM IS SAVED?
                self.begin_time = self.begin_time or event.begin_time
                self.end_time = self.end_time or event.end_time
                self.timezone = self.timezone or event.timezone
                # note... assume description not necessary to duplicate (only used for self reporting and authoring)
                self.city = self.city or event.city
                self.state = self.state or event.state
                self.country = self.country or event.country

                law = event.cm_law_approved
                ethics = event.cm_ethics_approved
                equity = event.cm_equity_credits
                targeted = event.cm_targeted_credits

                self.law_credits = law if law is not None else 0
                self.ethics_credits = ethics if ethics is not None else 0
                # FLAGGED FOR REFACTORING: CM CONSOLIDATION
                # DO NOT ACTIVATE UNTIL JAN 1 2022? -- NO, I THINK THIS IS OK
                self.equity_credits = equity if equity is not None else 0
                self.targeted_credits = targeted if targeted is not None else 0
                self.targeted_credits_topic = event.cm_targeted_credits_topic

                # if event.parent is not None and self.event.parent.id == 3027311:
                #     pass # what to do here for national????
                # else:
                self.title = self.title or event.title

                if not self.is_speaker:
                    self.credits = event.cm_approved

        super().save(*args, **kwargs)
