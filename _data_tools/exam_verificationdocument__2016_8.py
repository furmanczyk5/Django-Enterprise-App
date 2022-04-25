from exam.models import ApplicationJobHistory, ApplicationDegree

# !! DONT CALL DIRECTLY, THIS IS A HELPER FOR FUNCTIONS BELOW
def fix_verification_documents(ModelClass):
	"""
	Creates/Corrects publish versions for verification documents
		Can be used with ApplicationJobHistory or Application Degree
	"""

	# ModelClass should be either ApplicationJobHistory, or ApplicationDegree
	if ModelClass != ApplicationJobHistory and ModelClass != ApplicationDegree:
		raise Exception("Argument must be 'ApplicationJobHistory' or 'ApplicationDegree' class")

	print("Querying all submission versions for %s" % ModelClass._meta.verbose_name.title())
	sub_versions = ModelClass.objects.filter(application__exam__code="2016NOV", publish_status="SUBMISSION")
	TOTAL = sub_versions.count()
	count = 0
	print("TOTAL: %s")
	print("")

	for sub_version in sub_versions:

		count += 1

		versions = sub_version.get_versions()
		sub = versions["SUBMISSION"]
		dft = versions["DRAFT"]
		rsb = versions["EARLY_RESUBMISSION"]

		print("{0}, dft?:{1}, rsb?:{2}, {3}".format(sub.id, bool(dft), bool(rsb), sub))

		if dft and dft.verification_document:

			if dft.verification_document.publish_status == "DRAFT":
				print("", "Publishing DRAFT -> SUBMISSION")
				published_verification_sub = dft.verification_document.publish(publish_type="SUBMISSION")
				sub.verification_document = published_verification_sub
				sub.save()

		elif sub.verification_document:
			sub.verification_document.publish_status = "SUBMISSION"
			sub.verification_document.save()
			if dft:
				print("", "Publishing SUBMISSION -> DRAFT")
				published_verification_dft = sub.verification_document.publish(publish_type="DRAFT")
				dft.verification_document = published_verification_dft
				dft.save()
		else:
			print("", "NO VERIFICATION DOCS on sub or dft")


		if rsb:
			if sub.verification_document:

				existing_ver_ids = [sub.verification_document_id]
				if dft and dft.verification_document_id:
					existing_ver_ids.append(dft.verification_document_id)

				if rsb.verification_document and not rsb.verification_document_id in existing_ver_ids:
					print("", "EARLY_RESUBMISSION has it's own doc")
					rsb_verification_doc = rsb.verification_document
					rsb_verification_doc.publish_uuid = sub.verification_document.publish_uuid
					rsb_verification_doc.publish_status = "EARLY_RESUBMISSION"
					rsb.save()
				else:
					print("", "Publishing SUBMISSION -> EARLY_RESUBMISSION")
					published_verification_rsb = sub.verification_document.publish(publish_type="EARLY_RESUBMISSION")
					rsb.verification_document = published_verification_rsb
					rsb.save()

			else:

				if rsb.verification_document:
					print("", "EARLY_RESUBMISSION has it's own doc but no sub exists.")
					rsb_verification_doc = rsb.verification_document
					# if you get here the draft won't exist so this won't work
					# rsb_verification_doc.publish_uuid = dft.verification_document.publish_uuid
					rsb_verification_doc.publish_status = "EARLY_RESUBMISSION"
					rsb.save()


					# publish to sub
					# publish to draft
				else:
					print("", "also NO VERIFICATION DOC on rsb")

		print("%.2f%% complete" % (float(count/TOTAL)*100.0 ))
		print("")

	print("Finished!")


##########
# STEP 1 #
##########
def fix_publish_status_for_jobs_and_degrees():

	rsb_job_count = ApplicationJobHistory.objects.filter(application__exam__code="2016NOV", application__publish_status="EARLY_RESUBMISSION").exclude(publish_status="EARLY_RESUBMISSION").update(publish_status="EARLY_RESUBMISSION")
	print("Updated %s EARLY_RESUBMISSION jobs" % rsb_job_count)
	rsb_deg_count =ApplicationDegree.objects.filter(application__exam__code="2016NOV", application__publish_status="EARLY_RESUBMISSION").exclude(publish_status="EARLY_RESUBMISSION").update(publish_status="EARLY_RESUBMISSION")
	print("Updated %s EARLY_RESUBMISSION degrees" % rsb_deg_count)

	sub_job_count = ApplicationJobHistory.objects.filter(application__exam__code="2016NOV", application__publish_status="SUBMISSION").exclude(publish_status="SUBMISSION").update(publish_status="SUBMISSION")
	print("Updated %s SUBMISSION jobs" % sub_job_count)
	sub_deg_count = ApplicationDegree.objects.filter(application__exam__code="2016NOV", application__publish_status="SUBMISSION").exclude(publish_status="SUBMISSION").update(publish_status="SUBMISSION")
	print("Updated %s SUBMISSION degrees" % sub_deg_count)

	dft_job_count = ApplicationJobHistory.objects.filter(application__exam__code="2016NOV", application__publish_status="DRAFT").exclude(publish_status="DRAFT").update(publish_status="DRAFT")
	print("Updated %s DRAFT jobs" % dft_job_count)
	dft_deg_count = ApplicationDegree.objects.filter(application__exam__code="2016NOV", application__publish_status="DRAFT").exclude(publish_status="DRAFT").update(publish_status="DRAFT")
	print("Updated %s DRAFT degrees" % dft_deg_count)

	print("")
	print("Finished!")


##########
# STEP 2 #
##########

# Only call once!
def fix_verification_documents_applicationjobhistory():
	fix_verification_documents(ApplicationJobHistory)

# Only call once!
def fix_verification_documents_applicationdegree():
	fix_verification_documents(ApplicationDegree)



