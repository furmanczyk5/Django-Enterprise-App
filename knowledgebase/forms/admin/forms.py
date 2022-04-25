from django import forms

from knowledgebase.models import (
    SuggestionReviewRole
)
from content.forms import (
    ContentAdminAuthorForm,
    ContentAdminEditorForm
)


class ReviewForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].label = 'Assigned to'
        self.fields['role'].queryset = SuggestionReviewRole.objects.filter(
            review_type='KNOWLEDGEBASE_REVIEW'
        )
        self.fields['role'].required = True


class SubmissionAdminEditorForm(ContentAdminEditorForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['editorial_comments'].label = 'Notes to Staff'
        self.fields['editorial_comments'].help_text = ''


class SubmissionAdminAuthorForm(ContentAdminAuthorForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['editorial_comments'].label = 'Notes to Staff'
        self.fields['editorial_comments'].help_text = ''


class ResourceSuggestionAdminEditorForm(SubmissionAdminEditorForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _set_resource_suggestion_fields(self)


class ResourceSuggestionAdminAuthorForm(SubmissionAdminEditorForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _set_resource_suggestion_fields(self)


def _set_resource_suggestion_fields(form):
    form.fields['editorial_comments'].label = 'Notes to Staff'
    form.fields['editorial_comments'].help_text = ''
    form.fields['url'].help_text = 'Url of added resource suggestion'
    form.fields['url'].label = 'Published Resource Url'
    form.fields['resource_url'].help_text = (
        'Url to outside source of resource suggestion'
    )
    form.fields['text'].label = 'Description'
    form.fields['description'].label = 'Short Description'
