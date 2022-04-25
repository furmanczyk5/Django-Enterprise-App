from myapa.tests.factories.educational_degree import EducationalDegreeFactory
from planning.global_test_case import GlobalTestCase


class EducationalDegreeTestCase(GlobalTestCase):

    def test_write_to_imis(self):
        ed = EducationalDegreeFactory(
            other_school='DJANGO_TEST_FACTORY'
        )
        imis_degree = ed.write_to_imis()

        self.assertEqual(ed.contact.user.username, imis_degree.id)
        self.assertEqual(ed.school.user.username, imis_degree.school_id)
        self.assertEqual(ed.school_seqn, imis_degree.school_seqn)
        self.assertEqual(ed.level, imis_degree.degree_level)
        self.assertEqual(ed.program, imis_degree.degree_program)

        # FIXME: There seems to be some stored procedure in iMIS
        # that rounds any date passed to this degree_date field
        # down to the first of its month
        # e.g., datetime.date(2010, 11, 25) will get stored in iMIS as
        # datetime.datetime(2010, 11, 1)
        # self.assertEqual(ed.graduation_date, imis_degree.degree_date)
        self.assertEqual(ed.graduation_date.year, imis_degree.degree_date.year)
        self.assertEqual(ed.graduation_date.month, imis_degree.degree_date.month)

        self.assertEqual(ed.is_planning, imis_degree.degree_planning)
        self.assertEqual(ed.complete, imis_degree.degree_complete)
        self.assertEqual(ed.student_id, imis_degree.school_student_id),
        self.assertEqual(ed.is_current, imis_degree.is_current)
