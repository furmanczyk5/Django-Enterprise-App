import random
import string

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, TemplateView

from content.mail import Mail
from imis.enums.members import ImisNameAddressPurposes
from imis.models import CustomSchoolaccredited, Name, Advocacy, RaceOrigin, MailingDemographics
from myapa.forms import FreeStudentAdminAccountForm, FreeStudentAdminSchoolInformationForm, \
    FreeStudentAdminDemographicsForm, FreeStudentAdminEnhanceMembershipForm
from myapa.models.constants import DEGREE_LEVELS, DEGREE_TYPE_CHOICES
from myapa.models.contact import Contact
from myapa.models.contact_relationship import ContactRelationship
from myapa.models.educational_degree import EducationalDegree
from myapa.permissions import utils as permissions_utils
from myapa.utils import get_primary_chapter_code_from_zip_code
from myapa.viewmixins import AuthenticateLoginMixin
from store.models import Purchase
from .account import CreateAccountFormViewMixin
from .join import MembershipCartViewMixin


class AuthenticateSchoolAdminMixin(AuthenticateLoginMixin):
    authenticate_admin = True  # True if user must be an admin to continue
    authenticate_school = True  # True if user must be an admin for specified school to continue

    ACCESS_DENIED_MESSAGE = """
    Your ID is not currently linked to a school administrator profile. Please contact <a href="mailto:studentmembership@planning.org" class="button">studentmembership@planning.org</a> and we will help get you signed up.
    """

    def authenticate(self, request, *args, **kwargs):

        response = super().authenticate(request, *args, **kwargs)
        if response:
            return response

        school_id = self.get_school_id(request, *args, **kwargs)

        admin_relationship_query = ContactRelationship.objects.select_related(
            "source__user"
        ).filter(
            relationship_type='FSMA',
            target=request.user.contact
        )

        if self.authenticate_school:
            admin_relationship_query = admin_relationship_query.filter(
                source__user__username=school_id
            )

        admin_relationship = admin_relationship_query.first()
        self.school = admin_relationship.source if admin_relationship else None

        if not self.school and (not self.authenticate_school or not self.authenticate_admin):
            context = dict(access_denied_message=self.ACCESS_DENIED_MESSAGE)
            return render(request, "myapa/newtheme/member-access-only.html", context=context)

    def get_school_id(self, request, *args, **kwargs):
        return kwargs.get("school_id", None)


class FreeStudentAdminRouteSchool(AuthenticateSchoolAdminMixin, View):
    authenticate_school = False

    def get(self, request, *args, **kwargs):
        school_id = self.school.user.username
        return redirect("freestudents_school_admin_dashboard", school_id=school_id)


class FreeStudentAdminDashboard(AuthenticateSchoolAdminMixin, TemplateView):
    title = "School Dashboard"
    template_name = "myapa/newtheme/freestudents/admin/dashboard.html"

    def get(self, request, *args, **kwargs):
        self.accredited_programs = CustomSchoolaccredited.get_all_degree_programs(
            self.school.user.username
        )

        pending_students_queryset = EducationalDegree.objects.filter(
            school=self.school,
            contact__member_type="PSTU",
            is_current=True
        )

        current_students_queryset = EducationalDegree.objects.filter(
            school=self.school,
            contact__member_type="STU",
            is_current=True
        )

        self.pending_students = self.get_student_info(pending_students_queryset)
        self.current_students = self.get_student_info(current_students_queryset)

        return super().get(request, *args, **kwargs)

    def get_student_info(self, queryset):
        students_data = queryset.select_related(
            "contact__user"
        ).distinct(
            "contact"
        ).values(
            "contact__user__username",
            "contact__first_name",
            "contact__last_name",
            "contact__member_type",
            "seqn",
            "program",
            "level",
            "level_other",
            "graduation_date"
        )

        students = []
        for s in students_data:
            degree_level = s.get("level")

            student = dict()
            student["user_id"] = s.get("contact__user__username")
            student["member_type"] = s.get("contact__member_type")
            student["first_name"] = s.get("contact__first_name")
            student["last_name"] = s.get("contact__last_name")
            student["program"] = s.get("program")
            student["degree_level"] = next(
                (dt[1] for dt in DEGREE_LEVELS if dt[0] == degree_level), None
            ) if degree_level != "N" else s.get("level_other")
            student["graduation_date"] = s.get("graduation_date")

            students.append(student)

        return students

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["school"] = self.school
        context["pending_students"] = self.pending_students
        context["current_students"] = self.current_students
        context["accredited_programs"] = self.accredited_programs
        return context


