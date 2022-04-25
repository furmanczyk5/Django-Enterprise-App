from django import forms
from django.db.models import Max, Min
from django.utils import timezone

from cm.models import Period as CMPeriod
from imis.models import Name
from myapa.models.contact import Contact
from myapa.models.contact_role import ContactRole


class MergeContactRolesForm(forms.Form):
    """
    When for merging anonymous records in to record with an imis ID,
    the giver will give all of their contact roles to the receiver

    CAREFUL, YOU SHOULD TO DO PROPER CHECKS AND USER CONFIRMATION BEFORE SAVING
    """
    contact_giver_id = forms.CharField(widget=forms.HiddenInput(), required=True)
    contact_receiver_id = forms.CharField(widget=forms.HiddenInput(), required=True)
    confirm_merge = forms.BooleanField(label='Merge Record into Your APA account?', initial=False)

    def save(self, commit=True):

        data = self.cleaned_data

        if data["confirm_merge"]:
            contact_giver_roles = ContactRole.objects.filter(contact__id=data["contact_giver_id"])
            contact_receiver = Contact.objects.get(id=data["contact_receiver_id"])
            contact_giver_roles.update(contact=contact_receiver)

        # Now you can delete the giver contact if you like
        return contact_giver_roles


class ContactBioForm(forms.ModelForm):
    """
    Simple form for updating user's bio
    """
    bio = forms.CharField(required=True, widget=forms.Textarea(attrs={"class":"form-control"}))
    class Meta:
        model = Contact
        fields = ["bio"]


class ContactProfileForm(forms.ModelForm):
    """
    Simple form for collecting and updating basic myapa profile info
    """
    class Meta:
        model = Contact
        fields = ["bio", "about_me", "personal_url", "linkedin_url", "facebook_url", "twitter_url", "instagram_url"]


class ContactRolePermissionsForm(forms.Form):
    """
    Form used for conference proposals, where participants authorize or deny permissions
    """

    permission_av = forms.ChoiceField(widget=forms.RadioSelect, required=True,
        choices=(   ('PERMISSION_AUTHORIZED','Yes, you may record my session.'),
                    ('PERSMISSION_DENIED','No, you may NOT record my session.')     ))

    permission_content = forms.ChoiceField(widget=forms.RadioSelect, required=True,
        choices=(   ('PERMISSION_AUTHORIZED','Yes, include my PowerPoint presentation.'),
                    ('PERSMISSION_DENIED','No, do NOT include my PowerPoint presentation.')     ))


class CreateDjangoUserForm(forms.Form):
    """
    used for registration to create a user/contact record based on an imis ID passed in
    """

    username = forms.CharField(label="User ID", required=True, widget=forms.TextInput())

    def clean_username(self):
        username = self.cleaned_data['username']

        if not Name.objects.filter(id=username).exists():
            raise forms.ValidationError("No record found for the User ID entered.")

        return username


class MergeCheckForm(forms.Form):
    """
    used to provide list of Django/Postgres records associated with an imis ID
    """

    username = forms.CharField(label="User ID", required=True, widget=forms.TextInput())

    def clean_username(self):
        username = self.cleaned_data['username']

        if not Name.objects.filter(id=username).exists():
            raise forms.ValidationError("No iMIS record found for the User ID entered.")

        return username


class EvalDataDownloadForm(forms.Form):
    """
    Form that allows a user to select a CM Period that bounds the eval data they can download.
    """
    # Use this for partitioning by CM reporting period:
    # cm_period_qs = CMPeriod.objects.values("code", "title").order_by("title")
    # choices = [(v["code"],v["title"]) for v in cm_period_qs]
    # Use this for partitioning by year:
    maxim = CMPeriod.objects.aggregate(Max('begin_time'))
    max_year = getattr(maxim['begin_time__max'], 'year', timezone.now().year)
    minim = CMPeriod.objects.aggregate(Min('begin_time'))
    min_year = getattr(minim['begin_time__min'], 'year', 2007)
    current_year = timezone.now().year
    maxim = current_year if current_year < max_year else max_year
    choices = [(y, y) for y in range(min_year, max_year)]
    cm_period = forms.ChoiceField(choices=choices, label="Year", required=True)
