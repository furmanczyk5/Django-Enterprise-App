from content.models import TagType, Tag, ContentTagType
from events.models import Event, Course
from pages.models import Page
from publications.models import Article, Book, EBook
from imagebank.models import Image
from media.models import Audio, Video

def create_format_tag_type():

	format_tagtype, is_created = TagType.objects.get_or_create(title="Format", code="FORMAT")

	Tag.objects.get_or_create(title="Web Page", code="FORMAT_WEBPAGE", tag_type=format_tagtype),
	Tag.objects.get_or_create(title="Article", code="FORMAT_ARTICLE", tag_type=format_tagtype),
	Tag.objects.get_or_create(title="Book", code="FORMAT_BOOK", tag_type=format_tagtype),
	Tag.objects.get_or_create(title="E-book", code="FORMAT_EBOOK", tag_type=format_tagtype),
	Tag.objects.get_or_create(title="Blog Post", code="FORMAT_BLOGPOST", tag_type=format_tagtype),
	Tag.objects.get_or_create(title="Report", code="FORMAT_REPORT", tag_type=format_tagtype),
	Tag.objects.get_or_create(title="Toolkit", code="FORMAT_TOOLKIT", tag_type=format_tagtype),
	Tag.objects.get_or_create(title="Live In-Person Event", code="FORMAT_LIVE_IN_PERSON_EVENT", tag_type=format_tagtype),
	Tag.objects.get_or_create(title="Live Online Event", code="FORMAT_LIVE_ONLINE_EVENT", tag_type=format_tagtype),
	Tag.objects.get_or_create(title="On-Demand Education", code="FORMAT_ON_DEMAND_EDUCATION", tag_type=format_tagtype),
	Tag.objects.get_or_create(title="Audio", code="FORMAT_AUDIO", tag_type=format_tagtype),
	Tag.objects.get_or_create(title="Video", code="FORMAT_VIDEO", tag_type=format_tagtype),
	Tag.objects.get_or_create(title="Image", code="FORMAT_IMAGE", tag_type=format_tagtype),

	queried_tag_type = TagType.objects.prefetch_related("tags").get(code="FORMAT")
	print(queried_tag_type)
	for tag in queried_tag_type.tags.all():
		print("    %s" % tag)


def update_content(content_query, tag_code):
	"""
	HELPER FUNCTION
	"""

	format_tagtype = TagType.objects.prefetch_related("tags").get(code="FORMAT")
	webpage_tag = next(t for t in format_tagtype.tags.all() if t.code == tag_code)

	TOTAL = content_query.count()
	count = 0

	print("%s total records to update" % TOTAL)

	for content in content_query:
		count+=1
		contenttagtype, is_created = ContentTagType.objects.get_or_create(tag_type=format_tagtype, content=content)
		contenttagtype.tags.add(webpage_tag)

		try:
			if content.publish_status == "PUBLISHED":
				content.solr_publish()
				print("Updated and Reindexed %s, %.2f%% complete" % (content, float(count/TOTAL)*100.0 ))
			else:
				print("Updated %s, %.2f%% complete" % (content, float(count/TOTAL)*100.0 ))
		except:
			print("************ Failed: %s" % content)

def update_pages():
	"""
	add correct format tags to pages and re-publish to solr if necessary
	"""
	print("querying for all pages that need correcting...")
	pages = Page.objects.exclude(contenttagtype__tags__code="FORMAT_WEBPAGE") # exclude() will allow us to stop script and pick up where we left off
	update_content(pages, "FORMAT_WEBPAGE")
	print("Pages are Done!")

def update_articles():
	"""
	add correct format tags to articles and re-publish to solr if necessary
	"""
	print("querying for all articles that need correcting...")
	articles = Article.objects.exclude(contenttagtype__tags__code="FORMAT_ARTICLE") # exclude() will allow us to stop script and pick up where we left off
	update_content(articles, "FORMAT_ARTICLE")
	print("Articles are Done!")

def update_books():
	"""
	add correct format tags to books and re-publish to solr if necessary
	"""
	print("querying for all books that need correcting...")
	books = Book.objects.exclude(contenttagtype__tags__code="FORMAT_BOOK") # exclude() will allow us to stop script and pick up where we left off
	update_content(books, "FORMAT_BOOK")
	print("Books are Done!")

