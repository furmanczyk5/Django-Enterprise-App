from django import forms

from .models import Media, Image


class UploadMediaAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["image_file"].help_text = "Upload an image that will be used as a thumbnail for this media record"
        self.fields["image_file"].label = "Thummbnail File"

        self.fields["resource_url"].help_text = "If this media record does not include an upload (e.g. youtube video), enter it's url here"
        self.fields["url_source"].help_text    = "If you enetered a resource url, where does this resource come from?"

    class Meta:
        model = Media
        exclude = []
        widgets = {
            "text": forms.Textarea(attrs={"class":"ckeditor"})
        }


class ImageMediaAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["image_file"].label = "Image File"
        self.fields["image_file"].help_text = "Upload your image here. A thumbnail will also be generated from the image you upload."

        self.fields["resource_url"].help_text = "If this media record does not include an upload (e.g. youtube video), enter it's url here"
        self.fields["url_source"].help_text = "If you enetered a resource url, where does this resource come from?"

        self.fields["description"] = forms.CharField(
            min_length=1, max_length=400, required=False, widget=forms.Textarea,
            help_text="""A brief description of the content (phrase or 1-2 short sentences).
        For searchable content, this will display in the search results list.""")

    class Meta:
        model = Image
        exclude = []
