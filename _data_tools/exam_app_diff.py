import uuid
import django
django.setup()
from django.contrib.auth.models import User, Group
from myapa.models.contact import Contact
# from exam.models import	ExamApplication, Exam, DENIED_STATUSES_LIST
from exam.models import *
from submissions.models import Answer, AnswerReview

def compare_apps():

	current_exam = Exam.objects.filter(code='2016NOV').first()
	drafts = ExamApplication.objects.filter(publish_status="DRAFT", exam=current_exam)
	job_diff_count	= 0
	degree_diff_count = 0
	submission_none_count = 0

	for d in drafts:
		s = d.master.content.filter(publish_status="SUBMISSION").first()
		if s == None:
			print("No submission record.", d, s)
			submission_none_count += 1
		elif s is not None:
			if d.applicationjobhistory_set.count() != s.examapplication.applicationjobhistory_set.count():
				print("jobs don't match: ", d, s)
				job_diff_count += 1
			if d.applicationdegree_set.count() != s.examapplication.applicationdegree_set.count():
				print("degrees don't match: ", d, s )
				degree_diff_count += 1
	print("Number of draft records without submission records: ", submission_none_count)
	print("Number of applications where jobs differed: ", job_diff_count)
	print("Number of applications where degrees differed: ", degree_diff_count)


def find_empty_submission():

	current_exam = Exam.objects.filter(code='2016NOV').first()
	drafts = ExamApplication.objects.filter(publish_status="DRAFT", exam=current_exam)
	no_job_count	= 0
	no_degree_count = 0
	submission_none_count = 0

	for d in drafts:
		s = d.master.content.filter(publish_status="SUBMISSION").first()
		if s == None:
			print("No submission record.", d, s)
			submission_none_count += 1
		elif s is not None:
			if d.applicationjobhistory_set.count() > 0 and s.examapplication.applicationjobhistory_set.count() == 0:
				print("Draft has jobs, submission no jobs: ", d, s)
				no_job_count += 1
			if d.applicationdegree_set.count() > 0 and s.examapplication.applicationdegree_set.count() == 0:
				print("Draft has degrees, submission no degrees: ", d, s )
				no_degree_count += 1
	print("Number of draft records without submission records: ", submission_none_count)
	print("Number of drafts with jobs whose associated submission has no jobs: ", no_job_count)
	print("Number of drafts with degrees whose associated submission has no degrees: ", no_degree_count)


def find_empty_draft():

	current_exam = Exam.objects.filter(code='2016NOV').first()
	drafts = ExamApplication.objects.filter(publish_status="DRAFT", exam=current_exam)
	no_job_count	= 0
	no_degree_count = 0
	submission_none_count = 0

	for d in drafts:
		s = d.master.content.filter(publish_status="SUBMISSION").first()
		if s == None:
			print("No submission record.", d, s)
			submission_none_count += 1
		elif s is not None:
			if d.applicationjobhistory_set.count() == 0 and s.examapplication.applicationjobhistory_set.count() > 0:
				print("Submission has jobs, draft no jobs: ", d, s)
				no_job_count += 1
			if d.applicationdegree_set.count() == 0 and s.examapplication.applicationdegree_set.count() > 0:
				print("Submission has degrees, draft no degrees: ", d, s )
				no_degree_count += 1
	print("Number of draft records without submission records: ", submission_none_count)
	print("Number of drafts with no jobs whose associated submission has jobs: ", no_job_count)
	print("Number of drafts with no degrees whose associated submission has degrees: ", no_degree_count)


def restore_submission_old():
	current_exam = Exam.objects.filter(code='2016NOV').first()
	drafts = ExamApplication.objects.filter(publish_status="DRAFT", exam=current_exam)
	no_job_count	= 0
	no_degree_count = 0
	submission_none_count = 0

	for d in drafts:
		s = d.master.content.filter(publish_status="SUBMISSION").first()
		if s == None:
			print("No submission record.", d, s)
			submission_none_count += 1
		elif s is not None:
			d_job_count = d.applicationjobhistory_set.count()
			s_job_count = s.examapplication.applicationjobhistory_set.count()
			d_degree_count = d.applicationdegree_set.count()
			s_degree_count = s.examapplication.applicationdegree_set.count()
			if d_job_count > 0 and s_job_count == 0:
				print("Draft has jobs, submission no jobs: ", d, s)
				no_job_count += 1
				s.examapplication.applicationjobhistory_set = d.applicationjobhistory_set.all()
				# s.examapplication.save()
				print("Now draft job count is %s and submission job count is %s." % (d_job_count, s_job_count))
			if d_degree_count > 0 and s_degree_count == 0:
				print("Draft has degrees, submission no degrees: ", d, s )
				no_degree_count += 1
				s.examapplication.applicationdegree_set = d.applicationdegree_set.all()
				# s.examapplication.save()
				print("Now draft degree count is %s and submission degree count is %s." % (d_degree_count, s_degree_count))

	print("Number of draft records without submission records: ", submission_none_count)
	print("Number of drafts with jobs whose associated submission has no jobs: ", no_job_count)
	print("Number of drafts with degrees whose associated submission has no degrees: ", no_degree_count)


