from content.models import TagType, Tag, ContentTagType
from imagebank.models import Image

SUBJECT_TO_TOPIC_MAPPING = {
	"IMAGE_SUBJECT_CONSTRUCTION"				:"_DELETE_",
	"IMAGE_SUBJECT_INFRASTRUCTURE"				:"TOPIC_INFRASTRUCTURE",
	"IMAGE_SUBJECT_STREETSROADSANDHIGHWAYS"		:"TOPIC_TRANSPORTATION",
	"IMAGE_SUBJECT_TRANSPORTATION"				:"TOPIC_TRANSPORTATION",
	"IMAGE_SUBJECT_WATER"						:"TOPIC_NATURAL_RESOURCES_ENVIRONMENT",
	"IMAGE_SUBJECT_ARTSANDCULTURE"				:"_DELETE_",
	"IMAGE_SUBJECT_COMMERCIALSITES"				:"TOPIC_COMMERCIAL_LAND_USE",
	"IMAGE_SUBJECT_PARKSOPENSPACEANDGREENWAYS"	:"TOPIC_PARKS_RECREATION",
	"IMAGE_SUBJECT_EDUCATIONANDSCHOOLS"			:"TOPIC_INSTITUTIONAL_LAND_USE",
	"IMAGE_SUBJECT_ENERGY"						:"TOPIC_ENERGY",
	"IMAGE_SUBJECT_FOODANDAGRICULTURE"			:"TOPIC_FOOD_SYSTEMS",
	"IMAGE_SUBJECT_GOVERNMENT"					:"TOPIC_GOVERNMENT",
	"IMAGE_SUBJECT_HEALTHANDWELLNESS"			:"TOPIC_HEALTH",
	"IMAGE_SUBJECT_HISTORICPLACES"				:"TOPIC_HISTORIC_PRESERVATION",
	"IMAGE_SUBJECT_HOUSING"						:"TOPIC_RESIDENTIAL_LAND_USE",
	"IMAGE_SUBJECT_NATURALENVIRONMENT"			:"TOPIC_NATURAL_RESOURCES_ENVIRONMENT",
	"IMAGE_SUBJECT_PEDESTRIANS"					:"_DELETE_",
	"IMAGE_SUBJECT_PUBLICEVENTS"				:"_DELETE_",
	"IMAGE_SUBJECT_SIGNSANDBILLBOARDS"			:"TOPIC_URBAN_DESIGN",
	"IMAGE_SUBJECT_TECHNOLOGY"					:"TOPIC_PLANNING_METHODS_TOOLS",
	"IMAGE_SUBJECT_BUILTENVIRONMENT"			:"_DELETE_"	
}

DENSITY_TO_COMMUNITY_TYPE_MAPPING = {
	"IMAGE_DENSITY_SUBURBAN"	:"SUBURBAN",
	"IMAGE_DENSITY_EXURBAN"		:"EXURBAN",
	"IMAGE_DENSITY_RURAL"		:"RURAL",
	"IMAGE_DENSITY_URBAN"		:"URBAN"
}

STATE_CODES_AND_TITLES = [
	("AL","Alabama"),
	("AK","Alaska"),
	("AZ","Arizona"),
	("AR","Arkansas"),
	("CA","California"),
	("CO","Colorado"),
	("CT","Connecticut"),
	("DE","Delaware"),
	("FL","Florida"),
	("GA","Georgia"),
	("HI","Hawaii"),
	("ID","Idaho"),
	("IL","Illinois"),
	("IN","Indiana"),
	("IA","Iowa"),
	("KS","Kansas"),
	("KY","Kentucky"),
	("LA","Louisiana"),
	("ME","Maine"),
	("MD","Maryland"),
	("MA","Massachusetts"),
	("MI","Michigan"),
	("MN","Minnesota"),
	("MS","Mississippi"),
	("MO","Missouri"),
	("MT","Montana"),
	("NE","Nebraska"),
	("NV","Nevada"),
	("NH","New Hampshire"),
	("NJ","New Jersey"),
	("NM","New Mexico"),
	("NY","New York"),
	("NC","North Carolina"),
	("ND","North Dakota"),
	("OH","Ohio"),
	("OK","Oklahoma"),
	("OR","Oregon"),
	("PA","Pennsylvania"),
	("RI","Rhode Island"),
	("SC","South Carolina"),
	("SD","South Dakota"),
	("TN","Tennessee"),
	("TX","Texas"),
	("UT","Utah"),
	("VT","Vermont"),
	("VA","Virginia"),
	("WA","Washington"),
	("WV","West Virginia"),
	("WI","Wisconsin"),
	("WY","Wyoming")
]

