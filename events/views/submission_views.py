from django.forms.models import modelformset_factory
from django.views.generic import View, TemplateView, FormView
from django.shortcuts import render
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib import messages
from django.http import Http404
from django.http.response import HttpResponseRedirect
from django.db.models import Prefetch

from myapa.models.contact import Contact
from myapa.models.contact_role import ContactRole
from submissions.viewmixins import SubmissionMixin
from submissions.views import SubmissionEditFormView, \
    SubmissionReviewFormView
from submissions.utils import event_submission_delete

from store.models import ProductCart, ProductOption, Purchase, ProductPrice
from cm.models import ProviderRegistration

from events.models import EventMulti, Activity, Event, EventSingle, Course, \
    EventInfo, Speaker
from events.forms import EventSingleForm, EventSingleOnlineForm, \
    EventMultiForm, EventActivityForm, EventCourseForm, \
    EventSubmissionVerificationForm, ProviderSpeakerForm, \
    EventInfoForm
from events.viewmixins import AuthenticateProviderMixin, \
    ProviderEventSubmissionMixin


########################################
# # BASE VIEWS FOR EVENT SUBMISSIONS # #
########################################


class EventSubmissionEditFormView(SubmissionEditFormView):

    form_class = EventSingleForm
    home_url = reverse_lazy("myorg")
    success_url = "/cm/provider/events/{master_id}/speakers/"
    save_url = "/cm/provider/events/{master_id}/update/"
    default_publish_status = "DRAFT"


class EventSubmissionSpeakerFormsetView(FormView):

    form_class = ProviderSpeakerForm
    success_url = ""
    extra_forms = 1
    min_num = 1
    is_strict = True
    template_name = "events/newtheme/submission/speakers.html"
    default_publish_status = "DRAFT"

    def set_content(self, *args, **kwargs):
        if not hasattr(self, "content"):
            self.content = Event.objects.get(master_id=kwargs.get("master_id"), publish_status=self.default_publish_status)

    def setup(self, *args, **kwargs):
        self.set_content(*args, **kwargs)
        self.queryset = ContactRole.objects.filter(content=self.content, role_type="SPEAKER")
        if self.request.POST.get("submitButton", "submit") == "save":
            self.is_strict = False

    def get(self, request, *args, **kwargs):
        self.setup(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.setup(request, *args, **kwargs)
        return super().post(request, *args, **kwargs)

    def get_form_class(self):
        formset_kwargs = dict(extra=0, min_num=self.min_num, can_delete=True)
        if self.queryset.exists():
            formset_kwargs["extra"] = self.extra_forms
        if self.is_strict:
            formset_kwargs["validate_min"] = True
        return modelformset_factory(Speaker, self.form_class, **formset_kwargs)

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["queryset"] = self.queryset
        return form_kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial["content"] = self.content
        formset_initial = [initial for i in range(self.queryset.count() + self.extra_forms)]
        return formset_initial

    def form_valid(self, form):

        # is there a better way to save and delete these in one shot, while ignoring empty forms?
        # for f in form.save():
        #     if f.is_populated():
        #         f.save()
        # for obj in formset.deleted_objects:
        #     obj.delete()

        form.save() # How does this know not to save the "Add a speaker form when it's blank?"

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            "There was a problem processing the speakers for this event. "
            "Please ensure all required fields have been filled out for all speakers "
            "and try again."
        )
        return super().form_invalid(form)

    def get_success_url(self):
        if self.request.POST.get("submitButton", "submit") == "submit":
            return self.success_url.format(master_id=self.content.master_id)
        else:
            return self.request.get_full_path()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["content"] = self.content
        context["home_url"] = self.home_url
        return context


class EventSubmissionReviewFormView(SubmissionReviewFormView):

    preview_template = "events/newtheme/includes/event-details.html"
    home_url = reverse_lazy("myorg")
    success_url = reverse_lazy("myorg")
    edit_url = "/cm/provider/events/{master_id}/update/"
    default_publish_status = "DRAFT"

    def query_content(self, master_id):
        query = super().query_content(master_id).prefetch_related(
            Prefetch("contactrole", queryset=ContactRole.objects.filter(role_type="SPEAKER").select_related("contact"), to_attr="speaker_roles")
        )
        return query

#########################################################
# #                                                   # #
# #            PROVIDER EVENT SUBMISSIONS             # #
# #                                                   # #
#########################################################


