from datetime import datetime, timedelta

from django.contrib import messages
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse_lazy
from django.views.generic import TemplateView, View
from django.db.models import Prefetch
from django.utils import timezone

from content.mail import Mail
from myapa.viewmixins import AuthenticateLoginMixin, \
    AuthenticateContactRoleMixin
from myapa.models.contact_role import ContactRole
from myapa.models.contact import Contact
from submissions.models import Review, Question, Answer
from submissions.views import SelectSubmissionCategoryView, \
    SubmissionEditFormView, SubmissionUploadsView, SubmissionReviewFormView, \
    SubmissionDetailsView
from submissions.viewmixins import SubmissionMixin
from uploads.models import UploadType, Upload

from .models import SubmissionCategory, Submission
from .forms import AwardsSubmissionForm, AwardsSubmissionVerificationForm, \
    JurorReviewForm


class MyNominations(AuthenticateLoginMixin, TemplateView):

    template_name = "awards/newtheme/mynominations.html"

    def get(self, request, *args, **kwargs):

        awards_submission_cateogies = SubmissionCategory.objects.prefetch_related("periods").filter(status="A")
        latest_active_period_ids = [cat.get_latest_active_period().id for cat in awards_submission_cateogies]

        self.nominations = ContactRole.objects.filter(
            contact__user=request.user,
            role_type="PROPOSER",
            content__content_type="AWARD",
            publish_status="SUBMISSION",
            content__submission_period_id__in=latest_active_period_ids
        ).select_related(
            "content__submission__submission_category",
        ).order_by(
            "-content__submission_time", "-content__created_time"
        )

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nominations"] = self.nominations
        return context

class SelectAwardsCategory(AuthenticateLoginMixin, SelectSubmissionCategoryView):
    """
    View to select awards submission category
    """
    template_name = "awards/newtheme/submission-categories.html"
    title = "Select a nomination category to get started"
    CategoryModelClass = SubmissionCategory
    next_url = reverse_lazy("awards:submission_new")
    home_url = reverse_lazy("awards:mynominations")

class AwardsSubmissionEditFormView(AuthenticateContactRoleMixin, SubmissionEditFormView):

    title = "Awards Submission Entry"
    form_class = AwardsSubmissionForm
    template_name = "awards/newtheme/submission-edit.html"
    authenticate_role_type = "PROPOSER"
    home_url = reverse_lazy("awards:mynominations")
    success_url = "/awards/mynominations/submission/{master_id}/uploads/"

    def after_save(self, form):
        ContactRole.objects.update_or_create(contact=self.request.user.contact, content=self.content, role_type="PROPOSER", defaults=dict(publish_status="SUBMISSION"))
        super().after_save(form)


class AwardsSubmissionUploadsView(AuthenticateContactRoleMixin, SubmissionUploadsView):
    authenticate_role_type = "PROPOSER"
    template_name = "awards/newtheme/submission-uploads.html"
    home_url = reverse_lazy("awards:mynominations")

    def setup(self, request, *args, **kwargs):
        self.success_url = reverse_lazy("awards:submission_review", kwargs={"master_id":self.content.master_id})


class AwardsSubmissionReviewFormView(AuthenticateContactRoleMixin, SubmissionReviewFormView):
    title = "Review - Awards Nomination Entry"
    template_name = "awards/newtheme/submission-review.html"
    form_class = AwardsSubmissionVerificationForm
    authenticate_role_type = "PROPOSER"
    home_url = reverse_lazy("awards:mynominations")
    success_url = "/awards/mynominations/submission/{master_id}/complete/"
    edit_url = "/awards/mynominations/submission/{master_id}/update/"
    edit_uploads_url = "/awards/mynominations/submission/{master_id}/uploads/"

    def setup(self, request, *args, **kwargs):
        super().setup(self, request, *args, **kwargs)
        all_uploads = Upload.objects.select_related("upload_type").filter(content=self.content)
        self.uploads = dict(
            letters=[u for u in all_uploads if u.upload_type.code == "AWARD_LETTER_OF_SUPPORT"],
            supporting=[u for u in all_uploads if u.upload_type.code == "AWARD_IMAGE"],
            supplemental=[u for u in all_uploads if u.upload_type.code == "AWARD_SUPLEMENTAL_MATERIALS"]
        )
        self.success_url = self.success_url.format(master_id=self.content.master_id)

    def get_checkout_required(self):
        product_master = getattr(self.submission_category, "product_master", None)
        product = product_master.content_live.product if product_master and product_master.content_live else None
        if product and product.status == "A":
            product_price = product.get_price(contact=self.request.user.contact)
            return product_price and product_price.price
        else:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nominator"] = ContactRole.objects.select_related("contact").filter(content=self.content, role_type="PROPOSER").first().contact
        context["uploads"] = self.uploads
        context["edit_uploads_url"] = self.edit_uploads_url.format(master_id=self.content.master_id)
        return context

