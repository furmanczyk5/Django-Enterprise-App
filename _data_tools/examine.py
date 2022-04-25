import django
django.setup()

from submissions.models import *
from exam.models import *

# code for testing exam application publishing

def see(es):
	for e in es:
		print("-------START--------------------")
		print("APPLICATION---------------------")
		if e.exam.code == '2016NOV':
			e.publish_status
			e.publish_uuid
			e.master
			e.application_status
			ads=e.applicationdegree_set.all()
			print("DEGREES ------------------------")
			for ad in ads:
				ad.school
				ad.publish_status
				ad.publish_uuid
				ad.verification_document
				if ad.verification_document:
					ad.verification_document.publish_status
					ad.verification_document.publish_uuid
					ad.verification_document.id
			ajs=e.applicationjobhistory_set.all()
			print("JOBS----------------------------")
			for aj in ajs:
				aj.company
				aj.publish_status
				aj.publish_uuid
				aj.verification_document
				if aj.verification_document:
					aj.verification_document.publish_status
					aj.verification_document.publish_uuid
					aj.verification_document.id
			print("CRITERIA ANSWERS -------------------")
			answers = e.submission_answer.all()
			for a in answers:
				a.question
				a.publish_status
				a.publish_uuid
		print("------ END --------------------------------------------------")
		print("-------------------------------------------------------------")

# FOR STAGING:
def ssee(es):
	for e in es:
		print("-------START--------------------")
		print("APPLICATION---------------------")
		if e.exam.code == '2016NOV':
			print(e.publish_status)
			print(e.publish_uuid)
			print(e.master)
			print(e.application_status)
			ads=e.applicationdegree_set.all()
			print("DEGREES ------------------------")
			for ad in ads:
				print(ad.school)
				print(ad.publish_status)
				print(ad.publish_uuid)
				print(ad.verification_document)
				if ad.verification_document:
					print(ad.verification_document.publish_status)
					print(ad.verification_document.publish_uuid)
			ajs=e.applicationjobhistory_set.all()
			print("JOBS----------------------------")
			for aj in ajs:
				print(aj.company)
				print(aj.publish_status)
				print(aj.publish_uuid)
				print(aj.verification_document)
				if aj.verification_document:
					print(aj.verification_document.publish_status)
					print(aj.verification_document.publish_uuid)
			print("CRITERIA ANSWERS -------------------")
			answers = e.submission_answer.all()
			for a in answers:
				print(a.question)
				print(a.publish_status)
				print(a.publish_uuid)
		print("------ END --------------------------------------------------")
		print("-------------------------------------------------------------")

#try:
# current_submission_qs = ExamApplication.objects.filter(
# 	master__id=9106200,
# 	publish_status='EARLY_RESUBMISSION',
# 	publish_uuid='80734b5c-3e3e-4b82-9e96-142e72723dd2'
# 	)

#print("CURRENT SUBMISSION QUERYSET IS .........................", current_submission_qs)

#except:
#current_submission_qs = None

# if not current_submission_qs:
#try:
	# current_submission_qs = ExamApplication.objects.filter(
	# 	master__id=9106200, 
	# 	publish_status='SUBMISSION',
	# 	publish_uuid='80734b5c-3e3e-4b82-9e96-142e72723dd2'
	# 	)

#	print("CURRENT SUBMISSION QUERYSET IS .........................", current_submission_qs)

#except:
#	current_submission_qs = None

# print("CURRENT SUBMISSION QUERYSET IS .........................", current_submission_qs)

#DATA CLEANUP SCRIPT: CHECK FOR RSB APPS WITH DFT V_DOCS AND DFT CRIT ANSWERS -- also rsb with jobs/degrees but sub and dft no jobs/degrees
# 1. fix publish status of verif docs and crit answers on rsb app -- should be "EARLY_RESUBMISSION"
# 2. if rsb has jobs/degrees but sub/dft has no jobs/degrees, publish the jobs/degrees back to the sub/dft


# ************* DATA CLEANUP: ELIZABETH JERNIGAN, Brittany Anderson, HAS DRAFT CRITERIA ANSWERS ON AN EARLY RESUBMISSION APP
# *** KRISTI WATKINS HAS JOBS/DEGREES ON THE RSB BUT NOT ON THE DRFT OR SUB RECORDS

# FIRST: clean up the group of early resub apps that have draft verif docs