def restore_submission():
	"""
	restore the jobs/degrees to the submission record from the draft record
	"""
	no_job_count	= 0
	no_degree_count = 0
	submission_none_count = 0	

	print("Querying draft applications for current exam...")

	current_exam_code = "2016NOV"
	current_applications = ExamApplication.objects.filter(exam__code=current_exam_code, publish_status="DRAFT").prefetch_related("master__content__examapplication__applicationjobhistory_set", "master__content__examapplication__applicationdegree_set", "applicationjobhistory_set", "applicationdegree_set")

	TOTAL = current_applications.count()
	count = 0 

	for draft_app in current_applications:
		count += 1

		print(draft_app.id, draft_app.contact)

		pub_uuid = draft_app.publish_uuid
		sub_app = next((da.examapplication for da in draft_app.master.content.all() if da.publish_status=="SUBMISSION"), None)
		if sub_app == None:
			print("No submission record.", draft_app, sub_app)
			submission_none_count += 1
	
		if sub_app:
			if draft_app.applicationjobhistory_set.count() > 0 and sub_app.examapplication.applicationjobhistory_set.count() == 0:
				print("Draft has jobs, submission no jobs: ", draft_app, sub_app)
				no_job_count += 1

				sub_jobs = sub_app.examapplication.applicationjobhistory_set.all()
				for draft_job in draft_app.applicationjobhistory_set.all():
					if draft_job.publish_status == "DRAFT" and not (draft_job.publish_uuid in [j.publish_uuid for j in sub_jobs]):
						print("", "publishing job %s" % draft_job)
						draft_job.publish(replace=("application", sub_app), publish_type="SUBMISSION")

			if draft_app.applicationdegree_set.count() > 0 and sub_app.examapplication.applicationdegree_set.count() == 0:
				print("Draft has degrees, submission no degrees: ", draft_app, sub_app )
				no_degree_count += 1

				sub_degrees = sub_app.examapplication.applicationdegree_set.all()
				for draft_degree in draft_app.applicationdegree_set.all():
					if draft_degree.publish_status == "DRAFT" and not (draft_degree.publish_uuid in [d.publish_uuid for d in sub_degrees]):
						print("", "publishing degree %s" % draft_degree)
						draft_degree.publish(replace=("application", sub_app), publish_type="SUBMISSION")

		print("%.2f%%" % ((count/TOTAL)*100.0))

	print("TOTAL NUMBER OF DRAFT RECORDS EXAMINED: ", count)
	print("Number of draft records without submission records: ", submission_none_count)
	print("Number of drafts with jobs whose associated submission has no jobs: ", no_job_count)
	print("Number of drafts with degrees whose associated submission has no degrees: ", no_degree_count)

	print("Complete!")


def restore_one(contact):
	"""
	restore the jobs/degrees to the submission record from the draft record, or vice versa?
	"""

	current_exam_code = "2016NOV"
	current_application = ExamApplication.objects.filter(contact=contact, exam__code=current_exam_code, publish_status="DRAFT").prefetch_related("master__content__examapplication__applicationjobhistory_set", "master__content__examapplication__applicationdegree_set", "applicationjobhistory_set", "applicationdegree_set").first()
	draft_app = current_application

	print(draft_app.id, draft_app.contact)

	pub_uuid = draft_app.publish_uuid
	sub_app = next((da.examapplication for da in draft_app.master.content.all() if da.publish_status=="SUBMISSION"), None)

	if sub_app:
		sub_jobs = sub_app.examapplication.applicationjobhistory_set.all()
		for draft_job in draft_app.applicationjobhistory_set.all():
			if draft_job.publish_status == "DRAFT" and not (draft_job.publish_uuid in [j.publish_uuid for j in sub_jobs]):
				print("", "publishing job %s" % draft_job)
				draft_job.publish(replace=("application", sub_app), publish_type="SUBMISSION")
		sub_degrees = sub_app.examapplication.applicationdegree_set.all()
		for draft_degree in draft_app.applicationdegree_set.all():
			if draft_degree.publish_status == "DRAFT" and not (draft_degree.publish_uuid in [d.publish_uuid for d in sub_degrees]):
				print("", "publishing degree %s" % draft_degree)
				draft_degree.publish(replace=("application", sub_app), publish_type="SUBMISSION")

# CRITERIA DISCREPANCIES
# 1. NOV 2016: SUBMISSION HAS CRITERIA, DRAFT DOES NOT

# FIX PROCEDURE:
# RUN VIEWING METHODS
# FIX UUIDS
# FIX UUIDS ON SOLO SUBMISSIONS (NO DRAFT)
# RUN VIEWING METHODS
# FIX ANSWERS/PUBLISH

