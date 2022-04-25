from django import forms

from comments.models import SPEAKER_RATING_LEVELS_WITH_NUMBERS

from .models import (EventComment, ExtendedEventEvaluation, RATING_LEVELS,
                     LEARN_MORE_CHOICES, RATING_LEVELS_WITH_NUMBERS,
                    SPEAKER_RATING_LEVELS_WITH_NUMBERS
                     )


class ExtendedEventEvaluationForm(forms.ModelForm):
    """ Currently only used for National Planning Conference"""

    objective_rating = forms.ChoiceField(label="This activity achieved the stated learning outcomes",
        required=True, choices=RATING_LEVELS_WITH_NUMBERS, widget=forms.RadioSelect())

    knowledge_rating = forms.ChoiceField(label="This activity increased my knowledge",
        required=True, choices=RATING_LEVELS_WITH_NUMBERS, widget=forms.RadioSelect())

    practice_rating = forms.ChoiceField(label="I will make a change in the way I practice planning based upon my participation in this activity",
        required=True, choices=RATING_LEVELS_WITH_NUMBERS, widget=forms.RadioSelect())

    speaker_rating = forms.ChoiceField(label="The presenter(s)/subject matter expert(s) delivered the content effectively",
        required=True, choices=SPEAKER_RATING_LEVELS_WITH_NUMBERS, widget=forms.RadioSelect())

    value_rating = forms.ChoiceField(label="I would endorse this activity as a high-quality learning opportunity",
        required=True, choices=RATING_LEVELS_WITH_NUMBERS, widget=forms.RadioSelect())

    learn_more_choice = forms.ChoiceField(label="Would you like to learn more on this topic area?",
        required=True, choices=LEARN_MORE_CHOICES, widget=forms.RadioSelect())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = ExtendedEventEvaluation
        fields = ["content", "contact", "objective_rating", "knowledge_rating", "practice_rating", "speaker_rating",
                  "value_rating", "commentary_suggestions", "learn_more_choice", "publish"]
        widgets = {"content": forms.HiddenInput(), "contact": forms.HiddenInput()}
        labels = {"commentary_suggestion": "Provide any additional comments regarding this educational activity"}

