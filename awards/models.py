from django.db import models

from content.models import Content, BaseAddress
from submissions.models import Category, Review


class SubmissionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            content_type="AWARD", publish_status="SUBMISSION")


class Submission(Content, BaseAddress):
    """
    stores award nomination entries.
    """
    objects = SubmissionManager()

    is_finalist = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.content_type = "AWARD"
        self.publish_status = "SUBMISSION"
        super(Submission, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Award Nomination"
        verbose_name_plural = "Award Nominations"


class SubmissionCategoryManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(content_type="AWARD")


class SubmissionCategory(Category):
    """
    view award categories for submissions
    """
    objects = SubmissionCategoryManager()

    def save(self, *args, **kwargs):
        self.content_type = "AWARD"
        return super(SubmissionCategory, self).save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "Award Category"
        verbose_name_plural = "Award Categories"


class JurorAssignmentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            content__content_type="AWARD", review_type="AWARDS_JURY")


class JurorAssignment(Review):
    """
    view jurors and their assignments for awards
    """
    objects = JurorAssignmentManager()

    def save(self, *args, **kwargs):
        self.review_type = "AWARDS_JURY"
        return super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "Juror Assignment"