def compare_criteria(nes=None):
	# november exam applications
	nes=ExamApplication.objects.filter(exam__code='2016NOV')
	print("There are %s Nov 2016 Exam Applications." % nes.count())
	# november exam applications with no criteria responses
	# does not work:
	# nesnc=nes.exclude(submission_answer__all__isnull=False)
	nesnc=[]
	for e in nes:
		if not e.submission_answer.all():
			nesnc.append(e)
	print("There are %s Nov 2016 Exam Applications with no criteria responses." % len(nesnc))
	# november exams, no criteria, submission, draft and resubmission, and other
	nesncs=[]
	nesncd=[]
	nesncr=[]
	nesnco=[]
	sncdnc=[]
	scdnc=[]
	sncdc=[]
	for e in nesnc:
		ps=e.publish_status
		if ps=='SUBMISSION':
			nesncs.append(e)
		elif ps=='DRAFT':
			nesncd.append(e)
		elif ps=='EARLY_RESUBMISSION':
			nesncr.append(e)
		else:
			nesnco.append(e)
			print("ERROR?: PUBLISH STATUS IS: ", e.publish_status)
			print("")
	print("There are %s Nov 2016 SUBMISSION Exam Applications with no criteria responses." % len(nesncs))
	print("There are %s Nov 2016 DRAFT Exam Applications with no criteria responses." % len(nesncd))
	print("There are %s Nov 2016 RESUBMISSION Exam Applications with no criteria responses." % len(nesncr))
	print("There are %s Nov 2016 OTHER Exam Applications with no criteria responses." % len(nesnco))
	# compare submission to draft 
	# for each sub with no criteria, does the draft have criteria answers?
	for sub in nesncs:
		dft=ExamApplication.objects.filter(master__id=sub.master.id, publish_status='DRAFT')
		if dft and dft.count()==1:
			dft=dft[0]
			answers=dft.submission_answer.all()
			if not answers:
				# sub no dft no
				sncdnc.append(dft)
				print("SUB NO CRIT, DFT NO CRIT (same master)")
				print("sub record, no criteria: ", sub)
				print("dft record, no criteria ", dft)
				print("")
			else:
				# sub no dft yes
				sncdc.append(dft)
				print("SUB NO CRIT, DFT YES CRIT (same master)")
				print("sub record, no criteria: ", sub)
				print("dft record, no criteria ", dft)
				print("")
	# need to query for the group of nov and may exams that all have same uuids on jobs/degrees/criteria
	# script needs to fix uuid nums, then should we let the copying of criteria from sub to dft be manual?
	# or get the ok from Anna Read that we should do the copying in a script?

def yooyoo(nes=None):
	# compare uuids between nov 2016 and may 2017 exams
	# November Exam apps
	if not nes:
		nes=ExamApplication.objects.filter(exam__code='2016NOV')
	# May Exam apps
	# mes=ExamApplication.objects.filter(exam__code='2017MAY')
	exam = nes.first().exam.code
	print("There are %s %s Exam Applications." % (nes.count(),exam))
	# Nov Exam apps denied
	nesdd=[]
	for e in nes:
		if e.application_status in DENIED_STATUSES_LIST:
			nesdd.append(e)
	print("There are %s DENIED %s Exam Applications." % (len(nesdd), exam))
	nesdds=[]
	nesddd=[]
	nesddr=[]
	nesddo=[]
	for e in nesdd:
		ps=e.publish_status
		if ps=='SUBMISSION':
			nesdds.append(e)
		elif ps=='DRAFT':
			nesddd.append(e)
		elif ps=='EARLY_RESUBMISSION':
			nesddr.append(e)
		else:
			nesddo.append(e)
			print("ERROR?: PUBLISH STATUS IS: ", e.publish_status)
			print("")
	print("There are %s %s SUBMISSION Exam Applications denied." % (len(nesdds), exam))
	print("There are %s %s DRAFT Exam Applications denied." % (len(nesddd), exam))
	print("There are %s %s EARLY RESUBMISSION Exam Applications denied." % (len(nesddr),exam))
	print("There are %s %s OTHER Exam Applications denied." % (len(nesddo), exam))
	# look at people with denied nov exam apps who reapplied for may 2017 and have duplicate uuids from nov to may
	mays=set()	
	for e in nesdd:
		contact = e.contact
		mes=ExamApplication.objects.filter(contact=contact, exam__code='2017MAY')
		nov_uus=[a.publish_uuid for a in e.submission_answer.all()]
		nov_uus.sort()
		for me in mes:
			may_uus=[a.publish_uuid for a in me.submission_answer.all()]
			may_uus.sort()
			if nov_uus==may_uus:
				mays.add(me)
		# next( (may_app for mayapp in mes if cr.role_type == "PROVIDER")
	print("There are %s May 2017 Exam Applications that have duplicate uuids with a %s exam app." % (len(mays), exam))
	mayss=[]
	maysd=[]
	mayser=[]
	mayso=[]
	for e in mays:
		ps=e.publish_status
		if ps=='SUBMISSION':
			mayss.append(e)
		elif ps=='DRAFT':
			maysd.append(e)
		elif ps=='EARLY_RESUBMISSION':
			mayser.append(e)
		else:
			mayso.append(e)
			print("ERROR?: PUBLISH STATUS IS: ", ps)
			print("")
	print("There are %s MAY 2017 SUBMISSION Exam Applications that have duplicate uuids with a %s exam app." % (len(mayss), exam))
	print(mayss)
	print("There are %s MAY 2017 DRAFT Exam Applications that have duplicate uuids with a %s exam app." % (len(maysd), exam))
	print(maysd)
	print("There are %s MAY 2017 EARLY RESUBMISSION Exam Applications that have duplicate uuids with a %s exam app." % (len(mayser), exam))
	print(mayser)
	print("There are %s MAY 2017 OTHER Exam Applications that have duplicate uuids with a %s exam app." % (len(mayso), exam))
	print(mayso)
	return mayss


