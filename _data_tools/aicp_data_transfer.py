import csv
from collections import OrderedDict
import math

from django.db import connections

from exam.models import REGULAR_APPLICATION_TYPES, DENIED_STATUSES_LIST
from exam.settings import CAND_CERT_APP_TYPES

reg_app_types_tuple = tuple(REGULAR_APPLICATION_TYPES)
cand_app_types = ('CAND_ENR', 'FOOBAR')
cand_cert_types = tuple(CAND_CERT_APP_TYPES)
denied_statuses = tuple(DENIED_STATUSES_LIST)

contact_fields = ('myc.first_name, myc.middle_name, myc.last_name')
master_content_fields = ('cmc.id as master_id')
content_fields = ('cc.editorial_comments as notes_to_reviewers')#, cc.created_time as application_created_time')
exam_app_fields = ('eea.application_type, eea.application_status')
exam_reg_fields = ('eer.is_pass, eer.certificate_name, eer.release_information')

degree_fields = ('ead.id as degree_id, ead.school_name, ead.other_school, ead.program, ead.graduation_date, ead.level, \
ead.level_other, ead.is_planning, ead.degree_verification')

job_fields = ('eajh.id as job_id, eajh.title, eajh.company, eajh.supervisor_name,\
eajh.start_date, eajh.end_date, eajh.is_current, eajh.is_part_time, eajh.job_verification')

review_fields = ('qar.review_round as review_round, qar.custom_text_1 as draft_denial_statement')#, qar.custom_text_2 as denial_comments')

# Yes, but single rows (no jobs/degrees/essays/reviews)
def get_regular_approved():
    """
    Get Regular, Approved ExamApplication Data
    :return:
    """
    query = """
            SELECT
                --'--Contact:--' as contact_table_name,
                {},--myc.*,
                --'--User:--' as user_table_name,
                -- NO LEADING ZEROES in EXCEL, but they're in the .csv
                usr.username as imis_id,
                --'--MasterContent:--' as exam_app_master_table_name,
                {},--cmc.*,
                --'--Content:--' as content_table_name,
                {},--cc.*,
                --'--ExamApplication:--' as application_table_name,
                {},--eea.*,
                --'--ExamRegistration:--' as registration_table_name,
                {},--eer.*,
                --'--ApplicationDegree:--' as college_degree_table_name,
                {},--ead.*,
                --'--ApplicationJobHistory:--' as job_table_name,
                {},--eajh.*,
                --'--Exam:--' as exam_table_name,
                ee.code as exam_code,
                --'--ApplicationCategory:--' as submission_category_table_name,
                suc.title as application_category,
                --'--Question/Answer:--' as submission_questions_answers,
                qar.question_id, qar.question_text, qar.answer_id,
                --qar.answer_question_id as question_answered,
                qar.answer_text, qar.answerreview_id,
                --'--Review:--' as submission_review_table_name,
                {}--sur.*
            FROM exam_examapplication as eea
                INNER JOIN myapa_contact as myc ON myc.id = eea.contact_id
                INNER JOIN auth_user as usr ON usr.id = myc.user_id
                INNER JOIN content_content as cc ON cc.id = eea.content_ptr_id
                INNER JOIN content_mastercontent as cmc ON cmc.id = cc.master_id
                INNER JOIN exam_exam as ee ON ee.id = eea.exam_id
                INNER JOIN submissions_category as suc ON suc.id = cc.submission_category_id
                LEFT JOIN (select degree.*, uu.uploaded_file as degree_verification, school.title as school_name
                    from exam_applicationdegree as degree
                    LEFT JOIN myapa_contact as school ON school.id = degree.school_id
                        LEFT JOIN uploads_upload AS uu ON uu.id = degree.verification_document_id) ead
                        ON ead.application_id = eea.content_ptr_id
                LEFT JOIN (select job.*, uu.uploaded_file as job_verification
                    FROM exam_applicationjobhistory as job
                        LEFT JOIN uploads_upload AS uu ON uu.id = job.verification_document_id) eajh
                    ON eajh.application_id = eea.content_ptr_id
                LEFT JOIN exam_examregistration as eer ON eer.application_id = eea.content_ptr_id
                LEFT JOIN (SELECT suq.id as question_id, suq.title as question_text,
                    sua.question_id as answer_question_id, sua.text as answer_text, sua.content_id as answer_content_id,
                    sur.*, sua.id as answer_id, sur.id as answerreview_id
                    FROM submissions_answer as sua
                    INNER JOIN submissions_question as suq ON suq.id = sua.question_id
                    INNER JOIN submissions_review as sur ON sur.content_id = sua.content_id
                    ) qar ON answer_content_id = cc.id
            WHERE eea.application_status = 'A'
                and (cc.publish_status = 'DRAFT' or cc.publish_status = 'SUBMISSION')
                and eea.application_type in {}
            --ORDER BY cc.created_time DESC
            -- limiting for testing: (total is 369094 rows)
            GROUP BY
                imis_id, myc.first_name, myc.middle_name, myc.last_name,
                cmc.id,
                notes_to_reviewers,
                eea.application_type, eea.application_status,
                eer.is_pass, eer.certificate_name, eer.release_information,
                ead.id, ead.school_name, ead.other_school, ead.program, ead.graduation_date, ead.level,
                   ead.level_other, ead.is_planning, ead.degree_verification,
                eajh.id, eajh.title, eajh.company, eajh.supervisor_name, eajh.start_date, eajh.end_date,
                   eajh.is_current, eajh.is_part_time, eajh.job_verification,
                exam_code,
                application_category,
                qar.question_id, qar.question_text, qar.answer_id,
                --question_answered,
                qar.answer_text, qar.answerreview_id, qar.review_round, qar.custom_text_1
                --overall_rating, approval_denial_recommendation, denial_letter_option, overall_comments, review_round,
                --    agree_with_denial, draft_denial,
                --denial_comments
            LIMIT 500000
        """.format(contact_fields, master_content_fields, content_fields,
                   exam_app_fields, exam_reg_fields,
                   degree_fields, job_fields, review_fields,
                   reg_app_types_tuple,
                   )
    with connections['default'].cursor() as cursor:
        cursor.execute(
            query
            )
        rows = cursor.cursor.fetchall()
        # print(rows)
        print("num rows: ", len(rows))
        # print("dir cursor.cursor", dir(cursor.cursor))
        desc = cursor.cursor.description
        # columns = [d[0].name for d in desc]
        columns = [column.name for column in desc]
        print("COLUMNS ............")
        print(columns)
    return (columns, rows)

