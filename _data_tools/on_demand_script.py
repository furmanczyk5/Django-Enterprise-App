import django
django.setup()

# from _data_tools.on_demand import *
from learn.utils.wcw_api_utils import *

# mod()
# mlfod()
me = Contact.objects.get(user__username=322218)
lcs=LearnCourse.objects.filter(code__contains="LRN_19",status__in=["A","H"], publish_status="DRAFT")
wcw_contact_sync = WCWContactSync(me)
r = wcw_contact_sync.push_courses_to_wcw(lcs)
