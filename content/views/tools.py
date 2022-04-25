import json

from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.html import strip_tags
from six.moves import html_parser

from content.models import Content, MessageText


# FOR TESTING passing new MessageText Model to a Django Message
def test_message_call(request, **kwargs):
#    master_id = kwargs['master_id']
#    code = kwargs['code']
    try:
        msg = MessageText.objects.filter(code='TMI')[0]
        messages.success(request, "Successfully produced a Django message hard-coded in view")
        messages.success(request, msg.text)
        data = json.dumps({"success":"Successfully called MessageText Object json dump"})
    except:
        messages.error(request, "Failed to call MessageText Object")
        data = json.dumps({"failure":"Failed to call MessageText Object json dump"})
    return HttpResponse(data, content_type='application/json')
    #return HttpResponseRedirect("http://localhost:8000/admin/")


def content_json(request, **kwargs):
    """
    returns a content record in json format with option to strip html tags from text property
    """
    master_id = kwargs['master_id']

    # options
    text_format = request.GET.get("textformat","html")      # pass "text" to strip all html tags from "text" property

    context = {}

    try:
        content = Content.objects.get(master__id=master_id, publish_status="PUBLISHED")
    except Content.DoesNotExist:
        context = {"success":False, "message":"Error: No matching Content record"}
        return HttpResponse(json.dumps(context, cls=DjangoJSONEncoder), content_type='application/json')

    context["success"] = True
    context["content"] = model_to_dict(content, fields=["master","title","code","text", "resource_url"])

    if text_format == "text":
        # only want text. Not html tags.
        parser = html_parser.HTMLParser()
        context["content"]["text"] = parser.unescape(strip_tags(context["content"]["text"]))

    return HttpResponse(json.dumps(context, cls=DjangoJSONEncoder), content_type='application/json')


def admin_django_errorlog():
    """
    displays errors posted to /var/log/django/error.log in the admin site
    """

    context = []

    with open('/var/log/django/error.log','r') as log_file:
        #turns file to list
        a = log_file.readlines()
        #turns list to string
        b = ''.join(a)
        #turns string back into list
        context = log_file.split('[django]')

    return render(log_file, "admin/content/includes/django-errorlog.html", context)