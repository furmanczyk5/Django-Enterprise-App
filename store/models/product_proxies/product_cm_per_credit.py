from django.db import models
from django.utils import timezone

from events.models import EventSingle, EventMulti, Activity, Course, Event

from store.utils.prevent_delete_purchases_queryset import PreventDeletePurchasesQuerySet

from store.models.product import Product

class ProductCMPerCreditManager(models.Manager):
    """
    manager for querying event products
    """
    def get_queryset(self):
        return super().get_queryset().filter(product_type="CM_PER_CREDIT")


# TO CONSIDER... maybe this should move to the "cm" app...?
class ProductCMPerCredit(Product):
    objects = ProductCMPerCreditManager.from_queryset(PreventDeletePurchasesQuerySet)()

    def process_purchase(self, purchase_instance, purchase_json, *args, **kwargs):
        """
        function to write to iMIS, etc. that's specific to purchasing CM credits
        """
        if self.code == "PRODUCT_CM_PER_CREDIT" or self.code == "PRODUCT_CM_PER_CREDIT_2015":

            event_query = Event.objects.filter(publish_status="DRAFT", master=purchase_instance.content_master)
            event_query.update(submission_time=timezone.now())
            event_type = event_query.only("event_type").first().event_type # need to know event_type first to call proxy model specific provider_submit method
            
            if event_type == "EVENT_SINGLE":
                EventSubmissionModelClass = EventSingle
            elif event_type == "EVENT_MULTI":
                EventSubmissionModelClass = EventMulti
            elif event_type == "ACTIVITY":
                EventSubmissionModelClass = Activity
            elif event_type == "COURSE":
                EventSubmissionModelClass = Course
            else:
                EventSubmissionModelClass = Event

            event_submission = EventSubmissionModelClass.objects.filter(publish_status="DRAFT", master=purchase_instance.content_master).first()
            event_submission.provider_submit_async()

    def process_pending_check_purchase(self, purchase_instance, purchase_json, *args, **kwargs):
        # CODE HERE FOR ANYTHING THAT NEEDS TO BE DONE BEFORE CHECK IS RECEIVED
        #     i.e. email provider, email speakers, mark event as pending
        if self.code == "PRODUCT_CM_PER_CREDIT" or self.code == "PRODUCT_CM_PER_CREDIT_2015":

            event_query = Event.objects.filter(publish_status="DRAFT", master=purchase_instance.content_master)
            event_query.update(submission_time=timezone.now())
            event_type = event_query.only("event_type").first().event_type # need to know event_type first to call proxy model specific provider_submit method
            
            if event_type == "EVENT_SINGLE":
                EventSubmissionModelClass = EventSingle
            elif event_type == "EVENT_MULTI":
                EventSubmissionModelClass = EventMulti
            elif event_type == "ACTIVITY":
                EventSubmissionModelClass = Activity
            elif event_type == "COURSE":
                EventSubmissionModelClass = Course
            else:
                EventSubmissionModelClass = Event

            event_submission = EventSubmissionModelClass.objects.filter(publish_status="DRAFT", master=purchase_instance.content_master).first()
            event_submission.status = "P"
            event_submission.save()

            if event_submission.event_type != "ACTIVITY":
                event_submission.send_admin_emails(email_template="PROVIDER_EVENT_SUBMIT_CHECK_PAYMENT")
            event_submission.send_speaker_emails()

    class Meta:
        proxy = True