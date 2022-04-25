import os
import datetime
import pytz
import pickle

from django.db import models
from django.conf import settings

from content.models import BaseContent, Publishable

class MenuItem(BaseContent, Publishable):
    parent_landing_page = models.ForeignKey(
        "pages.LandingPage",
        related_name="child_menuitems",
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )

    parent = models.ForeignKey(
        "MenuItem",
        verbose_name="parent menu item",
        related_name="submenuitems",
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )

    master = models.ForeignKey(
        "MasterContent",
        verbose_name="Associated Content",
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )
    url = models.CharField("custom url", max_length=255, blank=True, null=True, help_text="only if menu item does not point to a specific content record")
    sort_number = models.IntegerField(null=True, blank=True)

    @staticmethod
    def autocomplete_search_fields():
        return ("id__iexact", "title__icontains", "code__icontains")

    def get_url(self):
        if self.master:
            if self.master.content_live:
                return self.master.content_live.url
            elif self.master.content_draft:
                return self.master.content_draft.url
        else:
            return self.url

    def get_child_menuitems(self):
        if self.master:
            if self.publish_status=="DRAFT":
                content = self.master.content_draft
            else:
                content = self.master.content_live
            if content and hasattr(content, "landingpage"):
            # if content and content.content_area=="LANDING": # SOME LANDING PAGES DON"T HAVE content_area set to landing...
                try:
                    # just in case parent_landing_master is not properly set to landing page instance
                    # IF WE WANT TO HIDE Hidden MenuItem records we need to filter here
                    # return content.landingpage.child_menuitems.all()
                    return content.landingpage.child_menuitems.filter(status='A')
                except:
                    pass
        return []

    # Look into using Redis instead of pickle
    @classmethod
    def get_root_menu(cls, landing_code="ROOT"):
        # print(landing_code)

        pickle_path = os.path.abspath(
            os.path.join(settings.BASE_DIR, "pickle", landing_code + ".p"))

        menu_last_updated = MenuItem.objects.filter(
            publish_status="PUBLISHED"
        ).order_by(
            "-updated_time"
        ).values(
            "updated_time"
        ).first()
        if menu_last_updated is not None:
            menu_last_updated = menu_last_updated.get("updated_time")

        if menu_last_updated and ( (not os.path.exists(pickle_path)) or (not os.path.getsize(pickle_path) > 0) or datetime.datetime.utcfromtimestamp(os.path.getmtime(pickle_path)).replace(tzinfo=pytz.UTC) < menu_last_updated):

            os.makedirs(os.path.dirname(pickle_path), exist_ok=True)

            prefetch_related_unit = "landingpage__child_menuitems__master__content_live"
            root_menu = MenuItem.objects.filter(
                parent_landing_page__code=landing_code,
                publish_status="PUBLISHED",
                status="A"
            ).prefetch_related(
                "master__content_live__{0}__{0}__{0}".format(prefetch_related_unit)
            ).all()

            pickle.dump(root_menu, open(pickle_path, "wb"))
        else:
            root_menu = pickle.load(open(pickle_path, "rb"))

        return root_menu

    # TO DO... do we still need this?
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = "MENUITEM_%s" % self.id
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ["sort_number"]