# NEW PROBLEM: EARLY RESUBMISSION APPS WITH DRAFT VERIF DOCS

# JOB HIST OBJECTS
# QUERY FOR RSB job hist objects WITH DRAFT VERIF DOCS: -- START LOOKING AT THIS GROUP OF 24 -   these are 24 job history objects, not 24 applications
# ajs=ApplicationJobHistory.objects.filter(
# 	application__exam__code="2016NOV", 
# 	application__publish_status="EARLY_RESUBMISSION", 
# 	verification_document__publish_status="DRAFT",
# 	)

# how to compare the publish_uuids on these mismatched jobs to the draft/submission jobs?


# MAKE A QUERY ON DEGREE OBJECTS ALSO 



# THEN FIND A WAY TO GET THE APPLICATIONS FROM THE ABOVE QUERYSETS
# QUERY FOR RSB Applications WITH DRAFT VERIF DOCS:
# apps = []
# for job in ajs:
# 	apps.append(job.application)
# 	ass = set(apps)
# 	apps = list(ass)


# QUERY FOR APP GROUP WITH RSB THAT HAS JOBS/DEGREES BUT SUB AND/OR DFT HAS NONE
# rsbs=ExamApplication.objects.filter(
# 	exam__code="2016NOV", 
# 	publish_status="EARLY_RESUBMISSION"
# 	)

# no_jobs= []

# for rsb in rsbs:
# 	no_jobs.append(
# 		ExamApplication.objects.filter(
# 			master_id=rsb.master_id,
# 			publish_uuid=rsb.publish_uuid,
# 			applicationjobhistory__isnull=True
# 			)
# 		)

# no_degrees = []

# for rsb in rsbs:
# 	no_degrees.append(
# 		ExamApplication.objects.filter(
# 			master_id=rsb.master_id,
# 			publish_uuid=rsb.publish_uuid,
# 			applicationdegree__isnull=True
# 			)
# 		)

def rsb_answers():
	for rsb in rsbs:
		answers = rsb.submission_answer.all()
		for a in answers:
			print("rsb is .................", rsb)
			print(a.question)
			print(a.publish_status)
			print(a.publish_uuid)
			print("END.....................")
			print("")


# QUERY FOR APP GROUP WITH RSB THAT HAS DRAFT CRITERIA ANSWERS
# dcas=ExamApplication.objects.filter(
# 	application__exam__code="2016NOV", 
# 	application__publish_status="EARLY_RESUBMISSION", 
# 	verification_document__publish_status="DRAFT"
# 	)



# ajs=ApplicationJobHistory.objects.filter(application__exam__code="2016NOV", application__publish_status="SUBMISSION", verification_document__publish_status="DRAFT")
# None


 # if you get a key error e.g. "round_2_contact" ... check the review assignments

# LIST OF RESUB APPS:
def resubs():

	apps=set()

	jobs=ApplicationJobHistory.objects.filter(
		application__exam__code="2016NOV", 
		application__publish_status="EARLY_RESUBMISSION", 
		verification_document__publish_status="DRAFT",
		)

	degrees=ApplicationDegree.objects.filter(
		application__exam__code="2016NOV", 
		application__publish_status="EARLY_RESUBMISSION", 
		verification_document__publish_status="DRAFT",
		)

	for aj in jobs:
		apps.add(aj.application)

	for ad in degrees:
		apps.add(ad.application)

	for app in apps:
		versions=app.get_versions()
		sub = versions["SUBMISSION"]
		dft = versions["DRAFT"]
		rsb = versions["EARLY_RESUBMISSION"]
		vers_list = [sub, dft, rsb]

		for v in vers_list:
			if v:
				e=v
				print("NEXT APPLICATION ---------------------------------")
				if e.exam.code == '2016NOV':
					print(e)
					print(e.publish_status)
					print(e.publish_uuid)
					print(e.master)
					print(e.application_status)
					ads=e.applicationdegree_set.all()
					print("DEGREES ------------------------")
					for ad in ads:
						print(ad.school)
						print(ad.publish_status)
						print(ad.publish_uuid)
						print(ad.verification_document)
						if ad.verification_document:
							print(ad.verification_document.publish_status)
							print(ad.verification_document.publish_uuid)
					ajs=e.applicationjobhistory_set.all()
					print("JOBS----------------------------")
					for aj in ajs:
						print(aj.company)
						print(aj.publish_status)
						print(aj.publish_uuid)
						print(aj.verification_document)
						if aj.verification_document:
							print(aj.verification_document.publish_status)
							print(aj.verification_document.publish_uuid)
					print("CRITERIA ANSWERS -------------------")
					answers = e.submission_answer.all()
					for a in answers:
						print(a.question)
						print(a.publish_status)
						print(a.publish_uuid)
				print("------ END --------------------------------------------------")

