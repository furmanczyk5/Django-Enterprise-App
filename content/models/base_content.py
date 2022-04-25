from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from planning.models_subclassable import SubclassableModel

from .settings import STATUSES


# could not get unique = True to work... might be too late to make this change.
class BaseContent(SubclassableModel):
    code = models.CharField(max_length=200, null=True, blank=True, db_index=True)
    title = models.CharField(max_length=200, null=True, blank=True)
    status = models.CharField(
        "visibility status",
        max_length=5,
        choices=STATUSES,
        default='A',
        db_index=True
    )
    description = models.TextField(blank=True, null=True)

    slug = models.SlugField(blank=True, null=True,
            help_text="An identifier for the ending of the url - will be auto-generated based on the title for web pages.")

    created_by = models.ForeignKey(User, related_name='%(app_label)s_%(class)s_created_by', on_delete=models.PROTECT)
    updated_by = models.ForeignKey(User, related_name='%(app_label)s_%(class)s_updated_by', on_delete=models.PROTECT)

    created_time = models.DateTimeField(editable=False)
    updated_time = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):

        current_time = timezone.now()

        if self.created_by_id is None:

            #if created by not specified, then default to the administrator account:
            self.created_by = User.objects.using(kwargs.get("using")).get(username="administrator")

        if self.created_time is None:
            #then this is a newly created record... so set created time, and also updated by is the same as created by
            self.created_time = current_time
            self.updated_by = self.created_by

        self.updated_time = current_time

        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title if self.title is not None else "[no title]"

    class Meta:
        abstract = True
