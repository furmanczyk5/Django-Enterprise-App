import uuid

from uploads.models import Upload

def assign_publish_uuids_and_statuses_to_uploads():
	"""
	Only run this once when uploads are first converted to publishable
	"""
	print("Starting Assignment of publish_uuids for Uploads")

	uploads = Upload.objects.all()
	TOTAL = uploads.count()
	count = 0

	print("%s TOTAL RECORDS" % TOTAL)
	print("")

	for upload in uploads:
		count += 1
		publish_uuid = uuid.uuid4()
		upload.publish_status = "SUBMISSION"
		upload.publish_uuid = publish_uuid
		upload.save()
		print("Completed %s (%.2f%%)" % (upload, float(count/TOTAL)*float(100.0)))

	print("")
	print("")

	print("Flawless Victory!")