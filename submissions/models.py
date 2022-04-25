import pytz
import datetime

from django.db import models

from planning.models_subclassable import SubclassableModel

from content.models import Content, Tag, TagType, BaseContent, \
    CONTENT_TYPES, Publishable
from myapa.models.contact import Contact


QUESTION_TYPES = (
    ("LONG_TEXT", "Long Text"),
    ("SHORT_TEXT", "Short Text"),
    ("CHECKBOX", "Checkbox"),
    ("CHECKBOX_FINAL", "Final Step Checkbox"),
    ("TAG", "Tag options")
)

REVIEW_ROUNDS = (
    (1, 1),
    (2, 2),
    (3, 3),
    (4, 4),
    (5, 5),
    (6, 6)
)

REVIEW_TYPES = (
    ("AWARDS_JURY", "Awards Jury"),
    ("RESEARCH_INQUIRY", "PAS Research Inquiry"),
    ("EXAM_REVIEW", "Exam Application Reviewer"),
    ("CONFERENCE_PROPOSAL_REVIEW", "Conference Proposal Review"),
    ("KNOWLEDGEBASE_SUGGESTION_REVIEW", "Knowledgebase Suggestion Review"),
    ("KNOWLEDGEBASE_STORY_REVIEW", "Knowledgebase Story Review"),
)

REVIEW_STATUSES = (
    ("REVIEW_RECEIVED", "Review Received"),
    ("REVIEW_UNDERWAY", "Review Underway"),
    ("REVIEW_COMPLETE_ADDED", "Review Completed: ADDED"),
    ("REVIEW_COMPLETE_DUPLICATIVE", "Review Completed: DUPLICATIVE"),
    ("REVIEW_COMPLETE_OFF_TOPIC", "Review Completed: OFF-TOPIC"),
)

# TO DO maybe: use SUBMISSION_TYPE in addition to CONTENT_TYPE? Assume not... but if so would look something like this:
# SUBMISSION_TYPES = (
#     ("AWARD", "Award Nominations"),
#     ("EXAM", "AICP exam"),
#     ("PROPOSAL", "Conference proposals"),
#     ("RFP", "RFPs/RFQs"),
#     ("RFP", "RFPs/RFQs"),
# )


class SubmissionModelMixin(object):

    # TBD: this might be useful:
    # def is_valid(self):
    #     pass

    def upload_type_valid(self, upload_type):
        """
        return true/false if given upload type is valid for this submission content
        NOTE: It is best to pass an upload_type with uploads prefetched, specific
        This method will update attributes on the queryset so that you can access errors for specific uploads (check the_errors property)
        """
        max_file_size   = (upload_type.max_file_size or 1000000)*1024 # surly nothing is that big
        allowed_min     = upload_type.allowed_min or 0
        allowed_max     = upload_type.allowed_max or 1000 # surly nothing has that many uploads
        allowed_extensions = [".%s" % ft.extension.strip(".") for ft in upload_type.allowed_types.all()] # this should have at least one
        number_of_uploads = len(upload_type.the_uploads)
        upload_type.the_errors = []

        is_valid = True
        if number_of_uploads > allowed_max:
            is_valid = False
            upload_type.the_errors.append("You cannot submit more than %s uploads for this section" % allowed_max)
        elif number_of_uploads < allowed_min:
            is_valid = False
            upload_type.the_errors.append("You cannot submit less than %s uploads for this section" % allowed_min)

        for upload in self.uploads:
            upload.the_errors = []
            file_or_image_upload = upload.fileupload.uploaded_file if hasattr(upload,"fileupload") else upload.imageupload.image_file
            if file_or_image_upload:
                if file_or_image_upload.size > max_file_size:
                    is_valid = False
                    upload.the_errors.append("Upload %s is larget than the max file size (%s) for this section. Replace this with a valid upload and try again." % (upload, max_file_size))
                root, ext = os.path.splitext(file_or_image_upload.name)
                if ext not in allowed_extensions:
                    is_valid = False
                    upload.the_errors.append("Upload %s has an invalid file extension (%s) for this section. Replace this upload with a valid file type for this section. %w" % (upload, ext, allowed_extensions))
        return is_valid


