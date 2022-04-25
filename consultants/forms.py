import re

from django import forms
from django.core.exceptions import ValidationError

from content.forms import StateCountryModelFormMixin, SearchFilterForm
from content.models import Tag, TagType
from content.widgets import YearMonthDaySelectorWidget
from myapa.models.contact_tag_type import ContactTagType
from myapa.models.profile import OrganizationProfile
from submissions.forms import SubmissionBaseForm, SubmissionVerificationForm
from .models import Consultant, RFP, RFP_TYPES, BranchOffice
from .widgets import NewTabClearableFileInput


def max_num_tags(list):
    if len(list) > 5:
        raise ValidationError(
            "Please limit your choices to a maximum of five firm specialties.")


class BranchOfficeForm(StateCountryModelFormMixin, forms.ModelForm):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.init_state_country_fields(state_required=True, country_required=True)
        self.fields['address1'].required = True
        self.fields['city'].required = True
        self.fields['zip_code'].required = True
        self.fields['phone'].required = True
        self.fields["website"].widget.attrs["placeholder"] = "Optional, ex: https://www.planning.org"
        self.fields["email"].widget.attrs["placeholder"] = "Optional"
        self.fields["cell_phone"].widget.attrs["placeholder"] = "Optional"
        self.fields["address2"].widget.attrs["placeholder"] = "Optional"

    class Meta:
        model = BranchOffice
        fields = ["email", "phone", "cell_phone", "website",
                  "user_address_num", "address1", "address2", "city", "state",
                  "zip_code", "country"]
        labels = {
            "parent_organization": "Headquarters",
        }
        widgets = {
            'website': forms.TextInput(attrs={'size': 80})
        }


# make a form for each model, combine them using view/template?
class OrganizationProfileForm(StateCountryModelFormMixin, forms.ModelForm):

    image_file = forms.ImageField(
        required=False,
        widget=NewTabClearableFileInput())

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        if self.instance and self.instance.image:
            initial_image_file = self.instance.image.image_file
        else:
            initial_image_file = None

        self.fields["image_file"].initial = initial_image_file
        # self.fields['contact'].required = False
        self.fields["date_founded"].widget.attrs = {
            "class": "planning-datetime-widget",
            "data-show-time": "false"}
        self.fields["date_founded"].required = True
        self.fields["principals"].widget.attrs["placeholder"] = "Optional"
        max_val = 1000000
        err_message = {
            'max_value':
                'Number must be less than or equal to ' + str(int(max_val))
        }

        self.fields["number_of_staff"] = forms.IntegerField(
            initial=0,
            min_value=0,
            max_value=1000000,
            error_messages=err_message,
            required=True,
            widget=forms.TextInput(attrs={"placeholder":"Enter a number", "size":20,}),
        )

    def clean(self):

        cleaned_data = super().clean()

        return cleaned_data

    class Meta:
        model = OrganizationProfile
        fields = [
            # "contact", 
            "principals", "number_of_staff", "number_of_planners",
            "number_of_aicp_members", "date_founded",   
            ]
        labels = {
            "date_founded": "Date Firm Was Founded",
            "number_of_staff": "Total Number of Staff",
            "number_of_planners": "Number of Professional Planners on Staff",
            "number_of_aicp_members": "Number of AICP Members on Staff"
        }
        widgets = {
            'principals': forms.TextInput(attrs={'size': 80}),
            'date_founded' : YearMonthDaySelectorWidget(include_day=False, include_month=False),
            "number_of_staff": forms.TextInput(attrs={'size': 20}),
            "number_of_planners": forms.TextInput(attrs={'size': 20, "placeholder":"Optional", }),
            "number_of_aicp_members": forms.TextInput(attrs={'size': 20, "placeholder":"Optional",}),            
            }


