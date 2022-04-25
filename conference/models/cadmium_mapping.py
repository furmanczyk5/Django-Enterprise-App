from django.db import models


MAPPING_TYPES = (
    # string to string (NOT FIELDS)
    ('HARVESTER_ROLE_TO_DJANGO_ROLE', 'Harvester Speaker Role to Django Role Type'),
    ('HARVESTER_SESSION_TYPE_TO_ACTIVITY_TYPE', 'Harvester Session Type to Django Activity Type'),
    ('HARVESTER_TRACK_TO_APA_CODE', 'Harvester Track to Django Track Tag'),
    ('HARVESTER_TOPICS_TO_APA_TAXO', 'Harvester Topics to Django Taxonomy Tags'),
    # field to field mappings (field names)
    ('PRESENTATION_FIELD_TO_POSTGRES_FIELD', 'Presentation Field to Django'),
    ('PRESENTER_FIELD_TO_POSTGRES_FIELD', 'Presenter Field to Django'),
    ('CUSTOM_PRES_FIELD_TO_POSTGRES_FIELD', 'Presentation Custom Field to Django'),
    ('PRESENTER_CUSTOM_FIELD_TO_POSTGRES_FIELD', 'Presenter Custom Field to Django'),
)


class CadmiumMapping(models.Model):
    mapping_type = models.CharField(
        choices=MAPPING_TYPES, max_length=100, null=True, blank=True)
    from_string = models.CharField(max_length=200, null=True, blank=True)
    to_string = models.CharField(max_length=200, null=True, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Mapping from <<%s>> to <<%s>>" % (
            self.from_string[:20] if self.from_string else None, self.to_string[:20] if self.to_string else None)


class SyncMapping(models.Model):
    sync = models.ForeignKey("conference.CadmiumSync", on_delete=models.CASCADE)
    mapping = models.ForeignKey(CadmiumMapping, on_delete=models.CASCADE)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cadmium Sync Mapping"
        verbose_name_plural = "Cadmium Sync Mappings"
