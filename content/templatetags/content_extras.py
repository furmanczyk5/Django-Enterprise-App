import os
import pytz
import datetime

from django import template
from django.db.models import Q
from django.conf import settings
from django.utils.timesince import timesince
from django.utils import timezone

from content.models import Content, MenuItem, CONTENT_TYPES, MessageText, Tag, TagType
from content.utils import solr_record_to_details_path, force_utc_datetime, \
    getattr_universal, resolve
from content.solr_search import SolrSearch
from exam.models import APPLICATION_STATUSES, ExamApplication

utc = pytz.utc
register = template.Library()


@register.filter
def print_filter(value):
    print(value)
    return ""


@register.filter
def system_file_path(value):
    return os.path.join(settings.STATIC_ROOT, value)


@register.filter
def subtract(value, arg):
    return value - arg


@register.filter
def percentage(value, arg):
    return (float(value)/float(arg)) * 100.0


@register.filter
def equate_strings(value, arg):
    """ sometimes it is difficult to equate different types in templates (like strings and ints)"""
    return str(value) == str(arg)


@register.filter(name="content_text")
def content_text(value):
    """
    Usage, "CONTENT_CODE"|content_text|safe

    FOR LATER: make so that you pass argument for what field to query by eg. code, id, etc
    """
    content_records = Content.objects.filter(code=str(value), publish_status='PUBLISHED')

    if len(content_records) >= 1:
        content_record = content_records[len(content_records)-1]
        html_returned = content_record.text
    else:
        html_returned = '<div data-failure="record_not_found"></div>'

    return html_returned


@register.filter(name="message_text")
def message_text(value):
    """
    Usage, "CONTENT_CODE"|message_text|safe

    FOR LATER: make so that you pass argument for what field to query by eg. code, id, etc
    """
    message_records = MessageText.objects.filter(code=str(value))

    if len(message_records) >= 1:
        message_record = message_records[len(message_records)-1]
        html_returned = message_record.text
    else:
        html_returned = '<div data-failure="record_not_found"></div>'

    return html_returned


@register.filter(name="remove_querystring_param")
def remove_querystring_param(value,arg):
    param_list = value.split('&')
    param_list_altered = [x.strip() for x in param_list if not x.strip().startswith(str(arg)+'=')]
    return '&'.join(param_list_altered)


@register.filter(name="startswith")
def startswith(value, arg):
    """
    Usage, {% if value|starts_with:"arg" %}
    """
    return value.startswith(arg)


@register.filter(name="getattr")
def getattr_tag(value, arg):
    """
    Usage, {{ value|getattr:"arg" }}
    """
    return getattr_universal(value, arg)


@register.filter(name="resolve")
def resolve_tag(value, argpath):
    """
    Usage, {{ value|getattr:"attr1.attr2" }}
        defaults to None
    """
    return resolve(value, argpath)


@register.filter(name="datetime_is_past")
def datetime_is_past(d):
    return d and d < timezone.now()


@register.filter(name="datetime_from_json")
def datetime_from_json(datetime_string):
    try:
        datetime_python = datetime.datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%S.%fZ')
        return datetime_python
    except:
        try:
            datetime_python = datetime.datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%SZ')
            return datetime_python
        except:
            return datetime_string


@register.filter(name="datetime_with_zone_is_past")
def datetime_with_zone_is_past(d):
    """
    must be called on a timezone-aware datetime
    """
    zone = d.tzinfo
    now=timezone.now()
    now_local = now.astimezone(zone)
    return d and d < now_local


@register.filter(name="datetime_with_zone_from_json")
def datetime_with_zone_from_json(datetime_string, timezone_string):
    tz_obj = pytz.timezone(timezone_string)
    try:
        datetime_python = datetime.datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%S.%fZ')
        datetime_localized = pytz.utc.localize(datetime_python)
        datetime_astimezone = datetime_localized.astimezone(tz_obj)
        return datetime_astimezone
    except:
        try:
            datetime_python = datetime.datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%SZ')
            datetime_localized = pytz.utc.localize(datetime_python)
            datetime_astimezone = datetime_localized.astimezone(tz_obj)
            return datetime_astimezone
        except:
            return datetime_string


@register.filter(name="datetime_from_json_nodecimal")
def datetime_from_json_nodecimal(datetime_string):
    try:
        datetime_python = datetime.datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%SZ')
        return datetime_python
    except:
        return datetime_string


