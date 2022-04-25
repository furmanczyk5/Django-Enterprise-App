import django
django.setup()

import warnings
warnings.filterwarnings('ignore')

import uuid

from django.conf import settings
from django.contrib.auth.models import Group

from urllib.request import urlopen
# from urllib import parse
# from xml.dom import minidom
from xml.etree import ElementTree # MUCH better than DOM!!!

from content.models import Content, MasterContent, Section, MenuItem

from content.models import *
from pages.models import *
from publications.models import *

IMPORT_URLS = [
    # "/aboutapa/",
    # "/divisions/",
    # "/divisions/blackcommunity/newsletter/",
    # "/china/nextgenerationforum.htm",
    # "/apaataglance/",
    # "/leadership/",
    # "/members/",
    # "/members/budget/"
    # "/apaataglance/history.htm",
    # "/apaataglance/greenteam/",
    # "/planning/2015/jan/",
    "/planning/2016/feb/",
    # "/newsreleases/"
    # "/" # entire site!!!!!
] 

EXCLUDE_URLS = [
    "/conference/",
    "/events/",
    "/cm/",
    "/annualreport/",
    "/chicago/welcome/",
    "/imagelibrary/",
    "/mobileapp/",
    "/webinar/",
    # app pages (either converted to django or outdated):
    "/certification/exam/",
    "/join/form/",
    "/nationalconference/kiosk/",
    "/practicingplanner/",
    "/myapa/",
]


START_NUMBER=0

END_NUMBER = 9000

API_KEY = "y03xp0rt"

PAGES_URL = "https://www.planning.org/xml/api/APASTAFF.export.pages.ashx"

PAGE_URL = "https://www.planning.org/xml/api/APASTAFF.export.page.ashx"

SECTION_IDS = [] # to keep track globally of which sections have been created

S3_ROOT = "https://planning-org-uploaded-media.s3.amazonaws.com/legacy_resources"

STATIC_FILETYPES = [".jpg",".gif",".png",".pdf",".xls",".xslx",".doc",".docx",".ppt",".pptx",".txt",
        ".mov",".avi",".mpeg",".mpg"]

