import django
django.setup()
from exam.models import	ExamApplication, Exam

def update_from_draft(rsbs, subs):
	exam = Exam.objects.filter(code='2016NOV')
	if rsbs == None:
		RSB_penders = ExamApplication.objects.filter(exam=exam, application_status='P', publish_status='EARLY_RESUBMISSION')
	else:
		RSB_penders = rsbs

	if subs == None:
		SUB_penders = ExamApplication.objects.filter(exam=exam, application_status='P', publish_status='SUBMISSION')
	else:
		SUB_penders = subs

	# get the contact off a pender, then query for the nov draft on that contact
	# then update the pender from that nov draft
	for pender in RSB_penders:
		contact = pender.contact
		NOV_DRAFT = ExamApplication.objects.filter(exam=exam, publish_status='DRAFT', contact=contact).first()
		dft_app_status = NOV_DRAFT.application_status

		if dft_app_status in ['A', 'D']:
			pender.application_status = dft_app_status
			pender.save()

	print("PENDING EARLY RESUB APPS UPDATED FROM DRAFT DONE.")

	for pender in SUB_penders:
		contact = pender.contact
		NOV_DRAFT = ExamApplication.objects.filter(exam=exam, publish_status='DRAFT', contact=contact).first()
		dft_app_status = NOV_DRAFT.application_status

		if dft_app_status in ['A', 'D']:
			pender.application_status = dft_app_status
			pender.save()

	print("PENDING SUBMISSION APPS UPDATED FROM DRAFT DONE.")