@register.filter(name="time_from_json_datetime")
def time_from_json_datetime(datetime_string):
    """
    useful when getting dates from solr
    eg. '2015-04-20T19:30:03Z' -> '7:30 p.m.'
    """
    try:
        datetime_python = datetime.datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%SZ')
        time_friendly =  datetime_python.strftime('%I:%M %p')
        return time_friendly.strip('0').replace('PM','p.m.').replace('AM','a.m.')
    except:
        return datetime_string


@register.filter(name="time_and_zone_from_json_datetime")
def time_and_zone_from_json_datetime(datetime_string, timezone_string):
    """
    useful when getting dates from solr
    eg. '2015-04-20T19:30:03Z' and 'America/Chicago' -> '7:30 p.m. CDT'
    """
    tz_obj = pytz.timezone(timezone_string)
    try:
        datetime_python = datetime.datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%SZ')
        datetime_localized = pytz.utc.localize(datetime_python)
        datetime_astimezone = datetime_localized.astimezone(tz_obj)
        time_friendly = datetime_astimezone.strftime('%I:%M %p %Z')
        return time_friendly.strip('0').replace('PM','p.m.').replace('AM','a.m.')
    except:
        return datetime_string


@register.filter(name="weekday_from_json_datetime")
def weekday_from_json_datetime(datetime_string):
    """
    useful when getting dates from solr
    eg. '2015-04-20T19:30:03Z' -> 'Monday'
    """
    try:
        datetime_python = datetime.datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%SZ')
        weekday_friendly = datetime_python.strftime('%A')
        return weekday_friendly
    except:
        return datetime_string


@register.filter(name="date_from_json_datetime")
def date_from_json_datetime(datetime_string, format_string=None):
    """
    useful when getting dates from solr
    eg. '2015-04-20T19:30:03Z' -> 'April 20'
    """
    try:
        format_string = format_string or "%B %d"
        datetime_python = datetime.datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%SZ')
        weekday_friendly = datetime_python.strftime(format_string)
        return weekday_friendly
    except:
        return datetime_string or ''


@register.filter(name="year_from_json_datetime")
def year_from_json_datetime(datetime_string):
    """
    useful when getting dates from solr
    eg. '2015-04-20T19:30:03Z' -> '2015'
    """
    try:
        datetime_python = datetime.datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%SZ')
        year_friendly = datetime_python.strftime('%Y')
        return year_friendly
    except:
        return datetime_string

@register.filter(name="full_date_from_json_datetime")
def full_date_from_json_datetime(datetime_string, format_string=None):
    """
    useful when getting dates from solr
    eg. '2015-04-20T19:30:03Z' -> 'April 20, 2015'
    """
    try:
        format_string = format_string or "%B %d, %Y"
        datetime_python = datetime.datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%SZ')
        weekday_friendly = datetime_python.strftime(format_string)
        return weekday_friendly
    except:
        return datetime_string or ''

@register.filter(name="date_from_open_water")
def date_from_open_water(datetime_string, format_string=None):
    """
    Converts an Open Water datetime string to a standard date
    e.g. '2015-04-20T19:30:03.0010012Z' -> '2015-04-20'
    Note: datetime module can't handle seconds with more than 6 decimal places?
    """
    try:
        format_string = format_string or "%F"
        if len(datetime_string) > 27:
            datetime_string = datetime_string[:26] + "Z"
        datetime_python = datetime.datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%S.%fZ')
        weekday_friendly = datetime_python.strftime(format_string)
        return weekday_friendly
    except:
        return datetime_string or ''


@register.filter(name="date_range_from_json_datetimes")
def date_range_from_json_datetimes(begin_time_json, end_time_json):
    """
    useful when getting dates from solr
    NOTE: WON't Work on windows because of hyphen formatting, '%-d'
    """
    try:
        begin_time_python = datetime.datetime.strptime(begin_time_json, '%Y-%m-%dT%H:%M:%SZ')
        end_time_python = datetime.datetime.strptime(end_time_json, '%Y-%m-%dT%H:%M:%SZ')

        begin_time_friendly = begin_time_python.strftime("%B %-d, %Y, %-I:%M %p").strip('0').replace('PM','p.m.').replace('AM','a.m.')

        if begin_time_python.date() == end_time_python.date(): # SAME DATE
            end_time_friendly = end_time_python.strftime("%-I:%M %p")
        # elif begin_time_python.year == end_time_python.year:
        #     end_time_friendly = end_time_python.strftime("%B %-d, %-I:%M %p")
        else:
            end_time_friendly = end_time_python.strftime("%B %-d, %Y, %-I:%M %p")

        end_time_friendly = end_time_friendly.strip('0').replace('PM','p.m.').replace('AM','a.m.')

        return begin_time_friendly + " to " + end_time_friendly
    except:
        return begin_time_json + " to " + end_time_json


