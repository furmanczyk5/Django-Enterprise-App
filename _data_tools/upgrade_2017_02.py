
# from django.contrib.auth.models import Permission, User
from myapa.models import ContactRole
from content.models import Content
from events.models import Event
from cm.models import Provider

import django
django.setup()


def update_all():
    update_templates()


def update_templates():

    Content.objects.filter(template="pages/default.html").update(template="pages/newtheme/default.html")
    Content.objects.filter(template="pages/section_overview.html").update(template="pages/newtheme/section-overview.html")
    Content.objects.filter(template="pages/landing.html").update(template="pages/newtheme/landing.html")
    Content.objects.filter(template="pages/research.html").update(template="pages/newtheme/research.html")

    Content.objects.filter(template="blog/post.html").update(template="blog/newtheme/post.html")

    Content.objects.filter(template="knowledgebase/collection.html").update(template="knowledgebase/newtheme/collection.html")
    Content.objects.filter(template="knowledgebase/resource.html").update(template="knowledgebase/newtheme/resource.html")

    Content.objects.filter(template="publications/planning_mag.html").update(template="publications/newtheme/planning-mag.html")

    Content.objects.filter(template="newtheme/store/product/details.html").update(template="store/newtheme/product/details.html")

    Content.objects.filter(template="events/newtheme/ondemand/course_details.html").update(template="events/newtheme/ondemand/course-details.html")
    Content.objects.filter(template="events/newtheme/event_details.html").update(template="events/newtheme/event-details.html")
    Content.objects.filter(template="events/newtheme/eventmulti_details.html").update(template="events/newtheme/eventmulti-details.html")

    Content.objects.filter(template="media/details.html").update(template="media/newtheme/details.html")
    Content.objects.filter(template="research_inquiries/inquiry/details.html").update(template="research_inquiries/newtheme/inquiry-details.html")

    Event.objects.filter(ticket_template="registrations/tickets/layouts/CONFERENCE_BADGE.html").update(ticket_template="registrations/tickets/layouts/CONFERENCE-BADGE.html")
    Event.objects.filter(ticket_template="registrations/tickets/layouts/EVENT_MULTI.html").update(ticket_template="registrations/tickets/layouts/EVENT-MULTI.html")

    # CONVERTING TO "PAGE" templates:
    # ("content/oldtheme/base-details.html", "[Interim conference design template]"),
    # ("content/test_details.html", "[APA test template (for testing only)]"),
    # ("content/landingpage_template.html", "[Old/interim design promo/landing page template]"),
    Content.objects.filter(
            template__in=("content/oldtheme/base-details.html","content/test_details.html","content/landingpage_template.html") 
        ).update(template="PAGE")


    # MAYBE TO DO, set specific templates instead of dealing with it in RenderContent (depends how we end up refactoring RenderContent)
    # Content.objects.filter(template="PAGE", ).update(template="SOMETHING")


def print_provider_admin_relationships_to_terminal():

    providers = Provider.objects.prefetch_related("contactrelationship_as_source__target").all()

    for p in providers:

        print("")
        print(p)

        print("", "Imis admins")
        # NEED TO GET ONLY ADMINS HERE
        imis_company_or_admins = ("{id} | {name}".format(id=c["ID"], name=c["FULL_NAME"]) for c in p.get_imis_company_relationships().get("data", []))
        for c in imis_company_or_admins:
            print("", "", c)

        print("", "Django admins")
        provider_admins = [c for c in p.contactrelationship_as_source.all()
                           if c.relationship_type == "ADMINISTRATOR"]
        for cr in provider_admins:
            print("", "", cr.target)


def write_provider_admin_relationships_to_imis():
    providers = Provider.objects.prefetch_related("contactrelationship_as_source__target").all()

    for p in providers:
        print("")
        print("{id} | {title}".format(id=p.user.username, title=p.title))

        provider_admins = [c for c in p.contactrelationship_as_source.all()
                           if c.relationship_type == "ADMINISTRATOR"]
        for cr in provider_admins:
            cr.target.post_imis_relationship(data={"co_id": p.user.username, "relation_type":"ADMIN_I"} )
            print("", cr.target)

