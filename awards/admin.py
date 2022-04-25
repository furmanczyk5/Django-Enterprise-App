from django.contrib import admin
from django.db.models import Prefetch

from content.admin import ContentAdmin
from myapa.models.contact_role import ContactRole
from uploads.admin import FileUploadInline, ImageUploadInline
from submissions.admin import CategoryAdmin, SubmissionCategoryFilter, \
    SubmissionAnswerInline

from .models import Submission, SubmissionCategory, JurorAssignment
from .forms import SubmissionCategoryForm, generateUploadTypeAdminInlineFormset


class JurorAssignmentInline(admin.StackedInline):
    model = JurorAssignment
    extra = 0
    classes = ("grp-collapse grp-open",)
    raw_id_fields = ["content", "contact"]
    readonly_fields = ["deadline_time", "review_time", "review_type"]
    autocomplete_lookup_fields = {"fk": ["contact"]}
    filter_horizontal = ["tags"]
    fieldsets = [
        (None, {
            "fields": ("contact",
                       "review_type",
                       "rating_1",
                       "comments",
                       ("deadline_time", "review_time"),
                       "tags"),
        }),
    ]


class LettersOfSupportInline(FileUploadInline):

    verbose_name = "Letter of Support"
    verbose_name_plural = "Letter of Support Uploads"
    readonly_fields = FileUploadInline.readonly_fields + ["upload_type"]
    formset = generateUploadTypeAdminInlineFormset("AWARD_LETTER_OF_SUPPORT")

    def get_queryset(self, request):
        """Alter the queryset to return Letters Of Support uploads"""
        qs = super().get_queryset(request).filter(
            upload_type__code="AWARD_LETTER_OF_SUPPORT")
        return qs


class SupplementalMaterialsInline(FileUploadInline):

    verbose_name = "Supplemental Material"
    verbose_name_plural = "Supplemental Material Uploads"
    readonly_fields = FileUploadInline.readonly_fields + ["upload_type"]
    formset = generateUploadTypeAdminInlineFormset("AWARD_SUPLEMENTAL_MATERIALS")

    def get_queryset(self, request):
        """Alter the queryset to return Supplemental Materials uploads"""
        qs = super().get_queryset(request).filter(upload_type__code="AWARD_SUPLEMENTAL_MATERIALS")
        return qs


class AwardsImagesInline(ImageUploadInline):

    verbose_name = "Image"
    verbose_name_plural = "Image Uploads"
    readonly_fields = ImageUploadInline.readonly_fields + ["upload_type"]
    formset = generateUploadTypeAdminInlineFormset("AWARD_IMAGE")

    def get_queryset(self, request):
        """Alter the queryset to return Image uploads"""
        qs = super().get_queryset(request).filter(upload_type__code="AWARD_IMAGE")
        return qs


class SubmissionCategoryAdmin(CategoryAdmin):
    form = SubmissionCategoryForm
    model = SubmissionCategory

    def get_queryset(self, request):
        return self.model.objects.filter(content_type="AWARD")


class AwardSubmissionCategoryFilter(SubmissionCategoryFilter):

    def get_submission_category_choices(self):
        return SubmissionCategory.objects.all()


class AwardsSubmissionPeriodFilter(admin.SimpleListFilter):

    title = 'Submission Periods'
    parameter_name = 'submission_period'

    def lookups(self, request, model_admin):
        return (
            (None,"Most recent active submission periods"),
            ("ALL","All submission periods for all years")
        )

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() is None or self.value() == "RECENT_ACTIVE":
            awards_submission_cateogies = SubmissionCategory.objects.prefetch_related("periods").filter(status="A")
            latest_active_period_ids = [cat.get_latest_active_period().id for cat in awards_submission_cateogies]
            return queryset.filter(submission_period_id__in=latest_active_period_ids)
        else:
            return queryset


class AwardAnswerInline(SubmissionAnswerInline):

    def get_questions(self, queryset):
        return queryset.filter(categories__content_type="AWARD").distinct("id")


class SubmissionAdmin(ContentAdmin):

    #fields = ("get_master_id", "submission_category", "submission_period", "title", "status", "description", "submission_verified")
    list_display = ["get_master_id", "title", "submission_category",
                    "submission_period", "submission_time", "get_nominator",
                    "get_jurors", "get_average", "is_finalist"]
    list_display_links = []
    search_fields = ["master__id", "title", "contacts__title"]
    readonly_fields = ["get_master_id", "get_jurors", "get_nominator"]
    list_filter = ("status", AwardSubmissionCategoryFilter,
                   AwardsSubmissionPeriodFilter)
    show_sync_harvester = False

    fieldsets = [
        (None, {
            "fields": (
                ("title", "status"),
                ("city", "state", "country"),
                "description",
                ("get_nominator", "submission_time", "is_finalist"),
                ("workflow_status")
            ),
        }),
    ]

    inlines = [AwardAnswerInline, LettersOfSupportInline,
               SupplementalMaterialsInline, AwardsImagesInline,
               JurorAssignmentInline]

    def get_nominator(self, obj):
        try:
            return obj.nominator_roles[0].contact
        except:
            return None
    get_nominator.short_description = "Nominator"
    get_nominator.admin_order_field = "contacts__title"

    def get_jurors(self, obj):
        try:
            return ", ".join([str(j.contact)+" ["+str(j.rating_1)+"]" for j in obj.juror_roles])
        except:
            return None
    get_jurors.short_description = "Jurors [Rating]"

    def get_average(self, obj):
        try:
            total_rating = 0
            num_rating = 0
            for juror in obj.juror_roles:
                total_rating += juror.rating_1
                num_rating += 1
            return float(total_rating/num_rating)

        except:
            return None
    get_average.short_description = "Avg. Rating"

    def get_queryset(self, request):
        return self.model.objects.filter(content_type="AWARD", publish_status="SUBMISSION").prefetch_related(
            Prefetch("contactrole", queryset=ContactRole.objects.filter(role_type="PROPOSER").select_related("contact"), to_attr="nominator_roles"),
            Prefetch("review_assignments", queryset=JurorAssignment.objects.filter(review_type="AWARDS_JURY").select_related("contact"), to_attr="juror_roles")
        ).select_related("submission_category", "submission_period")


class JurorAssignmentAdmin(admin.ModelAdmin):

    list_display = ["contact", "content", "rating_1", "deadline_time", "review_time"]
    raw_id_fields = ["content", "contact"]
    autocomplete_lookup_fields = { "fk" : ["content", "contact"] }
    list_display_links = ["contact", "content"]
    search_fields = []
    readonly_fields = ["deadline_time", "review_time", "review_type"]
    inlines = []
    filter_horizontal = ["tags"]
    fieldsets = [
        (None, {
            "fields":(  "contact",
                        ("content", "review_type"),
                        "rating_1",
                        "comments",
                        ("deadline_time", "review_time"),
                        "tags"
            ),
        }),
    ]

    def get_queryset(self, request):
        return self.model.objects.filter(content__content_type="AWARD")


admin.site.register(SubmissionCategory, SubmissionCategoryAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(JurorAssignment, JurorAssignmentAdmin)
