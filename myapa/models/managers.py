from django.db import models


class SchoolManager(models.Manager):
    # TODO... we should be able to get rid of this (only left around for now because of sorting...)
    def get_queryset(self):
        return super().get_queryset().filter(
            member_type="SCH",
            contact_type="ORGANIZATION"
        ).prefetch_related(
            "accredited_school__accreditation"
        ).prefetch_related(
            "students"
        ).order_by(
            'company'
        )


class BookmarkManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(added_type="BOOKMARK")


class ProviderManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            contact_type="ORGANIZATION",
            contactrole__role_type="PROVIDER"
        ).distinct()  # TODO CHANGE THIS LATER WHEN WE ACTUALLY HAVE SOMETHING