# NOPE
def get_candidate_enrollment():
    """
    Get Candidate Enrollment Application Data
    :return:
    """
    query = """
            SELECT
                -- '--Contact:--' as contact_table_name,
                {},--myc.*,
                -- '--User:--' as user_table_name,
                usr.username as imis_id,
                -- '--MasterContent:--' as exam_app_master_table_name,
                {},
                -- '--Content:--' as content_table_name,
                {},--cc.*,
                -- '--ExamApplication:--' as application_table_name,
                {},--eea.*,
                -- '--ExamRegistration:--' as registration_table_name,
                --<CURLY_BRACES>,--eer.*,
                -- '--ApplicationDegree:--' as college_degree_table_name,
                {},--ead.*,
                -- '--Exam:--' as exam_table_name,
                ee.code as exam_code,
                -- '--ApplicationCategory:--' as submission_category_table_name,
                suc.title as application_category
            FROM exam_examapplication as eea
                INNER JOIN myapa_contact as myc ON myc.id = eea.contact_id
                INNER JOIN auth_user as usr ON usr.id = myc.user_id
                INNER JOIN content_content as cc ON cc.id = eea.content_ptr_id
                INNER JOIN content_mastercontent as cmc ON cmc.id = cc.master_id
                INNER JOIN exam_exam as ee ON ee.id = eea.exam_id
                INNER JOIN submissions_category as suc ON suc.id = cc.submission_category_id
                -- LEFT JOIN exam_examregistration as eer ON eer.application_id = eea.content_ptr_id
                LEFT JOIN (select degree.*, uu.uploaded_file as degree_verification, school.title as school_name
                    from exam_applicationdegree as degree
                    LEFT JOIN myapa_contact as school ON school.id = degree.school_id
                        LEFT JOIN uploads_upload AS uu ON uu.id = degree.verification_document_id) ead
                        ON ead.application_id = eea.content_ptr_id
            WHERE eea.application_type in {}
                AND (cc.created_time > '2020-11-14' OR cc.updated_time > '2020-11-14')
            --ORDER BY cc.created_time DESC
            LIMIT 500000
        """.format(contact_fields, master_content_fields, content_fields,
                   exam_app_fields, #exam_reg_fields,
                   degree_fields,
                   cand_app_types)
    with connections['default'].cursor() as cursor:
        cursor.execute(
            query
        )
        rows = cursor.cursor.fetchall()
        print("num rows: ", len(rows))
        desc = cursor.cursor.description
        columns = [column.name for column in desc]
        print("COLUMNS ............")
        print(columns)
    return (columns, rows)