@register.simple_tag
def date_range_with_zone_from_json(begin_time_json, end_time_json, timezone_string):
    """
    useful when getting dates from solr
    NOTE: WON't Work on windows because of hyphen formatting, '%-d'
    """
    tz_obj = pytz.timezone(timezone_string)
    try:
        begin_time_python = datetime.datetime.strptime(begin_time_json, '%Y-%m-%dT%H:%M:%SZ')
        begin_time_localized = pytz.utc.localize(begin_time_python)
        begin_time_astimezone = begin_time_localized.astimezone(tz_obj)
        end_time_python = datetime.datetime.strptime(end_time_json, '%Y-%m-%dT%H:%M:%SZ')
        end_time_localized = pytz.utc.localize(end_time_python)
        end_time_astimezone = end_time_localized.astimezone(tz_obj)

        begin_time_friendly = begin_time_astimezone.strftime("%B %-d, %Y, %-I:%M %p").strip('0').replace('PM','p.m.').replace('AM','a.m.')

        if begin_time_python.date() == end_time_python.date(): # SAME DATE
            end_time_friendly = end_time_astimezone.strftime("%-I:%M %p %Z")
        # elif begin_time_python.year == end_time_python.year:
        #     end_time_friendly = end_time_astimezone.strftime("%B %-d, %-I:%M %p %Z")
        else:
            end_time_friendly = end_time_astimezone.strftime("%B %-d, %Y, %-I:%M %p %Z")

        end_time_friendly = end_time_friendly.strip('0').replace('PM','p.m.').replace('AM','a.m.')

        return begin_time_friendly + " to " + end_time_friendly
    except:
        return begin_time_json + " to " + end_time_json


@register.filter(name="content_type_friendly")
def content_type_friendly(content_type):
    return next(ct[1] for ct in CONTENT_TYPES if ct[0] == content_type)


@register.filter(name="split_on_period")
def split_on_period(value, arg):
    """
    Useful for getting id or name from tags on solr
    """
    try:
        split_array = value.split(".")
        return split_array[arg]
    except:
        return value


@register.filter(name="split_on_line")
def split_on_line(value, arg):
    """
    Useful for getting username or title from contacts on solr
    """
    try:
        split_array = value.split("|")
        return split_array[arg]
    except:
        return value


@register.filter(name="any_contains_any")
def any_contains_any(value, arg):
    """
    Useful for getting checking if tags are present
    """
    if value is not None and arg is not None:
        arg_list = arg.split(",")
        return any(y in x for y in arg_list for x in value)
    else:
        return False


@register.filter(name="human_readable_value_from_choice")
def human_readable_value_from_choice(choices, value):
    """
    To get the human readable text for the choice value
    Usage: choices|human_readable_value_from_choice:value -> (gives text matched with 'value')
    """
    if value:
        for choice in choices:
            if choice[0] == value:
                return choice[1]
    return None


