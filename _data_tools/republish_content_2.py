
def republish_content(queryset):
	"""
	function to publish all records in the queryset, one by one,
	IMPORTANT NOTE: make sure the queryset comes from the correct ModelClass
	"""

	queryset = queryset.filter(publish_status="DRAFT") # make sure that all of these are draft records
	total = queryset.count()

	for i, content in enumerate(queryset): 
		content.publish()
		print("published %s, %s of %s" % (content.master_id, i+1, total) )

	print("Flawless Victory")


# <ADD COVID 19 SEARCH TOPIC FILTER>

# ********************************************
# This is how you script adding a search topic
# ********************************************
def add_covid_search_topic():
    ids_set = set()
    taxo_t = covts.get(code="POLICYSERVICESHEALTHHUMANCOVID")
    cs=Content.objects.filter(taxo_topics=taxo_t, publish_status="DRAFT")
    taxo_ids=[c.id for c in cs]
    for idoo in taxo_ids:
            ids_set.add(idoo)
    print("len taxo ids set: ", len(ids_set))
    for t in covts:
            print(t.code)
            ctts=ContentTagType.objects.filter(tags=t, content__publish_status="DRAFT")
            print(ctts.count())
            ids = [ctt.content.id for ctt in ctts]
            for idee in ids:
                    ids_set.add(idee)
    print(ids_set)
    print("length of full content ids set: ", len(ids_set))
    cs = Content.objects.filter(id__in=ids_set)
    print("statuses of content: ", [c.status for c in cs])
    # ONLY PUBLISH THE ONES THAT HAVE BEEN PUBLISHED AND PUBLISHED RECORD IS ACTIVE
    for idee in ids_set:
            c = Content.objects.get(id=idee)
            if c.is_published() and c.status == 'A':
                    print("content: ", c)
                    c.taxo_topic_tags_save()
                    published = c.publish()
                    published.solr_publish()