# Yes -- but just approved, single rows (no jobs/degrees/essays/reviews)
def get_candidate_certification():
    """
    Get Candidate Certification ExamApplication Approved Data
    :return:
    """
    query = """
            SELECT
                --'--Contact:--' as contact_table_name,
                {},--myc.*,
                --'--User:--' as user_table_name,
                usr.username as imis_id,
                --'--MasterContent:--' as exam_app_master_table_name,
                {},--cmc.*,
                --'--Content:--' as content_table_name,
                {},--cc.*,
                --'--ExamApplication:--' as application_table_name,
                {},--eea.*,
                --'--ApplicationDegree:--' as college_degree_table_name,
                {},--ead.*,
                --'--ApplicationJobHistory:--' as job_table_name,
                {},--eajh.*,
                --'--Exam:--' as exam_table_name,
                ee.code as exam_code,
                --'--ApplicationCategory:--' as submission_category_table_name,
                suc.title as application_category,
                --'--Question/Answer:--' as submission_questions_answers, qar.question_id, qar.question_text,
                qar.question_id, qar.question_text, qar.answer_id,
                --    qar.answer_question_id as question_answered,
                qar.answer_text, qar.answerreview_id,
                --'--Review:--' as submission_review_table_name,
                {}--sur.*
            FROM exam_examapplication as eea
                INNER JOIN myapa_contact as myc ON myc.id = eea.contact_id
                INNER JOIN auth_user as usr ON usr.id = myc.user_id
                INNER JOIN content_content as cc ON cc.id = eea.content_ptr_id
                INNER JOIN content_mastercontent as cmc ON cmc.id = cc.master_id
                INNER JOIN exam_exam as ee ON ee.id = eea.exam_id
                INNER JOIN submissions_category as suc ON suc.id = cc.submission_category_id
                LEFT JOIN (select degree.*, uu.uploaded_file as degree_verification, school.title as school_name
                    from exam_applicationdegree as degree
                    LEFT JOIN myapa_contact as school ON school.id = degree.school_id
                        LEFT JOIN uploads_upload AS uu ON uu.id = degree.verification_document_id) ead
                        ON ead.application_id = eea.content_ptr_id
                LEFT JOIN (select job.*, uu.uploaded_file as job_verification
                    FROM exam_applicationjobhistory as job
                        LEFT JOIN uploads_upload AS uu ON uu.id = job.verification_document_id) eajh
                    ON eajh.application_id = eea.content_ptr_id
                LEFT JOIN (SELECT suq.id as question_id, suq.title as question_text,
                    sua.question_id as answer_question_id, sua.text as answer_text, sua.content_id as answer_content_id,
                    sur.*, sua.id as answer_id, sur.id as answerreview_id
                    FROM submissions_answer as sua
                    INNER JOIN submissions_question as suq ON suq.id = sua.question_id
                    INNER JOIN submissions_review as sur ON sur.content_id = sua.content_id
                    ) qar ON answer_content_id = cc.id
            WHERE eea.application_status = 'A'
                and eea.application_type in {}
                and (cc.publish_status = 'DRAFT' or cc.publish_status = 'SUBMISSION')
            --ORDER BY cc.created_time DESC
            LIMIT 500000
        """.format(contact_fields, master_content_fields, content_fields,
                   exam_app_fields, degree_fields, job_fields, review_fields,
                   cand_cert_types)
    with connections['default'].cursor() as cursor:
        cursor.execute(
            query
            )
        rows = cursor.cursor.fetchall()
        print("num rows: ", len(rows))
        desc = cursor.cursor.description
        columns = [column.name for column in desc]
        print("COLUMNS ............")
        print(columns)
    return (columns, rows)

