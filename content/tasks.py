from __future__ import absolute_import

from celery import shared_task
from sentry_sdk import capture_message


@shared_task(name="make_content_public_task")
def make_content_public_task(class_name, id_num):
    """
    Makes content public at time specified by editor
    """
    current_content_instance = class_name.objects.get(id__exact=id_num)
    obj = current_content_instance
    obj.make_public()
    capture_message("Made content record public", level='info')


@shared_task(name="publish_content_task")
def publish_content_task(class_name, id_num, solr_publish, publish_type, database_alias, solr_base):
    """
    Publishes content at time specified by editor
    """
    current_content_instance = class_name.objects.get(id__exact=id_num)
    obj = current_content_instance
    obj.workflow_status = 'IS_PUBLISHED'
    obj.save()
    # this publish method is on Content (not Publishable)
    published_obj = obj.publish(publish_type=publish_type, database_alias=database_alias)
    if solr_publish:
        published_obj.solr_publish(solr_base=solr_base)
    capture_message("Published content record", level='info')


@shared_task(name="make_content_inactive_task")
def make_content_inactive_task(class_name, id_num):
    """
    Makes content record inactive at time specified by editor
    """
    current_content_instance = class_name.objects.get(id__exact=id_num)
    obj = current_content_instance
    obj.make_inactive()
    capture_message("Made content record inactive", level='info')
