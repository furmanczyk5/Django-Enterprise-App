from bs4 import BeautifulSoup

from django import forms

from content.models import Content
from content.forms import StateCountryModelFormMixin, SearchFilterForm
from submissions.forms import SubmissionBaseForm, SubmissionVerificationForm

from .models import Job


class JobSubmissionTypeForm(SubmissionBaseForm):
    """
    Form for creating or updating jobs
    """

    submission_category_code = "JOB"

    def __init__(self, *args, **kwargs):

        product_code = kwargs.pop("product_code")
        category_code = kwargs.pop("category_code")

        super().__init__(*args, **kwargs)

        # job_product = Product.objects.filter(code=product_code, content__publish_status="PUBLISHED").first()

        job_content = Content.objects.select_related("product").filter(product__code=product_code, publish_status="PUBLISHED").first()

        JOB_TYPES_WITH_PRICES = []
        job_types_filtered = job_content.product.prices.all().filter(status='A').order_by("-price")

        for job in job_types_filtered:

            # these should be applied to the product price title. commenting out for now, but be aware.
            # if job.code == "INTERN":
            #     job.title = job.title + "(temporary position; no experience required)"
            # if job.code == "ENTRY_LEVEL":
            #     job.title = job.title + "(zero to one year of experience; not AICP)"
            # if job.code == "PROFESSIONAL_2_WEEKS":
            #     job.title = job.title + "(various levels of experience)"
            # if job.code == "PROFESSIONAL_4_WEEKS":
            #     job.title = job.title + "(various levels of experience)"

            JOB_TYPES_WITH_PRICES.append((job.code, job.title + ": $" + str(job.price)))

        self.fields['title'] = forms.CharField(label="Job Title")
        self.fields['job_type'] = forms.ChoiceField(choices=JOB_TYPES_WITH_PRICES, widget=forms.RadioSelect(), required=True, label="Ad Type")

        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    def presave(self):
        if self.instance.status != "X":
            self.instance.status = "N"

    class Meta:
        model = Job
        fields = ["title", "job_type"]


