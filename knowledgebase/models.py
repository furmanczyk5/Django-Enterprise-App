from content.models import Content, ContentManager, ContentRelationship
from content.utils import generate_filter_model_manager

from submissions.models import Review, ReviewRole


def add_places_for_solr(formatted_content, contentplaces):
        places = []

        if contentplaces:
            for contentplace in contentplaces:
                place_str = '{}|{}'.format(contentplace.id, contentplace.place)
                places.append(place_str)

            formatted_content['place_descriptor_name'] = ', '.join(places)

        return formatted_content


class Collection(Content):
    class_query_args = {'content_type': 'KNOWLEDGEBASE_COLLECTION'}
    objects = generate_filter_model_manager(
        ParentManager=ContentManager,
        content_type='KNOWLEDGEBASE_COLLECTION'
    )()
    default_template = 'knowledgebase/newtheme/collection.html'

    class Meta:
        proxy = True


class CollectionRelationship(ContentRelationship):
    class_query_args = {'relationship': 'KNOWLEDGEBASE_COLLECTION'}
    prevent_auto_class_assignment = True


class Resource(Content):
    objects = generate_filter_model_manager(
        ParentManager=ContentManager,
        content_type='KNOWLEDGEBASE'
    )()
    default_template = 'knowledgebase/newtheme/resource.html'

    def save(self, *args, **kwargs):
        self.content_type = 'KNOWLEDGEBASE'
        super().save(*args, **kwargs)

    def solr_format(self):
        formatted_content = super().solr_format()
        return add_places_for_solr(formatted_content, self.contentplace.all())

    class Meta:
        proxy = True
        verbose_name_plural = 'All resources'


class Story(Content):
    objects = generate_filter_model_manager(
        ParentManager=ContentManager,
        content_type='KNOWLEDGEBASE_STORY'
    )()
    default_template = 'knowledgebase/newtheme/story.html'

    def save(self, *args, **kwargs):
        self.content_type = 'KNOWLEDGEBASE_STORY'
        super().save(*args, **kwargs)

    def solr_format(self):
        formatted_content = super().solr_format()
        return add_places_for_solr(formatted_content, self.contentplace.all())

    class Meta:
        proxy = True
        verbose_name = 'Story Submission'
        verbose_name_plural = 'Story Submissions'


class StoryReview(Review):
    class_query_args = {'review_type': 'KNOWLEDGEBASE_STORY_REVIEW'}

    class Meta:
        proxy = True
        verbose_name = 'Story Submissions Review'
        verbose_name_plural = 'Story Submissions Reviews'


class SuggestionReviewRole(ReviewRole):
    class_query_args = {'review_type': 'KNOWLEDGEBASE_REVIEW'}

    class Meta:
        proxy = True
        verbose_name = 'Story/Suggestion Review Role'
        verbose_name_plural = 'Story/Suggestion Review Roles'


class ResourceSuggestion(Content):
    objects = generate_filter_model_manager(
        ParentManager=ContentManager,
        content_type='KNOWLEDGEBASE_SUGGESTION'
    )()

    def save(self, *args, **kwargs):
        self.content_type = 'KNOWLEDGEBASE_SUGGESTION'
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = 'Resource Suggestion'
        verbose_name_plural = 'Resource Suggestions'


class ResourceSuggestionReview(Review):
    class_query_args = {'review_type': 'KNOWLEDGEBASE_SUGGESTION_REVIEW'}

    class Meta:
        proxy = True
        verbose_name = 'Resource Suggestions Review'
        verbose_name_plural = 'Resource Suggestions Reviews'
