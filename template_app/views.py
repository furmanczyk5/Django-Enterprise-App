from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render
from django.views.generic import TemplateView, View, FormView
from django.http import HttpResponseRedirect

from myapa.viewmixins import AuthenticateStaffMixin

from .forms import NameForm, MyAccountForm, PrototypeStudentsAddDivisionsAndSubscriptionsForm, \
    PrototypeJoinStudentInformationForm, PrototypeJoinStudentAccountForm

# Create your views here.
class Publications(TemplateView):
    context={}
    template_name="newtheme/sandbox/frontend/publications.html"


class ConferencesAndMeetings(TemplateView):
    context={}
    template_name="newtheme/sandbox/frontend/conferences-and-meetings.html"

class DirectoryPage(TemplateView):
    context={}
    template_name="newtheme/sandbox/frontend/directory-page.html"

class PatternLibrary1(TemplateView):
    context={}
    template_name="newtheme/sandbox/pattern-library/pattern-library-1.html"

class PatternLibrary2(TemplateView):
    context={}
    template_name="newtheme/sandbox/pattern-library/pattern-library-2.html"

class PatternLibrary3(TemplateView):
    context={}
    template_name="newtheme/sandbox/pattern-library/pattern-library-3.html"

class PatternLibrary4(TemplateView):
    context={}
    template_name="newtheme/sandbox/pattern-library/pattern-library-4.html"

class PatternLibrary5(TemplateView):
    context={}
    template_name="newtheme/sandbox/pattern-library/pattern-library-5.html"

class PatternLibraryLinkedImages(TemplateView):
    context={}
    template_name="newtheme/sandbox/pattern-library/pattern-library-linked-images.html"

class LegacyContent1(TemplateView):
    context={}
    template_name="newtheme/sandbox/legacy-content/legacy-content-1.html"


class LegacyContent2(TemplateView):
    context={}
    template_name="newtheme/sandbox/legacy-content/legacy-content-2.html"


class LegacyContent3(TemplateView):
    context={}
    template_name="newtheme/sandbox/legacy-content/legacy-content-3.html"


class LegacyContent4(TemplateView):
    context={}
    template_name="newtheme/sandbox/legacy-content/legacy-content-4.html"


class NewContent(TemplateView):
    context={}
    template_name="newtheme/sandbox/frontend/new-content.html"

class InterimContent(TemplateView):
    context={}
    template_name="newtheme/sandbox/frontend/interim-content.html"

class Cart(TemplateView):
    context={}
    template_name="newtheme/sandbox/frontend/cart.html"

class OrderConfirmation(TemplateView):
    context={}
    template_name="newtheme/sandbox/frontend/order-confirmation.html"

class Search(TemplateView):
    context={}
    template_name="newtheme/sandbox/frontend/search.html"

class Home(TemplateView):
    context={}
    template_name="newtheme/sandbox/frontend/home.html"

class PlanningMagazineIssue(TemplateView):
    context={}
    template_name="newtheme/sandbox/frontend/planning-magazine-issue.html"

class FormTestView(FormView):
    form_class = NameForm
    template_name = "newtheme/sandbox/forms/name.html"

class AccountFormView(FormView):
    form_class = MyAccountForm
    template_name = "newtheme/sandbox/forms/account.html"

# Conference pattern libraries
class ConferencePatternLibrary1(TemplateView):
    context={}
    template_name="newtheme/sandbox/pattern-library-conference/pattern-library-1.html"

class ConferencePatternLibrary2(TemplateView):
    context={}
    template_name="newtheme/sandbox/pattern-library-conference/pattern-library-2.html"

class ConferencePatternLibrary3(TemplateView):
    context={}
    template_name="newtheme/sandbox/pattern-library-conference/pattern-library-3.html"

class ConferencePatternLibrary4(TemplateView):
    context={}
    template_name="newtheme/sandbox/pattern-library-conference/pattern-library-4.html"

class ConferencePatternLibrary5(TemplateView):
    context={}
    template_name="newtheme/sandbox/pattern-library-conference/pattern-library-5.html"

class ConferencePatternLibrary6(TemplateView):
    context={}
    template_name="newtheme/sandbox/pattern-library-conference/pattern-library-6.html"

class ConferencePatternLibrarySessionDetail(TemplateView):
    context={}
    template_name="newtheme/sandbox/pattern-library-conference/pattern-library-session-detail.html"

class ConferencePatternLibrarySponsorship(TemplateView):
    context={}
    template_name="newtheme/sandbox/pattern-library-conference/pattern-library-sponsorship.html"

# Conference Pages
class ConferenceHome(TemplateView):
    context={}
    template_name="newtheme/sandbox/frontend-conference/home.html"

class ConferenceTracks(TemplateView):
    context={}
    template_name="newtheme/sandbox/frontend-conference/tracks.html"

class ConferenceContent(TemplateView):
    context={}
    template_name="newtheme/sandbox/frontend-conference/content.html"

# Planning Magazine Pages
class PlanningMagazineLandingPage(TemplateView):
    context={}
    template_name="newtheme/sandbox/planning-magazine/landing-page.html"

class PlanningMagazineTypeLandingPage(TemplateView):
    context={}
    template_name="newtheme/sandbox/planning-magazine/type-landing-page.html"

class PlanningMagazineArticlePage(TemplateView):
    context={}
    template_name="newtheme/sandbox/planning-magazine/article-page.html"

def get_name(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = NameForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = NameForm()

    return render(request, 'name.html', {'form': form})


class PrototypeTemplateView(AuthenticateStaffMixin, TemplateView):

    template_name_root = "newtheme/prototype/"

    def get_template_names(self):
        return [self.template_name_root + self.kwargs.get("template_name")]


class PrototypeJoinStudentAccountInformationView(AuthenticateStaffMixin, FormView):
    """
    View for Adding divisions and subscriptions of Join process
    """

    form_class = PrototypeJoinStudentAccountForm
    template_name = "newtheme/prototype/2017-join-renew/student/account-information.html"
    success_url = reverse_lazy("template_app:prototype_join_student_information")

    def form_valid(self, form):
        if self.request.POST.get("submit", "") == "duplicate_continue":
            return super().form_valid(form)
        else:
            self.prompt_duplicate = True
            return self.form_invalid(form)

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        form_kwargs["request"] =self.request
        return form_kwargs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["prompt_duplicate"] = getattr(self, "prompt_duplicate", False)
        return context


class PrototypeJoinStudentInformationView(AuthenticateStaffMixin, FormView):
    """
    View for Adding divisions and subscriptions of Join process
    """

    form_class = PrototypeJoinStudentInformationForm
    template_name = "newtheme/prototype/2017-join-renew/student/student-information.html"
    success_url = reverse_lazy("template_app:PrototypeJoinAddDivisionsAndSubscriptionsView")


class PrototypeJoinAddDivisionsAndSubscriptionsView(AuthenticateStaffMixin, FormView):
    """
    View for Adding divisions and subscriptions of Join process
    """

    form_class = PrototypeStudentsAddDivisionsAndSubscriptionsForm
    template_name = "newtheme/prototype/2017-join-renew/student/enhance-membership.html"
    success_url = reverse_lazy("template_app:PrototypeJoinStudentAccountInformationView")
