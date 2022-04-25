import random
import datetime

from django.db import models
from django.db.models import Q

from imis.models import CustomSchoolaccredited
from cm.models import Log, Period
from content.models import Content, BaseContent, Publishable
from myapa.models.proxies import IndividualContact, School
from myapa.models.educational_degree import BaseEducationalDegree
from myapa.models.job_history import BaseJobHistory
from submissions.models import Category, Review, ReviewRole, REVIEW_ROUNDS
from uploads.models import DocumentUpload
from store.models import Purchase, Order

EXAM_FORM_CODES = {
    # "CPE": (6022031711, 6022031712,),
    "CPE": (6022031911, 6022031912,),
    "CEP": (6022041101,),
    "CTP": (6022051401,),
    "CUD": (6022061401,),
    # "AICP_CAND":(6022091801, 6022091802) # CPE exam form codes for Candidates (same exam)
    "AICP_CAND":("6022031911-C", "6022031912-C")
}

ADA_REQUIREMENTS = (
    ("", "I do not require special test center arrangements"),
    ("TIME AND A HALF", "Yes - require an additional 2 hours"),
    ("ADDITIONAL 30 MINUTES", "Yes - require additional 30 minutes"),
    ("DOUBLE TIME", "Yes - require an additional 4 hours"),
    ("READER REQUIRED", "Yes - require reader"),
    ("SEPARATE ROOM", "Yes - require separate room"),
    )

APPLICATION_TYPES = (
    # these types apply for the REG (comprehensive) exam windows, and the regular (EXAM_APPLICATION_AICP) category:
    ("REG","Regular Applicant"), # $70
    ("MCIP","Canadian Institute of Planners (MCIP)"), # $70? (but old bd had $425) ??
    ("NJ","NJ: applying for AICP only, already passed exam"), # $70
    ("SCHOLAR","SCHOLAR: (archived no longer used) "), #70 # needed as an application type? Assume NO... let's check with Eric/Jen
    ("NJ_REG","NJ: applying for AICP and will register for the exam"), # $70
    ("NJ_NOAICP", "NJ: Not Applying for AICP – Exam Only"),
    ("CAND_ENR","AICP Candidate Program Enrollment"), # $20
    ("CAND_CERT","AICP Candidate AICP Certification"), # $375
    ("CAND_RESUB","AICP Candidate AICP Certification Resubmission"), # $0
    )
REGULAR_APPLICATION_TYPES = ["REG","MCIP","NJ","SCHOLAR","NJ_REG","NJ_NOAICP"]
ADVANCED_APPLICATION_TYPES = ("CEP", "CTP", "CUD") # just a way to code which ones are advanced (the others are regular)
SKIP_APP_TYPES = ("MCIP", "NJ_NOAICP")
CAND_APP_TYPES = ("CAND_ENR", "CAND_CERT", "CAND_RESUB")

REGISTRATION_TYPES = (
    ("MCIP_A","MCIP_A: Canadian Institute of Planners (MCIP)"),
    ("NJ_NOAICP","NJ_NOAICP: NJ: registering for exam, not applying for AICP"),
    ("NJ_REG_A","NJ_REG_A: registering and applied for AICP"), #setup as application
    ("REG_A","REG_A: Regular Applicant - Pre Approved"), # setup as application
    ("REG_T_0","REG_T_0: Transfer from previous-no fee"), #setup as application
    ("REG_T_100","REG_T_100: Transfer from previous-150$ fee"), #setup as application
    ("SCHOLAR_A","SCHOLAR_A: Scholarship Recipient"), # setup as application
    ("PDO","PDO: Professional Development Officer registration"),
    ("CAND_ENR_A", "AICP Candidate - $100"),
    ("CAND_T_0", "AICP Candidate Free Transfer - $0"),
    ("CAND_T_100", "AICP Candidate Transfer - $100"),
    )
PRE_APPROVED_REG_TYPE_LIST = ['REG_A', 'REG_T_0', 'REG_T_100', 'SCHOLAR_A', 'MCIP_A']
CANDIDATE_REGISTRATION_TYPES = ("CAND_ENR_A", "CAND_T_0", "CAND_T_100")

