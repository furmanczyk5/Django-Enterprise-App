"""
This file was generated with the customdashboard management command and
contains the class for the main dashboard.

To activate your index dashboard add the following to your settings.py::
    GRAPPELLI_INDEX_DASHBOARD = 'planning.admin_dashboard.CustomIndexDashboard'
"""
import re

from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from grappelli.dashboard import modules, Dashboard


class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard for planning.org
    """

    class Media:
        css = {
            "all": ("content/css/apa_admin.css",),
        }

    @staticmethod
    def get_admin_link_dict(title, app_label, model_name):
        return {
            'title': _(title),
            'url': reverse("admin:%s_%s_changelist" % (app_label, model_name)),
            'external': False,
        }

    @staticmethod
    def has_any_permission(permissions_list, app_label, model_name=None):
        if model_name:
            regex = '^(?P<app>{app})\.(?P<perm>add|change|delete)_(?P<model>{model})$'.format(
                app=app_label,
                model=model_name
            )
        else:
            regex = '^(?P<app>{app})\..*$'.format(app=app_label)
        return next((True for p in permissions_list if re.search(regex, p)), False)

    def init_with_context(self, context):
        group_names = [g.name for g in context["user"].groups.all()]
        permissions = context["user"].get_all_permissions()

        pages_model_list = [
            "pages.models.MembershipPage",
            "pages.models.KnowledgeCenterPage",
            "pages.models.ConferencesPage",
            "pages.models.AICPPage",
            "pages.models.PolicyPage",
            "pages.models.CareerPage",
            "pages.models.OutreachPage",
            "pages.models.ConnectPage",
            "pages.models.AboutPage",
            "pages.models.AudioPage",
            "pages.models.VideoPage",
            "pages.models.JotFormPage"
        ]

        if "staff-editor" in group_names:
            pages_model_list += [
                "pages.models.LandingPage",
                "pages.models.Page",
                "pages.models.UncategorizedPage"

            ]

        self.children.append(modules.ModelList(
            _('Web Pages'),
            column=1,
            collapsible=True,
            css_classes=('grp-closed',),
            models=pages_model_list,
        ))

        self.children.append(modules.ModelList(
            _('Publications'),
            column=1,
            collapsible=True,
            css_classes=('grp-closed',),
            models=(
                'publications.models.PlanningMagArticle',
                'publications.models.Article',
                'publications.models.PublicationDocument',
                'publications.models.Report',
                'publications.models.Publication',
            ),
        ))

        self.children.append(modules.ModelList(
            _('Blog'),
            column=1,
            collapsible=True,
            css_classes=('grp-closed',),
            models=('blog.models.*',),
        ))

        kb_groups = ['staff-research', 'staff-editor', 'staff-marketing']
        if (any(x in kb_groups for x in group_names)) or context["user"].is_superuser:
            self.children.append(modules.ModelList(
                _('Research Knowledgebase'),
                column=1,
                collapsible=True,
                css_classes=('grp-closed',),
                models=(
                    'knowledgebase.models.Collection',
                    'knowledgebase.models.Resource',
                    'knowledgebase.models.*',
                ),
            ))

            self.children.append(modules.ModelList(
                _('Research Inquiries'),
                column=1,
                collapsible=True,
                css_classes=('grp-closed',),
                models=(
                    'research_inquiries.models.*',
                ),
            ))

        self.children.append(modules.ModelList(
            _('Submissions'),
            column=1,
            collapsible=True,
            css_classes=('grp-closed',),
            models=('submissions.models.*',)
        ))

        # TODO: not sure why this is showing up in seemingly every case
        # Awards model permissions were only explicitly granted to the
        # staff-communications group
        if 'staff-communications' in group_names or context["user"].is_superuser:
            self.children.append(modules.ModelList(
                _('Awards'),
                column=1,
                collapsible=True,
                css_classes=('grp-closed',),
                models=("awards.models.*",),
            ))

        self.children.append(modules.ModelList(
            _('Jobs'),
            column=1,
            collapsible=True,
            css_classes=('grp-closed',),
            models=("jobs.models.Job",
                    "jobs.models.WagtailJob",),
        ))

        self.children.append(modules.ModelList(
            _('AICP Exam'),
            column=1,
            collapsible=True,
            css_classes=('grp-closed',),
            models=(
                'exam.models.Exam',
                'exam.models.ApplicationCategory',
                'exam.models.ExamApplication',
                'exam.models.ExamRegistration',
                'exam.models.ExamApplicationOrder',
                'exam.models.ExamRegistrationOrder',
                'exam.models.ExamApplicationRole',
                'exam.models.AICPCandidateApplication',
                'exam.models.AICPCredentialData',
            ),
        ))

        if "staff-editor" in group_names \
                or "staff-events-editor" in group_names \
                or context["user"].is_superuser:
            self.children.append(modules.LinkList(
                _('Content Editor Administration'),
                column=1,
                collapsible=True,
                css_classes=('grp-closed',),
                children=(
                    self.get_admin_link_dict("Email templates", "content", "emailtemplate"),
                    self.get_admin_link_dict("Messages", "content", "messagetext"),
                    self.get_admin_link_dict("Taxonomy topics", "content", "taxotopictag"),
                    self.get_admin_link_dict("Menu items", "content", "menuitem"),
                    self.get_admin_link_dict("Serial publications", "content", "serialpub"),
                    self.get_admin_link_dict("Tag types / tags", "content", "tagtype"),
                    {
                        'title': _("Published pages (in order by most recent)"),
                        'url': "/admin/pages/page/?o=-8&workflow_status__exact=IS_PUBLISHED",
                        'external': False,
                    },
                    {
                        'title': _("Pages sent for publication (needs review)"),
                        'url': reverse("admin:pages_page_changelist") + "?workflow_status=NEEDS_REVIEW",
                        'external': False,
                    },
                    {
                        'title': _("Blog posts sent for publication (needs review)"),
                        'url': reverse("admin:blog_blogpost_changelist") + "?workflow_status=NEEDS_REVIEW",
                        'external': False,
                    },
                    {
                        'title': _("Publications sent for publication (needs review)"),
                        'url': reverse("admin:publications_publication_changelist") + "?workflow_status=NEEDS_REVIEW",
                        'external': False,
                    },
                    {
                        'title': _("Events sent for publication (needs review)"),
                        'url': reverse("admin:events_event_changelist") + "?workflow_status=NEEDS_REVIEW",
                        'external': False,
                    },
                    {
                        'title': _("Wagtail Jobs sent for publication (needs review)"),
                        'url': reverse("admin:jobs_wagtailjob_changelist") + "?workflow_status=NEEDS_REVIEW",
                        'external': False,
                    },
                ),
            ))

        has_any_myapa_permission = self.has_any_permission(permissions, "myapa")

        if has_any_myapa_permission:

            my_apa_children = []

            if self.has_any_permission(permissions, "myapa", "contact"):
                my_apa_children.append(
                    self.get_admin_link_dict("All contacts", "myapa", "contact")
                )

            if self.has_any_permission(permissions, "myapa", "individualcontact"):
                my_apa_children.append(
                    self.get_admin_link_dict("Individuals", "myapa", "individualcontact")
                )

            if self.has_any_permission(permissions, "myapa", "organization"):
                my_apa_children.append(
                    self.get_admin_link_dict("Organizations", "myapa", "organization")
                )

            if self.has_any_permission(permissions, "myapa", "school"):
                my_apa_children.append(
                    self.get_admin_link_dict("Schools", "myapa", "school")
                )

            if "staff" or "organization-store-admin" in group_names:
                my_apa_children.append({
                    'title': _('Create new user account'),
                    'url': '/myapa/account/create/admin/',
                    'external': False
                })

            if self.has_any_permission(permissions, "myapa", "contactrole"):
                my_apa_children.append(
                    self.get_admin_link_dict("Contributors", "myapa", "contactrole")
                )

            if self.has_any_permission(permissions, "myapa", "contactrelationship"):
                my_apa_children.append(
                    self.get_admin_link_dict("Contact relationships", "myapa", "contactrelationship")
                )

            if "staff" or "organization-store-admin" in group_names:
                my_apa_children.append({
                    'title': _('Update/create record from iMIS'),
                    'url': '/conference/admin/create-django-user/',
                    'external': False,
                })

            my_apa_linklist = modules.LinkList(
                _('My APA'),
                column=2,
                collapsible=True,
                css_classes=('grp-closed',),
                children=my_apa_children,
                pre_content="""
                <div class="grp-collapse grp-closed">
                    <form action="">
                    <ul class="grp-listing-small">
                    <li class="grp-row">
                        Lookup: <input type="text"></input>
                    </li>
                    </ul>
                    </form>
                </div>
                """
            )

            self.children.append(my_apa_linklist)

        self.children.append(modules.ModelList(
            _("Member/Customer Support"),
            column=2,
            collapsible=True,
            css_classes=('grp-closed',),
            models=(
                "support.models.*",
            ),
        ))

        self.children.append(modules.ModelList(
            _('E-commerce'),
            column=2,
            collapsible=True,
            css_classes=('grp-closed',),
            models=(
                'store.models.content_product.ContentProduct',
                # 'store.models.donation.Donation',
                'store.models.order.Order',
                # 'store.models.product_cart.ProductCart',
                # 'store.models.product_option.ProductOption',
                # 'store.models.product_price.ProductPrice',
                # 'store.models.purchase.Purchase',
            ),
        ))

        self.children.append(modules.ModelList(
            _('APA Learn'),
            column=2,
            collapsible=True,
            css_classes=('grp-closed',),
            models=(
                'learn.models.learn_course.*',
                'learn.models.learn_evaluation.*',
                'learn.models.group_license.*',
            ),
        ))

        if self.has_any_permission(permissions, "events"):

            events_children = []

            # if self.has_any_permission(permissions, "events", "nationalconferenceparticipant"):
            #     events_children.append(self.get_admin_link_dict("Conference Participants", "events", "nationalconferenceparticipant"))

            # if self.has_any_permission(permissions, "conference", "microsite"):
            #     events_children.append(self.get_admin_link_dict("Event microsites", "conference", "microsite"))

            # if self.has_any_permission(permissions, "events", "event"):
            #     events_children.append(self.get_admin_link_dict("Events with online registration", "events", "activity"))

            # if self.has_any_permission(permissions, "registrations", "attendee"):
            #     events_children.append(self.get_admin_link_dict("Event attendees", "registrations", "attendee"))

            # if self.has_any_permission(permissions, "events", "event"):
            #     events_children.append(self.get_admin_link_dict("APA Learn courses", "events", "course"))

            # if self.has_any_permission(permissions, "events", "event"):
            #     events_children.append(self.get_admin_link_dict("All on-demand education", "events", "course"))

            if self.has_any_permission(permissions, "events", "eventmulti"):
                events_children.append(self.get_admin_link_dict("Multipart events", "events", "eventmulti"))

            if self.has_any_permission(permissions, "events", "eventsingle"):
                events_children.append(self.get_admin_link_dict("Single events", "events", "eventsingle"))

            if self.has_any_permission(permissions, "events", "event"):
                events_children.append(self.get_admin_link_dict("Event activities", "events", "activity"))

            if self.has_any_permission(permissions, "events", "speaker"):
                events_children.append(self.get_admin_link_dict("Speakers", "events", "speaker"))

            if self.has_any_permission(permissions, "conference", "nationalconferenceactivity"):
                events_children.append(self.get_admin_link_dict("NPC activities", "conference", "nationalconferenceactivity"))

            if next((True for g in group_names if g in ['staff-store-admin', 'onsite-conference-admin']), False):
                events_children.extend([{
                    'title': _('NPC onsite kiosk ticket printing'),
                    'url': '/registrations/9135594/ticket_printing/',
                    'external': False
                }, {
                    'title': _('NPC onsite custom ticket printing'),
                    'url': '/registrations/staff/custom-tickets/',
                    'external': False
                }])

            if self.has_any_permission(permissions, "conference", "microsite"):
                events_children.append(self.get_admin_link_dict("Event microsites", "conference", "microsite"))

            if self.has_any_permission(permissions, "conference", "cadmiumsync"):
                events_children.append(self.get_admin_link_dict("Cadmium Syncs", "conference", "cadmiumsync"))

            if self.has_any_permission(permissions, "conference", "cadmiummapping"):
                events_children.append(self.get_admin_link_dict("Cadmium Mappings", "conference", "cadmiummapping"))

            if self.has_any_permission(permissions, "events", "course"):
                events_children.append(self.get_admin_link_dict("On-demand courses", "events", "course"))

            if self.has_any_permission(permissions, "events", "event"):
                events_children.append(
                    self.get_admin_link_dict(
                        "All events, activities, and courses", "events", "event"
                    )
                )

            events_linklist = modules.LinkList(
                _('Events, Microsites, NPC, Cadmium Syncs, On-demand'),
                column=2,
                collapsible=True,
                css_classes=('grp-closed',),
                children=events_children,
                pre_content="""
                <div class="grp-collapse grp-closed">
                    <form action="">
                    <ul class="grp-listing-small">
                    <li class="grp-row">
                        Lookup: <input type="text"></input>
                    </li>
                    </ul>
                    </form>
                </div>
                """
            )

            self.children.append(events_linklist)

        self.children.append(modules.ModelList(
            _('CM'),
            column=2,
            collapsible=True,
            css_classes=('grp-closed',),
            models=("cm.models.*",),
        ))

# self.children.append(modules.ModelList(
#     _('Conference Microsites'),
#     column=2,
#     collapsible=True,
#     models=(
#         "conference.models.microsite.Microsite",
#         ),
# ))

# self.children.append(modules.ModelList(
#     _('Event Registrations'),
#     column=2,
#     collapsible=True,
#     css_classes = ('grp-closed',),
#     models=('registrations.models.*',)
# ))

# npc_children = []

# GOING AWAY SINCE EVENT REG MOVING TO IMIS
# if self.has_any_permission(permissions, "conference", "nationalconferenceattendee"):
#     npc_children.append(self.get_admin_link_dict("NPC attendees", "conference", "nationalconferenceattendee"))

# npc_linklist = modules.LinkList(
#     _('NPC'),
#     column=2,
#     collapsible=True,
#     css_classes = ('grp-closed',),
#     children=npc_children,
#     pre_content="""
#     <div class="grp-collapse grp-closed">
#         <form action="">
#         <ul class="grp-listing-small">
#         <li class="grp-row">
#             Lookup: <input type="text"></input>
#         </li>
#         </ul>
#         </form>
#     </div>
#     """
# )

