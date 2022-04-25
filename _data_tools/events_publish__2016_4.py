import uuid
import datetime

from django.db.models import Q

from content.models import ContentTagType
from myapa.models import ContactRole
from events.models import Event, EventMulti
from store.models import Product, ProductOption, ProductPrice

def fix_broken_relisted_records():

    print("Querying for distinct Master IDs...")

    events_distinct_by_master_id = Event.objects.values("master_id", "publish_uuid").distinct("master_id")
    events_sorted_by_publish_uuid = sorted(events_distinct_by_master_id, key=lambda e: e.get("publish_uuid"))

    TOTAL = len(events_sorted_by_publish_uuid)
    GROUP_SIZE = 100
    count = 0
    fixed_master_ids = []

    print("%s total records" % TOTAL)

    last_event = {"master_id":"", "publish_uuid":""}
    for event in events_sorted_by_publish_uuid:

        count += 1

        if last_event.get("publish_uuid") == event.get("publish_uuid"):
            
            print("GOT ONE!", last_event["master_id"], last_event["publish_uuid"])
            fixed_master_ids.append((last_event["master_id"], event["master_id"]))

            # fix publish_uuid for events
            Event.objects.filter(publish_uuid=last_event["publish_uuid"], master_id=last_event["master_id"]).update(publish_uuid=uuid.uuid4())
            print("- - Fixed Event records")

            # "" content_tag_types
            ctt_count = 0
            contenttagtype_publish_uuids = ContentTagType.objects.filter(content__master_id=last_event["master_id"]).order_by("publish_uuid").distinct("publish_uuid").values_list("publish_uuid", flat=True)
            for ctt_publish_uuid in contenttagtype_publish_uuids:
                ContentTagType.objects.filter(content__master_id=last_event["master_id"], publish_uuid=ctt_publish_uuid).update(publish_uuid=uuid.uuid4())
                ctt_count += 1
            print("- - Fixed ContentTagType records", ctt_count)

            # "" contact_roles
            cr_count = 0 
            contactrole_publish_uuids = ContactRole.objects.filter(content__master_id=last_event["master_id"]).order_by("publish_uuid").distinct("publish_uuid").values_list("publish_uuid", flat=True)
            for cr_publish_uuid in contactrole_publish_uuids:
                ContactRole.objects.filter(content__master_id=last_event["master_id"], publish_uuid=cr_publish_uuid).update(publish_uuid=uuid.uuid4())
                cr_count += 1
            print("- - Fixed ContactRole records", cr_count)

            #### THESE NEXT ONES ARE PROBABLY NOT NECESSARY BUT, JUST IN CASE

            # "" product
            p_count = 0 
            product_publish_uuids = Product.objects.filter(content__master_id=last_event["master_id"]).order_by("publish_uuid").distinct("publish_uuid").values_list("publish_uuid", flat=True)
            for p_publish_uuid in product_publish_uuids:
                Product.objects.filter(content__master_id=last_event["master_id"], publish_uuid=p_publish_uuid).update(publish_uuid=uuid.uuid4())
                p_count += 1
            print("- - Fixed Product records", p_count)

            # "" product_options
            po_count = 0 
            productoption_publish_uuids = ProductOption.objects.filter(product__content__master_id=last_event["master_id"]).order_by("publish_uuid").distinct("publish_uuid").values_list("publish_uuid", flat=True)
            for po_publish_uuid in productoption_publish_uuids:
                ProductOption.objects.filter(content__master_id=last_event["master_id"], publish_uuid=po_publish_uuid).update(publish_uuid=uuid.uuid4())
                po_count += 1
            print("- - Fixed ProductOption records", po_count)

            # "" product_prices
            pp_count = 0 
            productprice_publish_uuids = ProductPrice.objects.filter(product__content__master_id=last_event["master_id"]).order_by("publish_uuid").distinct("publish_uuid").values_list("publish_uuid", flat=True)
            for pp_publish_uuid in productprice_publish_uuids:
                ProductPrice.objects.filter(content__master_id=last_event["master_id"], publish_uuid=pp_publish_uuid).update(publish_uuid=uuid.uuid4())
                pp_count += 1
            print("- - Fixed ProductPrice records", pp_count)

        last_event = event

        if count % GROUP_SIZE == 0 or count == TOTAL:
            print("%.2f%% complete" % (float(count/TOTAL)*100.0 ))

    print()
    print()

    if fixed_master_ids:
        print("FIXED RECORDS", len(fixed_master_ids) )
        for master_id_tuple in fixed_master_ids:
            print(master_id_tuple[0], master_id_tuple[1])
        print()
        print()

    print("COMPLETE!")


def submit_event(event_master):
    """
    Helper function for submitting submission records
    """
    versions = event_master.content.all().select_related("event")
    draft_version = next((c.event for c in versions if c.publish_status == "DRAFT"), None)
    submission_version = next((c.event for c in versions if c.publish_status == "SUBMISSION"), None)
    published_version = next((c.event for c in versions if c.publish_status == "PUBLISHED"), None)
    if draft_version:
        if not published_version:
            draft_version.publish()
        if not submission_version:
            draft_version.publish(publish_type="SUBMISSION")
    elif submission_version:
        if submission_version.status != "X" and submission_version.status != "H":
            submission_version.status = "A"
        submission_version.submission_time = datetime.datetime.now()
        submission_version.save()

        submission_version.publish(publish_type="DRAFT")  # first publish to draft
        submission_version.publish()                      # then to prod
        submission_version.solr_publish()                 # then to solr
    

    if versions and versions[0].event.event_type == "EVENT_MULTI":
        a_count = 0
        activities = event_master.children.distinct("master_id")
        a_total = activities.count()
        for activity in activities:
            a_count += 1
            print("", activity, "%s/%s" % (a_count, a_total) )
            submit_event(activity.master)
               



