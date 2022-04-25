from django.contrib.admin.utils import NestedObjects

from content.models import TagType, Tag
from conference.models.cadmium_mapping import CadmiumMapping, SyncMapping, MAPPING_TYPES
from conference.models.cadmium_sync import CadmiumSync

# NPC21 SCRIPTS

NPC21_TAGS = {
    # "TRACKS" NAME CHANGED TO "PROGRAM AREAS"
    'EVENTS_NATIONAL_TRACK_21': (
        'Program Areas',
        ('INEQUALITY_NPC21', 'Addressing a Legacy of Inequality'),
        ('RECOVERY_NPC21', 'COVID Recovery and Reinvention'),
        ('TRANSPORTATION_NPC21', 'Emerging Transportation and Infrastructure'),
        ('TECHNOLOGY_NPC21', 'Leveraging Rapid Technological Changes'),
        ('INNOVATION_NPC21', 'Planning Practice Innovation'),
        ('CLIMATE_NPC21', 'Resilient Planning in a Changing Climate')
        ),
    # DIVISIONS: NEW DIVISION ALREADY IN.
    'EVENTS_NATIONAL_TYPE': (
        'Activity Type',
        ('CONCURRENT_SESSIONS', 'Concurrent Sessions'),
        ('SPEED_SHARE_SESSIONS', 'Speed Share Sessions'),
        ('KEYNOTE_SPOTLIGHT_SESSIONS', 'Keynote and spotlight session'),
        ('BEATS_OF_BOSTON', 'Beats of Boston'),
        ('WELLNESS_EVENTS', 'Wellness Events'),
        # ??? SHOULD THIS JUST BE A NAME CHANGE: YES - edit Django directly
        # NAME CHANGES ON EXISTING TAGS:
        # ('STORYTELLING_SESSIONS', 'Storytelling Sessions'),
        # ('EXHIBIT_HALL', 'Exhibitor Presentations'),
        # ('CAREER_ZONE','Career Center')
        )
    }

# map harvester topics to apa taxo by creating/editing CadmiumMapping records
OLD_TOPICS = (
'Career Development',
'Community Revitalization',
'Social Justice/Equity',
'Economic Development',
'Energy',
'Ethics',
'Finance',
'Food Systems',
'Hazards',
'Health',
'Historic Preservation',
'Housing Policy',
'Law',
'Natural Resources and Environment',
'Planning Methods and Tools',
'Sustainability',
'Transportation',
'Urban Design',
'Zoning and Ordinances',
)

NEW_TOPICS = (
'American Planning Association',
'Commercial Land Use',
'Demographics',
'Industrial Land Use',
'Infrastructure',
'Institutional Land Use',
'Mixed Land Uses',
'Parks and Recreation',
'Partnerships and Agreements',
'Planning History and Theory',
'Plans',
'Public Participation',
'Public Service Delivery',
'Residential Land Use',
)

HARVESTER_TOPICS_TO_APA_TAXOTOPICTAGS = {
# OLD_TOPICS
'Career Development': 'SKILLSETCAREERSDEVELOPMENT',
'Community Revitalization': 'POLICYREGENERATION',
'Social Justice/Equity': 'POLICYEQUITY',
'Economic Development': 'POLICYECONOMICDEVELOPMENT',
'Energy': 'POLICYENERGY',
'Ethics': 'SKILLSETETHICS',
'Finance': 'MANIFESTATIONSFINANCIAL',
'Food Systems': 'POLICYFOOD',
'Hazards': 'POLICYHAZARDS',
'Health': 'POLICYHEALTHPUBLIC',
'Historic Preservation': 'POLICYPRESERVATIONHISTORIC',
'Housing Policy': 'POLICYHOUSING',
'Law': 'FRAMEWORK',
'Natural Resources and Environment': 'SKILLSETIMPACTSENVIRONMENTAL',
'Planning Methods and Tools': 'SKILLSETMETHODS',
'Sustainability': 'POLICYSUSTAINABILITY',
'Transportation': 'POLICYTRANSPORTATION',
'Urban Design': 'SKILLSETDESIGNURBAN',
'Zoning and Ordinances': 'SKILLSETZONING',
# NEW_TOPICS
'American Planning Association': 'APA',
'Commercial Land Use': 'USECOMMERCIAL',
'Demographics': 'SKILLSETPOPULATIONS',
'Industrial Land Use': 'USEINDUSTRIAL',
'Infrastructure': 'POLICYINFRASTRUCTURE',
'Institutional Land Use': 'USEFACILITIES',
'Mixed Land Uses': 'DEVELOPMENTMIXEDUSE',
'Parks and Recreation': 'POLICYPARKS',
'Partnerships and Agreements': 'MANIFESTATIONSAGREEMENTS',
'Planning History and Theory': 'SKILLSETHISTORY',
'Plans': 'MANIFESTATIONSPLANS',
'Public Participation': 'SKILLSETMETHODSPUBLICHEARINGS',
'Public Service Delivery': 'MANIFESTATIONSPROGRAMS',
'Residential Land Use': 'USERESIDENTIAL'
}

# METHODS TO FIGURE OUT THE MAPPINGS ABOVE
def find_taxo_via_mappings():
    harv_topics = HARVESTER_TOPICS_TO_APA_TAXOTOPICTAGS.keys()
    for topic in harv_topics:
        print("topic is ", topic)
        cm = CadmiumMapping.objects.filter(from_string__contains=topic)
        if cm:
            for c in cm:
                print("found a match: ", c.to_string)
        print("END\n")

