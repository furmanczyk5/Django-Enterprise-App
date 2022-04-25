from django.db import models
from django.contrib import messages

from .publishable_mixin import Publishable
from .base_content import BaseContent

# list of default message levels for use in our custom MessageText model
MESSAGE_LEVELS = sorted([(c[1], c[0]) for c in messages.constants.DEFAULT_LEVELS.items()],
                        key=lambda lev: lev[0])

MESSAGE_TYPES = (
    ("MESSAGE", "Erorr/warning/info message"),
    ("EMBEDDED", "Message/text embedded in app"),
    ("TOOLTIP", "Tooltip popup message")
)


class MessageText(BaseContent, Publishable):
    """
    To hold text messages to be passed to Django's Message object. This will allow messages
    to be edited in the admin and be publishable.
    """

    message_type = models.CharField(max_length=50, choices=MESSAGE_TYPES, default="MESSAGE")
    message_level = models.IntegerField(choices=MESSAGE_LEVELS, default=20, null=True, blank=True)
    text = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.text

    @classmethod
    def add_message(cls, request, code):
        """
        Adds a MessageText instance to django's built-in message framework, based on the message code.
        """
        try:
            message = MessageText.objects.get(code=code, status="A")
            messages.add_message(request, message.message_level, message.text)
        except:
            pass
            # silent fail

    @classmethod
    def set_content_messages(cls, context, message_codes):
        """
        adds a dictionary of messages to a context dictionary (for use in a front-end template).
        """
        content_messages = cls.objects.filter(code__in=message_codes, status="A")
        if "content_messages" not in context:
            context["content_messages"] = {}
        for message in content_messages:
            context["content_messages"][message.code] = message

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
