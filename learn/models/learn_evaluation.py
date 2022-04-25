from django.db import models

from comments.models import ExtendedEventEvaluation

class LearnCourseEvaluationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(comment_type="LEARN_COURSE")

class LearnCourseEvaluation(ExtendedEventEvaluation):
    objects = LearnCourseEvaluationManager()

    def __str__(self):
        if self.content:
            return self.content.title if self.content.title is not None else "[no title]"
        else:
            "[no content so no title]"

    def save(self, *args, **kwargs):
        self.comment_type = "LEARN_COURSE"
        super().save(*args, **kwargs)

    class Meta:
        verbose_name="APA Learn Course Eval/Completion"
        proxy = True