# LOOK AT ALL RESUB APPS with publish status discrepancy 
def rsb_all():

	tot=ExamApplication.objects.filter(exam__code="2016NOV", publish_status="EARLY_RESUBMISSION")

	for app in tot:
		versions=app.get_versions()
		sub = versions["SUBMISSION"]
		dft = versions["DRAFT"]
		rsb = versions["EARLY_RESUBMISSION"]
		vers_list = [sub, dft, rsb]

		for v in vers_list:
			if v:
				e=v
				print("NEXT APPLICATION ---------------------------------")
				if e.exam.code == '2016NOV':
					print(e)
					print(e.publish_status)
					print(e.publish_uuid)
					print(e.master)
					print(e.application_status)
					ads=e.applicationdegree_set.all()
					print("DEGREES ------------------------")
					for ad in ads:
						print(ad.school)
						print(ad.publish_status)
						print(ad.publish_uuid)
						print(ad.verification_document)
						if ad.verification_document:
							print(ad.verification_document.publish_status)
							print(ad.verification_document.publish_uuid)
					ajs=e.applicationjobhistory_set.all()
					print("JOBS----------------------------")
					for aj in ajs:
						print(aj.company)
						print(aj.publish_status)
						print(aj.publish_uuid)
						print(aj.verification_document)
						if aj.verification_document:
							print(aj.verification_document.publish_status)
							print(aj.verification_document.publish_uuid)
					print("CRITERIA ANSWERS -------------------")
					answers = e.submission_answer.all()
					for a in answers:
						print(a.question)
						print(a.publish_status)
						print(a.publish_uuid)
				print("------ END --------------------------------------------------")


# THESE ARE RESUB APPS WITH NO JOBS/DEGREES
def resub_no_jobs():
	# find resub apps with no jobs/degrees
	# bapps = broken apps
	bapps=set()
	tot=ExamApplication.objects.filter(exam__code="2016NOV", publish_status="EARLY_RESUBMISSION")

	for app in tot:
		if not app.applicationjobhistory_set.all() and not app.applicationdegree_set.all():
			bapps.add(app)
	print(len(bapps), " resub apps with no jobs/degrees.")
	print(bapps)

	print("PUBLISH STATUS RUNDOWN ------------------------")
	for ba in bapps:
		print(ba)
		print(ba.publish_status)
		for j in ba.applicationjobhistory_set.all():
			print(j)
			print(j.publish_status)
			print(j.verification_document)
			print(j.verification_document.publish_status)
			print("")

	return bapps