CONTENT_TYPE_ASSIGNMENTS = (
    ("/aboutapa/", AboutPage),
    ("/aboutplanning/", AboutPage),
    # ("/advertise/", Page), # ANYTHING MORE SPECIFIC?
    ("/advocacy/", PolicyPage),
    ("/aicp/", AICPPage),
    ("/amicus/", PolicyPage),
    ("/annualreport/", AboutPage),
    ("/apaataglance/", AboutPage),
    ("/asc/", AICPPage),
    ("/audioconference/", ConferencesPage),
    ("/awards/", OutreachPage),
    ("/benefits/", MembershipPage),
    ("/books/", KnowledgeCenterPage),
    ("/burnham/", ConferencesPage),
    ("/certification/", AICPPage),
    ("/chapters/", ConnectPage),
    ("/china/", OutreachPage),
    ("/cityparks/", ResearchPage),
    ("/cm/", AICPPage),
    ("/commissioners/", MembershipPage),
    # ("/communicationsguide/", Page),
    ("/community/", OutreachPage),
    ("/communityassistance/", OutreachPage),
    ("/conference/", ConferencesPage),
    ("/consultants/", CareerPage),
    ("/diversity/", OutreachPage),
    ("/divisions/", ConnectPage),
    ("/earlycareer/", ConnectPage),
    ("/education/", KnowledgeCenterPage),
    ("/elections/", AboutPage),
    ("/emergingprofessionals/", ConnectPage),
    ("/ep/", ConnectPage),
    ("/essay/", ConnectPage),
    ("/ethics/", AboutPage),
    ("/events/", ConferencesPage),
    ("/faicp/", AICPPage),
    ("/features/", AboutPage),
    ("/foundation/", ConnectPage),
    ("/getcertified/", AICPPage),
    ("/greatplaces/", OutreachPage),
    ("/growingsmart/", ResearchPage),
    ("/honors/", ConnectPage),
    ("/interact/", Article),
    ("/international/", OutreachPage),
    ("/japa/", KnowledgeCenterPage),
    ("/jobs/", CareerPage),
    ("/join/", MembershipPage),
    ("/joinapa/", MembershipPage),
    ("/katrina/", OutreachPage),
    ("/kidsandcommunity/", OutreachPage),
    ("/lbcs/", ResearchPage),
    ("/leadership/", AboutPage),
    ("/lenfant/", ConferencesPage),
    ("/library/", KnowledgeCenterPage),
    ("/media/", AboutPage),
    ("/members/", MembershipPage),
    ("/membership/", MembershipPage),
    ("/multimedia/", KnowledgeCenterPage),
    ("/nationalcenters/", ResearchPage),
    ("/ncpm/", OutreachPage),
    ("/news/", AboutPage),
    ("/newsreleases/", AboutPage),
    ("/onthejob/", CareerPage),
    ("/outreach/", OutreachPage),
    ("/partnerships/", OutreachPage),
    ("/pas/", ResearchPage),
    ("/pel/", KnowledgeCenterPage),
    ("/planificacion/", ResearchPage),
    ("/plannerspress/", KnowledgeCenterPage),
    ("/planning/open/", PlanningMagArticle),
    ("/planning/2002/", PlanningMagArticle),
    ("/planning/2003/", PlanningMagArticle),
    ("/planning/2004/", PlanningMagArticle),
    ("/planning/2005/", PlanningMagArticle),
    ("/planning/2006/", PlanningMagArticle),
    ("/planning/2007/", PlanningMagArticle),
    ("/planning/2008/", PlanningMagArticle),
    ("/planning/2009/", PlanningMagArticle),
    ("/planning/2010/", PlanningMagArticle),
    ("/planning/2011/", PlanningMagArticle),
    ("/planning/2012/", PlanningMagArticle),
    ("/planning/2013/", PlanningMagArticle),
    ("/planning/2014/", PlanningMagArticle),
    ("/planning/2015/", PlanningMagArticle),
    ("/planning/2016/", PlanningMagArticle),
    ("/planning/", PlanningMagArticle),
    ("/podcasts/", KnowledgeCenterPage),
    ("/policy/", PolicyPage),
    ("/pts/", ConferencesPage),
    ("/publications/", KnowledgeCenterPage),
    ("/readers/", KnowledgeCenterPage),
    ("/research/", ResearchPage),
    ("/resilience/", OutreachPage),
    ("/resources/", KnowledgeCenterPage),
    ("/salary/", CareerPage),
    ("/sandy/", OutreachPage),
    ("/scholarships/", ConnectPage),
    ("/solar/", ResearchPage),
    ("/shortcourse/", ConferencesPage),
    ("/store/", KnowledgeCenterPage),
    ("/students/", ConnectPage),
    ("/subscribe/", KnowledgeCenterPage),
    ("/sustainingplaces/", ResearchPage),
    ("/thecommissioner/", KnowledgeCenterPage),
    ("/thenewplanner/", KnowledgeCenterPage),
    ("/tuesdaysatapa/", ConferencesPage),
    ("/volunteer/", ConnectPage),
    ("/zoningpractice/", KnowledgeCenterPage),
)

def republish_page(page):
    try:
        if page.master.content_live:
            page.publish()
            page.solr_publish()
            print("publishing to STAGING and LIVE: " + str(page.url) )
        else:
            print("publishing to STAGING (only): " + str(page.url) )
        page.publish(database_alias="staging", publish_type="DRAFT")
        page.publish(database_alias="staging")
        page.solr_publish(solr_base=settings.SOLR_STAGING)
    except Exception as e:
        print("ERROR: ==================================================")
        print(str(e))

def republish_landings():
    for p in LandingPage.objects.filter(publish_status="DRAFT", status="A"):
        republish_page(p)

def republish_all():
    for p in Page.objects.filter(publish_status="DRAFT", status="A").exclude(content_area="LANDING"):
        republish_page(p)
    for p in Publication.objects.filter(publish_status="DRAFT", status="A"):
        republish_page(p)
    for p in LandingPage.objects.filter(publish_status="DRAFT", status="A"):
        republish_page(p)
        

def menu_uuids():
    # first, fix all menu item uuids
    print("resetting menu item uuids")
    for m in MenuItem.objects.all():
        m.publish_uuid = uuid.uuid4()
        m.save()

