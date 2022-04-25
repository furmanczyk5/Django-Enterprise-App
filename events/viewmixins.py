from django.shortcuts import render

from imis.enums.relationship_types import ImisRelationshipTypes
from myapa.models.contact_relationship import ContactRelationship
from myapa.models.contact import Contact
from myapa.models.contact_role import ContactRole
from myapa.viewmixins import AuthenticateLoginMixin
from submissions.models import Category
from cm.enums.messages import ProviderRestrictionMessages
from cm.models import Provider


class AuthenticateProviderMixin(AuthenticateLoginMixin):
    """
    Checks if user is an admin for a valid provider,
    and restricts access to content that the provider is owner of

    Assumes the View you are using implements a set_content method
    """

    active_providers_only = False
    restriction_message = ProviderRestrictionMessages.DEFAULT.value

    def is_validated_provider(self, request):

        contact = request.user.contact
        provider_relationships = contact.get_imis_source_relationships().filter(
            relation_type__in=(
                ImisRelationshipTypes.ADMIN_I.value,
                ImisRelationshipTypes.CM_I.value
            )
        )

        if not provider_relationships.exists():
            # The user is not a valid admin for ANY provider, NOT VALID
            self.restriction_message = ProviderRestrictionMessages.NO_PROVIDER_ACCOUNT.value
            provider = None

        elif getattr(self, "content", None) is None:
            # The user is a admin for some Provider
            # There is not a content record tied to this view, so just being an admin for a provider is enough to validate
            # e.g. new event form, dashboard,
            # provider = provider_relationships.first().source #for now it is the first one, later LET USER CHOOSE?
            provider = Contact.objects.filter(
                user__username=provider_relationships.last().target_id
            ).first()
        else:

            # TO DO... simplify the following checks? (could refactor)

            # There must already be a submission copy for this record, go from there
            event_provider_role_query = ContactRole.objects.select_related('contact').filter(content=self.content, role_type="PROVIDER")
            if event_provider_role_query.exists():
                # get the provider for this event
                self.provider_role = event_provider_role_query.first()
                provider = self.provider_role.contact # there should only be one
            else:
                # whichever provider saves it, snags it. This should only happen with existing records that have not implemented providers yet, so we should update previous records
                # provider = provider_relationships.first().source
                provider = Contact.objects.filter(
                    user__username=provider_relationships.last().target_id
                ).first()

            # if not provider_relationships.filter(source=provider).exists():
            if not provider or not Contact.objects.filter(pk=provider.pk).exists():
                # User does not belong to the provider that owns this event
                self.restriction_message = """You are not authorized to view this content. If you feel this is incorrect please <a href="/customerservice/contact-us/">contact us</a>"""
                provider = None

        # Get the proxy Provider instance, not the Contact instance
        if provider is not None:
            provider.__class__ = Provider

        # CHECK IF ACTIVE
        if self.active_providers_only and provider is not None:
            # TO DO... this should check for application that's approved and end_date in the future
            provider_applications = provider.applications.filter(status="A") # could possibly be setting up event for following year?
            if provider_applications.exists():
                pass
                # self.provider_registration_type = provider_registration.first().registration_type
            else:
                self.restriction_message = "%s is not an active provider. To perform this action you must first complete the <a href='/cm/provider/application/'>Provider Application</a>." % provider.title
                return (False, provider)

        return (provider is not None, provider)

    def authenticate(self, request, *args, **kwargs):

        authentication_response = super().authenticate(request, *args, **kwargs)

        if authentication_response is not None:
            return authentication_response
        else:
            if hasattr(self, "set_content"):
                self.set_content(request, *args, **kwargs)
            is_valid_provider, self.provider = self.is_validated_provider(request)

            if not is_valid_provider:
                if hasattr(self, "provider_check"):
                    return None
                return render(request, "myapa/newtheme/member-access-only.html", {"access_denied_message":self.restriction_message})
            else:
                return None


