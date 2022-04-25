from django.db import models

from content.models import Publishable, BaseAddress, Content
from myapa.models.contact import Contact
from myapa.models.constants import ROLE_TYPES, ROLE_SPECIAL_STATUSES, PERMISSION_STATUSES
from planning.models_subclassable import SubclassableModel


class ContactRole(SubclassableModel, Publishable, BaseAddress):
    """
    A connection between a contact and a piece of content...
    perhaps Contact_Content or Contact_ContentRoles is a better name?
    """
    content = models.ForeignKey(Content, related_name='contactrole', on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, related_name='contactrole', null=True, blank=True, on_delete=models.SET_NULL)
    role_type = models.CharField(max_length=50, choices=ROLE_TYPES)
    sort_number = models.PositiveIntegerField(null=True, blank=True)

    confirmed = models.BooleanField(default=False)
    invitation_sent = models.BooleanField(default=False)

    special_status = models.CharField(
        max_length=50,
        choices=ROLE_SPECIAL_STATUSES,
        null=True,
        blank=True
    )
    permission_content = models.CharField(
        max_length=50,
        choices=PERMISSION_STATUSES,
        default="NO_RESPONSE"
    )
    permission_av = models.CharField(max_length=50, choices=PERMISSION_STATUSES, default="NO_RESPONSE")

    # Best place for this??? ... used in awards
    # allows contact to rate the content that they are assigned to...
    content_rating = models.IntegerField(null=True, blank=True)

    first_name = models.CharField(max_length=20, blank=True, null=True)
    middle_name = models.CharField(max_length=20, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    company = models.CharField(max_length=80, blank=True, null=True)
    cell_phone = models.CharField(max_length=20, blank=True, null=True)
    external_bio_url = models.URLField(max_length=255, blank=True, null=True)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.contact:
            return self.role_type_friendly() + " | " + str(self.contact)
        else:
            return self.role_type_friendly() + " | " + str(self.first_name) + " " + str(self.last_name)

    def content_link(self):
        # TODO: fix to lookup appropriate content link for varions content_type and content_areas
        return self.content

    content_link.allow_tags = True
    content_link.short_description = "Content"
    content_link.admin_order_field = "content"

    def contact_link(self):
        # TODO: remove once content_link taken out everywhere
        if self.contact:
            # return '<a href="%s">%s</a>' % (reverse("admin:myapa_contact_change", args=(self.contact.id,)) , escape(self.contact))
            # TO DO: update to use reverse lookup or some other django method (reverse lookup above failed with django 1.8 upgrade)
            return self.contact.get_admin_link()
        else:
            return None

    contact_link.allow_tags = True
    contact_link.short_description = "Contact"
    contact_link.admin_order_field = "contact"

    def get_contact_name(self):
        return self.contact.title if self.contact else "%s %s" % (self.first_name, self.last_name)

    contact_name = property(get_contact_name)

    def get_contact_email(self):
        return self.contact.email if self.contact else self.email

    contact_email = property(get_contact_email)

    def role_type_friendly(self):
        return dict(ROLE_TYPES).get(self.role_type, "")

    def get_solr_role_types(self):
        """
        Get the formatted role types to include in a
        :class:`myapa.models.contact.Contact` Solr document

        :return: dict
        """
        role_types = {
            "contact_roles_{}".format(self.role_type): [
                str(self.content.master_id) + '|' + self.content.title
            ]
        }
        return role_types

    def get_solr_content_tags(self):
        """
        Get the :class:`content.models.tagging.ContentTagType` tags to include in a
        :class:`myapa.models.contact.Contact` Solr document

        :return: set
        """
        content_tag_types = set()
        for ctt in self.content.contenttagtype.all():
            for tag in ctt.tags.all():
                content_tag_types.add(tag.title)
        return content_tag_types

    class Meta:
        verbose_name = "contributor"
        ordering = ['content', 'sort_number']
