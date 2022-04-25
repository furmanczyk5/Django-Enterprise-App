import csv
from io import StringIO
from django.contrib import messages

from django.db import connections

from django.db.models.query import QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from cm.models import Period as CMPeriod, Claim
from comments.models import Comment#, ExtendedEventEvaluation
from myapa.forms.generic import EvalDataDownloadForm
from myapa.views.myorg.authentication import AuthenticateOrganizationAdminMixin
from myapa.models import *

CM_EVAL_QUESTIONS_FULL = {
    "Q1": "Q1: This activity achieved the stated learning outcomes.",
    "Q2": "Q2: This activity increased my knowledge.",
    "Q3": "Q3: I will make a change in the way I practice planning based upon my participation in this activity.",
    "Q4": "Q4: The presenter(s)/subject matter expert(s) delivered the content effectively.",
    "Q5": "Q5: I would endorse this activity as a high-quality learning opportunity.",
    "Q6": "Q6: Provide any additional comments regarding this educational activity:",
    "Q7": "Q7: Would you like to learn more on this topic area?",
    "Q8": "Q8: APA may publish these comments, along with my name, on APA’s website and social media; in APA publications; emails; and elsewhere, to help judge the quality of this education."
    }

CM_EVAL_QUESTIONS_ABBREV = {
    "Q1": "Q1: The activity achieved the stated learning outcomes.",
    "Q2": "Q2: The activity increased my knowledge.",
    "Q3": "Q3: The activity will change my planning practice.",
    "Q4": "Q4: The activity content was delivered effectively.",
    "Q5": "Q5: The activity was high quality.",
    "Q6": "Q6: Additional comments about this activity:",
    "Q7": "Q7: Would you like to learn more about this topic?",
    "Q8": "Q8: APA may publish my name and comments about this activity."
    }

class MyOrganizationEvalDataDownloadView(AuthenticateOrganizationAdminMixin, FormView):
    template_name = "myorg/eval-data-download.html"
    form_class = EvalDataDownloadForm
    success_url = reverse_lazy("myorg")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(dict(
            org=self.organization
        ))
        return context

    def form_valid(self, form):
        # Use this for grouping by CM reporting period:
        # cm_period_code = form.cleaned_data.get("cm_period", '')
        # cmperiod = CMPeriod.objects.get(code=cm_period_code)
        # period_begin_year = cmperiod.begin_time.year
        # period_end_year = cmperiod.end_time.year
        # period_years = (period_begin_year, period_end_year)
        year = form.cleaned_data.get("cm_period", '')
        provider = self.organization
        role_content = ContactRole.objects.filter(contact=provider).values("content")
        # comments = Comment.objects.filter(content__in=role_content,
        #                               content__event__begin_time__year__in=period_years).order_by(
        #     "content__master_id")
        comments = Comment.objects.filter(content__in=role_content,
                                      submitted_time__year=year, is_deleted=False).order_by(
            "content__master_id")
        # claims = Claim.objects.filter(event__in=role_content, log__period=cmperiod).order_by(
        #     "log__period__begin_time")
        # c.log.period.begin_time.year
        claims = Claim.objects.filter(
                    event__in=role_content,
                    submitted_time__year=year, is_deleted=False).order_by(
                    "log__period__begin_time")
        claim_comment_ids = claims.values("comment__id")
        claims_comments = Comment.objects.filter(id__in=claim_comment_ids).order_by(
            "content__master_id")
        merged_comments = comments | claims_comments

        vals = merged_comments.values("id")
        ids_tuple = tuple([d['id'] for d in vals])
        ids_tuple = ids_tuple if ids_tuple else (-1,-2)
        data = self.get_provider_evals(ids_tuple)

        if data:
            return CSVResponse(data, "{} eval_data".format(self.organization.title))
        else:
            messages.warning(self.request, "There is no evaluation data for the CM Period you selected.")
            return HttpResponseRedirect(self.request.META.get('HTTP_REFERER'))


    def get_provider_evals(self, comment_ids):
        """
        Get Activity Evaluation Data for a given Provider with Average ratings
        :return:
        """
        Q1 = CM_EVAL_QUESTIONS_ABBREV["Q1"]
        Q2 = CM_EVAL_QUESTIONS_ABBREV["Q2"]
        Q3 = CM_EVAL_QUESTIONS_ABBREV["Q3"]
        Q4 = CM_EVAL_QUESTIONS_ABBREV["Q4"]
        Q5 = CM_EVAL_QUESTIONS_ABBREV["Q5"]
        Q6 = CM_EVAL_QUESTIONS_ABBREV["Q6"]
        Q7 = CM_EVAL_QUESTIONS_ABBREV["Q7"]
        Q8 = CM_EVAL_QUESTIONS_ABBREV["Q8"]

        query = """
                SELECT cc.master_id as "Course ID", cc.title as "Course Title",
                    DATE(com.submitted_time) as "Submitted On",
                    myc.company as "Reviewer\'s Employer",
                    com.rating as "Rating",
                    ROUND(avg(com.rating) OVER (PARTITION BY com.content_id)::numeric,2) as "Rating Avg",
                    com.commentary as "Commentary",
                    --cee.objective_rating as "Q1: This activity achieved the stated learning outcomes.",
                    cee.objective_rating as "{}",
                    ROUND(avg(cee.objective_rating) OVER (PARTITION BY com.content_id)::numeric,2) as "Q1 Avg",
                    -- cee.knowledge_rating as "Q2: This activity increased my knowledge.",
                    cee.knowledge_rating as "{}",
                    ROUND(avg(cee.knowledge_rating) OVER (PARTITION BY com.content_id)::numeric,2) as "Q2 Avg",
                    -- cee.practice_rating as "Q3: I will make a change in the way I practice planning based upon my participation in this activity.",
                    cee.practice_rating as "{}",
                    ROUND(avg(cee.practice_rating) OVER (PARTITION BY com.content_id)::numeric,2) as "Q3 Avg",
                    -- cee.speaker_rating as "Q4: The presenter(s)/subject matter expert(s) delivered the content effectively.",
                    cee.speaker_rating as "{}",
                    ROUND(avg(cee.speaker_rating) OVER (PARTITION BY com.content_id)::numeric,2) as "Q4 Avg",
                    -- cee.value_rating as "Q5: I would endorse this activity as a high-quality learning opportunity.",
                    cee.value_rating as "{}",
                    ROUND(avg(cee.value_rating) OVER (PARTITION BY com.content_id)::numeric,2) as "Q5 Avg",
                    -- cee.commentary_suggestions as "Q6: Provide any additional comments regarding this educational activity:",
                    cee.commentary_suggestions as "{}",
                    -- cee.learn_more_choice as "Q7: Would you like to learn more on this topic area?",
                    cee.learn_more_choice as "{}",
                    -- com.publish as "Q8: APA may publish these comments, along with my name, on APA’s website and social media; in APA publications; emails; and elsewhere, to help judge the quality of this education."
                    com.publish as "{}"
                FROM comments_comment com
                    INNER JOIN content_content cc ON cc.id = com.content_id
                    INNER JOIN myapa_contact as myc ON myc.id = com.contact_id
                    INNER JOIN auth_user as usr ON usr.id = myc.user_id
                    LEFT JOIN comments_extendedeventevaluation AS cee ON cee.comment_ptr_id = com.id
                WHERE com.id IN {}
                ORDER BY cc.title ASC
                --LIMIT 500
            """.format(Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, comment_ids)
        with connections['default'].cursor() as cursor:
            cursor.execute(
                query
            )
            rows = cursor.cursor.fetchall()
            desc = cursor.cursor.description
            columns = [column.name for column in desc]
        return (columns, rows)


