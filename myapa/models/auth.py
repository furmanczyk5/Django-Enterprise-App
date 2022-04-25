from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class UserAuthorizationToken(models.Model):
    """
    Simple model to link contacts to auth tokens

    # TO DO MAYBE: remove if mobile app is outsourced
    # Don't know if this is how we want to do authorization on mobile app, but here it is...we can always delete it...
    """
    user = models.ForeignKey(User, related_name='authorizationtoken', on_delete=models.CASCADE)
    token = models.CharField(max_length=50)
    created_time = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):

        current_time = timezone.now()

        if self.created_time is None:
            self.created_time = current_time

        return super().save(*args, **kwargs)
