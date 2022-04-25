from unittest import mock

from planning.global_test_case import GlobalTestCase
from ..forms import AttendeeBadgeForm, AttendeeBadgeShippingForm


class AttendeeBadgeFormTest(GlobalTestCase):
    def test_form(self):
        fields = {
            'badge_name': 'Bob',
            'badge_company': 'Acme',
            'badge_location': 'Phoenix, AZ'
        }
        form = AttendeeBadgeForm(fields, user=self.administrator)

        self.assertTrue(form.is_bound)
        self.assertEqual(form.errors, {})
        self.assertTrue(form.is_valid())
        self.assertHTMLEqual(form.errors.as_ul(), '')
        self.assertEqual(form.errors.as_text(), '')
        self.assertEqual(form.cleaned_data['badge_name'], 'Bob')
        self.assertEqual(form.cleaned_data['badge_company'], 'Acme')
        self.assertEqual(form.cleaned_data['badge_location'], 'Phoenix, AZ')
        self.assertHTMLEqual(
            str(form['badge_name']),
            '<input class=" form-control" id="id_badge_name" name="badge_name" required type="text" value="Bob" />'
        )
        self.assertHTMLEqual(
            str(form['badge_company']),
            '<input class=" form-control" id="id_badge_company" name="badge_company" type="text" value="Acme" />'
        )
        self.assertHTMLEqual(
            str(form['badge_location']),
            '<input class=" form-control" id="id_badge_location" name="badge_location" required type="text" value="Phoenix, AZ" />'
        )

        form_ouput = []

        for boundfield in form:
            form_ouput.append([boundfield.label, boundfield.data])

        self.assertEqual(form_ouput, [
            ['First Name Only', 'Bob'],
            ['Organization', 'Acme'],
            ['Location (City, State)', 'Phoenix, AZ']
        ])

    def test_errors_for_empty_input(self):
        form = AttendeeBadgeForm({})
        self.assertEqual(form.errors['badge_name'], ['This field is required.'])
        self.assertEqual(form.errors['badge_location'], ['This field is required.'])
        self.assertFalse('badge_company' in form.errors.keys())

    def test_errors_for_field_length(self):
        form = AttendeeBadgeForm({
            'badge_name': 'Kevin the All Powerful',
            'badge_company': 'The Greater Incorporated Metropolitan Acme Corporation of Acmeburg Proper, a wholly-owned subsidiary of Standard Widgets and Fixtures, a Delaware Corporation',
            'badge_location': 'City of Acmeburg Incorporated, State of Acme in Hills and the Lakes'
        })
        self.assertEqual(
            form.errors['badge_name'],
            ['Ensure this value has at most 14 characters (it has 22).']
        )
        self.assertEqual(
            form.errors['badge_company'],
            ['Ensure this value has at most 80 characters (it has 157).']
        )
        self.assertEqual(
            form.errors['badge_location'],
            ['Ensure this value has at most 60 characters (it has 67).']
        )


