import datetime

from django.utils import timezone
from django.db import models
from django.apps import apps

from content.mail import Mail

from store.utils.prevent_delete_purchases_queryset import PreventDeletePurchasesQuerySet
from store.models.product import Product

from exam.settings import CAND_ENROLL_EMAIL_TEMPLATES

class ProductCandidateEnrollmentManager(models.Manager):
    """
    manager for querying candidate enrollment products
    """
    def get_queryset(self):
        return super().get_queryset().filter(product_type="AICP_CANDIDATE_ENROLLMENT")

class ProductCandidateEnrollment(Product):
    """
    Candidate enrollment product proxy class
    """
    objects = ProductCandidateEnrollmentManager.from_queryset(PreventDeletePurchasesQuerySet)()

    def process_purchase(self, purchase_instance, purchase_json, *args, **kwargs):
        """
        Executed on succesful payment for AICP Candidate Enrollment
        """
        candidate_application = None
        contact = purchase_instance.contact
        now = timezone.now()
        # now_date = now.date()
        five_years = datetime.timedelta(days=365*5)

        # DO WE NEED THIS?
        # contact.sync_from_imis()
        
        Period = apps.get_model(app_label="cm", model_name="Period")
        Log = apps.get_model(app_label="cm", model_name="Log")
        period = Period.objects.get(code="CAND")
        log, created = Log.objects.get_or_create(
            contact=contact, period=period, status='A', is_current = True, 
            )
        if created:
            log.credits_required = 16
            log.law_credits_required = 1.5
            log.ethics_credits_required = 1.5
            log.begin_time = now
            log.end_time = now + five_years
        log.save()

        ExamApplication = apps.get_model(app_label="exam", model_name="ExamApplication")
        cand_app_queryset = ExamApplication.objects.filter(master = purchase_instance.content_master, publish_status='DRAFT')

        if cand_app_queryset and len(cand_app_queryset) == 1:
            candidate_application = cand_app_queryset.first()
        else:
            raise Exception("AICP CANDIDATE PROCESS PURCHASE RUNTIME WARNING: MORE THAN ONE DRAFT APPLICATION")

        app_status = candidate_application.application_status
        degree = candidate_application.applicationdegree_set.first()

        if app_status == 'N' and not degree.graduation_date:
            candidate_application.application_status = "EN"
        # elif (app_status == 'N' or app_status == 'EN') and degree.graduation_date < now_date:
        elif (app_status == 'N' or app_status == 'EN') and degree.graduation_date:
            candidate_application.application_status = "P"
        else:
            raise Exception("AICP CANDIDATE PROCESS PURCHASE RUNTIME WARNING: APPLICATION VIOLATES ACCEPTED CONDITIONS")

        candidate_application.submission_time = timezone.now()
        candidate_application.save()
        candidate_application.publish(publish_type="DRAFT")

        mail_context = dict(
            contact=contact,
        )
        email_template_code = CAND_ENROLL_EMAIL_TEMPLATES.get(candidate_application.application_status)
        mail_to = contact.email
        Mail.send(email_template_code, mail_to, mail_context)

    class Meta:
        proxy = True