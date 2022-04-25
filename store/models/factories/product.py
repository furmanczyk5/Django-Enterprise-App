import factory

from content.models.settings import PublishStatus, ContentStatus
from content.tests.factories.content import ContentProductFactory
from store.models.product import Product
from store.models.product_cart import ProductCart
from store.models.settings import ProductTypes, ProductCode


class ProductFactory(factory.DjangoModelFactory):

    content = factory.SubFactory(ContentProductFactory)
    product_type = ''
    gl_account = ''
    status = ContentStatus.ACTIVE.value
    publish_status = PublishStatus.PUBLISHED.value

    class Meta:
        model = Product


class ProductCartFactory(ProductFactory):

    class Meta:
        model = ProductCart


class CMProviderRegistrationContentFactory(ContentProductFactory):
    code = "CM_PROVIDER_REGISTRATION"
    description = "CM Course Registration"
    og_description = "CM Course Registration"
    og_type = "article"
    title = "CM Annual Registration"


class CMProviderRegistrationProductFactory(ProductFactory):

    content = factory.SubFactory(CMProviderRegistrationContentFactory)
    code = "CM_PROVIDER_REGISTRATION"
    product_type = ProductTypes.CM_REGISTRATION.value
    confirmation_text = '<p>Thank you for your participation in the CM Program. '\
                        '<a href="https://www.planning.org/myorg">Please '\
                        'click here to return to your CM Provider Dashboard.</a></p>'
    gl_account = '450500-AD6400'
    imis_code = 'CM_REG'


class CMPerCreditContentFactory(ContentProductFactory):
    code = "CONTENT_CM_PER_CREDIT_FEE"
    title = "CM Per-Credit Fee"
    description = "CM Per-Credit Fee"
    og_description = "CM Per-Credit Fee"
    og_title = "CM Per-Credit Fee"
    og_type = "article"


class CMPerCreditProductFactory(ProductFactory):

    content = factory.SubFactory(CMPerCreditContentFactory)
    code = "PRODUCT_CM_PER_CREDIT"
    product_type = ProductTypes.CM_PER_CREDIT.value
    confirmation_text = """<p>Thank you for your participation in the CM Program. <a href="https://www.planning.org/myorg">Please click here to return to your CM Provider Dashboard.</a></p>"""
    gl_account = "450500-AD6400"
    imis_code = "CM_FEE"


class MembershipContentProductFactory(ContentProductFactory):

    code = "MEMBERSHIP_MEM"
    title = "APA Professional Membership"
    og_title = title
    description = title
    og_description = title


class MembershipProductFactory(ProductCartFactory):

    content = factory.SubFactory(MembershipContentProductFactory)
    code = "MEMBERSHIP_MEM"
    product_type = ProductTypes.DUES.value
    gl_account = "410100-IM4010"
    imis_code = "APA"


class ChapterContentProductFactory(ContentProductFactory):

    code = "CHAPT_TEST"
    title = "Test Chapter"
    og_title = title
    description = title
    og_description = title


class ChapterProductFactory(ProductCartFactory):

    content = factory.SubFactory(ChapterContentProductFactory)
    code = "CHAPT_TEST"
    product_type = ProductTypes.CHAPTER.value
    gl_account = '200953-000000'
    imis_code = "CHAPT/TEST"


class DivisionContentProductFactory(ContentProductFactory):

    code = "DIVISION_TEST"
    title = "Test Division"
    og_title = title
    description = title
    og_description = title


class DivisionProductFactory(ProductCartFactory):

    content = factory.SubFactory(DivisionContentProductFactory)
    code = "DIVISION_TEST"
    product_type = ProductTypes.DIVISION.value
    gl_account = '410120-MD6106'
    imis_code = "DIVISION_TEST"


class AICPMembershipContentProductFactory(ContentProductFactory):

    title = "AICP Membership"
    code = ProductCode.MEMBERSHIP_AICP
    og_title = title
    description = title
    og_description = title


class AICPMembershipProductFactory(ProductCartFactory):

    content = factory.SubFactory(AICPMembershipContentProductFactory)
    code = ProductCode.MEMBERSHIP_AICP
    product_type = ProductTypes.DUES.value
    gl_account = '410100-IA6200'
    imis_code = "AICP"