APPLICATION_STATUSES = (
    ("A", "Approved"),
    ("A_C", "Candidate Approved"),
    ("EN", "Enrolled"), # student accepted as AICP Candidate Program Participant, but not yet approved to take exam.
    # ("PE", "Pending Enrollment"), # awaiting initial student status verification to become Candidate Program Participant
    ("D", "Denied"),
    ("D_C", "Candidate Denied"),
    ("E", "Expired or Deleted"),
    ("EB_D", "Early Bird Denied"),
    ("EB_D_C", "Candidate Early Bird Denied"),
    ("EB_P", "Early Bird Pending and under review"),
    ("I", "Incomplete"),
    ("N", "Not yet submitted"),
    ("P", "Pending and under review"),
    ("R", "Under review"),
    ("V_C", "Verification Complete"),
    ("V_I", "Verification Incomplete"),
    ("V_R", "Verification Review")
)
DENIED_STATUSES_LIST = ['EB_D', 'D', 'I', 'D_C', 'EB_D_C']
APPROVAL_PROCESS_STATUSES = ['P', 'EB_P', 'R', 'V_C', 'V_I', 'V_R']
ENROLLED_STATUSES = ['EN', 'P', 'A', 'A_C']
APPROVED_STATUSES = ['A', 'A_C']

# phd: always 4
# other degree always 4
PLANNING_EXPERIENCE_DICT = {
    'masters_pab_planning_degree': 2,
    'bachelor_pab_planning_degree': 3,
    'masters_planning_degree': 3,
    'phd_degree': 4,
    'any_degree': 4,
    'no_degree': 8
    }
HIGHEST_REQUIRED_EXPERIENCE = 8

SUBMISSION_PUBLISH_STATUSES = ['SUBMISSION', 'EARLY_RESUBMISSION']

APP_TYPE_TO_EMAIL_CODE = {
    "MCIP": "EXAM_APPLICATION_MCIP",
    "NJ_NOAICP": "EXAM_APPLICATION_NJ_NOAICP",
}



def make_regular_application_types_list():
    tuple_list = []
    for toop in APPLICATION_TYPES:
        if toop[0] not in ADVANCED_APPLICATION_TYPES and toop[0] not in CAND_APP_TYPES:
            tuple_list.append(toop)
    tuple_list.remove(("SCHOLAR","SCHOLAR: (archived no longer used) "))
    return tuple_list

def make_advanced_application_types_list():
    tuple_list = []
    for toop in APPLICATION_TYPES:
        if toop[0] in ADVANCED_APPLICATION_TYPES:
            tuple_list.append(toop)
    return tuple_list

# Maybe not needed:
def get_application_category_codes():
    codes = []
    for exam_category in ApplicationCategory.objects.filter(code__isnull=False):
        codes.append(exam_category.code)
    return codes


# class ExamPeriodManager(models.Manager):
#     def get_queryset(self):
#         return super().get_queryset().filter(content_type="EXAM")
#         return super().get_queryset()

# class ExamPeriod(Period):
#     objects = ExamPeriodManager()

# do we need this now? assume yes since foreign key exists for application
class Exam(BaseContent):
    """
    Model to store exam windows. Records are created for exam periods, twice a year for the regular (comprehensive) exam... e.g. 2016NOV and 2016MAY,
    and once a year for the advanced exams... e.g. 2016ASC.
    """

    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)

    registration_start_time = models.DateTimeField(blank=True, null=True)
    registration_end_time = models.DateTimeField(blank=True, null=True)

    application_start_time = models.DateTimeField(blank=True, null=True)
    application_end_time = models.DateTimeField(blank=True, null=True)

    application_early_end_time = models.DateTimeField(blank=True, null=True)

    previous_exams = models.ManyToManyField("Exam", blank=True)
    is_advanced = models.BooleanField(default=False)
    product = models.ForeignKey("store.Product", blank=True, null=True, on_delete=models.SET_NULL)

    def generate_prometric_exam_code(self, exam_id):
        """
        returns a random exam form code
        """

        return random.choice(EXAM_FORM_CODES[exam_id])

class ApplicationCategoryManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(content_type="EXAM")

