from content.models import TagType, Tag

# PLANNING MAGAZINE SCRIPTS

PLANNING_MAGAZINE_TAGS = {
    'PLANNING_MAG_FEATURED': (
        'Planning Magazine Featured',
        ('FEATURED_HERO', 'Featured Hero'),
        ('FEATURED_RECENT', 'Featured Recent'),
        ('FEATURED_SECTION', 'Featured Section')
        ),
    'PLANNING_MAG_SECTION': (
        'Planning Magazine Section',
        ('INNOVATIONS', 'Innovations'),
        ('TOOLS', 'Tools'),
        ('INTERSECTIONS', 'Intersections'),
        ('VOICES', 'Voices')
        ),
    'PLANNING_MAG_SERIES': (
        'Planning Magazine Series',
        ('DISRUPTORS', 'Disruptors'),
        ),
    'PLANNING_MAG_SLUG': (
        'Planning Magazine Slug',
        ('CAREER', 'Career'),
        ('CLIMATE', 'Climate'),
        ('DEMOGRAPHICS', 'Demographics'),
        ('ECONOMIC_DEVELOPMENT', 'Economic Development'),
        ('ENERGY', 'Energy'),
        ('ENGAGEMENT', 'Engagement'),
        ('EQUITY', 'Equity'),
        ('ETHICS', 'Ethics'),
        ('FOOD_SYSTEMS', 'Food Systems'),
        ('HAZARDS_PLANNING', 'Hazards Planning'),
        ('HEALTH', 'Health'),
        ('HOUSING', 'Housing'),
        ('HOW_TO', 'How-To'),
        ('INFRASTRUCTURE', 'Infrastructure'),
        ('JAPA_TAKEAWAY', 'JAPA Takeaway'),
        ('LAND_USE', 'Land Use'),
        ('LEGAL_LESSONS', 'Legal Lessons'),
        ('MEDIA', 'Media'),
        ('PARKING', 'Parking'),
        ('PERSPECTIVES', 'Perspectives'),
        ('PLANNERS_LIBRARY', 'Planners Library'),
        ('PLANNING_PRACTICE', 'Planning Practice'),
        ('PLAN_TO_WATCH', 'Plan To Watch'),
        ('POLICY', 'Policy'),
        ('PUBLIC_SPACE', 'Public Space'),
        ('Q_AND_A', 'Q&A'),
        ('RESILIENCE', 'Resilience'),
        ('SUSTAINABILITY', 'Sustainability'),
        ('TECH', 'Tech'),
        ('THE_PROFESSION', 'The Profession'),
        ('TRANSPORTATION', 'Transportation'),
        ('URBAN_DESIGN', 'Urban Design'),
        ('VIEWPOINT', 'Viewpoint'),
        ('WATER', 'Water')
        ),
    'SPONSORED': (
        'Planning Magazine Sponsored',
        ('PLANNING_MAG_SPONSORED', 'Sponsored Content'),
        )
    }


def make_planning_magazine_tags(tag_data):
    for tt_code in tag_data:
        toop = tag_data.get(tt_code)
        tagtype, created = TagType.objects.get_or_create(code=tt_code, title=toop[0])
        print("tag type is ", tagtype)
        print("tag type created is ", created)
        for i in range(1,len(toop)):
            tag, created = Tag.objects.get_or_create(tag_type = tagtype, code=toop[i][0], title=toop[i][1])
            print("tag is ", tag)
            print("tag created is ", created)
        print("END TAG TYPE\n")
mpmt=make_planning_magazine_tags


def delete_planning_tags(tt_code):
    tt=TagType.objects.get(code=tt_code)
    tags=Tag.objects.filter(tag_type=tt)
    print("tags to delete: ", tags)
    tags.delete()
    print("tag type to delete: ", tt)
    tt.delete()
