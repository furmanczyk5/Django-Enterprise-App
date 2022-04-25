from myapa.forms.account import CreateAccountForm
from planning.global_test_case import GlobalTestCase


class CreateAccountFormTestCase(GlobalTestCase):

    @classmethod
    def setUpTestData(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        return super().tearDownClass()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_form_renders_email_input(self):
        form = CreateAccountForm()
        self.fail(form.as_p())