def fix_uuids(mays_subs_with_dup_uuids):
	for e in mays_subs_with_dup_uuids:
		master_id=e.master.id
		contact=e.contact
		# dupgrup=ExamApplication.objects.filter(contact=contact, master__id=master_id)
		# for each object on the submission create a new uuid and set it on sub and on corresponding obj on dft
		# OBJECTS CAN BE IN DIFFERENT ORDER FROM SUB TO DFT -- need to compare existing publish_uuids to verify
		sub=ExamApplication.objects.filter(contact=contact, master__id=master_id, publish_status='SUBMISSION').first()
		dft=ExamApplication.objects.filter(contact=contact, master__id=master_id, publish_status='DRAFT').first()
		if sub and dft:
			sub_jobs = sub.applicationjobhistory_set.all()
			dft_jobs = dft.applicationjobhistory_set.all()
			for sjob in sub_jobs:
				djob = next((djob for djob in dft_jobs if djob.publish_uuid == sjob.publish_uuid), None)
				if djob:
					newuu = uuid.uuid4()
					sjob.publish_uuid = newuu
					djob.publish_uuid = newuu
					sjob.save()
					djob.save()
				svd_uuid = sjob.verification_document.publish_uuid 
				dvd_uuid = djob.verification_document.publish_uuid
				if svd_uuid == dvd_uuid:
					new2_uuid = uuid.uuid4()
					sjob.verification_document.publish_uuid = new2_uuid
					djob.verification_document.publish_uuid = new2_uuid
					sjob.verification_document.save()
					djob.verification_document.save()
			sub_degrees = sub.applicationdegree_set.all()
			dft_degrees = dft.applicationdegree_set.all()
			for sdeg in sub_degrees:
				ddeg = next((ddeg for ddeg in dft_degrees if ddeg.publish_uuid == sdeg.publish_uuid), None)
				if ddeg:
					newuu = uuid.uuid4()
					sdeg.publish_uuid = newuu
					ddeg.publish_uuid = newuu
					sdeg.save()
					ddeg.save()
				svd_uuid = sdeg.verification_document.publish_uuid 
				dvd_uuid = ddeg.verification_document.publish_uuid
				if svd_uuid == dvd_uuid:
					new2_uuid = uuid.uuid4()
					sdeg.verification_document.publish_uuid = new2_uuid
					ddeg.verification_document.publish_uuid = new2_uuid
					sdeg.verification_document.save()
					ddeg.verification_document.save()
			sub_crits = sub.submission_answer.all()
			dft_crits = dft.submission_answer.all()
			for sans in sub_crits:
				dans = next((dans for dans in dft_crits if dans.publish_uuid == sans.publish_uuid), None)
				if dans:
					newuu = uuid.uuid4()
					sans.publish_uuid = newuu
					dans.publish_uuid = newuu
					sans.save()
					dans.save()

def fix_uuids_no_dft(mays_subs_with_dup_uuids):
	for e in mays_subs_with_dup_uuids:
		master_id=e.master.id
		contact=e.contact
		# dupgrup=ExamApplication.objects.filter(contact=contact, master__id=master_id)
		# for each object on the submission create a new uuid and set it on sub and on corresponding obj on dft
		# OBJECTS CAN BE IN DIFFERENT ORDER FROM SUB TO DFT -- need to compare existing publish_uuids to verify
		sub=ExamApplication.objects.filter(contact=contact, master__id=master_id, publish_status='SUBMISSION').first()
		dft=ExamApplication.objects.filter(contact=contact, master__id=master_id, publish_status='DRAFT').first()
		if sub and not dft:
			sub_jobs = sub.applicationjobhistory_set.all()
			for sjob in sub_jobs:
				newuu = uuid.uuid4()
				sjob.publish_uuid = newuu
				sjob.save()
				if sjob.verification_document:
					svd_uuid = sjob.verification_document.publish_uuid 
					new2_uuid = uuid.uuid4()
					sjob.verification_document.publish_uuid = new2_uuid
					sjob.verification_document.save()
			sub_degrees = sub.applicationdegree_set.all()
			for sdeg in sub_degrees:
				newuu = uuid.uuid4()
				sdeg.publish_uuid = newuu
				sdeg.save()
				if sdeg.verification_document:
					svd_uuid = sdeg.verification_document.publish_uuid 
					new2_uuid = uuid.uuid4()
					sdeg.verification_document.publish_uuid = new2_uuid
					sdeg.verification_document.save()
			sub_crits = sub.submission_answer.all()
			for sans in sub_crits:
				newuu = uuid.uuid4()
				sans.publish_uuid = newuu
				sans.save()