class ApplicationCategory(Category):
    objects = ApplicationCategoryManager()
    class Meta:
        proxy = True
        verbose_name_plural = "Exam Categories"

    def save(self, *args, **kwargs):
        self.content_type = "EXAM"
        return super(ApplicationCategory, self).save(*args, **kwargs)


class ExamApplication(Content):
    # TO DO... where to store GEE sent date??
    # TO DO... shere to store demographic info historical information?
    # contact field? or use contact roles?
    contact = models.ForeignKey(IndividualContact, related_name="exam_applications", on_delete=models.PROTECT)
    exam = models.ForeignKey(Exam, on_delete=models.PROTECT)
    application_type = models.CharField(max_length=10, choices=APPLICATION_TYPES)
    legacy_id = models.IntegerField(null=True, blank=True) # temp for application import
    application_status = models.CharField(max_length=10, choices=APPLICATION_STATUSES)
    code_of_ethics = models.BooleanField(default=False)
    current_review_round = models.IntegerField(choices=REVIEW_ROUNDS, null=True, blank=True)

    publish_reference_fields = [
        {"name":"permission_groups",
            "publish":False,
            "multi":True
        },
        {"name":"taxo_topics",
            "publish":False,
            "multi":True
        },
        {"name":"contacts",
            "publish":True,
            "multi":True,
            "through_name":"contactrole",
            "replace_field":"content"
        },
        {"name":"tag_types",
            "publish":True,
            "multi":True,
            "through_name":"contenttagtype",
            "replace_field":"content"
        },
        {"name":"related",
            "publish":True,
            "multi":True,
            "through_name":"contentrelationship_from",
            "replace_field":"content"
        },
        {"name":"places",
            "publish":True,
            "multi":True,
            "through_name":"contentplace",
            "replace_field":"content"
        },
        {"name":"product",
            "publish":True,
            "multi":False,
            "replace_field":"content"
        },
        {"name":"applicationdegree_set",
            "publish":True,
            "multi":True,
            "replace_field":"application"
        },
        {"name":"applicationjobhistory_set",
            "publish":True,
            "multi":True,
            "replace_field":"application"
        },
        {"name":"submission_answer",
            "publish":True,
            "multi":True,
            "replace_field":"content"
        },
    ]

    def deadline(self):
        try:
            contact=self.contact
            cand_period = Period.objects.get(code="CAND")
            cand_log = Log.objects.filter(contact=contact, period=cand_period, status='A', is_current = True)

            if cand_log and cand_log.count() == 1:
                return cand_log.first().end_time
            else:
                return None
        except:
            return None

    def previous_denial_application(self, *args, **kwargs):
        """
        Returns the most recent denial from a previous exam for this application, or None (if no previous denial).
        """
        allowed_application_exams = list(self.exam.previous_exams.all()) + [self.exam]
        return ExamApplication.objects.filter(contact=self.contact, application_status__in=DENIED_STATUSES_LIST,
            exam__in=allowed_application_exams).filter(Q(publish_status='EARLY_RESUBMISSION') | Q(publish_status='SUBMISSION')
            ).order_by('created_time').last()


    def save(self, *args, **kwargs):
        self.content_type = "EXAM"
        return_val = super(ExamApplication, self).save(*args, **kwargs)
        current_submission_qs = None

        current_submission_qs = ExamApplication.objects.filter(
            master__id=self.master.id,
            publish_status='EARLY_RESUBMISSION',
            publish_uuid=self.publish_uuid
            )

        if not current_submission_qs:
            current_submission_qs = ExamApplication.objects.filter(
                master__id=self.master.id,
                publish_status='SUBMISSION',
                publish_uuid=self.publish_uuid
                )

        if current_submission_qs and self.publish_status == "DRAFT":
            try:
                draft = ExamApplication.objects.get(master__id=self.master.id, publish_status="DRAFT")

                current_submission_qs.update(contact=self.contact, exam=self.exam, submission_category=self.submission_category,
                                application_type=self.application_type, application_status=self.application_status, status=self.status,
                                )
            except:
                raise Exception("Attempting to update submission record from draft when there are multiple draft records on same master.")
        # if self.publish_status == "DRAFT":
        #     other_versions_qs = ExamApplication.objects.filter(master__id=self.master.id).exclude(publish_status="DRAFT")
        #     other_versions_qs.update(contact=self.contact, exam=self.exam, submission_category=self.submission_category,
        #                 application_type=self.application_type, application_status=self.application_status, status=self.status,
        #                 submission_time=self.submission_time, submission_approved_time=self.submission_approved_time)
        return return_val

    # def publish(self, replace=(None,None), publish_type="PUBLISHED", database_alias="default", versions=None):
    #     return super(Content, self).publish(publish_type=publish_type)
    def __str__(self):
        return str(str(self.contact) + ' | ' + str(self.exam.code) + ' | ' + str(self.application_status))


