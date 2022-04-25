from django.db import models

from conference.models import NationalConferenceActivity
from events.models import Activity
from . import LearnCourse


class LearnCourseInfo(models.Model):
    """
    Model to hold related information for an APA Learn Course

    """
    # to be displayed/edited as hh:mm:ss
    run_time = models.DurationField(null=True, blank=True)
    run_time_cm = models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True)
    vimeo_id = models.IntegerField(null=True, blank=True)
    # lms course id same as our "code"
    lms_course_id = models.CharField(max_length=200, null=True, blank=True, db_index=True)
    lms_template = models.IntegerField(null=True, blank=True)
    lms_product_page_url = models.URLField(max_length=255, blank=True, null=True)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    activity = models.OneToOneField(Activity, related_name="course_info_from",
                                    verbose_name="Activity Pulled From", blank=True, null=True)
    learncourse = models.OneToOneField(LearnCourse, related_name="course_info_to",
                                     verbose_name="Course Written To", blank=True, null=True)
