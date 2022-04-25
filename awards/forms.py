from django import forms
from django.forms.models import BaseInlineFormSet

from content.forms import StateCountryModelFormMixin, AddFormControlClassMixin
from uploads.models import Upload, UploadType, COPYRIGHT_TYPES
from uploads.forms import FileUploadBaseForm, ImageUploadBaseForm, \
    UPLOAD_TYPE_FORMS
from submissions.forms import SubmissionBaseForm, \
    SubmissionCategoryForm as SubmissionCategoryBaseForm, \
    SubmissionVerificationForm

from .models import Submission, SubmissionCategory, JurorAssignment

RATING_CHOICES = ((None, "--"), (1, 1), (2, 2), (3, 3), (4, 4))


def generateUploadTypeAdminInlineFormset(upload_type_code):

    class UploadTypeAdminInlineFormset(BaseInlineFormSet):

        def save_new_objects(self, commit=True):
            saved_instances = super().save_new_objects(False)
            upload_type = UploadType.objects.get(code=upload_type_code)
            for instance in saved_instances:
                instance.upload_type = upload_type
            return super().save_new_objects(True)

    return UploadTypeAdminInlineFormset


class AwardsSubmissionForm(StateCountryModelFormMixin, SubmissionBaseForm):

    tag_type_choices = []

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['title'] = forms.CharField(
            required=True,
            label="Name of Entry",
            widget=forms.TextInput(
                attrs={"placeholder": "six words or less"}))

        self.fields['city'] = forms.CharField(
            required=self.is_strict,
            widget=forms.TextInput(
                attrs={"placeholder": "City"}))

        self.init_state_country_fields(
            state_required=self.is_strict,
            country_required=self.is_strict)

        self.add_form_control_class()

    def presave(self):
        super().presave()
        self.instance.status = "N"

    class Meta:
        model = Submission
        fields = ["title", "city", "state", "country"]


class AwardsSubmissionVerificationForm(SubmissionVerificationForm):

    submitted_status = "A"

    submission_verified = forms.BooleanField(
        label='Verify Submission',
        required=True,
        initial=False,
        help_text="By checking, I confirm the information presented in this \
                   nomination is truthful and complete.")

    class Meta:
        model = Submission
        fields = ["submission_verified"]


class UploadSupportLetterForm(AddFormControlClassMixin, FileUploadBaseForm):

    upload_type_code = "AWARD_LETTER_OF_SUPPORT"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["creator_full_name"].label = "Name of Letter Writer"
        self.fields["creator_full_name"].required = True

        self.add_form_control_class()

    def save(self, commit=True):
        upload = super().save(commit=False)
        upload.publish_status = "SUBMISSION"
        if commit:
            upload.save()
        return upload

    class Meta:
        model = Upload
        fields = ["content", "creator_full_name", "uploaded_file"]


class UploadImageForm(AddFormControlClassMixin, ImageUploadBaseForm):

    upload_type_code = "AWARD_IMAGE"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["description"] = forms.CharField(
            label="Caption",
            widget=forms.TextInput(),
            required=True)

        self.fields["copyright_type"] = forms.ChoiceField(
            choices=COPYRIGHT_TYPES,
            widget=forms.RadioSelect(attrs={"class": "no-style"}),
            label="Copyright",
            initial=COPYRIGHT_TYPES[0][0])

        self.add_form_control_class()

    def save(self, commit=True):
        upload = super().save(commit=False)
        upload.publish_status = "SUBMISSION"
        if commit:
            upload.save()
        return upload

    class Meta:
        model = Upload
        fields = ["content", "description", "copyright_type", "image_file"]


class UploadSupplementalMaterialForm(AddFormControlClassMixin, FileUploadBaseForm):

    upload_type_code = "AWARD_SUPLEMENTAL_MATERIALS"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["resource_class"].required=True
        self.fields["description"].required=True
        self.fields["url"].required=False
        self.fields["uploaded_file"].required=False #either provide file or url

        self.add_form_control_class()

    def clean(self):

        cleaned_data = super().clean()

        upload_or_url = cleaned_data.get(self.upload_field_name,None) or cleaned_data.get("url",None)
        if upload_or_url is None:
            self.add_error(self.upload_field_name, "You must provide either a file upload or a valid url")

        return cleaned_data

    def save(self, commit=True):
        upload = super().save(commit=False)
        upload.publish_status = "SUBMISSION"
        if commit:
            upload.save()
        return upload

    class Meta:
        model = Upload
        fields = ["content", "resource_class", "description", "url", "uploaded_file"]
        labels = {
            "resource_class": "Resource Type"
        }
        widgets = {
            "url": forms.TextInput(attrs={"placeholder":"https://www.planning.org"}),
            "description": forms.TextInput()
        }


UPLOAD_TYPE_FORMS["AWARD_LETTER_OF_SUPPORT"] = UploadSupportLetterForm
UPLOAD_TYPE_FORMS["AWARD_IMAGE"] = UploadImageForm
UPLOAD_TYPE_FORMS["AWARD_SUPLEMENTAL_MATERIALS"] = UploadSupplementalMaterialForm


class SubmissionCategoryForm(SubmissionCategoryBaseForm):

    class Meta:
        model = SubmissionCategory
        fields = ["code", "title", "status", "product_master", "description",
                  "questions", "upload_types"]


class JurorReviewForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):

        self.base_fields['rating_1'] = forms.ChoiceField(
            choices=RATING_CHOICES)

        super().__init__(*args, **kwargs)
        self.fields['contact'].widget = forms.HiddenInput()
        self.fields['content'].widget = forms.HiddenInput()
        self.fields['role'].widget = forms.HiddenInput()

    class Meta:
        model = JurorAssignment
        fields = ['contact', 'content', 'role', 'comments', 'rating_1']
