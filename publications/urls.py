from django.conf.urls import url
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
    url(r'^japa/subscriber/tandf_redirect/$', views.japa_archive_redirect, name="japa_archive_redirect"),
    url(r'^japa/subscriber/tandf_redirect_other/$', views.japa_journal_redirect, name="japa_journal_redirect"),
    url(r'^japa/subscriber/tandf_redirect/email/$', views.JAPAEmailRedirect.as_view(), name="japa_email_redirect"),

    url(r'^planning/$', views.PlanningMagazineHome.as_view(), name="planning_magazine_home"),
    url(r'^planning/section/(?P<mag_section>\w+)/$', views.PlanningMagazineSection.as_view(), name="planning_magazine_section"),
    url(r'^planning/series/(?P<mag_section>\w+)/$', views.PlanningMagazineSection.as_view(), name="planning_magazine_series"),
    url(r'^planning/load_more_articles/$', views.load_more_articles, name="load_more_articles"),
    url(r'^planning/load_more_articles/(?P<page>.*)/$', views.load_more_articles, name="load_more_articles"),

]