def move_sections():
    # create (or get existing) landing pages for each section
    
    for section in Section.objects.filter(url="/planning/2016/feb/"):
    # for section in Section.objects.all():
        # existing page... convert it to landing page and assign landing_master for existing sub-content to this page
        print("Creating/assigning landing page for section: " + str(section.url) + " | " + section.title)

        landing_page = None

        if section.new_landing_page:
            landing_page = section.new_landing_page

        if section.url:
            try:
                landing_page = LandingPage.objects.get(url=section.url, publish_status="DRAFT", status="A")[0]
            except:
                try:
                    content_landing_page = Content.objects.filter(url=section.url, publish_status="DRAFT", status="A")[0]
                    # kind of a hacky way to create landing pages from normal content...
                    landing_page = LandingPage(content_ptr_id=content_landing_page.pk)
                    landing_page.__dict__.update(content_landing_page.__dict__)
                except:
                    pass

        if not landing_page:                
            landing_page = LandingPage()
            landing_page.title = section.title

        if section.code:
            landing_page.code = section.code
        landing_page.save()

        section.new_landing_page = landing_page
        section.save()

        for menuitem in MenuItem.objects.filter(section=section):
            menuitem.parent_landing_page = landing_page
            menuitem.save()

def move_content_landings():
    print("----------------------------------------------------------------------------------")
    # associate all content with the new landing pages        
    # for c in Content.objects.filter(section__isnull=False):
    for c in Content.objects.filter(section__isnull=False, url__startswith="/planning/2016/feb/"):
        print("Reassigning content: " + str(c.master.id) )
        try:
            c.parent_landing_master = LandingPageMasterContent.objects.get(id=c.section.new_landing_page.master.id) 
            c.save()
        except Exception as e:
            print("=================================")
            print("ERROR: " +str(e))
    print("----------------------------------------------------------------------------------")
    print("Assigned landing masters to all content")

# now make sure that the section heirarchy is as it was before
def landing_parents():
    for section in Section.objects.all():
        if section.parent and section.url and not section.url.startswith("/planning/2"):
            print("Reassigning parent to landing: " + section.new_landing_page.title)
            landing = section.new_landing_page
            landing.parent_landing_master = LandingPageMasterContent.objects.get(id=section.parent.new_landing_page.master.id)
            landing.save()
            landing.publish()


def fix_landings():
    planning_mag_master = LandingPageMasterContent.objects.get(id="9023166")

    for l in LandingPage.objects.filter(publish_status="DRAFT"):
        if l.url and l.url.startswith("/planning/2"):
            l.parent_landing_master = planning_mag_master
            if l.section:
                l.title = l.section.title
            l.save()
            l.publish()


        # no existing content page... create new page and ditto

def get_pages():
    pages_import_url = PAGES_URL + "?ApiKey=" + API_KEY
   
    with urlopen(pages_import_url) as response:
        xml_str = response.readall().decode('utf-8')
    xml_pages = ElementTree.fromstring(xml_str)
    return xml_pages

def sort_menus():
    all_pages = get_pages()
    for section in Section.objects.all():
        try:
            print("-----------------------------------------------------")
            print("Sorting menu for what had been section: " + section.title)
            sort_menu(section, all_pages)
        except Exception as e:
            print("ERROR: " + str(e))

def sort_menu(section, all_pages):
    # # for testing only
    # if not section:
    #     section = Section.objects.get(title="Planning February 2012")
    # if not all_pages:
    #     all_pages = get_pages()

    if section.url:
        pagedef_xml = all_pages.find(".//IPage[@FriendlyUrl='" + section.url + "']" )
        page_id = pagedef_xml.get("Id")

        page_import_url = PAGE_URL + "?ApiKey=" + API_KEY + "&PageId=" + page_id + "&PagePath=" + section.url
        
        with urlopen(page_import_url) as response:
            xml_str = response.readall().decode('utf-8')
        # print(xml_str)

        xml_doc = ElementTree.fromstring(xml_str)
        xml_section = xml_doc.find(".//Section")
        
        # ==================================================================
        # create the section record with menu items, if it doesn't already exist

        if xml_section:
            # xml_section_root = xml_section.find("Page") 
            # print(xml_section)

            xml_section_root = xml_section.find("Page") 
            # print(dir(xml_root_page))
            for i, m1 in enumerate(xml_section_root):
                m_url = m1.get("FriendlyUrl")
                for menuitem in section._menuitems_depreciated.all():
                    if menuitem.get_url() == m_url:
                        menuitem.sort_number = i
                        menuitem.save()
                        print("sorted menu item: " + menuitem.title)


