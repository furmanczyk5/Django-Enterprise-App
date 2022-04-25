from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Prefetch
from django.views.generic import TemplateView, FormView

from content.models import Content
from store.models import ProductCart
from uploads.forms import UPLOAD_TYPE_FORMS
from uploads.models import Upload
from .forms import SubmissionBaseForm, SubmissionVerificationForm
from .models import Category, Question, Answer
from .viewmixins import SubmissionMixin, SubmissionUploadsMixin


class SelectSubmissionCategoryView(TemplateView):
    """
    View for selecting a submission category before starting a submission process
    """
    template_name = "submissions/newtheme/forms/select-category.html"
    title = "Submission Categories"
    next_url = ""
    home_url = ""

    # Specifiy either one or both of the two below
    category_codes = None  # A list of submission category codes
    CategoryModelClass = Category  # A model class that inherites from the Category Model (will use all active categories)

    def get_categories(self, **kwargs):
        filter_kwargs = {"status": "A"}
        if self.category_codes is not None:
            filter_kwargs["code__in"] = self.category_codes
        self.categories = self.CategoryModelClass.objects.prefetch_related("periods").filter(**filter_kwargs).order_by(
            "sort_number", "title")
        self.open_categories = [c for c in self.categories if c.is_open()]
        self.past_categories = [c for c in self.categories if not c.is_open()]

    def get_context_data(self, **kwargs):
        self.get_categories()
        context = super().get_context_data()
        context["title"] = self.title
        context["open_categories"] = self.open_categories
        context["past_categories"] = self.past_categories
        context["next_url"] = self.next_url
        context["home_url"] = self.home_url
        return context


class SubmissionBaseFormView(SubmissionMixin, FormView):
    """
    Base View for submissions view dealing with single submission forms
    """
    title = "Submission"
    template_name = ""  # set this

    home_url = ""
    success_url = ""
    form_class = SubmissionBaseForm  # Always define this when inheriting
    submission_category_code = None  # let the form define this, to get passed value, use after_setup method

    is_strict = True

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        form_kwargs["instance"] = self.content
        return form_kwargs

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if self.form_is_valid(form):
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_is_valid(self, form):
        """hook for determining if form is valid
        Sometimes it's more complex than calling form.is_valid()"""
        return form.is_valid()

    def form_valid(self, form):
        self.content = form.save()
        self.after_save(form)
        return super().form_valid(form)

    def after_save(self, form):
        """hook for doing additional processing after the form is saved"""
        pass

    def get_success_url(self):
        self.success_url = self.success_url.format(master_id=self.content.master_id)
        return super().get_success_url()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["title"] = self.title
        context["content"] = self.content
        context["home_url"] = self.home_url
        return context


class SubmissionEditFormView(SubmissionBaseFormView):
    """
    Base submission view for creating/editing submission records
    """

    template_name = "submissions/newtheme/forms/edit.html"
    is_final = False

    def setup(self, request, *args, **kwargs):
        # implement strict validate only on submit and continue
        if request.POST.get("submitButton", "submit") == "submit":
            self.is_strict = True
        else:
            self.is_strict = False
            self.success_url = self.home_url
        return super().setup(request, *args, **kwargs)

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        form_kwargs["is_strict"] = self.is_strict
        form_kwargs["submission_category_code"] = self.submission_category_code
        return form_kwargs

    def after_save(self, form):
        if self.content.title:
            messages.success(self.request, "Successfully saved submission record for %s!" % self.content.title)
        else:
            messages.success(self.request, "You may proceed with your application.")
        super().after_save(form)


