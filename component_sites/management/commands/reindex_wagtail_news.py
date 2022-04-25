from django.core.management.base import BaseCommand
from django.db import models
from django.conf import settings

from wagtail.wagtailcore.models import Page

from content.solr_search import SolrUpdate
from component_sites.models import Page as WagtailPage, NewsPage
from component_sites.wagtail_hooks import WagtailSolrPublish
from _data_tools.solr_reindex import scrub_dict, reindex_wagtail

class Command(BaseCommand):
    help = "Re-Indexes Wagtail News in Solr"

    def handle(self, **options):
        """remove deleted news pages from solr"""
        env = 'staging' if settings.ENVIRONMENT_NAME != 'PROD' else 'PROD'
        reindex_wagtail(
          Class = NewsPage,
          environment = env,
          delete_kwargs = {"query":"record_type:WAGTAIL_PAGE AND content_type:newspage"},
        )

