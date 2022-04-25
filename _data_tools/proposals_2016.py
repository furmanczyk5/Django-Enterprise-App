import django
django.setup()

from events.models import *
from content.models import *

def add_question(code, title, question_type="LONG_TEXT", description="", help_text="", required=False):
    q, q_created = SubmissionQuestion.objects.get_or_create(code=code, defaults={"title":title})
    q.title = title
    q.question_type = question_type
    q.description = description
    q.help_text = help_text
    q.required = required
    q.save()

def add_category(code, title, description="", question_codes=[]):
    c, created = SubmissionCategory.objects.get_or_create(code=code, defaults={"title":title})
    c.title = title
    c.description = description
    c.questions.clear()
    for q in question_codes:
        question = SubmissionQuestion.objects.get(code=q)
        c.questions.add(question)
    c.save()

def add_tag_type(code, title, description=""):
    tt, created = TagType.objects.get_or_create(code=code, defaults={"title":title})
    tt.title = title
    tt.description = description
    tt.save()

def add_tag(code, title, tag_type_code, description=""):
    tag_type = TagType.objects.get(code=tag_type_code)
    t, created = Tag.objects.get_or_create(code=code, defaults={"title":title, "tag_type":tag_type})
    t.tag_type = tag_type
    t.title = title
    t.description = description
    t.save()



def add_questions():

    # questions...
    add_question(code="EVENTS_NATIONAL_PROPOSAL_LEARNING", 
        title="Learning Objectives",
        question_type="LONG_TEXT",
        description="",
        help_text="3 required",
        required=True)
    add_question(code="EVENTS_NATIONAL_PROPOSAL_CASE", 
        title="Case Studies",
        question_type="LONG_TEXT",
        description="If your session includes examples and case studies, indicate the community, the significance, and the dates of the case studies or examples.",
        help_text="Research that supports your session.",
        required=False)
    add_question(code="EVENTS_NATIONAL_PROPOSAL_RESEARCH", 
        title="Research",
        question_type="LONG_TEXT",
        description="Indicate any specific research that applies to your session proposal.",
        help_text="",
        required=False)
    add_question(code="EVENTS_NATIONAL_PROPOSAL_SKILLS", 
        title="What information and skills will people take back to their own community?",
        question_type="LONG_TEXT",
        description="",
        help_text="",
        required=False)
    add_question(code="EVENTS_NATIONAL_PROPOSAL_OUTLINE", 
        title="Outline",
        question_type="LONG_TEXT",
        description="Rough agenda of your session with estimated minutes for each section.",
        help_text="",
        required=False)
    add_question(code="EVENTS_NATIONAL_PROPOSAL_KNOWLEDGE", 
        title="Skill or knowledge acquired by attendees",
        question_type="LONG_TEXT",
        description="",
        help_text="",
        required=False)
    add_question(code="EVENTS_NATIONAL_PROPOSAL_HANDOUTS", 
        title="Description of handouts", 
        question_type="LONG_TEXT",
        description="Describe any resource materials you will provide for attendees.",
        help_text="",
        required=False)
    add_question(code="EVENTS_NATIONAL_PROPOSAL_AUDIENCE", 
        title="Who is your audience?",
        question_type="LONG_TEXT",
        description="",
        help_text="",
        required=False)

    # mobile workshop questions
    add_question(code="EVENTS_NATIONAL_PROPOSAL_MOBILE_STOPS", 
        title="Mobile Workshop stops or highlights (Sample Itinerary)",
        question_type="LONG_TEXT",
        description="",
        help_text="",
        required=False)
    add_question(code="EVENTS_NATIONAL_PROPOSAL_MOBILE_DURATION", 
        title="Workshop Duration (number of hours from door to door)", 
        question_type="SHORT_TEXT",
        description="All mobile workshops start and finish at the convention center. Please tell us how many hours we should schedule for your workshop.",
        help_text="",
        required=False)
    add_question(code="EVENTS_NATIONAL_PROPOSAL_MOBILE_SCHEDULE", 
        title="Workshop Schedule:",
        question_type="LONG_TEXT",
        description="Please let us know the best day (or days) to schedule your mobile workshop between Saturday, April 2 and Tuesday, April 5th, and if you have a preference between a morning or an afternoon departure.",
        help_text="",
        required=False)
    add_question(code="EVENTS_NATIONAL_PROPOSAL_MOBILE_CAPACITY", 
        title="Capacity of workshop",
        question_type="SHORT_TEXT",
        description="How many attendees can you accommodate on your workshop?",
        help_text="",
        required=False)
    add_question(code="EVENTS_NATIONAL_PROPOSAL_MOBILE_CIRCUMSTANCES", 
        title="Special Circumstances: YES/NO",
        question_type="LONG_TEXT",
        description="Does your workshop have special circumstances which require specialized coordination with APA (such as a required security clearance, or special attendee dress code)? If so, please indicate what is required.",
        help_text="",
        required=False)
    add_question(code="EVENTS_NATIONAL_PROPOSAL_MOBILE_BUDGET", 
        title="Budgeted Expenses per Person",
        question_type="LONG_TEXT",
        description="APA will reimburse you for approved items that are budgeted into your workshop. Please detail all expected expenses which may include snacks, lunch, entrance or tour fees, transportation costs (not motorcoach rental), etc.",
        help_text="",
        required=False)
    add_question(code="EVENTS_NATIONAL_PROPOSAL_MOBILE_TRANSPORT", 
        title="Mode of Transportation",
        question_type="LONG_TEXT",
        description="Please let us know what your mode of transportation will be. Available options include: Motorcoach, Walking, Running, Bicycle, Public Transit (light rail or bus), etc. APA will arrange all motorcoach rentals. All other modes must be arranged by the workshop organizer.",
        help_text="",
        required=False)


