from planning.global_test_case import GlobalTestCase
from myapa.forms.account import AddressesFormMixin
from imis.forms.name_address import NameAddressForm


class MyOrgAddressesFormTest(GlobalTestCase):

    @classmethod
    def setUpTestData(cls):
        super(MyOrgAddressesFormTest, cls).setUpTestData()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_form_renders_address_text_input(self):
        form = NameAddressForm()
        # self.fail(form.as_p())
