from django.contrib import admin

from .models import Question, Category, Period, Answer
from .forms import SubmissionCategoryForm


class PeriodInline(admin.TabularInline):
    model = Period
    extra = 0
    min_num = 1
    ordering = ("end_time", "begin_time", "title")

    can_delete = False
    fields = ("title", "begin_time", "end_time", "status")


class QuestionAdmin(admin.ModelAdmin):
    model = Question
    list_display = ["title", "code", "question_type",]
    fields = ('code', 'title', 'status', 'description', 'question_type', 'help_text', 'required', ('words_min', 'words_max'), "sort_number")

admin.site.register(Question, QuestionAdmin)


class SubmissionAnswerInline(admin.StackedInline):
    model = Answer
    extra = 0
    fields = ("question", "text")
    readonly_fields = ['published_by']
    questions_codes = []

    def get_questions(self, queryset):
        if self.question_codes:
            return queryset.filter(categories__code__in=self.question_codes).distinct("id")
        else:
            return queryset

    def formfield_for_foreignkey(self, db_field, *args, **kwargs):
        field = super().formfield_for_foreignkey(db_field, *args, **kwargs)
        if db_field.name == "question":
            field.queryset = self.get_questions(field.queryset)
        return field


class CategoryAdmin(admin.ModelAdmin):
    model = Category
    form = SubmissionCategoryForm

    filter_horizontal = ("questions", "upload_types")

    list_display = ["id", "title", "content_type", "status"]
    list_filter = ["content_type"]
    inlines = [PeriodInline]

    raw_id_fields = ["product_master"]
    autocomplete_lookup_fields = ["product_master"]

admin.site.register(Category, CategoryAdmin)


class PeriodAdmin(admin.ModelAdmin):
	model = Period

	list_display = ["id", "title", "category", "begin_time", "end_time"]
	list_display_links = ["id", "title"]
	list_filter = ["category"]

	fields = (('code', 'status'), 'title', "category", ('begin_time', 'end_time'), 'description')
	
admin.site.register(Period, PeriodAdmin)


class SubmissionCategoryFilter(admin.SimpleListFilter):
    """
    List filter for filtering by submission category,
    Inherit from this for submission_catgegory filters because it is easy to 
    override which categories you can filter by
    """
    title = "Submission Category"
    parameter_name = "submission_category"

    def get_submission_category_choices(self):
        return Category.objects.all()

    def lookups(self, request, model_admin):
        lookup_list = []
        for category in self.get_submission_category_choices():
            lookup_list.append((category.id, category.title))
        return lookup_list

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(submission_category_id=self.value())


