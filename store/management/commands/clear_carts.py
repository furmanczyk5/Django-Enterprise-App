from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone
from sentry_sdk import capture_message

from events.models import EventMulti, NATIONAL_CONFERENCE_MASTER_ID
from imis.models import CustomEventSchedule
from store.models.purchase import Purchase


# Using the Django ORM delete() method is the safest way to delete
# things, mostly by ensuring any foreign key CASCADEs are properly handled.
# The downside is this can be quite slow and memory-intensive.
# If the total to delete is more than this number, send an email instead to the dev
# team for manual intervention.
MAX_RECORDS = 10000


def get_pending_purchases(cutoff, **kwargs):
    purchases = Purchase.objects.filter(
        order__isnull=True,
        created_time__lt=cutoff,
        **kwargs
    ).exclude(
        status='A'
    )
    return purchases


def hours_ago(hours):
    return timezone.now() - timedelta(hours=hours)


def days_ago(days):
    return timezone.now() - timedelta(days=days)


def notify(count):
    subject = "({}) Too many abandoned cart items ({}) to delete at once".format(
        settings.ENVIRONMENT_NAME,
        count
    )
    mail_body = """
    There are currently {} PENDING purchases that are scheduled to be deleted, but
    we've determined this is too many to do at once. Someone will have to manually delete
    them in batches. A good option would be to filter on a smaller date range than the
    30 days we've chosen here. See store/management/commands/clear_carts.py for more info.
    """.format(count)
    send_mail(
        subject=subject,
        message=mail_body,
        from_email='it@planning.org',
        recipient_list=['WebDev@planning.org']
    )


class Command(BaseCommand):
    help = """ """

    def add_arguments(self, parser):
        parser.add_argument(
            '-t',
            '--type',
            required=True,
            dest='clear_type'
        )

    def get_npc_ticketed_activities(self):
        self.npc = EventMulti.objects.get(
            publish_status="PUBLISHED",
            master_id=NATIONAL_CONFERENCE_MASTER_ID
        )
        return self.npc.get_activities().filter(product__isnull=False)

    def handle_npc_ticketed_activities(self):
        activities = self.get_npc_ticketed_activities()
        purchases = get_pending_purchases(
            cutoff=hours_ago(1),
            product__in=[x.product for x in activities]
        )
        self.stdout.write(
            self.style.WARNING(
                "timezone.now(): {} \n"
                "Preparing to delete {} PENDING NPC19 Ticketed Activity Purchases "
                "added more than 1 hour ago from Django and iMIS".format(
                    timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                    purchases.count()
                )
            )
        )
        for purchase in purchases:
            CustomEventSchedule.objects.filter(
                id=purchase.user.username,
                product_code__in=(purchase.product.imis_code, "{}_SBY".format(purchase.product.imis_code))
            ).exclude(
                status='A'
            ).delete()
        purchases.delete()

        self.stdout.write(
            self.style.SUCCESS(
                "Done!"
            )
        )

    def handle(self, *args, **options):
        if options['clear_type'] == 'activities':
            self.handle_npc_ticketed_activities()
        elif options['clear_type'] == 'all':
            purchases = get_pending_purchases(cutoff=days_ago(30))
            count = purchases.count()
            capture_message('Preparing to clear {} stale cart items'.format(count), level='info')
            if count > MAX_RECORDS:
                notify(count)
            else:
                purchases.delete()


def get_django_imis_cart_mismatch():
    """
    Show people who have empty Django carts but
    Inactive records in iMIS Custom Event Schedule
    """

    npc = EventMulti.objects.filter(
        publish_status="PUBLISHED",
        master_id=NATIONAL_CONFERENCE_MASTER_ID
    ).first()
    if npc is None:
        print('No EventMulti found with master_id {}'.format(NATIONAL_CONFERENCE_MASTER_ID))
        return
    activities = npc.get_activities_with_product_cart()
    for activity in activities:
        schedules = CustomEventSchedule.objects.filter(product_code=activity.product.code, status='I')
        if schedules.exists():
            purchases = Purchase.objects.filter(
                product__code=activity.code,
                order__isnull=True,
                user__username__in=[x.id for x in schedules]
            ).exclude(
                status='A'
            )
            for purchase in purchases:
                print('{}: {}...CES: {}... Cart: {}'.format(purchase.user.username, activity.title, schedules.status, purchase.status))
