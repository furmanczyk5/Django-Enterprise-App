import sys
from django.db import models
from planning.settings import ENVIRONMENT_NAME


class MasterContent(models.Model):
    content_live = models.ForeignKey(
        'Content',
        related_name='content_live',
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )
    content_draft = models.ForeignKey(
        'Content',
        related_name='content_draft',
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )

    # the last time that the record was published to prod (compare with updated_time to tell if needs to be published)
    published_time = models.DateTimeField(editable=False, blank=True, null=True)

    # TO DO... consider: should content_type be specified here on MasterContent??

    def __str__(self):
        if self.content_live is not None:
            return "%s | %s" % (self.id, str(self.content_live))
        elif self.content_draft is not None:
            return "%s | %s (draft)" % (self.id, str(self.content_draft))
        else:
            try:
                return "%s | %s (submission)" % (self.id, str(self.content.all()[0]))
            except:
                return "%s | (no content)" % self.id

    @staticmethod
    def autocomplete_search_fields():
        return ("id__iexact", "content_live__title__icontains", "content_draft__title__icontains")

    @classmethod
    def create(cls, content_live = None, content_draft = None):
        """
        set ID to lastest master content ID?
        """
        if 'test' not in sys.argv:
            pk = MasterContent.objects.latest('id').id + 1 # is this pk or id??
            test = cls(id=pk, content_live = content_live, content_draft = content_draft)
            test.save()
        elif 'test' in sys.argv:
            try:
                pk = MasterContent.objects.latest('id').id + 1 # is this pk or id??
            except:
                pk = 100000
            test = cls(id=pk, content_live = content_live, content_draft = content_draft)
            test.save()
        return test

    def save(self, *args, **kwargs):

        # this is a work-around for staging in order to prevent insertion pk violation error of dupe MasterContent records
        # (due to records being created both from prod publishing to staging, and from staging environment directly, at the same time)
        if ENVIRONMENT_NAME == "STAGING" and self.pk is None and 'test' not in sys.argv:
            try:
                self.pk = MasterContent.objects.latest('id').id + 1
            # may not need this exception:
            except Exception as e:
                print("EXCEPTION WHEN TRYING TO SAVE A MASTER CONTENT RECORD: ", e)
        super(MasterContent, self).save(*args, **kwargs)

    def get_top_version(self):
        publish_statuses = self.content.values_list("publish_status", flat=True)
        top_version = None

        if "PUBLISHED" in publish_statuses:
            top_version = "PUBLISHED"
        elif "DRAFT" in publish_statuses:
            top_version = "DRAFT"
        elif "SUBMISSION" in publish_statuses:
            top_version = "SUBMISSION"

        if top_version:
            return self.content.filter(publish_status=top_version).first()
        else:
            return self.content.first()
