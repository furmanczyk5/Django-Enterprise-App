import time

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from content.tests.factories.menu_item import MenuItemFactory
from myapa.tests.factories.contact import AdminUserFactory

MAX_WAIT = 20  # seconds to wait for a page to load


def wait(fn):
    """
    A Selenium retry loop decorator. Decorate any method you want
    to retry within MAX_WAIT seconds with

    @wait
    def my_retry_loop_function():
        pass

    :param fn: function
    :return: function
    """
    def modified_fn(*args, **kwargs):
        start_time = time.time()
        while True:
            try:
                return fn(*args, **kwargs)
            except (AssertionError, WebDriverException) as e:
                if time.time() - start_time > MAX_WAIT:
                    raise e
                time.sleep(0.5)

    return modified_fn


class FunctionalTest(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.administrator = AdminUserFactory()
        cls.menu_item = MenuItemFactory(
            created_by=cls.administrator,
            updated_by=cls.administrator
        )

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()