# BESIDES FIXING UUIDS -- IT LOOKS LIKE NOV 2016 DRAFT RECORDS GOT WIPED OUT (BECAUSE OF THE DUP UUIDS)?
# WE ALSO NEED TO RESTORE NOV 2016 DRAFT DATA FROM SUBMISSION

# def restore_nov_dfts():
	# prob just publish submission to draft? need to verify this with Jen, et al -- they should give the ok on the data set
	# pass

# nes = Nov draft exam apps that had duplicate uuids with may 
def fix_ans_reviews(nes):
	for ne in nes:
		rs=ne.review_assignments.all()
		is_problem = False

		for r in rs:
			ars=r.answer_reviews.all()
			for ar in ars:
				# if the ans review is pointing to May and the review is pointing to Nov
				# orig:
				# if ar.answer.content != r.content:
				if ar.answer.content.id != r.content.id:
					
					# make copy of answer
					if not is_problem:
						nov_exam_versions = r.content.examapplication.get_versions()
						nov_submission = nov_exam_versions["SUBMISSION"]
						if nov_submission:
							# ONLY PUBLISH IF DRAFT IS EMPTY?
							nov_submission.publish(publish_type="DRAFT")

						may_exam=ExamApplication.objects.get(contact=ne.contact, exam__code='2017MAY', publish_status='DRAFT')
						may_exam_versions = may_exam.get_versions()
						may_submission = may_exam_versions["SUBMISSION"]
						if may_submission:
							may_submission.publish(publish_type="DRAFT")

					is_problem = True
					# orig:
					# equivalent_review = ar.answer.content.reviews.filter(contact=r.contact, round=r.review_round).first()
					# should be this?:
					# actually we shouldn't be copying anything because the answer review comments were not overwritten 
					# by user -- the two answer reviews are still distinct -- it's just that they both point to answers
					# that point to May 2017 -- we need to get the Nov 2016 and point it back to Nov 2016 exam app
					# equivalent_review = Review.objects.filter(content=ar.answer.content ,contact=r.contact, review_round=r.review_round).first()

					# if equivalent_review:
					# 	AnswerReview.objects.create(
					# 		review=equivalent_review,
					# 		answer=ar.answer,
					# 		rating=ar.rating,
					# 		comments=ar.comments,
					# 		answered_successfully=ar.answered_successfully
					# 		)


					# orig:
					# ar.answer = r.content.review_answers.filter(question=ar.answer.question).first()
					# but i think this was intended:
					# ar.answer = r.answer_reviews.filter(answer__question=ar.answer.question).first()
					# or this??:
					ar.answer.content = r.content
					# or this?:
					# ar.answer = Answer.objects.filter(content=r.content, question=ar.answer.question).first()
					ar.answer.save()
					

					# correct_nov_answer = r.content.review_answers.filter(question=ar.answer.question)
					# ar.answer = correct_nov_answer
					# ar.save()
				# print(ar.answer.content.examapplication)
		if is_problem:
			print(ne)

def fix_answers(nes):
	for ne in nes:
		rs=ne.review_assignments.all()
		is_problem = False
		for r in rs:
			ars=r.answer_reviews.all()
			for ar in ars:
				# if the ans review is pointing to May and the review is pointing to Nov
				if ar.answer.content.id != r.content.id:
					app_answers_count = ne.submission_answer.all().count()				
					if not is_problem:
						nov_exam_versions = r.content.examapplication.get_versions()
						nov_submission = nov_exam_versions["SUBMISSION"]
						nov_draft = nov_submission = nov_exam_versions["DRAFT"]
						if nov_submission:
							if nov_draft:
								nov_dft_degrees = nov_draft.applicationdegree_set.all()
								nov_dft_jobs = nov_draft.applicationjobhistory_set.all()
								nov_dft_crit = nov_draft.submission_answer.all()
							if nov_draft and not nov_dft_degrees and not nov_dft_jobs and not nov_dft_crit:
								nov_submission.publish(publish_type="DRAFT")
								# pass
						may_exam=ExamApplication.objects.get(contact=ne.contact, exam__code='2017MAY', publish_status='DRAFT')
						may_exam_versions = may_exam.get_versions()
						may_submission = may_exam_versions["SUBMISSION"]
						may_draft = may_exam_versions["DRAFT"]
						if may_submission:
							if may_draft:
								may_submission.publish(publish_type="DRAFT")
								# pass
					is_problem = True
					equivalent_review = Review.objects.filter(content=ar.answer.content, contact=r.contact, review_round=r.review_round).first()
					print("equivalenet review is ", equivalent_review)
					if equivalent_review:
						AnswerReview.objects.create(
							review=equivalent_review,
							answer=ar.answer,
							rating=ar.rating,
							comments=ar.comments,
							answered_successfully=ar.answered_successfully
							)
					ar.answer = Answer.objects.filter(content_id=ne.id, question_id=ar.answer.question_id).first()
					print("ar.answer is ", ar.answer)
					ar.save()

					# if app_answers_count == 3:
					# 	pass
					# elif ar.answer.content.exam.code == '2017MAY' and r.content.exam.code == '2016NOV':
					# 	ar.answer.content = r.content
					# 	ar.answer.save()
					# correct_nov_answer = r.content.review_answers.filter(question=ar.answer.question)
					# ar.answer = correct_nov_answer
					# ar.save()

				# print(ar.answer.content.examapplication)
		if is_problem:
			print(ne)


