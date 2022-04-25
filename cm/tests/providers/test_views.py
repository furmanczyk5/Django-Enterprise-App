import datetime
from unittest import skip

import pytz
from django.core import mail
from django.test import Client
from django.urls import reverse

from cm.models import ProviderApplication
from content.models import MenuItem, EmailTemplate
from imis.enums.relationship_types import ImisRelationshipTypes
from imis.tests.factories.relationship import RelationshipFactory
from myapa.functional_tests.utils import build_imis_org_and_admin
from myapa.models.contact import Contact
from myapa.tests.factories.contact import ContactFactoryIndividual
from pages.models import Page
from planning.global_test_case import GlobalTestCase


class ProvidersViewTestCase(GlobalTestCase):

    @classmethod
    def setUpTestData(cls):

        super(ProvidersViewTestCase, cls).setUpTestData()

        # Bypassing save method to create with specified updated time 
        created_time = pytz.utc.localize(datetime.datetime.strptime("1900-01-01", "%Y-%m-%d"), is_dst=None)

        # assuming org, org_admin, and relationship record have already been created
        cls.org, cls.org_admin = build_imis_org_and_admin()
        cls.org.save()
        cls.org_admin.save()
        cls.rel_imis = RelationshipFactory(
            id=cls.org_admin.id,
            relation_type=ImisRelationshipTypes.ADMIN_I.value,
            target_id=cls.org.id,
            target_relation_type=ImisRelationshipTypes.ADMIN_C.value,
        )
        cls.rel_imis.save()

        cls.non_provider_user = ContactFactoryIndividual()

        Page.objects.bulk_create([
            Page(title="CM Log", status="A", publish_status="PUBLISHED",
                created_time=created_time, created_by=cls.administrator,
                updated_time=created_time, updated_by=cls.administrator,
                url=reverse("cm:log"))])

        MenuItem.objects.bulk_create([
            MenuItem(publish_status="PUBLISHED", status="A", 
                created_time=created_time, created_by=cls.administrator,
                updated_time=created_time, updated_by=cls.administrator),
            MenuItem(publish_status="PUBLISHED", status="A", 
                created_time=created_time, created_by=cls.administrator,
                updated_time=created_time, updated_by=cls.administrator)])

        # create email template for sending provider confirmation emails
        EmailTemplate.objects.get_or_create(code="PROVIDER_APPLICATION_SUCCESSFUL_SUBMIT", defaults=dict(
            subject="TEST Successfully Submitted Application",
            body="TEST body text",
            email_from="customerservice@planning.org"))

    def setUp(self):
        self.client = Client()

    def tearDown(self):
        self.client.logout()

    @skip
    def test_provider_application_submission(self):

        org = Contact.update_or_create_from_imis(self.org.id)
        admin = Contact.update_or_create_from_imis(self.org_admin.id)

        # non_provider_admin = ContactFactoryIndividual(first_name="TestNotProviderFirst", last_name="TestNotProviderLast")
        # provider_admin = ContactFactoryIndividual(first_name="TestFirst", last_name="TestLast")
        # provider = ContactFactoryOrganization(
        #     company="TestOrganization"
        # )
        #
        # ContactRelationship.objects.create(
        #     relationship_type="ADMINISTRATOR",
        #     source=provider,
        #     target=provider_admin
        # )

        # CREATE VIEW #######################
        new_url = reverse("cm:provider_application_new")

        EXPLAIN = "Testing explaing topics"
        OBJ1 = "Testing objective 1"
        OBJ2 = "Testing objective 2"
        OBJ3 = "Testing objective 3"
        SPEAKERS = "Testing how determines speakers"
        PROCEDURE = "Testing evaluation procedures"
        EVALUATES = True
        AGREE = False
        OBJ_STATUS = "SOMETIMES"

        provider_application_data = dict(
            submit="continue_later",
            explain_topics=EXPLAIN,
            objectives_example_1=OBJ1,
            how_determines_speakers=SPEAKERS,
            objectives_status=OBJ_STATUS)

        self.client.force_login(user=self.non_provider_user.user)
        request_headers = dict(HTTP_HOST="www.planning.org")

        # test access to creating new application
        res1 = self.client.get(new_url, **request_headers)
        self.assertEqual("access_denied_message" in res1.context, True) # cannot create application if not admin for a provider

        self.client.force_login(user=admin.user)
        res2 = self.client.post(new_url, provider_application_data, **request_headers)

        self.assertEqual(res2.status_code, 302)

        # query for new application
        provider_application = ProviderApplication.objects.filter(provider=org).first()
        self.assertIsNotNone(provider_application)
        self.assertEqual(provider_application.status, "I") # test status of application is incomplete
        self.assertIsNone(provider_application.review_status) # test that there is no review status status (only for periodic review applications)
        self.assertEqual(provider_application.explain_topics, EXPLAIN)
        self.assertEqual(provider_application.objectives_example_1, OBJ1)
        self.assertEqual(provider_application.how_determines_speakers, SPEAKERS)
        self.assertEqual(provider_application.objectives_status, OBJ_STATUS)
        

        # EDIT VIEW #######################
        edit_url = reverse("cm:provider_application_edit", kwargs=dict(application_id=provider_application.id))

        # test editing provider application
        provider_application_data.update(dict(
            submit="continue",
            objectives_example_2=OBJ2,
            objectives_example_3=OBJ3,
        ))

        res3 = self.client.post(edit_url, provider_application_data, **request_headers)

        self.assertEqual(res3.status_code, 200)
       
        res4 = self.client.post(edit_url, provider_application_data, **request_headers)

        self.assertEqual(res4.status_code, 302)

        # query for edited application
        provider_application = ProviderApplication.objects.filter(provider=org, id=provider_application.id).first()
        self.assertIsNotNone(provider_application)
        self.assertEqual(provider_application.status, "I") # test status of application is incomplete
        self.assertIsNone(provider_application.review_status) # test that there is no review status status (only for periodic review applications)
        self.assertEqual(provider_application.explain_topics, EXPLAIN)
        self.assertEqual(provider_application.objectives_example_1, OBJ1)
        self.assertEqual(provider_application.objectives_example_2, OBJ2)
        self.assertEqual(provider_application.objectives_example_3, OBJ3)
        self.assertEqual(provider_application.how_determines_speakers, SPEAKERS)
        self.assertEqual(provider_application.objectives_status, OBJ_STATUS)

        # REVIEW VIEW #######################
        review_url = reverse("cm:provider_application_review", kwargs=dict(application_id=provider_application.id))
        
        res5 = self.client.post(review_url, dict(agree=True), **request_headers)

        self.assertEqual(res5.status_code, 302)

        # requery for submitted application
        provider_application = ProviderApplication.objects.filter(provider=org, id=provider_application.id).first()
        self.assertEqual(provider_application.status, "S") # test status of application is incomplete
        self.assertIsNone(provider_application.review_status) # test that there is no review status status (only for periodic review applications)

        # Test that one message has been sent, and that subject is correct
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, EmailTemplate.objects.filter(code="PROVIDER_APPLICATION_SUCCESSFUL_SUBMIT").only("subject").first().subject)

