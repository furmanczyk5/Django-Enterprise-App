import django
django.setup()

import warnings
warnings.filterwarnings('ignore')

import uuid
from django.conf import settings
from django.contrib.auth.models import Group

from urllib.request import urlopen
import ssl 

# from urllib import parse
# from xml.dom import minidom
from xml.etree import ElementTree # MUCH better than DOM!!!

from content.models import *
from knowledgebase.models import *
from places.models import *

# def mark_delete_all():
#     qs = SolarResource.objects.filter(publish_status="DRAFT")
#     qs.solr_unpublish()
#     qs.update(status="X")
#     SolarResource.objects.filter(publish_status="PUBLISHED").update(status="X")

# def final_delete_all():
#     SolarResource.objects.filter(status="X").delete()

def solr_republish_all():
    qs = SolarResource.objects.filter(publish_status="DRAFT")
    for s in qs:
        s.solr_publish()
        print("Published: " + str(s))

def import_xml(from_path="./_data_tools/solar/"):
    xml_list = ElementTree.parse(from_path + "_LIST.xml")
    for i in xml_list.getroot()[:]:
        xml_doc = ElementTree.parse(from_path + i.text + ".xml")
        cx = xml_doc.getroot()[0].find("Content")
        m, m_created = MasterContent.objects.get_or_create(id=6000000+int(cx.get("ContentID")))

        c, created = SolarResource.objects.get_or_create(master=m, publish_status="DRAFT" )

        c.title = cx.get("Title")
        c.status="A"
        c.text = cx.get("ContentText")
        c.resource_url = cx.get("MoreInfoUrl")
        c.description = cx.get("ShortDescription")

        c.save()
        m.content_draft = c
        m.save()
        print( ("CREATED: " if created else "UPDATED: ") + c.title )
        
        solar_tag = TaxoTopicTag.objects.get(id=692)
        c.taxo_topics.clear()
        c.taxo_topics.add(solar_tag)
        
        
        px = xml_doc.getroot()[0].find("Place")
        place_type = px.get("PlaceTypeTagCode")

        if place_type=="STATE":
            print(" - - CREATING/GETTING STATE........")
            try:
                place, p_created = Place.objects.get_or_create(place_type="STATE", state_code=px.get("StateCode"), title=px.get("PlaceName"))
            except:
                print(" - - ERROR creating/getting state")
                pass
        else:
            try:
                geo_id = px.get("CensusGeoID")
                try:
                    place = Place.objects.get(census_geo_id=px.get("CensusGeoID"), place_type=place_type)
                except:
                    place = Place.objects.get(census_geo_id="0" + px.get("CensusGeoID"), place_type=place_type)
            except:
                pass

        try:            
            # place = Place.objects.get(census_geo_id="3624988")
            p = ContentPlace.objects.get_or_create(content=c, place=place)
            print(" - - place added!!! ... " + str(p) )
        except:
            print(" - - ERROR: setting place for: " + str(c.master.id))

        for ttx in xml_doc.getroot()[0].findall("TagType"):
            try:
                tt_code = ttx.get("TagTypeCode")
                if tt_code=="RESOURCE_TOOL":
                    tt_code="KNOWLEDGEBASE_TOOL"
                if tt_code=="SOLAR_PRACTICE":
                    tt_code="KNOWLEDGEBASE_SOLAR_PRACTICE"
                if tt_code=="REGION":
                    tt_code="CENSUS_REGION"
                tt = TagType.objects.get(code=tt_code)
                ctt, ctt_created = ContentTagType.objects.get_or_create(content=c, tag_type=tt)
                ctt.tags.clear()
                for tx in ttx.findall("Tag"):
                    try:
                        t = Tag.objects.get(code=tx.get("TagCode"), tag_type=tt)
                        ctt.tags.add(t)
                    except:
                        print(" - - ERROR TAGGING WITH TAG: " + tt.code + " - " + tx.get("TagCode"))
            except:
                print(" - - ERROR TAGGING with getting TAG CODE...")
                print(ttx)
                pass

        c.publish()
        c.solr_publish()

        

def get_xml(save_path = "./_data_tools/solar/"):
    import_url = "https://www-old.planning.org/xml/api/APA.solar.search.migrate.ashx"
    
    # this ignores ssl errors...
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    with urlopen(import_url, context=ctx) as response:
        xml_str = response.readall().decode('utf-8')
    xml_list = ElementTree.fromstring(xml_str)
    tree = ElementTree.ElementTree(xml_list)
    tree.write(save_path + "_LIST.xml")

    for i in xml_list:

        content_url = "https://www-old.planning.org/xml/api/APA.content.migrate.ashx?ContentID=" + i.text
        with urlopen(content_url, context=ctx) as response:
            xml_str = response.readall().decode('utf-8')
            xml_element = ElementTree.fromstring(xml_str)
            tree = ElementTree.ElementTree(xml_element)
            tree.write(save_path + i.text + ".xml")
            print("WROTE FILE: " + i.text)



