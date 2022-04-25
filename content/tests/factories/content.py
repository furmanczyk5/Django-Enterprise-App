import factory

from content.models.content import Content
from content.models.settings import ContentType, ContentStatus, PublishStatus, WorkflowStatus


class ContentFactory(factory.DjangoModelFactory):

    class Meta:
        model = Content


class ContentProductFactory(ContentFactory):
    content_type = ContentType.PRODUCT.value
    publish_status = PublishStatus.PUBLISHED.value
    workflow_status = WorkflowStatus.IS_PUBLISHED.value
    status = ContentStatus.ACTIVE.value
    template = "pages/newtheme/default.html"
