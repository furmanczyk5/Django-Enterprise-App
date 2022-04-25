import requests
import random
import string
import datetime

from django.contrib.auth.models import User
from django.db import connections, models
from django.db.models import Q
from django.forms.models import model_to_dict
from django.utils import timezone

from content.models import BaseContent, BaseAddress
from content.mail import Mail
from content.utils import get_api_root, get_api_key_querystring
from myapa.models.contact import Contact
from myapa.models.proxies import School


DEGREE_TYPES = (
    ("G", "Graduate"),
    ("U", "Undergraduate"),
    )

SCHOOL_ACCREDITATION_TYPES = (
    ("A001", "Accredited Undergraduate Program"),
    ("A002", "Accredited Graduate Program"),
    ("N001", "Non-Accredited Undergraduate Program"),
    ("N002", "Non-Planning Graduate FSTU Program"),
    ("N003", "Non-Accredited Graduate Planning Program"),
)

REGISTRATION_PERIODS = (
    ("SPRING", "Spring"),
    ("FALL", "Fall"),
    )

REGISTRATION_YEARS = (
    (2013, 2013),
    (2014, 2014),
    (2015, 2015),
    (2016, 2016),
    (2017, 2017),
    )

STUDENT_UPLOAD_STATUSES = (
    ("A", "Upload Complete"),
    ("P", "Pending"),
    ("DP", "Duplicate Pending"),
    ("DC", "Duplicate Confirmed"),
    )

def exec_schools_students(data: dict):
    data = {k: v or '' for (k, v) in data.items()}

    fields = [
        "first_name",
        "middle_name",
        "last_name",
        "expected_graduation_date",
        "degree_type",
        "school_id",
        "birth_date",
        "student_id",
        "address1",
        "address2",
        "city",
        "state",
        "zip_code",
        "country",
        "secondary_address1",
        "secondary_address2",
        "secondary_city",
        "secondary_state",
        "secondary_country",
        "email",
        "phone",
        "secondary_email",
        "registration_period",
        "registration_year"
    ]

    query = "EXEC [dbo].[API_iMIS_Schools_Students_POST] "
    parameters = []
    for field in fields:
        query += "@{}=%s, ".format(field)
        parameters.append(data.get(field, ''))
    query = query[:-2]
    with connections['MSSQL'].cursor() as cursor:
        cursor.execute(query, parameters)
        return cursor.fetchone()[0]


