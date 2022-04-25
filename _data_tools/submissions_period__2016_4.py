from content.models import Content
from submissions.models import Period, Category

def create_initial_submission_periods():
	"""
	Should only be run once to create periods for existing categories
	"""

	print("Querying all submission categories...")
	submission_categories = Category.objects.all()

	for category in submission_categories:

		print("Creating and assigning initial period for %s" % category)
		# get or create period
		period, is_created = Period.objects.get_or_create(category=category)
		period.title = (category.title or "[NONE] ") + " 15-16"
		period.end_time = category.deadline_time
		period.save()

		# assign periods to content
		Content.objects.filter(submission_category=category).update(submission_period=period)


def assign_periods_to_submissions():
	"""
	Should only be run once to assign periods to existing content based on submission category
	NOTE: There should be one and only one period for each category at this time
	"""
	print("Querying all submission categories and periods...")
	submission_categories = Category.objects.prefetch_related("periods").all()

	for category in submission_categories:
		print("Assigning content to periods for category %s" % category)
		period = category.periods.first()
		Content.objects.filter(submission_period__isnull=True, submission_category=category).update(submission_period=period)

		print("Complete!")