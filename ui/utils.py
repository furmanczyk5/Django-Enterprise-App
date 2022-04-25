import os

from cities_light.models import Region, Country
from compressor.css import CssCompressor
from bs4 import BeautifulSoup

from django.conf import settings

from content.models import Tag
from imis.models import CustomSchoolaccredited
from store.models import Product, ProductOption, ProductPrice


# Geonames uses the two-letter state abbreviation code for US Regions (states) for
# its `geoname_code` field, but other countries get digits or non-semantic representations
# of their regions.
# https://americanplanning.atlassian.net/browse/DEV-3922
# In the interest of maintaining data consistency we will continue using the two-letter
# abbreviation for U.S. states but use the `name` value for other countries
NORTH_AMERICAN_GEONAME_CODES = {
    'Alaska': 'AK',
    'Alabama': 'AL',
    'Arkansas': 'AR',
    'Arizona': 'AZ',
    'California': 'CA',
    'Colorado': 'CO',
    'Connecticut': 'CT',
    'Washington, D.C.': 'DC',
    'Delaware': 'DE',
    'Florida': 'FL',
    'Georgia': 'GA',
    'Hawaii': 'HI',
    'Iowa': 'IA',
    'Idaho': 'ID',
    'Illinois': 'IL',
    'Indiana': 'IN',
    'Kansas': 'KS',
    'Kentucky': 'KY',
    'Louisiana': 'LA',
    'Massachusetts': 'MA',
    'Maryland': 'MD',
    'Maine': 'ME',
    'Michigan': 'MI',
    'Minnesota': 'MN',
    'Missouri': 'MO',
    'Mississippi': 'MS',
    'Montana': 'MT',
    'North Carolina': 'NC',
    'North Dakota': 'ND',
    'Nebraska': 'NE',
    'New Hampshire': 'NH',
    'New Jersey': 'NJ',
    'New Mexico': 'NM',
    'Nevada': 'NV',
    'New York': 'NY',
    'Ohio': 'OH',
    'Oklahoma': 'OK',
    'Oregon': 'OR',
    'Pennsylvania': 'PA',
    'Rhode Island': 'RI',
    'South Carolina': 'SC',
    'South Dakota': 'SD',
    'Tennessee': 'TN',
    'Texas': 'TX',
    'Utah': 'UT',
    'Virginia': 'VA',
    'Vermont': 'VT',
    'Washington': 'WA',
    'Wisconsin': 'WI',
    'West Virginia': 'WV',
    'Wyoming': 'WY',
    # Appending Canada here instead of making a separate dict
    # we only mail badges to the U.S. and Canada so deal with it
    'Alberta': 'AB',
    'British Columbia': 'BC',
    "Manitoba": "MB",
    "New Brunswick": "NB",
    "Newfoundland and Labrador": "NL",
    "Northwest Territories": "NT",
    "Nova Scotia": "NS",
    "Nunavut": "NU",
    "Ontario": "ON",
    "Prince Edward Island": "PE",
    "Quebec": "QC",
    "Saskatchewan": "SK",
    "Yukon": "YT"
}


def get_selectable_options_tuple_list(mode="", value=None):

    if mode == "country":
        option_tuple_list = [(str(x.name), x.name) for x in Country.objects.all()]
    elif mode == "region_from_country":
        option_tuple_list = [
            (str(NORTH_AMERICAN_GEONAME_CODES.get(x.name, x.name)), x.name)
            for x in Region.objects.filter(country__name=value)
        ]
        filtered_option_tuple_list = []
        # iMIS has a 15-character limit on state names...(╯°□°）╯︵ ┻━┻
        for option in option_tuple_list:
            if len(option[0]) > 15:
                filtered_option_tuple_list.append((option[0][:15], option[1][:15]))
            else:
                filtered_option_tuple_list.append((option[0], option[1]))
        option_tuple_list = filtered_option_tuple_list
        del filtered_option_tuple_list

    elif mode == "current_programs_from_school":
        if value:
            option_tuple_list = [cs for cs in CustomSchoolaccredited.get_current_degree_programs(school_id=value)] + [("OTHER", "Other")]
        else:
            option_tuple_list = [(None, ""), ("OTHER", "Other")]
    elif mode == "all_programs_from_school":
        if value:
            option_tuple_list = [cs for cs in CustomSchoolaccredited.get_all_degree_programs(school_id=value)] + [("OTHER", "Other")]
        else:
            option_tuple_list = [(None, ""), ("OTHER", "Other")]
    elif mode == "all_programs_from_school_no_other":
        if value:
            option_tuple_list = [cs for cs in CustomSchoolaccredited.get_all_degree_programs(school_id=value, school_program_types=["PAB"])]
        else:
            option_tuple_list = [(None, "")]
    elif mode == "product":
        option_tuple_list = [(x.id, x.content.title) for x in Product.objects.filter(publish_status="PUBLISHED")]
        option_tuple_list = option_tuple_list
    elif mode == "productoption_from_product":
        option_tuple_list = [(str(x.id), x.title) for x in ProductOption.objects.filter(product__id=value)]
        if option_tuple_list == []:
            option_tuple_list = [(str(value) + "_NONE", "None")]
    elif mode == "productprice_from_productoption":
        
        option_tuple_list = []

        if value.endswith("_NONE"):
            value = value[:-5]
            option_tuple_list = [(x.id, x.title + ": " + str(x.price)) for x in ProductPrice.objects.filter(product=int(value),)]
        else: 
            try:
                product_option = ProductOption.objects.get(id=int(value))
                option_tuple_list = [(x.id, x.title + ": " + str(x.price)) for x in ProductPrice.objects.filter(product=product_option.product, option_code=product_option.code)]
            except ValueError:
                option_tuple_list = []

    elif mode == "tag":
        option_tuple_list = [(x.code, x.tuple) for x in Tag.objects.filter(tag_type__code=value)]
    else:
        option_tuple_list = []

    return option_tuple_list


def get_css_path_from_less_path(less_paths):
    before_compiler_html = ""
    for less_path in less_paths:
        before_compiler_html += '<link type="text/less" rel="stylesheet" href="%s" />' % less_path
    the_html = CssCompressor(content=before_compiler_html, resource_kind='css').output()

    soup = BeautifulSoup(the_html)
    return_list = []
    for link in soup.find_all('link', href=True):
        return_list.append(os.path.join(settings.STATIC_ROOT, link['href'].lstrip(settings.STATIC_URL) ))

    return return_list