def add_categories():

    add_category(code="EVENTS_NATIONAL_PROPOSAL_GEN", title="Session",
        description="A 75-minute presentation covering every facet of planning.",
        question_codes=["EVENTS_NATIONAL_PROPOSAL_LEARNING",
                        "EVENTS_NATIONAL_PROPOSAL_CASE",
                        "EVENTS_NATIONAL_PROPOSAL_RESEARCH",
                        "EVENTS_NATIONAL_PROPOSAL_SKILLS",
                        "EVENTS_NATIONAL_PROPOSAL_OUTLINE"])

    add_category(code="EVENTS_NATIONAL_PROPOSAL_DIVE", title="Deep Dive Session",
        description="A more workshop-like approach with lectures, hands-on experience, extensive interaction, and useful resources for participants.",
        question_codes=["EVENTS_NATIONAL_PROPOSAL_LEARNING",
                        "EVENTS_NATIONAL_PROPOSAL_CASE",
                        "EVENTS_NATIONAL_PROPOSAL_KNOWLEDGE",
                        "EVENTS_NATIONAL_PROPOSAL_HANDOUTS",
                        "EVENTS_NATIONAL_PROPOSAL_OUTLINE",
                        "EVENTS_NATIONAL_PROPOSAL_AUDIENCE"])

    add_category(code="EVENTS_NATIONAL_PROPOSAL_DISCUSSION", title="Facilitated Discussion",
        description="Allows for informal, intensive discussion among groups of people who share ideas or have situations in common.",
        question_codes=["EVENTS_NATIONAL_PROPOSAL_LEARNING",
                        "EVENTS_NATIONAL_PROPOSAL_CASE",
                        "EVENTS_NATIONAL_PROPOSAL_RESEARCH",
                        "EVENTS_NATIONAL_PROPOSAL_SKILLS",
                        "EVENTS_NATIONAL_PROPOSAL_OUTLINE"])

    add_category(code="EVENTS_NATIONAL_PROPOSAL_FUNNY", title="Fast and Funny",
        description="These 7-minute presentations are typically based on personal projects or short visual essays. Catch the flavor of planning today in a format that makes you laugh while it makes you think.",
        question_codes=["EVENTS_NATIONAL_PROPOSAL_LEARNING",
                        "EVENTS_NATIONAL_PROPOSAL_CASE",
                        "EVENTS_NATIONAL_PROPOSAL_RESEARCH",
                        "EVENTS_NATIONAL_PROPOSAL_SKILLS",
                        "EVENTS_NATIONAL_PROPOSAL_OUTLINE"])

    
    add_category(code="EVENTS_NATIONAL_PROPOSAL_STUDENT_FUNNY", title="Student Fast and Funny",
        description="Students share their work, such as their capstone projects, in a funny 7-minute presentation.",
        question_codes=["EVENTS_NATIONAL_PROPOSAL_LEARNING",
                        "EVENTS_NATIONAL_PROPOSAL_CASE",
                        "EVENTS_NATIONAL_PROPOSAL_RESEARCH",
                        "EVENTS_NATIONAL_PROPOSAL_SKILLS",
                        "EVENTS_NATIONAL_PROPOSAL_OUTLINE"])

    add_category(code="EVENTS_NATIONAL_PROPOSAL_POSTER", title="Poster",
        description="APA's members present their planning research, projects, and case studies in visual form.",
        question_codes=["EVENTS_NATIONAL_PROPOSAL_LEARNING",
                        "EVENTS_NATIONAL_PROPOSAL_CASE",
                        "EVENTS_NATIONAL_PROPOSAL_RESEARCH",
                        "EVENTS_NATIONAL_PROPOSAL_SKILLS"])

    add_category(code="EVENTS_NATIONAL_PROPOSAL_STUDENT_POSTER", title="Student Poster",
        description="Students present their capstone projects or other research in visual form.",
        question_codes=["EVENTS_NATIONAL_PROPOSAL_LEARNING",
                        "EVENTS_NATIONAL_PROPOSAL_CASE",
                        "EVENTS_NATIONAL_PROPOSAL_RESEARCH",
                        "EVENTS_NATIONAL_PROPOSAL_SKILLS"])

    add_category(code="EVENTS_NATIONAL_PROPOSAL_EMERGE", title="Emerging Professionals Mini Session",
        description="Any proposal that targets an audience of students and young planners. We encourage you to ‘think outside the box’ of a traditional session and develop innovative programs to encourage discussion, networking and career development.",
        question_codes=["EVENTS_NATIONAL_PROPOSAL_LEARNING",
                        "EVENTS_NATIONAL_PROPOSAL_CASE",
                        "EVENTS_NATIONAL_PROPOSAL_RESEARCH",
                        "EVENTS_NATIONAL_PROPOSAL_SKILLS",
                        "EVENTS_NATIONAL_PROPOSAL_OUTLINE"])

    add_category(code="EVENTS_NATIONAL_PROPOSAL_MOBILE", title="Mobile Workshop",
        description="Allows attendees an opportunity to visit planning projects throughout the host city and surrounding region.",
        question_codes=["EVENTS_NATIONAL_PROPOSAL_LEARNING",
                        "EVENTS_NATIONAL_PROPOSAL_MOBILE_STOPS",
                        "EVENTS_NATIONAL_PROPOSAL_SKILLS",
                        "EVENTS_NATIONAL_PROPOSAL_MOBILE_DURATION",
                        "EVENTS_NATIONAL_PROPOSAL_MOBILE_SCHEDULE",
                        "EVENTS_NATIONAL_PROPOSAL_MOBILE_CAPACITY",
                        "EVENTS_NATIONAL_PROPOSAL_MOBILE_CIRCUMSTANCES",
                        "EVENTS_NATIONAL_PROPOSAL_MOBILE_BUDGET",
                        "EVENTS_NATIONAL_PROPOSAL_MOBILE_TRANSPORT"])


