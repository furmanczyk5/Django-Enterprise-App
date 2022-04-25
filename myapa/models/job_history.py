from django.db import models

from myapa.models.proxies import IndividualContact


class BaseJobHistory(models.Model):
    """
    Base class for job history information... used both for My APA and the AICP exam application. Where possible,
    methods should be added here if they make sense for any job record.
    """
    contact = models.ForeignKey(IndividualContact, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, null=True, blank=True)
    company = models.CharField(max_length=80, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=True)
    is_part_time = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class JobHistory(BaseJobHistory):
    """
    Stores My APA profile job history.
    """

    def __str__(self):
        return str(self.contact.user.username) + ' | ' + str(self.company) + ' | ' + str(self.title)

    class Meta:
        verbose_name = "job"
        verbose_name_plural = "job history"
