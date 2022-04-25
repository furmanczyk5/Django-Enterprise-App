from bs4 import BeautifulSoup

from django import template

from ui.utils import get_selectable_options_tuple_list
from ui.planning_shortcode import route_shortcode


register = template.Library()
EMPTY_STRING = ''


@register.inclusion_tag('ui/select-input/options.html')
def selectable_options(mode="", value=None, has_empty=True, selected_option=None):

    option_tuple_list = get_selectable_options_tuple_list(mode=mode,value=value)

    context = {
        "has_empty":has_empty,
        "selected_option":selected_option,
        "option_tuple_list":option_tuple_list
    }

    return context

@register.filter(name="user_friendly_file_size")
def user_friendly_file_size(value, current_unit):

    kilobyte = 1024
    megabyte = kilobyte * 1024
    gigabyte = megabyte * 1024
    
    if current_unit == "KB":
        multiplier = kilobyte
    elif current_unit == "MB":
        multiplier = megabyte
    elif current_unit == "GB":
        multiplier = gigabyte
    else:
        multiplier = 1

    byte_count = value * multiplier

    try:
        if byte_count >= gigabyte:
            return "%.2f GB" % float(byte_count / gigabyte)
        elif byte_count >= megabyte:
            return "%.2f MB" % float(byte_count / megabyte)
        elif byte_count >= kilobyte:
            return "%.2f KB" % float(byte_count / kilobyte)
        else:
            return "%s bytes" % byte_count
    except:
        return None

# useful methods for filtering
def filter_planning_shortcodes(tag):
    return tag.name == "div" and tag.has_attr("data-planning-shortcode")

def make_filter_by_attribute(attribute_name):
    def return_filter(tag):
        return tag.has_attr(attribute_name)
    return return_filter

@register.filter(name="render_planning_shortcodes")
def render_planning_shortcodes(content):

    if content:
        soup = BeautifulSoup(content)
        planning_dynamic_elements = soup.find_all(filter_planning_shortcodes)
        for element in planning_dynamic_elements:

            shortcode = element.get("data-planning-shortcode")
            shortcode_params = element.find_all(make_filter_by_attribute("data-planning-shortcode-param"))
            sc_kwargs = dict()
            for param in shortcode_params:
                try:
                    param_name = param.find_all(make_filter_by_attribute("data-planning-shortcode-param-name"))[0].get_text()
                    param_value = param.find_all(make_filter_by_attribute("data-planning-shortcode-param-value"))[0].get_text()
                    sc_kwargs[param_name] = param_value
                except: 
                    pass #bomb out if value or name not provided
            element.replace_with(BeautifulSoup(route_shortcode(shortcode=shortcode, **sc_kwargs)))

        return str(soup)
    else:
        return ""

@register.inclusion_tag('ui/newtheme/forms/includes/multiform-display-errors.html')
def multiform_display_errors(*forms, display_errors=[], error_instructions=None, form_label_accessor=None):
    # TO DO: form_label_accessor argument not being used? Remove?

    forms_have_errors = False
    for form in forms:
        if form.errors:
            forms_have_errors = True

    context = {
        "forms":forms,
        "forms_have_errors":forms_have_errors,
        "display_errors":display_errors,
        "error_instructions":error_instructions
    }

    return context


@register.inclusion_tag('ui/newtheme/forms/includes/multiform-display-errors.html')
def formset_display_errors(formset, display_errors=[], error_instructions=None):

    forms_have_errors = False
    for form in formset:
        if form.errors:
            forms_have_errors = True

    context = {
        "forms":formset,
        "forms_have_errors":forms_have_errors,
        "display_errors":display_errors,
        "error_instructions":error_instructions
    }

    return context

@register.filter
def get_hidden_input_fields(url):
    split_url = url.split('?')

    if len(split_url) != 2:
        return EMPTY_STRING

    split_query = split_url[1].rstrip('/').split('&')

    return ''.join([
        _create_hidden_input(query)
        for query in split_query
        if '=' in query
    ])


def _create_hidden_input(query):
    name, value = query.split('=')
    if name and value:
        return '<input hidden name="{}" value="{}"/>'.format(name, value)

    return EMPTY_STRING

