from django.utils import timezone
from django.apps import apps
from django.db import models

from store.utils.prevent_delete_purchases_queryset import PreventDeletePurchasesQuerySet
from store.models.product import Product

class ProductExamApplicationManager(models.Manager):
    """
    manager for querying registration
    """
    def get_queryset(self):
        return super().get_queryset().filter(product_type="EXAM_APPLICATION")

class ProductExamApplication(Product):
    """
    Exam product proxy class
    """
    objects = ProductExamApplicationManager.from_queryset(PreventDeletePurchasesQuerySet)()

    def process_purchase(self, purchase_instance, purchase_json, *args, **kwargs):
        """
        Executed on succesful payment for AICP Exam Application
        """
        # print("purchase instance is: ", purchase_instance)
        ExamApplication = apps.get_model(app_label="exam", model_name="ExamApplication")
        early_resubmission_app = None
        exam_application = None
        draft_app = None

        draft_app = ExamApplication.objects.filter(master = purchase_instance.content_master, publish_status='DRAFT')
        early_resubmission_app = ExamApplication.objects.filter(master = purchase_instance.content_master, publish_status='EARLY_RESUBMISSION')
        submission_app = ExamApplication.objects.filter(master = purchase_instance.content_master, publish_status='SUBMISSION')

        if early_resubmission_app and len(early_resubmission_app) == 1:
            exam_application = early_resubmission_app.first()
            if draft_app:
                exam_application.editorial_comments = draft_app.first().editorial_comments
        elif submission_app and len(submission_app) == 1:
            exam_application = submission_app.first()

        exam_application.application_status = "P"
        # It doesn't matter if they're encoded in Central time; they get converted to UTC somewhere
        # exam_application.submission_time = timezone.now(tz=central)
        exam_application.submission_time = timezone.now()
        exam_application.save()
        # Do not publish the "EARLY_RESUBMISSION" record -- leave the original draft alone, don't create a new draft
        # if exam_application.publish_status == "SUBMISSION":
        exam_application.publish(publish_type="DRAFT")

    class Meta:
        proxy = True