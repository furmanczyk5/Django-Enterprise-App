import os
import re

from django import forms
from django.db.models import Prefetch

from uploads.models import Upload,  UploadType


class FileUploadBaseForm(forms.ModelForm):
    """
    Base form for uploading files based on upload type
    NOTE: Make sure to initialize content!
    """
    upload_type_code = "" # need to set this, maybe have a default type though
    upload_field_name = "uploaded_file" # to account for both FileUpload and ImageUpload
    is_final = False

    def __init__(self, *args, **kwargs):
        self.is_final = kwargs.pop("is_final", False)
        super().__init__(*args, **kwargs)
        self.fields[self.upload_field_name].required = True
        if self.fields.get("content"):
            self.fields["content"].widget = forms.HiddenInput()

    def add_form_control_class(self):
        """
        adds the form-control class to all initialized fields in the form
        """
        for field in self.fields:
            class_attr = self.fields[field].widget.attrs.get("class", '')
            widget = self.fields[field].widget
            if not isinstance(widget, forms.FileInput ) and not re.search(r'\bform-control\b', class_attr):
                self.fields[field].widget.attrs["class"] = "form-control " + class_attr

    def save(self, commit=True):
        self.instance = upload = super().save(commit=False)
        self.before_save(upload)
        upload.upload_type = self.upload_type
        if commit:
            upload.save()
        return upload

    def before_save(self, upload):
        pass

    def clean(self):

        cleaned_data = super().clean()

        self.upload_type = UploadType.objects.filter(code=self.upload_type_code).prefetch_related(
                Prefetch("uploads", queryset=self.Meta.model.objects.filter(content=cleaned_data.get("content")), to_attr="the_uploads"),
                "allowed_types"
            ).first()

        # restrict by max number if specified
        if self.upload_type.allowed_max is not None and self.upload_type.allowed_max <= len(self.upload_type.the_uploads):
            self.add_error(None, "You cannot submit more than %s uploads for this section" % self.upload_type.allowed_max)

        # restrict by size if specified
        uploaded_file = cleaned_data.get(self.upload_field_name, None)
        if uploaded_file is not None:
            max_size_kb = self.upload_type.max_file_size
            if max_size_kb is not None:
                max_size = max_size_kb*1024 #stored as kb?
                if uploaded_file._size > max_size:
                    self.add_error(self.upload_field_name, "You cannot submit files larger than %s KB for this section" % max_size_kb)
            
            # restrict by file_types allowed
            allowed_extensions = [".%s" % ft.extension.strip(".").lower() for ft in self.upload_type.allowed_types.all()]
            root, ext = os.path.splitext(uploaded_file.name)
            if ext.lower() not in allowed_extensions:
                self.add_error(self.upload_field_name, "You cannot submit %s files for this section" % ext)

        return cleaned_data

    class Meta:
        model = Upload
        fields = ["uploaded_file", "content"]


class ImageUploadBaseForm(FileUploadBaseForm):

    upload_field_name = "image_file"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = Upload
        fields = ["title", "image_file", "content"]


class TestUploadTypeOneForm(FileUploadBaseForm):

    upload_type_code = "TEST_UPLOAD_TYPE_ONE"

    class Meta:
        model = Upload
        fields = ["title", "uploaded_file", "content", "copyright_email"]


class TestUploadTypeTwoForm(FileUploadBaseForm):

    upload_type_code = "TEST_UPLOAD_TYPE_TWO"

    class Meta:
        model = Upload
        fields = ["title", "uploaded_file", "content", "resource_class"]
    

UPLOAD_TYPE_FORMS = {   
    "TEST_UPLOAD_TYPE_ONE":TestUploadTypeOneForm,
    "TEST_UPLOAD_TYPE_TWO":TestUploadTypeTwoForm 
}
