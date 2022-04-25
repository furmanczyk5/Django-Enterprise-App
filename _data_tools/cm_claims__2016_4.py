from django.db.models import Q 

from cm.models import Claim
from events.models import Event

def fix_ethics_credit_claims():

    print("Querying all claims that need ethics credits added...")

    claims = Claim.objects.filter(
        Q(ethics_credits__isnull=True) | Q(ethics_credits=0), event__cm_ethics_approved__gt=0
    ).select_related("event")

    TOTAL = claims.count()
    GROUP_SIZE = 10
    count = 0

    print("{TOTAL} total records to update".format(TOTAL=TOTAL))

    for c in claims:
        count += 1
        ethics_credits = c.event.cm_ethics_approved
        c.ethics_credits = ethics_credits
        c.save()

        if count % GROUP_SIZE == 0 or TOTAL == count:
            print("%.2f%% complete" % (float(count/TOTAL)*100.0 ))

    print("COMPLETE!")

def fix_law_credit_claims():

    print("Querying all claims that need law credits added...")

    claims = Claim.objects.filter(
        Q(law_credits__isnull=True) | Q(law_credits=0), event__cm_law_approved__gt=0
    ).select_related("event")

    TOTAL = claims.count()
    GROUP_SIZE = 10
    count = 0

    print("{TOTAL} total records to update".format(TOTAL=TOTAL))

    for c in claims:
        count += 1
        law_credits = c.event.cm_law_approved
        c.law_credits = law_credits
        c.save()

        if count % GROUP_SIZE == 0 or TOTAL == count:
            print("%.2f%% complete" % (float(count/TOTAL)*100.0 ))

    print("COMPLETE!")

# JUNE 2021
# SCRIPT TO UPDATE ALL NULL CM CLAIM CREDIT FIELDS TO ZERO
# FIRST MUST CREATE A SCRIPT TO WRITE ZERO TO ALL EVENT RECORD FIELDS (BCUZ CLAIMS PULL THOSE VALUES ON SAVE)

# this will take many hours (run as a nohup using cm_event_script.py)
def event_credits_null_to_zero(all_events=None, is_test=True):
    if not all_events and not is_test:
        all_events = Event.objects.all().order_by('id')
    total = all_events.count()
    print("total is ", total)
    number_of_objects = 1000

    for i in range(0,total,number_of_objects):
        events_slice = Event.objects.all().order_by('id')[i:i+number_of_objects]

        for j, e in enumerate(events_slice):
            if e.cm_approved == None:
                e.cm_approved = 0
            if e.cm_law_approved == None:
                e.cm_law_approved = 0
            if e.cm_ethics_approved == None:
                e.cm_ethics_approved = 0
            if e.cm_equity_credits == None:
                e.cm_equity_credits = 0
            if e.cm_targeted_credits == None:
                e.cm_targeted_credits = 0
            e.save()
            print("%s of %s DONE -----" % (i+j, total))

# AFTER EVENT SCRIPT IS DONE RUN THIS (as a nohup using cm_claim_script.py):
def claim_credits_null_to_zero(all_claims=None, is_test=True):
    if not all_claims and not is_test:
        all_claims = Claim.objects.all()
    total = all_claims.count()
    number_of_objects = 1000

    for i in range(0,total,number_of_objects):
        claims_slice = Claim.objects.all()[i:i+number_of_objects]

        for j, c in enumerate(claims_slice):
            if c.credits == None:
                c.credits = 0
            if c.law_credits == None:
                c.law_credits = 0
            if c.ethics_credits == None:
                c.ethics_credits = 0
            if c.equity_credits == None:
                c.equity_credits = 0
            if c.targeted_credits == None:
                c.targeted_credits = 0
            c.save()
            print("%s of %s DONE -----" % (i+j, total))

# Script ran to completion, but there are still 113724 claims with nulls on equity and targeted
# also still have 354 credits with nulls, 96859 law_credits with nulls and 101476 ethics_credits with nulls ???
def claim_cleanup_nulls(all_claims=None, is_test=True):
    if not all_claims and not is_test:
        all_claims = Claim.objects.filter(
            Q(credits__isnull=True) | Q(law_credits__isnull=True) | Q(ethics_credits__isnull=True) | Q(equity_credits__isnull=True) | Q(targeted_credits__isnull=True)
            ).values('id')
    total = all_claims.count()
    print("THERE ARE %s CLAIMS WITH AT LEAST ONE NULL CREDITS-TYPE FIELD" % total)
    number_of_objects = 1000

    for i in range(0,total,number_of_objects):
        claims_slice = Claim.objects.filter(id__in=all_claims).order_by('id')[i:i+number_of_objects]

        for j, c in enumerate(claims_slice):
            if c.credits == None:
                c.credits = 0
            if c.law_credits == None:
                c.law_credits = 0
            if c.ethics_credits == None:
                c.ethics_credits = 0
            if c.equity_credits == None:
                c.equity_credits = 0
            if c.targeted_credits == None:
                c.targeted_credits = 0
            c.save()
            print("%s of %s DONE -----" % (i+j, total))