# Yes
def get_regular_denied():
    """
    Get Regular Denied ExamApplication Data NEW: MAKE IT PULL ONLY MOST RECENTLY DENIED
    :return:
    """
    query = """
            SELECT
                --'--Contact:--' as contact_table_name,
                {},--myc.*,
                --'--User:--' as user_table_name,
                usr.username as imis_id,
                --'--MasterContent:--' as exam_app_master_table_name,
                {},--cmc.*,
                --'--Content:--' as content_table_name,
                {},--cc.*,
                --'--ExamApplication:--' as application_table_name,
                {},--eea.*,
                --'--ExamRegistration:--' as registration_table_name,
                {},--eer.*,
                --'--ApplicationDegree:--' as college_degree_table_name,
                {},--ead.*,
                --'--ApplicationJobHistory:--' as job_table_name,
                {},--eajh.*,
                --'--Exam:--' as exam_table_name,
                ee.code as exam_code,
                --'--ApplicationCategory:--' as submission_category_table_name,
                suc.title as application_category,
                --'--Question/Answer:--' as submission_questions_answers,
                qar.question_id, qar.question_text, qar.answer_id,
                --qar.answer_question_id as question_answered,
                qar.answer_text, qar.answerreview_id,
                --'--Review:--' as submission_review_table_name,
                {}--sur.*
            FROM exam_examapplication as eea
                INNER JOIN myapa_contact as myc ON myc.id = eea.contact_id
                INNER JOIN auth_user as usr ON usr.id = myc.user_id
                INNER JOIN content_content as cc ON cc.id = eea.content_ptr_id
                INNER JOIN content_mastercontent as cmc ON cmc.id = cc.master_id
                INNER JOIN exam_exam as ee ON ee.id = eea.exam_id
                INNER JOIN submissions_category as suc ON suc.id = cc.submission_category_id
                -- THIS IS TO REDUCE TABLE TO ONLY MOST RECENTLY DENIED:
                INNER JOIN (SELECT my_con.user_id as imis_id,
                                max(con_con.created_time) as maxDate
                    FROM exam_examapplication as ex_ex_app
                        INNER JOIN myapa_contact as my_con ON my_con.id = ex_ex_app.contact_id
                        INNER JOIN auth_user as au_us ON au_us.id = my_con.user_id
                        inner join content_content as con_con ON con_con.id = ex_ex_app.content_ptr_id
                     WHERE ex_ex_app.application_status in {}
                           and ex_ex_app.application_type in {}
                           and con_con.publish_status = 'DRAFT'
                      GROUP BY imis_id) b ON usr.id = b.imis_id AND cc.created_time = maxDate
                LEFT JOIN (select degree.*, uu.uploaded_file as degree_verification, school.title as school_name
                    from exam_applicationdegree as degree
                    LEFT JOIN myapa_contact as school ON school.id = degree.school_id
                        LEFT JOIN uploads_upload AS uu ON uu.id = degree.verification_document_id) ead
                        ON ead.application_id = eea.content_ptr_id
                LEFT JOIN (select job.*, uu.uploaded_file as job_verification
                    FROM exam_applicationjobhistory as job
                        LEFT JOIN uploads_upload AS uu ON uu.id = job.verification_document_id) eajh
                    ON eajh.application_id = eea.content_ptr_id
                LEFT JOIN exam_examregistration as eer ON eer.application_id = eea.content_ptr_id
                LEFT JOIN (SELECT suq.id as question_id, suq.title as question_text,
                    sua.question_id as answer_question_id, sua.text as answer_text, sua.content_id as answer_content_id,
                    sur.*, sua.id as answer_id, sur.id as answerreview_id
                    FROM submissions_answer as sua
                    INNER JOIN submissions_question as suq ON suq.id = sua.question_id
                    INNER JOIN submissions_review as sur ON sur.content_id = sua.content_id
                    ) qar ON answer_content_id = cc.id
            WHERE eea.application_status in {}
                and eea.application_type in {}
                and cc.publish_status = 'DRAFT'
                and ee.code IN (
                    '2017ASC','2017MAY','2017NOV',
                    '2018ASC','2018MAY','2018NOV',
                    '2019MAY','2019NOV',
                    '2020MAY','2020NOV')
            --ORDER BY cc.created_time DESC
            LIMIT 500000 --25329 rows
        """.format(contact_fields, master_content_fields, content_fields,
                   exam_app_fields, exam_reg_fields, degree_fields, job_fields, review_fields,
                   denied_statuses, reg_app_types_tuple, denied_statuses, reg_app_types_tuple)
    with connections['default'].cursor() as cursor:
        cursor.execute(
            query
            )
        rows = cursor.cursor.fetchall()
        print("num rows: ", len(rows))
        desc = cursor.cursor.description
        columns = [column.name for column in desc]
        print("COLUMNS ............")
        print(columns)
    return (columns, rows)