class AwardsSubmissionCompletedRedirectView(AuthenticateContactRoleMixin, SubmissionMixin, View):

    pattern_name = "awards:mynominations"
    authenticate_role_type = "PROPOSER"
    modelClass = Submission

    def send_email(self):
        """ a little strange, but doing this to match the context of product email template
                so that this can be used for purchases and free nominations """
        mail_context = {
            'contact':ContactRole.objects.select_related("contact").filter(content=self.content, role_type="PROPOSER").first().contact,
            'content_master':{
                "get_top_version":self.content
            }
        }
        Mail.send('AWARDS_NOMINATION_THANK_YOU', mail_context["contact"].email, dict(purchase=mail_context))

    def get(self, request, *args, **kwargs):
        self.set_content(request)
        self.send_email()
        messages.success(request, "Thank you for your 2016 APA Awards Nomination!")

        return redirect(self.pattern_name)


class AwardsSubmissionPreviewView(AuthenticateContactRoleMixin, TemplateView):
    template_name = "awards/newtheme/submission-details.html"
    authenticate_role_type = "PROPOSER"

    def set_content(self, *args, **kwargs):
        if not hasattr(self, "content"):
            master_id = kwargs.get("master_id")
            nomination = Submission.objects.select_related("submission_category").filter(publish_status="SUBMISSION", master_id=master_id).first()
            self.nomination = self.content = nomination

    def get(self, request, *args, **kwargs):
        all_uploads = Upload.objects.select_related("upload_type").filter(content=self.content)
        self.uploads = dict(
            letters=[u for u in all_uploads if u.upload_type.code == "AWARD_LETTER_OF_SUPPORT"],
            supporting=[u for u in all_uploads if u.upload_type.code == "AWARD_IMAGE"],
            supplemental=[u for u in all_uploads if u.upload_type.code == "AWARD_SUPLEMENTAL_MATERIALS"]
        )

        self.submission_questions = Question.objects.filter(categories=self.content.submission_category, status="A").prefetch_related(
             Prefetch("answers", queryset=Answer.objects.filter(content=self.content), to_attr="the_answer")
        ).order_by("sort_number")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            "nomination":self.nomination,
            "uploads":self.uploads,
            "submission_questions":self.submission_questions
        })
        return context


class JurorMyListView(AuthenticateLoginMixin, View):
    context={}
    template_name="awards/newtheme/jurornominations.html"

    def get(self, request, *args, **kwargs):

        # TO GET LIST OF PROPOSALS FOR REVIEW....

        contact_object = Contact.objects.get(user = request.user)

        filter_string = request.GET.get("filter", None)

        if(contact_object):
            this_year = timezone.now().year
            aug_01_of_last_year = datetime(year=this_year-1, month=8, day=1)
            aug_31_of_this_year = datetime(year=this_year, month=8, day=31)
    
            # TO DO EVENTUALLY... ONLY PULL NOMINATIONS FOR CURRENT PERIOD... ALTHOUGH FOR NOW THIS DATA MAY NOT BE AVAILABLE
            reviews_queryset = Review.objects.filter(
                review_type="AWARDS_JURY", content__content_type="AWARD", content__status="A"
            ).select_related(
                "contact__user", "content__submission__submission_category"
            ).order_by(
                "content__submission_category__title", "content__title", "content__master_id"
            ).filter(
                content__submission_period__end_time__gte=aug_01_of_last_year
            ).filter(
                content__submission_period__end_time__lte=aug_31_of_this_year
            )
            if filter_string == "mine_only":
                reviews = reviews_queryset.filter(content__review_assignments__contact=contact_object)
            elif filter_string == "finalist_only":
                reviews = reviews_queryset.filter(content__submission__is_finalist=True)
            elif filter_string == "nonfinalist_only":
                reviews = reviews_queryset.filter(content__submission__is_finalist=False)
            else:
                reviews = reviews_queryset

            submissions = []
            last_submission_master_id = None
            for review in reviews:
                if review.content.master_id == last_submission_master_id:
                    submissions[-1]["reviews"].append(review)
                    if review.contact == request.user.contact:
                        submissions[-1]["is_reviewer"] = True
                else:
                    last_submission_master_id = review.content.master_id
                    submissions.append(dict(
                        content=review.content.submission,
                        reviews=[review],
                        is_reviewer=review.contact == request.user.contact
                    ))

            self.context["submissions"] = submissions
            self.context["filter_string"] = filter_string

            # get all {Reviewer} objects for this contact, and use select_related to also get associated {content}
            # ... (will need to merge master into this branch to get reviewer model) -- Done
            # (those content records would be set as the proposals to the context)

        return self.render_template(request)

    def render_template(self, request):
        return render(request, self.template_name, self.context)


