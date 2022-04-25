from datetime import timedelta

from django.utils import timezone

from imis.enums.relationship_types import ImisRelationshipTypes
from imis.enums.members import ImisMemberTypes, ImisMemberStatuses, ImisNameAddressPurposes
from imis.models import OrgDemographics, Relationship, Counter, MeetMaster
from imis.tests.factories.name import ImisNameFactoryBlank, ImisNameFinFactoryBlank
from imis.tests.factories.name_address import ImisNameAddressFactoryBlank
from imis.tests.factories.ind_demographics import ImisIndDemographicsFactoryBlank
from imis.tests.factories.demographics import OrgDemographicsFactoryBlank, MailingDemographicsFactoryBlank
from imis.tests.factories.relationship import RelationshipFactoryBlank
from myapa.models.constants import DjangoOrganizationTypes
from myapa.models.contact import Contact
from myapa.models.contact_content_added import ContactContentAdded
from myapa.models.contact_relationship import ContactRelationship
from myapa.models.managers import BookmarkManager, SchoolManager, ProviderManager


class IndividualContact(Contact):
    class_query_args = {
        "contact_type": "INDIVIDUAL"
    }

    class Meta:
        proxy = True

    def create_imis_relationship(self, co_id, relation_type):
        """
        Create Relationship records that link this IndividualContact
        with an Organization
        :param co_id: str, the iMIS id of the organization
        :param relation_type: str, one of the values of
               :class:`imis.enums.relationship_types.ImisRelationshipTypes`
        :return: :class:`imis.models.Relationship`
        """
        now = timezone.now()
        relationship = RelationshipFactoryBlank(
            id=self.user.username,
            target_id=co_id,
            relation_type=relation_type,
            target_relation_type=getattr(
                ImisRelationshipTypes,
                "{}_RECIPROCAL".format(relation_type),
                ImisRelationshipTypes.BLANK_LABEL
            ).value,
            seqn=Counter.create_id('Relationship'),
            last_updated=now,
            date_added=now,
            updated_by='WEBUSER'
        )
        relationship.save()

        name = self.get_imis_name()
        name.co_id = co_id
        name.save()

        return relationship


class StaffContact(IndividualContact):
    class_query_args = {
        "contact_type": "INDIVIDUAL",
        "user__is_staff": True
    }

    class Meta:
        proxy = True
        verbose_name = "APA staff / admin user"


