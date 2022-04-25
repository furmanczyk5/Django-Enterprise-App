from uploads.forms import ImageUploadBaseForm
from uploads.models import ImageUpload
from django import forms
from myapa.models.profile import OrganizationProfile
from myapa.models.proxies import Organization


class OrgLogoForm(ImageUploadBaseForm):
    upload_type_code = "PROFILE_PHOTOS"

    class Meta:
        model = ImageUpload
        fields = ["image_file"]


class EmployerBioForm(forms.ModelForm):

    class Meta:
        model = OrganizationProfile
        fields = ["employer_bio"]


class OrgBioForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(OrgBioForm, self).__init__(*args, **kwargs)
        self.fields['bio'].label = 'Description'

    class Meta:
        model = Organization
        fields = ["bio"]
