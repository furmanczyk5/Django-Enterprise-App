from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from django.db.models import Sum
from django.contrib.staticfiles.templatetags.staticfiles import static
from django import forms

from cm.models import Log
from content.admin_abstract import BaseContentAdmin, BaseAddressAdmin
from free_students.admin import SchoolInline
from myapa.models.job_history import JobHistory
from myapa.models.contact import Contact
from myapa.models.contact_relationship import ContactRelationship
from myapa.models.contact_role import ContactRole
from myapa.models.profile import IndividualProfile, OrganizationProfile
from myapa.models.proxies import IndividualContact, Organization, School
from myapa.utils import has_webgroup
from support.models import Ticket


# WHY DOESN'T THIS SHOW UP UNDER THE MY APA HEADER?
class MyApaGroupAdmin(GroupAdmin):
    pass


class MyApaUserAdmin(UserAdmin):
    # THIS IS NEEDED FOR CHAPTER CONFERENCES

    list_display = [
        "username", "get_member_type", "first_name", "last_name", "email", "get_address1",
        "get_address2", "get_city", "get_state", "get_country", "get_zip_code"
    ]
    readonly_fields = [
        "get_member_type", "get_address1", "get_address2", "get_city", "get_state",
        "get_country", "get_zip_code",
    ]

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        if has_webgroup(user=request.user, required_webgroups=["organization-store-admin"]):
            return {}
        else:
            return super().get_model_perms(request)

    def get_address1(self, obj):
        return obj.contact.address1

    get_address1.short_description = "Address 1"

    def get_address2(self, obj):
        return obj.contact.address2

    get_address2.short_description = "Address 2"

    def get_city(self, obj):
        return obj.contact.city

    get_city.short_description = "City"

    def get_state(self, obj):
        return obj.contact.state

    get_state.short_description = "State"

    def get_country(self, obj):
        return obj.contact.country

    get_country.short_description = "Country"

    def get_zip_code(self, obj):
        return obj.contact.zip_code

    get_zip_code.short_description = "Zip code"

    def get_member_type(self, obj):
        return obj.contact.member_type

    get_member_type.short_description = "Member type"


