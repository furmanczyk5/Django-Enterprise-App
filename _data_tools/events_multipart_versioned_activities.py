import uuid
import datetime

from events.models import EventMulti

def get_versioned_activities( show_counts=False, begin_time=datetime.datetime.strptime("2015-10-1", "%Y-%m-%d") ):

    ######## GETTING published records with status 'N'
    print("Querying Published Submissions ...")
    published_submissions = EventMulti.objects.filter(begin_time__gt=begin_time, publish_status="SUBMISSION").exclude(master__content_live__isnull=True).prefetch_related("master__content")
    TOTAL = published_submissions.count()
    print("%s total records" % TOTAL)
    print()

    for e in published_submissions:
        if show_counts:
            print()
            print(e.master_id, e)
            for c in sorted(e.master.content.all(), key=lambda x: getattr(x, "publish_status")):
                c.__class__ = EventMulti

                print("", c.publish_status.ljust(10), c.get_activities().count(), c.status, c.updated_by.username.ljust(10), c.updated_time.strftime('%B %d, %Y, %I:%M %p'), sep='\t')
        else:
            print(e.master_id, e.title)

    print()
    print("COMPLETE!")