class SubmissionReviewFormView(SubmissionBaseFormView):
    template_name = "submissions/newtheme/forms/review.html"
    form_class = SubmissionVerificationForm
    edit_url = ""
    success_url = ""
    preview_template = None

    purchase_quantity = 1

    def setup(self, request, *args, **kwargs):
        self.requires_checkout = self.get_checkout_required()
        self.submission_questions = Question.objects.filter(
            categories=self.submission_category,
            status="A"
        ).prefetch_related(
            Prefetch("answers", queryset=Answer.objects.filter(content=self.content), to_attr="the_answer")
        ).order_by("sort_number")
        return super().setup(request, *args, **kwargs)

    def query_content(self, master_id):

        query = super().query_content(master_id).prefetch_related(
            "contenttagtype__tags",
        ).select_related(
            "submission_category__product_master__content_live__product"
        )
        return query

    def get_checkout_required(self):
        """
        Returns True if this submission requires payment to submit
        """
        try:
            product_master = getattr(self.submission_category, "product_master", None)
            return product_master and product_master.content_live.product.status == "A"
        except:
            return False

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        form_kwargs["complete_submission"] = not self.requires_checkout
        return form_kwargs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["edit_url"] = self.edit_url.format(master_id=self.content.master_id)
        context["requires_checkout"] = self.requires_checkout
        context["preview_template"] = self.preview_template
        context["submission_questions"] = self.submission_questions
        return context

    def after_save(self, form):
        if self.requires_checkout:
            self.update_cart()
        super().after_save(form)

    def get_success_url(self):
        if self.requires_checkout:
            self.success_url = reverse("store:cart")
        return super().get_success_url()

    def update_cart(self, *args, **kwargs):
        """
        adds/updates necessary cart purchases for checkout
        """
        product_master = self.submission_category.product_master
        provider = kwargs.get("provider", None)

        if product_master is not None:
            product = ProductCart.objects.get(id=product_master.content_live.product.id)
            # hackz 4 dayz - override ProductCart.get_price with a $0 productprice
            # for 1 free CM credit if provider is only buying 1 or less credits
            # https://americanplanning.atlassian.net/browse/DEV-5445
            if kwargs.get('quantity_hack', False):
                product.add_to_cart(
                    contact=self.request.contact,
                    code=kwargs.get("code", None),
                    content_master=self.content.master,
                    quantity=self.purchase_quantity,
                    provider=provider,
                    product_price=kwargs.get('product_price', None)
                )
            else:
                product.add_to_cart(
                    contact=self.request.contact,
                    code=kwargs.get("code", None),
                    content_master=self.content.master,
                    quantity=self.purchase_quantity,
                    provider=provider,
                )


class SubmissionUploadsView(SubmissionMixin, SubmissionUploadsMixin, TemplateView):
    template_name = "submissions/newtheme/forms/uploads.html"
    modelClass = Content  # NEED TO DEFINE THIS TO GET CONTENT
    success_url = ""
    title = "Uploads"

    def get(self, request, *args, **kwargs):

        self.set_upload_types()

        for upload_type in self.upload_types:
            formClass = UPLOAD_TYPE_FORMS[upload_type.code]
            if hasattr(self, "failed_form") and self.failed_form[0] == upload_type.code:
                upload_type.form = self.failed_form[1]
            else:
                upload_type.form = formClass(initial={"content": self.content})

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        if request.POST["submit_button"] == "remove":
            remove_id = request.POST["remove_id"]
            Upload.objects.filter(
                id=remove_id).delete()  # make sure everything gets deleted (the upload, the uploadBase table, the fileupload or imageupload table)
        elif request.POST["submit_button"] in UPLOAD_TYPE_FORMS:
            upload_type_code = request.POST["submit_button"]
            formClass = UPLOAD_TYPE_FORMS[upload_type_code]
            form = formClass(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully uploaded file!")
            else:
                self.failed_form = (upload_type_code, form)
                messages.error(request, "Failed to uploaded file! Make sure all required fields are valid.")

        return self.get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            "upload_types": self.upload_types,
            "success_url": self.success_url.format(master_id=self.content.master_id),
            "home_url": self.home_url,
            "title": self.title,
            "content": self.content,
            "upload_types_are_valid": self.upload_types_are_valid()
        })
        return context


class SubmissionDetailsView(SubmissionMixin, TemplateView):
    answers = None
    tag_types = None
    uploads = None
    contactroles = None
    apply_restrictions = False

    def set_content(self, request, *args, **kwargs):
        super().set_content(request, *args, **kwargs)
        self.answers = self.content.submission_answer.select_related("question")
        self.tag_type_assignments = self.content.contenttagtype.select_related("tag_type").prefetch_related("tags")
        self.uploads = self.content.uploads.select_related("upload_type")
        self.contactroles = self.content.contactrole.select_related("contact")

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["title"] = self.content.title
        context["content"] = self.content
        context["answers"] = self.answers
        context["tag_type_assignments"] = self.tag_type_assignments
        context["uploads"] = self.uploads
        context["contactroles"] = self.contactroles
        return context
