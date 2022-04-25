from django.db import models

from content.mail import Mail
from exam.prometric import Prometric

from store.utils.prevent_delete_purchases_queryset import PreventDeletePurchasesQuerySet
from store.models.product import Product

class ProductExamRegistrationManager(models.Manager):
    """
    manager for querying registration
    """
    def get_queryset(self):
        return super().get_queryset().filter(product_type="EXAM_REGISTRATION")

class ProductExamRegistration(Product):
    """
    Exam product proxy class
    """

    objects = ProductExamRegistrationManager.from_queryset(PreventDeletePurchasesQuerySet)()

    def process_purchase(self, purchase_instance, purchase_json, *args, **kwargs):
        """
        function to write to iMIS, etc. that's specific to events
        """

        # code here to get create gee code
        exam_registration = purchase_instance.examregistration_set.all().first()

        Prometric().submit_xelig(exam_registration=exam_registration)

        contact = purchase_instance.contact

        if exam_registration.registration_type.find("CAND") >= 0:
            mail_context = dict(
                contact=contact,
                purchase=purchase_instance
            )
            email_template_code = "EXAM_REGISTRATION_CAND"
            mail_to = contact.email
            Mail.send(email_template_code, mail_to, mail_context)
        else:
            mail_context = dict(
                contact=contact,
                purchase=purchase_instance,
                application=exam_registration.application
            )
            email_template_code = "EXAM_REGISTRATION_AICP"
            mail_to = contact.email
            Mail.send(email_template_code, mail_to, mail_context)

    class Meta:
        proxy = True