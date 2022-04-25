import django
django.setup()
from django.utils.text import slugify
from django.contrib.auth.models import User
from wagtail.wagtailcore.models import Page as WagtailPage, Site as WagtailSite

from content.models import Tag, TagType, JurisdictionContentTagType, CommunityTypeContentTagType
from component_sites.models import TopicTag, CommunityTypeTag, JurisdictionTag, \
	ChapterHomePage, DivisionHomePage

# Run make_wagtag_roots(), then run, make_wagtags()

def make_wagtag_roots():
	taxo_parents = Tag.objects.filter(tag_type__code="TAXO_MASTERTOPIC", parent__isnull=True)
	# taxo_children = Tag.objects.filter(tag_type__code="TAXO_MASTERTOPIC", parent__isnull=False)
	# these all are parents (they have no parents):
	commies = Tag.objects.filter(tag_type__code="COMMUNITY_TYPE")
	juries = Tag.objects.filter(tag_type__code="JURISDICTION")
	chapter_home = ChapterHomePage.objects.first()
	# need to create the wagtail page hierarchy according to the tag hierarchy
	# first make tags_root page (parent is chapter_home)
	# then all the root tags will have tags_root as parent
	# (to keep page hierarchy less cluttered)
	tt, created = TagType.objects.get_or_create(title='Wagtail Tags Root Page Tag Type', code='WAGTAG_ROOT')
	r, created = Tag.objects.get_or_create(title='Wagtail Tags Root Page', tag_type=tt)
	# parent = chapter_home
	parent = Page.objects.get(title='Root')
	new_page_get = TopicTag.objects.filter(tag=r).first()
	tags_root = new_page_get
	if not new_page_get:
		new_page = TopicTag(tag=r)
		new_page.title = r.title
		new_page.slug = slugify(new_page.title)
		page = parent.add_child(instance=new_page)
		tags_root = page
		print("tags root is ", tags_root)
	for t in taxo_parents:
		# determine parent based on django tag hierarchy
		parent = tags_root
		new_page_get = TopicTag.objects.filter(tag=t).first()
		if not new_page_get:
			new_page = TopicTag(tag=t)
			new_page.title = t.title
			new_page.slug = slugify(new_page.title)
			page = parent.add_child(instance=new_page)
			print("taxo page is ", page)
	for c in commies:
		# determine parent based on django tag hierarchy
		parent = tags_root
		new_page_get = CommunityTypeTag.objects.filter(tag=c).first()
		if not new_page_get:
			new_page = CommunityTypeTag(tag=c)
			new_page.title = c.title
			new_page.slug = slugify(new_page.title)
			page = parent.add_child(instance=new_page)
			print("commie page is ", page)
		# cp, created = CommunityTypeTag.objects.get_or_create(tag=c)
		# print("community type tag page is ", cp)
		# print("created is ", created)
		# print()
	for j in juries:
		# determine parent based on django tag hierarchy
		parent = tags_root
		new_page_get = JurisdictionTag.objects.filter(tag=j).first()
		if not new_page_get:
			new_page = JurisdictionTag(tag=j)
			new_page.title = j.title
			if new_page.title == 'Other':
				new_page.title = 'Other Jurisidiction Topics'
			new_page.slug = slugify(new_page.title)
			page = parent.add_child(instance=new_page)
			print("jury page is ", page)

		# jp, created = JurisdictionTag.objects.get_or_create(tag=j)

def make_wagtags():
	taxo_parents = Tag.objects.filter(tag_type__code="TAXO_MASTERTOPIC", parent__isnull=True)
	i=0
	for tp in taxo_parents:
		i+=1
		create_page_tree(tp)
		print("********************************************")
		print("FINISHED TAXO PARENT TREE #%s" % (i))
		print("TAXO PARENT TAG: ", tp)
		print("********************************************")
		print()

