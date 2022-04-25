from django.contrib import admin
 
from knowledgebase.models import (
    Collection,
    ResourceSuggestionReview,
    SuggestionReviewRole
)


class RoleFilter(admin.SimpleListFilter):
    title = 'Reviewer'
    parameter_name = 'role'

    def lookups(self, request, model_admin):
        return [
            (irr.id, irr)
            for irr in SuggestionReviewRole.objects.all()
        ]

    def queryset(self, request, queryset):
        if self.value():
            if self.value() == 'UNASSIGNED':
                return queryset.filter(role__isnull=True)
            else:
                return queryset.filter(role=self.value())


class CollectionFilter(admin.SimpleListFilter):
    title = 'Collection'
    parameter_name = 'search_topic'

    def lookups(self, request, model_admin):
        collections = Collection.objects.filter(
            publish_status='DRAFT'
        ).order_by('title')
        return [(c.master_id, c.title) for c in collections]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(related=self.value())
        else:
            return queryset


class ReviewStatusFilter(admin.SimpleListFilter):
    title = 'Review Status'
    parameter_name = 'review_status'

    def lookups(self, request, model_admin):
        review_statuses = list(ResourceSuggestionReview._meta.get_field('review_status').choices)
        review_statuses.insert(0, ('N', 'Not Complete'))
        review_statuses.insert(1, ('P', 'Pending'))
        return review_statuses

    def queryset(self, request, queryset):
        if self.value():
            results = queryset.filter(review_assignments__review_status=self.value())

            if not results:
                return queryset.filter(review_assignments=None,status=self.value())

            return results
        else:
            return queryset
