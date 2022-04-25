import os

from planning.settings import ENVIRONMENT_NAME

from events.models import Event, Activity

def get_provider(event):
    provider_role = next( (cr for cr in event.contactrole.all() if cr.role_type == "PROVIDER"), None)
    return provider_role.contact if provider_role else None

def get_pending_to_publish_events():
    events = Event.objects.filter(
        publish_status="SUBMISSION", status="A", master__content_live__isnull=True
    ).exclude(
        event_type="ACTIVITY"
    ).prefetch_related(
        "contactrole__contact__user"
    ).order_by("submission_time")

    events = [e for e in events if get_provider(e)]

    return events

def print_pending_to_publish_events():
    events = get_pending_to_publish_events()
    for event in events:
        master_id = event.master_id
        try:
            provider_id = get_provider(event).user.username
        except:
            provider_id = None
        submission_time = event.submission_time.strftime('%Y-%m-%d') if event.submission_time else "----------"
        begin_time = event.begin_time.strftime('%Y-%m-%d') if event.begin_time else None
        title = event.title[:40]
        print(master_id,"|",provider_id,"|",begin_time,"|",submission_time,"|",title)


def submit_event(event):
    print("Publishing %s | %s" % (event.master_id, event.title))
    event.publish(publish_type="DRAFT")
    event.publish()
    event.solr_publish()

def publish_pending_events():

    print("querying all active submissions without published copies")
    events = get_pending_to_publish_events()

    TOTAL = len(events)
    count = 0

    for event in events:
        count += 1
        event.__class__ = event.get_proxymodel_class()

        submit_event(event)

        if event.event_type == "EVENT_MULTI":
            print("PUBLISHING ACTIVITIES")

            activities = event.get_activities()
            # activities.update(status="A")
            for activity in activities:
                submit_event(activity)

        print("Completed %.2f%%" % (float(count/TOTAL)*100.0 ) )

    print("COMPLETE!")


# *** script to publish all 2020 Event Activities with status 'X'
# *** (they were left unpublished by a bug in the cm provider event submit process)

if ENVIRONMENT_NAME == 'LOCAL':
    def curlit(master_id):
        url="http://localhost:8983/solr/planning/select?q=id:CONTENT.%s" % master_id
        response = os.system("curl %s" % url)
        print(response)
        return response
elif ENVIRONMENT_NAME == 'STAGING':
    def curlit(master_id):
        url="http://162.243.16.153:8983/solr/planning/select?q=id:CONTENT.%s" % master_id
        response = os.system("curl %s" % url)
        print(response)
        return response
elif ENVIRONMENT_NAME == 'PROD':
    def curlit(master_id):
        url="http://162.243.9.52:8983/solr/planning/select?q=id:CONTENT.%s" % master_id
        response = os.system("curl %s" % url)
        print(response)
        return response

def publish_2020_X_activities(test=True, activities=None):
    if not activities:
        activities = Activity.objects.filter(status='X', begin_time__year=2020, publish_status='DRAFT')
    total = activities.count()
    print("Num activities is ", total)
    if test:
        for draft in activities:
            print("draft is ", draft)
            print("parent is ", draft.parent)
            curlit(draft.master_id)
    else:
        for i, draft in enumerate(activities):
            print("draft is ", draft)
            print("parent is ", draft.parent)
            curlit(draft.master_id)
            published_object = draft.publish()
            print("published_object is ", published_object)
            published_object.solr_publish()
            print("%s of %s Done." % (i+1, total))
            print("\n")
pxas=publish_2020_X_activities
