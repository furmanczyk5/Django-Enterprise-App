from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.views.generic import TemplateView, View, FormView

from myapa.viewmixins import AuthenticateLoginMixin

from .models import Student
from .forms import StudentForm


class FreeStudentAdminDashboard(AuthenticateLoginMixin, TemplateView):
    title = "School Dashboard"
    template_name = "free_students/newtheme/admin/dashboard.html"
    school = None

    def get(self, request, *args, **kwargs):

        self.contact = self.request.user.contact
        first_fsma_relationship = self.contact.contactrelationship_as_target.all().filter(relationship_type='FSMA').first()
        if first_fsma_relationship:
            self.school = first_fsma_relationship.source

        self.students = Student.objects.filter(school=self.school).order_by("-status", "-contact__user__username", "last_name",)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contact"] = self.contact
        context["students"] = self.students
        context["title"] = self.title
        context["school"] = self.school
        return context


class FreeStudentEditFormView(AuthenticateLoginMixin, FormView):
    model = Student
    template_name = "free_students/newtheme/form/edit.html"
    school = None
    form_class = StudentForm
    home_url = success_url = "/free-students/admin-dashboard/"
    is_strict = True
    student_id = None

    def setup(self, request, *args, **kwargs):
        # implement strict validate only on submit and continue
        if request.POST.get("submitButton", "submit") == "submit":
            self.is_strict = True
        else:
            self.is_strict = False

        self.student_id = kwargs.get("student_id", None)

        self.contact = self.request.user.contact
        first_fsma_relationship = self.contact.contactrelationship_as_target.filter(relationship_type='FSMA').first()
        if first_fsma_relationship:
            self.school = first_fsma_relationship.source

    def dispatch(self, request, *args, **kwargs):
        self.setup(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        """
        Returns an instance of the form to be used in this view.
        """
        if not form_class:
            form_class = self.form_class
        try:
            if self.student_id:
                student = Student.objects.get(id=self.student_id)
                return form_class(instance=student, **self.get_form_kwargs())
        except Student.DoesNotExist:
            return form_class(**self.get_form_kwargs())

        return form_class(**self.get_form_kwargs())

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        form_kwargs["is_strict"] = self.is_strict

    #         ("A001", "Accredited Undergraduate Program"),
    # ("A002", "Accredited Graduate Program"),
    # ("N001", "Non-Accredited Undergraduate Program"),
    # ("N002", "Non-Planning Graduate FSTU Program"),
    # ("N003", "Non-Accredited Graduate Planning Program"),

        degree_types = []

        if self.school.accredited_school.accreditation.all().filter(accreditation_type__in=("A001","N001")).exists():
            degree_types.append(("U", "Undergraduate"))
        if self.school.accredited_school.accreditation.all().filter(accreditation_type__in=("A002","N002","N003")).exists():
            degree_types.append(("G", "Graduate"))

        form_kwargs["degree_types"] = degree_types

        return form_kwargs

    def get(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)

    def form_valid(self, form):

        student = form.save(commit=False)
        student.school = self.school

        if self.is_strict:
            # API call here to upload student
            is_duplicate = student.create_user()
            if is_duplicate:
                messages.success(self.request,"""APA is processing the enrollment information and checking for duplicate records for this individual in our member database. If a duplicate record is found, APA will notify you and the student by email.  The student’s enrollment status appears as “Duplicate Pending” on your dashboard.""")
            else:
                messages.success(self.request,"""You have successfully uploaded enrollment information to APA for student {0} {1}. A membership record has been created and assigned an APA ID and the student’s enrollment status has been changed to “Complete” on your dashboard.""".format(student.first_name, student.last_name))
        student.save()

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contact"] = self.contact
        context["title"] = "TEST"
        context["school"] = self.school
        context["home_url"] = self.home_url
        return context


class FreeStudentDeleteView (AuthenticateLoginMixin, View):

    def setup(self, request, *args, **kwargs):
        # implement strict validate only on submit and continue
        self.student_id = kwargs.get("student_id", None)

    def dispatch(self, request, *args, **kwargs):
        self.setup(request, *args, **kwargs)
        student_id = kwargs.get('student_id', None)
        student = Student.objects.filter(id=student_id, contact__isnull=True).first()
        first_name = student.first_name
        last_name = student.last_name
        student.delete()

        messages.success(request,"Student: {0} {1} has been deleted".format(first_name, last_name))
        return HttpResponseRedirect(reverse('free_students:student_dashboard'))


class FreeStudentDetailsView (AuthenticateLoginMixin, TemplateView):

    template_name = "free_students/newtheme/details.html"
    student = None
    home_url = "/free-students/admin-dashboard/"

    def setup(self, request, *args, **kwargs):
        # implement strict validate only on submit and continue
        student_id = kwargs.get("student_id", None)
        self.student = Student.objects.get(id=student_id)

    def dispatch(self, request, *args, **kwargs):
        self.setup(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["student"] = self.student
        context["home_url"] = self.home_url
        return context
