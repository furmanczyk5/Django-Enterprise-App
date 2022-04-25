from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect
from django.views.generic import FormView

from cm.models import Log, Claim, ProviderApplication, ProviderRegistration
from comments.models import Comment
from exam.models import ExamApplication, ExamRegistration, ApplicationDegree, ApplicationJobHistory
from free_students.models import Student
from myapa.forms import CreateDjangoUserForm, MergeCheckForm
from myapa.models.contact import Contact
from myapa.models import ContactRole, ContactContentAdded, ContactRelationship, ContactTagType
from myapa.models.educational_degree import EducationalDegree
from myapa.models.job_history import JobHistory
from myapa.models.profile import IndividualProfile, OrganizationProfile
from myapa.permission_groups import PermissionGroups
from myapa.permissions import utils
from myapa.viewmixins import AuthenticateWebUserGroupMixin
from registrations.models import Attendee
from store.models import LineItem, Order, Payment, Purchase
from submissions.models import Review, ReviewRole
from support.models import Ticket


class CreateDjangoUserView(AuthenticateWebUserGroupMixin, FormView):

    template_name = 'myapa/newtheme/admin/create-contact.html'
    authenticate_groups = ["staff", "onsite-conference-admin"]
    form_class = CreateDjangoUserForm
    success_url = '/admin/'

    def form_valid(self, form):

        username = self.request.POST.get('username')
        contact = Contact.update_or_create_from_imis(username)

        utils.update_user_groups(contact.user)

        messages.success(self.request, 'User and Contact record have been created/updated.')
        
        return redirect(self.get_success_url())

    def get(self, request, *args, **kwargs):
        """
        Pass parameters for this method for updating contact information from an iMIS Staff Site link
        """

        form = self.get_form()

        username = request.GET.get("UserID", "")

        if username != "":
            contact = Contact.update_or_create_from_imis(username)

            utils.update_user_groups(contact.user)

            messages.success(self.request, "User and Contact record have been created/updated.")

            return redirect(self.get_success_url())

        return self.render_to_response(self.get_context_data(form=form))

# admin superuser tool to update django groups from json file
# not so elegant... maybe update this automatically somehow??
@user_passes_test(lambda u: u.is_superuser)
def admin_update_groups(request, **kwargs):
    PermissionGroups.update()
    return redirect('/admin/')


class MergeCheckView(AuthenticateWebUserGroupMixin, FormView):
    """
    After submitting an iMIS ID, the user is shown a list of Django
    records associated with that ID.
    """
    template_name = 'myapa/newtheme/admin/merge-check.html'
    authenticate_groups = ["staff"]
    form_class = MergeCheckForm
    user_id = None

    def form_valid(self, form):
        self.user_id = self.request.POST.get('username')
        messages.success(self.request, 'See below for list of Django records associated with the iMIS ID you entered.')

        return redirect(self.get_success_url())

    def get(self, request, *args, **kwargs):
            """
            Update the page with current results
            """
            form = self.get_form()
            self.user_id = request.GET.get("user_id", "")

            return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, *args, **kwargs):

        context = super().get_context_data(**kwargs)
        context["username"] = self.user_id
        if self.user_id:
            try:
                contact = Contact.objects.get(user__username=self.user_id)
            except Exception as e:
                print("No contact record found: ", e)
                raise Http404("No Django contact record found")
        else:
            contact = None

        if contact:
            comments = Comment.objects.filter(contact=contact, is_deleted=False).select_related("contact__user")
            logs = Log.objects.filter(contact=contact).select_related("contact__user")
            claims = Claim.objects.filter(contact=contact, is_deleted=False).select_related("contact__user")
            provider_applications = ProviderApplication.objects.filter(provider=contact).select_related("provider__user")
            provider_registrations = ProviderRegistration.objects.filter(provider=contact).select_related("provider__user")
            exam_applications = ExamApplication.objects.filter(contact=contact).select_related("contact__user")
            exam_registrations = ExamRegistration.objects.filter(contact=contact).select_related("contact__user")
            exam_jobs = ApplicationJobHistory.objects.filter(contact=contact).select_related("contact__user")
            exam_degrees = ApplicationDegree.objects.filter(contact=contact).select_related("contact__user")
            students = Student.objects.filter(contact=contact).select_related("contact__user")
            contact_content_added = ContactContentAdded.objects.filter(contact=contact).select_related("contact__user")
            contact_relationships = ContactRelationship.objects.filter(Q(source=contact) | Q(target=contact)).select_related("source__user", "target__user")
            contact_roles = ContactRole.objects.filter(contact=contact).select_related("contact__user")
            contact_tag_types = ContactTagType.objects.filter(contact=contact).select_related("contact__user")
            myapa_degrees = EducationalDegree.objects.filter(contact=contact).select_related("contact__user")
            myapa_jobs = JobHistory.objects.filter(contact=contact).select_related("contact__user")
            individual_profiles = IndividualProfile.objects.filter(contact=contact).select_related("contact__user")
            organization_profiles = OrganizationProfile.objects.filter(contact=contact).select_related("contact__user")
            attendees = Attendee.objects.filter(contact=contact).select_related("contact__user")
            orders = Order.objects.filter(user=contact.user).select_related("user")
            payments = Payment.objects.filter(contact=contact).select_related("contact__user")
            purchases = Purchase.objects.filter(contact=contact).select_related("contact__user")
            review_roles = ReviewRole.objects.filter(contact=contact).select_related("contact__user")
            reviews = Review.objects.filter(contact=contact).select_related("contact__user")
            tickets = Ticket.objects.filter(contact=contact).select_related("contact__user")
            context["merge_data"] = [
                self.make_results_tuple(comments),
                 self.make_results_tuple(logs),
                  self.make_results_tuple(claims),
                   self.make_results_tuple(provider_applications),
                    self.make_results_tuple(provider_registrations),
                     self.make_results_tuple(exam_applications),
                      self.make_results_tuple(exam_registrations),
                       self.make_results_tuple(exam_jobs),
                        self.make_results_tuple(exam_degrees),
                         self.make_results_tuple(students),
                          self.make_results_tuple(contact_content_added),
                           self.make_results_tuple(contact_relationships),
                             self.make_results_tuple(contact_roles),
                              self.make_results_tuple(contact_tag_types),
                               self.make_results_tuple(myapa_degrees),
                                self.make_results_tuple(myapa_jobs),
                                 self.make_results_tuple(individual_profiles),
                                  self.make_results_tuple(organization_profiles),
                                   self.make_results_tuple(attendees),
                                    self.make_results_tuple(orders),
                                     self.make_results_tuple(payments),
                                      self.make_results_tuple(purchases),
                                       self.make_results_tuple(review_roles),
                                        self.make_results_tuple(reviews),
                                         self.make_results_tuple(tickets),
            ]
        else:
            context["merge_data"] = []
        return context

    def get_success_url(self):
        """
        Returns the supplied success URL.
        """
        self.success_url = reverse_lazy("merge_check") + "?user_id={0}".format(self.user_id)
        return super().get_success_url()

    def make_results_tuple(self, queryset):
        return (queryset.model.__name__, list(queryset))