def update_ebooks():
	"""
	add correct format tags to ebooks and re-publish to solr if necessary
	"""
	print("querying for all e-books that need correcting...")
	ebooks = EBook.objects.exclude(contenttagtype__tags__code="FORMAT_EBOOK") # exclude() will allow us to stop script and pick up where we left off
	update_content(ebooks, "FORMAT_EBOOK")
	print("E-Books are Done!")

def update_liveinperson():
	"""
	add correct format tags to events (live in person) and re-publish to solr if necessary
	"""
	print("querying for all live in person events that need correcting...")
	events = Event.objects.exclude(is_online=True).exclude(event_type="COURSE").exclude(contenttagtype__tags__code="FORMAT_LIVE_IN_PERSON_EVENT") # exclude() will allow us to stop script and pick up where we left off
	update_content(events, "FORMAT_LIVE_IN_PERSON_EVENT")
	print("Events (live in person) are Done!")

def update_liveonline():
	"""
	add correct format tags to events (live in person) and re-publish to solr if necessary
	"""
	print("querying for all live online events that need correcting...")
	events = Event.objects.filter(is_online=True).exclude(contenttagtype__tags__code="FORMAT_LIVE_ONLINE_EVENT") # exclude() will allow us to stop script and pick up where we left off
	update_content(events, "FORMAT_LIVE_ONLINE_EVENT")
	print("Events (live online) are Done!")

def update_ondemand():
	"""
	add correct format tags to events (live in person) and re-publish to solr if necessary
	"""
	print("querying for all on demand courses that need correcting...")
	events = Course.objects.exclude(contenttagtype__tags__code="FORMAT_ON_DEMAND_EDUCATION") # exclude() will allow us to stop script and pick up where we left off
	update_content(events, "FORMAT_ON_DEMAND_EDUCATION")
	print("On Demand Courses are Done!")

def update_imagelibrary():
	"""
	add correct format tags to events (live in person) and re-publish to solr if necessary
	"""
	print("querying for all image library images that need correcting...")
	images = Image.objects.exclude(contenttagtype__tags__code="FORMAT_IMAGE") # exclude() will allow us to stop script and pick up where we left off
	update_content(images, "FORMAT_IMAGE")
	print("Images are Done!")

def update_videos():
	"""
	add correct format tags to events (live in person) and re-publish to solr if necessary
	"""
	print("querying for all videos that need correcting...")
	videos = Video.objects.exclude(contenttagtype__tags__code="FORMAT_VIDEO") # exclude() will allow us to stop script and pick up where we left off
	update_content(videos, "FORMAT_VIDEO")
	print("Videos are Done!")

def update_audios():
	"""
	add correct format tags to events (live in person) and re-publish to solr if necessary
	"""
	print("querying for all audios that need correcting...")
	audios = Audio.objects.exclude(contenttagtype__tags__code="FORMAT_AUDIO") # exclude() will allow us to stop script and pick up where we left off
	update_content(audios, "FORMAT_AUDIO")
	print("Audio are Done!")


##############################
#### CENSUS REGIONS STUFF ####
##############################
def create_census_region_tag_type():
	region_tagtype, is_created = TagType.objects.get_or_create(title="Region", code="CENSUS_REGION")

	Tag.objects.get_or_create(title="Mountain", code="MOUNTAIN", tag_type=region_tagtype),
	Tag.objects.get_or_create(title="Middle Atlantic", code="MIDDLE_ATLANTIC", tag_type=region_tagtype),
	Tag.objects.get_or_create(title="International", code="INTERNATIONAL", tag_type=region_tagtype),
	Tag.objects.get_or_create(title="New England", code="NEW_ENGLAND", tag_type=region_tagtype),
	Tag.objects.get_or_create(title="East South Central", code="EAST_SOUTH_CENTRAL", tag_type=region_tagtype),
	Tag.objects.get_or_create(title="West South Central", code="WEST_SOUTH_CENTRAL", tag_type=region_tagtype),
	Tag.objects.get_or_create(title="South Atlantic", code="SOUTH_ATLANTIC", tag_type=region_tagtype),
	Tag.objects.get_or_create(title="East North Central", code="EAST_NORTH_CENTRAL", tag_type=region_tagtype),
	Tag.objects.get_or_create(title="West North Central", code="WEST_NORTH_CENTRAL", tag_type=region_tagtype),
	Tag.objects.get_or_create(title="Pacific", code="PACIFIC", tag_type=region_tagtype),

	queried_tag_type = TagType.objects.prefetch_related("tags").get(code="CENSUS_REGION")
	print(queried_tag_type)
	for tag in queried_tag_type.tags.all():
		print("    %s" % tag)
