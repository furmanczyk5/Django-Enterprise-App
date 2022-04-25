from django.db import models
from django.utils import timezone

from content.models.content import Content
from myapa.models.contact import Contact
from myapa.models.constants import CONTENT_ADDED_TYPES


# this is a simpler relationship between a contact and a piece of content... for tracking actions such as "saving to schedule"
# QUESTION... would it make more sense for this relationship to be defined with MasterContent instead of content?
#           (assume it's OK as is to keep the joins simpler)
# TO DO: simplify or get rid of this model... (for example CM claims now moved to cm and comments apps...)
class ContactContentAdded(models.Model):
    content = models.ForeignKey(Content, related_name='contactcontentadded', on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, related_name='contactcontentadded', on_delete=models.CASCADE)
    added_type = models.CharField(max_length=50, choices=CONTENT_ADDED_TYPES, default="BOOKMARK")
    added_time = models.DateTimeField(editable=False)
    comments = models.TextField(blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)

    def save(self, *args, **kwargs):

        current_time = timezone.now()

        if self.added_time is None:
            self.added_time = current_time

        return super().save(*args, **kwargs)

    # is this adding unnecessary db hits??
    def __str__(self):
        return self.added_type + " | " + str(self.contact) + " | " + str(self.content)
