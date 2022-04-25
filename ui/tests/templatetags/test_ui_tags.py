from unittest import TestCase
from ui.templatetags.ui_tags import get_hidden_input_fields

class GetHiddenInputFieldsTest(TestCase):
    def test_returns_empty_string_for_url_without_query(self):
        url = '/knowledgebase/search/'
        fields = get_hidden_input_fields(url)
        self.assertEqual('', fields)

    def test_returns_hidden_input_for_single_query(self):
        url = '/knowledgebase/search/?tag=88'
        fields = get_hidden_input_fields(url)
        expected = '<input hidden name="tag" value="88"/>'
        self.assertEqual(expected, fields)

    def test_returns_hidden_input_for_multiple_queries(self):
        url = '/knowledgebase/search/?tag=88&sort=relevance'
        fields = get_hidden_input_fields(url)
        expected = (
            '<input hidden name="tag" value="88"/>'
            '<input hidden name="sort" value="relevance"/>'
        )
        self.assertEqual(expected, fields)  

    def test_returns_empty_string_for_query_malformed_queries(self):
        url = '/knowledgebase/search/?&tag=&sort&=relevance'
        fields = get_hidden_input_fields(url)
        self.assertEqual('', fields)     

    def test_removes_any_trailing_slash(self):
        url = '/knowledgebase/search/?tag=88/'
        fields = get_hidden_input_fields(url)
        expected = '<input hidden name="tag" value="88"/>'
        self.assertEqual(expected, fields)