# nes=ExamApplication.objects.filter(exam__code='2016NOV', publish_status='DRAFT', application_status__in=DENIED_STATUSES_LIST)[20:23]
def revyoo(nes):
	for ne in nes:
		print("TOP OF EXAM APP LOOP")
		rs=ne.review_assignments.all()
		is_problem = False
		for r in rs:
			print("TOP OF REVIEW LOOP")
			ars=r.answer_reviews.all()
			for ar in ars:
				# if the ans review is pointing to May and the review is pointing to Nov
				print("*****************************")
				print("TOP OF ANSWER REVIEW LOOP")
				print("ar.answer.content is: ", ar.answer.content.examapplication)
				print("ar.answer.content.master.id is: ", ar.answer.content.examapplication.master.id)
				print("ar.answer.content.id is ", ar.answer.content.id)
				print("r.content is: ", r.content)
				print("r.content.master.id is: ", r.content.master.id)
				print("r.content.id is ", r.content.id)
				print("---------------------------")
				print("ar.answer.question is: ", ar.answer.question)
				print("ar.review: ", ar.review)
				print("ar.review.content is: ", ar.review.content)
				print("ar.answer: ", ar.answer)
				print("---------------------------")
				print("ar.comments is ", ar.comments)
				print("")
				if ar.answer.content.id != r.content.id:
					app_answers = ne.submission_answer.all()
					# make copy of answer
					if not is_problem:
						nov_exam_versions = r.content.examapplication.get_versions()
						nov_submission = nov_exam_versions["SUBMISSION"]
						nov_draft = nov_exam_versions["DRAFT"]
						if nov_submission:
							if nov_draft:
								nov_dft_degrees = nov_draft.applicationdegree_set.all()
								nov_dft_jobs = nov_draft.applicationjobhistory_set.all()
								nov_dft_crit = nov_draft.submission_answer.all()
							if nov_draft and not nov_dft_degrees and not nov_dft_jobs and not nov_dft_crit:
								# BEFORE PUBLISHING -- MUST PRESERVE THE COMMENTS TO REVIEWERS ON THE Draft
								nov_submission.editorial_comments = nov_draft.editorial_comments
								nov_submission.save()
								nov_submission.publish(publish_type="DRAFT")
							print("SUBMISSION DEGREES")
							print(nov_submission.applicationdegree_set.all())
							print("SUBMISSION JOBS")
							print(nov_submission.applicationjobhistory_set.all())
							print("SUBMISSION CRITERIA")
							print([(a.question, a.text+" ***************************************** ") for a in nov_submission.submission_answer.all() if a.text])
							print("")
						else:
							print("No November submission")
							print()
						if nov_draft:
							# nov_dft_degrees = nov_draft.applicationdegree_set.all()
							# nov_dft_jobs = nov_draft.applicationjobhistory_set.all()
							# nov_dft_crit = nov_draft.submission_answer.all()
							print("DRAFT DEGREES")
							print(nov_draft.applicationdegree_set.all())
							print("DRAFT JOBS")
							print(nov_draft.applicationjobhistory_set.all())
							print("DRAFT CRITERIA")
							print([a.text+" ***************************************** " for a in nov_draft.submission_answer.all() if a.text])
							print("DRAFT REVIEWS")
							print(nov_draft.review_assignments.all())
							print("")
						else:
							print("No November draft")
							print()
						# now fix May 2017 draft by publishing sub to dft
						may_exam=ExamApplication.objects.get(contact=ne.contact, exam__code='2017MAY', publish_status='DRAFT')
						may_exam_versions = may_exam.get_versions()
						may_submission = may_exam_versions["SUBMISSION"]
						may_draft = may_exam_versions["DRAFT"]
						if may_submission:
							# you must test that draft is empty before publishing 
							if may_draft:
								may_dft_degrees = may_draft.applicationdegree_set.all()
								may_dft_jobs = may_draft.applicationjobhistory_set.all()
								may_dft_crit = may_draft.submission_answer.all()
							if may_draft:# and not may_dft_degrees and not may_dft_jobs and not may_dft_crit:
								# BEFORE PUBLISHING -- MUST PRESERVE THE COMMENTS TO REVIEWERS ON THE Draft
								may_submission.editorial_comments = may_draft.editorial_comments
								may_submission.save()								
								may_submission.publish(publish_type="DRAFT")
							print("SUBMISSION DEGREES")
							print(may_submission.applicationdegree_set.all())
							print("SUBMISSION JOBS")
							print(may_submission.applicationjobhistory_set.all())
							print("SUBMISSION CRITERIA")
							print([(a.question, a.text+" ***************************************** ") for a in may_submission.submission_answer.all() if a.text])
							print("")
						else:
							print("No May submission")
							print()
						if nov_draft:
							print("DRAFT DEGREES")
							print(may_draft.applicationdegree_set.all())
							print("DRAFT JOBS")
							print(may_draft.applicationjobhistory_set.all())
							print("DRAFT CRITERIA")
							print([a.text+" ***************************************** " for a in may_draft.submission_answer.all() if a.text])
							print("DRAFT REVIEWS")
							print(may_draft.review_assignments.all())
							print("")
						else:
							print("No May draft")
							print()
						# if ar.answer.content.id == may_draft.id:
						# 	ar.answer.content = r.content
						# 	ar.answer.save()		
					is_problem = True
					equivalent_review = Review.objects.filter(content=ar.answer.content.examapplication ,contact=r.contact, review_round=r.review_round).first()
					if equivalent_review:
						print("current nov review from loop is:", r)
						print("current reveiw contact is ", r.contact)
						print("current review content is ", r.content.examapplication)
						print("equivalent_review ise: ", equivalent_review)
						print("equivalent review contact is ", equivalent_review.contact)
						print("equivalent review content is ", equivalent_review.content.examapplication)
						print()
						print("CREATE new ANSWER REVIEW OBJECT WITH nov VALUES (e.g. commments added by reviewers)")
						print("review=equivalent_review: ", equivalent_review)
						print("answer=ar.answer: ", ar.answer)
						print("rating=ar.rating: ", ar.rating)
						print("comments=ar.comments: ", ar.comments)
						print("answered_successfully=ar.answered_successfully: ", ar.answered_successfully)
						AnswerReview.objects.create(
							review=equivalent_review,
							answer=ar.answer,
							rating=ar.rating,
							comments=ar.comments,
							answered_successfully=ar.answered_successfully
							)
						print()
					else:
						print("no equivalent review")
						print()
					print("ar.answer.content before: ", ar.answer.content)
					print("ar.answer.content.examapplication is: ", ar.answer.content.examapplication)
					# THIS MUST ONLY HAPPEN ONCE PER ANSWER BUT SAME ANSWER GETS REVIEWED IN MULTIPLE ROUNDS 
					# SO must enclose in id check?
					# we need to only do this if the answer is pointing to May 2017 and there are not three answers on the 2016 app
					# somehow test for 0 the first time?
					# answer_ids = []
					# if ne.submission_answer.all().count() < 3 and ar.answer.content.id == may_draft.id
					# 	ar.answer.content = r.content
					# 	ar.answer.save()					
					ar.answer = Answer.objects.filter(content_id=ne.id, question_id=ar.answer.question_id).first()
					ar.save()
					# if app_answers.count() == 3:
					# 	pass
					# elif ar.answer.content.exam.code == '2017MAY' and r.content.exam.code == '2016NOV':
					# 	ar.answer.content = r.content
					# 	ar.answer.save()					
					# print(
					# 	"ar.answer after = r.answer_reviews.filter(answer__question=ar.answer.question).first(): ",
					# 	r.answer_reviews.filter(answer__question=ar.answer.question).first()
					# 	)
					print("ar.answer.content after: ", ar.answer.content)
					print()
				# print(ar.answer.content.examapplication)
		if is_problem:
			print("PROBLEM DRAFT NOV EXAM APP: ", ne)
			print("********************  END OF ONE PROBLEM APP  ************************")
			print()

