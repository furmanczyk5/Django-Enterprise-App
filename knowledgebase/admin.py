from django.contrib import admin

from .admin_content.collection import CollectionAdmin
from .admin_content.resource import ResourceAdmin
from .admin_content.review import (
    ResourceSuggestionReviewAdmin,
    StoryReviewAdmin
)
from .admin_content.review_role import SuggestionReviewRoleAdmin
from .admin_content.submission.resource_suggestion import ResourceSuggestionAdmin
from .admin_content.submission.story import StoryAdmin
from .models import (
    Collection, Resource,
    ResourceSuggestion,
    ResourceSuggestionReview,
    Story, StoryReview,
    SuggestionReviewRole
)


admin.site.register(Collection, CollectionAdmin)
admin.site.register(Resource, ResourceAdmin)
admin.site.register(Story, StoryAdmin)
admin.site.register(StoryReview, StoryReviewAdmin)
admin.site.register(ResourceSuggestion, ResourceSuggestionAdmin)
admin.site.register(ResourceSuggestionReview, ResourceSuggestionReviewAdmin)
admin.site.register(SuggestionReviewRole, SuggestionReviewRoleAdmin)