class ProviderEventSubmissionEditFormView(ProviderEventSubmissionMixin, EventSubmissionEditFormView):

    def get_initial(self):
        initial = super().get_initial()

        contact_info_source = getattr(self, "provider_role", self.request.user.contact)
        contact_info = dict(contact_email=contact_info_source.email, contact_firstname=contact_info_source.first_name, contact_lastname=contact_info_source.last_name)
        initial.update(contact_info)

        return initial

    def after_save(self, form):
        # if provider role record does not exist yet for this record, then create one

        provider_role_defaults = dict(publish_status=self.default_publish_status, confirmed=True)

        provider_role_defaults.update(dict(
            email=form.cleaned_data.get("contact_email", None),
            first_name=form.cleaned_data.get("contact_firstname", None),
            last_name=form.cleaned_data.get("contact_lastname", None)
        ))

        ContactRole.objects.update_or_create(
            contact=self.provider,
            content=self.content,
            role_type="PROVIDER",
            defaults=provider_role_defaults
        )

        return super().after_save(form)


class ProviderEventSubmissionSpeakerFormsetView(EventSubmissionSpeakerFormsetView):
    title = "Add Speakers"
    success_url = "/cm/provider/events/{master_id}/review/"
    home_url = reverse_lazy("myorg")


class ProviderEventSubmissionReviewFormView(
    ProviderEventSubmissionMixin,
    EventSubmissionReviewFormView
):

    form_class = EventSubmissionVerificationForm

    def after_save(self, form):
        if not self.requires_checkout:
            self.content.provider_submit_async() # SEND EMAILS IN PROVIDER_SUBMIT
            messages.success(self.request, "Successfully published %s" % self.content.title)

        # FLAGGED FOR REFACTORING: SPEAKER DELETE
        if self.content.publish_status == "DRAFT":
            draft_role_publish_uuids = ContactRole.objects.filter(content=self.content).values('publish_uuid')
            draft_publish_uuids = [v.get('publish_uuid') for v in draft_role_publish_uuids]
            published_event = self.content.get_versions().get('PUBLISHED')

            if published_event:
                published_contact_roles = ContactRole.objects.filter(content=published_event)

                for s in published_contact_roles:

                    if s.publish_uuid not in draft_publish_uuids:
                        s.delete()

        super().after_save(form)

    def get_checkout_required(self):
        requires_checkout = super().get_checkout_required()
        self.total_cm_credits = self.content.get_total_cm_credits()

        requires_checkout = requires_checkout \
            and (self.content.submission_category.code == "CM_EVENT_PER_CREDIT"
                 or self.content.submission_category.code == "CM_EVENT_PER_CREDIT_2015")\
            and self.total_cm_credits > 0

        # if an active published copy exists no checkout required unless more credits were added:
        live_copy = Event.objects.filter(master_id=self.content.master_id, publish_status="PUBLISHED").first()
        if requires_checkout and live_copy and live_copy.cm_status == 'A':
            submission_cm_credits = self.total_cm_credits
            live_cm_credits = live_copy.get_total_cm_credits()
            requires_checkout = submission_cm_credits > live_cm_credits
        return requires_checkout

    def form_is_valid(self, form):
        is_valid = super().form_is_valid(form)

        # prevent submission if provider not approved for time period
        if self._provider_application_restriction:
            self.display_errors.append("""
                You cannot register this event at this time, either because you were not an eligible CM provider as of the event’s start date, or because your application to become (or continue to be) an eligible CM provider is still under review. Please contact APA at <a href="mailto:aicpcm@planning.org">aicpcm@planning.org</a> for assistance.
                """.format(self.content.begin_time.year))
            is_valid = False

        # prevent submission if user's annual registration is pending payment
        elif self._reg_pending_approval_restriction:
            self.display_errors.append("""
                Our records indicate that you have an annual unlimited plan pending approval for {0}.
                Upon approval, you will be able to submit events for {0}. If you have any questions, please contact <a href="mailto:aicpcm@planning.org">aicpcm@planning.org</a>.
                """.format(self.content.begin_time.year))
            is_valid = False

        return is_valid

    def update_cart(self, **kwargs):

        self.purchase_quantity = self.total_cm_credits

        if not self.provider.registrations.filter(year=self.content.begin_time.year, status="A", registration_type="CM_PER_CREDIT").exists():
            # if provider does not already have per-credit registration for this year, then we add that to the cart too...
            # also, if we hadd the per-credit reg, then up to 1 credit is included
            registration_product = ProductCart.objects.get(
                code="CM_PROVIDER_REGISTRATION",
                publish_status="PUBLISHED"
            )
            registration_option = ProductOption.objects.get(
                code="CM_PER_CREDIT",
                publish_status="PUBLISHED"
            )

            self.purchase_quantity -= 1  # starting 2016, providers get 1 credit included with reg

            registration_price = registration_product.get_price(
                contact=self.request.contact,
                option=registration_option
            )

            registration_purchase = Purchase.objects.create(
                user=self.request.user,
                product=registration_product,
                product_price=registration_price,
                amount=registration_price.price,
                option=registration_option,
                submitted_product_price_amount=registration_price.price,
                contact_recipient=self.provider
            )
            ProviderRegistration.objects.create(
                provider=self.provider,
                is_unlimited=False,
                registration_type="CM_PER_CREDIT",
                year=self.content.begin_time.year,
                purchase=registration_purchase
            )

            # TODO: This is quite the hack to prevent a normal-priced item
            #  being added to the cart with a quantity of 0 (causes all sorts
            #  of problems down the line, like division-by-zero errors).
            #  The django_invoice_submit stored procedure calculates
            #  the unit price by dividing amount by quantity.
            #  https://americanplanning.atlassian.net/browse/DEV-5445
            #  Needs to be addressed in a major shopping cart refactor.
            #  In the meantime, we could create a $0 ProductPrice record
            #  and pass that in to update_cart().
            if self.purchase_quantity <= 0:
                self.purchase_quantity = 1
                super().update_cart(
                    quantity_hack=True,
                    provider=self.provider,
                    product_price=ProductPrice.objects.filter(
                        code="PRODUCT_CM_PER_CREDIT_COMPLIMENTARY",
                        publish_status="PUBLISHED",
                        status='A'
                    ).first(),
                    **kwargs
                )
                return

        super().update_cart(provider=self.provider, **kwargs)


