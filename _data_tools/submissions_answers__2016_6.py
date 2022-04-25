from exam.models import ExamApplication
from submissions.models import Answer


def fix_publish_status_for_submission_answers():
	Answer.objects.filter(content__publish_status="SUBMISSION", publish_status="DRAFT").update(publish_status="SUBMISSION") # needs to be done for everything
	print("Complete")


def fix_application_answers():

	print("Querying draft applications for current exam...")

	current_exam_code = "2016NOV"
	current_applications = ExamApplication.objects.filter(exam__code=current_exam_code, publish_status="DRAFT").prefetch_related("master__content__submission_answer")

	TOTAL = current_applications.count()
	count = 0 

	for draft_app in current_applications:
		count += 1

		print(draft_app.id, draft_app.contact)

		pub_uuid = draft_app.publish_uuid
		sub_app = next((da for da in draft_app.master.content.all() if da.publish_status=="SUBMISSION"), None)
	
		if sub_app:
			sub_answers = sub_app.submission_answer.all()
			for draft_answer in draft_app.submission_answer.all():
				if draft_answer.publish_status == "DRAFT" and not (draft_answer.publish_uuid in [a.publish_uuid for a in sub_answers]):
					print("", "publishing answer %s" % draft_answer.question)
					draft_answer.publish(replace=("content", sub_app), publish_type="SUBMISSION")

		print("%.2f%%" % ((count/TOTAL)*100.0))

	print("Complete!")