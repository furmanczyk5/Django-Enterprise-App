from content.models import ContentTagType, Tag, TagType


def add_member_story_tag(instance):
    tag_type = TagType.objects.get(code='KNOWLEDGEBASE_RESOURCE_CATEGORIES')

    content_tag_type, _ = ContentTagType.objects.get_or_create(
        content=instance,
        tag_type=tag_type
    )

    member_story_tag = Tag.objects.get(code='MEMBER_STORY')
    content_tag_type.tags.add(member_story_tag)
    content_tag_type.save()
