from django.contrib import admin

from .models import AccreditedSchool, Accreditation, Student
from .forms import StudentAdminForm


class SchoolInline(admin.TabularInline):
    model = AccreditedSchool
    fields = ["accreditation", "school"]
    readonly_fields = ["school"]
    extra = 1
    raw_id_fields=["school"]
    filter_horizontal = ["accreditation",]
    title = "Accreditations"
    max_num = 1


class AccreditationAdmin(admin.ModelAdmin):
    model = Accreditation
    list_display = ["accreditation_type"]


class StudentAdmin(admin.ModelAdmin):
    model = Student
    form = StudentAdminForm
    search_fields = ["=school__user__username","school__company","first_name","last_name","email","phone","=contact__user__username"]
    list_display = ["last_name","first_name","email","phone","registration_period","registration_year","upload_status","school"]
    list_display_links = ["first_name", "last_name"]
    raw_id_fields = ["contact","school","duplicate_contact",]
    fields = [("school","upload_status",),("contact","duplicate_contact",), ("registration_period", "registration_year","degree_type",),("first_name","middle_name","last_name"),("student_id","expected_graduation_date","birth_date",),("address1","address2","city",),("state","zip_code","country"),("email","phone"),("secondary_address1","secondary_address2","secondary_city"),("secondary_state","secondary_zip_code","secondary_country"),("secondary_email","secondary_phone")]
    list_filter = ["registration_year", "registration_period","school", "upload_status"]
    autocomplete_lookup_fields = {'fk': ['contact','school','duplicate_contact'] }

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.contact:
            return ["first_name", "middle_name","last_name","expected_graduation_date","address1","address2","city","state","zip_code","country","email","phone","secondary_phone","secondary_email","degree_type","registration_period","registration_year","student_id","secondary_address1","secondary_address2","secondary_city","secondary_state","secondary_zip_code","secondary_country"]
        return self.readonly_fields

    def save_model(self, request, student, form, change):

        # need a better way to get this old value:
        if student.id:
            old_upload_status = Student.objects.get(id=student.id).upload_status

            if old_upload_status == "DP" and student.upload_status == "DC" and student.duplicate_contact is not None:
                student.duplicate_confirmed_confirmation_email()

            elif old_upload_status == "DP" and student.upload_status == "A" and student.duplicate_contact is None:
                student.password = student.generate_password()
                student_user = student.contact.user
                student_user.set_password(student.password)
                student_user.save()

                student.confirmation_email()
        return super().save_model(request, student, form, change)

    class Media:
        js = (
            "//ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js",
            "/static/ui/forms/js/selectchain.js",
        )

admin.site.register(Accreditation, AccreditationAdmin)
admin.site.register(Student, StudentAdmin)