# self.children.append(npc_linklist)

        self.children.append(modules.ModelList(
            _('Consultants'),
            column=2,
            collapsible=True,
            css_classes=('grp-closed',),
            models=('consultants.models.*',)
        ))

        self.children.append(modules.ModelList(
            _("Wagtail Sites"),
            column=2,
            collapsible=True,
            css_classes=('grp-closed',),
            models=(
                "component_sites.models.*",
            ),
        ))

        self.children.append(modules.ModelList(
            _("Directories"),
            column=2,
            collapsible=True,
            css_classes=('grp-closed',),
            models=(
                "directories.models.Directory"
            )
        ))

        self.children.append(modules.ModelList(
            _('Media'),
            column=3,
            collapsible=True,
            css_classes=('grp-closed',),
            models=('media.models.*',),
        ))

        self.children.append(modules.ModelList(
            _('Image Library'),
            column=3,
            collapsible=True,
            css_classes=('grp-closed',),
            models=('imagebank.models.Image',),
        ))

        self.children.append(modules.ModelList(
            _('Places'),
            column=3,
            collapsible=True,
            css_classes=('grp-closed',),
            models=('places.models.*',),
        ))

        # TODO: need to figure out why this is showing up in seemingly every case
        has_administration_access = False
        for group in [
            'onsite-conference-admin',
            'staff-aicp',
            'staff-conference',
            'staff-editor',
            'staff-events-editor',
            'staff-membership',
            'staff-store-admin'
        ]:
            if group in group_names or context["user"].is_superuser:
                has_administration_access = True
        if has_administration_access:
            self.children.append(modules.ModelList(
                _('Administration'),
                column=3,
                collapsible=True,
                css_classes=('grp-closed',),
                models=(
                    'django.contrib.auth.models.User',
                    'django.contrib.auth.models.Group',
                    'django.contrib.redirects.models.Redirect',
                    'django.contrib.sites.models.Site'
                ),
            ))