class CSVResponse(HttpResponse):

  def __init__(self, data, output_name='data', headers=None, encoding='utf8'):
    valid_data = False
    if isinstance(data, QuerySet):
        # if we go back to .values() may have to comment this out again:
        data = list(data.values())

    if hasattr(data, '__getitem__'):
        if isinstance(data[0], dict):
            if headers is None:
                headers = data[0].keys()
                # sub in full questions here to overcome postgres identifier 63 char limit, (if full is desired)
                # for i, q in enumerate(CM_EVAL_QUESTIONS_ABBREV.values()):
                #     index = headers.index(q)
                #     headers[index] = CM_EVAL_QUESTIONS_FULL.get(q[0:2])
            data = [[row[col] for col in headers] for row in data]
        elif isinstance(data[0], list):
            if headers is None:
                headers = data[0]
                # sub in full questions here, (if full is desired)
                # for i, q in enumerate(CM_EVAL_QUESTIONS_ABBREV.values()):
                #     index = headers.index(q)
                #     headers[index] = CM_EVAL_QUESTIONS_FULL.get(q[0:2])
            data = [list(row) for row in data[1]]
        data = [[]] if not data else data
        if hasattr(data[0], '__getitem__'):
            valid_data = True
        data.insert(0, headers)
    assert valid_data is True, "CSVResponse requires a sequence of sequences"

    output = StringIO()
    for row in data:
        if row:
            out_row = []
            for value in row:
                if not isinstance(value, str):
                    value = str(value)
                out_row.append(value.replace('"', '""'))
            output.write('"%s"\n' %
                     '","'.join(out_row))
    mimetype = 'text/csv'
    file_ext = 'csv'
    output.seek(0)
    super(CSVResponse, self).__init__(content=output.getvalue(), content_type=mimetype)
    self['Content-Disposition'] = 'attachment;filename="%s.%s"' % \
        (output_name.replace('"', '\"'), file_ext)