#####################################
# # SINGLE EVENT SUBMISSION VIEWS # #
#####################################

class SingleEventSubmissionEditView(ProviderEventSubmissionEditFormView):

    title = "Single Event Live In Person"
    form_class = EventSingleForm

    def setup(self, request, *args, **kwargs):
        if (self.content and self.content.is_online) or kwargs.get("single_type", "single") == "online":
            self.title = "Single Event Live Online"
            self.form_class = EventSingleOnlineForm
        super().setup(request, *args, **kwargs)


class SingleEventSubmissionSpeakerFormsetView(ProviderEventSubmissionSpeakerFormsetView):
    pass


class SingleEventSubmissionReviewView(ProviderEventSubmissionReviewFormView):

    title = "Review - Single Event Live In Person"
    modelClass = EventSingle
    # can_have_speakers = True

    def setup(self, request, *args, **kwargs):
        if (self.content and self.content.is_online) or kwargs.get("single_type", "single") == "online":
            self.title = "Review - Single Event Live Online"
        super().setup(request, *args, **kwargs)


##################################
## MULTI EVENT SUBMISSION VIEWS ##
##################################

class MultiEventSubmissionEditView(ProviderEventSubmissionEditFormView):

    title = "Multipart Event"
    form_class = EventMultiForm
    # can_have_speakers = False
    success_url = "/cm/provider/events/{master_id}/activity/list/"

    def after_save(self, form):
        # disabling this as according to CM and Events team this is
        # an old business rule that is no longer in effect
        # https://americanplanning.atlassian.net/browse/DEV-5052
        # self.content.get_activities().update(status="N")
        super().after_save(form)


class MultiEventSubmissionReviewView(ProviderEventSubmissionReviewFormView):

    title = "Review - Multipart Event"
    preview_template = "events/newtheme/includes/eventmulti-details.html"
    modelClass = EventMulti
    # can_have_speakers = False

    def query_content(self, master_id):

        activities_prefetch = Prefetch(
            "master__children",
            queryset=Activity.objects.filter(parent__id=master_id, publish_status=self.default_publish_status).prefetch_related(
                Prefetch("contactrole", queryset=ContactRole.objects.filter(role_type="SPEAKER").select_related("contact"), to_attr="speaker_roles"),
            ).order_by("begin_time", "title"),
            to_attr="activities"
        )

        query = super().query_content(master_id).prefetch_related(activities_prefetch)
        return query

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class MultiEventSubmissionActivitiesView(AuthenticateProviderMixin, SubmissionMixin, TemplateView):

    template_name = "events/newtheme/submission/event-multi-activities.html"
    modelClass = EventMulti
    default_publish_status = "DRAFT"

    def post(self, request, *args, **kwargs):
        if request.POST.get("submitButton","") == "remove_activity":
            remove_activity_master_id = request.POST.get("activity_master_id","")
            event_submission_delete(request, remove_activity_master_id)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):

        # Should this be moved somewhere else
        self.activities = Activity.objects.filter(
            parent__id=self.content.master_id,
            publish_status=self.default_publish_status).order_by("begin_time", "end_time", "title")
        for activity in self.activities:
            activity.submission_form = EventActivityForm(instance=activity)
            activity.is_valid_for_submission = activity.submission_form.validate_unbound_form()
            if not activity.is_valid_for_submission:
                print(activity.submission_form.errors)

        context = super().get_context_data(**kwargs)
        context["event"] = self.content
        context["activities"] = self.activities
        return context


