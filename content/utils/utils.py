import ftplib
import os
import random
import ssl
import string
import sys
from decimal import Decimal

from bs4 import BeautifulSoup
from django import forms
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from sentry_sdk import capture_exception

from planning.settings import RESTIFY_SERVER_ADDRESS


def file_extension_in(path, extensions):
    """
    Returns True if file exists at path, and it's file extension is one of extensions
    where extensions is a list eg. [.html,.htm]
    """

    if os.path.isfile(path):
        fileName, fileExtension = os.path.splitext(path)
        if fileExtension in extensions:
            return True

    return False


def import_content_text_from_file(content_record):
    """
    Updates the text field of the passed content record.
    It populates this field with whatever is inside the 'body' tag.
    If the record that is passed does not specify a valid html (or htm) file
    in it's file_path field, then nothing happens.
    """

    if content_record.file_path is not None and content_record.file_path != "":

        file_path = ""

        try:
            file_path = '/var/www/html' + content_record.file_path
            file_path = os.path.normpath(file_path)
        except:
            content_record.text = "ERROR GETTING FILE PAGE: " + str(sys.exc_info()[0])

        if file_extension_in(file_path, ['.html', '.htm']):

            file_content = ""

            try:
                with open(file_path, encoding="utf-8") as opened_file:
                    file_content = opened_file.read()
                try:
                    soup = BeautifulSoup(file_content)
                    content_record.text = ''.join(str(x) for x in soup.body)
                except:
                    content_record.text = "ERROR PARSING FILE: " + str(sys.exc_info()[0])
            except:
                content_record.text = "ERROR OPENING/READING FILE: " + str(sys.exc_info()[0])

    return content_record.text


def force_utc_datetime(datetime_arg):
    """
    Needed because django is doing something funky with datetimes when publishing to prod
    When "publishing to Prod", "published_time" does not have solr acceptable format (missing z for utc at the end)
    When "publishing to solr", "published_time" is utc formatted

    This is very confusing because both call the same function to publish to solr

    "published_time" is the only field that behaves this way, so it probably has something to do with the master record being saved
    just before trying to access this???

    NOTE: This doesn't actually convert the time to utc, just adds formatting (it's kind of hacky)
    """
    if not datetime_arg:
        return None
    elif timezone.is_naive(datetime_arg):
        return timezone.make_aware(datetime_arg, timezone=timezone.utc)
    else:
        return datetime_arg.astimezone(timezone.utc)


def force_solr_date_format(date_obj, blog_time_bool):
    d = str(date_obj)
    one = str(d).split(' ')
    two = one[1].split('.')
    three = two[1].split('+')
    three3 = int((three[0][0:3]))
    three3dec = three3 / 1000
    three_rou = round(Decimal(three3dec), 3)
    three_nor = three_rou.normalize()
    three_str = str(three_nor).split('.')[1]
    if blog_time_bool:
        return one[0] + 'T' + two[0] + 'Z'
    else:
        return one[0] + 'T' + two[0] + '.' + three_str + 'Z'


def model_to_modelform(model):
    """
    dynamically creates and returns a modelform class for the given model
    """
    meta = type('Meta', (), {"model": model, "exclude": []})
    modelform_class = type('modelform', (forms.ModelForm,), {"Meta": meta})
    return modelform_class


def generate_random_string(length, stringset=string.ascii_letters+string.digits):
    '''
    Returns a string with `length` characters chosen from `stringset`
    >>> len(generate_random_string(20) == 20
    '''
    return ''.join(random.choice(stringset) for i in range(length))


def keep_tags(value, tags):
    """
    Strips all [X]HTML tags except the space seperated list of tags
    from the output.

    Usage: keep_tags:"strong em ul li"
    """
    import re
    from django.utils.html import strip_tags, escape
    tags = [re.escape(tag) for tag in tags.split()]
    tags_re = '(%s)' % '|'.join(tags)
    singletag_re = re.compile(r'<(%s\s*/?)>' % tags_re)
    starttag_re = re.compile(r'<(%s)(\s+[^>]+)>' % tags_re)
    endtag_re = re.compile(r'<(/%s)>' % tags_re)
    value = singletag_re.sub('##~~~\g<1>~~~##', value)
    value = starttag_re.sub('##~~~\g<1>\g<3>~~~##', value)
    value = endtag_re.sub('##~~~\g<1>~~~##', value)
    value = strip_tags(value)
    value = escape(value)
    recreate_re = re.compile('##~~~([^~]+)~~~##')
    value = recreate_re.sub('<\g<1>>', value)
    return value


