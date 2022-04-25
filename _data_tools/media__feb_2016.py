from django.db.models import Q, F
from media.models import Media

def make_all_draft_media_published():

	draft_media = Media.objects.select_related("master").filter(Q(publish_status="DRAFT") | Q(master__content_draft__id=F("id")))

	TOTAL = draft_media.count()
	count = 0

	for media in draft_media:
		count+=1
		master = media.master
		master.content_live = media
		master.content_draft = None
		master.save()
		print("Completed %s of %s (%.2f%%)" % (count, TOTAL, float(count/TOTAL)*100.0 ) )

	draft_media.update(publish_status="PUBLISHED")

	print("Flawless Victory!")