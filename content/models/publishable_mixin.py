import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models import QuerySet
from django.utils import timezone

from .settings import PUBLISH_STATUSES


def verify_publish_type(publish_type):
    """
    simple function to make sure publish is not trying to do something funky,
    will raise exception to prevent publish if necessary
    """
    if publish_type not in ["PUBLISHED", "DRAFT", "SUBMISSION", "EARLY_RESUBMISSION"]:
        raise ValueError("Invalid Publish Type: '%s'" % publish_type)


class Publishable(models.Model):
    """
    abstract model for anything that's publishable (includes publish status, time, by, etc.)
    """
    published_time = models.DateTimeField(editable=False, null=True, blank=True) # time at which item is published
    publish_time = models.DateTimeField("publish time", blank=True, null=True) # time to publish item in the future
    published_by = models.ForeignKey(
        User,
        related_name="%(app_label)s_%(class)s_published_by",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    publish_status = models.CharField(
        max_length=50,
        choices=PUBLISH_STATUSES,
        default="DRAFT",
        db_index=True
    )
    publish_uuid = models.CharField(null=True, blank=True, max_length=36, default=uuid.uuid4)

    is_publish_root = False
    is_content = False

    publish_reference_fields = []

    def get_versions(self, database_alias="default"):
        versions_qs = list(type(self).objects.using(database_alias).filter(publish_uuid=self.publish_uuid))
        versions = {
            "PUBLISHED": next((v for v in versions_qs if v.publish_status == "PUBLISHED"), None),
            "DRAFT": next((v for v in versions_qs if v.publish_status == "DRAFT"), None),
            "SUBMISSION": next((v for v in versions_qs if v.publish_status == "SUBMISSION"), None),
            "EARLY_RESUBMISSION": next((v for v in versions_qs if v.publish_status == "EARLY_RESUBMISSION"), None)
        }
        return versions

    def deep_copy(self, replace=dict()):
        """
        makes a copy of this record, and related records from publish_reference_fields, but saves with different publish_uuid
        """
        instance = type(self).objects.get(id=self.id)
        instance.pk = None
        instance.id = None
        instance.publish_uuid = uuid.uuid4()

        for key, value in replace.items():
            setattr(instance, key, value)

        instance.save()

        for x in self.publish_reference_fields:

            if not x["publish"]:
                if x["multi"]:
                    from_records = getattr(self, x["name"]).all()
                    to_records = instance._meta.get_field(x["name"]).related_model.objects.filter(pk__in=[r.pk for r in from_records])
                    getattr(instance, x['name']).set(to_records)
            else:

                publish_name = x.get("through_name", x["name"])

                if x["multi"]:

                    from_records = getattr(self, publish_name).all() if hasattr(self, publish_name) else []

                    for record in from_records:
                        record.deep_copy(replace={"%s_id" % x["replace_field"]: instance.id})

                else:
                    # when related object can only have one relationship
                    if hasattr(self, publish_name):
                        record = getattr(self, publish_name)
                        if record:
                            record.deep_copy(replace={"%s_id" % x["replace_field"]: instance.id})

        if self.publish_reference_fields:
            # necessary if anything else on instance has changed e.g. the "not publish"
            instance.save()

        return instance

    def publish(self, replace=(None, None), publish_type="PUBLISHED", database_alias="default", versions=None):
        """
        publishes model to another instance, either on same database, or another.
         - replace: for models that relate back to models in publish hierarchy by foreign key,
               replace should specify the attribute name and value of the newly published model

        TODO: publish to id option

        NOTE: To speed up publishing, could maybe pass in "versions", would save one query for every time publish is called
        """
        verify_publish_type(publish_type)

        versions = versions or self.get_versions()
        instance = self.get_instance_to_publish(database_alias, publish_type, replace, versions)

        for field in self.publish_reference_fields:

            try:
                if not field["publish"]:
                    if field["multi"]:
                        # if related object does not exist on separate database this will fail...maybe use try except to handle this case?
                        from_records = getattr(self, field["name"]).all()
                        to_records = instance._meta.get_field(
                            field["name"]
                        ).related_model.objects.using(
                            database_alias
                        ).filter(
                            pk__in=[r.pk for r in from_records]
                        )
                        getattr(instance, field['name']).set(to_records)
                else:

                    publish_name = field.get("through_name", field["name"])

                    if field["multi"]:

                        self.handle_multi_publish(database_alias, instance, publish_name, publish_type, field)

                    else:
                        self.handle_single_publish(database_alias, instance, publish_name, publish_type, field)

            except Exception as e:
                if database_alias != "staging":
                    raise e

        # is this extra save really necessary?... Yes it is
        if self.publish_reference_fields or replace[0]:
            # only need to do this again if reference fields changed or something needed to be replaced
            instance.save(using=database_alias)

        return instance

    def get_instance_to_publish(self, database_alias, publish_type, replace, versions):

        instance = versions.get(self.publish_status)  # this will become the published copy
        instance.pk = instance.id = versions.get(publish_type).pk if versions.get(publish_type, None) else None
        instance.publish_status = publish_type
        instance.published_time = timezone.now()
        if replace[0]:
            setattr(instance, replace[0], replace[1])
        instance.save(using=database_alias)

        instance = type(
            self
        ).objects.using(
            database_alias
        ).filter(
            id=instance.id
        )  # requery...
        return instance.first()

    def handle_single_publish(self, database_alias, instance, publish_name, publish_type, field):
        # when related object can only have one relationship
        if hasattr(self, publish_name):
            record = getattr(self, publish_name)
            if record:
                published_record = record.publish(
                    replace=("%s_id" % field["replace_field"], instance.id),
                    publish_type=publish_type,
                    database_alias=database_alias
                )

                self.after_publish_reference(instance, published_record, publish_name)  # hook

    def handle_multi_publish(self, database_alias, instance, publish_name, publish_type, field):
        from_records = []
        if hasattr(self, publish_name):
            try:
                from_records = getattr(self, publish_name).all()
            except AttributeError:
                # OneToOne field?
                from_records = [getattr(self, publish_name)]

        if hasattr(instance, publish_name) and isinstance(getattr(instance, publish_name), QuerySet):
                getattr(instance, publish_name).exclude(
                    publish_uuid__in=[
                        r.publish_uuid for r in from_records
                    ]
                ).delete()  # delete needs to be done this way when through table specified
        for record in from_records:
            published_record = record.publish(
                replace=("%s_id" % field["replace_field"], instance.id),
                publish_type=publish_type,
                database_alias=database_alias
            )

            self.after_publish_reference(instance, published_record, publish_name)  # hook

    def after_publish_reference(self, published_instance, published_reference, publish_name):
        """
        hook in the publish method for additional handling of related publishable references
            NOTE: careful when using, should only be for special exceptions, make sure you have the correct publish_name

            params:
                published_instance - the published instance of this class
                published_reference - the published instance of the related reference
                publish_name - an identifier, the name of the attribute on published_instance for accessing published_reference (see publish method)
        """
        pass

    class Meta:
        abstract = True
        permissions = (("can_publish", "Can publish"),) # DOES THIS WORK???
