import json
import urllib
import os

from django.apps import apps
from django.contrib.auth.models import Group, User
from django.utils import timezone
from django.conf import settings

from planning.settings import RESTIFY_SERVER_ADDRESS

from myapa.models.contact import Contact
from myapa.models.contact_role import ContactRole
from events.models import NATIONAL_CONFERENCE_MASTER_ID
from content.models import ContentTagType
from exam.models import ExamApplicationRole


# JUST TESTING THIS OUT...
# class CustomPermissionGroup(Group):
#     ids = () # ids of anyone auto included in the group

#     def contact_has_group(self, contact):
#         return False

#     class Meta:
#         proxy = True

# class SubscriptionsBasedGroup(CustomPermissionGroup):
#     subscriptions = ()

#     def contact_has_group(self, contact):
#         return False

#     class Meta:
#         proxy = True

# is it even worth making a class for this, or just move this logic into functions or into a view??
class PermissionGroups(object):
    """
    For integrating custom APA permission groups with django
    """
    @staticmethod
    def update(groups_json='myapa/permission_groups.json'):
        """
        Updates django groups from json permsission_groups.json file. New groups are added to django if they don't
        already exist. Groups deleted form the json file are NOT removed from django (perhaps we should auto-remove?)
        """
        with open(os.path.join(settings.BASE_DIR, groups_json)) as groups_file:
            groups_data = json.load(groups_file)

        for group_name in list(groups_data.keys()):
            new_group, created = Group.objects.get_or_create(name=group_name)

    @staticmethod
    def get_contact_groups(user, contact=None, contact_roles=None, groups_json='myapa/permission_groups.json'):
        """
        gets groups for a particular user based off of misc django data for that user/contact record
        """
        print('get_contact_groups groups_json={}'.format(groups_json))

        with open(os.path.join(settings.BASE_DIR, groups_json)) as groups_file:
             group_names = []    
             groups_data = json.load(groups_file)

        if contact is None:

            contact = Contact.objects.get(user__username = user.username)

         
         # QUESTION... IS THIS EVEN NECESSARY, or can we query the roles at the same time as we query the contact
        if contact_roles is None:
            contact_roles = ContactRole.objects.filter(contact=contact)

        for group_name, group_definition in groups_data.items():
            # guilty until proven innocent

            try:

                is_allowed = False 

                # --- adds the django based groups to the list based off the individual user/contact and requirements for each group
                if group_definition.get('source') == 'django' and group_definition.get("check", "group") != "group":

                    logical = group_definition.get('logical')
                    requirement_check = group_definition.get("check")
                    include_contact = group_definition.get("include_contact", False)

                    for requirement in group_definition['requirements']['requirement']:
                        if requirement_check == "hasModelFieldValue":
                            model = apps.get_model(app_label=requirement.get("app"), model_name=requirement.get("model"))
                            filter_dict = requirement.get('conditions')

                            # quick way to add date filters... value = "GET_CURRENT_DATE" in JSON FILE
                            if "GET_CURRENT_DATE" in filter_dict.values():
                                for field, value in filter_dict.items():
                                    if value == "GET_CURRENT_DATE":
                                        filter_dict[field] = timezone.now()

                            meets_requirement = PermissionGroups.has_model_field_value(model, filter_dict, contact, include_contact)

                        elif requirement_check == "isConferenceContact":
                            meets_requirement = PermissionGroups.is_conference_contact(requirement, user, contact, contact_roles)

                        if meets_requirement: 
                            if logical == "or":
                                is_allowed = True
                                break

                            if logical == "and":
                                is_allowed = True
                                continue

                        else:
                            
                            if logical == "and":
                                is_allowed = False
                                break

                            if logical == "or":
                                continue

                    if is_allowed == True:
                        group_names.append(group_name)

            except Exception as e:
                print(str(e))
                pass

        return group_names

    @staticmethod
    def has_model_field_value(model, filter_dict, contact, include_contact):
        """
        checks if field requirements exist
        """
        
        if include_contact:
            meets_requirement = model.objects.filter(contact = contact, **filter_dict).exists()
        else:
            meets_requirement = model.objects.filter(**filter_dict).exists()

        return meets_requirement

    @staticmethod
    def is_conference_contact(requirement, user, contact, contact_roles):
        """
        checks a group of requirements in the requisites list
        """
        # try:
        meets_requirement = False

        # if content has necessary tag id (tag for regular sessions vs. mobile workshops)
        # content is related to current national conference
        # contact is confirmed
        # contact role type is a speaker or organizer
        # check with Alena for other tag types that should get speaker rate

        meets_condition = False
        has_tag_types = False
        for contact_role in contact_roles:

            # gets and determines if an activity tag has the required 'content_tag_code' code
            try:
                content_tagtype = ContentTagType.objects.get(content = contact_role.content, tag_type__code='EVENTS_NATIONAL_TYPE')

                for tag in content_tagtype.tags.all():

                    if tag.code in requirement.get('content_tag_codes'):
                        has_tag_types = True

                if contact_role.content.parent.id == NATIONAL_CONFERENCE_MASTER_ID and has_tag_types and contact_role.confirmed and contact_role.role_type in ['SPEAKER','ORGANIZER']:
                    meets_condition = True
                    break

            except Exception as e:
                continue

        return meets_condition

    @staticmethod
    def get_external_groups(webuserid):
        """
        returns external webgroups from node url.
        """

        external_url = RESTIFY_SERVER_ADDRESS + '/contact/' + webuserid + '/webgroups'

        with urllib.request.urlopen(external_url) as response:
            json_string = response.read().decode('utf-8')
        return json.loads(json_string)

    @staticmethod
    def get_groups(user, contact=None, contact_roles=None, groups_json='myapa/permission_groups.json'):
        """
        combines the external groups and contact groups. returns a list.
        """

        all_groups = PermissionGroups.get_external_groups(user.username)
        print('get_groups groups_json={}'.format(groups_json))
        all_groups.extend(PermissionGroups.get_contact_groups(user, contact, contact_roles, groups_json=groups_json))

        return all_groups

    @staticmethod
    def update_user_groups(username, password='', groups_json='myapa/permission_groups.json'):
        """
        creates django user if none exist and adds/updates groups
        """
        user, user_created = User.objects.get_or_create(username=username)
        print('user_created: {}'.format(user_created))
        print('update user groups is running')
        print('update_user_groups groups_json={}'.format(groups_json))
            
        # django_groups = []
        # remove this exception: no longer allow administrator, editor and author groups
        # to persist -- clear them just like other groups
        # for group_name, group_definition in groups_data.items():
            # if group_definition.get('source') == 'django' and group_definition.get("check") == 'group':
            #     django_groups.append(group_name)
        # clear_groups = user.groups.exclude(name__in=django_groups)
        # user.groups.remove(*clear_groups)

        # WARNING!
        # TO DO... re-enable auto-dropping of staff access
        # user.is_staff = False

        try:
            contact = Contact.objects.get(user__username=username)
        except Contact.DoesNotExist:
            contact = Contact.objects.create(user=user, created_by=user, updated_by=user)

        try:
            contact.sync_from_imis()
        except:
            pass 

        group_names = PermissionGroups.get_groups(user, groups_json=groups_json)
        print('update_user_groups group_names: {}'.format(group_names))

        # clear groups and re-add them...        
        user.groups.clear()
        groups = Group.objects.filter(name__in=group_names).all()
        user.groups.add(*groups)
        if next((True for g in group_names if g in ['staff', 'onsite-conference-admin']), False):
            user.is_staff = True
            # NOTE: originally, any staff users were auto-assigned as superusers... disabling that auto-assignment as of 3/25/16
            # user.is_superuser = True

        # quick way to add chapter admins to staff-store-admin group
        if not user.is_staff and contact.contactrelationship_as_target.all().filter(relationship_type='ADMINISTRATOR').exists():
            # user.is_staff = True

            # WARNING!!!!!!!!!
            # TO DO... this needs to be rethought to only allow admin access for
            # components.... NOT ANY ADMIN FOR ANY ORG!!!!!!!!!!!!!!!
            group = Group.objects.get(name='organization-store-admin')
            user.groups.add(group)

        elif not user.is_staff and user.contact in [x.contact for x in ExamApplicationRole.objects.filter(status="A", title__contains='Staff reviewer')]:
            user.is_staff = True

        user.save()

        return user
    #def get_groups_restify

