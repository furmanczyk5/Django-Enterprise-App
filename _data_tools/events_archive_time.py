import time, pytz, datetime

import django
django.setup()
from django.utils import timezone

from events.models import Event

def archive_oldies(oldies):
    now=timezone.now()
    three_years = datetime.timedelta(days=3*365)
    if not oldies:
        oldies = Event.objects.filter(end_time__lte=now-three_years, archive_time__isnull=True)
    for event in oldies:
        if event.begin_time or event.end_time:
            event.archive_time = now
            event.save()

def archive_newbies(newbies):
    now=timezone.now()
    three_years = datetime.timedelta(days=3*365)
    if not newbies:
        newbies = Event.objects.filter(end_time__gte=now-three_years, archive_time__isnull=True)
    for event in newbies:
        if event.end_time:
            event.archive_time = event.end_time + three_years
            event.save()
        elif event.begin_time:
            event.archive_time = event.begin_time + three_years
            event.save()
        else:
            print("no begin or end time for: ", event)

def ao(oldies):
    archive_oldies(oldies)
    print("OLDIES DONE!")

def an(newbies):
    archive_newbies(newbies)
    print("NEWBIES DONE!")
