from content.models import TagType
from content.models import Tag, Content

def shift_tags(retire_tag_id, shift_to_tag_id, tag_type_group):
    from jobs.models import Job
    from content.models import ContentTagType, Tag
    retire_tag = Tag.objects.get(id=retire_tag_id)
    shift_to_tag = Tag.objects.get(id=shift_to_tag_id)
    print("RetireTag: ", retire_tag)
    print("TagContentAs: ", shift_to_tag)
    content_to_adjust_qs = Job.objects.filter(contenttagtype__tag_type=tag_type_group, contenttagtype__tags=retire_tag)
    num_to_change = content_to_adjust_qs.count()
    print("\tNumToChange", num_to_change)
    counter=1
    for content in content_to_adjust_qs:
        tag_set = ContentTagType.objects.get(content=content, tag_type=tag_type_group)
        tag_set.tags.remove(retire_tag)
        tag_set.tags.add(shift_to_tag)
        tag_set.save()
        percent_done = round(counter/num_to_change*100, 2)
        print("\t\tChanged Content called %s, %s percent done" % (content, percent_done))
        counter += 1


def remove_tag(id):
    from content.models import Tag, Content
    this_tag = Tag.objects.get(id=id)
    print(this_tag)
    content_count = Content.objects.filter(contenttagtype__tags=this_tag).count()
    if content_count == 0:
        print("Removing this tag: ", this_tag)
        this_tag.delete()
    else:
        print("Unable to remove %s, %s records remaining" % (this_tag, content_count))

if __name__ == "__main__":
    # list of dicts representing the tags to retire and how to tag existing content
    tags_list = [
        [1293, 1306],  # Development Regulation or Administration(1293) to	Land Use Planning (1306)
        [1300, 1298],  # Health and Human Services(1300)	Food Systems Planning(1298)
        [1304, 1289]  # Landscape Architecture(1304)	Civil Engineering(1289)
    ]

    specialty_group = TagType.objects.get(title="Specialty")

    for tag_pair in tags_list:
        shift_tags(tag_pair[0], tag_pair[1], specialty_group)
        remove_tag(tag_pair[0])
