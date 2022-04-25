from django.db import models
from django.db.models import Q

from myapa.models.contact import Contact
from myapa.models.constants import CONTACT_RELATIONSHIP_TYPES
from planning.models_subclassable import SubclassableModel


class ContactRelationship(SubclassableModel):
    """
    Model class for relating ORGANIZATION records to INDIVIDUAL records...
    NOTE changed recently to specifically target relationships between individual and org (not any relationships)
    MAY REVISIT THIS IN THE FUTURE...


    TO ACCESS RELATED CONTACTS:
    Use contact.related_contacts ... if "contact" is the source of the relationship
    Use contact.related_contact_sources ... if "contact" is the target of the relationship
    Use Contact.objects.filter( Q(contactrelationship_as_target__source=contact) | Q(contactrelationship_as_source__target=contact) ) ... to get all related contacts
    """
    source = models.ForeignKey(
        Contact,
        help_text="the related organization",
        related_name='contactrelationship_as_source',
        on_delete=models.CASCADE
    )
    target = models.ForeignKey(
        Contact,
        help_text="the related individual",
        related_name='contactrelationship_as_target',
        on_delete=models.CASCADE
    )
    relationship_type = models.CharField(max_length=50, choices=CONTACT_RELATIONSHIP_TYPES)

    @classmethod
    def get_company_contact(cls, user):
        """
        Returns the company contact for an administrative user

        :param user: :class:`django.contrib.auth.models.User`
        :return: :class:`myapa.models.contact.Contact` or None
        """
        company = None

        contact = Contact.objects.get(user__username=user.username)

        # target/source fields don't have a standard in iMIS (goes both ways). We need to check both.
        # ALSO --- better to check iMIS instead of django for relationship???

        try:
            contact_relationship = cls.objects.filter(
                Q(relationship_type="ADMINISTRATOR"),
                (Q(source=contact) | Q(target=contact))
            ).select_related(
                "source", "target"
            ).first()

            if contact_relationship:
                if contact_relationship.source == contact:
                    company = contact_relationship.target
                elif contact_relationship.target == contact:
                    company = contact_relationship.source
        except cls.DoesNotExist:
            pass

        return company

    @classmethod
    def get_company_admin(cls, contact):
        """
        Returns the company admin record for company record passed

        :param contact: :class:`myapa.models.contact.Contact`
        :return: :class:`myapa.models.contact.Contact`
        """

        # target/source fields don't have a standard in iMIS (goes both ways). We need to check both.
        company = None

        try:
            if contact:
                contact_relationship = cls.objects.filter(
                    (
                        Q(relationship_type="ADMINISTRATOR")
                    ),
                    (
                        Q(source=contact) | Q(target=contact)
                    )
                ).first()

                if contact_relationship:
                    if contact_relationship.source == contact:
                        company = contact_relationship.target
                    elif contact_relationship.target == contact:
                        company = contact_relationship.source

        except cls.DoesNotExist:
            pass

        return company

    def __str__(self):
        return str(self.target)
