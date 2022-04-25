import operator
from functools import reduce

from django.apps import apps
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.shortcuts import render
from django.db.models import Q

from ui.utils import get_selectable_options_tuple_list


def get_selectable_options(request, **kwargs):

    mode = kwargs.get("mode", "")
    value = request.GET.get("value", None)

    option_tuple_list = get_selectable_options_tuple_list(mode=mode,value=value)

    context = {
        "has_empty":True,
        "selected_option":None,
        "option_tuple_list":option_tuple_list
    }

    return render(request, "ui/select-input/options.html", context)



def autocomplete(request, **kwargs):
    """ 
    Performs autocomplete suggestions for search on a specified model
    """

    record_template = kwargs.get("record_template", "ui/newtheme/autocomplete/record-template/default.html")
    app = kwargs.get("app", None) # required  
    model = kwargs.get("model", None) # required
    filters = kwargs.get("filters", {})
    exclude = kwargs.get("exclude", {})

    keyword = request.GET.get("keyword", "")
    is_search = request.GET.get("is_search", False) # variable used in the template, results display as autocomplete selectables or as search results (if chose "see more", or submitted search)

    context = {}
    
    # get model object from kwargs
    model_class = apps.get_model(app_label=app, model_name=model)
    # get autocomplete fields from model object
    search_fields = model_class.autocomplete_search_fields()

    # cobine search fields and keyword into list of Q queries
    queries = [Q((field,keyword)) for field in search_fields]

    # filter results for logical 'or' combined Q queries
    results_all = model_class.objects.filter(**filters).exclude(**exclude).filter(reduce(operator.or_, queries))
    results_count = results_all.count()

    if is_search:
        results = results_all[:100]
    else:
        results = results_all[:6]

    context['kwargs'] = kwargs
    context['results'] = results
    context['is_search'] = is_search
    context['results_total'] = results_count
    context['request'] = request

    return render(request, record_template, context)

    #############################
    # Need to do checks on everything!!!!!

    # try:
    #     model_object = get_model(kwargs['app'],kwargs['model'])
    # except LookupError, e:
    #     response_data["error"] = e
    #     response_data["show_results"] = False



    # if 'autocomplete_search_fields' in model_object:
    #     search_fields = model_object.autocomplete_search_fields()
    # else:
    #     response_data["error"] = "autocomplete_search_fields is not defined for %s.%s" % (kwargs['app'],kwargs['model'])
    #     response_data["show_results"] = False



    # if "keyword" in request.GET and request.GET["keyword"] != '':
    #     keyword = request.GET["keyword"]

    #     filter_kwargs = {}

    #     for filter_term in search_fields
    #     response_data["results"] = model_object.
    # else
    #     response_data["show_results"] = False
