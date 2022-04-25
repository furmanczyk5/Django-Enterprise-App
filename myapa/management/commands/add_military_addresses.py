from django.core.management.base import BaseCommand

from cities_light.models import Country, Region


class Command(BaseCommand):

    def handle(self, *args, **options):

        # TODO: Delete existing first?

        # NOTE: Some existing views have to be dropped before migrations can be run
        # Specifically,
        """
        apa=# drop view v_reporting_aicp_candidate ;
        DROP VIEW
        apa=# drop view v_contactrole cascade ;
        NOTICE:  drop cascades to view v_comment
        DROP VIEW
        apa=# drop view v_contact ;
        DROP VIEW
        apa=# drop view v_cm_provider_registrations ;
        DROP VIEW
        apa=# drop view v_awards_2018_submission_reviews ;
        DROP VIEW
        apa=# drop view v_bookstore_product_details ;
        DROP VIEW
        apa=# drop view v_awards_submission_reviews ;

        """
        # They can be re-added after migrations successfully run (see the planning-sql repo)

        # Create a "United States Military" country entry in cities_light
        mil, _ = Country.objects.update_or_create(
            name='United States Military',
            name_ascii='United States Military'
        )

        # Create state entries
        for state in ('AA', 'AE', 'AP'):
            Region.objects.update_or_create(
                name=state,
                name_ascii=state,
                display_name=state,
                geoname_code=state,
                country=mil
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Successfully loaded in United States Military countries and states to their  "
                "respective cities_light tables"
            )
        )