def import_pages(start_number=START_NUMBER, end_number=END_NUMBER):
    print()
    print()
    print("==========================================================================================================")
    print("IMPORTING PAGES FROM C1: #" + str(start_number) + " up to #" + str(end_number) )
    print("==========================================================================================================")

    
    pages_import_url = PAGES_URL + "?ApiKey=" + API_KEY
    
    with urlopen(pages_import_url) as response:
        xml_str = response.readall().decode('utf-8')
        
    xml_pages = ElementTree.fromstring(xml_str)

    failed_nodes = []
    success_nodes = []
    skipped_nodes=[]

    counter = start_number

    # NOT PARTICULARLY ELEGANT, but it's a 1-time script anyway....
    for p in xml_pages[start_number : end_number]:
        p_url = p.get("FriendlyUrl").lower()
        p_include = False # assume guilty until proven innocent

        if p_url and not p_url.endswith("*") and not "?" in p_url and not "#" in p_url:
            p_include = True

            for u_exclude in EXCLUDE_URLS:
                if p_url.startswith(u_exclude):
                    p_include = False
                    break

            if p_include:
                p_include = False # assume guilty until proven innocent
                for u_include in IMPORT_URLS:
                    if p_url.startswith(u_include):
                        p_include = True
                        break

        if p_include:
            page_success = import_page(p.get("Id"), p_url, p.get("Title"))
            
            if page_success[0]==True:
                print("imported #" + str(counter) + ": " + p_url)
                success_nodes.append((p_url, None))
            else:
                print("FAILED: " + p_url)
                failed_nodes.append((p_url, page_success[1]))
        else:
            skipped_nodes.append((p_url, None))
            # print("skipped: " + (p_url or "(empty url)") )

        counter += 1

    print("==========================================================================================================")
    print("FINAL REPORT:")
    print("Successfully imported " + str(len(success_nodes)) + " pages!")
    # IN CASE WE WANT TO SHOW REPORT OF SKIPPED URLS
    # print("-------------------------------")
    # print(str(len(skipped_nodes)) + " page records SKIPPED:")
    # for s in skipped_nodes:
    #     print(s[0] or "(empty url)")
    print("-------------------------------")
    print(str(len(failed_nodes)) + " page records FAILED:")
    for f in failed_nodes:
        print(f[0] + " - ERROR: " + f[1])
    
    print("==========================================================================================================")



def import_page(page_id, page_path, page_title):
    try:
        success = True # assume innocent until proven guilty
        page_import_url = PAGE_URL + "?ApiKey=" + API_KEY + "&PageId=" + page_id + "&PagePath=" + page_path
        # print(page_import_url)

        with urlopen(page_import_url) as response:
            xml_str = response.readall().decode('utf-8')
        # print(xml_str)

        xml_doc = ElementTree.fromstring(xml_str)
        xml_content = xml_doc[0].find("Content")

        if not xml_content:
            return (False, "Content is empty... maybe page has been deleted?")
        
        page_type = Page
        for pt in CONTENT_TYPE_ASSIGNMENTS:
            if page_path.startswith(pt[0]):
                page_type = pt[1]
                break
        
        try:
            content_old = Content.objects.get(url=page_path, publish_status="DRAFT")
            content_old.delete()
        except:
            pass

        content, content_created = page_type.objects.get_or_create(url=page_path, publish_status="DRAFT")
        # print("created: " + str(content_created) + " | ID: " + str(content.id))

        # try:
        # THOUGHT... do we need the sitemap node at all?
        xml_section = xml_doc.find(".//Section")
        
        # ==================================================================
        # create the section record with menu items, if it doesn't already exist

        if xml_section:
            xml_section_root = xml_section.find("Page") 
            # print(dir(xml_root_page))

            section_url = xml_section_root.get("FriendlyUrl")
            section, section_created = Section.objects.get_or_create(
                url=section_url, 
                publish_status="DRAFT")

            if section_created or section.id not in SECTION_IDS:
                # then this is a new or first-time-updated section for this import run:
                SECTION_IDS.append(section.id)

                section.title = xml_section_root.get("Title")

                for m1 in xml_section_root:
                    mi1, mi1_created = MenuItem.objects.get_or_create(
                        url = m1.get("FriendlyUrl"),
                        section = section )
                    mi1.title = m1.get("Title")
                    mi1.save()
                    for m2 in m1:
                        mi2, mi2_created = MenuItem.objects.get_or_create(
                            url = m2.get("FriendlyUrl"),
                            section = section )
                        mi2.title = m2.get("Title")
                        mi2.parent = mi1
                        mi2.save()
                        for m3 in  m2:
                            mi3, mi3_created = MenuItem.objects.get_or_create(
                                url = m3.get("FriendlyUrl"),
                                section = section )
                            mi3.title = m3.get("Title")
                            mi3.parent = mi2
                            mi3.save()
                section.save()
            content.section = section

        # except:

        # ==================================================================
        # create the page title (from the c1 title... or from the h1 if it exists, and remove the h1)
        content.title = page_title

        h1_elements = xml_content.findall(".//h1")
        if h1_elements:
            content.title = h1_elements[0].text
            h1_parent = xml_doc.findall(".//*[h1]")[0]
            h1_parent.remove(h1_elements[0])

        login_groups = xml_doc[0].get("LoginGroups")

        # ==================================================================
        # fix image and static file link urls
        
        for image in xml_content.findall(".//img"):
            try:
                old_image_url = image.get("src")
                image.set("src", fix_static_url(old_image_url) )
            except:
                print("WARNING: error updating image url")
                pass

        for link in xml_content.findall(".//a"):
            try:
                old_link_url = link.get("href")
                if old_link_url and any(old_link_url.lower().endswith(ext) for ext in STATIC_FILETYPES):
                    link.set("href", fix_static_url(old_link_url) )
                elif link.get("id"):
                    # link.set("href","#")
                    link.text = " "
            except:
                print("WARNING: error updating static file download link url")
                pass



        for g in login_groups.split(","):
            try:
                group = Group.objects.get(name=g)
                content.permission_groups.add(group)
                # print("ADDED GROUP: " + str(group))
            except Group.DoesNotExist:
                pass

        # content.template = "content/newtheme/content-page-sidebar.html"

        # print(xml_content.toprettyxml())
        content.text = ElementTree.tostring(xml_content[0]) 
        # content.text = "BOO!"
        content.save()

        try:
            content.publish(database_alias="staging", publish_type="DRAFT")
            content.publish(database_alias="staging")
            # content.solr_publish(solr_base=settings.SOLR_STAGING)
        except:
            print("Content imported saved... but error posting to staging.")
            pass

        # print("==========================================================================================================")
        # print("==========================================================================================================")
        # print(xml_str)
        return (True, None)
    except  Exception as exc:
        return (False, str(exc))

