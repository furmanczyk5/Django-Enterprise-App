import re
import struct

from django import template

from content.models import MenuItem, Content

register = template.Library()


@register.filter
def divide(value, arg): return int(value / arg)


@register.simple_tag
def get_global_nav(root_menu):
    """
    Assignment tag to assign the root_menu variable even if the context does not define it
    NOTE: Assignment tags are deprecated in django 1.9, once we upgrade, start using simple_tag instead
    Also, can probably remove this from the renderContent function
    """
    return root_menu or MenuItem.get_root_menu()

@register.simple_tag
def get_conference_nav(conference_menu):
    return conference_menu or MenuItem.get_root_menu(landing_code="CONFERENCE_HOME") 


@register.inclusion_tag('newtheme/templates/includes/sidenav.html', takes_context=True)
def sidenav(context, **kwargs):

    for_url = kwargs.get("for_url", None) # For dynamic pages, pass this parameter to grab the side nav of the content matching this url
    current_page_url = kwargs.get("current_page_url", for_url) # if current page url is different from the for_url, specify
    content_record = kwargs.get("content", None) # DON't REMEMBER WHAT THIS IS FOR

    if for_url:
        content = Content.objects.with_details().filter(
            status__in=("A", "H"),
            publish_status="PUBLISHED",
            url=for_url
        ).order_by(
            "published_time"
        ).select_related(
            "landingpage",
            "{0}__{0}__{0}__{0}".format(
                "parent_landing_master__content_live__landingpage")
        ).last()
        if content is not None:
            ancestors = content.get_landing_ancestors()
        else:
            ancestors = context.get('ancestors', [])
    else:
        content = context.get("content", None)
        ancestors = context.get("ancestors", [])

    sidenav_content = dict(url=current_page_url) if current_page_url else content.url

    return dict(content=sidenav_content, ancestors=ancestors)


@register.simple_tag
def meunitems(landingpage):
    select_related = (
        "master__content_draft" if landingpage.publish_status == "DRAFT" else
        "master__content_live")
    return landingpage.child_menuitems.select_related(select_related)


@register.filter
def ss_next(some_list, current_index):
    """
    Returns the next element of the list using the current index if it exists.
    Otherwise returns an empty string.
    {% with next_element=some_list|ss_next:forloop.counter0 %}
    """
    try:
        return some_list[int(current_index) + 1] # access the next element
    except:
        return '' # return empty string in case of exception


@register.filter
def ss_previous(some_list, current_index):
    """
    Returns the previous element of the list using the current index if it exists.
    Otherwise returns an empty string.
    {% with previous_element=some_list|ss_previous:forloop.counter0 %}
    """
    try:
        return some_list[int(current_index) - 1] # access the previous element
    except:
        return '' # return empty string in case of exceptio

@register.filter
def test_for_reg_url(url):
    """
    True if url fits pattern /conference*registration/ (* wildcard)
    """
    m = re.search('\/conference.*registration', url)
    return True if m and m.group() else False

@register.filter
def hex_to_rgb(hexstr):
    """
    convert hex string to rgb string
    """
    if hexstr:
        tokens = hexstr.split("#")
        if len(tokens) == 1:
            hexstr = tokens[0]
        elif len(tokens) > 1:
            hexstr = tokens[1]
        rgb_toop = struct.unpack('BBB', bytes.fromhex(hexstr))
        return ','.join(str(s) for s in rgb_toop)
    else:
        return None