def create_page_tree(tag_tree):
	current_children = [t for t in tag_tree.tag_set.all()]
	if not current_children:
		return
	else:
		for c in current_children:
			parent = TopicTag.objects.get(tag=tag_tree)
			new_page_get = TopicTag.objects.filter(tag=c).first()
			if not new_page_get:
				new_page = TopicTag(tag=c)
				new_page.title = c.title
				new_page.slug = slugify(new_page.title)
				page = parent.add_child(instance=new_page)
				print("taxo child page is ", page)
			create_page_tree(c)



def make_wagtags_old():
	taxo_parents = Tag.objects.filter(tag_type__code="TAXO_MASTERTOPIC", parent__isnull=True)
	i=0
	for tp in taxo_parents:
		# determine parent based on django tag hierarchy
		previous_children = []
		current_children = [t for t in tp.tag_set.all()]
		while current_children:
			# create all the pages for children
			for c in current_children:
				# this parent must be a wagtail page, not a tag
				parent = TopicTag(tag=tp)
				# print("tag is ", c)
				# print("parent is ", c.parent)
				# print()
				new_page_get = TopicTag.objects.filter(tag=c).first()
				if not new_page_get:
					new_page = TopicTag(tag=c)
					new_page.title = c.title
					new_page.slug = slugify(new_page.title)
					page = parent.add_child(instance=new_page)
					print("taxo child page is ", page)
			# get new children
			previous_children = current_children
			current_children = []
			for c in previous_children:
				current_children.extend([t for t in c.tag_set.all()])
			i+=1
			print("BOTTOM OF LOOP #%s" % i)




## ATTEMPTS TO TRAVERSE SPAGHETTI STACK:


	# leaves = []
	# for t in taxo_children:
	# 	if not taxo_children.filter(parent=t):
	# 		leaves.append(t)

	# for ell in leaves:
	# 	parent = chapter_home
	# 	new_page_get = TopicTag.objects.filter(tag=ell).first()
	# 	new_page = new_page_get if new_page_get else TopicTag(tag=ell)
	# 	new_page.slug = slugify(new_page.title)
	# 	page = parent.add_child(instance=new_page)
	# 	if page:
	# 		page.publish()

	# previous_set = set(leaves)
	# current_set = set()
	# while previous_set:
	# 	for t in previous_set:
	# 		current_set.add(t.parent)
	# 	for t in current_set:
	# 		# make_page(t)
	# 		print(current_set)
	# 	previous_set = current_set
	# 	current_set = set()


	# for tp in taxo_parents:
	# 	parent = tp
	# 	current_nodes = taxo_children.filter(parent=tp)
	# 	for tc in taxo_children:
	# 		# determine parent based on django tag hierarchy
	# 		# need to traverse the tree somehow -- it's actually
	# 		# multiple trees,-- 7 roots
	# 		parent = None
	# 		new_page_get = TopicTag.objects.filter(tag=t).first()
	# 		new_page = new_page_get if new_page_get else TopicTag(tag=t)
	# 		new_page.slug = slugify(new_page.title)
	# 		page = parent.add_child(instance=new_page)
	# 		if page:
	# 			page.publish()

		# tp, created = TopicTag.objects.get_or_create(tag=t)



# need a recursive way to make pages
# traverse from leaves up to last group
# make pages on last group, unwind, make pages, unwind, etc.
# base case current_set is empty (then make pages on previous_set, and
# start unwinding)

def make_pages(current_set, previous_set):
	if not current_set:
		for t in previous_set:
			# the parent is the tag page that has a tag with a code 
			# the same as the code of the tag that is the parent of our 
			# current tag we want to make a new tag page for. 
			parent = TopicTag.objects.get(tag__code=t.parent.code)
			new_page_get = TopicTag.objects.filter(tag=t).first()
			new_page = new_page_get if new_page_get else TopicTag(tag=t)
			new_page.slug = slugify(new_page.title)
			page = parent.add_child(instance=new_page)
			if page:
				page.publish()
	else:
		current_set = set()
		for t in previous_set:
			current_set.add(t.parent)
		# for t in current_set:
		# 	# make_page(t)
		# 	print(current_set)
		# previous_set = current_set
		make_pages(current_set, previous_set)
		parent = TopicTag.objects.get(tag__code=t.parent.code)
		new_page_get = TopicTag.objects.filter(tag=t).first()
		new_page = new_page_get if new_page_get else TopicTag(tag=t)
		new_page.slug = slugify(new_page.title)
		page = parent.add_child(instance=new_page)
		if page:
			page.publish()