# Yes -- because we're going to limit the Cand Cert Approved Data to just single rows
def get_candidate_denied():
    """
    Get Candidate Certification Denied ExamApplication Data
    Candidate Enrollment Denied (separate process) is excluded
    :return:
    """
    query = """
            SELECT
                --'--Contact:--' as contact_table_name,
                {},--myc.*,
                --'--User:--' as user_table_name,
                usr.username as imis_id,
                --'--MasterContent:--' as exam_app_master_table_name,
                {},--cmc.*,
                --'--Content:--' as content_table_name,
                {},--cc.*,
                --'--ExamApplication:--' as application_table_name,
                {},--eea.*,
                --'--ApplicationDegree:--' as college_degree_table_name,
                {},--ead.*,
                --'--ApplicationJobHistory:--' as job_table_name,
                {},--eajh.*,
                --'--Exam:--' as exam_table_name,
                ee.code as exam_code,
                --'--ApplicationCategory:--' as submission_category_table_name,
                suc.title as application_category,
                --'--Question/Answer:--' as submission_questions_answers,
                qar.question_id, qar.question_text, qar.answer_id,
                --qar.answer_question_id as question_answered,
                qar.answer_text, qar.answerreview_id,
                --'--Review:--' as submission_review_table_name,
                {}--sur.*
            FROM exam_examapplication as eea
                INNER JOIN myapa_contact as myc ON myc.id = eea.contact_id
                INNER JOIN auth_user as usr ON usr.id = myc.user_id
                INNER JOIN content_content as cc ON cc.id = eea.content_ptr_id
                INNER JOIN content_mastercontent as cmc ON cmc.id = cc.master_id
                INNER JOIN exam_exam as ee ON ee.id = eea.exam_id
                INNER JOIN submissions_category as suc ON suc.id = cc.submission_category_id
                -- THIS IS TO REDUCE TABLE TO ONLY MOST RECENTLY DENIED:
                INNER JOIN (SELECT my_con.user_id as imis_id,
                                --con_con.master_id as app_master_id,
                                max(con_con.created_time) as maxDate
                    FROM exam_examapplication as ex_ex_app
                        INNER JOIN myapa_contact as my_con ON my_con.id = ex_ex_app.contact_id
                        INNER JOIN auth_user as au_us ON au_us.id = my_con.user_id
                        inner join content_content as con_con ON con_con.id = ex_ex_app.content_ptr_id
                     WHERE ex_ex_app.application_status in {}
                           and ex_ex_app.application_type in {}
                           and con_con.publish_status = 'DRAFT'
                      GROUP BY imis_id--, con_con.master_id
                        ) b ON usr.id = b.imis_id AND cc.created_time = maxDate--ON cc.master_id = b.app_master_id
                LEFT JOIN (select degree.*, uu.uploaded_file as degree_verification, school.title as school_name
                    from exam_applicationdegree as degree
                    LEFT JOIN myapa_contact as school ON school.id = degree.school_id
                        LEFT JOIN uploads_upload AS uu ON uu.id = degree.verification_document_id) ead
                        ON ead.application_id = eea.content_ptr_id
                LEFT JOIN (select job.*, uu.uploaded_file as job_verification
                    FROM exam_applicationjobhistory as job
                        LEFT JOIN uploads_upload AS uu ON uu.id = job.verification_document_id) eajh
                    ON eajh.application_id = eea.content_ptr_id
                LEFT JOIN (SELECT suq.id as question_id, suq.title as question_text,
                    sua.question_id as answer_question_id, sua.text as answer_text, sua.content_id as answer_content_id,
                    sur.*, sua.id as answer_id, sur.id as answerreview_id
                    FROM submissions_answer as sua
                    INNER JOIN submissions_question as suq ON suq.id = sua.question_id
                    INNER JOIN submissions_review as sur ON sur.content_id = sua.content_id
                    ) qar ON answer_content_id = cc.id
            WHERE eea.application_status in {}
                and eea.application_type in {}
                and (cc.publish_status = 'DRAFT' or cc.publish_status = 'SUBMISSION')
            --ORDER BY cc.created_time DESC
            GROUP BY
                imis_id, myc.first_name, myc.middle_name, myc.last_name, usr.username,
                cmc.id,
                --exam_app_id,
                cc.created_time, cc.editorial_comments, cc.submission_time, cc.submission_approved_time,
                eea.application_type, eea.application_status,
                ead.school_name, ead.other_school,  ead.pab_accredited, ead.year_in_program, ead.graduation_date, ead.level,
                    ead.level_other, ead.is_planning, ead.complete, ead.program, ead.is_current, ead.student_id,
                    ead.degree_verification, ead.id,
                eajh.is_planning, eajh.contact_employer, eajh.supervisor_name,
                    eajh.title, eajh.company, eajh.city, eajh.state, eajh.zip_code, eajh.country, eajh.start_date,
                    eajh.end_date, eajh.is_current, eajh.is_part_time, eajh.phone, eajh.job_verification, eajh.id,
                exam_code,
                application_category,
                qar.question_id, qar.question_text, --question_answered,
                qar.answer_id, qar.answer_text, qar.custom_text_1, qar.custom_text_2,
                qar.review_round, qar.answerreview_id
                --overall_rating, approval_denial_recommendation, denial_letter_option, overall_comments, review_round,
                    --agree_with_denial, draft_denial, denial_comments
            LIMIT 500000
        """.format(contact_fields, master_content_fields, content_fields,
                   exam_app_fields, degree_fields, job_fields, review_fields,
                   denied_statuses, cand_cert_types, denied_statuses, cand_cert_types)
    print("QUERY IS ...")
    print(query)
    with connections['default'].cursor() as cursor:
        cursor.execute(
            query
            )
        rows = cursor.cursor.fetchall()
        print("num rows: ", len(rows))
        desc = cursor.cursor.description
        columns = [column.name for column in desc]
        print("COLUMNS ............")
        print(columns)
    return (columns, rows)

def get_column_names(table):
    query="""
    select *
    from {}
    -- adding this line to try to accommodate joins:
    --on true
    where false;
    """.format(table)
    with connections['default'].cursor() as cursor:
        cursor.execute(
            query
            )
        # print("dir is .........")
        # print(dir(cursor.cursor))
        # print("DESCRIPTION............", cursor.cursor.description)
        # print("NAME..................", cursor.cursor.name)
        # print("LEN DESC.....,", len(cursor.cursor.description))
        # print("DESC 0 ........", type(cursor.cursor.description[0]))
        desc = cursor.cursor.description
        # columns = [d[0].name for d in desc]
        columns = [column.name for column in desc]
        print("COLUMNS ............")
        print(columns)
    return columns

