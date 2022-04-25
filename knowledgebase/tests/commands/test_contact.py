from unittest import TestCase, skip

from knowledgebase.management.commands.csv_transforms.contact import *


class AddContactTest(TestCase):
    def test_adds_contact_if_row_has_author(self):
        row = add_contact({'Author': 'Billy'})
        self.assertIn('contact', row.keys())

    def test_does_not_add_contact_if_row_has_no_author(self):
        row = add_contact({'Author': ' '})
        self.assertNotIn('contact', row.keys())


class TransformContactTest(TestCase):
    def test_creates_orgnization_contact(self):
        company = 'ASPO Committee Report'
        contact = transform_contact(company)
        expected = {
            'company': 'ASPO Committee Report',
            'contact_type': 'ORGANIZATION'
        }

        self.assertDictEqual(contact, expected)

    @skip
    def test_creates_individual_contact(self):
        """Something funky going on with this one..."""
        contact = transform_contact('Ross,Bob')
        expected = {
            'first_name': 'Bob',
            'last_name': 'Ross',
            'contact_type': 'INDIVIDUAL'
        }
        self.assertDictEqual(contact, expected)


class CleanNameTest(TestCase):
    def test_removes_extraneous_spaces(self):
        name = clean_name(" Smith , Mr. K.  T .  ")
        self.assertEqual(name, "Smith,Mr. K. T.")


class HandleFirstNameTest(TestCase):
    def test_adds_single_name_as_first_name(self):
        contact = handle_first_name('Mary', {})
        self.assertEqual('Mary', contact['first_name'])
        self.assertNotIn('prefix_name', contact.keys())
        self.assertNotIn('middle_name', contact.keys())

        contact = handle_first_name('Miss', {})
        self.assertEqual('Miss', contact['first_name'])
        self.assertNotIn('prefix_name', contact.keys())
        self.assertNotIn('middle_name', contact.keys())

    def test_adds_prefix_and_first_name(self):
        contact = handle_first_name('Miss Daisy', {})
        self.assertEqual('Miss', contact['prefix_name'])
        self.assertEqual('Daisy', contact['first_name'])

        contact = handle_first_name('The Reverend Bob', {})
        self.assertEqual('The Reverend', contact['prefix_name'])
        self.assertEqual('Bob', contact['first_name'])

    def test_add_prefix_first_and_middle_name(self):
        contact = handle_first_name('The Reverend Billy Bob', {})
        self.assertEqual('The Reverend', contact['prefix_name'])
        self.assertEqual('Billy', contact['first_name'])
        self.assertEqual('Bob', contact['middle_name'])

    def test_adds_first_and_middle_name(self):
        contact = handle_first_name('Mary Sue', {})
        self.assertEqual('Mary', contact['first_name'])
        self.assertEqual('Sue', contact['middle_name'])