def spaghetti_stack_traversal():
	taxos = Tag.objects.filter(tag_type__code="TAXO_MASTERTOPIC", parent__isnull=False)
	leaves = []
	sets_list = []
	for t in taxos.filter(parent__isnull=False):
		if not taxos.filter(parent=t):
			leaves.append(t)
	previous_set = set(leaves)
	print("after setting previous_set")
	current_set = set()
	while previous_set:
		sets_list.append(previous_set)
		print("previous_set len is ", len(previous_set))
		print()
		if len(previous_set) < 10:
			print("previous set is ", previous_set)
			print()
		for t in previous_set:
			if len(previous_set) < 70:
				# for some reason there is a none object in the set of 61 tags??
				# so just test for none? 
				print("tag is ", t)
				print()
			if t:
				current_set.add(t.parent)
		print("current set len is ", len(current_set))
		print()
		previous_set = current_set
		current_set = set()
	sets_list.reverse()
	for tag_set in sets_list:
		for t in tag_set:
			if t and t.parent:
				parent = TopicTag.objects.get(tag__code=t.parent.code)
				print("parent is ", parent)
				# new_page_get = TopicTag.objects.filter(tag=t).first()
				# new_page = new_page_get if new_page_get else TopicTag(tag=t)
				# new_page.slug = slugify(new_page.title)
				# page = parent.add_child(instance=new_page)
				# if page:
				# 	page.publish()
	# return leaves


def spaghetti_stack_traversal_orig():
	taxos = Tag.objects.filter(tag_type__code="TAXO_MASTERTOPIC")
	leaves = []
	sets_list = []
	# i = 0
	for t in taxos.filter(parent__isnull=False):
		# i+=1
		# print("tag num. %s", i)
		if not taxos.filter(parent=t):
			leaves.append(t)
	# for ell in leaves:
	# 	# make_page(ell)
	# 	print(leaves)
	previous_set = set(leaves)
	current_set = set()
	while previous_set:
		sets_list.append(previous_set)
		for t in previous_set:
			current_set.add(t.parent)
		# for t in current_set:
		# 	# make_page(t)
		# 	print(current_set)
		previous_set = current_set
		current_set = set()
	for set in reverse(sets_list):
		for t in set:
			parent = TopicTag.objects.get(tag__code=t.parent.code)
			print("parent is ", parent)
			# new_page_get = TopicTag.objects.filter(tag=t).first()
			# new_page = new_page_get if new_page_get else TopicTag(tag=t)
			# new_page.slug = slugify(new_page.title)
			# page = parent.add_child(instance=new_page)
			# if page:
			# 	page.publish()
	# return leaves

	# to get children of a tag t: t.tag_set.all()

# scalar is 0.0-1.0 -- 0% to 100% lightening or darkening of the remaining scale of darkness
# for a given color -- negative scalar = darkening, positive = lightening
# this just returns a list, but the corresponding template filter returns a string
def scale_rgb(rgb_list, scalar=0.0):
    if scalar > 0:
        return [val+((255-val)*scalar) for val in rgb_list]
    else:
        return [val-(val*abs(scalar)) for val in rgb_list]

# set the wagtail notificaitons to False for all staff users

def set_wagtail_notifications_to_false(yoos=None):
	if not yoos:
		# yoos=User.objects.filter(is_staff=True).order_by("last_name")
		# this narrows it down better:
		yoos=User.objects.filter(wagtail_userprofile__isnull=False, is_staff=True).order_by("last_name")
		total = yoos.count()*1.0
	for i,y in enumerate(yoos):
		y.wagtail_userprofile.approved_notifications=False
		y.wagtail_userprofile.submitted_notifications=False
		y.wagtail_userprofile.rejected_notifications=False
		y.save()
		y.wagtail_userprofile.save()
		print("%s%% done." % ('{0:.2f}'.format((i/total)*100)))

