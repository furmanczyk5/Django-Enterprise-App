import django
django.setup()
from django.db.models.deletion import Collector
import random

from content.models import *

def setup_tags():
	title_list = ["Financial Tools: Other Tools", "Gated & Planned Communities Development",
	"Other Development", "Other Guidelines", "Other Land Uses, Activities, and Structures",
	"Other Manifestations of Policy", "Other Policy", "Other Policy Framework", 
	"Other Programs", "Other State and Regional Bodies", "Other Tax Incentives",
	"Other Tribal Bodies", "Policy Framework: Other", "Rate of Growth Regulations",
	"State Laws – Other", "Subdividing Lots Policy", "Town & Civic Center Development",
	"Warehouse Store Development",
	]
	tags=[]
	for title in title_list:
		try:
			tags.append(Tag.objects.get(title=title))
		except:
			print(title)
	return tags

# In shell:
def delete_tags(tags):
	for tag in tags:
		tag.delete()


# DELETE INACTIVE TAGS -- CHECK THAT ONLY one TAG AND one or more CONTENT TAG TYPE RECORDS
# WILL BE DELETED...
# dits = delete inactive tags

# it looks like setting the status of Tags you don't want to delete to 'A'
# and then running the script will delete only the tags we want to delete
# Cory will spin up a snapshot of prod postgres locally so we can run a before/after
# final check of the script
def dits():
	ts = Tag.objects.filter(status="I").exclude(title__contains="OLD", id=534)
	apa_old = Tag.objects.filter(title__contains="OLD").first()
	other_topics = Tag.objects.filter(title="Other Topics").first()
	# ts = [Tag.objects.filter(status="I").last()]
	# print("ts is ", ts)

	# collector = Collector(using='default') # or specific database
	# ts_list = list(ts)
	# collector.collect(ts_list)
	# collector.collect([ts.first()])
	for t in ts:
		# print("\n**************************************************************************************")
		# print("Looking at Tag: ", t)
		# print("**************************************************************************************\n")
		collector = Collector(using='default') # or specific database
		collector.collect([t])

		inactive_tags = 0
		non_inactive_tags = 0
		other_models = 0
		tags = set()
		tags_that_will_delete_other_models = set()
		other_models_to_be_deleted = set()
		nits = list()
		its = list()

		for model, instance in collector.instances_with_model():
			# print(type(model))
			# print(instance)
			# print()
			# print("-------- MODEL NAME IS ", model.__name__)
			if model.__name__ == 'Tag':
				tags.add(instance)
			if model.__name__ == 'Tag' and instance.status != "I":
				# grab tag instance here -- if other delete model check is true add to set
				non_inactive_tags+=1
				nits.append(instance)
				print("##### Non-inactive Tag instances that will be deleted: %s" % instance)
				print("Status of non-inactive tag that will be deleted: ", instance.status)
			elif model.__name__ == 'Tag' and instance.status == "I":
				inactive_tags+=1
				its.append(instance)
				# print("##### Inactive Tag instance that will be deleted: %s" % instance)
			if non_inactive_tags > 1:
				pass
				# return
			# if model.__name__ == 'ContentTagType_tags':
			# 	print("***** model is a tag type *****")
			if model.__name__ != 'ContentTagType_tags' and model.__name__ != 'Tag' \
				and model.__name__ != 'Content_taxo_topics':
				other_models += 1
				# no this puts all -- just want tag
				tags_that_will_delete_other_models = tags
				other_models_to_be_deleted.add(type(instance))
				# print("*** model is not a Tag or ContentTagType_tags")
				# print("*** model is: ", model.__name__)
				# print("model name length is ", len(model.__name__))
				# return
		# print("tag is ", t)
		if non_inactive_tags > 0:
			print("Looking at Tag: ", t)
			print("%s Non-inactive Tag records will be deleted" % non_inactive_tags)
			if apa_old in nits:
				print("Apa old will be deleted")
		# DON'T SHOW THE ONE-OFFS
		if inactive_tags > 1:
			print("tag is ", t)
			print("%s Inactive Tag records will be deleted" % inactive_tags)
			if apa_old in its:
				print("Apa old will be deleted")
			# for i in its:
			# 	print(i)
			print()
		if other_models > 0:
			print("other models that would be deleted number %s" % other_models)
		# print("The set of tags that will delete other models is ", tags_that_will_delete_other_models)
		if other_models_to_be_deleted:
			print("other models to be deleted are: ", other_models_to_be_deleted)
		# print("**************************************************************************************\n")
		# after commenting back in return statements then bring this print back in
		# print("Nothing to exclude this tag from being deleted.\n")
		# if non_inactive_tags == 0:
		# 	t.delete()

# ********************************************
# NOW SWITCH OUT OLD APA TAXO TAG WITH NEW ONE
# ********************************************

# soawina = switch old apa taxo with new apa taxo
def soawina(test=True):
	i = j = 0
	old = Tag.objects.get(title="American Planning Association OLD", id=1549)
	new = Tag.objects.get(title="American Planning Association", id=1744)

	if test:
		total = ContentTagType.objects.filter(tags=old, publish_status='DRAFT').count()
		if total > 0:
			index = random.randint(0, total-1)
			ctts = [ContentTagType.objects.filter(tags=old, publish_status='DRAFT').all()[index]]
		else:
			ctts = None
		# ctts = [ContentTagType.objects.filter(tags=old, publish_status='DRAFT').last()]
		cs=Content.objects.filter(taxo_topics=old, publish_status='DRAFT')
		total = cs.count()
		if total > 0:
			index = random.randint(0, total-1)
			cs = [cs[index]]
		else:
			cs = None

	else:
		ctts = ContentTagType.objects.filter(tags=old, publish_status='DRAFT')
		cs=Content.objects.filter(taxo_topics=old, publish_status='DRAFT')

	if ctts:
		for ctt in ctts:
			i+=1
			print("\n****************** START ********************")
			print("####### CONTENT TAG TYPE")
			print("ContentTagType id is ", ctt.id)
			print("original tags: ", ctt.tags.all())
			ctt.tags.add(new)
			ctt.tags.remove(old)
			print("new tags: ", ctt.tags.all())
			ctt.save()
			if ctt.content:
				published_record = ctt.content.publish()
				solr_response = published_record.solr_publish()
				print("published record is ", published_record)
				print("id is ", published_record.id)
				print("solr response is ", solr_response)
			else:
				print("Content Tag Type HAS NO CONTENT")
			print("FINISHED %s Content Tag Type Records.\n" % i)

	old = TaxoTopicTag.objects.get(title="American Planning Association OLD", id=1549)
	new = TaxoTopicTag.objects.get(title="American Planning Association", id=1744)

	if cs:
		for c in cs:
			j+=1
			print("####### CONTENT")		
			print("Content id is ", c.id)
			print("original tags: ", c.taxo_topics.all())
			c.taxo_topics.add(new)
			c.taxo_topics.remove(old)
			print("new tags: ", c.taxo_topics.all())
			c.save()
			try:
				published_record = c.publish()
				if published_record:
					solr_response = published_record.solr_publish()
			except:
				published_record = None
				solr_response = None
			print("published record is ", published_record)
			print("id is ", published_record.id)
			print("solr response is ", solr_response)
			print("FINISHED %s Content Records.\n" % j)
			print("****************** END ********************\n")

