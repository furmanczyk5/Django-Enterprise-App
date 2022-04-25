from events.models import Event

def create_draft_events_from_submissions(limit=None):
    """ 
    Creates draft events for submission events which don't have draft events
    """

    subs = Event.objects.filter(
        publish_status="SUBMISSION"
    ).exclude(
        master__content__publish_status="DRAFT"
    ).only("master_id","publish_uuid", "updated_time").order_by("-updated_time")

    if limit:
        TOTAL = min(limit, subs.count())
        sub_subset = subs[:limit]
    else:
        TOTAL = subs.count()
        sub_subset = subs
    
    count = 0

    print("TOTAL:", TOTAL)

    for sub in sub_subset:
        count += 1
        if count % 20 == 0:
            print("%.2f%%" % (float(count/TOTAL)*100.0 ))
            
        if not Event.objects.filter(publish_status="DRAFT", publish_uuid=sub.publish_uuid).exists():
            sub.publish(publish_type="DRAFT")
            print(sub.master_id, sub.updated_time.date(), "published to draft")
        else:
            print(sub.master_id, sub.updated_time.date(), "not published")

    print("%.2f%%" % (float(count/TOTAL)*100.0 ), "Complete")