@register.filter(name="columns")
def columns(thelist, n):
    """ Break a list into n peices, but "horizontally." That is,
    columns_distributed(range(10), 3) gives::
            [[0, 1, 2],
             [3, 4, 5],
             [6, 7, 8],
             [9]]
        Clear as mud?
    """
    from math import ceil
    try:
        n = int(n)
        thelist = list(thelist)
    except (ValueError, TypeError):
        return [thelist]
    newlists = [list() for i in range(int(ceil(len(thelist) / float(n))))]
    for i, val in enumerate(thelist):
        newlists[i//n].append(val)
    return newlists


@register.filter(name="columns_alternate")
def columns_alternate(thelist, n):
    """
    Break a list into ``n`` columns, filling up each row to the maximum equal
    length possible. For example::
        >>> l = range(10)
        >>> columns(l, 2)
        [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9]]
        >>> columns(l, 3)
        [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9]]
        >>> columns(l, 4)
        [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
        >>> columns(l, 5)
        [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9]]
        >>> columns(l, 9)
        [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9], [], [], [], []]
        # This filter will always return `n` columns, even if some are empty:
        >>> columns(range(2), 3)
        [[0], [1], []]
    """
    try:
        n = int(n)
        thelist = list(thelist)
    except (ValueError, TypeError):
        return [thelist]
    list_len = len(thelist)
    split = list_len // n

    if list_len % n != 0:
        split += 1
    return [thelist[split*i:split*(i+1)] for i in range(n)]


@register.filter(name="columns_alternate_even")
def columns_alternate_even(thelist, n):
    """
    Break a list into ``n`` columns
    """
    try:
        n = int(n)
        thelist = list(thelist)
    except (ValueError, TypeError):
        return [thelist]
    list_len = len(thelist)

    split = list_len // n

    if list_len % n != 0:
        split += 1

    remainder = list_len % n
    cutoff = split - remainder

    split_list = []
    for i in range(n):
        start = split*i
        end = split*(i+1)
        if i >= cutoff:
            end = split*(i+1) - 1
        if i > cutoff:
            start = split*i - 1

        split_list.append((start, end))

    # print(split_list)
    # print(cutoff)
    # print(remainder)

    return [thelist[split_list[i][0]:split_list[i][1]] for i in range(n)]


@register.filter(name="solr_record_to_details_path_filter")
def solr_record_to_details_path_filter(record):
    """ given a solr result, will return the path for that result"""
    return solr_record_to_details_path(record)


# NOT USING REGISTER DECORATOR BECAUSE WE WANT TO USE THIS OUTSIDE OF TEMPLATES
@register.inclusion_tag('admin/content/content/submit-line.html', takes_context=True)
def submit_row_content_content(context, **kwargs):
    """
    Displays the row of buttons for delete and save.
    """
    opts = context['opts']
    change = context['change']
    is_popup = context['is_popup']
    save_as = context['save_as']

    wagtail_job_post = context.get('wagtail_job_post', False)
    extra_save_options = context.get('extra_save_options', {})

    if wagtail_job_post:
        show_publish = True
        show_send_publish = False
    else:
        show_publish = extra_save_options.get('show_publish', wagtail_job_post) # for publishing to the live copy on the prod database
        show_send_publish = extra_save_options.get('show_send_publish', False) # for sending for publication to an editor

    show_preview = extra_save_options.get('show_preview', False) # for publishing to the live copy on the staging database
    show_create_draft = extra_save_options.get('show_create_draft', False) # for publishing to the draft copy on the prod database
    show_sync_imis = extra_save_options.get('show_sync_imis', False) # for publishing to the imis products
    show_sync_harvester = extra_save_options.get('show_sync_harvester', False)
    show_cm_period_log_drop = extra_save_options.get('show_cm_period_log_drop', False)

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

    ctx['original'] = context.get('original', None)

    #this is the difference (also the register.inclusion_tag target template)
    original = ctx.get('original')
    if original is None or (hasattr(original, 'publish_status') and original.publish_status == "DRAFT"):
        # should only be able to do this for draft copies
        ctx['show_publish'] = not is_popup and show_publish
        ctx['show_send_publish'] = not is_popup and show_send_publish
        ctx['show_preview'] = not is_popup and show_preview
        ctx['show_sync_imis'] = not is_popup and show_sync_imis
        ctx['show_sync_harvester'] = not is_popup and show_sync_harvester
    if original is None or (hasattr(original, 'publish_status') and original.publish_status == "SUBMISSION"):
        # FOR NOW: can only do for submission copies
        ctx['show_create_draft'] = not is_popup and show_create_draft

    return ctx


def list_to_tree_dictionary(array_list, parent_field):
    tree_dictionary = {}

    for r in array_list:

        # for some reason, getattr is not working here ???????
        parent_key = r.parent #getattr(r, parent_field)
        parent_key = str(parent_key.id) if parent_key is not None else "ROOT"

        if parent_key in tree_dictionary:
            tree_dictionary[parent_key].append(r)
        else:
            tree_dictionary[parent_key] = [r]

    return tree_dictionary


def tree_dict_to_tree(tree_dict, node):

    tree_dict_key = node if type(node) is str else str(node.id)

    node_list = tree_dict[tree_dict_key] if tree_dict_key in tree_dict else []

    tree_list = []

    for node in node_list:

        tree_list.append({
                "node" : node,
                "children" : tree_dict_to_tree(tree_dict, node)
            })

    return tree_list


# THIS IS FOR THE ADMIN
@register.filter('admin/content/change_list_results_tree.html', takes_context=True)
def list_to_treelist(context):
    results = context['results']
    parent_field = context['parent_field']

    tree_dictionary = list_to_tree_dictionary(results, parent_field)

    tree_list = tree_dict_to_tree(tree_dictionary, "ROOT")

    return context


@register.inclusion_tag('content/newtheme/templatetags/solr-results.html')
def solr_results(record_template="content/newtheme/search/record_templates/generic.html", q=None, filters=None, rows=None, sort=None):
    solr_return = SolrSearch(q=q, filters=[filters], rows=rows, sort=sort).get_results()
    # This is not great but Solr doesnt sort on tokenized fields and this is better than rebuilding the solr database
    if sort == 'title asc' and solr_return.get('response', {}).get('docs', []):
        solr_return['response']['docs'] = sorted(solr_return['response']['docs'], key=lambda i: i.get('title', ''))
    return {
        "record_template": record_template,
        "results": solr_return
    }

@register.inclusion_tag('content/newtheme/includes/ferguson_style.html', takes_context=True)
def ferguson(context):
    try:
        today = timezone.now().date()

        is_ferguson = context.request.user.username == "228416"
        is_date = today.month == 4 and today.day == 1

        if is_ferguson and is_date:
            profile = context.request.user.contact.individualprofile
            return {
                "is_ferguson":True,
                "is_date":today.month == 4 and today.day == 1,
                "background_image":profile.image.image_thumbnail.url
            }
        else:
            return {}

    except:
        return {}

@register.filter
def age(value):
    now = timezone.now()
    try:
        difference = force_utc_datetime(now) - force_utc_datetime(value)
    except:
        return value

    if difference <= datetime.timedelta(minutes=1):
        return 'Just now'
    return '%(time)s ago' % {'time': timesince(value).split(', ')[0]}

@register.filter
def age_in_days(value):
    now = timezone.now()
    try:
        difference = force_utc_datetime(now) - force_utc_datetime(value)
    except:
        return value

    if difference <= datetime.timedelta(hours=24):
        return 'Today'
    elif difference <= datetime.timedelta(hours=48):
        return 'Yesterday'
    return '%s days ago' % difference.days


@register.filter(name='addcss')
def addcss(field, css):
   return field.as_widget(attrs={"class":css})


@register.filter(name='field_type')
def field_type(field):
    return field.field.widget.__class__.__name__


@register.filter
def is_member_only(groups_list):
    member_only_values = {"member"}
    if groups_list:
        return not (set(groups_list) - member_only_values)
    else:
        return False

@register.filter
def is_member_or_subscription(permission_groups_list):
    member_or_subscription_values = {"member", "planning", "commissioner"}
    if permission_groups_list:
        return bool(set(permission_groups_list) & member_or_subscription_values)
    else:
        return False

@register.filter
def is_aicpmember_only(groups_list):
    aicpmember_only_values = {"aicpmember"}
    if groups_list:
        return not (set(groups_list) - aicpmember_only_values)
    else:
        return False

@register.filter
def is_subscription_only(permission_groups_list):
    subscription_only_values = {"JAPA"}
    if permission_groups_list:
        return not (set(permission_groups_list) - subscription_only_values)
    else:
        return False

@register.filter
def interpolate_hex(hex_string1, hex_string2):
    """
    return a hex color in between the two color arguments
    """
    rgb_list1 = [ int(hex_string1[x:x+2],16) for x in range(1,6,2) ]
    rgb_list2 = [ int(hex_string2[x:x+2],16) for x in range(1,6,2) ]
    min_vals = [ min(rgb_list1[x], rgb_list2[x]) for x in range(0,len(rgb_list1)) ]
    new_list = [  (min_vals[x] + int((abs(rgb_list1[x] - rgb_list2[x]) / 2))) for x in range(0,len(rgb_list1)) ]
    hex_digits = [ hex(h).replace('0x','') for h in new_list]
    hex_string = "#" + "".join(str(hh) for hh in hex_digits)
    return hex_string

@register.filter(name="has_group")
def has_group(user, group):
    return next((True for g in user.groups.all() if g.name==group), False)


@register.filter(name="activity_is_past")
def activity_is_past(activity):
    if getattr(activity, "begin_time", None):
        return True if activity.begin_time < datetime.datetime.now(tz=utc) else False
    else:
        return False


@register.filter(name="sorted_by")
def sorted_by(iterable, sort_fields):

    sort_vars = sort_fields.split(",")

    def sort_functon(x):
        sort_values = []
        for sort_path in sort_vars:
            value = resolve(x, sort_path)
            sort_values += [value is None, value]
        return tuple(sort_values)

    return sorted(iterable, key=sort_functon)


@register.filter
def get_application_status(master_id):
    exam_app = ExamApplication.objects.filter(master__id=master_id, publish_status='SUBMISSION').first()
    if exam_app:
        return exam_app.application_status
    else:
        return None

@register.filter(name="is_deceased")
def is_deceased(mem_type):
    if mem_type == "DEC":
        return "*"
    else:
        return ''

@register.simple_tag
def get_tags(content=None, tagtype_code=None):
    if content and tagtype_code:
        return Tag.objects.filter(contenttagtype__content=content, tag_type__code=tagtype_code)
    else:
        return []

@register.filter(name="get_verbose_app_status")
def get_verbose_app_status(status):
    """
    convert a status code into a status description
    """
    app_status_dict = dict(APPLICATION_STATUSES)
    return app_status_dict[status]

@register.filter(name="limit_chars")
def limit_chars(value,arg):
    value = value[0:arg]
    return value

@register.filter(name="is_filter_field")
def is_filter_field(field):
    if field.name:
        return field.name.find("filter_") >= 0 and not field.name.find("cm") >= 0
    else:
        return False

@register.filter(name="convert_field_name")
def convert_field_name(field):
    if field.name:
        if field.name.find("filter_") >= 0:
            tag_type_code = field.name.replace("filter_", "").upper()
            tag_type = TagType.objects.get(code=tag_type_code)
            if tag_type:
                return tag_type.title
            else:
                return field.name
        else:
            return field.name
    else:
        return "Unnamed"

@register.filter(name="get_highest_search_count")
def get_highest_search_count(dict_list):
    highest = 0
    tag_dict = {}
    if dict_list:
        for d in dict_list:
            count = d.get("count", 0)
            if count > highest:
                highest = count
        for d in dict_list:
            if highest == d.get("count", 0):
                tag_dict = d
            tag_id = tag_dict.get("id", None)
    return (tag_id, highest)


@register.filter(name="convert_to_label")
def convert_initial_form_value_to_label(initial):
    return initial[1]


@register.filter(name="get_preview_url")
def get_preview_url(content):
    if content:
        if getattr(content, 'url', None):
            return "{0}/?publish_status=DRAFT".format(content.url.rstrip('/'))
        else:
            draft = Content.objects.get(id=content.id)

            if draft.content_type == 'PUBLICATION':
                my_app = 'publications'
                my_model = draft.resource_type.lower()
                if draft.resource_type == 'PUBLICATION_DOCUMENT':
                    my_model = 'document'

            elif draft.content_type == 'BLOG':
                my_app = 'blog'
                my_model = 'blogpost'

            else:
                my_app = draft._meta.app_label
                my_model = draft._meta.model_name

            my_id = draft.master_id

            # TO DO: these hardcoded exceptions are wonky...
            # should come up with a better way to associate url paths with model names
            if my_app == "learn" and my_model == "learncourse":
                my_model = "course"
            if my_app == "learn" and my_model == "learncoursebundle":
                my_model = "bundle"
            elif my_app == "publications" and my_model == "publicationdocument":
                my_model = "document"
            return "/{0}/{1}/{2}/?publish_status=DRAFT".format(my_app, my_model, my_id)
    return '#'


@register.filter
def is_link(url):
    if not isinstance(url, str):
        return False
    allowed_protocols = [
        'http://',
        'https://'
    ]
    return any(url.startswith(x) for x in allowed_protocols)

@register.simple_tag
def should_render_activity(is_waitlist_block=False, master_id_from_solr=None, waitlisted_master_ids=None):
    if (is_waitlist_block and int(master_id_from_solr) in waitlisted_master_ids) \
        or (not is_waitlist_block and int(master_id_from_solr) not in waitlisted_master_ids):
        return True
    else:
        return False

@register.filter
def none_to_empty_string(value):
    if value == None:
        return ''
    else:
        return value

@register.filter
def planning_mag_section(content):
    ctt = content.contenttagtype.filter(tag_type__code="PLANNING_MAG_SECTION").first() if content else None
    tag = ctt.tags.first() if ctt else None
    return getattr(tag, 'title', None)