#################################
# # ACTIVITY SUBMISSION VIEWS # #
#################################

class ActivitySubmissionEditView(ProviderEventSubmissionEditFormView):

    title = "Activity"
    form_class = EventActivityForm
    # can_have_speakers = True

    def setup(self, request, *args, **kwargs):
        self.parent_master_id = self.content.parent_id if self.content else kwargs.get("parent_master_id")
        self.home_url = reverse("cm:multi_event_activities_view", kwargs={"master_id":self.parent_master_id})
        super().setup(request)

    def get_initial(self):
        initial = super().get_initial()
        initial["parent"] = self.parent_master_id

        parent_instance = Event.objects.filter(publish_status=self.default_publish_status, master_id=self.parent_master_id).first()
        initial["timezone"] = getattr(parent_instance, "timezone", None) or "US/Central"

        return initial


class ActivitySubmissionSpeakerFormsetView(ProviderEventSubmissionSpeakerFormsetView):

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.parent_master_id = self.content.parent_id
        self.home_url = self.success_url = reverse("cm:multi_event_activities_view", kwargs={"master_id":self.parent_master_id})


class ActivitySubmissionReviewView(ProviderEventSubmissionReviewFormView):
    title = "Review - Activity"
    modelClass = Activity
    # can_have_speakers = True

###############################
# # COURSE SUBMISSION VIEWS # #
###############################

class CourseSubmissionEditView(ProviderEventSubmissionEditFormView):
    title = "On Demand Course"
    form_class = EventCourseForm
    # can_have_speakers = True

class CourseSubmissionSpeakerFormsetView(ProviderEventSubmissionSpeakerFormsetView):
    pass

class CourseSubmissionReviewView(ProviderEventSubmissionReviewFormView):
    title = "Review - On Demand Course"
    # can_have_speakers = True
    modelClass = Course

###############################################
# # INFORMATION-ONLY EVENT SUBMISSION VIEWS # #
###############################################

class InfoEventSubmissionEditView(ProviderEventSubmissionEditFormView):
    template_name = "submissions/newtheme/forms/editinfo.html"
    title = "Information-only Event"
    form_class = EventInfoForm
    # can_have_speakers = False
    success_url = "/cm/provider/events/{master_id}/review/"

    # def setup(self, request, *args, **kwargs):
    #     if (self.content and self.content.is_online) or kwargs.get("single_type", "single") == "online":
    #         self.title = "Single Event Live Online"
    #         self.form_class = EventSingleOnlineForm
    #     super().setup(request, *args, **kwargs)


# class SingleEventSubmissionSpeakerFormsetView(ProviderEventSubmissionSpeakerFormsetView):
#     pass


class InfoEventSubmissionReviewView(ProviderEventSubmissionReviewFormView):

    title = "Review - Information-only Event"
    # all info events will use EventSingle model
    modelClass = EventInfo
    # can_have_speakers = False

    # def setup(self, request, *args, **kwargs):
    #     if (self.content and self.content.is_online) or kwargs.get("single_type", "single") == "online":
    #         self.title = "Review - Single Event Live Online"
    #     super().setup(request, *args, **kwargs)


####################################
# # OTHER HANDY SUBMISSION VIEWS # #
####################################

