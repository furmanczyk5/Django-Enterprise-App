from events.models import *

def publish_events_to_provider_dashboard(*master_ids):
	"""
	Pushes draft copies to submission copies using the publish method
	"""
	
	for master_id in master_ids:
		draft = Event.objects.filter(publish_status="DRAFT", master_id=master_id).first()
		if draft:
			draft.__class__ = draft.get_proxymodel_class()
			draft.publish(publish_type="SUBMISSION")
			print("pushed event %s from draft to submission copy" % master_id)
		else:
			print("could not find draft for %s" % master_id)

	print("complete")