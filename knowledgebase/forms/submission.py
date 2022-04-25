from django import forms

from knowledgebase.models import (
    ResourceSuggestion,
    Story
)
from content.models import Content
from submissions.forms import SubmissionBaseForm


class SubmissionTypeForm(SubmissionBaseForm):
    default_publish_status = 'DRAFT'
    submission_category_code = None

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)

        super().__init__(*args, **kwargs)

        self.fields['title'] = forms.CharField(
            required=True, min_length=1, max_length=250
        )

        self.fields['text'] = forms.CharField(
            required=True,
            widget=forms.Textarea(attrs={"data-wysiwyg": True})
        )

        self.fields['description'] = forms.CharField(
            required=True,
            max_length=250,
            help_text='Must be 250 characters or less'
        )

        self.fields['editorial_comments'] = forms.CharField(
            required=False,
            label='Notes to Staff',
            help_text='Notes for APA staff regarding your submission',
            widget=forms.TextInput(attrs={"placeholder": "Optional"})
        )

        self.fields['submission_verified'].label = (
            'I verify that I am authorized to share this '
            'information and that it is accurate to the best '
            'of my knowledge. (required)'
        )
        self.fields['submission_verified'].required = True

        collection_drop_choices = [(None, '-' * 25)] + [
            (content.master_id, content.title)
            for content in Content.objects.filter(
                content_type='KNOWLEDGEBASE_COLLECTION',
                publish_status='PUBLISHED',
                status='A'
            ).order_by('title')
        ]

        self.fields['collection_choices'] = forms.CharField(
            label='Associated Collection',
            required=True,
            widget=forms.Select(
                attrs={'class': 'form-control'},
                choices=collection_drop_choices
            ),
            initial=self.set_collection_default(collection_drop_choices)
        )

    def set_collection_default(self, collection_drop_choices):
        if self.instance.id:
            master_collection = self.instance.related.first()
            for collection in collection_drop_choices:
                if master_collection.id == collection[0]:
                    return collection

        return (None, '-' * 25)

    def add_field_class(self):
        for field in self.fields:
            if field != 'text':
                self.fields[field].widget.attrs['class'] = 'form-control'

    def get_save_status(self):
        if self.request and 'submitButton' in self.request.POST:
            return 'P'

        return 'N'


class StorySubmissionTypeForm(SubmissionTypeForm):
    submission_category_code = 'KNOWLEDGEBASE_STORY'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['title'].label = 'Story Title'
        self.fields['text'].label = 'Story Narrative'
        self.fields['description'].label = 'Story Summary'
        self.add_field_class()

    class Meta:
        model = Story
        fields = [
            'title', 'text', 'description', 'editorial_comments',
            'submission_verified', 'related'
        ]


class ResourceSuggestionTypeForm(SubmissionTypeForm):
    submission_category_code = 'KNOWLEDGEBASE_SUGGESTION'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['title'].label = 'Resource Name'
        self.fields['resource_url'].label = 'Resource Url'
        self.fields['resource_url'] = forms.CharField(
            label='Resource Url',
            required=True,
            help_text='Url to recommended resource'
        )

        self.fields['text'].label = 'Description'
        self.fields['description'].label = 'Short Description'
        self.add_field_class()

    class Meta:
        model = ResourceSuggestion
        fields = [
            'title', 'resource_url', 'text', 'description',
            'editorial_comments', 'submission_verified', 'related'
        ]
