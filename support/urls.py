from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    url(r'^contact-us/success/$', TemplateView.as_view(template_name="support/newtheme/contact-us-success.html"),
        name="contact_us_success"),
    url(r'^contact-us/$', views.ContactUsView.as_view(), name="contact_us"),
    url(r'^contact-us/(?P<category>\w+)/$', views.ContactUsView.as_view(), name="contact_us_topic"),
]