def write_csv(column_names, rows, outfile='/tmp/reg_approved.csv'):
    with open(outfile, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(column_names)
        for row in rows:
            writer.writerow(row)

# for use in shell testing:
# from exam.models import *
from myapa.models import *
from submissions.models import *
# ea=ExamApplication.objects.last()

# from _data_tools.aicp_data_transfer import *
#
# table = 'exam_examapplication'
# table = 'exam_examapplication INNER JOIN exam_examregistration'
# table = 'exam_examapplication, exam_examregistration, exam_applicationdegree'
# table = """
#     exam_examapplication, exam_examregistration, exam_applicationdegree,
#     exam_applicationjobhistory, exam_exam
# """

outfile_ra = '/tmp/ra.csv'
outfile_ra_flat = '/tmp/ra_flat.csv'

outfile_ce = '/tmp/ce.csv'

outfile_cc = '/tmp/cc.csv'
outfile_cc_flat = '/tmp/cc_flat.csv'

outfile_rd = '/tmp/rd.csv'
outfile_rd_flat = '/tmp/rd_flat.csv'

outfile_cd = '/tmp/cd.csv'
outfile_cd_flat = '/tmp/cd_flat.csv'

# data_ra = get_regular_approved()
# data_ce = get_candidate_enrollment()
# data_cc = get_candidate_certification()
# data_rd = get_regular_denied()
# data_cd = get_candidate_denied()

def make_csv(data, outfile):
    write_csv(data[0], data[1], outfile)

def open_excel(outfile):
    import os
    os.system('ls /tmp/*.csv')
    # os.system('open -a "Microsoft Excel" /tmp/ra.csv')
    # os.system('open -a "Microsoft Excel" /tmp/ce.csv')
    # os.system('open -a "Microsoft Excel" /tmp/cc.csv')
    # os.system('open -a "Microsoft Excel" /tmp/rd.csv')
    sys_str = 'open -a "Microsoft Excel" {}'.format(outfile)
    # os.system('open -a "Microsoft Excel" /tmp/cd.csv')
    os.system(sys_str)


# CALL THE ABOVE LIKE THIS: (for flattening don't make_csv here)
# NONE OF THIS APPLIES ANYMORE EXCEPT CANDIDATE ENROLLMENT:

# REGULAR APPROVED
# data_ra = get_regular_approved()
# make_csv(data_ra, outfile_ra)
# open_excel(outfile_ra)

# CANDIDATE APPROVED
# data_cc = get_candidate_certification()
# make_csv(data_cc, outfile_cc)
# open_excel(outfile_cc)

# REGULAR DENIED
# data_rd = get_regular_denied()
# make_csv(data_rd, outfile_rd)
# open_excel(outfile_rd)

# CANDIDATE DENIED
# data_cd = get_candidate_denied()
# make_csv(data_cd, outfile_cd)
# open_excel(outfile_cd)

# CANDIDATE ENROLLMENT
# data_ce = get_candidate_enrollment()
# make_csv(data_ce, outfile_ce)
# open_excel(outfile_ce)


# Flatten the rows in the denied csv from above

# changes to original query needed:
# ---pull only most recently denied
# original query needs to pull only most recently denied app
# SORT KEYS IN ORDERED DICT: (IF I WANT IT ORDERED BY MASTER ID)
# https://stackoverflow.com/questions/23587174/how-to-sort-ordereddict-using-a-sorted-list-of-keys

def make_flat_data(column_names, rows):
    flat_data = []
    list_of_rows_of_values = []
    print("COLUMN NAMES") # list of strings
    print(column_names)
    main_od = OrderedDict()
    degree_columns = ['degree_id', 'school_name', 'other_school','program', 'graduation_date', 'level', 'level_other',
        'is_planning', 'degree_verification']
    degree_is_new = False
    job_columns = ['job_id', 'title', 'company', 'supervisor_name',
        'start_date', 'end_date', 'is_current', 'is_part_time', 'job_verification']
    job_is_new = False
    question_columns = ['question_id','question_text']
    question_is_new = False
    answer_columns = ['answer_id','answer_text']
    answer_is_new = False
    answerreview_columns = ['answerreview_id','review_round', 'draft_denial_statement']
    answerreview_is_new = False
    all_iterated_columns = degree_columns + job_columns + question_columns + answer_columns + answerreview_columns
    current_master_id = None
    latest_review_round = 0
    latest_draft_denial = ""
    max_degrees = 0
    max_jobs = 0
    max_questions = 0
    max_answers = 0

    for row in rows:
        master_id = row[column_names.index("master_id")]
        if master_id != current_master_id:
            vals_od = OrderedDict()
            vals_od["draft_denial_statement"] = latest_draft_denial
            latest_draft_denial = ""
            latest_review_round = 0
            degrees = set()
            jobs = set()
            questions = set()
            answers = set()
            answerreviews = set()
        degree_id = row[column_names.index("degree_id")]
        if degree_id not in degrees:
            degree_is_new = True
        degrees.add(degree_id)
        max_degrees = max(max_degrees, len(degrees))
        job_id = row[column_names.index("job_id")]
        if job_id not in jobs:
            job_is_new = True
        jobs.add(job_id)
        max_jobs = max(max_jobs, len(jobs))
        question_id = row[column_names.index("question_id")]
        if question_id not in questions:
            question_is_new = True
        questions.add(question_id)
        max_questions = max(max_questions, len(questions))
        answer_id = row[column_names.index("answer_id")]
        if answer_id not in answers:
            answer_is_new = True
        answers.add(answer_id)
        max_answers = max(max_answers, len(answers))
        answerreview_id = row[column_names.index("answerreview_id")]
        if answerreview_id not in answerreviews:
            answerreview_is_new = True
        answerreviews.add(answerreview_id)
        imis_id = row[column_names.index("imis_id")]
        for col_name in column_names:
            subdict_val =  row[column_names.index(col_name)]
            if col_name in degree_columns and degree_is_new:
                if col_name != "degree_id":
                    new_col_name = "degree_" + str(len(degrees)).zfill(2) + "_" + col_name
                    vals_od[new_col_name] = subdict_val
            elif col_name in job_columns and job_is_new:
                if col_name != "job_id":
                    new_col_name = "job_" + str(len(jobs)).zfill(2) + "_" + col_name
                    vals_od[new_col_name] = subdict_val
            elif col_name in question_columns and question_is_new:
                if col_name != "question_id":
                    new_col_name = "question_" + str(len(questions)) + "_" + col_name
                    vals_od[new_col_name] = subdict_val
            elif col_name in answer_columns and answer_is_new:
                if col_name != "answer_id":
                    new_col_name = "answer_" + str(len(answers)) + "_" + col_name
                    vals_od[new_col_name] = subdict_val
            elif col_name in answerreview_columns and answerreview_is_new:
                if col_name == "review_round":
                    review_round = row[column_names.index("review_round")]
                    if review_round is None:
                        review_round = 0
                    if review_round > latest_review_round:
                        latest_review_round = review_round
                        latest_draft_denial = row[column_names.index("draft_denial_statement")]
            elif col_name not in all_iterated_columns:
                vals_od[col_name] = subdict_val
        main_od[master_id] = vals_od
        current_master_id = master_id
        degree_is_new = False
        job_is_new = False
        question_is_new = False
        answer_is_new = False
        answerreview_is_new = False

    # NEXT: NULL PADDING of the dict
    degree_columns.remove("degree_id")
    job_columns.remove("job_id")
    question_columns.remove("question_id")
    answer_columns.remove("answer_id")

    for master_id_key, subdict in main_od.items():
        num_degrees = max([int(k[7:9]) for k in subdict.keys() if k.find("degree_") >= 0])
        num_jobs = max([int(k[4:6]) for k in subdict.keys() if k.find("job_") >= 0])
        num_questions = max([int(k[9]) for k in subdict.keys() if k.find("question_") >= 0])
        num_answers = max([int(k[7]) for k in subdict.keys() if k.find("answer_") >= 0])
        for i in range(num_degrees+1, max_degrees+1):
            for col_name in degree_columns:
                new_col_name = "degree_" + str(i).zfill(2) + "_" + col_name
                subdict[new_col_name] = None
        for i in range(num_jobs+1, max_jobs+1):
            for col_name in job_columns:
                new_col_name = "job_" + str(i).zfill(2) + "_" + col_name
                subdict[new_col_name] = None
        for i in range(num_questions+1, max_questions+1):
            for col_name in question_columns:
                new_col_name = "question_" + str(i) + "_" + col_name
                subdict[new_col_name] = None
        for i in range(num_answers+1, max_answers+1):
            for col_name in answer_columns:
                new_col_name = "answer_" + str(i) + "_" + col_name
                subdict[new_col_name] = None
        main_od[master_id_key] = OrderedDict(sorted(subdict.items()))
        row_of_values = main_od[master_id_key].values()
        list_of_rows_of_values.append(list(row_of_values))

    first_subdict = main_od[list(main_od.keys())[0]]
    column_names = list(first_subdict.keys())
    first_columns = ["imis_id", "first_name", "middle_name", "last_name", "master_id"]
    last_columns = ["answer_1_answer_text", "answer_2_answer_text", "answer_3_answer_text", "answer_4_answer_text"]
    first_column_inds = [column_names.index(n) for n in first_columns]
    last_column_inds = [column_names.index(n) for n in last_columns]
    mid_column_inds = [column_names.index(n) for n in column_names if n not in first_columns and n not in last_columns]
    column_order = first_column_inds + mid_column_inds + last_column_inds
    column_names = [column_names[i] for i in column_order]
    list_of_rows_of_values = [
        tuple([row[i] for i in column_order]) for row in list_of_rows_of_values
        ]
    flat_data.append(column_names)
    flat_data.append(list_of_rows_of_values)
    # print("FLAT DATA IS --------------------------------------")
    # print(flat_data)
    return flat_data
mfd=make_flat_data

def flatten_chunks(data):
    # data is a tuple containing two lists; list 1 is column names; list 2 are tuples containing row values
    # we need to call mfd() on new chunks that are tuples containing two lists:
    # list 1 = data[0]
    # list 2 = a portion of tuples from data[1]
    num_rows = len(data[1])
    # USE ONLY EVEN NUMBERS FOR THE DIVVY (DIDN'T TEST ODD)
    chunk_divvy = 8
    chunk_size = math.floor(num_rows / chunk_divvy)
    finish = False
    print("chunk_size is ", chunk_size)
    for i in range(0,num_rows, chunk_size):
        print("START SLICE: ", i)
        if i >= chunk_size * (chunk_divvy - 1):
            print("END SLICE: ", num_rows)
            end_slice = num_rows
            finish=True
        else:
            print("END SLICE: ", i+chunk_size)
            end_slice = i+chunk_size
        data_chunk = data[1][i:end_slice]
        print("len data_chunk is ", len(data_chunk))
        data_flat=mfd(data[0], data_chunk)
        # name based on spreadsheet row numbers:
        outfile_flat = '/tmp/trad_approved_flat_rows_' + str(i+1) + '_to_' + str(end_slice) + '.csv'
        print("outfile_flat_name is ", outfile_flat)
        make_csv(data_flat, outfile_flat)
        if finish:
            break

# for testing:
# data=(['foo'],[(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),()])
# flatten_chunks(data)

# CALL LIKE THIS:

# REGULAR DENIED
# data_rd = get_regular_denied()
# just for testing:
# flatten_chunks(data_rd)
# data_rd_flat=mfd(data_rd[0], data_rd[1])
# make_csv(data_rd_flat, outfile_rd_flat)
# open_excel(outfile_rd_flat)

# CANDIDATE DENIED
# data_cd = get_candidate_denied()
# just for testing:
# flatten_chunks(data_cd)
# data_cd_flat=mfd(data_cd[0], data_cd[1])
# make_csv(data_cd_flat, outfile_cd_flat)
# open_excel(outfile_cd_flat)

# data_ra = get_regular_approved()
# data_ra_flat=mfd(data_ra[0], data_ra[1])
# flatten_chunks(data_ra)
# NOPE CAN'T DO THIS ON THE WEB SERVERS, PYTHON KILLS THE PROCESS BECAUSE DICT IS TOO BIG:
# make_csv(data_ra_flat, outfile_ra_flat)
# open_excel(outfile_ra_flat)

# CANDIDATE APPROVED
# data_cc = get_candidate_certification()
# just for testing:
# flatten_chunks(data_cc)
# data_cc_flat=mfd(data_cc[0], data_cc[1])
# make_csv(data_cc_flat, outfile_cc_flat)
# open_excel(outfile_cc_flat)

# NO FLATTEN:
# CANDIDATE ENROLLMENT
# data_ce = get_candidate_enrollment()
# just for testing: probabaly can't flatten this one
# flatten_chunks(data_ce)
# make_csv(data_ce, outfile_ce)
# open_excel(outfile_ce)


# """
# table='exam_examapplication'
# query="""
# select *
# from {}
# where false;
# """.format(table)
# with connections['default'].cursor() as cursor:
#     cursor.execute(
#         query
#         )
#     print("dir is .........")
#     print(dir(cursor.cursor))
#     print("DESCRIPTION............",cursor.cursor.description)
#     print("NAME..................",cursor.cursor.name)
#     print("LEN DESC.....,", len(cursor.cursor.description))
#     print("DESC 0 ........", type(cursor.cursor.description[0]))
#     desc = cursor.cursor.description
#     # columns = [d[0].name for d in desc]
#     columns = [column.name for column in desc]
#     print("COLUMNS ............")
#     print(columns)
# """

# THIS WORKS...IT PULLS VERIF DOCS SO WE NEED TO PULL OUT STUFF ABOVE AND PUT IT BACK IN ONE BY ONE
# won't pull verif docs for cand_cert apps ?? narrow down query to bare bones on cand_cert

# q = """
# select eea.content_ptr_id,
# --myc.id, cc.id, cmc.id, ee.id, suc.id,
# uu.id as verif_doc_id
# from exam_examapplication as eea
# --INNER JOIN myapa_contact as myc ON myc.id = eea.contact_id
# --INNER JOIN content_content as cc ON cc.id = eea.content_ptr_id
# --INNER JOIN content_mastercontent as cmc ON cmc.id = cc.master_id
# --INNER JOIN exam_exam as ee ON ee.id = eea.exam_id
# --INNER JOIN submissions_category as suc ON suc.id = cc.submission_category_id
# --LEFT JOIN exam_applicationdegree as ead ON ead.application_id = eea.content_ptr_id
# --LEFT JOIN exam_applicationjobhistory as eajh ON eajh.application_id = eea.content_ptr_id
# --LEFT JOIN submissions_answer as sua ON sua.content_id = cc.id
# --LEFT JOIN submissions_question as suq ON suq.id = sua.question_id
# --LEFT JOIN submissions_review as sur ON sur.content_id = cc.id
# LEFT JOIN uploads_upload as uu ON uu.content_id = eea.content_ptr_id
# where eea.application_status IN ('EB_D', 'D', 'I', 'D_C', 'EB_D_C')
# and eea.application_type = 'CAND_CERT'
# --and cc.publish_status = 'DRAFT'
# ;
# """
# # how to write query results to file in psql:
# 'COPY ([Query]) TO '[File Name]' DELIMITER ',' CSV HEADER;'
# q2 = """
# COPY (select eea.*, uu.* from exam_examapplication as eea LEFT JOIN uploads_upload as uu ON uu.content_id = eea.content_ptr_id where eea.application_status = 'D' and eea.application_type = 'CAND_ENR')
# TO '/tmp/vd.csv' DELIMITER ',' CSV HEADER;
# """
# import os
# os.system('open -a "Microsoft Excel" /tmp/vd.csv')
