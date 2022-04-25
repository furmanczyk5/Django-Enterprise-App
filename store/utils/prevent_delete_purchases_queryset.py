from django.db import models

class PreventDeletePurchasesQuerySet(models.QuerySet):

    def delete(self, *args, **kwargs):
        if self.exclude(purchases__isnull=True).exists():
            raise ValidationError("Cannot delete records with one or more purchases")
        else:
            super().delete(*args, **kwargs)