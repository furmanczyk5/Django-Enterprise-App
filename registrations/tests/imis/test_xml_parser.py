from unittest import TestCase

from ...imis import *


TEXT_XML = (
    '<PropertyContainer xmlns="http://schemas.imis.com/2008/01/CommunicationsDataContracts" '
    'xmlns:i="http://www.w3.org/2001/XMLSchema-instance"><Property '
    'i:type="a:PropertyTypeStringData" '
    'xmlns:a="http://schemas.imis.com/2008/01/SharedDataContracts">'
    '<a:Caption>single line text</a:Caption>'
    '<a:Description>Field Description</a:Description>'
    '<a:Name>Field Name</a:Name>'
    '<a:PropertyId>id</a:PropertyId>'
    '<a:PropertyTypeName>String</a:PropertyTypeName>'
    '<a:RenderingInformation><a:ControlType>TextField</a:ControlType>'
    '</a:RenderingInformation><a:Required>true</a:Required><a:Visible>'
    'true</a:Visible><a:MaxLength>400</a:MaxLength></Property></PropertyContainer>'
)

INTEGER_XML = (
    '<PropertyContainer xmlns="http://schemas.imis.com/2008/01/CommunicationsDataContracts" '
    'xmlns:i="http://www.w3.org/2001/XMLSchema-instance"><Property '
    'i:type="a:PropertyTypeIntegerData" '
    'xmlns:a="http://schemas.imis.com/2008/01/SharedDataContracts">'
    '<a:Caption>this is a numeric questions</a:Caption>'
    '<a:Description>Field Description</a:Description>'
    '<a:Name>Field Name</a:Name>'
    '<a:PropertyId>id</a:PropertyId>'
    '<a:PropertyTypeName>Integer</a:PropertyTypeName>'
    '<a:Required>false</a:Required>'
    '<a:Visible>false</a:Visible>'
    '</Property></PropertyContainer>'
)

DROPDOWN_XML = (
    '<PropertyContainer xmlns="http://schemas.imis.com/2008/01/CommunicationsDataContracts" '
    'xmlns:i="http://www.w3.org/2001/XMLSchema-instance">'
    '<Property i:type="a:PropertyTypeStringData" '
    'xmlns:a="http://schemas.imis.com/2008/01/SharedDataContracts">'
    '<a:Caption>drop down list</a:Caption>'
    '<a:Description>Field Description</a:Description>'
    '<a:Name>Field Name</a:Name>'
    '<a:PropertyId>id</a:PropertyId>'
    '<a:PropertyTypeName>String</a:PropertyTypeName>'
    '<a:RenderingInformation>'
    '<a:ControlType>DropDownList</a:ControlType>'
    '</a:RenderingInformation>'
    '<a:Rule i:type="a:PropertyRuleValueListData">'
    '<a:ValueList><a:GenericProperty><a:Name>value 1</a:Name>'
    '<a:Value i:type="b:string" xmlns:b="http://www.w3.org/2001/XMLSchema">'
    'value1</a:Value></a:GenericProperty><a:GenericProperty><a:Name>value 2</a:Name>'
    '<a:Value i:type="b:string" xmlns:b="http://www.w3.org/2001/XMLSchema">value2'
    '</a:Value></a:GenericProperty></a:ValueList></a:Rule>'
    '</Property></PropertyContainer>'
)


class XMLParserTest(TestCase):

    def test_parses_control_type(self):
        self.assertEqual('TextField', control_type(TEXT_XML))
        self.assertEqual(None, control_type(INTEGER_XML))

    def test_parses_visbility(self):
        self.assertTrue(visible(TEXT_XML))
        self.assertFalse(visible(INTEGER_XML))
        self.assertFalse(visible(DROPDOWN_XML))

    def test_parses_required(self):
        self.assertTrue(required(TEXT_XML))
        self.assertFalse(required(INTEGER_XML))
        self.assertFalse(required(DROPDOWN_XML))

    def test_parses_max_length(self):
        self.assertEqual(400, max_length(TEXT_XML))

    def test_parses_choices(self):
        expected = [
            ('value1', 'value 1'),
            ('value2', 'value 2')
        ]
        self.assertEqual(expected, choices(DROPDOWN_XML))
