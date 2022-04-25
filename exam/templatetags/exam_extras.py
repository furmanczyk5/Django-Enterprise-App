from django import template

register = template.Library()


@register.filter
def year_filter(value):
    return round(value/365, 1)


@register.filter
def timedelta_to_year(td):
    # td comes in in this format: '0:00:05.551746'
    if td:
        year_of_seconds = 365 * 24 * 60 * 60
        job_seconds = td.total_seconds()
        years = job_seconds / year_of_seconds
        return float("{0:.2f}".format(years))
    else:
        return 0


@register.filter
def criteria_filter(value):
    if value == 1:
        verbage = "Meets Requirements"
    elif value == 2:
        verbage = "Does Not Meet Requirements"
    else:
        verbage = "Not Selected"
    return verbage


@register.filter
def approval_filter(value):
    if value == 1:
        verbage = "Approval"
    elif value == 2:
        verbage = "Denial"
    else:
        verbage = "Not Selected"
    return verbage


@register.filter
def in_range(value, arg):
    if value in range(arg,7):
        return True
    else:
        return False


# THIS IS FOR THE ADMIN
@register.inclusion_tag('admin/exam/examregistration/submit-line.html', takes_context=True)
def submit_row_exam_examregistration(context, **kwargs):
    """
    Displays the row of buttons for admin operations.
    """
    opts = context['opts']
    change = context['change']
    is_popup = context['is_popup']
    save_as = context['save_as']

    extra_save_options = context.get('extra_save_options', {})
    show_prometric = extra_save_options.get('show_prometric', True)

    ctx = {
        'opts': opts,
        'show_delete_link': not is_popup and context['has_delete_permission'] and change and context.get('show_delete', True),
        'show_save_as_new': not is_popup and change and save_as,
        'show_save_and_add_another': context['has_add_permission'] and not is_popup and (not save_as or context['add']),
        'show_save_and_continue': not is_popup and context['has_change_permission'],
        'is_popup': is_popup,
        'show_save': True,
        'preserved_filters': context.get('preserved_filters'),
    }

    ctx['show_prometric'] =  not is_popup and show_prometric
    return ctx
