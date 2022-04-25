import random

import factory

from myapa.models.educational_degree import EducationalDegree
from myapa.tests.factories.contact import ContactFactoryIndividual, SchoolFactory
from myapa.models.constants import DEGREE_LEVELS

TOP_20_DEGREE_PROGRAMS = (
    '', 'Planning', 'Urban and Regional Planning', 'City and Regional Planning',
    'Public Administration', 'Urban Studies', 'Geography', 'Urban Planning',
    'Environmental Science', 'Architecture', 'Engineering', 'Master of Urban and Regional Planning',
    'Master of Urban Planning', 'Political Science', 'City Planning', 'Landscape Architecture',
    'Master of City and Regional Planning', 'Community and Regional Planning',
    'Urban Planning and Development', 'Regional Planning'
)


class EducationalDegreeFactory(factory.DjangoModelFactory):

    contact = factory.SubFactory(ContactFactoryIndividual)
    school = factory.SubFactory(SchoolFactory)
    school_seqn = factory.Sequence(lambda n: str(n + 100000))
    seqn = factory.Sequence(lambda n: str(n + 100000))
    graduation_date = factory.Faker('date_this_century')
    level = random.choice([x[0] for x in DEGREE_LEVELS])
    is_planning = random.choice((True, False))
    complete = random.choice((True, False))
    is_current = random.choice((True, False))
    program = random.choice(TOP_20_DEGREE_PROGRAMS)

    class Meta:
        model = EducationalDegree

