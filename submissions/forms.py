import re

from django import forms
from django.db.models import Prefetch
from django.utils import timezone

from content.models import Content, ContentTagType, Tag, TagType

from .models import Category, Question, Answer


class SubmissionVerificationForm(forms.ModelForm):
    """
    Form used for verifying content before it's final submission
    """
    submitted_status = "A"

    def __init__(self, *args, **kwargs):
        self.complete_submission = kwargs.pop("complete_submission", True)
        super().__init__(*args, **kwargs)
        self.fields["submission_verified"].required = True

    def save(self):
        content = super().save(commit=False)
        if self.complete_submission:
            content.submission_time = timezone.now()
            content.status = self.submitted_status
        content.save()
        return content

    class Meta:
        model = Content
        fields = ["submission_verified"]


class SubmissionBaseForm(forms.ModelForm):

    tag_type_choices = []  # list of dicts e.g. {"code":"SEARCH_TOPIC", "required"="True"} could also include optional values like description, label, help_text, etc.
    submission_category_code = None  # by default defined elsewhere
    default_publish_status = "SUBMISSION" # by default, the publish_status to save edited record with

    # OTHER FIELDS...

    # is_strict
    # submission_category_code

    # submission_category
    # tag_types

    def __init__(self, *args, **kwargs):

        self.is_strict = kwargs.pop("is_strict", True)
        self.publish_status = kwargs.pop("publish_status", self.default_publish_status)

        submission_category_code = kwargs.pop("submission_category_code", None)
        self.submission_category_code = getattr(self, "submission_category_code", None) or submission_category_code # If it's defined on the form use, that

        super().__init__(*args, **kwargs)

        if self.instance.pk is not None and self.instance.submission_category is not None:
            self.submission_category_code = self.instance.submission_category.code

        self.init_tag_choice_fields()
        self.init_submission_question_fields()

    def add_form_control_class(self):
        """
        adds the form-control class to all initialized fields in the form
        """

        for field in self.fields:
            class_attr = self.fields[field].widget.attrs.get("class", '')
            if not re.search(r'\bform-control\b', class_attr):
                self.fields[field].widget.attrs["class"] = "form-control " + class_attr

    def init_tag_choice_fields(self):
        """
        Initializes all tag choice fields, these are any fields that will be saves as a tag attached to content
        """

        self.tag_types = TagType.objects.filter(
            code__in=[x["code"] for x in self.tag_type_choices]
        ).prefetch_related(
            Prefetch(
                "contenttagtype",
                queryset=ContentTagType.objects.filter(content=self.instance),
                to_attr="the_contenttagtype"
            ),
            Prefetch("tags", to_attr="the_tags")
        )

        for tag_type in self.tag_types:

            tag_type_choice = [x for x in self.tag_type_choices if x["code"] == tag_type.code][0]
            max_tags = tag_type_choice.get("max_tags", 1)
            tag_type_field = tag_type_choice.get("field", forms.ChoiceField)

            choices = [
                (tag.code, tag.title) for tag in
                sorted(tag_type.the_tags, key=lambda x: (x.sort_number, x.title), reverse=False)
            ]
            the_contenttagtype = tag_type.the_contenttagtype

            if the_contenttagtype and the_contenttagtype[0].tags.all():
                if max_tags > 1: # indicator that this is select multiple, may want to assign field and widget based on this too
                    tag_code_initial = [t.code for t in the_contenttagtype[0].tags.all()]
                else:
                    tag_code_initial = the_contenttagtype[0].tags.all()[0].code
            else:
                tag_code_initial = None

            self.fields['tag_choice_%s' % tag_type.code] = tag_type_field(
                label=tag_type.title,
                required=tag_type_choice["required"] and self.is_strict,
                choices=choices,
                initial=tag_code_initial,
                help_text=tag_type.description,
            )

    def init_submission_question_fields(self):

        self.submission_category = Category.objects.filter(
            code=self.submission_category_code
        ).prefetch_related(
            Prefetch(
                "questions",
                queryset=Question.objects.filter(
                    status="A"
                ).prefetch_related(
                    Prefetch(
                        "answers",
                        queryset=Answer.objects.filter(content=self.instance),
                        to_attr="the_answer"
                    )
                ).order_by(
                    "sort_number"
                ), to_attr="the_questions"
            )
        ).first()

        for question in self.submission_category.the_questions:

            is_required = question.required and self.is_strict

            if question.question_type == "CHECKBOX":
                form_field = forms.BooleanField
                widget = None
                empty_value = False
            elif question.question_type == "SHORT_TEXT":
                form_field = forms.CharField
                widget = None
                empty_value = None
            elif question.question_type == "LONG_TEXT":
                form_field = forms.CharField
                widget = forms.Textarea(
                    attrs={'class': 'full-width wordcounter', 'placeholder': question.help_text}
                )
                empty_value = None
            elif question.question_type == "TAG":
                form_field = forms.ChoiceField
                widget = None
                empty_value = None
            else:
                # add any others - If these values aren't set here, the AICP application process throws an error below
                form_field = forms.CharField
                widget = forms.Textarea(
                    attrs={'class': 'full-width wordcounter', 'placeholder': question.help_text}
                )
                empty_value = None

            if self.instance.pk is not None and question.the_answer:
                initial_answer = question.the_answer[0].get_value()
            else:
                initial_answer = empty_value

            self.fields["submission_question_%s" % question.id] = form_field(
                required=is_required,
                label=question.title,
                help_text=question.description,
                initial=initial_answer
            )
            if widget is not None:
                self.fields["submission_question_%s" % question.id].widget = widget

    def process_submission_questions(self):

        for question in self.submission_category.the_questions:
            submission_field_name = "submission_question_%s" % question.id
            the_answer, is_created = Answer.objects.update_or_create(
                content=self.instance,
                question=question,
                defaults={"publish_status": self.publish_status}
            )
            if submission_field_name in self.cleaned_data: # make sure the field is in the form before setting it
                the_answer.set_value(self.cleaned_data[submission_field_name])

    def process_tag_choice_fields(self):

        for tag_type in self.tag_types:
            tag_code = self.cleaned_data['tag_choice_%s' % tag_type.code]

            if tag_code:
                tag_code_list = tag_code if isinstance(tag_code, list) else [tag_code] # will work for mulitple or single selection
                content_tag_type, _ = ContentTagType.objects.update_or_create(
                    content=self.instance,
                    tag_type=tag_type,
                    defaults={"publish_status": self.publish_status}
                )
                content_tag_type.tags.clear()
                content_tag_type.tags.add(*list(Tag.objects.filter(tag_type=tag_type, code__in=tag_code_list)))
            else:
                ContentTagType.objects.filter(content=self.instance, tag_type__code=tag_type.code).delete()

    def save_nonmodel_fields(self):
        """
        Very similar to save_m2m. Call this on the form after calling save with commit=False to process
            data not on the Image model
        NOTE: I made this up because you can't inherit from save_m2m, which is generated method within the save method
        """
        if self.instance:
            self.process_submission_questions()
            self.process_tag_choice_fields()

    def presave(self):
        """
        hook for any logic that needs to happen with model before writing to db
        """
        # e.g. for events
        # event.event_type = self.event_type
        pass

    def clean(self):

        cleaned_data = super().clean()

        if not self.is_strict:
            return cleaned_data # DON'T OD extra validation if self.is_strict is False

        for question in self.submission_category.the_questions:
            words_min = question.words_min or None
            words_max = question.words_max or None
            question_field_name = "submission_question_%s" % question.id
            answer = self.cleaned_data.get(question_field_name, "")
            answer_word_count = len(re.findall(r'\S+', answer))

            if answer and words_min and answer_word_count < words_min:
                self.add_error(
                    question_field_name,
                    "Word Count: %s; Your response must be over %s words." % (answer_word_count, words_min))
            elif answer and words_max and answer_word_count > words_max:
                self.add_error(
                    question_field_name,
                    "Word Count: %s; Your response must not exceed %s words. " % (answer_word_count, words_max))

        begin_time = self.cleaned_data.get('begin_time', "")
        end_time = self.cleaned_data.get('end_time', "")

        if begin_time and begin_time.year < 2:
            self.add_error('begin_time', "Begin time year must be at least 0002")
        if end_time and end_time.year < 2:
            self.add_error('end_time', "End time year must be at least 0002")

        return cleaned_data

    def save(self, commit=True):

        status = self.get_save_status()

        self.instance = content = super().save(commit=False)
        content.publish_status = self.publish_status
        # does this need to change depending on the submission type??
        content.status = status
        content.submission_category = self.submission_category
        content.submission_period = self.submission_category.get_open_active_period()
        self.presave() #HOOK

        if commit:
            content.save()
            self.save_nonmodel_fields()

        return content

    def get_save_status(self):
        """ by default always save with status N,
            any edits still need to be reviewed and submitted """
        return "N"

    def validate_unbound_form(self):
        """
        Call this after initialization to validate an unbound form
        NOTE: you can only do this for unbound forms
        """
        if not self.is_bound:

            self.data = self.initial

            for key, field in self.fields.items():
                if field.initial is not None and key not in self.data:
                    self.data[key] = field.initial # any initial extra processing will be factored in

            self.is_bound = True

            return self.is_valid()

    class Meta:
        model = Content
        fields = ["title", "submission_verified"]


class SubmissionCategoryForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields["product_master"].queryset = MasterContent.objects.filter(content__content_type="PRODUCT").distinct("id")

    class Meta:
        model = Category
        fields = [
            "code",
            "title",
            "status",
            "product_master",
            "sort_number",
            "description",
            "questions",
            "upload_types"
        ]