class FreeStudentAdminEditStudentFormView(AuthenticateSchoolAdminMixin, MembershipCartViewMixin,
                                          CreateAccountFormViewMixin, TemplateView):
    """
    TODO: This duplicates a lot of code in
    :class:`myapa.views.account.PersonalInformationView`
    """
    template_name = "myapa/newtheme/freestudents/admin/studentmember-edit.html"

    account_form_class = FreeStudentAdminAccountForm
    degree_form_class = FreeStudentAdminSchoolInformationForm
    demographics_form_class = FreeStudentAdminDemographicsForm
    divisions_form_class = FreeStudentAdminEnhanceMembershipForm

    membership_product_code = "MEMBERSHIP_STU"

    def setup(self):

        self.is_strict = self.request.POST.get('submit_button', '') != 'save'
        self.student = self.get_student()

        self.account_form = self.account_form_class(
            **self.get_account_form_kwargs()
        )

        self.degree_form = self.degree_form_class(
            **self.get_degree_form_kwargs()
        )

        self.demographics_form = self.demographics_form_class(
            **self.get_demographics_form_kwargs()
        )

        self.divisions_form = self.divisions_form_class(
            **self.get_divisions_form_kwargs()
        )

    def get(self, request, *args, **kwargs):
        self.setup()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.setup()

        if self.forms_are_valid():
            self.save_account_form(self.account_form)
            self.save_degree_form(self.degree_form)
            self.save_demographics_form(self.demographics_form)
            self.save_divisions_form(self.divisions_form)

            if self.is_strict:

                # process zero dollar order for student user
                membership_purchases = self.get_membership_purchases(user=self.student.user)
                self.order = self.process_membership(
                    purchases=membership_purchases,
                    user=self.student.user,
                    send_order_confirmation=False
                )

                # set temporary password for user
                self.temporary_password = ''.join(
                    random.choice(string.ascii_letters) for _ in range(7)
                )
                self.student.user.set_password(self.temporary_password)
                self.student.user.save()

                potential_duplicates = self.get_potential_duplicates(
                    self.account_form,
                    contact=self.student
                )
                if potential_duplicates:
                    self.send_duplicate_notification_emails(potential_duplicates)
                self.send_confirmation_emails()

            return redirect(
                "freestudents_school_admin_dashboard",
                school_id=self.school.user.username
            )
        else:
            return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        context["school"] = self.school

        context["account_form"] = self.account_form
        context["degree_form"] = self.degree_form
        context["demographics_form"] = self.demographics_form
        context["divisions_form"] = self.divisions_form

        # for displaying errors
        context["forms"] = [
            self.account_form,
            self.degree_form,
            self.demographics_form,
            self.divisions_form
        ]
        context["forms_have_errors"] = self.account_form.errors \
                                       or self.degree_form.errors \
                                       or self.demographics_form.errors \
                                       or self.divisions_form.errors

        context["display_errors"] = getattr(self, "display_errors", None)

        return context

    def forms_are_valid(self):
        account_form_valid = self.account_form.is_valid()
        degree_form_valid = self.degree_form.is_valid()
        demographics_form_valid = self.demographics_form.is_valid()
        divisions_form_valid = self.divisions_form.is_valid()
        return account_form_valid and degree_form_valid and demographics_form_valid and divisions_form_valid

    def get_student(self):
        username = self.kwargs.get("student_id", None)
        if username:
            can_edit_contact = EducationalDegree.objects.filter(
                contact__member_type="PSTU",
                contact__user__username=username,
                school=self.school
            ).exists()
            if not can_edit_contact:
                raise Http404("Cannot find editable pending free student record.")
            return get_object_or_404(Contact, member_type="PSTU", user__username=username)
        else:
            return None

    def get_form_kwargs(self):
        kwargs = {
            'is_strict': self.is_strict
        }
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES
            })

        return kwargs


    def get_account_form_kwargs(self):
        form_kwargs = self.get_form_kwargs()
        initial = dict()

        if self.student:
            self.addresses = self.student.get_imis_name_address()

            mailing_preferences = None
            billing_preferences = None

            primary_address = home_address = self.addresses.filter(purpose='Home Address')

            if primary_address.count() == 1:
                primary_address = primary_address.first()
            elif primary_address.count() > 1:
                raise Http404("Error: More than one home address.")
            else:
                primary_address = None

            secondary_address = work_address = self.addresses.filter(purpose='Work Address')

            if secondary_address.count() == 1:
                secondary_address = secondary_address.first()
            elif secondary_address.count() > 1:
                raise Http404("Error: More than one work address.")
            else:
                secondary_address = None

            if primary_address.preferred_mail:
                mailing_preferences = ImisNameAddressPurposes.HOME_ADDRESS.value
            elif secondary_address and secondary_address.preferred_mail:
                mailing_preferences = ImisNameAddressPurposes.WORK_ADDRESS.value

            if primary_address.preferred_bill:
                billing_preferences = ImisNameAddressPurposes.HOME_ADDRESS.value
            elif secondary_address and secondary_address.preferred_bill:
                billing_preferences = ImisNameAddressPurposes.WORK_ADDRESS.value

            initial.update({
                "informal_name": self.student.informal_name,

                "mailing_preferences": mailing_preferences,
                "billing_preferences": billing_preferences,

                "user_address_num": getattr(primary_address, "address_num", None),
                "address1": getattr(primary_address, "address_1", ""),
                "address2": getattr(primary_address, "address_2", ""),
                "city": getattr(primary_address, "city", ""),
                "state": getattr(primary_address, "state_province", ""),
                "zip_code": getattr(primary_address, "zip", ""),
                "country": getattr(primary_address, "country", ""),
                "company": getattr(primary_address, "company", ""),

                "additional_user_address_num": getattr(secondary_address, "address_num", None),
                "additional_address1": getattr(secondary_address, "address_1", ""),
                "additional_address2": getattr(secondary_address, "address_2", ""),
                "additional_city": getattr(secondary_address, "city", ""),
                "additional_state": getattr(secondary_address, "state_province", ""),
                "additional_zip_code": getattr(secondary_address, "zip", ""),
                "additional_country": getattr(secondary_address, "country", ""),
                "additional_company": getattr(secondary_address, "company", ""),
            })

        form_kwargs["instance"] = self.student
        form_kwargs["initial"] = initial

        return form_kwargs

    def get_degree_form_kwargs(self):
        form_kwargs = self.get_form_kwargs()
        initial = dict(
            school=self.school.user.username,
            other_school=None
        )

        self.degree = None

        if self.student:

            self.degree = EducationalDegree.objects.filter(
                contact=self.student,
                school=self.school,
                is_current=True
            ).first()

            if self.degree:

                if self.degree.school_seqn:
                    initial_degree_program = self.degree.school_seqn
                    initial_degree_type_choice = None
                    initial_degree_type_other = None
                elif self.degree.program in [dt[0] for dt in DEGREE_TYPE_CHOICES]:
                    initial_degree_program = "OTHER"
                    initial_degree_type_choice = self.degree.program
                    initial_degree_type_other = None
                else:
                    initial_degree_program = "OTHER"
                    initial_degree_type_choice = "OTHER"
                    initial_degree_type_other = self.degree.program

                initial.update({
                    "degree_program": initial_degree_program,
                    "degree_type_choice": initial_degree_type_choice,
                    "degree_type_other": initial_degree_type_other,
                    "level": self.degree.level,
                    "level_other": self.degree.level_other,
                    "graduation_date": self.degree.graduation_date,
                    "student_id": self.degree.student_id
                })

        form_kwargs["instance"] = self.degree
        form_kwargs["initial"] = initial

        return form_kwargs

    def get_demographics_form_kwargs(self):
        form_kwargs = self.get_form_kwargs()
        initial = dict()

        self.demographics = dict()

        if self.student:
            self.demographics = self.student.get_imis_demographics_legacy()

            initial.update({
                "race": (self.demographics.get("race", "") or "").split(","),
                "hispanic_origin": self.demographics.get("origin", ""),
                "gender": self.demographics.get("gender", None),
                "gender_other": self.demographics.get("gender_other", None),
                "ai_an": self.demographics.get("ai_an", None),
                "asian_pacific": self.demographics.get("asian_pacific", None),
                "other": self.demographics.get("other", None),
                "span_hisp_latino": self.demographics.get("span_hisp_latino", None),
            })

            initial["planners_advocacy"] = Advocacy.objects.filter(
                id=self.student.user.username,
                grassrootsmember=True
            ).exists()

        form_kwargs["initial"] = initial

        return form_kwargs

    def get_divisions_form_kwargs(self):
        form_kwargs = self.get_form_kwargs()
        initial = dict()

        if self.student:
            form_kwargs["contact"] = self.student
            form_kwargs["subscriptions"] = []
            form_kwargs["cart_products"] = [
                p.product for p in Purchase.cart_items(user=self.student.user)
            ]

            initial["planners_advocacy"] = Advocacy.objects.filter(
                id=self.student.user.username,
                grassrootsmember=True
            ).exists()

        form_kwargs["initial"] = initial

        return form_kwargs

    def save_account_form(self, form):
        if self.student:
            # existing user
            self.student = form.save(commit=False)
            self.student.member_type = "PSTU"
            self.student.salary_range = "KK" if self.student.is_international else "K"
            self.student.save()

            user_data = {
                "prefix": form.cleaned_data.get("prefix_name", ""),
                "first_name": form.cleaned_data.get("first_name", ""),
                "middle_name": form.cleaned_data.get("middle_name", ""),
                "last_name": form.cleaned_data.get("last_name", ""),
                "suffix": form.cleaned_data.get("suffix_name", ""),
                "informal": form.cleaned_data.get("informal_name", ""),
                "email": form.cleaned_data.get("email", ""),
                "email_secondary": form.cleaned_data.get("secondary_email", ""),
                "home_phone": form.cleaned_data.get("phone", ""),
                "work_phone": form.cleaned_data.get("secondary_phone", ""),
                "mobile_phone": form.cleaned_data.get("cell_phone", ""),
                "birth_date": form.cleaned_data.get("birth_date", "")
            }
            email_secondary = user_data.pop('email_secondary')
            ind_demo = self.student.get_imis_ind_demographics()
            if ind_demo is not None:
                ind_demo.email_secondary = email_secondary
                ind_demo.salary_range = self.student.salary_range
                ind_demo.save()
            name = self.student.get_imis_name()
            name.__dict__.update(user_data)
            name.last_updated = self.student.getdate()
            name.updated_by = 'WEBUSER'
            name.save()
            self.student.insert_name_log_record(
                data=self.student.make_name_log_data(
                    self.student.NAME_LOG_CHANGE_RECORD
                )
            )
        else:
            # new user
            form.cleaned_data['member_type'] = 'STU'
            imis_user = self.post_new_user_to_imis(form)

            user = User.objects.create(
                username=imis_user.id,
                first_name=form.cleaned_data.get("first_name", ""),
                last_name=form.cleaned_data.get("last_name", ""),
                email=form.cleaned_data.get("email", "")
            )

            self.student = form.save(commit=False)
            self.student.user = user
            self.student.member_type = "PSTU"
            self.student.salary_range = "KK" if self.student.is_international else "K"
            self.student.save()

        self.post_address_data_to_imis(form, contact=self.student)
        self.student = permissions_utils.update_user_groups(self.student.user)
        self.add_membership_to_cart(user=self.student.user)
        if not self.student.is_international:
            us_chapter = get_primary_chapter_code_from_zip_code(self.student.zip_code)
            if us_chapter:
                self.add_primary_chapter_to_cart(us_chapter, user=self.student.user)

    def save_degree_form(self, form):
        degree = form.save(commit=False)
        degree.contact = self.student  # student should always exist at this point
        imis_degree = degree.write_to_imis()
        degree.seqn = imis_degree.seqn
        degree.save()

    def save_demographics_form(self, form):
        self.demographics.update({
            "ethnicity_noanswer": bool("NO_ANSWER" in form.cleaned_data.get("race", [])),
            "race_noanswer": bool("NO_ANSWER" in form.cleaned_data.get("race", [])),
            "origin_noanswer": bool(form.cleaned_data.get("hispanic_origin", "") == "O000"),
            "ethnicity": ",".join(form.cleaned_data.get("race", [])),
            "origin": form.cleaned_data.get("hispanic_origin"),
            "gender": form.cleaned_data.get("gender", ""),
            "gender_other": form.cleaned_data.get("gender_other", ""),

            "ai_an": form.cleaned_data.get("ai_an", ""),
            "asian_pacific": form.cleaned_data.get("asian_pacific", ""),
            "ethnicity_other": form.cleaned_data.get("other", ""),
            "span_hisp_latino": form.cleaned_data.get("span_hisp_latino", ""),

            # Not submitted by form
            "exclude_planning_print": True,  # Students don't get printed planning
            "functional_title": "F999",  # "Student / Other / Not Applicable"
            "salary_range": self.student.salary_range,  # should be "K" or "KK" for international

            "join_source": "SCHOOL_ADMIN"  # This is how we distinguish joining online and through school admin portal
        })

        self.update_functional_title()
        self.update_ind_demographics()
        self.update_race_origin()
        MailingDemographics.objects.update_or_create(
            id=self.student.user.username,
            defaults=dict(
                excl_planning_print=self.demographics['exclude_planning_print']
            )
        )

    def update_ind_demographics(self):
        ind_demo = self.student.get_imis_ind_demographics()
        ind_demo.salary_range = self.demographics['salary_range']
        ind_demo.salary_verifydate = self.student.getdate()
        ind_demo.functional_title_verifydate = self.student.getdate()
        ind_demo.gender = self.demographics['gender']
        if ind_demo.gender == 'S':
            ind_demo.gender_other = self.demographics['gender_other']
        ind_demo.join_source = self.demographics['join_source']
        ind_demo.save()

    def update_functional_title(self):
        name = self.student.get_imis_name()
        name.functional_title = self.demographics["functional_title"]
        name.save()

    def update_race_origin(self):
        # Can't do `get_or_create` on just the id - the table (like many in iMIS) allows
        # empty strings but not nulls...
        race_origin = RaceOrigin.objects.filter(
            id=self.student.user.username
        ).first()

        if race_origin is None:
            race_origin = RaceOrigin(id=self.student.user.username)

        race_origin.span_hisp_latino = self.demographics['span_hisp_latino']
        race_origin.race = self.demographics['ethnicity']
        race_origin.ai_an = self.demographics['ai_an']
        race_origin.asian_pacific = self.demographics['asian_pacific']
        race_origin.other = self.demographics['ethnicity_other']
        race_origin.ethnicity_noanswer = self.demographics['ethnicity_noanswer']
        race_origin.origin_noanswer = self.demographics['origin_noanswer']
        race_origin.ethnicity_verifydate = self.student.getdate()
        race_origin.origin_verifydate = self.student.getdate()
        race_origin.save()

    def save_divisions_form(self, form):
        form.save(user=self.student.user)  # divisions are added to cart here

        Advocacy.objects.update_or_create(
            id=self.student.user.username,
            defaults=dict(
                grassrootsmember=form.cleaned_data.get("planners_advocacy", False)
            )
        )

    def get_membership_purchases(self, user=None):
        return super().get_membership_purchases(
            user=user
        ).filter(
            product_price__price=0
        )

    def send_duplicate_notification_emails(self, potential_duplicates):
        # for users who have failed the duplicate check

        # Later make this a method on Contact model when Ran is finished refactoring

        account_data = self.account_form.cleaned_data
        primary_address = "{0}, {1}, {2}, {3} {4}, {5}".format(
            account_data.get("address1", ""),
            account_data.get("address2", ""),
            account_data.get("city", ""),
            account_data.get("state", ""),
            account_data.get("zip_code", ""),
            account_data.get("country", ""))

        if self.account_form.cleaned_data.get("additional_address1"):
            secondary_address = "{0}, {1}, {2}, {3} {4}, {5}".format(
                account_data.get("additional_address1", ""),
                account_data.get("additional_address2", ""),
                account_data.get("additional_city", ""),
                account_data.get("additional_state", ""),
                account_data.get("additional_country", ""),
                account_data.get("additional_zip_code", ""))
        else:
            secondary_address = ""

        mail_context = dict(
            student=self.student,
            school=self.school,
            password=self.temporary_password,
            student_primary_address=primary_address,
            student_secondary_address=secondary_address,
            student_birth_date=self.student.birth_date.strftime('%m/%d/%y'),
            potential_duplicates=potential_duplicates
        )
        school_admin_email = self.request.user.contact.email
        if school_admin_email and school_admin_email != "":
            Mail.send(
                mail_code="FREE_STUDENT_DUPLICATE_PENDING_ADMIN",
                mail_context=mail_context,
                mail_to=school_admin_email
            )
        Mail.send(mail_code="FREE_STUDENT_DUPLICATE_PENDING_STAFF", mail_context=mail_context)

    def send_confirmation_emails(self):
        # for users that have passed the duplicate check
        purchases = Purchase.objects.select_related(
            "product__content"
        ).filter(
            order_id=self.order.id
        )

        mail_context = dict(
            student=self.student,
            school=self.school,
            divisions=[p.product.content for p in purchases if p.product.product_type == "DIVISION"],
            primary_chapter=next((p.product.content for p in purchases if p.product.product_type == "CHAPTER"), dict()),
            password=self.temporary_password,
        )
        Mail.send(
            mail_code="FREE_STUDENT_CONFIRMATION_STUDENT",
            mail_to=self.student.email,
            mail_context=mail_context
        )


class FreeStudentAdminDeleteStudentFormView(AuthenticateSchoolAdminMixin, View):
    success_url = "freestudents_school_admin_dashboard"
    allowed_methods = ["post", "delete"]  # html forms only support post method

    def get_success_url(self):
        return reverse(self.success_url, kwargs=dict(school_id=self.school.user.username))

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):

        student_id = kwargs.get("student_id", None)

        is_unsubmitted_student = EducationalDegree.objects.filter(
            contact__member_type="PSTU",
            contact__user__username=student_id,
            school=self.school
        ).exists()

        if is_unsubmitted_student:
            Name.objects.filter(id=student_id).update(status="D")

            # should cascade delete all associated records (contact and degree)
            User.objects.filter(username=student_id).delete()

            messages.success(request, "Successfully deleted pending student")
        else:
            raise Http404("Pending student record does not exist")

        return redirect(self.get_success_url())