class ContactRoleInline(admin.StackedInline):
    model = ContactRole
    fields = [
        "role_type", "sort_number", ("invitation_sent", "confirmed", "resend_invite"),
        "special_status", ("permission_content", "permission_av"), "content_rating"
    ]
    extra = 0
    raw_id_fields = ['contact', 'content']
    readonly_fields = ["resend_invite", "published_by"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("content", "contact")

    def resend_invite(self, obj):
        contact = obj.contact

        if contact and contact.email:
            return "<a href='/admin/resend_invite/%s'>Resend Invite</a>" % contact.user.username

        else:
            return "No contact or email for invitation"

    resend_invite.short_description = ""
    resend_invite.allow_tags = True


class ContactRoleInlineAdminForm(forms.ModelForm):
    class Meta:
        model = ContactRole
        exclude = []
    def __init__(self, *args, **kwargs):
        super(ContactRoleInlineAdminForm, self).__init__(*args, **kwargs)
        self.fields['external_bio_url'].label = "APA Learn Bio URL"


class ContactRoleInlineContact(ContactRoleInline):
    model = ContactRole
    form = ContactRoleInlineAdminForm
    fields = [
                 ('id', 'contact_link'), 'contact', ('first_name', 'middle_name', 'last_name'),
                 'email', 'company', 'phone', 'cell_phone', 'external_bio_url', 'bio',
             ] + ContactRoleInline.fields
    autocomplete_lookup_fields = {'fk': ['contact']}
    readonly_fields = ContactRoleInline.readonly_fields + ['id', 'contact_link']
    sortable_field_name = "sort_number"  # grappelli sorting inlines
    verbose_name = "ROLE:"
    verbose_name_plural = "Contributors (previously contact roles)"


class ContactRoleInlineContent(admin.TabularInline):
    """
    This is the inline TO content (to add to to the contact admin)
    """
    model = ContactRole
    extra = 0
    fields = ["content", "role_type"]
    raw_id_fields = ["content"]
    autocomplete_lookup_fields = {"fk": ["content"]}
    classes = ("grp-collapse grp-closed",)
    title = "Contributed content"



class IndividualProfileAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = IndividualProfile
        exclude = []
        widgets = {
            "experience":forms.Textarea(attrs={"class":"ckeditor"})
        }


class IndividualProfileInline(admin.StackedInline):
    model = IndividualProfile
    form = IndividualProfileAdminForm

    list_display_links = ["contact", ]
    list_display = ["contact", ]
    readonly_fields = ("img_thumbnail", "resume_link",)
    fieldsets = [
        (None, {
            "fields": (("img_thumbnail"), ("resume_link"),
                       "slug",
                       "statement",
                       "experience",
                       "share_profile",
                       "share_contact",
                       "share_bio",
                       "share_social",
                       "share_leadership",
                       "share_education",
                       "share_jobs",
                       "share_events",
                       "share_resume",
                       "share_conference",
                       "share_advocacy",
                       )
        })
    ]

    def resume_link(self, obj):
        return '<a href="%s">%s</a>' % (obj.resume.uploaded_file.url, obj.resume.uploaded_file.url)

    resume_link.allow_tags = True
    resume_link.short_description = 'Resume'
    classes = ("grp-collapse grp-closed",)
    inline_classes = ('grp-open',)

    def has_delete_permission(self, request, obj=None):
        """ We don't want admin users deleting profiles through the inline! """
        return False

    title = "My APA Profile"


class OrganizationRelationshipInline(admin.TabularInline):
    model = ContactRelationship
    fk_name = 'target'
    fields = ["relationship_type", "source"]
    extra = 0
    raw_id_fields = ['source']
    autocomplete_lookup_fields = {"fk": ['source']}
    title = "Admin relationships"
    classes = ("grp-collapse grp-closed",)


class IndividualContactRelationshipInline(admin.TabularInline):
    model = ContactRelationship
    fk_name = 'source'
    fields = ["relationship_type", "target"]
    extra = 0
    raw_id_fields = ['target']
    autocomplete_lookup_fields = {"fk": ['target']}
    title = "Admin relationships"
    classes = ("grp-collapse grp-closed",)


# using this now at least for debugging & seeing user's schedule in the admin... not sure we want to keep it around or not
# class ContactContentAddedInline(admin.StackedInline):
#     model = ContactContentAdded
#     fields = ["content", "added_type"]
#     raw_id_fields=['content']
#     autocomplete_lookup_fields = { 'fk' : ['content'] }
#     extra = 0
#     title = "Content Added/Saved By Contact:"


class ContactAdmin(BaseContentAdmin):
    raw_id_fields = ['user']
    list_display = [
        'get_username', 'get_title', 'company', 'member_type', 'email', 'city', 'state',
        'contact_type', 'organization_type'
    ]
    list_filter = ['contact_type', 'contactrole__role_type', 'member_type']
    search_fields = ['=user__username', 'first_name', 'last_name', 'company', 'email']

    # TODO ... make sure we don't need ContactContentAddedInline anymore...

    list_display_links = ["get_username", "get_title"]

    fieldsets = [BaseAddressAdmin.fieldsets[0]]

    def get_username(self, obj):

        if obj.user:
            return obj.user.username
        else:
            return 'Anonymous'

    def get_title(self, obj):
        if not obj.user or not obj.user.username:
            return ''
        return obj.full_title()

    get_username.short_description = "User ID"
    get_title.short_description = 'Title'

    show_solr_publish = False
    show_imis_sync = False
    show_sync_credly = True

    change_form_template = "admin/myapa/contact/change_form.html"

    # revision_form_template = "admin/myapa/revision_form.html"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "user"
        ).prefetch_related(
            "cm_logs"
        ).prefetch_related(
            "tickets"
        ).prefetch_related(
            "contactrole"
        )

    def change_form_extra_context(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["extra_save_options"] = {
            "show_solr_publish": self.show_solr_publish,
            "show_imis_sync": self.show_imis_sync,
            "show_sync_credly": self.show_sync_credly
        }
        return extra_context

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = self.change_form_extra_context(request, extra_context)
        return super().change_view(
            request, object_id, form_url,
            extra_context=extra_context
        )

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = self.change_form_extra_context(request, extra_context)
        return super().add_view(
            request, form_url,
            extra_context=extra_context
        )

    def response_add(self, request, obj, **kwargs):
        self.change_form_button_actions(request, obj)
        return super().response_add(request, obj)

    def response_change(self, request, obj):
        self.change_form_button_actions(request, obj)
        return super().response_change(request, obj)

    def change_form_button_actions(self, request, obj):
        if "_sync_imis" in request.POST:
            results = obj.sync_from_imis()
            messages.success(
                request,
                'Successfully synced %s school data from iMIS to django' % obj.company
            )
        if "_solr_publish" in request.POST:
            obj.solr_publish()
            messages.success(request, "Successfully published %s to search" % obj.title)

        if "_sync_credly" in request.POST:
            results = obj.designation_to_badges(request)
            messages.success(request,'Successfully synced \"%s\" from iMIS to Credly' % (obj.title))


class JobHistoryInline(admin.StackedInline):
    model = JobHistory
    fields = [
        "title", "company", ("city", "state", "zip_code"), "country",
        ("start_date", "end_date"), ("is_current", "is_part_time")
    ]
    extra = 0
    raw_id_fields = ['contact', ]
    classes = ("grp-collapse grp-closed",)
    title = "My APA Job History"


class TicketInline(admin.TabularInline):
    model = Ticket
    fields = ["id", "get_admin_link", "category", "created_time"]
    readonly_fields = fields
    extra = 0
    max_num = 0
    classes = ("grp-collapse grp-closed",)

    # show_change_link = True # NOTE: it appears that show_change_link not supported with Grapelli

    def has_delete_permission(self, request, obj=None):
        """ We don't want admin users deleting tickets through the inline! """
        return False


class CMLogInline(admin.TabularInline):
    model = Log
    fields = ["get_admin_link", "status"]
    readonly_fields = fields
    extra = 0
    max_num = 0
    classes = ("grp-collapse grp-closed",)

    def has_delete_permission(self, request, obj=None):
        """ We don't want admin users deleting cm logs through the inline! """
        return False


class IndividualContactAdmin(ContactAdmin):
    fieldsets = [
        (None, {

            "fields": (("member_type", "contact_type", "user"),
                       ("first_name", "middle_name", "last_name"),
                       ("prefix_name", "suffix_name", "designation"),
                       ("company", "company_fk"),
                       ("chapter", "salary_range",),
                       ("job_title",),
                       ("email", "cell_phone",
                        "secondary_phone",  # = WORK PHONE
                        "phone",  # = HOME PHONE
                        ),
                       ("login_as_user", "get_groups",),
                       ("solr_publish",)
                       )

        }),
        ("My APA Biographical Info", {
            "classes": ("grp-collapse grp-closed",),
            "fields": ("bio",
                       "about_me",
                       "slug",
                       ("personal_url", "linkedin_url"),
                       ("facebook_url", "twitter_url"))
        })
    ]
    readonly_fields = [
        "member_type", "contact_type", "user", "first_name", "middle_name", "last_name",
        "prefix_name", "suffix_name", "designation", "company", "company_fk", "chapter",
        "salary_range", "job_title", "email", "phone", "secondary_phone", "cell_phone",
        "get_groups", "login_as_user", "solr_publish"
    ]

    raw_id_fields = ['user', 'company_fk']
    autocomplete_lookup_fields = {"fk": ['user', 'company_fk']}
    inlines = [
        IndividualProfileInline, JobHistoryInline, ContactRoleInlineContent, TicketInline,
        CMLogInline, OrganizationRelationshipInline
    ]

    def get_groups(self, obj):
        return ", ".join([g.name for g in obj.user.groups.all()])

    get_groups.short_description = "Permission groups"

    def set_staff_teams_access(self, obj):
        if obj.user.groups.filter(name="staff-editor").exists() or obj.user.is_superuser:
            self.fieldsets[0][1]['fields'] += ("staff_teams",)

    def login_as_user(self, obj):
        return "<a href='/admin/%s/auto_login/'>LOGIN AS %s</a>" % (
            obj.user.username, obj.title.upper()
        )

    login_as_user.allow_tags = True

    def solr_publish(self, obj):
        return ("""
            <a href='/events/speakers/admin/speaker/{0}/publish/' onclick="return confirm('Any un-saved changes will be lost. Are you sure you want to leave?');">UPDATE SPEAKER DATABASE</a>
            <p class="grp-help">Updates this user's record in the Speaker Database.
                If user is no longer a speaker, this will remove their record from the search.</p>
            <p class="grp-help">Any unsaved changes will be lost.</p>""".format(obj.user.username))

    solr_publish.short_description = "Search"
    solr_publish.allow_tags = True
    show_sync_credly = True

    class Media:
        js = (
            "//ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js",
            static("ckeditor/ckeditor.js"),
            # static("ckeditor/plugins/lite/lite-interface.js")
        )
        css = {
             'all': ( static("ckeditor/plugins/planning_media/admin.css"), )
        }


# The new OrganizationProfileInline
class OrganizationProfileInline(admin.StackedInline):
    model = OrganizationProfile
    extra = 0
    fk_name = "contact"
    # raw_id_fields=["image"]
    # autocomplete_lookup_fields = {"fk":["image"]}
    title = "Organization Profile"
    classes = ("grp-collapse grp-open",)
    inline_classes = ('grp-open',)
    readonly_fields = ("img_thumbnail", "total_inquiry_hours_used")
    fields = [("contact", "image", "img_thumbnail",),
              ("principals", "date_founded",),
              ("number_of_staff", "number_of_planners", "number_of_aicp_members",),
              "consultant_listing_until",
              ("research_inquiry_hours", "total_inquiry_hours_used")
              ]
    raw_id_fields = ["image"]
    autocomplete_lookup_fields = {'fk': ["image"]}

    def total_inquiry_hours_used(self, obj):
        # calculates the total number of research inquiry hours used by this organization
        inquiry_aggregate = ContactRole.objects.filter(
            content__content_type="RESEARCH_INQUIRY",
            contact=obj.contact,
            role_type="PROPOSER",
            publish_status="DRAFT"  # I DONT THINK WE PUBLISH THESE, WE CAN IF WE WANT TO THOUGH
        ).exclude(
            content__inquiry__hours__isnull=True
        ).select_related(
            "content__inquiry"
        ).aggregate(
            Sum("content__inquiry__hours")
        )

        return inquiry_aggregate["content__inquiry__hours__sum"]

    total_inquiry_hours_used.short_description = "Total Inquiry Hours Used"


class OrganizationAdmin(ContactAdmin):
    fieldsets = [
        (None, {

            "fields": (("member_type", "contact_type", "user"),
                       ("company"),
                       ("organization_type"),
                       ("pas_type"),
                       ("address1"),
                       ("address2"),
                       ("city", "state"),
                       ("zip_code", "country"),
                       ("email",),
                       ("secondary_phone", "cell_phone"),
                       )}),
        ("Company Profile", {
            "classes": ("grp-collapse grp-closed",),
            "fields": ("bio",
                       "about_me",
                       "slug",
                       ("personal_url", "linkedin_url"),
                       ("facebook_url", "twitter_url"))
        })
    ]

    # TO DO... add ContactRoleInlineContent here once we can figure out how to limit queries (and maybe the overall result set)...
    inlines = [IndividualContactRelationshipInline, OrganizationProfileInline]
    show_sync_credly = False

    # THIS LOOKS LIKE IT SHOULDN'T BE HERE... IT BELONGS TO A FILTER CLASS... maybe it's leftovers from a merge conflict
    # def queryset(self, request, queryset):
    #     if self.value() is None: # default to most recent conference
    #         return queryset.filter(content__parent__content_live__code=NATIONAL_CONFERENCES_ADMIN[0])
    #     else:
    #         return queryset.filter(content__parent__content_live__code=self.value())


# The original second OrganizationProfileInline:
# class OrganizationProfileInline(admin.StackedInline):
#     model = OrganizationProfile
#     extra = 0
#     fk_name = "contact"
#     # raw_id_fields=["image"]
#     # autocomplete_lookup_fields = {"fk":["image"]}
#     title = "Organization Profile"
#     classes=( "grp-collapse grp-open",)
#     inline_classes = ('grp-open',)
#     fields = [("contact", "image",),
#                 ("principals", "date_founded",),
#                 ("number_of_staff", "number_of_planners", "number_of_aicp_members",),
#                 "consultant_listing_until",
#     ]
#     raw_id_fields = ["image"]
#     autocomplete_lookup_fields = { 'fk' : ["image"] }


class ContactRoleAdmin(admin.ModelAdmin):
    list_display = [
        "id", "get_username", "contact_link", "get_content_code", "content",
        "get_user_email", "role_type", "get_content_type", "get_content_status"
    ]
    list_filter = [
        "confirmed", "invitation_sent", "role_type", "content__content_type", "content__status"
    ]
    search_fields = [
        "=contact__user__username", "contact__first_name", "contact__last_name", "contact__email",
        "content__title", "content__code"
    ]

    list_display_links = ["id"]

    raw_id_fields = ["contact", "content"]
    autocomplete_lookup_fields = {'fk': ["contact", "content"]}

    fieldsets = [
        (None, {
            "fields": (("id", "contact_link", "content_link"), "contact", "content",
                       ("first_name", "middle_name", "last_name", "bio"), "role_type", "sort_number",
                       ("invitation_sent", "confirmed"), "special_status", ("permission_content", "permission_av"),
                       "content_rating", "external_bio_url")
        })
    ]

    readonly_fields = ["id", "contact_link", "content_link"]

    def get_content_type(self, obj):
        return obj.content.content_type

    get_content_type.short_description = "Content Type"
    get_content_type.admin_order_field = "content__content_type"

    def get_content_status(self, obj):
        return obj.content.status

    get_content_status.short_description = "Content Status"
    get_content_status.admin_order_field = "content__status"

    def get_content_code(self, obj):
        return obj.content.code

    get_content_code.short_description = "Content Code"
    get_content_code.admin_order_field = "content__code"

    def get_user_email(self, obj):
        if obj.contact:
            return obj.contact.email
        else:
            return obj.email

    get_user_email.short_description = "Email"
    get_user_email.admin_order_field = "contact__email"

    def get_username(self, obj):

        try:
            return obj.contact.user.username
        except:
            return 'None'

    get_username.short_description = "User ID"
    get_username.admin_order_field = "contact__user__username"

    # QUERY SET IS: all draft contactroles
    def get_queryset(self, request):
        # also only events with parent NPC! or some tag?
        return super().get_queryset(request).select_related(
            "content", "contact", "contact__user"
        ).filter(content__publish_status="DRAFT").distinct()


class SchoolAdmin(ContactAdmin):
    model = School
    list_display = [
        "get_username", "get_company", "get_school_accreditations", "get_graduate_student_count",
        "get_undergraduate_student_count", "get_pending_student_count",
    ]
    list_display_links = ("get_username", "get_company")
    search_fields = ["=user__username", "title", ]

    # http://stackoverflow.com/questions/10504521/assigning-a-proxy-model-instance-to-foreign-key
    # inlines = [IndividualContactRelationshipInline]
    # is this not possible?
    inlines = [SchoolInline, ]
    fieldsets = [
        (None, {
            "fields": (
                (
                    "get_graduate_student_count",
                    "get_undergraduate_student_count",
                    "get_pending_student_count"
                ),
                ("get_students", "get_admins"),
                "company",
                "address1",
                "address2",
                "city", "state",
                "country",
                "email",
                ("phone", "cell_phone"),
            )
        }
         ),
    ]
    readonly_fields = [
        "get_students", "get_graduate_student_count", "get_undergraduate_student_count",
        "get_pending_student_count", "get_admins", "company", "address1", "address2", "city",
        "state", "country", "zip_code", "email", "phone", "cell_phone"
    ]
    # raw_id_fields = ["get_graduate_student_count", "get_undergraduate_student_count",]

    show_imis_sync = True
    show_sync_credly = False

    def get_username(self, obj):

        if obj.user:
            return obj.user.username
        else:
            return 'Anonymous'

    get_username.short_description = "School ID"

    def get_company(self, obj):
        return obj.company

    get_company.short_description = "School"

    def get_school_accreditations(self, obj):
        return ",\n".join(
            [s.get_accreditation_type_display() for s in
             obj.accredited_school.accreditation.all()]
        )

    get_school_accreditations.short_description = "Accreditations"

    def get_graduate_student_count(self, obj):
        return obj.students.filter(status="A", degree_type="G").exclude(contact__isnull=True).count()

    get_graduate_student_count.short_description = "Graduate Uploads"

    def get_undergraduate_student_count(self, obj):
        return obj.students.filter(status="A", degree_type="U").exclude(contact__isnull=True).count()

    get_undergraduate_student_count.short_description = "Undergraduate Uploads"

    def get_pending_student_count(self, obj):
        return obj.students.filter(status="P", contact__isnull=True).count()

    get_pending_student_count.short_description = "Pending Uploads"

    def get_admins(self, obj):
        return ("<a href='/admin/myapa/contactrelationship/?q=%s'>Admins</a>" % obj.user.username)

    get_admins.allow_tags = True
    get_admins.short_description = "Organization relationships"

    def get_students(self, obj):
        return ("<a href='/admin/free_students/student/?school__id=%s'>Students</a>" % obj.id)

    get_students.allow_tags = True
    get_students.short_description = "View Students"


class ContactRelationshipAdmin(admin.ModelAdmin):
    model = ContactRelationship

    list_display = ["source", "get_target_link", "relationship_type"]

    search_fields = [
        "=source__user__username", "=target__user__username", "source__company",
        "target__first_name", "target__last_name",
    ]

    fields = ["relationship_type", "source", "target", "get_target_link"]
    extra = 0
    raw_id_fields = ["target", "source", ]
    readonly_fields = ["get_target_link"]
    autocomplete_lookup_fields = {"fk": ["target", "source", ]}
    title = "Admin relationships"

    # temp fix for a quick way to navigate to the organization admins
    def get_target_link(self, obj):
        return '<a href="/admin/myapa/individualcontact/%s/" >%s</a>' % (
            obj.target.id, str(obj.target)
        )

    get_target_link.allow_tags = True
    get_target_link.short_description = "Admin"


admin.site.register(Contact, ContactAdmin)
admin.site.register(IndividualContact, IndividualContactAdmin)
admin.site.register(Organization, OrganizationAdmin)

admin.site.register(ContactRole, ContactRoleAdmin)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, MyApaUserAdmin)

# Re-register UserAdmin
admin.site.unregister(Group)
admin.site.register(Group, MyApaGroupAdmin)

admin.site.register(School, SchoolAdmin)
admin.site.register(ContactRelationship, ContactRelationshipAdmin)