# def publish_active_cm_records( begin_time=datetime.datetime.strptime("2015-10-1", "%Y-%m-%d") ):

#     # If the submission record is active, it means that no changes we're made to this event
#     #    after the attempt to submit

#     print("Querying Active Submission Records...")
#     active_multipart_submissions = EventMulti.objects.filter(begin_time__gt=begin_time, publish_status="SUBMISSION", status="A")

#     TOTAL = active_multipart_submissions.count()
#     count = 0
#     fixed_active_events = []

#     print("%s total records" % TOTAL)

#     for submission in active_multipart_submissions:
#         count += 1
#         print(submission, "%.2f%%" % (float(count/TOTAL)*100.0 ) )
#         submit_event(submission)
#         fixed_active_events.append(submission)
#         print("publish complete")
#         print()
#         print()

#     print("Published Events")
#     for e in fixed_active_events:
#         print(e.master_id, e.title)

#     print()
#     print("COMPLETE")


def fix_published_submissions( begin_time=datetime.datetime.strptime("2015-10-1", "%Y-%m-%d") ):

    # If the submission record is active, it means that no changes we're made to this event
    #    after the attempt to submit

    # EVENTS THAT WERE THOUGHT TO BE PROBLEMATIC
    exclude_master_ids = [
        9003498, # Land Use Academy Advanced Training- (copy)
        3031378, # ACSP 55th Annual Conference
        9005134, # 39th USF Basic Economic Development Course
        9003016, # Virginia Rural Planning Caucus 2015 Conference  - Rural Resiliency
        3031177, # 15th Annual New Partners for Smart Growth Conference
        9007339, # 49th Annual Georgia Tech Basic Economic Development Course
        9006396, # Charting the Next 40 Years of Environmental Stewardship
        9007530, # FOCUS NORTH TEXAS Planning Symposium
        9007479, # TRB Annual Meeting
        9006022, # 30th Anniversary Land Use Law & Planning Conference
        9008715, # 36th Annual Statewide Preservation Conference - Resolve, Revolve, Evolve
        9008768, # 2016 Saving Places Conference
        9008829, # 2016 David J. Allor Planning & Zoning Workshop
        9008926, # 2016 Louisiana APA Conference: Planning on the Edge
        9008945, # Nebraska Annual Planning Conference
        9008683, # 36th Annual Statewide Preservation Conference - Resolve, Revolve, Evolve
        9026550, # National Bike Summit & Women's Forum
        9027365, # Transportation Winter Workshop - 2016
        9027944, # Northwest WA Planners Forum: Fall 2015
        9028469, # Texas Trails & Active Transportation Conference
        9028694, # Citizen Planner Training Collaborative Annual Conference
        9027896, # 2016 Urban Planning Conference at Savannah State University
        9028248, # Planning and Conservation League Symposium
        9027333, # 2016 National Outdoor Recreation Conference and River Management Symposium
    ]

    # AFTER FURTHER REVIEW, THESE ARE OK TO PUBLISH
    include_master_ids = [
        3031378,
        9005134,
        3031177,
        9006396,
        9007530,
        9006022,
        9008768,
        9008829,
        9008945,
        9026550,
        9027365,
        9028469,
        9028694,
        9027896,
        9027333
    ]

    # AFTER MANUAL CHANGES, RUN THESE ONES
    manual_include_master_ids = [
        9003016,
        9007479,
        9008683,
        9027944
    ]
    print("Querying Published Submission Records...")
    published_multipart_submissions = EventMulti.objects.filter(
        begin_time__gt=begin_time, publish_status="SUBMISSION"
    ).exclude( 
        ~Q(master__content__publish_status="PUBLISHED"), master__content_live__isnull=True
    ).filter(master_id__in=manual_include_master_ids)

    TOTAL = published_multipart_submissions.count()
    count = 0
    fixed_events = []

    print("%s total records" % TOTAL)

    for submission in published_multipart_submissions:
        count += 1
        print(submission, "%.2f%%" % (float(count/TOTAL)*100.0 ) )
        submit_event(submission.master)
        fixed_events.append(submission)
        print("publish complete")
        print()
        print()

    print("Published Events")
    for e in fixed_events:
        print(e.master_id, e.title)

    print()
    print("COMPLETE")



# def get_published_submission_status_n( show_counts=False, begin_time=datetime.datetime.strptime("2015-10-1", "%Y-%m-%d") ):

#     ######## GETTING published records with status 'N'
#     print("Querying Published Submissions with status 'N' ...")
#     published_submissions_with_n = EventMulti.objects.filter(begin_time__gt=begin_time, publish_status="SUBMISSION", status="N").exclude(master__content_live__isnull=True).prefetch_related("master__content")
#     TOTAL = published_submissions_with_n.count()
#     print("%s total records" % TOTAL)
#     print()

#     for e in published_submissions_with_n:
#         if show_counts:
#             print()
#             print(e.master_id, e)
#             for c in e.master.content.all():
#                 c.__class__ = EventMulti
#                 print("", c.publish_status, c.get_activities().count())
#         else:
#             print(e.master_id, e.title)

#     print()
#     print("COMPLETE!")