class Organization(Contact):
    class_query_args = {
        "contact_type": "ORGANIZATION"
    }

    class Meta:
        proxy = True

    def get_imis_org_demographics(self):
        return OrgDemographics.objects.filter(id=self.user.username)

    def update_or_create_relationships_from_imis(self):
        """
        Update or create :class:`myapa.models.contact_relationship.ContactRelationship`
        from this Organization's record in the iMIS Relationship table.
        :return: None

        TODO: This is assuming the Relationship table in iMIS is the source of truth for
        these relationships. Also, what is the difference between ContactRelationships
        and company_fk (e.g., :meth:`myapa.models.contact.Contact._sync_parent_org` )?

        also TODO: This currently only works for org ; need one for the admins too?

        also also TODO: this will no longer be needed given that iMIS alone will
        be the sole source of Relationships now
        """
        relationships = Relationship.objects.filter(
            target_id=self.user.username,
            relation_type__in=(
                ImisRelationshipTypes.ADMIN_I.value,
                ImisRelationshipTypes.BILLING_I.value,
                ImisRelationshipTypes.CM_I.value
            )
        )
        if not relationships.exists():
            # TODO: finish the "_or_create" part of this method name
            return
        # clear out existing relationships (in case some were removed from iMIS)
        ContactRelationship.objects.filter(target=self).delete()
        # then [re-]add
        for relationship in relationships:
            # update or create all targets
            source_contact = Contact.update_or_create_from_imis(relationship.id)
            # TODO: clean this up (see note above myapa.models.constants.CONTACT_RELATIONSHIP_TYPES)
            relation_type = 'ADMINISTRATOR' \
                if relationship.relation_type in (
                    ImisRelationshipTypes.ADMIN_I.value, ImisRelationshipTypes.CM_I.value
                ) else relationship.relation_type
            ContactRelationship.objects.update_or_create(
                source=source_contact,
                target=self,
                relationship_type=relation_type
            )

    def get_admin_contacts(self):
        """
        Get the :class:`myapa.models.contact.Contact` who have ADMIN_I/CM_I
        entries in the iMIS Relationships table
        :return: :class:`django.db.models.query.QuerySet`
        """
        rel_sources = self.get_imis_target_relationships().filter(
            relation_type__in=(
                ImisRelationshipTypes.ADMIN_I.value,
                ImisRelationshipTypes.CM_I.value
            )
        )
        return Contact.objects.filter(
            user__username__in=[x.id for x in rel_sources]
        )

    def imis_create(self, **kwargs):
        name = self._imis_create_name()
        name_address = self._imis_create_name_address(name.id)
        name.full_address = name_address.full_address
        name.company_sort = name_address.get_company_sort()
        name.set_address_num_fields(name_address.address_num)
        name_address.save()
        self.create_id_only_records(name.id)
        org_demo = OrgDemographicsFactoryBlank(id=name.id, org_type=kwargs.get('org_type', ''))
        org_demo.save()
        self.insert_name_security(name.id)
        self.insert_name_picture(name.id)
        self.insert_name_log_record(
            dict(
                date_time=self.getdate(),
                log_type="CHANGE",
                sub_type="ADD",
                user_id="WEBUSER",
                id=name.id,
                log_text=''
            )
        )
        self.insert_name_security_groups(name.id)
        name.save()
        return name

    @staticmethod
    def create_id_only_records(name_id):
        """
        Create necessary records (empty other than the Name id)
        :param name_id: str
        :return: None
        """

        ind_demo = ImisIndDemographicsFactoryBlank(id=name_id)
        ind_demo.save()
        name_fin = ImisNameFinFactoryBlank(id=name_id)
        name_fin.save()
        mdemo = MailingDemographicsFactoryBlank(id=name_id)
        mdemo.save()

    def _imis_create_name(self):
        name = ImisNameFactoryBlank(
            id=Counter.create_id('Name'),
            org_code='APA',
            member_type=self.get_imis_member_type(),
            status=ImisMemberStatuses.ACTIVE.value,
            company_record=True,
            company=self.company,
            work_phone=self.phone,
            city=self.city,
            state_province=self.state,
            country=self.country,
            zip=self.zip_code,
            source_code='WEB',
            website=self.personal_url
        )
        return name

    def _imis_create_name_address(self, name_id):
        name_address = ImisNameAddressFactoryBlank(
            id=name_id,
            address_num=Counter.create_id('Name_Address'),
            purpose=ImisNameAddressPurposes.WORK_ADDRESS.value,
            company=self.company,
            address_1=self.address1,
            address_2=self.address2,
            city=self.city,
            state_province=self.state,
            zip=self.zip_code,
            country=self.country,
        )
        name_address.full_address = name_address.get_full_address()
        return name_address

    def get_imis_member_type(self):
        """
        Mapping of our :const:`myapa.models.constants.ORGANIZATION_TYPES` to a
        :class:`imis.enums.members.ImisMemberTypes`
        :return: str
        """
        mapping = {
            DjangoOrganizationTypes.PR001.value: ImisMemberTypes.SCH.value,
            DjangoOrganizationTypes.PR002.value: ImisMemberTypes.PRI.value,
            DjangoOrganizationTypes.PR003.value: ImisMemberTypes.PRI.value,
            DjangoOrganizationTypes.PR005.value: ImisMemberTypes.PRI.value,
            DjangoOrganizationTypes.PR006.value: ImisMemberTypes.PRI.value,
            DjangoOrganizationTypes.P001.value: ImisMemberTypes.AGC.value,
            DjangoOrganizationTypes.P002.value: ImisMemberTypes.AGC.value,
            DjangoOrganizationTypes.P003.value: ImisMemberTypes.AGC.value,
            DjangoOrganizationTypes.P004.value: ImisMemberTypes.AGC.value,
            DjangoOrganizationTypes.P005.value: ImisMemberTypes.AGC.value,
            DjangoOrganizationTypes.P999.value: ImisMemberTypes.AGC.value,
            DjangoOrganizationTypes.PR004.value: ImisMemberTypes.AGC.value,
        }
        return mapping.get(self.organization_type, None)

    def get_meet_master(self, **kwargs):
        return MeetMaster.objects.filter(contact_id=self.user.username, **kwargs)

    @property
    def location_label(self):
        data = dict(
            city=self.city or '',
            state=self.state or '',
            country=self.country or ''
        )
        return '{city}, {state}, {country}'.format(**data)

    @property
    def has_apa_event(self):
        """If this is an APA Chapter or Division, does it have events in iMIS?"""
        # 3-week grace period beyond event begin date
        grace_period = timezone.now() - timedelta(days=21)
        return self.company_is_apa and self.get_meet_master(
            status='A',
            end_date__gt=grace_period
        ).exists()


class School(Organization):
    class_query_args = {
        "contact_type": "ORGANIZATION",
        "member_type": "SCH"
    }

    objects = SchoolManager()

    class Meta:
        proxy = True

    def get_program_type(self):
        """
        Get the school program type
        :return: str
        """
        org_demo = self.get_imis_org_demographics().first()
        if org_demo is not None:
            return org_demo.school_program_type

    def sync_from_imis(self):
        """
        Sync as a normal Contact, with some additional processing
        for school accreditations and relationships
        :return: None
        """

        # sync normally
        super().sync_from_imis()

        # sync with free_students.models.AccreditedSchool
        # importing here to avoid circular import
        from free_students.models import AccreditedSchool, Accreditation
        accreditedschool, _ = AccreditedSchool.objects.get_or_create(school=self)

        # sync program types
        school_program_type = self.get_program_type()
        if school_program_type:
            # clear out and re-add this school's accreditations
            accreditedschool.accreditation.clear()
            for program_type in school_program_type.split(','):
                accreditedschool.accreditation.add(
                    Accreditation.objects.filter(
                        accreditation_type=program_type
                    ).first()
                )

        # add relationships if they exist
        self.update_or_create_relationships_from_imis()


class Bookmark(ContactContentAdded):
    objects = BookmarkManager()

    class Meta:
        proxy = True


class Provider(Contact):

    objects = ProviderManager()

    class Meta:
        proxy = True
        verbose_name = "CM Provider"
        verbose_name_plural = "CM Providers"