# THIS WOULD BE NICE FOR SUBMISSION CATEGORIES
def specified_order_sort_by_attribute(the_list, attribute_name, attribute_value_order_list):
    """
    Will sort a list by the a attribute and in the the order you specify
    """
    max_sort_number = len(attribute_value_order_list)

    def sort_func(x):
        try:
            sort_num = attribute_value_order_list.index(getattr(x, attribute_name))
        except:
            sort_num = max_sort_number
        return sort_num

    return sorted(the_list, key=lambda x: sort_func(x), reverse=False)


def generate_filter_model_manager(ParentManager=models.Manager, **filter_kwargs):
    """
    returns a generated class that inherites from models.Manager. Useful for proxy models \
    when you only need to filter the queryset
    """
    class FilterManager(ParentManager):
        def get_queryset(self):
            return super().get_queryset().filter(**filter_kwargs)
    return FilterManager


def get_api_root():
    server_name = RESTIFY_SERVER_ADDRESS
    return server_name + "/api/0.2"


def get_api_key_querystring():
    return "?api_key=C00k13m0nst3r."


def content_class_from_content(content):
    """ to determine what sub-class a content record should have
            NOTE: proxy models not included
    """
    content_type = content.content_type

    content_app = "content"
    content_model = "content"

    if content_type == "PAGE" and hasattr(content, "landingpage"):
        content_app = "pages"
        content_model = "landingpage"
    elif content_type == "EVENT":
        content_app = "events"
        content_model = "event"
    elif content_type == "MEDIA":
        content_app = "media"
        content_model = "media"
    elif content_type == "AWARD":
        content_app = "awards"
        content_model = "submission"
    elif content_type == "RFP":
        content_app = "consultants"
        content_model = "rfp"
    elif content_type == "IMAGE":
        content_app = "imagebank"
        content_model = "image"
    elif content_type == "EXAM":
        content_app = "exam"
        content_model = "examapplication"
    elif content_type == "RESEARCH_INQUIRY":
        content_app = "research_inquiries"
        content_model = "inquiry"
    elif content_type == "BLOG":
        content_app = "blog"
        content_model = "blogpost"
    else:
        content_app = "content"
        content_model = "content"

    return apps.get_model(app_label=content_app, model_name=content_model)


