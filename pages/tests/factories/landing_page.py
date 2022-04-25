import factory

from myapa.tests.factories.contact import AdminUserFactory
from pages.models import LandingPage, LandingPageMasterContent


YEAR = 2019


class LandingPageFactory(factory.DjangoModelFactory):

    created_by = factory.SubFactory(AdminUserFactory)
    updated_by = factory.SubFactory(AdminUserFactory)

    class Meta:
        model = LandingPage


class LandingPageFactoryNPC(LandingPageFactory):

    code = "CONFERENCE_HOME"
    content_area = "CONFERENCES"
    created_by = factory.SubFactory(AdminUserFactory)
    description = "Come to APA's {} National Planning Conference and see what's ahead for you, your community, and your career.".format(YEAR)
    keywords = 'american planning association conference\r\napa conference\r\napa national conference',
    og_description = description
    og_type = 'article'
    og_url = 'https://planning.org/conference'
    status = 'A'
    template = "conference/newtheme/home.html"
    title = "National Planning Conference"
    og_title = title
    updated_by = factory.SubFactory(AdminUserFactory)
    url = "/conference/"


class LandingPageMasterContentFactory(factory.DjangoModelFactory):

    class Meta:
        model = LandingPageMasterContent
