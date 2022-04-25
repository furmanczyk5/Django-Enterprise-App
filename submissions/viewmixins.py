import os

from django.shortcuts import redirect
from django.http import Http404
from django.contrib import messages
from django.db.models import Prefetch

from uploads.models import UploadType, Upload
from .models import Category


class SubmissionMixin(object):
    """
    Mixin defining methods that are common to most submission pages
    !REQUIREMENTS: View needs either self.modelClass or self.formClass defined, where self.formClass is a ModelForm
    """
    apply_restrictions = True # by default apply these restrictions
    default_publish_status = "SUBMISSION" # by default, the publish_status to save and query content record with

    def set_content(self, request, *args, **kwargs):

        if not getattr(self, "content", None):
            master_id = kwargs.pop("master_id", None)
            if master_id is not None:
                self.modelClass = self.modelClass if hasattr(self, "modelClass") else self.form_class.Meta.model
                self.content = self.query_content(master_id).first()
                if not self.content:
                    Http404("Submission Record not Found")
            else:
                self.content = None

    def query_content(self, master_id):
        """
        Hook for tweaking the content query
        Great for select_related or prefetch_related
        """
        query = self.modelClass.objects.filter(
            master__id=master_id, publish_status=self.default_publish_status
        ).select_related(
            "submission_category"
        )
        return query

    def set_submission_category(self, request, *args, **kwargs):

        if not hasattr(self, "submission_category"):

            if self.content and self.content.submission_category:
                #  1. check on content, content should not be changing categories
                self.submission_category = self.content.submission_category
            elif self.form_class and self.form_class.submission_category_code:
                #  2. check form, form is a good place to define
                self.submission_category = Category.objects.select_related("product_master__content_live__product").get(code=self.form_class.submission_category_code)
            elif self.submission_category_code:
                #  3. check self       (for code)
                self.submission_category = Category.objects.select_related("product_master").get(code=self.submission_category_code)
            elif request.GET.get("submission_category_code", None):
                #  4. check querystring (for code)
                self.submission_category = Category.objects.select_related("product_master").get(code=request.GET.get("submission_category_code"))

        self.submission_category_code = self.submission_category.code
        return self.submission_category

    def setup(self, request, *args, **kwargs):
        """hook for doing additional setup for both get and post requests"""
        pass

    def restrict(self, request, *args, **kwargs):
        """
        Similar to login authentication, but restrict is for things unrelated to user
        """
        if self.apply_restrictions and not self.submission_category.is_open():
            messages.info(request, "The period to enter submissions for \"%s\" is over." % self.submission_category)
            return redirect(self.home_url) # I think this is defined for everything
        else:
            return None

    def dispatch(self, request, *args, **kwargs):
        self.set_content(request, *args, **kwargs) # don't need to set_content on views that inherit from this class
        self.set_submission_category(request, *args, **kwargs)
        self.setup(request, *args, **kwargs)
        restriction_response = self.restrict(request, *args, **kwargs)
        if restriction_response is not None:
            return restriction_response
        else:
            return super().dispatch(request, *args, **kwargs)


class SubmissionUploadsMixin(object):
    """
    Provides useful methods to handle uploads on submissions
    """

    # Content.objects.select_related("uploads").select_related("submission_category").prefetch_related("submission_category__upload_types").get()

    def set_upload_types(self):
        if not hasattr(self,"upload_types"):
            self.upload_types = UploadType.objects.filter(submission_categories=self.content.submission_category).prefetch_related(
                    Prefetch("uploads", queryset=Upload.objects.filter(content=self.content), to_attr="the_uploads")
                )

    def upload_types_are_valid(self):
        """
        returns true if all uploads are valid
        Assumes the content record already exists
        """
        self.set_upload_types()
        are_valid = True #assume they are valid
        for upload_type in self.upload_types:
            max_file_size   = (upload_type.max_file_size or 1000000)*1024 # surly nothing is that big
            allowed_min     = upload_type.allowed_min or 0
            allowed_max     = upload_type.allowed_max or 1000 # surly nothing has that many uploads
            allowed_extensions = [".%s" % ft.extension.strip(".").lower() for ft in upload_type.allowed_types.all()] # this should have at least one
            number_of_uploads = len(upload_type.the_uploads)
            upload_type.the_errors = []

            if number_of_uploads > allowed_max:
                are_valid = False
                upload_type.the_errors.append("You cannot submit more than %s uploads for this section" % allowed_max)
            elif number_of_uploads < allowed_min:
                are_valid = False
                upload_type.the_errors.append("You cannot submit less than %s uploads for this section" % allowed_min)

            for upload in upload_type.the_uploads:
                upload.the_errors = []
                file_upload = upload.get_file()
                if file_upload:
                    if file_upload.size > max_file_size:
                        are_valid = False
                        upload.the_errors.append("Upload %s is larget than the max file size (%s) for this section. Replace this with a valid upload and try again." % (upload, max_file_size))
                    root, ext = os.path.splitext(file_upload.name)
                    if ext.lower() not in allowed_extensions:
                        are_valid = False
                        upload.the_errors.append("Upload %s has an invalid file extension (%s) for this section. Replace this upload with a valid file type for this section. %w" % (upload, ext, allowed_extensions))
        return are_valid







