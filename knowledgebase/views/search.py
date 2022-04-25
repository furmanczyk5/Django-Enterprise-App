from content.views import SearchView


class ResourceSearchView(SearchView):
    """
    View for searching all of resources and resources for specific collections
    """
    title = 'Research Resource Search'
    filters = [
        (
            "(content_type:KNOWLEDGEBASE OR "
            "content_type:KNOWLEDGEBASE_STORY OR "
            "content_type:KNOWLEDGEBASE_COLLECTION OR "
            "related:KNOWLEDGEBASE_COLLECTION|*)"
        )
    ]
    facets = [
        'tags_SEARCH_TOPIC', 'tags_COMMUNITY_TYPE',
        'tags_JURISDICTION', 'tags_FORMAT',
        'tags_STATE', 'tags_JOB_CATEGORY',
        'tags_KNOWLEDGEBASE_RESOURCE_CATEGORIES',
        'tags_PLACE_DENSITY', 'tags_PLACE_POPULATION_RANGE'
    ]

    def get(self, request, *args, **kwargs):
        self.collection_master_id = kwargs.get('master_id', None)
        return super().get(request, *args, **kwargs)

    def get_filters(self, *args, **kwargs):
        filters = super().get_filters(*args, **kwargs)
        if self.collection_master_id:
            filters = filters + ["related:KNOWLEDGEBASE_COLLECTION|%s" % self.collection_master_id]
        return filters


class CollectionSearchView(SearchView):
    """
    View for searching resource collections
    """
    title = 'Research Collection Search'
    filters = ["content_type:KNOWLEDGEBASE_COLLECTION"]
    facets = [
        'tags_COMMUNITY_TYPE', 'tags_JURISDICTION',
        'tags_STATE', 'tags_KNOWLEDGEBASE_RESOURCE_CATEGORIES',
        'tags_PLACE_DENSITY', 'tags_PLACE_POPULATION_RANGE'
    ]