class Question(BaseContent):
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPES, default="SHORT_TEXT")
    help_text = models.TextField(blank=True, null=True)
    required = models.BooleanField(default=False)
    words_min = models.IntegerField(null=True, blank=True)
    words_max = models.IntegerField(null=True, blank=True)
    tag_type = models.ForeignKey("content.TagType", null=True, blank=True, on_delete=models.SET_NULL)
    sort_number = models.IntegerField(null=True, blank=True)
    # class Meta:
    #     managed = False
    #     db_table = 'submissions_question'


class Category(BaseContent):
    """
    questions and terms for a submission category (ie. content type: AWARD - category: best practice)
    NOTE: all submissions must have a category
    """
    content_type = models.CharField(max_length=50, choices=CONTENT_TYPES, default="PAGE")
    questions = models.ManyToManyField("Question", related_name="categories", blank=True,)
    reviewer_tag_types = models.ManyToManyField(TagType, blank=True)
    upload_types = models.ManyToManyField("uploads.UploadType", related_name="submission_categories", blank=True)
    product_master = models.ForeignKey(
        "content.MasterContent",
        related_name="submission_categories",
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )

    deadline_time = models.DateTimeField("deadline", blank=True, null=True) # DONT USE THIS ANYMORE
    sort_number = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return str(self.title)

    def deadline_chicago(self):
        """
        returns the deadline_time to have with chicago timezone, but does not
        change the time (e.g. 12:00 utc -> 12:00 chicago, and not 12:00 utc -> 7:00 chicago)
        """
        return pytz.timezone("America/Chicago").localize(self.deadline_time.replace(tzinfo=None)) if self.deadline_time else None

    def get_open_active_period(self):
        return next( (p for p in self.periods.all() if p.is_open()) , None)

    def get_latest_active_period(self):
        mindate = datetime.datetime(datetime.MINYEAR, 1, 1, tzinfo=pytz.timezone("America/Chicago"))
        maxdate = datetime.datetime(datetime.MAXYEAR, 1, 1, tzinfo=pytz.timezone("America/Chicago"))
        sorted_periods = sorted(self.periods.all(), key=lambda p: (p.begin_time_chicago() or mindate, p.end_time_chicago() or maxdate), reverse=True)
        return next((p for p in sorted_periods if p.status == "A"), None)

    def is_open(self):
        return self.get_open_active_period() is not None

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Categories"


class Answer(Publishable):
    text = models.TextField(blank=True, null=True)
    boolean = models.BooleanField(default=False)
    question = models.ForeignKey("Question", related_name="answers", on_delete=models.CASCADE)
    content = models.ForeignKey("content.Content", related_name="submission_answer", on_delete=models.CASCADE)
    tag = models.ForeignKey(
        "content.Tag",
        null=True,
        blank=True,
        related_name="submission_answers",
        on_delete=models.SET_NULL
    )

    def get_value(self):
        question_type = self.question.question_type
        if question_type in "CHECKBOX":
            return self.boolean
        else:
            return self.text

    def set_value(self, value):
        question_type = self.question.question_type
        if question_type == "CHECKBOX":
            self.boolean = value
        else:
            self.text = value
        self.save()

    def __str__(self):
        return str(self.question) + " answered:"

    # class Meta:
    #     managed = False
    #     db_table = 'submissions_answer'


