from django.db import models
from django.db.models import Prefetch

from content.models import MasterContent
from content.utils import generate_filter_model_manager
from events.models import Event, EventManager

class LearnCourse(Event):

    class_queryset_args = {"content_type":"EVENT", "event_type":"LEARN_COURSE"}
    objects = generate_filter_model_manager(ParentManager=EventManager, event_type="LEARN_COURSE")()

    def __init__(self, *args, **kwargs):
        super(LearnCourse, self).__init__(*args, **kwargs)

        # TO DO ... is this necessary?
        self._meta.get_field('event_type').default = 'LEARN_COURSE'

    def save(self, *args, **kwargs):
        if self.event_type != 'LEARN_COURSE_BUNDLE':
            self.event_type = 'LEARN_COURSE'
        self.template = "learn/newtheme/course-details.html"
        super(LearnCourse, self).save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "APA Learn Course"


class CourseBundleManager(EventManager):

    def with_details(self, publish_status="PUBLISHED"):
        subcourse_masters = Prefetch("related",
            queryset=MasterContent.objects.filter(#publish_status=publish_status
                ).order_by("published_time"), to_attr="subcourse_masters")
        qs = super().with_details().prefetch_related(subcourse_masters)
        return qs

    def get_queryset(self):
        return super().get_queryset().filter(event_type="LEARN_COURSE_BUNDLE")

class LearnCourseBundle(LearnCourse):

    class_queryset_args = {"content_type":"EVENT", "event_type":"LEARN_COURSE_BUNDLE"}
    objects = CourseBundleManager()

    def __init__(self, *args, **kwargs):
        super(LearnCourseBundle, self).__init__(*args, **kwargs)
        self._meta.get_field('event_type').default = 'LEARN_COURSE_BUNDLE'

    def get_courses(self):
        return LearnCourse.objects.filter(parent__id=self.master_id,
            publish_status=self.publish_status).select_related("product")

    def get_total_cm_credits(self):
        total_cm_credits = 0
        for course in self.get_courses():
            total_cm_credits += course.get_total_cm_credits()
        return total_cm_credits

    def save(self, *args, **kwargs):
        self.event_type = 'LEARN_COURSE_BUNDLE'
        self.template = "learn/newtheme/course-details.html"
        super(LearnCourseBundle, self).save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "APA Learn Course Bundle"