# CALL THIS FIRST!!!!
def create_update_new_tags():
	"""
	Newly defined tags that are part of this change
	"""

	# TagType Name: Color -> Color vs. Black and White
	tagtype_color = TagType.objects.filter(code="IMAGE_COLOR")
	tagtype_color.update(title="Color vs Black and White")
	print("Updated tag type \"Color vs. Black and White\"")

	# New Color Tag: Color
	tag_color, tag_color_is_created = Tag.objects.get_or_create(code="IMAGE_COLOR_COLOR", title="Color", tag_type=tagtype_color.first())
	print("New tag \"Color\"" if tag_color_is_created else "\"Color\" tag already exists")

	# Tag Name: More than Three People -> Three or more people
	tag_three_plus = Tag.objects.filter(code="IMAGE_NUMBEROFPEOPLE_MORETHANTHREEPEOPLE").update(code="IMAGE_NUMBEROFPEOPLE_THREEORMOREPEOPLE", title="Three or More People")
	print("Updated tag  \"Three or More People\"")

	create_state_tagtype()

	print("Complete!")


def fix_contenttagtype_numofpeople(contenttagtype):
	
	print("","Number of People")

	for tag in contenttagtype.tags.all():
		if tag.code == "IMAGE_NUMBEROFPEOPLE_THREEPEOPLE":
			tag_three_plus = Tag.objects.filter(code="IMAGE_NUMBEROFPEOPLE_THREEORMOREPEOPLE").first()
			contenttagtype.tags.remove(tag)
			contenttagtype.tags.add(tag_three_plus)
			print("","","%s -> %s" % (tag.title, tag_three_plus.title))
		else:
			print("","",tag.title, "no action")

	
def fix_contenttagtype_subject(contenttagtype):

	print("","Subject")

	topic_contenttagtype = None

	for tag in contenttagtype.tags.all():

		subject_code = tag.code
		topic_code = SUBJECT_TO_TOPIC_MAPPING.get(subject_code, None)

		contenttagtype.tags.remove(tag)

		if topic_code and topic_code != "_DELETE_":
			mapped_topic_tag = Tag.objects.select_related("tag_type").get(tag_type__code="SEARCH_TOPIC", code=topic_code)
			if not topic_contenttagtype:
				topic_contenttagtype, is_created = ContentTagType.objects.get_or_create(content=contenttagtype.content, tag_type=mapped_topic_tag.tag_type)
			topic_contenttagtype.tags.add(mapped_topic_tag)
			print("","","%s <SUBJECT> -> <TOPIC> %s" % (tag.title, mapped_topic_tag.title))
		else:
			print("","",tag.title, "removed tag")


def fix_contenttagtype_color(contenttagtype):

	print("","Color")
	
	tag_codes = [t.code for t in contenttagtype.tags.all()]

	if "IMAGE_COLOR_BLACKANDWHITE" in tag_codes:
		contenttagtype.tags.clear()
		baw_tag = Tag.objects.get(code="IMAGE_COLOR_BLACKANDWHITE")
		contenttagtype.tags.add(baw_tag)
		print("","","cleared tags,", "then added %s" % baw_tag.title)
	elif tag_codes:
		col_tag = Tag.objects.get(code="IMAGE_COLOR_COLOR")
		contenttagtype.tags.clear()
		contenttagtype.tags.add(col_tag)
		print("","","cleared tags,", "then added %s" % col_tag.title)
	else:
		print("","","no action")


def fix_contenttagtype_density(contenttagtype):

	print("","Density")

	communitytype_contenttagtype = None

	for tag in contenttagtype.tags.all():

		density_code = tag.code
		communitytype_code = DENSITY_TO_COMMUNITY_TYPE_MAPPING.get(density_code, None)

		contenttagtype.tags.remove(tag)

		if communitytype_code:
			mapped_comminitytype_tag = Tag.objects.select_related("tag_type").get(tag_type__code="COMMUNITY_TYPE", code=communitytype_code)
			if not communitytype_contenttagtype:
				communitytype_contenttagtype, is_created = ContentTagType.objects.get_or_create(content=contenttagtype.content, tag_type=mapped_comminitytype_tag.tag_type)
			communitytype_contenttagtype.tags.add(mapped_comminitytype_tag)
			print("","","%s <DENSITY> -> <COMMUNITYTYPE> %s" % (tag.title, mapped_comminitytype_tag.title))
		else:
			print("","",tag.title, "removed tag")


# Nothing to do for these
# def fix_contenttagtype_imagetype(contenttagtype):
# 	# REMOVING THIS TAGTYPE, NOTHING TO DO
# 	print(,"Image Type", "no action")

# def fix_contenttagtype_orientation(contenttagtype):
# 	# NO CHANGE
# 	print(,"Image Orientation", "no action")

# def fix_contenttagtype_region(contenttagtype):
# 	# NO CHANGE
# 	print(,"Region", "no action")


