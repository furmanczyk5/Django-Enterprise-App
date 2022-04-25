from django.test import Client
from django.urls import reverse
from unittest import skip

from imis.models import Name
from myapa.models.contact import Contact
from myapa.models.contact_relationship import ContactRelationship
from myapa.models.educational_degree import EducationalDegree
from myapa.tests.factories.contact import SchoolFactory, ContactFactoryIndividual
from planning.global_test_case import GlobalTestCase


class FreestudentsViewsTestCase(GlobalTestCase):

    @skip
    def test_delete_pending_freemember(self):
        """ School admin ability to delete unsubmitted student members"""

        client = Client()

        # create schools, admins, students, degrees, etc.
        school1 = SchoolFactory(company="School1")
        school2 = SchoolFactory(company="School2")
        school1_admin = ContactFactoryIndividual(first_name="ShoolAdmin", last_name="Test")
        school2_admin = ContactFactoryIndividual(first_name="ShoolAdmin", last_name="Test")
        student1 = ContactFactoryIndividual(first_name="PSTUuart", last_name="PTest", member_type="PSTU")
        student2 = ContactFactoryIndividual(first_name="STUuart", last_name="Test", member_type="STU")

        ContactRelationship.objects.create(source=school1, target=school1_admin, relationship_type='FSMA')
        ContactRelationship.objects.create(source=school2, target=school2_admin, relationship_type='FSMA')

        EducationalDegree.objects.create(contact=student1, school=school1, is_current=True)
        EducationalDegree.objects.create(contact=student2, school=school1, is_current=True)

        # - log in as school admin for different school
        client.force_login(user=school2_admin.user)

        request_headers = dict(HTTP_HOST="www.planning.org")

        # should not be able to delete student if admin for different school
        res1 = client.post(
            reverse(
                viewname="freestudents_admin_student_delete",
                kwargs=dict(
                    school_id=school2.user.username,
                    student_id=student1.user.username
                )
            ),
            **request_headers
        )
        res2 = client.post(
            reverse(
                viewname="freestudents_admin_student_delete",
                kwargs=dict(
                    school_id=school1.user.username,
                    student_id=student1.user.username
                )
            ),
            **request_headers
        )

        stu1_exists1 = Contact.objects.filter(id=student1.id).exists()

        # log in as school admin for correct student's school
        client.force_login(user=school1_admin.user)

        # should be able to delete PSTU student, but not STU student
        res3 = client.post(
            reverse(
                viewname="freestudents_admin_student_delete",
                kwargs=dict(
                    school_id=school1.user.username,
                    student_id=student1.user.username
                )
            ),
            **request_headers
        )
        res4 = client.post(
            reverse(
                viewname="freestudents_admin_student_delete",
                kwargs=dict(
                    school_id=school1.user.username,
                    student_id=student2.user.username
                )
            ),
            **request_headers
        )

        stu1_exists2 = Contact.objects.filter(id=student1.id).exists()
        stu2_exists = Contact.objects.filter(id=student2.id).exists()
        stu1_imis_dropped = Name.objects.filter(id=student1.user.username, status="D").exists()

        # must delete student from the correct student admin portal
        self.assertEqual(res1.status_code, 404)

        # cannot delete students if you are not an admin for that school
        self.assertEqual("access_denied_message" in res2.context, True)

        # pstu student should not have been deleted
        self.assertTrue(stu1_exists1)

        # school admins can delete pstu students (should be redirected back to dashboard afterwards)
        self.assertEqual(res3.status_code, 302)

        # school admins cannot delete stu students (they are already submitted)
        self.assertEqual(res4.status_code, 404)

        # pstu student should no longer exist
        self.assertFalse(stu1_exists2)

        # stu student should still exist
        self.assertTrue(stu2_exists)

        # deleted pstu student should have status "D" in imis
        self.assertTrue(stu1_imis_dropped)
