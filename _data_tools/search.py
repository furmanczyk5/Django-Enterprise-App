import os
import requests

from django.contrib.admin.utils import NestedObjects

from content.models import *
import imagebank
from planning.settings import ENVIRONMENT_NAME

new_search_filter_topics = [
    "Autonomous Vehicles", "Land Uses and Activities", "Open Space and Natural Resources",
              "Real Estate Development", "Smart Cities"]

old_to_new=[
("Public Participation", "Community Engagement"),
 ("Social Justice and Equity", "Equity, Diversity, and Inclusion"),
 ("Public Service Delivery", "Public Services"),
 ("Sustainability", "Sustainability and Resilience")
]

def change_search_topics():
    tt = TagType.objects.get(code="SEARCH_TOPIC")
    # print("Search topic tag type: ")
    # print(tt.__dict__)
    #for tag_title in new_search_filter_topics:
    for toop in old_to_new:
        old_tag_title = toop[0]
        # print("tag title is: ", tag_title)
        t=Tag.objects.get(title=old_tag_title, tag_type=tt)
        print("\nTAG START")
        # print(t.__dict__)
        print("OLD: ", t.title, " ", t.code)
        new_tag_title = toop[1]
        tokens = new_tag_title.split(" ")
        # print("tokens: ", tokens)
        keywords = [t.replace(',','').strip().upper() for t in tokens if t != 'and']
        # print("keywords: ", keywords)
        new_tag_code = "TOPIC_" + "_".join(keywords)
        print("NEW: ", new_tag_title, " ", new_tag_code)
        print("TAG TYPE: ", t.tag_type)
        t.title = new_tag_title
        t.code = new_tag_code
        t.save()
        # print("tags are: ", ts)
        ctts=ContentTagType.objects.filter(tags=t, content__publish_status="DRAFT").distinct("content__id")
        print("content tag types count is: ", ctts.count())
        # ALSO SOLR DATA WILL NOT MATCH WHAT IS BEING CHANGED -- SO IT WILL BREAK
        # MUST REPUBLISH ALL CONTENT TAGGED WITH THE CHANGED TAGS publish and solr_publish -- VERY LONG -- DO AS NOHUP
        # TEST ON A SINGLE:
        # ctts = ctts[0:1]
        for ctt in ctts:
            print("content on the ContentTagType: ", ctt.content)
            # this will cause a rewrite of the search topics on a piece of content? (do we need?)
            ctt.content.taxo_topic_tags_save()
            # then publish
            published = ctt.content.publish()
            published.solr_publish()

# after this completes, delete the solr 'ghost' records
def publish_changed_search_topics():
    tt = TagType.objects.get(code="SEARCH_TOPIC")
    for toop in old_to_new:
        print("\nTAG START")
        new_tag_title = toop[1]
        t=Tag.objects.get(title=new_tag_title, tag_type=tt)
        print("TAG TYPE: ", t.tag_type)
        ctts=ContentTagType.objects.filter(tags=t, content__publish_status="DRAFT")
        total = ctts.count()
        print("content tag types count is: ", total)
        # ctt=ctts.first()
        # print("tag is ", t)
        # print('content is ', ctt.content.master)
        # what_would_be_deleted(ctt)
        # ctts=ctts[0:1]
        for i, ctt in enumerate(ctts):
            print("content on the ContentTagType: ", ctt.content)
            ctt.content.taxo_topic_tags_save()
            published = ctt.content.publish()
            published.solr_publish()
            print("%s of %s done." %(i, total))

def what_would_be_deleted(some_instance):
    collector = NestedObjects(using='default') # or specific database
    collector.collect([some_instance])
    to_delete = collector.nested()
    print("TO BE DELETED START")
    print(to_delete)
    print("TO BE DELETED END\n")


# YOU MUST SET A SORT_NUMBER WHEN CREATING NEW TAGS!
def add_search_topics():
    tt = TagType.objects.get(code="SEARCH_TOPIC")
    for tag_title in new_search_filter_topics:
        print("\nTAG START")
        tokens = tag_title.split(" ")
        # print("tokens: ", tokens)
        keywords = [t.replace(',','').strip().upper() for t in tokens if t != 'and']
        # print("keywords: ", keywords)
        tag_code = "TOPIC_" + "_".join(keywords)
        print("NEW TAG IS: ", tag_title, " ", tag_code)
        t=Tag.objects.get_or_create(code=tag_code, title=tag_title, tag_type=tt, sort_number=0)


# only use this for pasting into shell:
#from _data_tools.search import *
def test_new_search_topics():
    for toop in old_to_new:
        tt = TagType.objects.get(code="SEARCH_TOPIC")
        otit=toop[0]
        ntit=toop[1]
        print(otit,ntit)
        # ot=Tag.objects.get(title=otit, tag_type=tt)
        # print("old tag: ",ot)
        # print("title that fails to pull a tag: ", otit)
        nt=Tag.objects.get(title=ntit, tag_type=tt)
        print("")
        print("new tag: ",nt)
        # octts=ContentTagType.objects.filter(tags=ot)
        nctts=ContentTagType.objects.filter(tags=nt, publish_status="DRAFT")
        # print(ot, octts.count())
        print(nt, nctts.count())

# here's a public participation search result: 9142271
# mid='9142271'

# SUNSET IMAGE LIBRARY
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

def hide_image_library(test=True):
    if not test:
        images = imagebank.models.Image.objects.filter(publish_status="DRAFT",
            status="A")
        total = images.count()
        print("total images: ", total)
    else:
        test_images = [9000417, 9000430, 9000424, 9007714, 9000422]
        # images = imagebank.models.Image.objects.filter(publish_status="DRAFT")[0:5]
        images = imagebank.models.Image.objects.filter(master_id__in=test_images[1:3],
            publish_status="DRAFT",
            status="A")
        total = images.count()
        print("total images: ", total)
        print("visibility statuses: ", [i.status for i in images])
        master_ids = [i.master_id for i in images]
        print("master ids: ", master_ids)
        print("content types: ", [i.content_type for i in images])
        for mid in master_ids:
            curlit(mid)

    for c, i in enumerate(images):
        # there is a reason to publish -- that also publishes to solr so the images
        # won't be returned in search results
        # also remove Image tag -- delete ContentTagType ?
        if i.status == "A":
            i.status = 'H'
            i.save()
            published_instance = i.publish()
            published_instance.solr_publish()
            print("%s of %s done." % (c+1, total))

# mid="9109344"
# r=curlit(mid)

# IF AFTER RUNNING ABOVE THERE ARE STILL FACET COUNTS FOR IMAGES, PROBABLY BECAUSE
# IMAGE does not exist in postgres but still exists as a solr search record
# one-off solr staging removal:

# prod solr: 162.243.9.52:8983
# staging solr: 162.243.16.153:8983

# master_ids = ['9156786']

def remove_solr_records(master_ids):
    for mid in master_ids:
        u="http://162.243.16.153:8983/solr/planning/update?commit=true&stream.body=<delete><query>id%3ACONTENT.%s</query></delete>" % mid
        r=requests.get(u)
        print(r.content)

# confirm deleted with query:
def confirm_solr_deleted(master_ids):
    for mid in master_ids:
        u = "http://162.243.16.153:8983/solr/planning/query?q=id:CONTENT.%s" % mid
        r=requests.get(u)
        print(r.content)

# Can easily script the above for adhoc solr deletions of groups of records
