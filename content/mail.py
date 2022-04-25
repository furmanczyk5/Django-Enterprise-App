from html import unescape

from django.conf import settings
from django.core.mail import EmailMessage
from django.template import Template, Context
from sentry_sdk import capture_exception

from content.models import EmailTemplate


DEV_TEAM_EMAILS = [
        'rwest@planning.org',
        'plowe@planning.org',
        'akrakos@planning.org',
        'tjohnson@planning.org',
        'msullivan@planning.org',
        'mgranja@planning.org',
        'cmollet@planning.org',
]


class Mail(object):

    # TO DO.. this is is not well implemented... it would make much more sense to create send() as a method on the EmailTemplate class,
    # not some static method on this random class

    @staticmethod
    def send(mail_code='', mail_to='', mail_context=None):
        """
        combines context and mail template (based on mail_code). sends email.
        """
        try:
            mailtemplate = EmailTemplate.objects.get(code=mail_code)

            if mailtemplate.status == 'A':
                subject_template = Template(unescape(mailtemplate.subject))
                body_template = Template(unescape(mailtemplate.body))

                # Mail to requires a list
                mail_to_list = []

                # if no mail_to value is passed use mail_to from template (used for reporting issues)
                if mail_to == '' or mail_to is None or mail_to == [] or mail_to == ['']:
                    mail_to = mailtemplate.email_to
                mail_from = mailtemplate.email_from
                mail_subject = subject_template.render(Context(mail_context or {}))
                mail_body = body_template.render(Context(mail_context or {}))

                if settings.ENVIRONMENT_NAME == 'PROD' \
                        or (settings.ENVIRONMENT_NAME == 'STAGING' and '@planning.org' in mail_to):
                    # send prod and internal planning.org staging emails as normal:
                    if isinstance(mail_to, list):
                        mail_to_list.extend(mail_to)
                    else:
                        mail_to_list.append(mail_to)
                    msg = EmailMessage(
                        mail_subject,
                        mail_body,
                        mail_from,
                        mail_to_list,
                        ["confirmations@realmagnet.com"],  # always Bccing RealMagent for email tracking with marketing
                    )
                    msg.content_subtype = "html"
                    msg.send(fail_silently=True)

                elif settings.ENVIRONMENT_NAME == 'STAGING' and '@planning.org' not in mail_to:
                    # send external staging emails only to IT as tests:
                    mail_to_list.extend(DEV_TEAM_EMAILS)
                    msg = EmailMessage(
                        mail_subject,
                        mail_body,
                        mail_from,
                        mail_to_list,
                        ["confirmations@realmagnet.com"],
                    )
                    msg.content_subtype = "html"
                    msg.send(fail_silently=False)
                else:
                    # for local development, print the fact that an email would be sent:
                    if isinstance(mail_to, list):
                        mail_to_list = ', '.join(mail_to)
                    else:
                        mail_to_list = mail_to
                    print("EMAIL WOULD BE SENT TO: " + mail_to_list + " | FROM: " + mail_from + " | SUBJECT: " + mail_subject)
                    print("EMAIL BODY: " + mail_body)

        except Exception as exc:
            capture_exception(exc)
