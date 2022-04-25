from decimal import Decimal

from django.contrib import messages
from django import forms
from django.forms.models import modelformset_factory, model_to_dict
from django.http import Http404

from myapa.models.contact_relationship import ContactRelationship
from myapa.models.contact_role import ContactRole
from content.models import MasterContent, ContentTagType
from events.models import Event

from .models import Answer


def get_submission_record_simple(request, event_master_id):

    event_submission_query = Event.objects.filter(
        master__id=event_master_id, publish_status="SUBMISSION")
    event_draft_query = Event.objects.filter(
        master__id=event_master_id, publish_status="DRAFT")

    if event_submission_query.exists():
        return event_submission_query.first()
    elif event_draft_query.exists():
        messages.error(request, 'There is no submission record for the given event. This application does not yet support creating submissions from existing events that have not gone through the submission process.')
        Http404('Submission Record not Found')
        return None
    else:
        Http404('Submission Record not Found')
        return None


def get_validated_provider(request, event, username): #
    """
    Helper function to validate that a user is an admin for a provider, and that provider owns the event
    """
    provider_relationships = ContactRelationship.objects.select_related('source').filter(target__user__username=username, relationship_type='ADMINISTRATOR') # All of user's provider relationships


    if not provider_relationships.exists():
        # The User is not a valid provider, send them to the dashboard
        messages.error(request, 'To create and edit events you must be a valid CM Provider.')
        provider = None

    elif event is None:
        # This is for a new event
        provider = provider_relationships.first().source #for now it is the first one, later LET USER CHOOSE?

    else:
        # There must already be a submission copy for this record, go from there
        event_provider_role_query = ContactRole.objects.select_related('contact').filter(content=event, role_type="PROVIDER")
        if event_provider_role_query.exists():
            # get the provider for this event
            provider = event_provider_role_query.first().contact # there should only be one
        else:
            # whichever provider saves it, snags it. This should only happen with existing records that have not implemented providers yet, so we should update previous records
            provider = provider_relationships.first().source

        if not provider_relationships.filter(source=provider).exists():
            # User does not belong to the provider that owns this event
            messages.error(request, 'You are not authorized to edit this event.')
            provider = None

    return provider


def init_speaker_formset(request, event):
    """
    Initializes the speaker formset for the event form
    """
    EventSubmissionSpeakersFormset = modelformset_factory(ContactRole, fields=('contact',), widgets={'contact':forms.HiddenInput()}, extra=0, can_delete=True)

    if event is not None:
        speakers = event.contactrole.filter(role_type="SPEAKER").order_by('-confirmed')
    else:
        speakers = ContactRole.objects.none()

    if request.method == 'POST':
        speakers_formset = EventSubmissionSpeakersFormset(request.POST, prefix="speakers") # --------only if not event_type == "EVENT_MULTI"
    else:
        speakers_formset = EventSubmissionSpeakersFormset(queryset=speakers, prefix="speakers")

    return speakers_formset



def process_speaker_formset(speakers_formset, event_instance):
    """
    Processes the post for the speaker formset
    """
    # SAVING THE EVENT SPEAKER CONTACTROLES
    speakers = speakers_formset.save(commit=False)
    for speaker in speakers_formset.changed_objects + speakers_formset.new_objects:
        speaker.content=event_instance
        speaker.role_type="SPEAKER"
        speaker.save()

    # DELETING THE EVENT SPEAKER CONTACTROLES THAT WERE MARKED FOR DELETION
    for speaker in speakers_formset.deleted_objects:
        speaker.delete()


# function to validate that an event/activity has all required fields for submission
def event_is_valid_for_submission(request, event, theEventForm, is_final=False):
    """
    returns a tuple,
    the first is a boolean that is True if the event is valid for submission
    the second is a list of things that need to be fixed before submission
    """
    model_dict = model_to_dict(event) #model_to_dict(event)
    # Not actually submitting through form, but want to get the initial values from init,
    # then anything that is a choice field or not in the model needs to be retrieved
    # (This is reeeeeealy lazy, but it should work...)
    submission_form_initial = theEventForm(None, instance=event)
    for key, field in submission_form_initial.fields.items():
        if field.initial is not None and (key not in model_dict or model_dict[key] is None):
            model_dict[key] = field.initial
    submission_form = theEventForm(model_dict, instance=event, is_final=is_final)

    return (submission_form.is_valid(), submission_form)


def event_submission_delete(request, event_master_id):
    """
    Will delete the submission if there is no draft copy. Will mark submission for deletion (status "X", a drafy copy exists)
    Returns True if deleted or marked for deletion.

    (However we want to handle event submission removals...put the logic in this function)
    """

    # OLD QUESTIONS:
    # HOW DO WE WANT TO HANDLE MULTI EVENT SUBMISSIONS?
    # DELETE ALL CHILD ACTIVITIES AS WELL?
    # WOULD IT BE BETTER TO MARK THE MASTER CONTENT RECORD FOR DELETION INSTEAD OF THE ACTUAL RECORD?

    # "Deleting" a draft event from CM Provider:
    # 1. remove the provider as the role
    # 2. change the CM status to inactive,
    # 3. change the CM credits (approved field(s)) to 0
    # 4. change the visibility status to marked for deletion.
    # 5. For a session on a multipart event, remove the parent link.

    event_submission_query = Event.objects.filter(publish_status="SUBMISSION", master__id=event_master_id)
    event_draft_query = Event.objects.filter(publish_status="DRAFT", master__id=event_master_id)
    event_published_query = Event.objects.filter(publish_status="PUBLISHED", master__id=event_master_id)
    if event_published_query.exists():
        ContactRole.objects.filter(content__master__id=event_master_id, role_type="PROVIDER", content__publish_status="PUBLISHED").delete()
        event_published_query.update(cm_status="I")
        event_published_query.update(cm_approved=Decimal('0.00'))
        event_published_query.update(cm_law_approved=Decimal('0.00'))
        event_published_query.update(cm_ethics_approved=Decimal('0.00'))
        event_published_query.update(status="X")
        event_published_query.update(parent=None)

        messages.success(request,"Successfully marked published record %s for deletion" % event_master_id)

    if event_draft_query.exists():
        ContactRole.objects.filter(content__master__id=event_master_id, role_type="PROVIDER", content__publish_status="DRAFT").delete()
        event_draft_query.update(cm_status="I")
        event_draft_query.update(cm_approved=Decimal('0.00'))
        event_draft_query.update(cm_law_approved=Decimal('0.00'))
        event_draft_query.update(cm_ethics_approved=Decimal('0.00'))
        event_draft_query.update(status="X")
        event_draft_query.update(parent=None)
        for draft in event_draft_query:
            published_object = draft.publish()
            published_object.solr_publish()

        messages.success(request,"Successfully marked draft record %s for deletion" % event_master_id)
        return True
    elif event_submission_query.exists():
        # delete any relationships
        ContactRole.objects.filter(content__master__id=event_master_id).delete()
        ContentTagType.objects.filter(content__master__id=event_master_id).delete()
        Answer.objects.filter(content__master__id=event_master_id).delete()
        #Delete the submission, and the Master Content record
        event_submission_query.delete()
        MasterContent.objects.filter(id=event_master_id).delete()

        messages.success(request,"Successfully deleted record %s" % event_master_id)
        return True
    else:
        messages.error(request,"Failed to delete submission record for %s because it could not be found" % event_master_id)
        return False