class AwardDetailsView(AuthenticateLoginMixin, SubmissionDetailsView):
    template_name="awards/newtheme/nomination-details.html" # TO DO.. MAKE A NEW TEMPLATE... USE THE SAME TEMPLATE... INHERIT?

    # TO DO... DEFINE TEMPLATE AND ADD RENDER_TEMPLATE METHOD... LIKE ABOVE.
    # TO DO... ProposalReviewForm class does not exist... need to create it within events/forms.py
    # form should just have the comments, a single rating (1-4) dropdown, and the tag selections as checkboxes
    modelClass = Submission
    # can_have_speakers = False
    context={}

    def setup(self, request, *args, **kwargs):
        self.set_content(request, *args, **kwargs) # TO DO... FIGURE OUT HOW TO MAKE THIS METHOD AVAIBLE... MAY NEED TO INHERIT FROM SOMETHING ELSE
        upload_type_codes = ["AWARD_LETTER_OF_SUPPORT", "AWARD_IMAGE", "AWARD_SUPLEMENTAL_MATERIALS"]
        self.upload_types = UploadType.objects.filter(code__in=upload_type_codes).prefetch_related(
                Prefetch("uploads", queryset=Upload.objects.filter(content=self.content), to_attr="the_uploads")
            )
        return super().setup(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.context["is_proposal"] = True  # is this needed?
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["upload_types"] = self.upload_types
        return context


# TO DO AFTER WE GET THIS WORKING... MOST OF THIS IS GENERIC FOR ALL SUBMISSION REVIEWS... COULD REFACTOR
class AwardJurorDetailsView(AuthenticateLoginMixin, SubmissionDetailsView):#render the other view for new template_
    template_name="awards/newtheme/nomination-details.html"
    # TO DO... DEFINE TEMPLATE AND ADD RENDER_TEMPLATE METHOD... LIKE ABOVE.
    # TO DO... ProposalReviewForm class does not exist... need to create it within events/forms.py
    # form should just have the comments, a single rating (1-4) dropdown, and the tag selections as checkboxes
    modelClass = Submission
    form_class = JurorReviewForm
    can_have_speakers = False
    context = {}

    def setup(self, request, *args, **kwargs):
        self.set_content(request, *args, **kwargs) # TO DO... FIGURE OUT HOW TO MAKE THIS METHOD AVAIBLE... MAY NEED TO INHERIT FROM SOMETHING ELSE
        self.master_id = kwargs.pop("master_id", None)
        try:
            self.review = Review.objects.filter(contact__user__username=self.username, content=self.content)[0]

            self.form_obj = self.form_class(request.POST or None, instance=self.review)
            upload_type_codes = ["AWARD_LETTER_OF_SUPPORT", "AWARD_IMAGE", "AWARD_SUPLEMENTAL_MATERIALS"]
            self.upload_types = UploadType.objects.filter(code__in=upload_type_codes).prefetch_related(
                    Prefetch("uploads", queryset=Upload.objects.filter(content=self.content), to_attr="the_uploads")
                )
        except:
            self.review = None
            self.form_obj = None
            # return messages.error(request,"You have not been assigned this proposal")

        return super().setup(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if self.review is None:
            return render(request, "myapa/newtheme/restricted-access.html", {"message":"<h2>You have not been to assigned this award nomination</h2>"})
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if self.form_obj.is_valid():
            self.form_obj.save()
            messages.success(request, "Successfully updated your review")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["form_obj"] = self.form_obj
        context["is_proposal"] = False
        context["upload_types"] = self.upload_types
        return context