def menus_add_pages():
    """
    Adds page references for menu items
    """
    for m in MenuItem.objects.all():
        if m.url:
            url = m.url.strip()
            content = Content.objects.filter(url=url, publish_status="DRAFT", status="A").first()
            if not content:
                content = Content.objects.filter(url=url + "index.htm", publish_status="DRAFT").first()
            if not content:
                print("WARNING: no content record found for menu item url: " + url)
            else:
                m.master = content.master
                m.url = None
                m.save()
                print("added page for menu item: " + m.title)
        elif not m.master:
            print("WARNING: menu item : " + m.title + " has no master or url ")

def arrange_sections():
    """
    Adds parent sections based on menu item urls
    """
    for s in Section.objects.filter(publish_status="DRAFT"):
        # get the first menu item that matches the section url that is NOT within this section...
        # assume that that is the menu item that belongs to the parent section
        mi = MenuItem.objects.filter(url=s.url).exclude(section=s).first()
        if mi:
            s.parent = mi.section
            s.save()


def fix_static_url(url):
    """
    updates static urls to point to amazon
    """
    url = url.replace("https://www.planning.org/", "/")
    return S3_ROOT + url


def mass_assign_sections(start_url, section_url=None):
    section_url = section_url or start_url
    section = Section.objects.get(url=section_url)
    for s in Section.objects.filter(url__startswith=start_url):
        if s != section:
            s.parent = section
            s.save()
            print("Assigned section " + s.title + " underneath " + section.title)

def mass_assign_content(start_url, section_url=None):
    section_url = section_url or start_url
    section = Section.objects.get(url=section_url)
    for c in Content.objects.filter(url__startswith=start_url):
        c.section = section
        c.save()
        print("Assigned page " + c.url + " underneath " + section.title)

def rearrange_sections():
    # mass_assign_sections("/planning/")
    # mass_assign_content("/asc/")
    # mass_assign_content("/ethics/")
    # mass_assign_content("/policy/guides/adopted/", "/policy/guides/")
    # mass_assign_content("/growingsmart/")
    # mass_assign_content("/greatplaces/")
    # mass_assign_content("/awards/")
    # mass_assign_content("/communityassistance/")
    # mass_assign_content("/communityassistance/teams/")
    mass_assign_content("/newsreleases/", "/news/")




