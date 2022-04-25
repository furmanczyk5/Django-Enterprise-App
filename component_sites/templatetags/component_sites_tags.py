from wagtail.wagtailcore.models import Page

from django import template

register = template.Library()


def get_nav_for_page(page, open_node_ids, depth=1, max_open_depth=2, max_depth=3):

    return_page = dict(
        id=page.id,
        title=page.title, 
        url=page.url)

    is_open = page.id in open_node_ids
    if (depth < max_depth) and (is_open or (depth < max_open_depth)):
        depth += 1
        return_page["is_open"] = is_open
        return_page["children"] = [get_nav_for_page(c, open_node_ids, depth, max_open_depth, max_depth
            ) for c in page.get_children().filter(live=True, show_in_menus=True)]

    return return_page


@register.simple_tag
def get_navigation(page):
    """
    useful when getting dates from solr
    NOTE: WON't Work on windows because of hyphen formatting, '%-d'
    """
    ancestors = list(page.get_ancestors()[1:])

    navigation = dict(breadcrumb=[dict(title=a.title, get_url=a.url) for a in ancestors])

    open_nodes = ancestors[:3]
    if len(open_nodes) < 3 and page.show_in_menus:
        open_nodes.append(page)

    homepage = open_nodes[0]

    navigation["menu"] = [get_nav_for_page(p, open_nodes) for p in homepage.get_children().filter(show_in_menus=True)]

    return navigation["menu"]


@register.inclusion_tag('component-sites/component-theme/templates/includes/nav.html')
def globalnav(page):
    """
    Assignment tag to assign the root_menu variable even if the context does not define it
    NOTE: Assignment tags are deprecated in django 1.9, once we upgrade, start using simple_tag instead
    Also, can probably remove this from the renderContent function
    """
    ancestors_and_self = list(page.get_ancestors()) + [page]
    homepage = ancestors_and_self[1]
    navigation = [get_nav_for_page(c, [], max_open_depth=3, max_depth=4) for c in homepage.get_children().filter(live=True, show_in_menus=True)]
    context = dict(navigation=navigation)
    return context


@register.inclusion_tag('component-sites/component-theme/templates/includes/nav-footer.html')
def footernav(page):
    ancestors_and_self = list(page.get_ancestors()) + [page]
    homepage = ancestors_and_self[1]
    navigation = [get_nav_for_page(c, [], max_open_depth=3, max_depth=4) for c in homepage.get_children().filter(live=True, show_in_menus=True)]
    context = dict(navigation=navigation)
    return context


@register.inclusion_tag('component-sites/component-theme/templates/includes/breadcrumb.html')
def breadcrumb(page):
    context = dict(ancestors=[dict(title=a.title, url=a.url) for a in page.get_ancestors()[1:]])
    return context


@register.inclusion_tag('component-sites/component-theme/templates/includes/sidenav.html')
def sidenav(page):

    ancestors = list(page.get_ancestors()[2:5])
    how_many = len(ancestors)
    # do not test for show_in_menus when there are no other ancestors (page itself will be section root)
    if how_many == 0:
        ancestors.append(page)
    # if page will not be section root then it only gets appended if show_in_menus is true:
    elif how_many >=1 and how_many < 3 and page.show_in_menus:
        ancestors.append(page)

    section_root = ancestors[0]
    ancestor_ids = [a.id for a in ancestors]
    context = dict()
    context["sidenav"] = dict(
        id=section_root.id,
        title=section_root.title,
        url=section_root.url,
        is_open=True,
        children=[get_nav_for_page(c, ancestor_ids, 1, 0, 4) for c in section_root.get_children().filter(show_in_menus=True)])
    return context

# this may be better as a utility function:
@register.filter
def get_url_path_no_home(page):
    """
    the url path with the homepage slug does not work, so get rid of it.
    """
    full_url_path = page.url_path
    url_parts = full_url_path.split("/")
    if url_parts:
        del url_parts[0]
    if url_parts:
        del url_parts[0]
    if url_parts:
        url_path_no_home = "/" + "/".join(url_parts)
    else:
        url_path_no_home = "/"

    return url_path_no_home


@register.filter
def scale_rgb(rgb_string, scalar=0.0):
    """
    scalar is -1.0 to 1.0, or 0% to 100% lightening or darkening of the remaining scale of darkness
    for a given color: -1.0 = maximum darkening, 1.0 = maximum lightening
    """
    rgb_list = [int(val) for val in rgb_string.split(',')]
    if scalar > 0:
        return ",".join([str(int(val+((255-val)*scalar))) for val in rgb_list])
    else:
        return ",".join([str(int(val-(val*abs(scalar)))) for val in rgb_list])

