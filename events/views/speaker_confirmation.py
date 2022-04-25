from django.http import Http404
from django.shortcuts import render, redirect
from django.contrib import messages

from myapa.models.contact import Contact
from myapa.models.contact_role import ContactRole
from myapa.forms import ContactBioForm, MergeContactRolesForm
from myapa.utils import is_authenticated_check_all


###############################################################
# TODO: IF WE ARE NOT CONFIRMING SPEAKERS FOR REGULAR EVENTS,
#       THEN DELETE THIS FILE AND REMOVE URL ROUTING
###############################################################


# ARE WE USING THIS TO CONFIRM SPEAKERS FOR REGULAR EVENTS?
# TODO: REMOVE THIS. This is handled by Cadmium, 
# This can be used for any content_type but currently using for events
# Should we refactor and move to myapa so that this makes more sense used for other content_types?
def contactrole_confirm(request, **kwargs):
    """
    confirms an unconfirmed contact role and assigns the contact to the logged in user's contact record
    """

    is_authenticated, username = is_authenticated_check_all(request) # authentication check

    confirm_role_id = kwargs.get("confirm_role_id", None)
    confirm_role_query = ContactRole.objects.select_related('content','content__event').filter(id=confirm_role_id)   # the contact_role that is being directly confirmed

    # initial values
    confirm_role = None #this will change if actually trying to confirm something
    context = {}

    if is_authenticated:

        contact = Contact.objects.get(user__username=username)

        if confirm_role_query.exists():

            confirm_role = confirm_role_query.first()
            confirm_role.is_conference_activity = confirm_role.content.event.is_conference_activity()

            # so we can update any other versions of this contact role as well
            content = confirm_role.content
            content_master = content.master
            role_type = confirm_role.role_type
            old_contact = confirm_role.contact

            if not old_contact or old_contact == contact:


                context["contact"] = contact
                context["confirm_role"] = confirm_role # change this when ready

                if request.method == "POST":
                    # either confirming role, editing permissions, merging records, or editing profile
                    # may just want to do each of these on separate pages though
                    ContactRole.objects.filter(publish_uuid=confirm_role.publish_uuid).update(contact=contact, confirmed=True)

                    # update the permissions for any other of user's roles for this event as well (for consistency)
                    if confirm_role.is_conference_activity:
                        permission_av = request.POST.get("permission_av", "PERMISSION_DENIED")
                        permission_content = request.POST.get("permission_content", "PERMISSION_DENIED")
                        all_user_roles_for_activity = ContactRole.objects.filter(contact=contact, content__master=confirm_role.content.master).update(permission_av=permission_av, permission_content=permission_content)


                    messages.success(request, 'You have confirmed your participation in "%s." To complete the confirmation process, please verify and submit any changes to your profile information' % confirm_role.content)


                    return redirect("/events/speaker/confirm/update_bio/")

                else:

                    # this block is duplicated in post as well....
                    confirm_role_id = request.GET.get("confirm_role_id", None)
                    confirm_role_query = ContactRole.objects.select_related('content','content__event').filter(id=confirm_role_id)
                    if confirm_role_query.exists():
                        confirm_role = confirm_role_query.first()
                        confirm_role.is_conference_activity = confirm_role.content.is_conference_activity()

                    return render(request, "events/oldtheme/contact-role-confirm.html", context)

            else:
                messages.error(request, 'Cannot confirm participation in "%s." Please verify with the organizer that you have a role in this event.' % confirm_role.content)
                # TO DO ... should change this redirect
                return redirect("/conference/")
        else:
            raise Http404("ERROR: This link does not match any event role records in our database. Please verify with the organizer that you were not removed from this activity or contact customer service for assistance.")
    else:
        return redirect("/login/?next=%s" % request.path)


# ARE WE USING THIS TO CONFIRM SPEAKERS FOR REGULAR EVENTS?
# TODO: REMOVE THIS. This is handled by Cadmium
#   ...PLUS IT"S REALLY OLD
def contactrole_confirm_bio(request, **kwargs):
    """
    View for after user confirms contactrole. This asks user to update bio.
    """

    is_authenticated, username = is_authenticated_check_all(request) # authentication check

    post_is_successful = False
    context = {}

    if is_authenticated:

        contact = Contact.objects.get(user__username=username)

            
        if request.method == "POST":
            profile_form = ContactBioForm(request.POST, instance=contact, prefix="update_profile")
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Successfully updated your bio.")
                post_is_successful = True
            else:
                messages.error(request, "Failed to update bio. Please check that all required fields are valid and try again.")
        else:
            profile_form = ContactBioForm(None, instance=contact, prefix="update_profile")


        context["contact"] = contact
        context["profile_form"] = profile_form

        # handle merge conflict stuff
        merge_contact_id = request.POST.get('contact_giver_id', request.GET.get('merge_contact_id', None))
        if merge_contact_id is not None:
            try:
                old_contact = Contact.objects.get(id=merge_contact_id)
                remaining_old_contact_roles = ContactRole.objects.select_related("content","content__master","content__event").filter(contact__id=merge_contact_id).order_by("content__master").distinct("content__master")
                
                # no longer use anonymous contacts...
                if str.startswith(old_contact.user.username, "A") and remaining_old_contact_roles.exists():

                    if request.method == "POST":
                        merge_contactroles_form = MergeContactRolesForm(request.POST, initial={'contact_giver_id':old_contact.id, 'contact_receiver_id':contact.id}, prefix="merge_roles")
                        if merge_contactroles_form.is_valid() and profile_form.is_valid():
                            merge_contactroles_form.save()
                            messages.success(request, "Successfully merge user accounts")
                            old_contact.delete()
                        else:
                            post_is_successful = False

                    else:
                        merge_contactroles_form = MergeContactRolesForm(None, initial={'contact_giver_id':old_contact.id, 'contact_receiver_id':contact.id}, prefix="merge_roles")

                    context["merge_contact"] = old_contact
                    context["remaining_old_contact_roles"] = remaining_old_contact_roles
                    context["merge_contactroles_form"] = merge_contactroles_form
            except Contact.DoesNotExist:
                pass # just ignore if trying to merge record that does not exist


        context["post_is_successful"] = post_is_successful
        return render(request, "events/oldtheme/contact-role-confirm-complete.html", context)

    else:
        return redirect("/login/?next=%s" % request.path)