class ProviderEventSubmissionMixin(AuthenticateProviderMixin):
    """
    View Mixin intended to be used with the FormView Class Based View
    """

    category_per_credit_code = "CM_EVENT_PER_CREDIT"
    #... 2008-2015 events get a separate category code because they have unique pricing...
    category_per_credit_code_2015 = "CM_EVENT_PER_CREDIT_2015"
    category_unlimited_registration_code = "CM_EVENT_ANNUAL_SUBSCRIPTION"

    active_providers_only = True

    # Flags used to determine if provider has credentials for this submission
    _reg_pending_approval_restriction = False # make property or method on models...
    _provider_application_restriction = False

    def reset_display_errors(self):
        self.display_errors = [] # django is storing this, so need to reset?

    def set_submission_category(self, request, *args, **kwargs):
        """
        Assigns the submission category based on the state and context of the submission
        NOTE: unlike the set_submission_category method,
        """

        if self.content and self.content.begin_time:

            begin_time = self.content.begin_time

            if begin_time and not self.provider.applications.filter(end_date__gt=begin_time.date(), status="A").exists():
                self._provider_application_restriction = True
                # self.display_errors.append("The begin date for this event does not fall within a period for which you have been approved as a CM provider.")

            annual_unlimited_list = self.provider.registrations.filter(
                year=self.content.begin_time.year,
                status__in=["A", "P"],
                is_unlimited=True
            )
            is_unlimited = False
            is_active_unlimited = False
            for reg in annual_unlimited_list:
                is_unlimited = True # if has any unlimited
                if reg.status == "A":
                    is_active_unlimited = True # if any are active

            if is_unlimited and not is_active_unlimited:
                self._reg_pending_approval_restriction = True

            if is_unlimited:
                correct_code = self.category_unlimited_registration_code
            else:
                correct_code = self.category_per_credit_code_2015 \
                    if self.content.begin_time.year <= 2015 \
                    else self.category_per_credit_code

            if not self.content.submission_category or self.content.submission_category.code != correct_code:
                self.content.submission_category = Category.objects.get(code=correct_code)
                self.content.save()

            self.submission_category = self.content.submission_category

        else:
            # Technically has no inherited method for this,
            #     so always use with a FormView that does
            super().set_submission_category(request, *args, **kwargs)


    def setup(self, request, *args, **kwargs):
        self.reset_display_errors()
        super().setup(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["display_errors"] = self.display_errors
        return context



#
# REMOVING SPEAKER FORMSET FROM PAGES LIKE THIS AND SEPARATING OUT
#   EVENT SUBMISSION PROCESS INTO MULTIPLE STEPS: 1)GENERAL INFO, 2)ADD SPEAKERS
#
# class EventSubmissionMixin(object):
#     """
#     Mixin for defining useful methods specific to Event Submissions
#     """
#     # sets
#     #   speakers
#     #   speaker_formset

#     display_errors = []

#     def reset_display_errors(self):
#         self.display_errors = [] # django is storing this, so need to reset?

#     def init_speaker_formset(self, request):
#         """
#         Initializes the speaker formset for the event form
#         """
#         EventSubmissionSpeakersFormset = modelformset_factory(ContactRole, fields=("contact", "id"), formset=SubmissionSpeakerFormset, widgets={'contact':forms.HiddenInput(), "id":forms.HiddenInput()}, can_delete=True, extra=0)

#         if self.content is not None:
#             speakers = self.content.contactrole.filter(role_type="SPEAKER").order_by('-confirmed')
#         else:
#             speakers = ContactRole.objects.none()

#         if request.method == 'POST':
#             speaker_formset = EventSubmissionSpeakersFormset(request.POST, queryset=speakers, prefix="speakers", is_strict=self.is_strict)
#         else:
#             speaker_formset = EventSubmissionSpeakersFormset(queryset=speakers, prefix="speakers", is_strict=self.is_strict)

#         self.speakers = speakers
#         self.speaker_formset = speaker_formset


#     def process_speaker_formset(self):
#         """
#         Processes the post for the speaker formset, (init_speaker_formset must be called first)
#         """
#         # SAVING THE EVENT SPEAKER CONTACTROLES
#         speakers = self.speaker_formset.save(commit=False)
#         for speaker in self.speaker_formset.changed_objects + self.speaker_formset.new_objects:
#             speaker.content=self.content
#             speaker.role_type="SPEAKER"
#             speaker.publish_status = "SUBMISSION"
#             speaker.save()

#         # DELETING THE EVENT SPEAKER CONTACTROLES THAT WERE MARKED FOR DELETION
#         for speaker in self.speaker_formset.deleted_objects:
#             speaker.delete()

#         self.speakers = speakers

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["display_errors"] = self.display_errors
#         return context