# NEXT: EARLY BIRD! ANY EARLY BIRDS CREATED SO FAR COULD BE A PROBLEM -- START WITH UUID CHECK?? OR DOES THE ORIG
# UUID SCRIPT HANDLE IT ALREADY? -- FALSE ALARM

def no_hup():
	while True:
		time.sleep(10)
		tim=Contact.objects.get(user__username=322218)
		print(tim)

ilist=[
321603,
155718,
281176,
219669,
271724,
301783,
147772,
109469,
291016,
299592,
315203,
231079,
309456,
306497,
321898
]

# keep record of what exam app the reviews were originally tied to
def orig_app(id_list):
	for uname in id_list:
		c = Contact.objects.get(user__username=uname)
		may_dft = ExamApplication.objects.get(exam__code='2017MAY', publish_status='DRAFT', contact=c)
		print("START-----------------")
		print("ORIGINAL EXAM APPLICATION is ", may_dft)
		rs = may_dft.review_assignments.all()
		for r in rs:
			if r.review_round in [1,2,3]:
				print("Review is ", r)
		print("END-------------------")
		print()

# script to remove reviews from group of apps and put them on dummy app (Arturo Figueroa 275302 may 2005 aicp app)
def move_reviews(id_list):
	afc = Contact.objects.get(user__username=275302)
	print("afc is ", afc)
	arturo = ExamApplication.objects.get(exam__code='2005MAY', publish_status='DRAFT', contact=afc)
	print("arturo is ", arturo)
	for uname in id_list:
		c = Contact.objects.get(user__username=uname)
		print("c is ", c)
		may_dft = ExamApplication.objects.get(exam__code='2017MAY', publish_status='DRAFT', contact=c)
		print("may_dft is ", may_dft)
		rs = may_dft.review_assignments.all()
		print("rs is ", rs)
		for r in rs:
			if r.review_round in [1,2,3]:
				print("r is ", r)
				r.content = arturo
				r.save()