class ExamRegistration(models.Model):

    # might need a exam key here since not all registrations relate to the same year that the exam took plac
    contact = models.ForeignKey(IndividualContact, related_name="exam_registrations", on_delete=models.PROTECT)
    registration_type = models.CharField(max_length=20, choices=REGISTRATION_TYPES)
    ada_requirement = models.CharField(max_length=50, choices=ADA_REQUIREMENTS, blank=True)
    verified = models.BooleanField(default=False) #?? is this needed?
    code_of_ethics = models.BooleanField(default=False)
    release_information = models.BooleanField(default=False)
    certificate_name = models.CharField(max_length=100)
    gee_eligibility_id = models.CharField(max_length=50, null=True, blank=True)
    application = models.ForeignKey(ExamApplication, null=True, blank=True, on_delete=models.SET_NULL)
    legacy_id = models.IntegerField(null=True, blank=True) # temp for registration import
    exam = models.ForeignKey(Exam, on_delete=models.PROTECT)
    purchase = models.ForeignKey(Purchase, null=True, blank=True, on_delete=models.SET_NULL)
    is_pass = models.NullBooleanField(null=True, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    def get_form_code_id(self):
        """
        same as get_exam_id but accounts for AICP Candidates and only intented for
        retrieving form codes (unlike get_exam_id which is for sending the exam type
        to Prometric)
        """
        exam_id = None
        reg_type = self.registration_type

        if reg_type.find("CAND") < 0:
            if self.purchase:
                if self.purchase.product.code == "EXAM_REGISTRATION_CTP":
                    exam_id = "CTP"
                elif self.purchase.product.code == "EXAM_REGISTRATION_CEP":
                    exam_id = "CEP"
                elif self.purchase.product.code == "EXAM_REGISTRATION_CUD":
                    exam_id = "CUD"

                else:
                    exam_id = "CPE"
            else:
                exam_id = "CPE"
        else:
            exam_id = "AICP_CAND"
        return exam_id

    def get_exam_id(self):
        """
        returns exam id used in prometric calls ... should this be somewhere else?
        NOTE: only works if there is a purchase associated with the registration. defaults to AICP
        """
        exam_id = None

        if self.purchase:
            if self.purchase.product.code == "EXAM_REGISTRATION_CTP":
                exam_id = "CTP"
            elif self.purchase.product.code == "EXAM_REGISTRATION_CEP":
                exam_id = "CEP"
            elif self.purchase.product.code == "EXAM_REGISTRATION_CUD":
                exam_id = "CUD"
            else:
                cand_exam_reg_record = ExamRegistration.objects.filter(
                    purchase=self.purchase,
                    registration_type__contains="CAND").first()
                if cand_exam_reg_record:
                    exam_id = "AICP-C"
                else:
                    exam_id = "CPE"
        else:
            if bool(self.registration_type) and self.registration_type.find("CAND") > -1:
                exam_id = "AICP-C"
            else:
                exam_id = "CPE"

        return exam_id

    def __str__(self):
        return str(str(self.contact) + ' | ' + str(self.exam.code))


class VerificationDocument(DocumentUpload):
    """
    Stores documents uploaded for job history or education verification purposes
    """
    # TO DO: add manager here to filter out exam verification documents
    class Meta:
        proxy=True

class ApplicationJobHistory(Publishable, BaseJobHistory):
    application = models.ForeignKey(ExamApplication, on_delete=models.CASCADE)
    verification_document = models.ForeignKey(VerificationDocument, null=True, on_delete=models.SET_NULL) #WARNING: this will create issues with publishing unless we make VerificationDocument NOT published
    is_planning = models.BooleanField(default=False)
    contact_employer = models.BooleanField(default=False)
    supervisor_name = models.CharField(max_length=30, null=True, blank=True)
    legacy_id = models.IntegerField(null=True, blank=True) # TO DO: remove?

    def get_planning_experience(self):
        # Because is_planning is being removed from the job form, make it always True here
        # If at some point this needs to be changed back to a user input remove this line:
        self.is_planning = True

        if self.start_date and self.end_date and (self.end_date - self.start_date) < datetime.timedelta(0):
            return datetime.timedelta(0)
        elif self.is_planning == True and self.end_date and self.start_date:
            return (self.end_date - self.start_date) * (.5 if self.is_part_time else 1)
        elif self.is_planning == True and self.is_current == True and self.start_date:
            # start_datetime = datetime.datetime.combine(self.start_date, datetime.datetime.min.time())
            try:
                if self.application.submission_time:
                    return (self.application.submission_time.date() - self.start_date) * (.5 if self.is_part_time else 1)
                else:
                    return (datetime.date.today() - self.start_date) * (.5 if self.is_part_time else 1)
            except:
                return (datetime.date.today() - self.start_date) * (.5 if self.is_part_time else 1)
        else:
            return datetime.timedelta(0)

    def __str__(self):
        return str(str(self.contact) + ' | ' + str(self.company) + ' | ' + str(self.title))


    publish_reference_fields = [
        {"name":"verification_document",
            "publish":True,
            "multi":False,
            "replace_field":"applicationjobhistory_set"
        },
    ]

    def after_publish_reference(self, published_instance, published_reference, publish_name):
        if publish_name == "verification_document":
            published_instance.verification_document = published_reference


class ApplicationDegree(Publishable, BaseEducationalDegree):

    school = models.ForeignKey(School, null=True, blank=True, related_name="application_degree", on_delete=models.SET_NULL)
    application = models.ForeignKey(ExamApplication, on_delete=models.CASCADE)
    verification_document = models.ForeignKey(VerificationDocument, null=True, on_delete=models.SET_NULL) #WARNING: this will create issues with publishing unless we make VerificationDocument NOT published
    pab_accredited = models.BooleanField(default=False)
    legacy_id = models.IntegerField(null=True, blank=True)
    year_in_program = models.IntegerField(null=True, blank=True) # e.g. "3" indicates 3rd-year bachelor

    def get_experience_requirement(self):

        masters_pab_planning_degree = False
        bachelor_pab_planning_degree = False
        masters_planning_degree = False
        # phd_degree = False
        any_degree = False
        no_degree = False

        required_planning_experience = None
        is_masters = False
        level = "B"
        is_planning = False
        is_pab = False

        # we can assume that whatever degree a candidate has is PAB, because
        # it has been verified during enrollment, so we may not need this here:
        csa = CustomSchoolaccredited.objects.filter(seqn=self.school_seqn).first()

        if csa:
            level = csa.degree_level or self.level
            is_planning = True
            is_pab = csa.school_program_type in ['PAB','ACSP'] or self.pab_accredited
        else:
            level = self.level
            is_planning = self.is_planning
            is_pab = self.pab_accredited

        # Code to get highest degree credential:
        if level == "M":
            is_masters = True

        if is_masters and is_planning and is_pab:
            masters_pab_planning_degree = True
        elif level == "B" and is_planning and is_pab:
            bachelor_pab_planning_degree = True
        elif is_masters and is_planning:
            masters_planning_degree = True
        elif level in ["B", "M", "P", "O"]:
            any_degree = True
        else:
            no_degree = True

        if masters_pab_planning_degree:
            required_planning_experience = PLANNING_EXPERIENCE_DICT['masters_pab_planning_degree']
        elif bachelor_pab_planning_degree:
            required_planning_experience = PLANNING_EXPERIENCE_DICT['bachelor_pab_planning_degree']
        elif masters_planning_degree:
            required_planning_experience = PLANNING_EXPERIENCE_DICT['masters_planning_degree']
        elif any_degree:
            required_planning_experience = PLANNING_EXPERIENCE_DICT['any_degree']
        elif no_degree:
            required_planning_experience = PLANNING_EXPERIENCE_DICT['no_degree']
        else:
            print("An error occured in get_experience_requirement")

        return required_planning_experience


    def __str__(self):
        return str(str(self.contact) + ' | ' + str(self.other_school))


    publish_reference_fields = [
        {"name":"verification_document",
            "publish":True,
            "multi":False,
            "replace_field":"applicationdegree_set"
        },
    ]

    def after_publish_reference(self, published_instance, published_reference, publish_name):
        if publish_name == "verification_document":
            published_instance.verification_document = published_reference


class ExamApplicationOrderManager(models.Manager):
    def get_queryset(self):
        # TO DO... may be better to query by product type code instead of product code...
        # .select_related("purchase_set")
        return super().get_queryset().filter(purchase__product__product_type__in=["EXAM_APPLICATION"]).distinct()

class ExamApplicationOrder(Order):
    objects = ExamApplicationOrderManager()

    class Meta:
        verbose_name="Exam application order"
        proxy = True

class ExamRegistrationOrderManager(models.Manager):
    def get_queryset(self):
        # TO DO... may be better to query by product type code instead of product code...
        # .select_related("purchase_set")
        return super().get_queryset().filter(purchase__product__product_type__in=["EXAM_REGISTRATION"]).distinct()

class ExamRegistrationOrder(Order):
    objects = ExamRegistrationOrderManager()

    class Meta:
        verbose_name="Exam registration order"
        proxy = True

class ExamApplicationReviewManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(content__submission_category__code__in=get_application_category_codes()).distinct()

class ExamApplicationReview(Review):
    objects = ExamApplicationReviewManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return "ROUND %s | %s" % (self.review_round, self.contact)

    def save(self, *args, **kwargs):
        self.review_type = "EXAM_REVIEW"
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name="Exam application review"
        proxy = True


class ExamApplicationRole(ReviewRole):
    class_query_args = {"review_type":"EXAM_REVIEW"}

    class Meta:
        verbose_name="Exam application reviewer role"
        proxy = True


class AICPCandidateApplication(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(content_type="EXAM", application_type__contains="CAND")


class AICPCandidateApplication(ExamApplication):
    objects = ApplicationCategoryManager()
    class Meta:
        proxy = True
        verbose_name_plural = "AICP Candidate Applications"

    def save(self, *args, **kwargs):
        self.content_type = "EXAM"
        return super(AICPCandidateApplication, self).save(*args, **kwargs)


class AICPCredentialData(models.Model):
    """
    A convenience table to allow us to avoid constant calls to Open Water's API.
    The system of record for this data is Open Water. This is only for display in MyAPA.
    """

    imis_id = models.CharField(max_length=200, null=True, blank=True, db_index=True)
    open_water_user_id = models.CharField(max_length=200, null=True, blank=True, db_index=True)

    candidate_application_submission_date = models.DateTimeField(blank=True, null=True)
    candidate_application_status = models.CharField(max_length=200, null=True, blank=True)

    candidate_essays_submission_date = models.DateTimeField(blank=True, null=True)
    candidate_essays_status = models.CharField(max_length=200, null=True, blank=True)

    traditional_application_submission_date = models.DateTimeField(blank=True, null=True)
    traditional_application_status = models.CharField(max_length=200, null=True, blank=True)

    traditional_essays_submission_date = models.DateTimeField(blank=True, null=True)
    traditional_essays_status = models.CharField(max_length=200, null=True, blank=True)

    exam_registration_submission_date = models.DateTimeField(blank=True, null=True)
    exam_registration_eligibility_id = models.CharField(max_length=200, null=True, blank=True)
    exam_registration_exam_window_open = models.DateTimeField(blank=True, null=True)
    exam_registration_exam_window_close = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "AICP Process Data from Open Water for imis user: %s" % (self.imis_id)

    class Meta:
        verbose_name = "AICP Credential Data"
        verbose_name_plural = "AICP Credential Data"
