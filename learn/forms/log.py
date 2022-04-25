from django import forms

from comments.forms import ExtendedEventEvaluationForm
from learn.models.learn_evaluation import LearnCourseEvaluation

class LearnCourseEvaluationForm(ExtendedEventEvaluationForm):
    """
    Form for apa learn course evaluations
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commentary_suggestions"].label = "Provide any additional comments regarding this educational activity"
        self.fields["value_rating"].required = True

    class Meta:
        model = LearnCourseEvaluation
        fields = ["content", "contact", "objective_rating", "knowledge_rating", "practice_rating", "speaker_rating",
                  "value_rating", "commentary_suggestions", "learn_more_choice", "publish"]
        widgets = {"content": forms.HiddenInput(), "contact": forms.HiddenInput()}