class Period(BaseContent):
    """
    will allow us to dynamically open and close submissions
    """
    content_type = models.CharField(max_length=50, choices=CONTENT_TYPES, default="AWARDS")
    begin_time = models.DateTimeField('begin time', null=True, blank=True)
    end_time = models.DateTimeField('end time', null=True, blank=True)
    category = models.ForeignKey("Category", related_name="periods", on_delete=models.CASCADE)

    def begin_time_chicago(self):
        tz=pytz.timezone('America/Chicago')
        return self.begin_time.astimezone(tz) if self.begin_time else None
        # return pytz.timezone("America/Chicago").localize(self.begin_time.replace(tzinfo=None)) if self.begin_time else None

    def end_time_chicago(self):
        tz=pytz.timezone('America/Chicago')
        return self.end_time.astimezone(tz) if self.end_time else None
        # return pytz.timezone("America/Chicago").localize(self.end_time.replace(tzinfo=None)) if self.end_time else None

    def is_past(self):
        now_chicago = datetime.datetime.now(pytz.timezone("America/Chicago"))
        end_time_chicago = self.end_time_chicago()
        return not (end_time_chicago is None or end_time_chicago > now_chicago)

    def is_future(self):
        now_chicago = datetime.datetime.now(pytz.timezone("America/Chicago"))
        begin_time_chicago = self.begin_time_chicago()
        return not (begin_time_chicago is None or begin_time_chicago < now_chicago)

    def is_open(self):
        now_chicago = datetime.datetime.now(pytz.timezone("America/Chicago"))
        begin_time_chicago = self.begin_time_chicago()
        end_time_chicago = self.end_time_chicago()
        return (self.status == "A") and not self.is_past() and not self.is_future()


# try not to hard code rating field names... may need to define in submission category
# submitted time only used when complete
# defining particular types of roles (juror 1, 2, 3)
# right now - assign by id
class ReviewRole(BaseContent):
    """
    Stores an assignment for a person to a particular role for reviewing... the title can be used
    to name the role (e.g. "Awards Juror 1" or "Proposal Reviewer")
    """
    contact = models.ForeignKey(Contact, related_name='review_roles', on_delete=models.CASCADE)

    #TO DO MAYBE... maybe it would make more sense to change this to "content_type" (or SUBMISSION_TYPE if we go that route)??
    review_type = models.CharField(max_length=50, choices=REVIEW_TYPES, default="AWARDS_JURY")

    def __str__(self):
        return str(self.review_type) + " | " + str(self.contact) + " | " + str(self.title)


class Review(SubclassableModel, models.Model):
    """
    Stores a particular review assignment for a given person and a given piece
    of content, including the comments/tags/ratings submitted by the reviewer
    when completing the review assignment
    """
    role = models.ForeignKey(ReviewRole, related_name="reviews", null=True, blank=True, on_delete=models.SET_NULL)
    contact = models.ForeignKey(Contact, related_name="reviews", on_delete=models.CASCADE)
    content = models.ForeignKey(Content, related_name="review_assignments", on_delete=models.CASCADE)
    # TO DO: can we simplify this so that there is only a single rating field?
    rating_1 = models.IntegerField(null=True, blank=True)
    rating_2 = models.IntegerField(null=True, blank=True)
    rating_3 = models.IntegerField(null=True, blank=True)
    rating_4 = models.IntegerField(null=True, blank=True)
    comments = models.TextField(blank=True, null=True)
    assigned_time = models.DateTimeField(editable=False, blank=True, null=True)
    deadline_time = models.DateTimeField(blank=True, null=True)
    review_time = models.DateTimeField(editable=False, blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True)
    review_type = models.CharField(max_length=50, choices=REVIEW_TYPES, default="AWARDS_JURY")
    review_round = models.IntegerField(choices=REVIEW_ROUNDS, default=1) # for submission processes with multiple rounds of reviews (e.g. exam app)
    recused = models.BooleanField(default=False)
    custom_boolean_1 = models.BooleanField(default=False)
    custom_text_1 = models.TextField(blank=True, null=True)
    custom_text_2 = models.TextField(blank=True, null=True)
    review_status = models.CharField(max_length=50, choices=REVIEW_STATUSES, default="REVIEW_RECEIVED" )
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.contact) + " | " + str(self.content)


class AnswerReview(models.Model):
    """
    Stores a reviewer's rating and comments on a particular answer for a submission.
    """
    #TO DO... should we use many-to-many on Review in order to
    review = models.ForeignKey(Review, related_name="answer_reviews", on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, related_name="answer_reviews", on_delete=models.CASCADE)
    rating = models.IntegerField(null=True, blank=True)
    comments = models.TextField(blank=True, null=True)
    answered_successfully = models.NullBooleanField(blank=True, null=True)

    def __str__(self):
        return "REVIEW OF: %s" % self.answer.question.title
