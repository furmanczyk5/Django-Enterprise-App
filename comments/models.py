from statistics import mean
from django.db import models
from django.utils import timezone

from content.utils import generate_filter_model_manager

COMMENT_TYPES = (
    ("STORE_REVIEW", "Product Review"),
    ("CONTENT", "General Comments on Content"),
    ("CM", "CM Log Comments and Ratings"),
    ("EVENT_EVAL", "Event Evaluations"),
    ("LEARN_COURSE", "APA Learn Course Eval/Completion"),
    ("LEARN_SPEAKER", "APA Learn Speaker Eval/Completion"),
    ("SPEAKER_EVAL", "Speaker Evaluations"),
    ("HIDDEN_LEARN_COURSE", "Hidden APA Learn Course Eval/Completion"),
)

LEARN_MORE_CHOICES = (
    ("YES", "Yes"),
    ("NO", "No"),
    ("UNDECIDED", "Undecided")
)

RATING_LEVELS_ASSESS = (
    (1, "Poor"),
    (2, "Fair"),
    (3, "Good"),
    (4, "Very Good"),
    (5, "Excellent")
    )
RATING_LEVELS = (
    (1, "Strongly Disagree"),
    (2, "Disagree"),
    (3, "Neutral"),
    (4, "Agree"),
    (5, "Strongly Agree")
    )

SPEAKER_RATING_LEVELS = (
    (0, "Not Applicable"),
    (1, "Strongly Disagree"),
    (2, "Disagree"),
    (3, "Neutral"),
    (4, "Agree"),
    (5, "Strongly Agree")
    )

# These are used in forms -- prob. should be in those files
RATING_LEVELS_WITH_NUMBERS = (
    (5, RATING_LEVELS[len(RATING_LEVELS)-1][1] + " (5)"),
    (4, RATING_LEVELS[len(RATING_LEVELS)-2][1] + " (4)"),
    (3, RATING_LEVELS[len(RATING_LEVELS)-3][1] + " (3)"),
    (2, RATING_LEVELS[len(RATING_LEVELS)-4][1] + " (2)"),
    (1, RATING_LEVELS[len(RATING_LEVELS)-5][1] + " (1)"),
    )

SPEAKER_RATING_LEVELS_WITH_NUMBERS = (
    (5, RATING_LEVELS[len(RATING_LEVELS)-1][1] + " (5)"),
    (4, RATING_LEVELS[len(RATING_LEVELS)-2][1] + " (4)"),
    (3, RATING_LEVELS[len(RATING_LEVELS)-3][1] + " (3)"),
    (2, RATING_LEVELS[len(RATING_LEVELS)-4][1] + " (2)"),
    (1, RATING_LEVELS[len(RATING_LEVELS)-5][1] + " (1)"),
    (0, "Not Applicable")
    )


class Comment(models.Model):
    """
    Stores a comment that a contact submits for a particular piece of content (including possibly commentary
    text and rating, depending on the particular type of comment). Used for comments on content (e.g. on articles),
    store reviews, CM ratings, etc.
    """
    comment_type = models.CharField(max_length=50, choices=COMMENT_TYPES, default="CONTENT")
    contact = models.ForeignKey("myapa.Contact", related_name="comments", on_delete=models.CASCADE)
    content = models.ForeignKey(
        "content.Content",
        related_name="comments",
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )
    submitted_time = models.DateTimeField(editable=False)
    commentary = models.TextField(blank=True, null=True)
    rating = models.IntegerField(choices=RATING_LEVELS_ASSESS, blank=False, null=True)
    flagged = models.BooleanField(default=False)
    publish = models.BooleanField(default=False)

    contactrole = models.ForeignKey(
        "myapa.ContactRole",
        related_name="comments",
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    ) # For commenting on specific roles, used for speaker ratings

    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    def save(self, *args, **kwargs):

        if not self.submitted_time:
            self.submitted_time = timezone.now()
        super().save(*args, **kwargs)

        # update content rating count and average
        if self.content:
            content = self.content
            content.recalculate_rating()
            content.save()

    def __str__(self):
        return str(self.rating) + " stars | " + str(self.submitted_time)

class EventComment(Comment):

    objects = generate_filter_model_manager(ParentManager=models.Manager, comment_type="EVENT_EVAL")()

    def save(self, *args, **kwargs):
        self.comment_type = "EVENT_EVAL"
        super().save(*args, **kwargs)

    class Meta:
        proxy = True


class ExtendedEventEvaluation(Comment):
    objective_rating = models.IntegerField(choices=RATING_LEVELS, blank=False, null=True)
    value_rating = models.IntegerField(choices=RATING_LEVELS, blank=False, null=True)
    learn_more_choice = models.CharField(choices=LEARN_MORE_CHOICES, max_length=25, blank=False, null=True)
    commentary_takeaways = models.TextField(blank=True, null=True)
    commentary_suggestions = models.TextField(blank=True, null=True)
    knowledge_rating = models.IntegerField(choices=RATING_LEVELS, blank=False, null=True)
    practice_rating = models.IntegerField(choices=RATING_LEVELS, blank=False, null=True)
    speaker_rating = models.IntegerField(choices=SPEAKER_RATING_LEVELS, blank=False, null=True)

    def save(self, *args, **kwargs):
        if self.comment_type not in ["EVENT_EVAL", "CM", "LEARN_COURSE"]:
            self.comment_type = "EVENT_EVAL"

        ratings = [self.objective_rating, self.value_rating, self.knowledge_rating, self.practice_rating]
        # speaker rating is not included if zero('N/A')
        if self.speaker_rating != 0:
            ratings.append(self.speaker_rating)

        ratings_mean = []
        for rating in ratings:
            try:
                ratings_mean.append(float(rating))
            except (TypeError, ValueError):
                pass
        if ratings_mean:
            self.rating = mean(ratings_mean)
        super().save(*args, **kwargs)

    def __str__(self):
        if self.rating:
            return "Rating: " + str(RATING_LEVELS[self.rating-1][1]) + " | " + str(self.submitted_time)
        else:
            if self.content:
                return "Evaluation of: " + self.content.title
            elif self.contact:
                return "Evaluation by: " + self.contact
            else:
                return "Evaluation"
