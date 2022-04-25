from unittest import TestCase

from knowledgebase.management.commands.csv_transforms.resource import *


class ResourceTransformsTest(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.page = '58'
        self.resource_url = 'https://fake-url.com'
        self.title = 'LETTER TO THE PEOPLE, HON. BACON PANCAKE, 1909'
        self.subtitle = 'Proceedings of a Conference'
        self.text = (
            'This resource is on page %s of %s, '
            'an electronic text contained in the APA '
            'Library E-book Collection. This text is '
            'available to APA members as a benefit of '
            'membership.' %(self.page, self.subtitle,)
        )
        self.year = '1909'
        self.author = 'Pancake, Bacon'

        self.row_dict = {
            'Year': self.year,
            'Volume': self.subtitle,
            'Author': self.author,
            'Title': self.title,
            'Starting Page': self.page,
            'Link': self.resource_url
        }


        self.partial_long_title = (
            'National Proceedings of the Earth, Wind, and Fire Institute, '
            'Given at the Lunch of Bea Arthur on the Occassion of her 200th '
            'Birthday, Hon. Bacon Pancake Reciting a Pledge to Love The Golden'
        )
        self.long_title = self.partial_long_title + ' Girls for All Eternity'

        # self.updated_dict = Command().transform_row(row_dict)

    def test_maps_link_to_model_key(self):
        updated_dict = add_resource_url(self.row_dict)
        self.assertNotIn('Link', updated_dict.keys())
        self.assertEqual(self.resource_url, updated_dict['resource_url'])

    def test_maps_title_to_model_key(self):
        updated_dict = add_title(self.row_dict)
        self.assertNotIn('Title', updated_dict.keys())
        self.assertEqual('{} (p. {})'.format(self.title, self.page), updated_dict['title'])

    def test_truncates_long_title_with_page(self):
        row_dict = {
            'Year': self.year,
            'Volume': self.subtitle,
            'Author': self.author,
            'Title': self.long_title,
            'Starting Page': self.page,
            'Link': self.resource_url
        }
        updated_dict = add_title(row_dict)
        expected = self.partial_long_title + '... (p. 58)'
        self.assertNotIn('Title', updated_dict.keys())
        self.assertEqual(expected, updated_dict['title'])

    def test_truncates_long_title_without_page(self):
        row_dict = {
            'Year': self.year,
            'Volume': self.subtitle,
            'Author': self.author,
            'Title': self.long_title,
            'Starting Page': '',
            'Link': self.resource_url
        }
        updated_dict = add_title(row_dict)
        expected = self.partial_long_title + ' Girls...'
        self.assertNotIn('Title', updated_dict.keys())
        self.assertEqual(expected, updated_dict['title'])


    def test_maps_volume_to_model_key(self):
        updated_dict = add_subtitle(self.row_dict)
        self.assertNotIn('Volume', updated_dict.keys())
        self.assertEqual(self.subtitle, updated_dict['subtitle'])

    def test_transform_and_map_page_and_volume_to_model_key(self):
        updated_dict = add_text(self.row_dict)
        self.assertNotIn('Starting Page', updated_dict.keys())
        self.assertEqual(self.text, updated_dict['text'])
        self.assertEqual(self.text, updated_dict['description'])

    def test_removes_year_from_row_data(self):
        updated_dict = remove_year(self.row_dict)
        self.assertNotIn('Year', updated_dict.keys())