class JobSubmissionDetailsForm(StateCountryModelFormMixin, SubmissionBaseForm):
    """
    Form for creating or updating jobs
    """
    submission_category_code = "JOB"

    tag_type_choices = [
        {"code": "JOB_EXPERIENCE_LEVEL", "required": True},
        {"code": "JOB_CATEGORY", "required": True},
        {"code": "AICP_LEVEL", "required": True}
    ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # if self.instance.job_type in ("ENTRY_LEVEL", "INTERN") and {"code":"AICP_LEVEL", "required":True} in self.tag_type_choices: #intern and entry level test
        #     self.tag_type_choices.remove({"code":"AICP_LEVEL", "required":True}) #remove aicp tag type

        self.init_state_country_fields(
            state_required=self.is_strict,
            country_required=self.is_strict
        )

        # Re-initialize these fields (prefixed with "contact_us_")
        # for the Contact Us section of the form
        self.init_state_country_fields(
            prefix="contact_us_",
            state_required=self.is_strict,
            country_required=self.is_strict
        )

        self.fields['title'] = forms.CharField(label="Job Title")
        self.fields['company'] = forms.CharField(label="Company/Agency")
        self.fields['city'] = forms.CharField(label="City")
        self.fields['text'] = forms.CharField(
            label="Job Description",
            required=True,
            widget=forms.Textarea()
        )

        self.fields['salary_range'] = forms.CharField(
            label="Salary Range",
            required=False,
            widget=forms.TextInput(attrs={'placeholder': 'optional'})
        )

        self.fields["resource_url"] = forms.CharField(
            label="Website URL",
            required=False,
            widget=forms.TextInput(attrs={'placeholder': 'optional.  ex: http://www.example.com'})
        )

        self.fields["editorial_comments"] = forms.CharField(
            label="How to Apply",
            required=False,
            widget=forms.TextInput(attrs={'placeholder': 'URL or email for submission'})
        )

        self.fields["display_contact_info"] = forms.BooleanField(
            label="Display contact name on ad",
            required=False
        )

        self.fields['contact_us_first_name'] = forms.CharField(
            label="First Name",
            required=False,
            widget=forms.TextInput(attrs={'placeholder': 'optional'})
        )
        self.fields['contact_us_last_name'] = forms.CharField(
            label="Last Name",
            required=False,
            widget=forms.TextInput(attrs={'placeholder': 'optional'})
        )
        self.fields['contact_us_address1'] = forms.CharField(
            label="Address 1",
            required=False,
            widget=forms.TextInput(attrs={'placeholder': 'optional'})
        )
        self.fields['contact_us_address2'] = forms.CharField(
            label="Address 2",
            required=False,
            widget=forms.TextInput(attrs={'placeholder': 'optional'})
        )
        self.fields['contact_us_city'] = forms.CharField(
            label="City",
            required=False,
            widget=forms.TextInput(attrs={'placeholder': 'optional'})
        )

        # self.fields['contact_us_state'] = forms.CharField(label="State", required=False)
        # self.fields['contact_us_country'] = forms.CharField(label="Country", required=False)

        self.fields['contact_us_zip_code'] = forms.CharField(
            label="Zip Code",
            required=False,
            widget=forms.TextInput(attrs={'placeholder': 'optional'})
        )

        self.fields['contact_us_phone'] = forms.CharField(
            label="Phone",
            required=False,
            widget=forms.TextInput(attrs={'placeholder': 'optional'})
        )
        self.fields['contact_us_email'] = forms.CharField(
            label="Email",
            required=False,
            widget=forms.TextInput(attrs={'placeholder': 'optional'})
        )

        self.fields["state"].label = "State/Province"
        self.fields['contact_us_state'].label = "State/Province"
        self.fields['contact_us_state'].help_text = "optional"
        self.fields['contact_us_state'].required = False

        self.fields['contact_us_country'].label = "Country"
        self.fields['contact_us_country'].help_text = "optional"
        self.fields['contact_us_country'].required = False

        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

        self.fields['country'].widget.attrs['class'] = 'form-control selectchain'
        self.fields['contact_us_country'].widget.attrs['class'] = 'form-control selectchain'

    def clean(self):
        cleaned_data = super().clean()

        description = cleaned_data.get("text", "")
        stripped_desc = BeautifulSoup(description, 'html.parser').get_text()
        tokens = stripped_desc.split()
        word_count = len(tokens)

        if word_count > 1000:
            self.add_error("text", "Please limit job description to 1000 words or less.")

        return cleaned_data

    def presave(self):
        # what is this?
        if self.instance.status != "X" and self.instance.status != "P":
            self.instance.status = "N"

    def save(self, *args, **kwargs):

        content = super().save(*args, **kwargs)

        return content

    class Meta:
        model = Job
        fields = ["title", "company", "city", "state", "text", "resource_url",
                  "editorial_comments", "salary_range", "contact_us_first_name",
                  "contact_us_last_name", "contact_us_email", "contact_us_phone",
                  "contact_us_address1", "contact_us_address2", "contact_us_city",
                  "contact_us_state", "contact_us_zip_code", "contact_us_country",
                  "display_contact_info", "country"]


class JobSubmissionDetailsNoAICPForm(JobSubmissionDetailsForm):
    """
    Form for creating or updating jobs, no AICP_LEVEL required in tag_type_choices
    """

    tag_type_choices = [
        {"code": "JOB_EXPERIENCE_LEVEL", "required": True},
        {"code": "JOB_CATEGORY", "required": True}
    ]


class JobSubmissionReviewForm(SubmissionVerificationForm):

    submitted_status = "P"

    submission_verified = forms.BooleanField(label="Verify Entry", widget=forms.CheckboxInput(), required=True, initial=False,
        help_text="""I verify that the information submitted in this form is complete and accurate to the best of my knowledge.""")

    class Meta:
        model = Job
        fields = ["submission_verified"]


class JobSearchFilterForm(SearchFilterForm):

    sort_choices = (
        ("sort_time desc", "Date Posted"),
        ("title_string asc", "Title (A to Z)"),
        ("title_string desc", "Title (Z to A)"),
        ("relevance", "Relevance"),
    )

    # should have better way to set default sort value
    def get_sort(self):
        sort_field = self.query_params.get("sort", None)
        keyword = self.query_params["keyword"]

        if not sort_field:
            self.data["sort"] = "sort_time desc"
        elif sort_field == "relevance":
            self.query_params["sort"] = "relevance"
            self.data["sort"] = None

        # print(self.data.get("sort", None))
        return self.data.get("sort", None)

