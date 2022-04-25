from content.models import Content

def recalculate_ratings(only_nulls=False):

	print("*****************************")
	print("* recalculating all ratings *")
	print("*****************************")

	content_w_comments = Content.objects.exclude(comments__isnull=True)
	if only_nulls:
		content_w_comments = content_w_comments.filter(rating_average__isnull=True, rating_count__isnull=True)

	total = content_w_comments.count()
	current_count = 1
	print("")
	print("* UPDATING:%s *" % total )
	print("")

	for c in content_w_comments:
		c.recalculate_rating()
		c.save()
		print("finished {0} of {1}".format(current_count, total))
		current_count += 1

	print("Flawless Victory")