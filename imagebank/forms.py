import re
import datetime

from django import forms

from content.models import TagType, ContentTagType
from content.forms import SearchFilterForm
from content.widgets import YearMonthDaySelectorWidget, \
    SelectMultipleTagsWidget
from myapa.models.contact_role import ContactRole
from submissions.forms import SubmissionBaseForm, SubmissionVerificationForm

from .models import Image


class ImageBankAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["abstract"].label = "Notes"
        self.fields["resource_published_date"].initial = datetime.date.today()
        self.fields["resource_published_date"].label = "Date Uploaded"
        self.fields["copyright_date"].label = "Date Taken"
        self.fields["copyright_statement"].label = "Copyright Statement"
        self.fields["copyright_statement"].initial = "Copyright American Planning Association"

    class Meta:
        model = Image
        exclude = []


class ImageLibrarySearchFilterForm(SearchFilterForm):

    sort_choices = (
        ("copyright_date desc, published_time desc", "Date (newest to oldest)"),
        ("relevance", "Relevance"),
        ("title_string asc", "Title (A to Z)"), 
        ("title_string desc", "Title (Z to A)")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["sort"].initial = self.sort_choices[0]

    def get_sort(self):
        sort_field = self.query_params.get("sort", None)
        keyword = self.query_params["keyword"]

        if (not sort_field and not keyword) or (not sort_field and keyword):
            self.data["sort"] = "copyright_date desc, published_time desc"
        elif not sort_field or sort_field == "relevance":
            self.query_params["sort"] = "relevance"
            self.data["sort"] = None
        return self.data.get("sort", None)


class ImageSubmissionCreateForm(SubmissionBaseForm):

    submission_category_code = "IMAGELIBRARY"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_fields["title"].required = True
        self.fields["title"].help_text = "Choose a brief (3-5 word) title for the image."
        self.fields["submission_verified"].label = "I have read and accept the APA Image Library Terms of Use for Image Uploading."
        self.fields["submission_verified"].required = True
        self.fields["submission_verified"].widget.attrs["required"] = True
        self.add_form_control_class()
        self.fields["image_file"] = forms.FileField(required=True, widget=forms.FileInput(),
            help_text="""Maximum file size is 20 MB. After you choose your image file 
            and click \"Save and Continue,\" the image thumbnail will display on the next page.""")

    def clean_image_file(self):
        max_file_size   = 20*1024*1024 # 20MB
        image_file = self.cleaned_data.get("image_file", None)
        if image_file.size > max_file_size:
            are_valid = False
            raise forms.ValidationError("You cannot upload files larger than 20MB, try uploading a smaller image.")
        return image_file

    class Meta:
        model = Image
        fields = ["title", "submission_verified", "image_file"]

class ImageSubmissionEditForm(SubmissionBaseForm):

    tag_type_choices = [
        {"code":"SEARCH_TOPIC", "required":True, 
        "field":forms.MultipleChoiceField, 
        # "widget":SelectMultipleTagsWidget, 
        "max_tags":3},
        {"code":"IMAGE_COLOR", "required":True},
        {"code":"STATE", "required":False},
        {"code":"IMAGE_NUMBEROFPEOPLE", "required":True},
        {"code":"COMMUNITY_TYPE", "required":True}]

    def __init__(self, *args, **kwargs):
        self.base_fields["title"].required = True
        super().__init__(*args, **kwargs)
        self.init_photographer()

        self.fields["description"].widget.attrs["class"] = "wordcounter"
        
        self.add_form_control_class()

        # self.fields["image_file"] = forms.FileField(
        #     label="Change Image File", 
        #     required=True, 
        #     widget=forms.FileInput(),
        #     help_text="""Skip this step if you do not need to change your image file. 
        #         If you do need to choose a different image, click "Choose File" above, 
        #         select your image, and then click the "Save" button below to save your changes.""")

        self.fields["copyright_statement"].help_text = """
            Include the year that the photo was taken 
            as well as the copyright holder’s name (often the name of the photographer). 
            Suggested format: \"Copyright 2016 Jane Doe.\""""
        self.fields["keywords"].help_text = """
            Enter any important words or concepts that do not appear in the caption. 
            APA Image Library users will not see these words or phrases, 
            but they will be used for keyword searches."""
        self.fields["title"].help_text = "Choose a brief (3-5 word) title for the image."
        self.fields["copyright_date"].help_text = """If you do not choose a year 
            from the drop-down menu, \"Unknown\" will display as the date taken."""
        self.fields["tag_choice_SEARCH_TOPIC"].help_text = "Choose at least 1 but no more than 3 topics that best capture the content of the image. Use the Ctl key (or Command key on a mac) to select multiple."

        self.fields["description"].required = self.is_strict
        self.fields["copyright_statement"].required = self.is_strict
        self.fields["resolution"].required = False

    def save_nonmodel_fields(self):
        """
        Very similar to save_m2m. Call this on the form after calling save with commit=False to process
            data not on the Image model
        NOTE: I made this up because you can't inherit from save_m2m, which is generated method within the save method
        """
        super().save_nonmodel_fields()
        if self.instance:
            self.save_photographer()
            self.save_orientation_tag()

    def init_photographer(self):

        if self.instance:
            photographer_role = ContactRole.objects.filter(content=self.instance, role_type="PHOTOGRAPHER").first()

        self.fields["photographer_first_name"] = forms.CharField(label="First Name", 
            initial=photographer_role.first_name if photographer_role else None, 
            required=self.is_strict)
        self.fields["photographer_last_name"] = forms.CharField(
            label="Last Name", 
            initial=photographer_role.last_name if photographer_role else None, 
            required=self.is_strict)

    def save_photographer(self, *args, **kwargs):
        photographer_first_name = self.cleaned_data.get("photographer_first_name", None)
        photographer_last_name = self.cleaned_data.get("photographer_last_name", None)
        if photographer_first_name or photographer_last_name:
            defaults = dict(
                publish_status="SUBMISSION",
                first_name=photographer_first_name,
                last_name=photographer_last_name
                )
            ContactRole.objects.update_or_create(content=self.instance, role_type="PHOTOGRAPHER", defaults=defaults)
        else:
            ContactRole.objects.filter(content=self.instance, role_type="PHOTOGRAPHER").delete()

    def save_orientation_tag(self, *args, **kwargs):
        """
        Auto generating this tag based on the height and width of the image
            NOTE:   Because image_file field was removed from this step,
                    consider moving this to the first step when image is uploaded,
                    even though other tagging happens in this view
        """
        height = self.instance.image_file.height
        width = self.instance.image_file.width
        orientation_tagtype = TagType.objects.prefetch_related("tags").get(code="IMAGE_ORIENTATION") #1
        orientation_contenttagtype, is_created = ContentTagType.objects.get_or_create(tag_type=orientation_tagtype, content=self.instance) #2
        orientation_contenttagtype.tags.clear()

        if height < width:
            orientation_tag_code = "IMAGE_ORIENTATION_LANDSCAPE"
        elif height > width:
            orientation_tag_code = "IMAGE_ORIENTATION_PORTRAIT"
        else:
            orientation_tag_code = "IMAGE_ORIENTATION_SQUARE"

        orientation_tag = next((t for t in orientation_tagtype.tags.all() if t.code == orientation_tag_code), None)
        orientation_contenttagtype.tags.add(orientation_tag)

    def clean_tag_choice_SEARCH_TOPIC(self):
        # Might be better to build into the 'init_tag_choice_fields' method?
        tags = self.cleaned_data.get("tag_choice_SEARCH_TOPIC", "")
        tags_count = len(tags)
        if tags_count > 3:
            raise forms.ValidationError("You cannot select more than 3 topic tags. You have chosen %s" % tags_count)
        return tags

    def clean_description(self):
        WORDS_MAX = 75
        the_text = self.cleaned_data.get("description", "")
        word_count = len(re.findall(r'\S+', the_text))
        if self.is_strict and word_count > WORDS_MAX:
            raise forms.ValidationError("Your response must be less than {WORDS_MAX} words. You have {word_count} words.".format(WORDS_MAX=WORDS_MAX, word_count=word_count))
        return the_text

    # word count doesn't really work for this field bc it currently does not differentiate comma separated words without spaces
    def clean_keywords(self):
        CHAR_MAX = 300
        the_text = self.cleaned_data.get("keywords", "")
        char_count = len(the_text)
        if self.is_strict and char_count > CHAR_MAX:
            raise forms.ValidationError("Your response must be less than {CHAR_MAX} characters. You have {char_count} characters.".format(CHAR_MAX=CHAR_MAX, char_count=char_count))
        return the_text

    class Meta:
        model = Image
        fields = ["title", "description", "copyright_statement", "copyright_date", "keywords", "resolution"]
        widgets = dict(copyright_date=YearMonthDaySelectorWidget(us_notation=True,include_month=False, include_day=False,attrs={'class': 'form-control'}))
        labels = dict(description="Caption", copyright_date="Date Taken", resolution="Dots Per Inch/Pixels Per Inch")

class ImageSubmissionVerificationForm(SubmissionVerificationForm):

    submitted_status = "P"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["submission_verified"].required = True
        self.fields["submission_verified"].widget = forms.HiddenInput()

    class Meta:
        model = Image
        fields = ["submission_verified"]
        labels = dict(submission_verified="Verify Entry")
