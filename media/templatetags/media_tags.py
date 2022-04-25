from django import template

from media.models import Media

register = template.Library()


@register.simple_tag
def media_link(master_id):
	try:
		media_record = Media.objects.filter(publish_status="PUBLISHED", master_id=master_id).first()
		return media_record.get_file().url
	except:
		return ""