# CALL THIS SECOND!!!!
def fix_image_tags():

	print("Querying all Image Library Images")

	images = Image.objects.prefetch_related("contenttagtype__tag_type", "contenttagtype__tags")

	TOTAL = images.count()
	count = 0

	print("%s TOTAL RECORDS" % TOTAL)
	print("")

	for image in images:
		print(image.id, image)
		count += 1

		for contenttagtype in image.contenttagtype.all():
			if contenttagtype.tag_type.code == "IMAGE_NUMBEROFPEOPLE":
				fix_contenttagtype_numofpeople(contenttagtype)
			elif contenttagtype.tag_type.code == "IMAGE_SUBJECT":
				fix_contenttagtype_subject(contenttagtype)
			elif contenttagtype.tag_type.code == "IMAGE_COLOR":
				fix_contenttagtype_color(contenttagtype)
			elif contenttagtype.tag_type.code == "IMAGE_DENSITY":
				fix_contenttagtype_density(contenttagtype)
			else:
				print("",contenttagtype.tag_type.title, "no action")

		print("(%.2f%%) Complete" % (float(count/TOTAL)*float(100.0)))
		print("")

	print("")
	print("")

	print("Complete!")


# CALL THIS LAST!!!!!
# DO WE JUST WANT TO DO THIS IN THE ADMIN? DELETE THE TAGTYPES, TAGS MANUALLY?
def remove_unnecessary_tags():
	"""
	deletes tag_types and tags that are no longer necessary
		use print only for details about each tag, if they are safe to delete, etc
	"""

	# delete all contenttagtypes for tagtype=imagetype
	# delete tagtype=imagetype
	tagtype_imagetype = TagType.objects.filter(code="IMAGE_IMAGETYPE").first()
	if tagtype_imagetype:
		print("Deleting all contenttagtypes for Tag Type \"%s\" ..." % tagtype_imagetype)
		imagetype_num = ContentTagType.objects.filter(tag_type=tagtype_imagetype).delete()
		print("","aaand they're gone (%s)" % imagetype_num)
		print("")

		print("Deleting Tag Type \"%s\"" % tagtype_imagetype)
		tagtype_imagetype.delete()
		print("","aaand it's gone")


	# delete contenttagtypes for tagtype=Density
	# delete tagtype=density
	tagtype_density = TagType.objects.filter(code="IMAGE_DENSITY").first()
	if tagtype_density:
		print("Deleting all contenttagtypes for Tag Type \"%s\" ..." % tagtype_density)
		density_num = ContentTagType.objects.filter(tag_type=tagtype_density).delete()
		print("","aaand they're gone (%s)" % density_num)
		print("")

		print("Deleting Tag Type \"%s\"" % tagtype_density)
		tagtype_density.delete()
		print("","aaand it's gone")

	# delete contenttagtypes for tagtype=subject
	# delete tagtype=subject
	tagtype_subject = TagType.objects.filter(code="IMAGE_SUBJECT").first()
	if tagtype_subject:
		print("Deleting all contenttagtypes for Tag Type \"%s\" ..." % tagtype_subject)
		subject_num = ContentTagType.objects.filter(tag_type=tagtype_subject).delete()
		print("","aaand they're gone (%s)" % subject_num)
		print("")

		print("Deleting Tag Type \"%s\"" % tagtype_subject)
		tagtype_subject.delete()
		print("","aaand it's gone")


	# delete tags for individual colors
	print("Deleting unnecessary \"Image Color\" tags...")
	color_num = Tag.objects.filter(tag_type__code="IMAGE_COLOR").exclude(code__in=["IMAGE_COLOR_COLOR", "IMAGE_COLOR_BLACKANDWHITE"]).delete()
	if color_num and color_num > 0:
		print("","...deleted %s tags" % color_num)
	else:
		print("","...nothing to delete")

	# delete tag for three people
	print("Deleting unnecessary \"Number of People\" tags...")
	people_num = Tag.objects.filter(tag_type__code="IMAGE_COLOR", code="IMAGE_NUMBEROFPEOPLE_THREEPEOPLE").delete()
	if people_num and people_num > 0:
		print("","...deleted %s tags" % people_num)
	else:
		print("","...nothing to delete")

	delete_image_region_tags()

# CALL THIS ONCE, ONLY BEFORE MEMBER IMAGE UPLOADS ARE ENABLED...
# ...at that point all images are is_apa=True
def make_images_apa():
	print("Marking all image library images as \"APA\"")
	Image.objects.update(is_apa=True)
	print("Complete!")

def create_state_tagtype():

	state_tagtype, is_created = TagType.objects.update_or_create(code="STATE", defaults=dict(title="State"))
	if is_created:
		print("Created State Tag Type")

	for tag_code_title in STATE_CODES_AND_TITLES:
		tag, is_created = Tag.objects.update_or_create(tag_type=state_tagtype, code="STATE_{0}".format(tag_code_title[0]), defaults=dict(title=tag_code_title[1]))
		if is_created:
			print("Created {0} Tag".format(tag.title))

	print("Complete!")

def delete_image_region_tags():
	TagType.objects.filter(code="IMAGE_REGION").delete()
	print("Image region tag type: AND IT'S GONE!")

#################################################################
# IMPORTANT FOR STAGING AND LIVE...REINDEX IMAGE LIBRARY IMAGES #
#################################################################