# to find resub apps whose sub/dft versions have no jobs/degrees
def resub_no_jobs_others():
	# find resub apps with no jobs/degrees
	# bapps = broken apps
	bapps=set()
	tot=ExamApplication.objects.filter(exam__code="2016NOV", publish_status="EARLY_RESUBMISSION")
	no_sub_dft = 0
	multiples = 0

	for app in tot:
		versions=app.get_versions()
		sub = versions["SUBMISSION"]
		dft = versions["DRAFT"]
		rsb = versions["EARLY_RESUBMISSION"]
		vers_list = [sub, dft, rsb]

		subq=ExamApplication.objects.filter(exam__code="2016NOV", publish_status="SUBMISSION")
		dftq=ExamApplication.objects.filter(exam__code="2016NOV", publish_status="DRAFT")

	for app in tot:
		subs=ExamApplication.objects.filter(master__id=app.master.id, publish_status="SUBMISSION")
		dfts=ExamApplication.objects.filter(master__id=app.master.id, publish_status="DRAFT")		

		for sub in subs:
			if sub:
				print("------------------")
				print("SUB ON SAME MASTER AS RESUB")
				print(sub)
				print(sub.master)
				print(sub.publish_status)
				print("sub uuid: ", sub.publish_uuid)
				print("resub uuid: ", app.publish_uuid)
				print("-----------------")

		for dft in dfts:
			if dft:
				print("------------------")
				print("DFT ON SAME MASTER AS RESUB")
				print(dft)
				print(dft.master)
				print(dft.publish_status)
				print("dft uuid: ", dft.publish_uuid)
				print("resub uuid: ", app.publish_uuid)
				print("-----------------")

		if sub and dft:
			if not sub.applicationjobhistory_set.all() and not sub.applicationdegree_set.all()\
				and not dft.applicationjobhistory_set.all() and not dft.applicationdegree_set.all():
				bapps.add(app)

		if (len(subq) <= 1) and (len(dftq) <=1):
			subq=subq.first()
			dftq =dftq.first()
			
			if subq and dftq:
				if not subq.applicationjobhistory_set.all() and not subq.applicationdegree_set.all()\
					and not dftq.applicationjobhistory_set.all() and not dftq.applicationdegree_set.all():
					bapps.add(app)			
		else:
			print("FOUND MULTIPLE SUBS OR DFTS")
			multiples+=1

		if not sub and not dft:
			no_sub_dft += 1

	print("PUBLISH STATUS RUNDOWN ------------------------")
	for ba in bapps:
		print(ba)
		print(ba.publish_status)
		for j in ba.applicationjobhistory_set.all():
			print(j)
			print(j.publish_status)
			print(j.verification_document)
			print(j.verification_document.publish_status)
			print("")

	print(len(bapps), " resub apps with no jobs/degrees on sub/dft versions.")
	print(bapps)
	print(no_sub_dft, " resub apps with no sub/dft apps at all.")
	print(multiples, " resub apps with multiple subs or dfts.")
	print("\n")

	return bapps

# ers= early resubmissions -- get all apps for each user with an early resubmission
def ers(es):
	for e in es:
		eyed=e.master.id
		qset=ExamApplication.objects.filter(exam__code='2016NOV', master__id=eyed)
		see(qset)

# GET LIST OF MASTER IDS FOR RESUB APPS WITH NO JOBS AND NO DEGREES
def get_mids():
	ersbs=ExamApplication.objects.filter(publish_status='EARLY_RESUBMISSION', exam__code='2016NOV')
	masterids = []
	for rsb in ersbs:
		if not rsb.applicationjobhistory_set.all() and not rsb.applicationdegree_set.all():
			masterids.append(rsb.master.id)
	return masterids

# staging mids
mids = [
9103876,
 9103842,
 9104011,
 9104195,
 9103739,
 9103712,
 9104363,
 9104018,
 9104397,
 9104187,
 9103709,
 9103688,
 9104053,
 9104007,
 9103806,
 9103996,
 9104364,
 9104182,
 9104358,
 9103986,
 9103778,
 9103723,
 9103698,
 9104664,
 9104723,
 9103800,
 9104130,
 9104740,
 9103697,
 9103683,
 9104328,
 9103749,
 9104000,
 9104092,
 9104417
 ]

# prod list of masters:
pmids = [
9103723,
 9103876,
 9104364,
 9104053,
 9104397,
 9104358,
 9103986,
 9104723,
 9104182,
 9103709,
 9104130,
 9103688,
 9103806,
 9104018,
 9104007,
 9103996,
 9103698,
 9103739,
 9104011,
 9104195,
 9103778,
 9103842,
 9104664,
 9104187,
 9103800,
 9104363,
 9103712,
 9103697,
 9104328,
 9103683,
 9104092,
 9103749,
 9104000,
 9104740,
 9104417
 ]

def restore_apps(masterids, db_key):
	# check that jobs/degrees are empty -- done in get_mids above
	for mas in masterids:
		es=ExamApplication.objects.filter(exam__code='2016NOV', master__id=mas)
		for e in es:
			# Because only the draft records have uploads -- because verif docs were'nt publishing correctly
			if e.publish_status == 'DRAFT':
				# Don't do this...it will return the exam object from the target which has no degrees/jobs
				# e.save(using='staging')
				for vd in e.uploads.all():
					vd.save(using=db_key)
				for j in e.applicationjobhistory_set.all():
					j.save(using=db_key)
				for d in e.applicationdegree_set.all():
					d.save(using=db_key)

def vu(mids):
	for n in mids:
		es=ExamApplication.objects.filter(master__id=n, exam__code='2016NOV')#, publish_status='DRAFT')
		for e in es:
			print(e.publish_status)
			print(e.applicationjobhistory_set.all())
			print(e.applicationdegree_set.all())
			print(e.uploads.all())
			print("")