class AttendeeBadgeShippingFormTest(GlobalTestCase):
    @mock.patch('content.forms.get_selectable_options_tuple_list')
    def test_form(self, mock_choices):
        self.max_diff=None
        state_choices = [
            ('New Mexico', 'NM'),
            ('Arizona', 'AZ')
        ]
        country_choices = [
            ('United States', 'United States'),
            ('Germany', 'Germany')
        ]
        mock_choices.side_effect = [
            state_choices,
            country_choices
        ]
        form = AttendeeBadgeShippingForm({
            'badge_name': 'Bob',
            'badge_company': 'Acme',
            'badge_location': 'Phoenix, AZ',
            'address1': '123 Lane',
            'address2': None,
            'city': 'Phoenix',
            'state': 'Arizona',
            'country': 'United States',
            'zip_code': '54321'
        })

        self.assertTrue(form.is_bound)
        self.assertEqual(form.errors, {})
        self.assertTrue(form.is_valid())
        self.assertHTMLEqual(form.errors.as_ul(), '')
        self.assertEqual(form.errors.as_text(), '')
        self.assertEqual(form.cleaned_data['badge_name'], 'Bob')
        self.assertEqual(form.cleaned_data['badge_company'], 'Acme')
        self.assertEqual(form.cleaned_data['badge_location'], 'Phoenix, AZ')
        self.assertEqual(form.cleaned_data['address1'], '123 Lane')
        self.assertEqual(form.cleaned_data['address2'], '')
        self.assertEqual(form.cleaned_data['city'], 'Phoenix')
        self.assertEqual(form.cleaned_data['state'], 'Arizona')
        self.assertEqual(form.cleaned_data['country'], 'United States')
        self.assertEqual(form.cleaned_data['zip_code'], '54321')
        self.assertHTMLEqual(
            str(form['badge_name']),
            '<input class=" form-control" id="id_badge_name" name="badge_name" required type="text" value="Bob" />'
        )
        self.assertHTMLEqual(
            str(form['badge_company']),
            '<input class=" form-control" id="id_badge_company" name="badge_company" type="text" value="Acme" />'
        )
        self.assertHTMLEqual(
            str(form['badge_location']),
            '<input class=" form-control" id="id_badge_location" name="badge_location" required type="text" value="Phoenix, AZ" />'
        )
        self.assertHTMLEqual(
            str(form['address1']),
            '<input class=" form-control" id="id_address1" name="address1" required type="text" value="123 Lane" />'
        )
        self.assertHTMLEqual(
            str(form['address2']),
            '<input class=" form-control" id="id_address2" name="address2" type="text" />'
        )
        self.assertHTMLEqual(
            str(form['city']),
            '<input class=" form-control" id="id_city" name="city" required type="text" value="Phoenix" />'
        )
        self.assertHTMLEqual(
            str(form['zip_code']),
            '<input class=" form-control" id="id_zip_code" name="zip_code" required type="text" value="54321" />'
        )

        form_ouput = []

        for boundfield in form:
            form_ouput.append([boundfield.label, boundfield.data])

        self.assertEqual(form_ouput, [
            ['First Name Only', 'Bob'],
            ['Organization', 'Acme'],
            ['Location (City, State)', 'Phoenix, AZ'],
            ['Address 1', '123 Lane'],
            ['Address 2', None],
            ['City', 'Phoenix'],
            ['State', 'Arizona'],
            ['Country', 'United States'],
            ['Zip/Postal Code', '54321']
        ])

    def test_errors_for_empty_input(self):
        form = AttendeeBadgeShippingForm({})
        self.assertEqual(form.errors['address1'], ['This field is required.'])
        self.assertEqual(form.errors['city'], ['This field is required.'])
        self.assertEqual(form.errors['country'], ['This field is required.'])
        self.assertEqual(form.errors['zip_code'], ['This field is required.'])
        self.assertFalse('address2' in form.errors.keys())

    @mock.patch('content.forms.get_selectable_options_tuple_list')
    def test_truncates_long_state_province_input(self, mock_choices):
        self.max_diff=None
        state_choices = [
            ('British Columbia', 'British Columbia'),
            ('Arizona', 'AZ')
        ]
        country_choices = [
            ('United States', 'United States'),
            ('Germany', 'Germany')
        ]
        mock_choices.side_effect = [
            state_choices,
            country_choices
        ]
        form = AttendeeBadgeShippingForm({'state': 'British Columbia'})
        form.is_valid()
        self.assertEqual(form.cleaned_data['state'], 'British Columbi')

    @mock.patch('content.forms.get_selectable_options_tuple_list')
    def test_truncates_long_state_province_input(self, mock_choices):
        self.max_diff=None
        state_choices = [
            ('New Mexico', 'NM'),
            ('Arizona', 'AZ')
        ]
        country_choices = [
            ('South Georgia and the South Sandwich Islands', 'South Georgia and the South Sandwich Islands'),
            ('Germany', 'Germany')
        ]
        mock_choices.side_effect = [
            state_choices,
            country_choices
        ]
        form = AttendeeBadgeShippingForm({'country': 'South Georgia and the South Sandwich Islands'})
        form.is_valid()
        self.assertEqual(form.cleaned_data['country'], 'South Georgia and the Sou')