class SubmissionFormRouteUpdateView(View):
    """
    Determines the event type of the event to update, and routes to the appropriate view
    While different event types have different views, we need to route update requests to their matching view
    """
    default_publish_status = "DRAFT"

    def dispatch(self,request,*args,**kwargs):

        master_id = kwargs.get('master_id', None)
        event = Event.objects.filter(master__id=master_id, publish_status=self.default_publish_status).only("event_type").first()

        # Create submission from draft if it doesn't exist?
        if not event:
            try:
                published_event = Event.objects.get(master__id=master_id, publish_status="PUBLISHED")
                event = published_event.publish(publish_type=self.default_publish_status)
            except:pass

        if not event:
            raise Http404("Could not find submissison record for %s" % master_id)
        elif event.event_type == "EVENT_SINGLE":
            return SingleEventSubmissionEditView.as_view()(request, *args, **kwargs)
        elif event.event_type == "EVENT_MULTI":
            return MultiEventSubmissionEditView.as_view()(request, *args, **kwargs)
        elif event.event_type == "ACTIVITY":
            return ActivitySubmissionEditView.as_view()(request, *args, **kwargs)
        elif event.event_type == "COURSE":
            return CourseSubmissionEditView.as_view()(request, *args, **kwargs)
        elif event.event_type == "EVENT_INFO":
            return InfoEventSubmissionEditView.as_view()(request, *args, **kwargs)
        else:
            # invalid event type
            pass


class SubmissionFormRouteSpeakerView(View):
    """
    Determines the event type of the event to update, and routes to the appropriate view
    While different event types have different views, we need to route update requests to their matching view
    """
    default_publish_status = "DRAFT"

    def dispatch(self,request,*args,**kwargs):

        master_id = kwargs.get('master_id', None)
        event = Event.objects.filter(master__id=master_id, publish_status=self.default_publish_status).only("event_type").first()

        if not event:
            raise Http404("Could not find submissison record for %s" % master_id)
        elif event.event_type == "EVENT_SINGLE":
            return SingleEventSubmissionSpeakerFormsetView.as_view()(request, *args, **kwargs)
        elif event.event_type == "ACTIVITY":
            return ActivitySubmissionSpeakerFormsetView.as_view()(request, *args, **kwargs)
        elif event.event_type == "COURSE":
            return CourseSubmissionSpeakerFormsetView.as_view()(request, *args, **kwargs)
        else:
            # invalid event type
            pass


class SubmissionFormRouteDeleteView(AuthenticateProviderMixin, View):

    default_publish_status = "DRAFT"

    def set_content(self, *args, **kwargs):
        master_id = kwargs.pop("master_id", None)
        self.content = Event.objects.filter(master__id=master_id, publish_status=self.default_publish_status).first()

    def get(self, request, *args, **kwargs):
        if self.content:
            event_all = Event.objects.filter(master__id=self.content.master_id) # qs with records for all publish statuses for this event
            event_all.delete()
        return HttpResponseRedirect(reverse('myorg_events'))

    def post(self, request, *args, **kwargs):
        if self.content:
            event_all = Event.objects.filter(master__id=self.content.master_id) # qs with records for all publish statuses for this event
            event_all.delete()
            messages.success(self.request, "Successfully deleted {}".format(self.content.title))
        return HttpResponseRedirect(reverse('myorg_events'))


class SubmissionFormRouteReviewView(View):
    """
    Determines the event type of the event to update, and routes to the appropriate view
    Bc different event types have different views, we need to route update requests to their matching view

    NOTE: A little too similar to SubmissionFormRouteUpdateView (above)
    """
    default_publish_status = "DRAFT"

    def dispatch(self,request,*args,**kwargs):

        master_id = kwargs.get('master_id', None)
        event = Event.objects.filter(master__id=master_id, publish_status=self.default_publish_status).only("event_type").first()

        if event is None:
            raise Http404("Could not find submissison record for %s" % master_id)
        elif event.event_type == "EVENT_SINGLE":
            return SingleEventSubmissionReviewView.as_view()(request, *args, **kwargs)
        elif event.event_type == "EVENT_MULTI":
            return MultiEventSubmissionReviewView.as_view()(request, *args, **kwargs)
        elif event.event_type == "ACTIVITY":
            return ActivitySubmissionReviewView.as_view()(request, *args, **kwargs)
        elif event.event_type == "COURSE":
            return CourseSubmissionReviewView.as_view()(request, *args, **kwargs)
        elif event.event_type == "EVENT_INFO":
            return InfoEventSubmissionReviewView.as_view()(request, *args, **kwargs)
        else:
            # invalid event type
            pass


class SubmissionSpeakerRecordDisplay(View):
    """
    Returns a html to display a single contact
    """

    def get(self, request, *args, **kwargs):
        speaker_id = kwargs.get("speaker_id", None)
        speaker = Contact.objects.get(id=speaker_id)
        return render(request, "submissions/newtheme/includes/speaker-formset-display-record-button.html", {"speaker":speaker})
