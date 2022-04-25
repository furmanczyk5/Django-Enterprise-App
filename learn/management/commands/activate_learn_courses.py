import csv
from datetime import datetime

import pytz
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from events.models import Course
from myapa.models import Contact
from pages.models import LandingPageMasterContent
from store.models import ProductPrice

TZ = pytz.timezone("America/Chicago")
BEGIN_TIME = TZ.localize(datetime(2018, 11, 14))
END_TIME = TZ.localize(datetime(2021, 11, 14))
ARCHIVE_TIME = TZ.localize(datetime(2024, 11, 14))

NPC17_EVENT_MULTI_MASTER_ID = 9102340
NPC18_EVENT_MULTI_MASTER_ID = 9135594

COURSE_CATALOG_URL = "https://{}/catalog/".format(settings.LEARN_DOMAIN)

# In this case we want to send them to the generic product page
# with the legendary Get It! button because this could be clicked
# on by an anonymous user who hasn't purchased the course yet.
# Append the LearnCourse code (starts with LRN_) to the end
COURSE_PRODUCT_PAGE = "https://{}/local/catalog/view/product.php?globalid=".format(
    settings.LEARN_DOMAIN
)

APA_PROVIDER_CONTACT = Contact.objects.get(user__username='119523')


class Command(BaseCommand):
    help = """Activates LearnCourse records and associated Product/ProductPrices"""

    npc17 = apps.get_model('events', 'EventMulti').objects.get(
        publish_status="PUBLISHED",
        master_id=NPC17_EVENT_MULTI_MASTER_ID
    )

    npc18 = apps.get_model('events', 'EventMulti').objects.get(
        publish_status="PUBLISHED",
        master_id=NPC18_EVENT_MULTI_MASTER_ID
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '-m',
            '--landing-master-id',
            dest='master_id',
            nargs=1,
            type=int,
            help='Change all Events parent landing master to the page with this master_id'
        )
        parser.add_argument(
            '-i',
            '--limit',
            dest='limit',
            nargs=1,
            type=int,
            help='Limit the amount of events to re-publish (e.g., for testing small batches)'
        )

    def handle(self, *args, **options):
        # self.activate_learn_courses(**options)
        # self.add_digital_product_url_to_old_courses()
        # self.create_staff_product_price()
        # self.republish_active_events(**options)
        # self.reactivate_od()
        self.adjust_template()

    def activate_learn_courses(self, **options):
        for model_name in ('LearnCourse', 'LearnCourseBundle'):
            model = apps.get_model(app_label='learn', model_name=model_name)
            for course in model.objects.filter(
                publish_status="DRAFT",
                product__isnull=False
            ).exclude(
                status='X'
            ):
                course.status = 'A'
                # TODO: Need new master_id of Education and Events landing page
                # UPDATE:
                # staging: 9156635
                # prod: ???
                parent_landing_master = LandingPageMasterContent.objects.get(
                    id=options['master_id'][0]
                )
                course.parent_landing_master = parent_landing_master
                course.archive_time = ARCHIVE_TIME
                course.product.status = 'A'
                course.product.save()
                course.product.options.update(status='A')
                course.product.prices.update(
                    status='A',
                    begin_time=BEGIN_TIME,
                    end_time=END_TIME
                )
                course.save()
                course.publish()
                self.stdout.write(
                    self.style.SUCCESS(
                        "Activated {} {}: {}".format(model_name, course.master_id, course.title)
                    )
                )

    def republish_active_events(self, **options):
        parent_landing_master = LandingPageMasterContent.objects.get(
            id=options['master_id'][0]
        )
        # Get all "Active" events (end_time in the future)
        # excluding those that have already had their landing page changed
        # to avoid duplicating publishing if the script errors out before completing
        active_events = apps.get_model('events', 'event').objects.filter(
            event_type="LEARN_COURSE",
            publish_status="DRAFT",
            status='A',
            end_time__gte=datetime.now(tz=TZ)
        ).order_by(
            '-updated_time'
        )

        self.stdout.write(
            self.style.NOTICE(
                """
                Preparing to re-publish {} Event records.
                Get comfy, we're going to be here for a while...
                """.format(active_events.count())
            )
        )
        # end_idx = options['limit'][0]
        # for event in active_events[:end_idx]:
        for event in active_events:
            self.stdout.write(
                self.style.NOTICE(
                    "Re-publishing {} {}: {}".format(event.event_type, event.master_id, event.title)
                )
            )
            event.parent_landing_master = parent_landing_master
            event.save()
            event.solr_publish()
            try:
                event.content_ptr.publish()
            except:
                self.stdout.write(
                    self.style.WARNING(
                        "Error re-publishing {}: purchases exist".format(event)
                    )
                )
        self.stdout.write(
            self.style.SUCCESS(
                "Done!"
            )
        )

    def create_staff_product_price(self):
        """
        Creates a staff Product for prod APA Learn courses
        :return:
        """
        for model_name in ('LearnCourse', 'LearnCourseBundle'):
            model = apps.get_model(app_label='learn', model_name=model_name)
            for course in model.objects.filter(
                publish_status='DRAFT',
                product__isnull=False
            ).exclude(
                status='X'
            ):
                self.stdout.write(
                    self.style.NOTICE(
                        "Creating APA Staff Price for {}: {}".format(
                            course.product.code,
                            course.product.title
                        )
                    )
                )
                # try:
                #     course.product.prices.filter(title='APA Staff', price=0).delete()
                # except:
                #     self.stdout.write(
                #         self.style.WARNING(
                #             "Unable to delete existing APA Staff product price for {}".format(course)
                #         )
                #     )
                pp, created = ProductPrice.objects.get_or_create(
                    status='H',
                    product=course.product,
                    title="APA Staff",
                    price=0,
                    min_quantity=1,
                    max_quantity=1,
                    option_code="INDIVIDUAL",
                    include_search_results=False
                )
                if created:
                    pp.begin_time = TZ.localize(datetime(2018, 11, 13, 12))
                    pp.required_groups.clear()
                    pp.required_groups.add(Group.objects.get(name='staff'))
                    pp.save()
                    try:
                        course.publish()
                    except:
                        self.stdout.write(
                            self.style.WARNING(
                                "Unable to delete existing APA Staff product price for {}".format(course)
                            )
                        )

    def add_digital_product_url_to_old_courses(self):
        self.stdout.write(
            self.style.NOTICE(
                "Adding link to APA Learn Product Page for NPC sessions"
            )
        )

        self._add_npc17_url(self.npc17)
        self._add_npc18_url(self.npc18)
        self._add_od_url()
        self._add_nca_url()

    def _add_nca_url(self):
        for npc in [self.npc17, self.npc18]:
            for nca in apps.get_model(
                app_label='conference',
                model_name='NationalConferenceActivity'
            ).objects.filter(
                parent=npc.master
            ):
                lc = apps.get_model(
                    app_label='learn',
                    model_name='LearnCourse'
                ).objects.filter(
                    title__iexact=nca.title,
                    digital_product_url__isnull=False,
                )
                if lc.exists():
                    nca.digital_product_url = COURSE_PRODUCT_PAGE + lc.first().code
                    nca.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            "Set NationalConferenceActivity {} | {} URL to {}".format(
                                nca.master_id,
                                nca.title,
                                COURSE_PRODUCT_PAGE + lc.first().code
                            )
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            "No Learn Course found for {} | {}".format(
                                nca.master_id,
                                nca.title
                            )
                        )
                    )

    def _add_od_url(self):
        self.stdout.write(
            self.style.NOTICE(
                "Adding link to APA Learn Product Page for old On-Demand Courses"
            )
        )
        for course in Course.objects.filter(
                publish_status="PUBLISHED",
                product__product_type="STREAMING"
        ):
            lc = apps.get_model(app_label='learn', model_name='LearnCourse').objects.filter(
                code="LRN_{}".format(course.code)
            ).first()
            if lc is not None:
                course.digital_product_url = COURSE_PRODUCT_PAGE + lc.code
                course.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        "Set On-Demand Course {}: {} APA Learn Link to {}".format(
                            course.master_id, course.title, COURSE_PRODUCT_PAGE + lc.code
                        )
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "No corresponding APA Learn course found for {}: {}, "
                        "setting URL to {}".format(
                            course.master_id,
                            course.title,
                            COURSE_CATALOG_URL
                        )
                    )
                )
                course.digital_product_url = COURSE_CATALOG_URL
                course.save()

    def _add_npc18_url(self, npc18):
        # NPC18 codes are prepended with 'NPC' (unlinke NPC17)
        # have to adjust queries accordingly
        for npc18act in npc18.get_activities():
            npc18actcode = npc18act.code.split('NPC')
            try:
                code = npc18actcode[1]
            except IndexError:
                code = None
            if code is not None:
                lc = apps.get_model('learn', 'LearnCourse').objects.filter(
                    publish_status="PUBLISHED",
                    code="LRN_{}".format(code)
                ).first()
                if lc is not None:
                    npc18act.digital_product_url = COURSE_PRODUCT_PAGE + lc.code
                    npc18act.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            "Set NPC18 Activity {}: {} APA Learn link to {}".format(
                                npc18act.master_id, npc18act.title, COURSE_PRODUCT_PAGE + lc.code
                            )
                        )
                    )

                else:
                    self.stdout.write(
                        self.style.WARNING(
                            "No LearnCourse match found for NPC18 Activity {}: {}, "
                            "setting URL to {}".format(
                                npc18act.master_id,
                                npc18act.title,
                                COURSE_CATALOG_URL
                            )
                        )
                    )
                    npc18act.digital_product_url = COURSE_CATALOG_URL
                    npc18act.save()

    def _add_npc17_url(self, npc17):
        for npc17act in npc17.get_activities():
            lc = apps.get_model('learn', 'LearnCourse').objects.filter(
                publish_status="PUBLISHED",
                code="LRN_{}".format(npc17act.code)
            ).first()
            if lc is not None:
                npc17act.digital_product_url = COURSE_PRODUCT_PAGE + lc.code
                npc17act.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        "Set NPC17 Activity {}: {} APA Learn link to {}".format(
                            npc17act.master_id, npc17act.title, COURSE_PRODUCT_PAGE + lc.code
                        )
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "No LearnCourse match found for NPC17 Activity {}: {}, "
                        "setting URL to {}".format(
                            npc17act.master_id,
                            npc17act.title,
                            COURSE_CATALOG_URL
                        )
                    )
                )
                npc17act.digital_product_url = COURSE_CATALOG_URL
                npc17act.save()

    @staticmethod
    def _has_learn_course(course):
        lc = apps.get_model(app_label='learn', model_name='LearnCourse')
        if lc.objects.filter(code='LRN_{}'.format(course.code)).exists():
            return True
        npc18code = ''
        if course.code is not None:
            npc18code = course.code.split("NPC")
        if len(npc18code) > 1:
            return lc.objects.filter(code="LRN_{}".format(npc18code[1])).exists()
        if lc.objects.filter(title__icontains=course.title).exists():
            return True
        return False

    def reactivate_od(self):
        with open("/tmp/od_reactivate.csv", "w") as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=[
                    "master_id",
                    "course_status",
                    "course_publish_status",
                    "title",
                    "prod_url",
                    "product_status",
                    "product_type",
                    "end_time",
                    "has_apa_provider",
                    "has_zero_product_price",
                    "has_apa_learn_equivalent"
                ]
            )
            writer.writeheader()
            courses = Course.objects.filter(
                publish_status="PUBLISHED",
                status__in=('A', 'H'),
                product__status='I',
                product__product_type="STREAMING",
                end_time__isnull=False,
                end_time__gt=datetime.now(tz=pytz.timezone(settings.TIME_ZONE))
            ).order_by('master_id')
            for course in courses:
                data = dict()
                if course.contactrole.filter(
                    contact=APA_PROVIDER_CONTACT,
                    role_type="PROVIDER"
                ).exists():
                    if course.product.prices.filter(price=0).exists():
                        if not self._has_learn_course(course):
                            course.product.status = 'A'
                            course.product.save()
                            course.product.options.update(status='A')
                            course.product.prices.update(status='A', end_time=None)
                            data["master_id"] = course.master_id
                            data["course_status"] = course.status
                            data["course_publish_status"] = course.publish_status
                            data["title"] = course.title
                            data["prod_url"] = "https://planning.org/events/course/{}/".format(
                                course.master_id
                            )
                            data["product_status"] = course.product.status
                            data["product_type"] = course.product.product_type
                            data["end_time"] = course.end_time
                            data["has_apa_provider"] = "TRUE"
                            data["has_zero_product_price"] = "TRUE"
                            data["has_apa_learn_equivalent"] = "FALSE"
                            writer.writerow(data)
                            self.stdout.write(
                                self.style.WARNING(
                                    "Reactivating {} | {}".format(course.master_id, course.title)
                                )
                            )

    def adjust_template(self):
        """
        Yet another function to plug yet another hole in the leaky dam that is APA Learn
        (╯°□°）╯︵ ┻━┻
        :return:
        """

        npc15 = apps.get_model('events', 'EventMulti').objects.get(
            publish_status="PUBLISHED",
            master_id=3027311
        )
        npc15_titles = [i.title for i in npc15.get_activities()]
        npc15_titles.extend(["On Demand: {}".format(i) for i in npc15_titles])
        npc15_courses = Course.objects.filter(
            title__in=npc15_titles,
            product__product_type="STREAMING",
            publish_status="DRAFT"
        ).exclude(
            status='X'
        )
        for course in npc15_courses:
            if not self._has_learn_course(course):
                self.stdout.write(
                    self.style.NOTICE(
                        "Changing template for {} | {}".format(course.master_id, course.title)
                    )
                )
            course.product.status = 'I'
            course.product.save()
            course.product.options.update(status='I')
            course.product.prices.update(status='I')
            course.template = 'events/newtheme/ondemand/course-details.html'
            course.save()
            published_course = course.publish()
            published_course.solr_publish()

        npc16 = apps.get_model('events', 'EventMulti').objects.get(
            publish_status="PUBLISHED",
            code="EVENT_16CONF"
        )

        npc16_titles = [i.title for i in npc16.get_activities()]
        npc16_titles.extend(['On Demand: {}'.format(i) for i in npc16_titles])
        npc16_courses = Course.objects.filter(
            title__in=npc16_titles,
            product__product_type="STREAMING",
            publish_status="DRAFT"
        ).exclude(
            status='X'
        )

        for course in npc16_courses:
            if not self._has_learn_course(course):
                self.stdout.write(
                    self.style.NOTICE(
                        "Changing template for {} | {}".format(course.master_id, course.title)
                    )
                )
            course.product.status = 'I'
            course.product.save()
            course.product.options.update(status='I')
            course.product.prices.update(status='I')
            course.template = 'events/newtheme/ondemand/course-details.html'
            course.save()
            published_course = course.publish()
            published_course.solr_publish()

        npc17 = apps.get_model('events', 'EventMulti').objects.get(
            publish_status="PUBLISHED",
            master_id=NPC17_EVENT_MULTI_MASTER_ID
        )

        npc17_titles = [i.title for i in npc17.get_activities()]
        npc17_titles.extend(['On Demand: {}'.format(i) for i in npc17_titles])

        npc17_courses = Course.objects.filter(
            title__in=npc17_titles,
            product__product_type="STREAMING",
            publish_status="DRAFT",
        ).exclude(
            status='X'
        )

        for course in npc17_courses:
            if not self._has_learn_course(course):
                self.stdout.write(
                    self.style.NOTICE(
                        "Changing template for {} | {}".format(course.master_id, course.title)
                    )
                )

            course.product.status = 'I'
            course.product.save()
            course.product.options.update(status='I')
            course.product.prices.update(status='I')
            course.template = 'events/newtheme/ondemand/course-details.html'
            course.save()
            published_course = course.publish()
            published_course.solr_publish()

