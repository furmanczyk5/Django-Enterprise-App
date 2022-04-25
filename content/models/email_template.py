from django.db import models
from .base_content import BaseContent


class EmailTemplate(BaseContent):
    email_from = models.EmailField(max_length=200, blank=False)
    email_to = models.EmailField(max_length=200, blank=True, help_text="Will this work with multiple addresses?")
    subject = models.CharField(max_length=200, blank=False)
    body = models.TextField(blank=False, help_text="Use {{ }} for passing values.")

    class Meta:
        verbose_name = "Email Template"
        verbose_name_plural = "Email Templates"
