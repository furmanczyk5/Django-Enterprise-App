from pages.models import Page, LandingPage

# script to get all root landing pages
# ps = Page.objects.filter(content_area="LANDING", parent_landing_master__content_live__code="ROOT", publish_status="PUBLISHED").order_by("master_id")

# CONTENT_AREAS = (
#     ("NONE", "Uncategorized pages"),
#     ("MEMBERSHIP", "Membership"),
#     ("KNOWLEDGE_CENTER", "Knowledge Center"),
#     ("CONFERENCES", "Conferences and Meetings"),
#     # ("RESEARCH", "Research and PAS"), # research is broken out from knowledge center in order to help organize content management assignments/access
#     ("AICP", "AICP"),
#     ("POLICY", "Policy and Advocacy"),
#     ("CAREER", "Career Center"),
#     ("OUTREACH", "Community Outreach"),
#     ("CONNECT", "Connect with APA"),
#     ("ABOUT", "About"),
#     # separate content areas???
#     # ("CHAPTERS", "Chapters"),
#     # ("DIVISIONS", "Divisions"),
# )

MAX_RECURSIVE_DEPTH = 6

def get_content_area_landing_pages():
    CONTENT_AREAS_LANDING_PAGES = [
        ("MEMBERSHIP", LandingPage.objects.filter(master_id=9022797)), # Membership
        ("KNOWLEDGE_CENTER", LandingPage.objects.filter(master_id=9026570)), # Knowledge Center
        ("CONFERENCES", LandingPage.objects.filter(master_id=9026571)), # Conferences and Meetings
        ("AICP", LandingPage.objects.filter(master_id=9021558)), # AICP Certification
        ("POLICY", LandingPage.objects.filter(master_id=9025867)), # Policy and Advocacy
        ("CAREER", LandingPage.objects.filter(master_id=9022695)), # Career Center
        ("OUTREACH", LandingPage.objects.filter(master_id=9029150)), # Community Outreach
        ("CONNECT", LandingPage.objects.filter(master_id=9047407)), # Connect with APA
        ("ABOUT", LandingPage.objects.filter(master_id=9021543)), # About APA

        # Others
        ("CAREER", LandingPage.objects.filter(master_id=9022695)), # Jobs and Practice
        ("KNOWLEDGE_CENTER", LandingPage.objects.filter(master_id=9022292)), # Education
        ("KNOWLEDGE_CENTER", LandingPage.objects.filter(master_id=9026084)), # Resources
    ]
    return CONTENT_AREAS_LANDING_PAGES


def print_with_depth(depth, *args): # depth is int > 0
    print_args = ["" for i in range(0, depth)] + list(args)
    print(*print_args)

def assign_content_area_recursive(content_area, page, depth=0, parent_history=[]):

    print_with_depth(depth, "ENTERING recursive depth {0}, {1}".format(depth, page))

    if page.content_area != content_area:
        print_with_depth(depth, ">>>>>>>>>>> changing content_area: {0}, {1}".format(content_area, page) )
        page.content_area = content_area
        page.save()

    child_pages = Page.objects.filter(publish_status=page.publish_status, parent_landing_master_id=page.master_id)
    new_parent_history = parent_history + [cp.id for cp in child_pages] # will prevent recursive loops!
    for cp in child_pages:
        if depth < MAX_RECURSIVE_DEPTH and cp.id not in parent_history:
            assign_content_area_recursive(content_area, cp, depth=depth+1, parent_history=new_parent_history)

    print_with_depth(depth, "EXITING recursive depth {0}, {1}".format(depth, page))

    if depth == 0:
        print("")
        print("")


# RUN THIS ONE
def fix_landing_records():
    """ FIXES THE PROBLEM WITH CONTENT_AREA = "LANDING" pages"""
    content_area_landing_page_tuple_list = get_content_area_landing_pages()
    for landing_page_tuple in content_area_landing_page_tuple_list:
        for landing_page_tuple_version in landing_page_tuple[1]:
            assign_content_area_recursive(landing_page_tuple[0], landing_page_tuple_version)
    
    print("")
    print("")
    print("Updating remaining Landing Pages")

    # Now that these are updated, catch the remaining content_area = "LANDING"
    Page.objects.filter(content_area="LANDING").update(content_area="NONE")
    print("")
    print("")

    print("FINISHED!")
    print("")
    print("")


# ALL TOP LEVEL LANDING PAGES
# Page.objects.filter(content_area="LANDING", parent_landing_master__content__code="ROOT")

# ALL WITH WRONG content_area
# Page.objects.filter(content_area="LANDING")





