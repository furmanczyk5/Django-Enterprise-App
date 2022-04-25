from django.db import models
from django.utils import timezone
from django.apps import apps
from django.db.models import Q

from cm.models import settings as cm_settings

from store.utils.prevent_delete_purchases_queryset import PreventDeletePurchasesQuerySet

from store.models.product import Product

from imis.models import Subscriptions, IndDemographics
from imis.models import Activity as ImisActivity

class ProductDuesManager(models.Manager):
    """
    manager for querying membership products
    """
    def get_queryset(self):
        return super().get_queryset().filter(product_type="DUES")

class ProductDues(Product):
    """
    Membership and Chapter product proxy class
    """

    objects = ProductDuesManager.from_queryset(PreventDeletePurchasesQuerySet)()

    def process_purchase(self, purchase_instance, purchase_json, *args, **kwargs):
        """
        function to write to iMIS, etc. that's specific to events
        """
        contact = purchase_instance.contact
        now = timezone.now()

        if purchase_instance.product.code == 'MEMBERSHIP_AICP_PRORATE':

            subs = contact.get_imis_subscriptions()

            contact.sync_from_imis()

            Period = apps.get_model(app_label="cm", model_name="Period")
            Log = apps.get_model(app_label="cm", model_name="Log")
            this_year = now.year

            if this_year % 2 == 0:
                begin_year = this_year + 2
            else:
                if now.month >= 11:
                    begin_year = this_year + 3
                else:
                    begin_year = this_year + 1

            period = Period.objects.filter(begin_time__year=begin_year).order_by('begin_time').first()
            # period = Period.objects.filter(begin_time__year__gt=this_year).order_by('begin_time').first()
            log, created = Log.objects.get_or_create(
                contact=contact, period=period, status='A', is_current = True,
                )
            # if log already exists:

            # if log is new:
            if created:
                log.credits_required = 32
                log.law_credits_required = 1.0
                log.ethics_credits_required = 1.0
                log.equity_credits_required = 1.0
                log.targeted_credits_required = 1.0
                log.targeted_credits_topic = cm_settings.TARGETED_CREDITS_TOPIC
                log.begin_time = now
                log.end_time = period.end_time

            log.save()

            cand_period = Period.objects.filter(code="CAND").first()
            cand_log = Log.objects.filter(contact=contact, period=cand_period).first() if cand_period else None
            if cand_log:
                cand_log.end_time = now
                cand_log.is_current = False
                cand_log.status = 'I'
                cand_log.save()

        # UPDATE IND_DEMOGRAPHICS DATA FOR STUDENT AND NEW MEMBERS
        elif purchase_instance.product.imis_code == "APA" and contact.salary_range in ("K", "L"):
            ind_demographics = IndDemographics.objects.get(id=contact.user.username)
            ind_demographics.update_student_new_member_demographics()

        contact.sync_from_imis()

    class Meta:
        proxy = True
