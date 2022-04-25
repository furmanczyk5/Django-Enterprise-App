import pprint

from django.db.models import Max

from submissions.models import *
from exam.models import *
from store.models import *


def create_role(username, title):
	try:
		contact = Contact.objects.get(user__username=username)
		ExamApplicationRole.objects.get_or_create(contact=contact, title=title)
		print("Created exam reviewer role for: " + str(contact) + " | as " + title)
	except Contact.DoesNotExist:
		print("No record with ID: " + username)

def create_roles():
	create_role("216879", "Staff reviewer 1")
	create_role("181410", "Staff reviewer 2")
	create_role("089655", "Staff reviewer 3")
	create_role("042872", "Staff reviewer 4")

	create_role("019595", "Peer reviewer 1")
	create_role("044039", "Peer reviewer 2")
	create_role("126477", "Peer reviewer 3")
	create_role("195630", "Peer reviewer 4")
	create_role("165711", "Peer reviewer 5")
	create_role("032756", "Peer reviewer 6")
	create_role("094392", "Peer reviewer 7")
	create_role("010522", "Peer reviewer 8")
	create_role("177749", "Peer reviewer 9")
	create_role("168305", "Peer reviewer 10")


# ***** CLEARING INCORRECT EXAM APPLICATION REVIEWER ASSIGNMENTS *****
# SO AICP STAFF CAN REASSIGN THEM (MUST BE REASSIGNED BY STAFF
# BECAUSE CUSTOM ADMIN CODE RUNS WHEN A REVIEWER IS ASSIGNED IN DJANGO)
# reviewer_usernames = [
# 317909,
# 300459,
# 326224,
# 332301,
# 264318,
# 301082,
# 330344,
# 103088,
# 376034,
# 306265,
# 374519,
# 358207,
# 337579,
# 378436,
# 351422,
# 317143,
# 348790,
# 378866,
# 338241,
# 337660,
# 350532,
# 331589,
# 317091,
# 332413,
# 310674,
# 358610,
# 332903,
# 332765,
# 275480,
# 192845,
# 333303,
# 355244,
# 230824,
# 312382,
# 359149,
# 258772,
# 339432,
# 378925,
# 324987,
# 295385,
# 306507,
# 265281,
# 345624,
# 306623,
# 378682,
# 287534,
# 373362,
# 375752,
# 324648,
# 307350
# ]
# 2020 AUG 13
# uids = [
# 306507,
# 265281,
# 345624,
# 306623,
# 378682,
# 287534,
# 373362,
# 375752,
# 324648,
# 307350,
# 262582,
# 323827,
# 304167,
# 296790,
# 356010,
# 252025,
# 349243,
# 350134,
# 318775,
# #349393, # THIS REVIEW HAS DATA IN ROUND 1 -- CAN'T BE REMOVED
# ]
# 2020 AUG 14
# uids=[
# 306507,
# 265281,
# 345624,
# 306623,
# 378682,
# 287534,
# 373362,
# 375752,
# 324648,
# 307350
# ]

def verify_reviews_have_no_data(uids):
    es = ExamApplication.objects.filter(
        contact__user__username__in=uids,
        publish_status="DRAFT",
        exam__code="2020NOV"
        ).exclude(application_type="CAND_ENR", review_assignments__comments__isnull=False
        ).order_by("contact")
    print("----- EXAM APPLICATIONS -----")
    for e in es:
        print(e.contact)
        print("Review Rounds: ",[ra.review_round for ra in e.review_assignments.all()])
    print("")
    lids=len(uids)
    count=es.count()
    print("num ids is ", lids)
    print("num apps is ", count, "\n")
    purs = Purchase.objects.filter(user__username__in=uids, product__imis_code="AICP_APPFEE")
    print("NUM PURCHASES IS ", len(purs))
    print("\n")
    pp = pprint.PrettyPrinter(indent=4)
    for e in es:
        print("REVIEW DATA: ------------")
        print("application django id: ", e.id)
        print("application: ", e)
        # pp.pprint([ra.__dict__ for ra in e.review_assignments.all()])
        pp.pprint([(ra.review_round, ra.rating_1, ra.comments) for ra in e.review_assignments.all()])
        print("ANSWER REVIEW DATA: ----------------")
        for ra in e.review_assignments.all():
            pp.pprint([(ar.rating, ar.comments, ar.answered_successfully) for ar in ra.answer_reviews.all()])
        print("")
    return es
vrhnd=verify_reviews_have_no_data

# first call:
# exam_applications = vrhnd(reviewer_usernames)

# THEN DELETE highest round REVIEW assignment:
def delete_highest_round_review_assignments(es):
    print("START..............")
    for e in es:
        print(e)
        agg_dict = e.review_assignments.all().aggregate(Max('review_round'))
        highest_review_round = agg_dict['review_round__max']
        qs = Review.objects.filter(content=e, review_round=highest_review_round)
        print(qs)
        print(qs.count())
        ra=qs.first()
        print("REVIEW DATA: ", ra.review_round, ra.rating_1, ra.comments)
        print()
        ar_ratings_and_comments = [(ar.rating, ar.comments, ar.answered_successfully) for ar in ra.answer_reviews.all()]
        print("ANSWER REVIEW DATA: ", ar_ratings_and_comments)
        if not ra.rating_1 and not ra.comments and not ar_ratings_and_comments:
            print("GOT IN TO DELETE _________________________________")
            qs.delete()
dhrra=delete_highest_round_review_assignments

# if looks ok call:
# dhrra(exam_applications)

# or DELETE ALL REVIEWS: **** USE WITH CARE ****
# def delete_review_assignments(es):
#     for e in es:
#         e.review_assignments.all().delete()
# dra=delete_review_assignments

# if looks ok call:
# dra(exam_applications)