class ConsultantForm(StateCountryModelFormMixin, forms.ModelForm):
    # NOTE... assumes that users only select one specialization (may change
        # this in the future)
    specialty_tag_ids = forms.MultipleChoiceField(
        label="Firm Specialty (optional)",
        help_text="Please limit choices to no more than five.",
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        validators=[max_num_tags],
    )

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        specialty_tags_qs = Tag.objects.filter(tag_type__code="JOB_CATEGORY")
        tag_list = [ (t.id, t.title) for t in specialty_tags_qs ]
        # tag_list.insert(0, (-1, "-------"))
        self.fields["specialty_tag_ids"].choices = tag_list

        self.instance = kwargs.get("instance", None)
        org_id = kwargs.get("org_id")
        self.consultant = Consultant.objects.filter(id=org_id).first() 
        self.init_specialty_tag()

        self.fields['company'].required = True
        self.fields['bio'] = forms.CharField(required=False, label="Short Description of Your Firm", widget=forms.Textarea(attrs={"placeholder":"This short description will only appear in search results.", "data-wysiwyg":True, "class":"wordcounter"}))
        self.fields['about_me'] = forms.CharField(required=True, label="Main Description of Your Firm", widget=forms.Textarea(attrs={"placeholder":"Main Description of Your Firm", "class":"wordcounter"}))
        self.fields["personal_url"].required = False
        self.fields["address1"].required = True
        self.fields["address2"].required = False
        self.fields["city"].required = True
        # self.fields["state"].required = True
        self.fields["zip_code"].required = True
        # self.fields["country"].required = True
        self.fields["phone"].required = True
        self.fields["email"].required = True
        # self.fields["state"].help_text = "Optional"

        # self.fields["deadline"].widget.attrs = {"class":"planning-datetime-widget", "data-show-time":"false"}
        self.fields["personal_url"].widget.attrs["placeholder"] = "Optional, ex: https://www.planning.org"

        self.init_state_country_fields(state_required=True, country_required=True)

    def init_specialty_tag(self):

        try:
            tag_type_specialty = TagType.objects.get(code="JOB_CATEGORY")
            contact_tag_type_specialty = ContactTagType.objects.get(contact=self.instance, tag_type=tag_type_specialty)
            contact_tag_type_specialty_tags = contact_tag_type_specialty.tags.all()
            tag_list = []
            for tag in contact_tag_type_specialty_tags:
                tag_list.append(tag.id)
            self.fields["specialty_tag_ids"].initial = tag_list
        except:
            self.fields["specialty_tag_ids"].initial = None

    def clean(self):

        cleaned_data = super().clean()

        MAX_WORDS_BIO = 40
        MAX_WORDS_ABOUT = 250
        the_bio = self.cleaned_data.get("bio", "")
        the_about_me = self.cleaned_data.get("about_me", "")
        bio_word_count = len(re.findall(r'\S+', the_bio))
        about_word_count = len(re.findall(r'\S+', the_about_me))
        bio_label = self.fields["bio"].label
        about_label = self.fields["about_me"].label

        if  bio_word_count > MAX_WORDS_BIO:
            self.add_error("bio", 'Please keep the "%s" text to %s words or less.' % (bio_label, MAX_WORDS_BIO))

        if  about_word_count > MAX_WORDS_ABOUT:
            self.add_error("about_me", 'Please keep the "%s" text to %s words or less.' % (about_label, MAX_WORDS_ABOUT))

        return cleaned_data

    class Meta:
        model = Consultant
        fields = ["company", "user_address_num", "address1", "address2", "city", "state", "zip_code",
            "country", "phone", "email", "personal_url", "about_me", "bio", # "tag_types",
            ]
        labels = dict(company="Company Name",  # tag_types="Areas of Expertise",
            email="Main Office Email Address", personal_url="Firm's Website Address", phone="Main Office Phone")
        widgets = { 'company': forms.TextInput(attrs={'size': 80}),
                    # 'parent_organization': forms.TextInput(attrs={'size': 80}),
                    'personal_url': forms.TextInput(attrs={'size': 80}),
                    'address1': forms.TextInput(attrs={'size': 80}),
                    'address2': forms.TextInput(attrs={'size': 80, "placeholder":"Optional",})}


class RFPSubmissionEditForm(StateCountryModelFormMixin, SubmissionBaseForm):

    submission_category_code = "RFP"

    rfp_type = forms.ChoiceField(label="Request Type", choices=RFP_TYPES, required=True, initial="RFP")

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['text'] = forms.CharField(required=self.is_strict, label="General Description", widget=forms.Textarea(attrs={"data-wysiwyg":True, "class":"wordcounter"}))
        self.fields['description'] = forms.CharField(required=self.is_strict, label="Short Description", widget=forms.Textarea(attrs={"placeholder":"less than 40 words", "class":"wordcounter"}))

        self.fields["title"].required = True
        self.fields["company"].required = self.is_strict
        self.fields["city"].required = self.is_strict
        self.fields["deadline"].required = self.is_strict
        self.fields["email"].required = self.is_strict
        self.fields["description"].required = self.is_strict
        self.fields["website"].required = False

        self.fields["deadline"].widget.attrs = {"class":"planning-datetime-widget", "data-show-time":"false"}
        self.fields["website"].widget.attrs["placeholder"] = "Optional, ex: https://www.planning.org"

        self.init_state_country_fields(state_required=self.is_strict, country_required=self.is_strict)
        self.add_form_control_class()

    def clean_text(self):
        WORDS_MAX = 2000
        the_text = self.cleaned_data.get("text", "")
        word_count = len(re.findall(r'\S+', the_text))
        if self.is_strict and len(re.findall(r'\S+', the_text)) > WORDS_MAX:
            raise forms.ValidationError("Your response must be less than {WORDS_MAX} words. You have {word_count} words.".format(WORDS_MAX=WORDS_MAX, word_count=word_count))
        return the_text

    def clean_description(self):
        WORDS_MAX = 40
        the_text = self.cleaned_data.get("description", "")
        word_count = len(re.findall(r'\S+', the_text))
        if self.is_strict and len(re.findall(r'\S+', the_text)) > WORDS_MAX:
            raise forms.ValidationError("Your response must be less than {WORDS_MAX} words. You have {word_count} words.".format(WORDS_MAX=WORDS_MAX, word_count=word_count))
        return the_text

    class Meta:
        model = RFP
        fields = ["rfp_type", "title", "company", "city", "state", 
            "country", "deadline", "email", "website", "description", "text"]
        labels = dict(company="Municipality, Business or Organization Name", description="Short Description", state="State/Province", 
            email="Contact Email", deadline="Submittal Deadline")


class RFPSubmissionVerificationForm(SubmissionVerificationForm):

    submitted_status = "P"

    class Meta:
        model = RFP
        fields = ["submission_verified"]
        labels = dict(submission_verified="Verify Entry")


class RFPSearchFilterForm(SearchFilterForm):
    sort_choices = (
        ("sort_time desc, title asc", "Date posted"),
        ("title_string asc", "Title (A to Z)"),
        ("title_string desc", "Title (Z to A)"),
        ("end_time asc, title asc", "Deadline"),
        ("relevance", "Relevance"),
    )