def create_tags():
    tt_density, created = TagType.objects.get_or_create(code="PLACE_DENSITY")
    tt_density.title = "Population Density"
    tt_density.description = "Population density of the place associated with the resource."
    tt_density.save()

    tt_population, created = TagType.objects.get_or_create(code="PLACE_POPULATION_RANGE")
    tt_population.title = "Population Range"
    tt_population.save()

    tt_place, created = TagType.objects.get_or_create(code="PLACE_TYPE")
    tt_place.title = "Type of Place"
    tt_place.description = "Type of place associated with the resource."
    tt_place.save()

    tt_tool, created = TagType.objects.get_or_create(code="KNOWLEDGEBASE_TOOL")
    tt_tool.title = "Tool Type"
    tt_tool.description = "The type of planning tool represented by the resource."
    tt_tool.save()

    tt_solar, created = TagType.objects.get_or_create(code="KNOWLEDGEBASE_SOLAR_PRACTICE")
    tt_solar.title = "Solar Practice"
    tt_solar.description = "The specific solar energy issue(s) that the resource addresses."
    tt_solar.save()

    # ---------------------------------------------------------------------------------------------------------

    # 3007    PLACE_DENSITY   NULL    RURAL   A   <1,000/square mile
    t, created = Tag.objects.get_or_create(code="RURAL", tag_type=tt_density)
    t.sort_number = 1
    t.title="<1,000/square mile"
    t.save()

    # 3008    PLACE_DENSITY   NULL    URBAN_LOW   A   1,000-2,999/square mile
    t, created = Tag.objects.get_or_create(code="URBAN_LOW", tag_type=tt_density)
    t.sort_number = 2
    t.title="1,000-2,999/square mile"
    t.save()

    # 3009    PLACE_DENSITY   NULL    URBAN_MEDIUM    A   3,000-4,999/square mile
    t, created = Tag.objects.get_or_create(code="URBAN_MEDIUM", tag_type=tt_density)
    t.sort_number = 3
    t.title="3,000-4,999/square mile"
    t.save()

    # 3010    PLACE_DENSITY   NULL    URBAN_HIGH  A   >5,000/square mile
    t, created = Tag.objects.get_or_create(code="URBAN_HIGH", tag_type=tt_density)
    t.sort_number = 4
    t.title=">5,000/square mile"
    t.save()

    # ---------------------------------------------------------------------------------------------------------

    # 3019    RESOURCE_TOOL   NULL    PLAN_COMPREHENSIVE  A   Comprehensive Plan
    t, created = Tag.objects.get_or_create(code="PLAN_COMPREHENSIVE", tag_type=tt_tool)
    t.title="Comprehensive Plan"
    t.save()

    # 3020    RESOURCE_TOOL   NULL    PLAN_SUBAREA    A   Subarea Plan
    t, created = Tag.objects.get_or_create(code="PLAN_SUBAREA", tag_type=tt_tool)
    t.title="Subarea Plan"
    t.save()

    # 3021    RESOURCE_TOOL   NULL    PLAN_FUNCTIONAL A   Sustainability Plan, Energy Plan, Climate Plan
    t, created = Tag.objects.get_or_create(code="PLAN_FUNCTIONAL", tag_type=tt_tool)
    t.title="Sustainability Plan, Energy Plan, Climate Plan"
    t.save()

    # 3022    RESOURCE_TOOL   NULL    DEVELOPMENT_REGULATIONS A   Development Regulations
    t, created = Tag.objects.get_or_create(code="DEVELOPMENT_REGULATIONS", tag_type=tt_tool)
    t.title="Development Regulations"
    t.save()

    # 3023    RESOURCE_TOOL   NULL    DESIGN_GUIDELINES   A   Design Guidelines
    t, created = Tag.objects.get_or_create(code="DESIGN_GUIDELINES", tag_type=tt_tool)
    t.title="Design Guidelines"
    t.save()

    # 3024    RESOURCE_TOOL   NULL    MODEL_REGULATIONS   A   Model Development Regulations or Plan Policy Statements
    t, created = Tag.objects.get_or_create(code="MODEL_REGULATIONS", tag_type=tt_tool)
    t.title="Model Development Regulations or Plan Policy Statements"
    t.save()

    # 3025    RESOURCE_TOOL   NULL    DEVELOPMENT_GUIDE   A   Development Guide
    t, created = Tag.objects.get_or_create(code="DEVELOPMENT_GUIDE", tag_type=tt_tool)
    t.title="Development Guide"
    t.save()
    
    # 3026    RESOURCE_TOOL   NULL    MAP A   A Map
    t, created = Tag.objects.get_or_create(code="MAP", tag_type=tt_tool)
    t.title="A Map"
    t.save()

    # ---------------------------------------------------------------------------------------------------------

    # 3027    SOLAR_PRACTICE  NULL    ACCESSORY_SOLAR A   Supports Accessory Solar Energy Use
    t, created = Tag.objects.get_or_create(code="ACCESSORY_SOLAR", tag_type=tt_solar)
    t.title="Supports Accessory Solar Energy Use"
    t.save()

    # 3028    SOLAR_PRACTICE  NULL    PRIMARY_SOLAR   A   Supports Primary Solar Energy Use
    t, created = Tag.objects.get_or_create(code="PRIMARY_SOLAR", tag_type=tt_solar)
    t.title="Supports Primary Solar Energy Use"
    t.save()
    
    # 3029    SOLAR_PRACTICE  NULL    SOLAR_ACCESS    A   Supports Solar Access Protections
    t, created = Tag.objects.get_or_create(code="SOLAR_ACCESS", tag_type=tt_solar)
    t.title="Supports Solar Access Protections"
    t.save()

    # 3030    SOLAR_PRACTICE  NULL    SOLAR_SITING    A   Supports Solar Siting
    t, created = Tag.objects.get_or_create(code="SOLAR_SITING", tag_type=tt_solar)
    t.title="Supports Solar Siting"
    t.save()

    # 3031    SOLAR_PRACTICE  NULL    SOLAR_HOMES A   Supports Solar-Ready Homes
    t, created = Tag.objects.get_or_create(code="SOLAR_HOMES", tag_type=tt_solar)
    t.title="Supports Solar-Ready Homes"
    t.save()

    # 3032    SOLAR_PRACTICE  NULL    COMPETING_PRIORITIES    A   Addresses Competing Priorities
    t, created = Tag.objects.get_or_create(code="COMPETING_PRIORITIES", tag_type=tt_solar)
    t.title="Addresses Competing Priorities"
    t.save()

    # 3033    SOLAR_PRACTICE  NULL    CCR_LIMITS  A   Limits Covenants, Conditions, and Restrictions
    t, created = Tag.objects.get_or_create(code="CCR_LIMITS", tag_type=tt_solar)
    t.title="Limits Covenants, Conditions, and Restrictions"
    t.save()

    # ---------------------------------------------------------------------------------------------------------

    # 3092    PLACE_TYPE  NULL    CENSUS_CITY A   City
    t, created = Tag.objects.get_or_create(code="CENSUS_CITY", tag_type=tt_place)
    t.title="City"
    t.save()

    # 3093    PLACE_TYPE  NULL    COUNTY  A   County
    t, created = Tag.objects.get_or_create(code="COUNTY", tag_type=tt_place)
    t.title="County"
    t.save()

    # # 3094    PLACE_TYPE  NULL    CENSUS_URBANAREA    A   Urban Area
    
    # 3095    PLACE_TYPE  NULL    STATE   A   State
    t, created = Tag.objects.get_or_create(code="STATE", tag_type=tt_place)
    t.title="State"
    t.save()

    # 3096    PLACE_TYPE  NULL    CENSUS_REGION   A   US Region
    t, created = Tag.objects.get_or_create(code="CENSUS_REGION", tag_type=tt_place)
    t.title="US Region"
    t.save()

    # # 3097    PLACE_TYPE  NULL    COUNTRY A   Country
    # # 3098    PLACE_TYPE  NULL    INTERNATIONAL_CITY  A   International City
    # # 3099    PLACE_TYPE  NULL    INTERNATIONAL_PROVINCE  A   International Province
    # # 3100    PLACE_TYPE  NULL    WORLD_REGION    A   International Region
    # # 3101    PLACE_TYPE  NULL    OTHER   A   Other Region

    # ---------------------------------------------------------------------------------------------------------

    # 3102    PLACE_POPULATION_RANGE  NULL    LESS_25K    A   <25K    1
    t, created = Tag.objects.get_or_create(code="LESS_25K", tag_type=tt_population)
    t.sort_number = 1
    t.title="<25K"
    t.save()

    # 3103    PLACE_POPULATION_RANGE  NULL    25K_100K    A   25K to 100K 2
    t, created = Tag.objects.get_or_create(code="25K_100K", tag_type=tt_population)
    t.sort_number = 2
    t.title="25K to 100K"
    t.save()

    # 3104    PLACE_POPULATION_RANGE  NULL    100K_250K   A   100K to 250K    3
    t, created = Tag.objects.get_or_create(code="100K_250K", tag_type=tt_population)
    t.sort_number = 3
    t.title="100K to 250K"
    t.save()

    # 3105    PLACE_POPULATION_RANGE  NULL    250K_PLUS   A   250K+   4
    t, created = Tag.objects.get_or_create(code="250K_PLUS", tag_type=tt_population)
    t.sort_number = 4
    t.title="250K+"
    t.save()



def import_paces():
    # TO DO... node function + stored procedures needed ???????
    # OR... read gov CSV via python and loop through to create model instances
    pass


def import_solar(re_import=False):
    pass
    # TO DO... add 8,000,000 to old Content id from solar db
    # import through the XML / c1 functions
