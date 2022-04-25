from django import forms

from submissions.forms import SubmissionBaseForm, SubmissionVerificationForm
from uploads.models import Upload
from uploads.forms import FileUploadBaseForm, UPLOAD_TYPE_FORMS

from .models import Inquiry, INQUIRY_UPLOAD_RESOURCE_CLASSES


class InquirySubmissionEditForm(SubmissionBaseForm):

    submission_category_code = "PAS"

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["title"].required = True
        self.fields['text'] = forms.CharField(
            required=self.is_strict,
            label="Full Inquiry",
            widget=forms.Textarea(attrs={"class": "wordcounter"})
        )

        self.fields["contact_first_name"] = forms.CharField(required=self.is_strict, label="First Name")
        self.fields["contact_last_name"] = forms.CharField(required=self.is_strict, label="Last Name")
        self.fields["contact_email"] = forms.EmailField(required=self.is_strict, label="Email")

        self.add_form_control_class()

    class Meta:
        model = Inquiry
        fields = ["title", "text"]
        labels = dict(title="Subject")


class InquirySubmissionVerificationForm(SubmissionVerificationForm):

    submitted_status = "P"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["submission_verified"].required = False
        self.fields["submission_verified"].widget = forms.HiddenInput()

    class Meta:
        model = Inquiry
        fields = ["submission_verified"]
        labels = dict(submission_verified="Verify Entry")


class UploadResearchMaterialForm(FileUploadBaseForm):

    upload_type_code = "PAS_INQUIRY"

    resource_class = forms.ChoiceField(
        label="Resource Type",
        choices=((None, "-- Select one --"),)+INQUIRY_UPLOAD_RESOURCE_CLASSES,
        required=True,
        widget=forms.Select(attrs={"class":"required"}),
        help_text="Please select the category that best describes this resource")

    description = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class":"required"}),
        help_text="Please provide a short description of this resource.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_form_control_class()

        self.fields["uploaded_file"].required=True #either provide file or url
        self.fields["uploaded_file"].widget.attrs = {"class":"required"}

    def before_save(self, upload):
        upload.publish_status = "SUBMISSION"
        super().before_save(upload)

    class Meta:
        model = Upload
        fields = ["content", "resource_class", "description", "uploaded_file"]
        labels = {
            "resource_class":"Resource Type"
        }


UPLOAD_TYPE_FORMS["PAS_INQUIRY"] = UploadResearchMaterialForm

class ReviewInlineForm(forms.ModelForm):

    def has_changed(self):
        """
        Necesarry to always force save the Reviews, just in case a time needs to be updated
        """
        return True

    class Meta:
        labels = {
            "role":"Assigned to"
        }



