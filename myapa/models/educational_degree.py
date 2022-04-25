from django.db import models

from imis.models import CustomDegree, Counter
from myapa.models.proxies import IndividualContact, School
from myapa.models.constants import DEGREE_LEVELS


class BaseEducationalDegree(models.Model):
    """
    Base class for educational / school information... used both for My APA and the AICP exam application.
    Where possible, methods should be added here if they make sense for any job record.
    """
    contact = models.ForeignKey(IndividualContact, on_delete=models.CASCADE)
    school = models.ForeignKey(School, null=True, blank=True, on_delete=models.SET_NULL)
    other_school = models.CharField(max_length=80, blank=True, null=True)
    school_seqn = models.IntegerField(blank=True, null=True)  # imis custom_schoolaccredited seqn
    graduation_date = models.DateField(blank=True, null=True)
    level = models.CharField(max_length=50, choices=DEGREE_LEVELS)
    level_other = models.CharField(max_length=50, blank=True, null=True)
    is_planning = models.BooleanField(default=False)
    complete = models.BooleanField(default=False, blank=True)
    program = models.CharField(max_length=255, blank=True, null=True)
    is_current = models.BooleanField(default=False, blank=True)
    student_id = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        abstract = True


class EducationalDegree(BaseEducationalDegree):
    school = models.ForeignKey(
        School,
        null=True,
        blank=True,
        related_name="educational_degree",
        on_delete=models.SET_NULL
    )
    seqn = models.IntegerField(blank=True, null=True)  # imis seqn to match custom degree record

    def write_to_imis(self):

        degree_info = dict(
            id=self.contact.user.username,
            school_id=self.school.user.username if self.school else "",
            school_other=self.other_school,
            school_seqn=self.school_seqn or 0, # This is the pk to the
            degree_level=self.level,
            degree_level_other=self.level_other or "",
            degree_program=self.program,
            accredited_program=self.program if self.school_seqn else "",
            degree_date=self.graduation_date,
            degree_planning=self.is_planning,
            degree_complete=self.complete,
            school_student_id=self.student_id,
            is_current=self.is_current
        )

        imis_degree, is_created = CustomDegree.objects.update_or_create(
            seqn=self.seqn or Counter.create_id(counter_name="Custom_Degree"),
            defaults=degree_info
        )

        return imis_degree
