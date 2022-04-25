import json
import os

from django.conf import settings
from django.db import connections
from django.test import TestCase

from cm.models.claims import Period
from content.models.message_text import MessageText
from content.models.tagging import TagType
from content.tests.factories.menu_item import MenuItemFactory
from imis import models as imis_models
from myapa.tests.factories import contact as contact_factory


class GlobalTestCase(TestCase):
    """
    I had to dump these fixtures with natural keys, i.e.
    python manage.py dumpdata --natural-foreign --natural-primary --indent 2 -o out.json
    auth.Group, auth.Permission, contenttypes

    https://docs.djangoproject.com/en/1.11/topics/serialization/#natural-keys
    https://docs.djangoproject.com/en/1.11/ref/django-admin/#django-admin-dumpdata
    https://stackoverflow.com/questions/853796/problems-with-contenttypes-when-loading-a-fixture-in-django/40558318
    """

    # Ordering matters for the first three! 1. contenttypes 2. permissions 3. groups
    fixtures = [
        "contenttypes.json",
        "permissions.json",
        "groups.json",
        "sites.json"
    ]

    @classmethod
    def setUpTestData(cls):
        """
        Most of these are necessary because certain views/forms/models have
        hardcoded queries/attributes/etc. for these things, essentially assuming
        they are always present in the database in the state they existed at
        whenever time that code was written. When running tests on a fresh
        database, they obviously don't exist and throw errors all over the place that
        prevent tests from running properly in the first place. Examples:


        - A user called "Administrator" that is the default created/updated by (
        - At least one MenuItem
        - a JOB_CATEGORY TagType
        - MessageTexts with certain codes
        - cm.models.claim.Period:
          - assumes record with a code of "CAND"
        - :meth:`events.models.Event.save`:
          - assigns a hardcoded master id of a LandingPage as its parent_landing_master_id
          - Job model does the same thing
        - UploadType with code "PROFILE_PHOTOS"
          - :class:`myapa.forms.account.ImageUploadForm`

        Good candidates for reveiwing our assumptions and possibly refactoring,
        e.g. - could some of these be objects instead of DB records?
        :return: None
        """
        cls.administrator = contact_factory.AdminUserFactory()
        cls.tt, _ = TagType.objects.get_or_create(code="JOB_CATEGORY")
        cls.menu_item = MenuItemFactory(
            created_by=cls.administrator,
            updated_by=cls.administrator
        )
        cls.mastertopic_tt, _ = TagType.objects.get_or_create(code="TAXO_MASTERTOPIC", title="Taxonomy Master Topics")

        # Don't load things in setUpTestData if you're going to change them
        # later in the tests themselves
        Period.objects.get_or_create(code='CAND')

        # Can't load these in as fixtures until after an administrator user is created
        # (for the created/updated by fields)
        with open(os.path.join(
                settings.BASE_DIR, 'myapa/fixtures/message_texts.json'
        )) as message_text_fixture:
            message_texts = json.load(message_text_fixture)
        for message_text in message_texts:
            MessageText.objects.update_or_create(**message_text['fields'])

    @classmethod
    def tearDownClass(cls):
        """
        Delete test data created in iMIS because we can't create and destroy
        a separate SQL Server database, so we have to use the existing dev database

        Needless to say, be mindful about changing these values, they get
        set by the factory classes in :mod:`imis.tests.factories`
        """
        imis_models.CustomDegree.objects.filter(school_other="DJANGO_TEST_FACTORY").delete()
        imis_models.Name.objects.filter(updated_by='DJANGO_TEST_FACTORY').delete()
        imis_models.NameAddress.objects.filter(mail_code='DTEST').delete()
        imis_models.IndDemographics.objects.filter(hint_answer='DJANGO_TEST_FACTORY').delete()
        imis_models.Subscriptions.objects.filter(updated_by='DJANGO_TEST_FACTORY').delete()
        imis_models.Relationship.objects.filter(updated_by='DJANGO_TEST_FACTORY').delete()
        imis_models.Activity.objects.filter(source_code="DJANGO_TEST_FACTORY").delete()
        imis_models.NamePicture.objects.filter(updated_by="DJANGO_TEST_FACTORY").delete()
        imis_models.OrgDemographics.objects.filter(parent_id="DJANGO_TE").delete()
        imis_models.Orders.objects.filter(updated_by='DJANGO_TEST_FACTORY').delete()
        imis_models.OrderLines.objects.filter(note='DJANGO_TEST_FACTORY').delete()
        imis_models.Product.objects.filter(intent_to_edit='DJANGO_TEST_FACTORY').delete()

        # Due to a variety of mostly silly reasons (certainly too silly to enumerate here),
        # we have to use raw SQL in cursors for some iMIS tables
        with connections['MSSQL'].cursor() as cursor:
            cursor.execute(
                "DELETE FROM Name_Security_Groups WHERE SECURITY_GROUP = 'DJANGO_TEST_FACTORY'"
            )
            # This is painfully slow - Name_Log has tens of millions of records
            # and no index on USER_ID.
            # Disabling it until something affecting Name_Log becomes something we need to test
            # cursor.execute(
            #     "DELETE FROM Name_Log WHERE USER_ID = 'DJANGO_TEST_FACTORY'"
            # )

        super(GlobalTestCase, cls).tearDownClass()
