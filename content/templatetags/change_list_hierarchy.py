from django import template
from django.contrib.admin.templatetags import admin_list

from bs4 import BeautifulSoup

register = template.Library()


def results_hierarchy(cl):
    tree_dict = results_tree_dict(cl)
    return results_tree_list(cl, tree_dict, "ROOT", [])


def results_tree_dict(cl):
    """
    Returns a dictionary, the keys are nodes, values are children of that node.
    The key "ROOT" is special. Any node without a parent is a root.
    """
    tree_dict = {}

    id_list = [res.id for res in cl.result_list]

    # maybe check if cl.formset -> zip (cl.result_list, cl.formset.forms)
    for res in cl.result_list:
        parent_key = res.parent  # get hierarchy field defined in model
        parent_key = str(parent_key.id) if parent_key is not None and parent_key.id in id_list else "ROOT"
        if parent_key in tree_dict:
            tree_dict[parent_key].append(res)
        else:
            tree_dict[parent_key] = [res]

    return tree_dict


def results_tree_list(cl, tree_dict, node, ancestry):
    """
    Uses a tree dictionary and a given node key. Returns a hierarchical data list
    """
    tree_dict_key = node if type(node) is str else str(node.id)
    node_list = tree_dict[tree_dict_key] if tree_dict_key in tree_dict else []
    tree_list = []
    for res in node_list:
        res_ancestry = ancestry[:]
        res_ancestry.append(res.id)
        tree_list.append({
                "node": admin_list.ResultList(None, admin_list.items_for_result(cl, res, None)),
                "id": res.id,
                "ancestry": ancestry,
                "children": results_tree_list(cl, tree_dict, res, res_ancestry)
            })
    return tree_list


# the inclusion tag file should be in a different location if we want to make this generic
@register.inclusion_tag("admin/content/taxotopictag/change_list_results.html")
def result_list_tree(cl):
    """
    Displays the headers and hierarchical data list together
    """
    headers = list(admin_list.result_headers(cl))
    num_sorted_fields = 0
    for h in headers:
        if h['sortable'] and h['sorted']:
            num_sorted_fields += 1
    return {'cl': cl,
            'result_hidden_fields': list(admin_list.result_hidden_fields(cl)),
            'result_headers': headers,
            'num_sorted_fields': num_sorted_fields,
            'results': results_hierarchy(cl)}


@register.filter(name="hierarchy_cell")
def hierarchy_cell(item, result):
    """
    Usage, {{ item|hierarchy_cell:result }}
    """
    soup = BeautifulSoup(item, 'xml') # using xml parser because html parser is working with partial tables

    # We only want to apply hierarchy formatting to the head cell (Django
    #  designates this as the first cell that is not the check box)
    if soup.th:
        th = soup.th
        span_tag = soup.new_tag("span")
        if "children" in result and result["children"]:
            span_tag['class'] = "windowshade_tree"
            span_tag['data-target'] = ".cl_tree_" + str(result["id"])
        else:
            span_tag['class'] = "windowshade_tree_leaf"

        margin = len(result["ancestry"]) * 24
        span_tag['style'] = "margin-left:%spx" % margin
        th.insert(0, span_tag)
        return str(th)
    else:
        return item
