from django.contrib.admin.utils import NestedObjects

from comments.models import SpeakerComment

def get_test_records():
    num = SpeakerComment.objects.count()
    return SpeakerComment.objects.all()[num-10:num]
gtr=get_test_records

def remove_speaker_comments(speaker_comments=None):
    i = 0
    if not speaker_comments:
        speaker_comments = SpeakerComment.objects.all()
    for sc in speaker_comments:
        i += 1
        collector = NestedObjects(using='default')
        collector.collect([sc])
        to_delete = collector.nested()
        if len(to_delete) == 1 and sc.comment_type == "SPEAKER_EVAL":
            print("DEL: %s %s %s" % (i,sc,sc.comment_type))
            sc.delete()
rsc=remove_speaker_comments

# TO TEST IN SHELL:
# from _data_tools.eval import *
# ts=gtr()
# rsc(ts)