# looks like uuids are ok
# need to switch master
# change publish_status
# fix uuid 
# remove duplicate answers -- compare the text of resub answer to text of dft answer
# if they match, delete the resub answer -- draft has the old answers, resub has old and new?
# then submit application 


	
def dup_subs(mds=None):
	tz_obj=pytz.timezone('UTC')
	jan31midnight = datetime.datetime(year=2017, month=1, day=31,)
	jan31utc = tz_obj.localize(jan31midnight)
	if not mds:
		# dup_sub_list = [282658, 328196, 327905, 257609, 314259, 255398, 285203, 261457, 270564]
		dup_sub_list = [299981, 328272, 281697, 220395]
		contact_set = Contact.objects.filter(user__username__in=dup_sub_list)
		mds=ExamApplication.objects.filter(exam__code='2017MAY', publish_status='DRAFT', application_status='EB_D', contact__in=contact_set)
	for md in mds:
		# this gets the original submission and draft
		# versions=md.get_versions()
		mces=ExamApplication.objects.filter(contact=md.contact, exam__code='2017MAY')
		subs=mces.filter(publish_status='SUBMISSION')
		dft=mces.get(publish_status='DRAFT')
		rsbs=mces.filter(publish_status='EARLY_RESUBMISSION')
		if subs.count() == 2 and dft and rsbs.count() == 0:
			print(dft)
			will_be_rsb=mces.get(publish_status='SUBMISSION', created_time__gt=jan31utc)
			will_be_rsb.publish_status = 'EARLY_RESUBMISSION'
			will_be_rsb.master = dft.master
			will_be_rsb.publish_uuid = dft.publish_uuid
			# REMOVE DUPLICATE SUBMISSION ANSWERS only IF THEIR TEXT MATCHES DRAFT.answer.text (old text)
			rsb_answers = will_be_rsb.submission_answer.all()
			if rsb_answers.count() > 3:
				for da in dft.submission_answer.all():
					match = next((ra for ra in rsb_answers if ra.text == da.text), None)
					print("matching resub answer is: ", match)
					print()
					print("matching resub answer text is: ")
					print(match.text)
					print("************************************************************")
					print()
					match.delete()
			will_be_rsb.save()
			print("made it through")
		elif subs.count() == 2 and dft and rsbs.count() == 1:
			print("*********************************")
			print(md)
			print("ONE DRAFT, TWO SUBS AND AN EARLY RESUB -------------------------")
			print("*********************************")
			print()
		elif subs.count() == 1 and dft and rsbs.count() == 0:
			# print("*********************************")
			# print(md)
			# print("ONE DRAFT, ONE SUB AND NO EARLY RESUB -------------------------")
			# print("*********************************")
			print()
		elif subs.count() == 1 and dft and rsbs.count() == 1:
			print("*********************************")
			print(md)
			print("ONE DRAFT, ONE SUB AND ONE RESUB  -------------------------")
			print("*********************************")
			print()


def dup_sub_and_rsb():
	pass

def vu(es):
	for mce in es:
		print(mce.master)
		print(mce)
		print(mce.publish_status)
		print(mce.application_status)
		print(mce.created_time)
		print("UUIDs ---------------------------------------------------: ")
		print(mce.publish_uuid)
		print([j.publish_uuid for j in mce.applicationjobhistory_set.all()])
		print([d.publish_uuid for d in mce.applicationdegree_set.all()])
		print([a.publish_uuid for a in mce.submission_answer.all()])
		for a in mce.submission_answer.all():
			print(a.publish_uuid)
			print(a.created_time)
			print()
		print()

def dup_ans(dft):
	versions = dft.get_versions()
	rsb=versions["EARLY_RESUBMISSION"]
	rsb_answers = rsb.submission_answer.all()
	dft = rsb.get_versions()["DRAFT"]
	if rsb_answers.count() > 3:
		for da in dft.submission_answer.all():
			match = next((ra for ra in rsb_answers if ra.text == da.text), None)
			print("matching resub answer is: ", match)
			print()
			print("matching resub answer text is: ")
			print(match.text)
			print("************************************************************")
			print()
			match.delete()
