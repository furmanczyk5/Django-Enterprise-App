from django.conf import settings

from content.models import Content
from events.models import Event
from learn.models import LearnCourse


def iterate_OnDemand_APALearn(on_demand_course=None):
    if not on_demand_course: 
        on_demand_course = Content.objects.filter(content_type= "EVENT",\
            event__event_type= "COURSE", code__isnull=False).\
            exclude(code='None').exclude(code='').order_by('code')
    # print (on_demand_course.count())
    counter=0
    total = on_demand_course.count()
    for i, x in enumerate(on_demand_course):
        try:
            learn_course_code = get_learn_course_code(x)
            if x.code and learn_course_code:
                if x.event.digital_product_url == 'https://learn.planning.org/catalog/' or x.event.digital_product_url is None  :
                    set_DPUrl(x, learn_course_code)
                    counter+=1
            print('{0:.2f}%'.format(i/total*100))
        except:
            pass
    print ("There are "+counter+ " updated URLs.")

def get_learn_course_code(content):
    """What is APA learn course corresponds to the OnDemandCourse?"""
    LRN = LearnCourse.objects.filter(code='LRN_{}'.format(content.code), publish_status = "PUBLISHED")
    if LRN and LRN.first().code:
        return LRN.first().code
    npc18code = ''

    if content.code is not None:
        npc18code = content.code.split("NPC")
    if len(npc18code) > 1:
        print("this is a thing")
        LRN = LearnCourse.objects.filter(code="LRN_{}".format(npc18code[1]), publish_status="PUBLISHED")
        if LRN:
            return LRN.first().code 
    LRN = LearnCourse.objects.filter(title__icontains=content.title)
    if LRN and LRN.first().code:
        return LRN.first().code
    return False

def set_DPUrl(content, code):
    DPUrl ="https://"+settings.LEARN_DOMAIN+"/local/catalog/view/product.php?globalid="+code
    old_url=content.event.digital_product_url
    setattr(content.event, "digital_product_url", DPUrl)
    content.event.save()
    print ("{} url was updated from {} to {}".format(content.event.code, old_url, DPUrl))
    

if __name__ == '__main__':
    qs = Content.objects.filter(master_id=9152541)
    # iterate_OnDemand_APALearn(qs)
    iterate_OnDemand_APALearn()
