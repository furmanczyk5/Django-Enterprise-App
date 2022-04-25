from functools import reduce
import re
from lxml import etree as ElementTree

from ..multi_method import multi, method


NAMESPACES = {'a': 'http://schemas.imis.com/2008/01/SharedDataContracts'}
TRUE = 'true'


def get_value(xml, element):
    parser = ElementTree.XMLParser(recover=True)
    tree = ElementTree.fromstring(xml, parser)
    return tree.xpath('//a:{}/text()'.format(element), namespaces=NAMESPACES)


def get_element(xml, element):
    parser = ElementTree.XMLParser(recover=True)
    tree = ElementTree.fromstring(xml, parser)
    return tree.xpath('//a:{}'.format(element), namespaces=NAMESPACES)


def get_choice_value(xml, element):
    parser = ElementTree.XMLParser(recover=True)
    tree = ElementTree.ElementTree(ElementTree.fromstring(xml, parser))
    return tree.xpath(
        '//a:ValueList/a:GenericProperty/a:{}/text()'.format(element),
        namespaces=NAMESPACES
    )


def control_type(xml):
    value = get_value(xml, 'ControlType')
    return None if not value else value[0]


def visible(xml):
    value = get_value(xml, 'Visible')
    return False if not value else value[0] == TRUE


def required(xml):
    value = get_value(xml, 'Required')
    return False if not value else value[0] == TRUE 


def max_length(xml):
    return int(get_value(xml, 'MaxLength')[0])


def choices(xml):
    values = get_choice_value(xml, 'Value')
    names = get_choice_value(xml, 'Name')
    return list(zip(values, names))
