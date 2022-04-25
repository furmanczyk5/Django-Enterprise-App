# Template App

__Easy way to toggle__

_don't forget to change back before commit!_

/ui/middleware.py

change `"use_template" : 'content/web_base.html'`
to this `"use_template" : 'newtheme/templates/base.html'`

__Usage__

Basic usage

{% extends "newtheme/templates/base.html"

Use static files

Load with `{% load staticfiles %}`

use with `{% static 'newtheme/js/base.js' %}`


__Template Blocks__

additional_head_js - any additional template specific js to be loaded in the head

additional_head_css - any additional template specific CSS

title - title sent to page or APA default

messages - form validation / notifications sent from apps

header - includes/header.html

content_wrap - all content dumped here

block footer - includes/footer.html

additional_head_js - any additional template specific js


__Sandbox__

http://127.0.0.1:8000/template_app/sandbox/publications/
http://127.0.0.1:8000/template_app/sandbox/pattern-library/
http://127.0.0.1:8000/template_app/sandbox/legacy-content/1
http://127.0.0.1:8000/template_app/sandbox/legacy-content/2
http://127.0.0.1:8000/template_app/sandbox/legacy-content/3
http://127.0.0.1:8000/template_app/sandbox/legacy-content/4
http://127.0.0.1:8000/template_app/sandbox/new-content/
http://127.0.0.1:8000/template_app/sandbox/interim-content/
http://127.0.0.1:8000/template_app/sandbox/search/
http://127.0.0.1:8000/template_app/sandbox/home/

__Check if user is Authenticated__

`{% if request.user.is_authenticated %}`






