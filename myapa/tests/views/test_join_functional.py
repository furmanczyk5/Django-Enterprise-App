#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import datetime
import os
import random
import time
from unittest import skip

from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.conf import settings
from django.test import LiveServerTestCase
from faker import Faker
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.ui import Select, WebDriverWait

from imis import models as imis_models
from myapa.models.contact import Contact


def country_state_form_initialized(driver):
    country = driver.find_element_by_id('id_country')
    if not country:
        print('cannot find country')
        return False
    country = Select(country)
    assert len(country.options) > 1


class JoinFunctionalTestCase(StaticLiveServerTestCase):

    fixtures = ["cities_light_country.json", "cities_light_region.json"]

    @classmethod
    def setUpClass(cls):
        super(JoinFunctionalTestCase, cls).setUpClass()
        cls.fake = Faker()

        # Since ZIP codes are what we use to automatically assign a state chapter to
        # U.S. members (by querying the Zip_Code table in iMIS), it would make sense
        # to have a zip code that matches the randomly-chosen state
        with open(os.path.join(
                settings.BASE_DIR, 'myapa/fixtures/imis_state_zip.csv'
        )) as state_zip_csv:
            reader = csv.reader(state_zip_csv)
            cls.state_zip = [x for x in reader]

        cls.browser = webdriver.Firefox()
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super(JoinFunctionalTestCase, cls).tearDownClass()

    def random_option_input(self, elem_id):
        """
        Select a <select> DOM element and randomly choose one of its <option>s
        :param elem_id: :class:`selenium.webdriver.remote.webelement.WebElement`
        :return: str
        """
        elem = Select(self.browser.find_element_by_id(elem_id))
        elem.select_by_index(random.choice(range(1, len(elem.options))))
        value = elem.first_selected_option.get_attribute('value')
        return value

    def text_input(self, elem_id, value):
        """
        Input value in to the given <input> element with elem_id
        :param elem_id: :class:`selenium.webdriver.remote.webelement.WebElement`
        :param value: str
        :return: str
        """
        elem = self.browser.find_element_by_id(elem_id)
        elem.send_keys(value)
        return value

    def test_join_account_view(self):
        self.browser.get("{}/join/account/".format(self.live_server_url))

        # wait for the selectchain.js injected <option> elements to be populated
        # in the country/state dropdowns
        WebDriverWait(
            driver=self.browser,
            timeout=5
        ).until(
            presence_of_element_located((By.CSS_SELECTOR, '#id_country > option:nth-child(254)'))
        )

        # Name
        first_name = self.text_input('id_first_name', self.fake.first_name())
        last_name = self.text_input('id_last_name', self.fake.last_name())

        # Date of Birth
        dob_year = self.random_option_input('id_birth_date_0')
        dob_month = self.random_option_input('id_birth_date_1')
        dob_day = self.random_option_input('id_birth_date_2')

        # Email
        email = self.text_input('id_email', self.fake.email())
        self.text_input('id_verify_email', email)

        # Password
        password = self.text_input('id_password', self.fake.password(random.randrange(8, 17)))
        self.password = password
        self.text_input('id_verify_password', password)
        self.random_option_input('id_password_hint')
        self.text_input('id_password_answer', self.fake.catch_phrase())

        # Phone
        # TODO: check if we have any business rules that depend on the type(s) of phones
        # iMIS has a 20-character limit on all phone columns
        # Can't use the Faker.fake method - will sometimes generate long phone numbers with extensions
        work_phone = self.text_input('id_secondary_phone', random.randrange(1000000000, 9999999999))

        # Address
        self.text_input('id_address1', self.fake.street_address())
        # flip a coin to enter a non-blank address_2
        if random.choice((True, False)):
            self.text_input('id_address2', self.fake.secondary_address())

        # Country
        # Forcing United States for now
        # TODO: Add a separate international test case
        country = Select(self.browser.find_element_by_id('id_country'))
        country.select_by_value("United States")

        WebDriverWait(
            driver=self.browser,
            timeout=5
        ).until(
            presence_of_element_located((By.CSS_SELECTOR, '#submission-state-select > option:nth-child(52)'))
        )

        # State
        state = self.random_option_input('submission-state-select')

        # City
        self.text_input('id_city', self.fake.city())

        # ZIP Code
        # see comment in setUpClass
        zip_code = self.browser.find_element_by_id('id_zip_code')
        zip_code_choices = [x for x in self.state_zip if x[0] == state]
        zip_code_value = random.choice([z[1] for z in zip_code_choices])
        zip_code.send_keys(zip_code_value)

        # clicky clicky
        self.browser.find_element_by_name('submit').click()

        # we so slow :(
        # actually no, making requests to Facebook is slow <sigh>
        # TODO: Only run on production for all them sweet hashtag social analytics big data insights
        time.sleep(10)

        name = imis_models.Name.objects.filter(
            first_name=first_name,
            last_name=last_name,
            # birth_date__date=datetime.date(int(dob_year), int(dob_month), int(dob_day)),
            email=email,
            work_phone=work_phone
        )
        self.assertEqual(name.count(), 1)
        self.name = name.first()
        print(self.name.id)

        user = User.objects.filter(username=self.name.id)
        self.assertEqual(user.count(), 1)

        # if the Name record got created, NameAddress and IndDemographics records
        # should have also been created with the same id
        # name_address = imis_models.NameAddress.objects.filter(id=self.name.id)
        #
        # self.assertEqual(name_address.count(), 1)
        # self.name_address = name_address.first()
        #
        # self.assertEqual(self.name_address.address_1, address_1)
        # self.assertEqual(self.name_address.address_2, address_2)
        # self.assertEqual(self.name_address.country, country)
        # self.assertEqual(self.name_address.state_province, state)
        # self.assertEqual(self.name_address.city, city)
        # self.assertEqual(self.name_address.zip, zip_code_value)
        #
        # ind_demographics = imis_models.IndDemographics.objects.filter(id=self.name.id)
        # self.assertEqual(ind_demographics.count(), 1)
        # self.ind_demographics = ind_demographics
        #
        # self.assertEqual(self.ind_demographics.hint_password, password_hint_question)
        # self.assertEqual(self.ind_demographics.hint_answer, password_hint_answer)
