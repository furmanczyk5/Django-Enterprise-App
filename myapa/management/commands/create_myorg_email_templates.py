from django.core.management.base import BaseCommand

from content.models.email_template import EmailTemplate


EMAIL_FROM = "AICPCM@planning.org"


EMAILS = [
    {
        "code": "MYORG_NEW_ADMIN_TO_NEW_ADMIN",
        "title": "MYORG_NEW_ADMIN_TO_NEW_ADMIN",
        "subject": "Welcome to MyOrganization",
        "body": """<p>Dear {{ new_admin.first_name }} {{ new_admin.last_name }},</p>\r\n<p>You have been successfully added as an administrator for {{ organization.company }}.</p>\r\n<p>Please contact {{ admin.first_name }} {{ admin.last_name }} at {{ admin.email }} if you have questions about your new administrator role.</p>\r\n<p>If you feel you have received this email in error, or if you have questions about APA in general, please contact AICPCM@planning.org.</p>\r\n<p>Thank you,</p>\r\n<p>Alisa Moore <br/>Senior Program Associate<br />American Planning Association</p>"""
    },
    {
        "code": "MYORG_NEW_ADMIN_TO_OTHER_ADMINS",
        "title": "MYORG_NEW_ADMIN_TO_OTHER_ADMINS",
        "subject": "New administrator recently added",
        "body": """<p>Dear Admin,</p>\r\n<p> {{ new_admin.first_name }} {{ new_admin.last_name }} has been added as an administrator to {{ organization.company }}. If you have any questions, please contact AICPCM@planning.org.</p>\r\n<p>Thank you,</p>\r\n<p>Alisa Moore <br/>Senior Program Associate<br />American Planning Association</p>"""
    },
    {
        "code": "MYORG_REMOVED_ADMIN_TO_REMOVED_ADMIN",
        "title": "MYORG_REMOVED_ADMIN_TO_REMOVED_ADMIN",
        "subject": "Administrator access removed",
        "body": """<p>Dear {{ removed_admin.first_name }} {{ removed_admin.last_name }},</p>\r\n<p>You have been removed as an administrator from: {{ organization.company }}. If you feel you have received this email in error, please contact AICPCM@planning.org.</p>\r\n<p>Thank you,</p>\r\n<p>Alisa Moore <br />Senior Program Associate<br />American Planning Association</p>"""
    },
    {
        "code": "MYORG_REMOVED_ADMIN_TO_OTHER_ADMINS",
        "title": "MYORG_REMOVED_ADMIN_TO_OTHER_ADMINS",
        "subject": "Administrator access removed",
        "body": """<p>Dear Admin,</p>\r\n<p>{{ removed_admin.first_name }} {{ removed_admin.last_name }} has been removed as an administrator from {{ organization.company }}. If you have any questions, please contact AICPCM@planning.org.</p>\r\n<p>Thank you,</p>\r\n<p>Alisa Moore <br />Senior Program Associate<br />American Planning Association</p>"""
    }

]


class Command(BaseCommand):
    help = """Create new email templates needed by MyOrg"""

    def add_arguments(self, parser):
        # parser.add_argument('', nargs='+', type=int)
        pass

    def handle(self, *args, **options):
        for email in EMAILS:
            et, _ = EmailTemplate.objects.get_or_create(
                code=email["code"]
            )
            et.title = email['title']
            et.subject = email['subject']
            et.body = email['body']
            et.email_from = EMAIL_FROM
            et.save()
