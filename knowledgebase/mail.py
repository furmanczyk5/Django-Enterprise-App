from django.conf import settings
from sentry_sdk import capture_exception

from content.mail import Mail
from content.models import Content
from myapa.models import Contact


RESOURCE_PUBLISHED = 'KNOWLEDGEBASE_SUBMISSION_PUBLISHED'
RESOURCE_SUGGESTION_REJECTED = 'KNOWLEDGEBASE_SUBMISSION_REJECTED'
REVIEW_ASSIGNED = 'KNOWLEDGEBASE_REVIEW_ASSIGNED'
STORY_PUBLISHED = 'KNOWLEDGEBASE_SUBMISSION_PUBLISHED'
STORY_REJECTED = 'KNOWLEDGEBASE_SUBMISSION_REJECTED'
STORY_STATUS_MAP = {
    'A': 'KNOWLEDGEBASE_SUBMISSION_PUBLISHED',
    'I': 'KNOWLEDGEBASE_SUBMISSION_REJECTED'
}


def send_resource_accepted_email(contentrelationship):
    master_suggestion = contentrelationship.content_master_related
    resource_suggestion = Content.objects.get(master_id=master_suggestion.id)

    _send_email(
        RESOURCE_PUBLISHED,
        _get_emails_by_content(resource_suggestion),
        _get_mail_context(contentrelationship.content)
    )


def send_resource_published_email(content, resource_suggestion):
    _send_email(
        RESOURCE_PUBLISHED,
        _get_emails_by_content(resource_suggestion),
        _get_mail_context(content)
    )


def send_story_published_email(obj):
    _send_email(
        STORY_PUBLISHED,
        _get_emails_by_content(obj),
        _get_mail_context(obj)
    )


def send_story_rejected_email(obj):
    _send_email(
        STORY_REJECTED,
        _get_emails_by_content(obj),
        _get_mail_context(obj)
    )


def send_resource_rejected_email(obj):
    _send_email(
        RESOURCE_SUGGESTION_REJECTED,
        _get_emails_by_relationship(obj),
        _get_mail_context(obj.content)
    )


def send_reviewer_email(obj):
    _send_email(
        REVIEW_ASSIGNED,
        Contact.objects.get(id=obj.role.contact_id).email,
        _get_mail_context(obj.content)
    )


def _send_email(template, emails, context):
    try:
        Mail.send(template, emails, context)
    except Exception as e:
        capture_exception(e)


def _get_emails_by_content(obj):
    contact_roles = obj.contactrole.all()
    return _get_emails(contact_roles)


def _get_emails_by_relationship(obj):
    contact_roles = obj.content.contactrole.all()
    return _get_emails(contact_roles)


def _get_emails(contact_roles):
    emails = []

    for role in contact_roles:
        email = Contact.objects.get(id=role.contact_id).email
        if email:
            emails.append(email)

    return emails


def _get_mail_context(obj):
    return {
        'content': obj,
        'SERVER_ADDRESS': settings.SERVER_ADDRESS
    }