class Student(BaseContent, BaseAddress):

    contact = models.ForeignKey(Contact, related_name="student", blank=True, null=True, on_delete=models.SET_NULL)
    school = models.ForeignKey("myapa.School", related_name="students", blank=True, null=True, on_delete=models.SET_NULL)

    first_name = models.CharField(max_length=20, blank=True, null=True)
    middle_name = models.CharField(max_length=20, blank=True, null=True) # check this in student form
    last_name = models.CharField(max_length=30, blank=True, null=True)
    expected_graduation_date = models.DateField(blank=True, null=True)
    degree_type = models.CharField(max_length=50, choices=DEGREE_TYPES, default="U")
    student_id = models.CharField(max_length=20, blank=True, null=True) # check this on student form
    birth_date = models.DateField(blank = True, null=True)

    email = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    secondary_address1 = models.CharField(max_length=40, blank=True, null=True)
    secondary_address2 = models.CharField(max_length=40, blank=True, null=True)
    secondary_city = models.CharField(max_length=40, blank=True, null=True)
    secondary_state = models.CharField(max_length=15, blank=True, null=True)
    secondary_zip_code = models.CharField(max_length=10, blank=True, null=True)
    secondary_country = models.CharField(max_length=20, blank=True, null=True)
    # should this be renamed to cell??
    # WORK , HOME, and CELL are in iMIS. where should these populate
    secondary_phone = models.CharField(max_length=20, blank=True, null=True)
    secondary_email = models.CharField(max_length=100, blank=True, null=True)

    registration_period = models.CharField(max_length=10, choices=REGISTRATION_PERIODS, blank=True, null=True)
    registration_year = models.IntegerField(choices=REGISTRATION_YEARS, blank=True, null=True)

    duplicate_contact = models.ForeignKey(
        Contact,
        related_name="duplicate_student",
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )
    upload_status = models.CharField(max_length=5, choices=STUDENT_UPLOAD_STATUSES, blank=True, null=True, default="P")

    uploaded_on = models.DateField(null=True, blank=True)

    def create_user(self):
        """
        creates iMIS user. returns iMIS ID
        """
        data = model_to_dict(self)
        school_id = self.school.user.username

        random_generated_password = self.generate_password()

        api_root = get_api_root()
        path = "/school/{0}/students/create".format(school_id)
        url = api_root + path + get_api_key_querystring()

        r = requests.post(url, data)
        print("RETURN POST DATA: " + str(r.json()))
        user_id = r.json()['data'][0].get('WebUserID')

        Contact.update_or_create_from_imis(username=user_id)

        user = User.objects.get(username=user_id)
        user.set_password(random_generated_password)
        user.save()

        self.uploaded_on = datetime.date.today()
        self.registration_year = timezone.now().year

        if datetime.datetime.now().month < 6:
            self.registration_period = "SPRING"
        else:
            self.registration_period = "FALL"

        self.contact = user.contact


        # add send email function here
        self.password = random_generated_password



        # END USER / CONTACT CREATION
        ###############################################################

        # BEGIN DUPLICATE CHECKS

        duplicate_dict = None
        is_duplicate, duplicate_dict = self.duplicate_check()

        if is_duplicate:
            self.upload_status = "DP"
            self.duplicate_pending_confirmation_email(duplicate_dict)
        else:
            self.upload_status = "A"
            self.confirmation_email()

        self.save()

        return is_duplicate

    def duplicate_check(self):
        """
        checks for duplicate users based on point system
        first and last name = 1 point
        primary or additional address = 8 points
        work or home phone number = 8 points
        primary or secondary email addresses = 9 points
        """
        is_duplicate = False
        duplicate_points = 0

        secondary_address_check = None
        secondary_phone_check = None
        secondary_email_check = None

        duplicate_dict = {}

        name_check = Contact.objects.filter(first_name__iexact=self.first_name, last_name__iexact=self.last_name).exclude(id=self.contact.id)
        primary_address_check = Contact.objects.filter(address1__iexact=self.address1, address2__iexact=self.address2, city__iexact=self.city, state__iexact=self.state, zip_code__iexact=self.zip_code, country__iexact=self.country).exclude(id=self.contact.id)

        if self.secondary_address1:
            secondary_address_check = Contact.objects.filter(address1__iexact=self.secondary_address1, address2__iexact=self.secondary_address2, city__iexact=self.secondary_city, state__iexact=self.secondary_state, zip_code__iexact=self.secondary_zip_code, country__iexact=self.secondary_country).exclude(id=self.contact.id)

        phone_check = Contact.objects.filter(Q(phone__iexact=self.phone) | Q(cell_phone__iexact=self.phone)).exclude(id=self.contact.id)

        if self.secondary_phone:
            secondary_phone_check = Contact.objects.filter(Q(phone__iexact=self.secondary_phone) | Q(cell_phone__iexact=self.secondary_phone)).exclude(id=self.contact.id)

        email_check = Contact.objects.filter(Q(email__iexact=self.email)).exclude(id=self.contact.id)

        if self.secondary_email:
            secondary_email_check = Contact.objects.filter(email__iexact=self.secondary_email).exclude(id=self.contact.id)

        name_check_ids = []
        primary_address_check_ids = []
        secondary_address_check_ids = []
        phone_check_ids = []
        secondary_phone_check_ids = []
        email_check_ids = []
        secondary_email_check_ids = []

        if name_check:
            duplicate_points += 1
            for x in name_check:
                if x.user:
                    name_check_ids.append(x.user.username)

        if primary_address_check:
            duplicate_points += 8
            for x in primary_address_check:
                if x.user:
                    primary_address_check_ids.append(x.user.username)

        if secondary_address_check:
            duplicate_points += 8
            for x in secondary_address_check:
                if x.user:
                    secondary_address_check_ids.append(x.user.username)

        if phone_check:
            duplicate_points += 8
            for x in phone_check:
                if x.user:
                    phone_check_ids.append(x.user.username)

        if secondary_phone_check:
            duplicate_points += 8
            for x in secondary_phone_check:
                if x.user:
                    secondary_phone_check_ids.append(x.user.username)

        if email_check:
            duplicate_points += 9
            for x in email_check:
                if x.user:
                    email_check_ids.append(x.user.username)

        if secondary_email_check:
            duplicate_points += 9
            for x in secondary_email_check:
                if x.user:
                    secondary_email_check_ids.append(x.user.username)

        if duplicate_points >= 9:
            is_duplicate = True

        duplicate_dict["name"] = name_check_ids
        duplicate_dict["primary_address"] = primary_address_check_ids
        duplicate_dict["secondary_address"] = secondary_address_check_ids
        duplicate_dict["phone"] = phone_check_ids
        duplicate_dict["secondary_phone"] = secondary_phone_check_ids
        duplicate_dict["email"] = email_check_ids
        duplicate_dict["secondary_email"] = secondary_email_check_ids
        duplicate_dict["points"] = duplicate_points
        return is_duplicate, duplicate_dict

    def confirmation_email(self):
        # for users that have passed the duplicate check
        mail_context = {"student": self, "password": self.password}
        Mail.send(mail_code="FREE_STUDENT_CONFIRMATION_STUDENT", mail_to=self.contact.email, mail_context=mail_context)

    def duplicate_pending_confirmation_email(self, duplicate_dict):
        # for users who have failed the duplicate check
        duplicate_dict["password"] = self.password
        duplicate_dict["student"] = self
        duplicate_dict["student_birth_date"] = self.birth_date.strftime('%m/%d/%y')
        Mail.send(mail_code="FREE_STUDENT_DUPLICATE_PENDING_STUDENT", mail_to=self.email, mail_context=duplicate_dict)

        school_admin_email = self.school.contactrelationship_as_source.all().filter(relationship_type='FSMA').first().target.user.email
        if school_admin_email and school_admin_email != "":
            Mail.send(mail_code="FREE_STUDENT_DUPLICATE_PENDING_ADMIN", mail_context=duplicate_dict, mail_to=school_admin_email)
        Mail.send(mail_code="FREE_STUDENT_DUPLICATE_PENDING_STAFF", mail_context=duplicate_dict)

    def duplicate_confirmed_confirmation_email(self):
        # staff have confirmed these users are duplicates
        mail_context = {"student": self}
        Mail.send(mail_code="FREE_STUDENT_DUPLICATE_CONFIRMED_STUDENT", mail_to=self.contact.email, mail_context=mail_context)
        # add a confirmation email here for school admins ?
        school_admin_email = self.school.contactrelationship_as_source.all().filter(relationship_type='FSMA').first().target.user.email
        if school_admin_email and school_admin_email != "":
            Mail.send(mail_code="FREE_STUDENT_DUPLICATE_CONFIRMED_ADMIN", mail_to=school_admin_email, mail_context=mail_context)

    def generate_password(self):
        # generates a random 7 character password
        # move this somewhere more generic?
        return ''.join(random.choice(string.ascii_letters) for x in range(7))

    def __str__(self):
        return str(self.first_name) + " " + str(self.last_name) + " | " + str(self.school)


class AccreditedSchool(models.Model):

    school = models.OneToOneField(
        School,
        related_name="accredited_school",
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )
    accreditation = models.ManyToManyField("Accreditation", related_name="accredited_school", blank=True)

    def __str__(self):
        return str(self.school)


class Accreditation(models.Model):
    accreditation_type = models.CharField(max_length=20, choices=SCHOOL_ACCREDITATION_TYPES, blank=True, null=True)

    def __str__(self):
        return self.get_accreditation_type_display()

    class Meta:
        verbose_name = "Accreditation type"
        verbose_name_plural = "Accreditation types"