def solr_record_to_details_path(record):
    """ given a solr result, will return the path for that result"""
    try:
        content_type = record.get("content_type", None)
        resource_type = record.get("resource_type", None)
        master_id = str(record.get("id").split(".")[1])
        content_url = record.get("url", None)
        record_type = record.get("record_type", None)

        if record_type == "WAGTAIL_PAGE":
            host = record.get("code", "")
            path_parts = content_url.split("/")
            if path_parts:
                del path_parts[0]
            if path_parts:
                del path_parts[0]
            path = ""
            for part in path_parts:
                path = path + "/" + part
            if "local" in host:
                protocol = "http://"
            else:
                protocol = "https://"
            return protocol + host + path

        if content_url:
            return content_url
        elif content_type == "EVENT":
            event_type = record.get("event_type", None)
            if event_type == "EVENT_SINGLE":
                return "/events/eventsingle/%s/" % master_id
            elif event_type == "EVENT_MULTI":
                return "/events/eventmulti/%s/" % master_id
            elif event_type == "ACTIVITY":
                return "/events/activity/%s/" % master_id
            elif event_type == "COURSE":
                return "/events/course/%s/" % master_id
            elif event_type == "LEARN_COURSE":
                product_code = pc = record.get("code", None)
                return "https://{}/local/catalog/view/product.php?globalid={}".format(settings.LEARN_DOMAIN, pc)
            elif event_type == "EVENT_INFO":
                return "/events/eventinfo/%s/" % master_id
            else:
                return "/events/event/%s/" % master_id
        elif content_type == "PAGE":
            return "/pages/page/%s/" % master_id
        elif content_type == "BLOG":
            return "/blog/blogpost/%s/" % master_id
        elif content_type == "JOB":
            return "/jobs/ad/%s/" % master_id
        elif content_type in ["RFP","RFQ"]:
            return "/consultants/rfp/%s/" % master_id
        elif content_type == "IMAGE":
            return "/imagelibrary/details/%s/" % master_id
        elif content_type == "PUBLICATION" and resource_type == "REPORT":
            return "/publications/report/%s/" % master_id
        elif content_type == "PUBLICATION" and resource_type == "PUBLICATION_DOCUMENT":
            return "/publications/document/%s/" % master_id
        elif resource_type == "BOOK" or resource_type=="EBOOK":
            return "/publications/book/%s/" % master_id
        elif content_type == "KNOWLEDGEBASE":
            return "/knowledgebase/resource/%s/" % master_id
        elif content_type == "KNOWLEDGEBASE_COLLECTION":
            return "/knowledgebase/collection/%s/" % master_id
        elif content_type == "MEDIA":
            media_format = record.get("media_format", None)
            if media_format == "VIDEO":
                 return "/media/video/%s/" % master_id
            elif media_format == "AUDIO":
                 return "/media/audio/%s/" % master_id
            else:
                 return "/media/media/%s/" % master_id
        elif record_type == "CONTACT":
            return "/consultants/profile/display/%s/" % master_id
        else:
            return "/content/content/%s/" % master_id
    except Exception as e:
        capture_exception(e)
        return ""


def html_to_text(html):
    if html:
        soup = BeautifulSoup(html)
        text = " ".join(soup.strings)
        return text
    else:
        return ""


def getattr_universal(x, attr , default=None):
    """
    getattr that works for objects, dictionaries and lists
    """
    try:
        return x[attr]  # first try as dict or list
    except (TypeError, KeyError):
        try:
            return getattr(x, attr, default)  # then try as attribute
        except:
            return default


def resolve(x, attrpath, default=None):
    value = x
    for attr in attrpath.split("."):
        value = getattr_universal(value, attr, default)
    return value


class ImplicitFTP_TLS(ftplib.FTP_TLS):
    """FTP_TLS subclass that automatically wraps sockets in SSL to support implicit FTPS."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sock = None

    @property
    def sock(self):
        """Return the socket."""
        return self._sock

    @sock.setter
    def sock(self, value):
        """When modifying the socket, ensure that it is ssl wrapped."""
        if value is not None and not isinstance(value, ssl.SSLSocket):
            value = self.context.wrap_socket(value)
        self._sock = value


def batch_qs(qs, batch_size=1000):
    """
    Returns a (start, end, total, queryset) tuple for each batch in the given
    queryset.

    Usage:
        # Make sure to order your querset
        article_qs = Article.objects.order_by('id')
        for start, end, total, qs in batch_qs(article_qs):
            print "Now processing %s - %s of %s" % (start + 1, end, total)
            for article in qs:
                print article.body
    """
    total = qs.count()
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        yield (start, end, total, qs[start:end])


def validate_lon_lat(longitude, latitude):
    """
    Validate longitude and latitude values. Since the -180/180 and -90/90
    bounds are mostly in the middle of the Pacific Ocean and at the extreme poles,
    respectively, we don't really care about floating point tolerance as part of the test.
    :param longitude: any
    :param latitude: any
    :return: bool
    :raises: :class:`django.core.exceptions.ValidationError`
    """
    try:
        longitude = float(longitude)
        latitude = float(latitude)
    except (TypeError, ValueError):
        raise ValidationError(
            "longitude ({0}) and/or latitude ({1}) is not a number".format(
                longitude,
                latitude
            )
        )

    if (not -180 <= longitude <= 180) or (not -90 <= latitude <= 90):
        raise ValidationError(
            "longitude ({0}) and/or latitude ({1}) exceed the +/- 180/90 range".format(
                longitude,
                latitude
            )
        )
    return longitude, latitude