# NOPE
def find_taxo_via_tokens():
    for topic in harv_topics:
        print("topic is ", topic)
        tokens = topic.split(" ")
        for s in tokens:
            ttt=TaxoTopicTag.objects.filter(title__contains=s)
            if ttt:
                print("FOUND A MATCH")
                for tag in ttt:
                    print(tag.code)
        print("END\n")

def find_taxo_via_keywords():
    TAXO_STRINGS = (
        'Career', 'Community', 'Equity', 'Housing', 'Environment', 'Sustainability', 'Zoning',
        'Planning', 'Commercial', 'Industrial', 'Institutional', 'Mixed', 'Parks', 'Partnerships', 'History', 'Plans',
        'Public', 'Residential'
        )
    for s in TAXO_STRINGS:
        print("topic is ", s)
        ttt=TaxoTopicTag.objects.filter(title__contains=s)
        if ttt:
            print("FOUND A MATCH")
            for tag in ttt:
                print(tag.code)
        print("END\n")


# 1. Run without saving, correct any dupe mapping records (any that have same from_string and incorrect mapping_type)
def create_taxo_mappings():
    sync = CadmiumSync.objects.get(cadmium_event_key='WKDYRNNY')

    for k,v in HARVESTER_TOPICS_TO_APA_TAXOTOPICTAGS.items():
        print("\nSTART --------------------")
        print("harvester topic: ", k)
        print("apa taxo code: ", v)
        # we need to make sure that we are not overwriting other kinds of non-topic mappings with same from_string
        # cm = CadmiumMapping.objects.filter(
        #     from_string=k,
        #     to_string=v
        #     )
        # if cm:
        #     print("Mapping: ",cm.first().to_string)
        mapping, created = CadmiumMapping.objects.get_or_create(
            from_string=k,
            to_string=v)
        print("created: ", created)
        # print("NUM Mapping records in queryset: ",cm.count())
        # cm = cm.first()
        if mapping and mapping.mapping_type != 'HARVESTER_TOPICS_TO_APA_TAXO':
            print("incorrect mapping type: ", mapping.mapping_type)
            mapping.mapping_type = 'HARVESTER_TOPICS_TO_APA_TAXO'
            mapping.save()
        sync_mapping, created = SyncMapping.objects.get_or_create(sync=sync, mapping=mapping)
        print("END --------------------------\n")

# ***** WILL ALSO NEED TO CORRECT THE MAPPING TYPE ON ALL OTHER CADMIUM MAPPING RECORDS *****
# currently only mapping types involved with tags are being used in the sync code

def fix_mapping_types():
    pass

# CUSTOM FIELD CHANGES: No new mappings
def verify_custom_field_mappings():
    mappings = CadmiumMapping.objects.filter(from_string__contains="Custom")
    for m in mappings:
        print(m.from_string, m.to_string, m.mapping_type)

def make_conference_tags(tag_data):
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

def create_tag_mappings(mapping_type=None, tag_type_code=None):
    track_tag_type = TagType.objects.get(code=tag_type_code)
    sync = CadmiumSync.objects.get(cadmium_event_key='WKDYRNNY')

    for tag in track_tag_type.tags.all():
        print("\nSTART --------------------")
        print("track tag: ", tag)
        # we need to make sure that we are not overwriting other kinds of non-topic mappings with same from_string
        # mapping = CadmiumMapping.objects.filter(
        #     from_string=tag.title,
        #     # mapping_type=mapping_type,
        #     )
        # print("NUM Mapping records in queryset: ",mapping.count())
        # mapping = mapping.first()
        # if mapping:
        #     print("Mapping: ",mapping.from_string, mapping.to_string, mapping.mapping_type)
        mapping, created = CadmiumMapping.objects.get_or_create(
            from_string=tag.title,
            to_string=tag.code)
        print("created: ", created)
        if mapping and mapping.mapping_type != mapping_type:
            print("incorrect mapping type: ", mapping.mapping_type)
            mapping.mapping_type = mapping_type
            mapping.save()
        sync_mapping, created = SyncMapping.objects.get_or_create(sync=sync, mapping=mapping)
        print("END --------------------------\n")

# Call like this:
# BECAUSE THIS IS NEW WE NEED TO UPDATE CODEBASE WHERE EVENTS_NATIONAL_TRACK IS HARDCODED
# mapping_type="HARVESTER_TRACK_TO_APA_CODE"
# tag_type_code = "EVENTS_NATIONAL_TRACK_21"
# create_tag_mappings(mapping_type, tag_type_code)

# mapping_type="HARVESTER_SESSION_TYPE_TO_ACTIVITY_TYPE"
# tag_type_code = "EVENTS_NATIONAL_TYPE"
# create_tag_mappings(mapping_type, tag_type_code)

def verify_field_mappings(mapping_type):
    mappings = CadmiumMapping.objects.filter(mapping_type=mapping_type)
    for m in mappings:
        print(m.from_string, m.to_string, m.mapping_type)

def delete_conference_tags(tt_code):
    tt=TagType.objects.get(code=tt_code)
    tags=Tag.objects.filter(tag_type=tt)
    print("tags to delete: ", tags)
    tags.delete()
    print("tag type to delete: ", tt)
    tt.delete()

# ALSO DO THIS ON PROD:
def delete_npc20_track_mappings():
    mappings = CadmiumMapping.objects.filter(mapping_type="HARVESTER_TRACK_TO_APA_CODE")
    for m in mappings:
        if m.to_string.find('npc20') >= 0:
            print("To delete:")
            print(m.from_string, m.to_string, m.mapping_type)
            m.delete()

def show_to_delete(some_instance):
    collector = NestedObjects(using='default') # or specific database
    collector.collect([some_instance])
    to_delete = collector.nested()
    print(to_delete)