def add_tag_types():

    add_tag_type(code="NPC_TOPIC",
        title="National Conference Topic - 2016",
        description=""
        )

    add_tag_type(code="NPC_TRACK_2016",
        title="National Conference Track - 2016",
        description='Tracks help focus a portion of the conference program on selected current topics and provide a "conference within a conference." These topics help call attention to emerging issues and guide planning practice. Not all sessions will fit into a track, as planning is broad field with many topical areas.'
        )


def add_tags():

    add_tag(code="NPC_TOPIC_ARTS",
        title="Arts and Culture",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_AGING",
        title="Aging",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_BLACK",
        title="Black Community Planning",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_CAREER",
        title="Career Development",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_CLIMATE",
        title="Climate",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_REVITALIZATION",
        title="Community Revitalization",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_COMPREHENSIVE",
        title="Comprehensive Planning",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_COUNTY",
        title="County Planning",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_DIVERSITY",
        title="Diversity and Social Equity",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_DEVELOPMENT",
        title="Development",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_ECONOMIC",
        title="Economic Development",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_FINANCE",
        title="Finance",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_EDUCATION",
        title="Education",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_ENVIRONMENT",
        title="Environment",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_ENERGY",
        title="Energy",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_ETHICS",
        title="Ethics",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_FEDERAL",
        title="Federal Planning",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_FOOD",
        title="Food Systems",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_GAYS",
        title="Gays and Lesbians",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_HAZARDS",
        title="Hazards",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_HEALTH",
        title="Health",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_HISTORIC",
        title="Historic Preservation",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_URBAN_DESIGN",
        title="Urban Design & Preservation",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_HOUSING",
        title="Housing and Community Development",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_INDIGENOUS",
        title="Indigenous Planning",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_INTERNATIONAL",
        title="International",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_LATINO",
        title="Latino Planning",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_LAW",
        title="Law",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_MANAGEMENT",
        title="Management",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_NEW_URBANISM",
        title="New Urbanism",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_PARKS",
        title="Parks, Open Space, and Greenways",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_PRIVATE",
        title="Private Practice",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_METHODS",
        title="Planning Methods",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_PUBLIC",
        title="Public Participation",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_REGIONAL",
        title="Regional Planning",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_RURAL",
        title="Small Town and Rural",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_SUBURBAN",
        title="Suburban Planning",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_SUSTAINABILITY",
        title="Sustainability",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_TECH",
        title="Technology",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_STREET",
        title="Transportation: Streets and Corridors",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_AIRPORT",
        title="Transportation: Airports",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_PEDESTRIAN",
        title="Transportation: Biking, Pedestrian",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_TRANSIT",
        title="Transportation: Transit",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_URBAN",
        title="Urban Design",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_WOMEN",
        title="Women and Planning",
        tag_type_code="NPC_TOPIC",
        description="")
    add_tag(code="NPC_TOPIC_ZONING",
        title="Zoning, Codes, and Ordinances",
        tag_type_code="NPC_TOPIC",
        description="")



    add_tag(code="NPC_TRACK_2016_ENERGY",
        title="Evolving Solar, Wind, and Energy Planning",
        tag_type_code="NPC_TRACK_2016",
        description="How we harvest and use energy plays an important role in how communities develop and sustain themselves. The last decade has brought many technical innovations, and utility companies themselves are often leading the way in creating sustainable practices. Delve into creative energy planning (this might include utilities) and see what is happening across the country. Session proposals are encouraged that demonstrate the role of planning in supporting sustainable energy.")
    add_tag(code="NPC_TRACK_2016_HOUSING",
        title="Housing Trends",
        tag_type_code="NPC_TRACK_2016",
        description="It’s been a roller coaster ride for housing. As America has emerged from the recession, the landscape of housing has changed. Proposers may wish to examine what is happening in the market place, others will look at the challenges to providing adequate, varied, and affordable housing for all members of the community. Housing is central to the well-being of a community.")
    add_tag(code="NPC_TRACK_2016_RECESSION",
        title="Lessons from the Recession",
        tag_type_code="NPC_TRACK_2016",
        description="The great recession had a broad and historic impact on communities and the practice of planning. How has planning and how have communities changed since the recession? There are many dimensions to this change with economic development being one of the most important. Session proposals may examine management practices, economic development, new services provided by planners, or municipal finance to suggest a few. Sessions will take stock of where we are and what we have learned about how community planning should proceed in the future.")
    add_tag(code="NPC_TRACK_2016_NUTS",
        title="Nuts and Bolts",
        tag_type_code="NPC_TRACK_2016",
        description="This track will focus on essential planning skills. Consider what planners need to know for their day-to-day jobs and what skill building you might provide in a session. Whether it’s zoning, management, implementing site planning, or developing a new plan, this track will help new planners and provide a refresher for experienced planners. Here is your opportunity to help your colleagues solve common problems and master essential skills.")
    add_tag(code="NPC_TRACK_2016_REGULATORY",
        title="Planning and the Regulatory Realm",
        tag_type_code="NPC_TRACK_2016",
        description="The regulatory landscape is a mix of federal initiatives, case law challenges, local land use regulation development, and state policies. Session proposals may address how states are creating legislation in the absence of Congressional leadership. Other proposals may focus on the U.S. Supreme Court and federal district court rulings. Yet other proposals may consider regulation developed at the local level. The track will explore what’s new, emerging trends and their implications, and how regulatory tools are being used in the current environment.")
    add_tag(code="NPC_TRACK_2016_POPULATION",
        title="Planning for a More Dynamic Population",
        tag_type_code="NPC_TRACK_2016",
        description="The U.S. population is dynamic. Not only are traditional categories of households changing, but where and how people live is changing as well. Session proposals may consider how planning is responding to new immigrants or new life-style choices, such as transportation choices. Not all immigrant communities are the same. Not all groups conform to one pattern of behavior. Not all communities, such as suburbs, are the same as they were 25 years ago. Sessions will explore what makes our population dynamic, how communities respond to rapid changes, and how planning can address these issues.")
    add_tag(code="NPC_TRACK_2016_GENERATIONS",
        title="Planning for All Generations",
        tag_type_code="NPC_TRACK_2016",
        description="It is critical to engage all generations and populations in planning for their needs and goals. Among the things session proposals can consider are the issues of the wage-earner population and how it is declining as the retired population grows. This track looks at the trends and implications of varied populations and the manifestations of generational shifts in opportunity, attitude, and living choice.")
    add_tag(code="NPC_TRACK_2016_HEALTH",
        title="Public Health and Planning for Resilience",
        tag_type_code="NPC_TRACK_2016",
        description="How do health and resilience come together and how should your community consider this issue? Health is now a significant driver of planning. Sessions will examine how planners and professional colleagues are creating healthy communities and populations that can withstand changes in the economy and natural hazards. Whether the issue is research, policy, plan implementation, or measurement of actions, consider proposing a session on current health and planning practice.")
    add_tag(code="NPC_TRACK_2016_REAL_ESTATE",
        title="Real Estate and Finance and Role of Planning",
        tag_type_code="NPC_TRACK_2016",
        description="The real estate market affects communities in ways not always well understood by planners. Development and municipal finance have changed considerably over the past few years. Therefore, it is time for planners to assess what is happening and what the dynamic of market really are. Session proposals are encouraged that make the connection to planning.")
    add_tag(code="NPC_TRACK_2016_WATER",
        title="Water and Community Planning",
        tag_type_code="NPC_TRACK_2016",
        description="Partner organizations will work with APA planners to explore issues of water and how to develop effective multi-departmental, inter-disciplinary plans for water. Community planners and water resource professionals can significantly impact each other’s outcomes, but traditionally have operated in separate spheres. The fractured nature of water governance, the layers of regulations for community planning and water planning, the lack of a shared vocabulary, the lack of understanding of each other’s objectives — all create significant obstacles to achieve sustainable, resilient communities and water resources. Consider proposing a session on how to integrate water planning and management.")
    add_tag(code="NPC_TRACK_2016_LOCAL_HOST",
        title="Local Host Committee",
        tag_type_code="NPC_TRACK_2016",
        description="")

    

        
def go():
    add_questions()
    add_categories()
    add_tag_types()
    add_tags()
    


