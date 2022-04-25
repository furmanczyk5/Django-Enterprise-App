from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^blog/$', views.BlogSearchView.as_view(), name='search'),
    url(r'^apanews/$', views.APANewsSearchView.as_view()),
]
