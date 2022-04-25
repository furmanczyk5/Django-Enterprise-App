from django.db import models
from content.models import Content, ContentManager
from content.utils import generate_filter_model_manager
from submissions.models import SubmissionModelMixin, Review, ReviewRole

REVIEW_STATUSES = (
    ("RECEIVED", "Received"),
    ("ESTIMATED", "Estimated"),
    ("UNDERWAY", "Underway"),
    ("COMPLETED", "Completed")

)

INQUIRY_UPLOAD_RESOURCE_CLASSES = (
    ("Ordinance", "Ordinance"),
    ("Plan", "Plan"),
    ("Monograph", "Monograph"),
    ("Article", "Article"),
    ("Staff report", "Staff report"),
    ("Other", "Other")
)


class Inquiry(Content, SubmissionModelMixin):
    response_text = models.TextField("Inquiry response", blank=True, null=True)
    review_status = models.CharField(max_length=50, choices=REVIEW_STATUSES, default="RECEIVED")
    hours = models.IntegerField(help_text="Hours to deduct form org's total", null=True, blank=True)

    objects = generate_filter_model_manager(ParentManager=ContentManager, content_type="RESEARCH_INQUIRY")()

    default_template = "research_inquiries/newtheme/inquiry-details.html"

    def save(self, *args, **kwargs):
        self.content_type = "RESEARCH_INQUIRY"
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural="Inquiries"


class InquiryReviewRole(ReviewRole):
    class_query_args = {"review_type":"RESEARCH_INQUIRY"}
    class Meta:
        proxy=True


class InquiryReview(Review):
    class_query_args = {"review_type":"RESEARCH_INQUIRY"}
    class Meta:
        proxy=True
        verbose_name = "Inquiry Assignment"
