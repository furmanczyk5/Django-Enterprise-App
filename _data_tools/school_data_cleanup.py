from imis.models import *
from myapa.models.educational_degree import EducationalDegree
from myapa.models.proxies import School
from store.models import *
from django.db.models import Sum, Q, Prefetch
import pytz

"""
THINKING OUT LOUD

1. IN SQL, first delete any iMIS records that have a blank school id, school other, all schools, and accred schools
    # there are 4770 degrees in iMIS that have inadaquate information
    DELETE
    FROM Custom_Degree
    WHERE SCHOOL_OTHER = ''
    AND (SCHOOL_ID = '' OR SCHOOL_ID = '0')
    AND (ALL_SCHOOLS = '' )
    AND (ACCRED_SCHOOLS = '' )

    In django, also delete any degree records that do not have a school id and other school populated
    
    # there are 9 degrees in django that hvae inadaquate information
    EducationalDegree.objects.filter(school__isnull=True, other_school="").delete()

2. We need to update iMIS records so that if accred school or all schools
    A. Can Karl's team provide a list of school ids that match the programs? Then we can update the school other field with appropriate school name

    -- first update all degrees with school_other names - regardless if tracked
    -- for all schools
    UPDATE Custom_Degree
    SET SCHOOL_OTHER = N.COMPANY,
    SCHOOL_ID = CASE WHEN CSA.ID IS NOT NULL THEN N.ID ELSE '' END
    FROM Custom_Degree
    LEFT JOIN _custom_degree_schools_fix CDSF ON CDSF.IMIS_CODE = ALL_SCHOOLS AND 
                                                    CDSF.TABLE_NAME = 'ALL_SCHOOLS' AND
                                                    CDSF.IMIS_CODE IS NOT NULL
    LEFT JOIN Custom_SchoolAccredited CSA ON CSA.ID = CDSF.ID
    INNER JOIN Name N ON N.ID = CDSF.ID
                                AND CDSF.ID != '000000'
    WHERE Custom_Degree.SCHOOL_OTHER = ''

    -- for accredited schools
    UPDATE Custom_Degree
    SET SCHOOL_OTHER = N.COMPANY,
    SCHOOL_ID = CASE WHEN CSA.ID IS NOT NULL THEN N.ID ELSE '' END
    FROM Custom_Degree
    LEFT JOIN _custom_degree_schools_fix CDSF ON CDSF.IMIS_CODE = ACCRED_SCHOOLS AND 
                                                    CDSF.TABLE_NAME = 'ACCRED_SCHOOLS' AND
                                                    CDSF.IMIS_CODE IS NOT NULL
    LEFT JOIN Custom_SchoolAccredited CSA ON CSA.ID = CDSF.ID
    INNER JOIN Name N ON N.ID = CDSF.ID
                                AND CDSF.ID != '000000'
    WHERE Custom_Degree.SCHOOL_OTHER = ''

    -- update school_other data to the best of our ability for those that do not have an accreditation (000000)
    -- for all schools
    UPDATE Custom_Degree
    SET SCHOOL_OTHER = SUBSTRING(CDSF.DESCRIPTION, 1, 79)
    FROM Custom_Degree
    LEFT JOIN _custom_degree_schools_fix CDSF ON CDSF.IMIS_CODE = ACCRED_SCHOOLS AND 
                                                    CDSF.TABLE_NAME = 'ALL_SCHOOLS' AND
                                                    CDSF.ID = '000000' AND
                                                    CDSF.IMIS_CODE IS NOT NULL
    WHERE Custom_Degree.SCHOOL_OTHER = '' AND CDSF.DESCRIPTION IS NOT NULL
     
    -- for accredited schools
    UPDATE Custom_Degree
    SET SCHOOL_OTHER = SUBSTRING(CDSF.DESCRIPTION, 1, 79)
    FROM Custom_Degree
    LEFT JOIN _custom_degree_schools_fix CDSF ON CDSF.IMIS_CODE = ACCRED_SCHOOLS AND 
                                                    CDSF.TABLE_NAME = 'ACCRED_SCHOOLS' AND
                                                    CDSF.ID = '000000' AND
                                                    CDSF.IMIS_CODE IS NOT NULL
    WHERE Custom_Degree.SCHOOL_OTHER = '' AND CDSF.DESCRIPTION IS NOT NULL

    -- for all those we couldn't get school information for... simply update the school name from the appropriate table
    UPDATE Custom_Degree
    SET SCHOOL_OTHER = SUBSTRING(GT.[DESCRIPTION], 1,79)
    FROM Custom_Degree
    INNER JOIN Gen_Tables GT ON GT.CODE = Custom_Degree.ACCRED_SCHOOLS
                                AND GT.TABLE_NAME = 'ACCRED_SCHOOLS'
    WHERE (SCHOOL_OTHER = '' OR SCHOOL_OTHER IS NULL)

    UPDATE Custom_Degree
    SET SCHOOL_OTHER = SUBSTRING(GT.[DESCRIPTION], 1,79)
    FROM Custom_Degree
    INNER JOIN Gen_Tables GT ON GT.CODE = Custom_Degree.ALL_SCHOOLS
                                AND GT.TABLE_NAME = 'ALL_SCHOOLS'
    WHERE (SCHOOL_OTHER = '' OR SCHOOL_OTHER IS NULL)


    update Custom_Degree
    SET SCHOOL_OTHER = N.COMPANY,
    Custom_Degree.SCHOOL_ID = CASE WHEN CSA.ID IS NOT NULL THEN Custom_Degree.SCHOOL_OTHER ELSE '' END
    FROM Custom_Degree
    INNER JOIN Name N ON N.ID = Custom_Degree.SCHOOL_ID
    LEFT JOIN Custom_SchoolAccredited CSA ON CSA.ID = Custom_Degree.SCHOOL_ID
    WHERE Custom_Degree.SCHOOL_OTHER = '' and Custom_Degree.SCHOOL_ID != ''

    -- finally, delete any school records we could not add school data for
    delete from Custom_Degree
    where SCHOOL_OTHER = ''

3. run sync to update degrees to imis from django

"""
def update_degrees_to_imis():
    # function to copy school data into iMIS (if it doesn't already exist)
    # then copies free student school data into django

    ed = EducationalDegree.objects.filter(seqn__isnull=True)

    #ed = EducationalDegree.objects.filter(contact__user__username__in=['279264','265330','254176','211949','339772','339750','339714'])
    #ed = EducationalDegree.objects.filter(contact__user__username__in=['123462'])
    
    print("processing {0} degrees in Django to iMIS".format(ed.count()))
    
    errors_log = {} 
    imis_degrees_total = str(ed.count())
    school_id_exists_update_imis_total = 0
    not_school_id_exists_update_imis_total = 0
    school_other_exists_update_imis_total = 0
    not_school_other_exists_update_imis_total = 0
    clean_update_school_with_school_seqn_total = 0
    clean_remove_school_id_accred_total = 0
    deleted_school = 0
    invalid_seqn = 0
    skip_seqn = 0

    accredited_schools= CustomSchoolaccredited.objects.all().values_list("id", flat=True)
    accred_school_dict = {}

    all_schools = Name.objects.filter(member_type='SCH').values_list("id", flat=True)
    all_school_dict = {}

    # get accredited school names!
    for school in accredited_schools:
        accred_school_dict[school] = Name.objects.get(id=school).company

    # get all school names
    for school in all_schools:
        all_school_dict[school] = Name.objects.get(id=school).company


    for index, x in enumerate(ed):
        try:
            school_name = ""
            school_id = None
            graduation_date = None
            imis_degree = None
            user_id = x.contact.user.username
            print("processing degree {0} of {1}".format(str(index), ed.count()))

            # to follow:
            # 1. if the school is accredited, show the school id.
            # if the school is not accredited, remove the school id.

            # 2. if the school has a seqn, update imis with the school information
            # if there is no seqn, search for a degree that matches. if no degree matches, create a new one

            if x.school:
                print("school found")
                school_id = x.school.user.username
                school_name = x.school.company
            else:
                school_name = x.other_school

            if x.seqn == 0:
                x.seqn = None

            if x.graduation_date:
                # utc graduation date
                graduation_date = datetime.datetime(year=x.graduation_date.year, month=x.graduation_date.month, day=1, tzinfo=pytz.utc)

            # SEQN test. if does not exist, create a new iMIS degree
            if x.seqn:
                try:
                    imis_degree = CustomDegree.objects.get(id=user_id, seqn=x.seqn)

                    print("imis seqn exists. SKIP update.")
                    skip_seqn += 0

                except:
                    print("imis degree doesn't exist with the same seqn number... clear out the seqn")
                    invalid_seqn += 0

                    # set x seqn to none so we can create a new degree
                    x.seqn = None
                    continue

            # no linked degree in iMIS
            if not x.seqn:
                # if user's imis degree has the same school and degree level, we update graduation date and is planning.        
                if school_id:   

                    imis_degree = CustomDegree.objects.filter(id=user_id, degree_level=x.level, school_id = school_id).first()

                    if imis_degree:
                        print("school_id degree exists in iMIS- updating graduation date and degree complete information.")
                        school_id_exists_update_imis_total += 1

                    else:
                        print("school_id degree in iMIS does NOT exist. new degree object being created in iMIS.")
                        imis_degree = CustomDegree.objects.create(id=user_id, school_id=school_id)
                        not_school_id_exists_update_imis_total += 1
                    
                # no school attached to the educational degree record. try to find by other school and degree level
                else:
                    imis_degree = CustomDegree.objects.filter(id=x.contact.user.username, degree_level=x.level, school_other = x.other_school).first()

                    if imis_degree:
                        print("degree exists for untracked school in iMIS- updating graduation date and degree complete information")
                        school_other_exists_update_imis_total +=1
                    else:
                        print("new degree object being created in iMIS for untracked school.")
                        imis_degree = CustomDegree.objects.create(id=user_id, school_other=x.other_school)
                        not_school_other_exists_update_imis_total += 1

            if imis_degree is not None and not x.seqn:

                if school_id and school_id in accred_school_dict:
                    imis_degree.school_id = school_id
                    imis_degree.school_other = x.other_school = accred_school_dict[school_id]

                elif school_id and school_id in all_school_dict:
                    imis_degree.school_id = ""
                    x.school = None
                    imis_degree.school_other = x.other_school = all_school_dict[school_id]
                    x.school = None
                else:
                    imis_degree.school_id = ""
                    imis_degree.school_other = x.other_school
                    x.school = None

                # remove accredited program and degree program fields for those that are not synced

                imis_degree.accredited_program = ""
                imis_degree.degree_program = ""
                x.program = ""

                imis_degree.degree_level=x.level
                imis_degree.degree_date=graduation_date
                imis_degree.degree_planning=x.is_planning
                imis_degree.degree_complete = x.complete
                x.seqn = imis_degree.seqn
                
                x.save()
                imis_degree.save()      

        except Exception as e:
            print("error!: " + str(e))
            errors_log[x.id] = str(e)
            continue

    print("ERRORS")
    print(str(errors_log))
    print("------------------------------------------")
    print("------------------------------------------")
    print("imis degrees total: " + imis_degrees_total)
    print("school id exists. update degree info total: " + str(school_id_exists_update_imis_total))
    print("school id does not exist. create degree info total: " + str(not_school_id_exists_update_imis_total))
    print("school other exists for untracked school total: " + str(school_other_exists_update_imis_total))
    print("school other does not exist for untracked school total: " + str(not_school_other_exists_update_imis_total))
    print("schools deleted (did not contain a school_id or text for other_school" + str(deleted_school))
    print("invalid seqn numbers: " + str(invalid_seqn))
    print("seqn exists in imis. skipped update. : " + str(skip_seqn))

    print("------------------------------------------")

    print("records cleaned")
    print("cleaned records should match school_id exists results")
    print("school seqn does not exist. update imis and django with seqn total : " + str(clean_update_school_with_school_seqn_total))
    print("removed school_id and replaced with school_other total: " + str(clean_remove_school_id_accred_total))

def update_schools_to_django():

    # function to copy free student school data into django (if it doesn't already exist)

    cd = CustomDegree.objects.all()
    #cd = CustomDegree.objects.filter(id__in=['123462'])

    print("processing {0} degrees in iMIS to Django.".format(cd.count()))

    django_degree_exists_update_total = 0
    not_django_degree_exists_update_total = 0
    invalid_seqn = 0
    degree_seqn_exists = 0

    error_logs = {}

    accredited_schools= CustomSchoolaccredited.objects.all().values_list("id", flat=True)
    accred_school_dict = {}

    all_schools = Name.objects.filter(member_type='SCH').values_list("id", flat=True)
    all_school_dict = {}

    accredited_school_programs= CustomSchoolaccredited.objects.all().values_list("seqn", flat=True)
    accred_school_program_dict = {}

    for seqn in accredited_school_programs:
        accred_school_program_dict[seqn] = CustomSchoolaccredited.objects.get(seqn=seqn).degree_program
    # get accredited school names!
    for school in accredited_schools:
        accred_school_dict[school] = Name.objects.get(id=school).company

    # get all school names
    for school in all_schools:
        all_school_dict[school] = Name.objects.get(id=school).company


    # create degrees from django into iMIS
    for index, x in enumerate(cd):
        try:
            print("processing degree {0} of {1}".format(str(index), cd.count()))
            
            school = None
            degree_date = None
            django_degree = None
            accredited_school = None
            school_name = ""
            school_id = ""
            contact = None

            Contact.update_or_create_from_imis(username=x.id)
            contact = Contact.objects.get(user__username=x.id)
            
            school_id = x.school_id

            if x.school_id == "0":
                school_id = ""

            if school_id != "":
                school = School.objects.filter(user__username=x.school_id).first()

                if school:
                    school_name = school.company
                else:
                    school_name = x.school_other

            if x.degree_date:
                degree_date = datetime.datetime(year=x.degree_date.year, month=x.degree_date.month, day=1)

            # first try to get the degree by seqn number
            django_degree_seqn = EducationalDegree.objects.filter(seqn = x.seqn).first()
              
            if not django_degree_seqn and contact is not None:  
                django_degree = EducationalDegree.objects.filter(contact__user__username=x.id, level=x.degree_level, school = school).exclude(school__isnull=True).first()
            
                if not django_degree:
                    django_degree = EducationalDegree.objects.filter(contact__user__username=x.id, level=x.degree_level,other_school = x.school_other).exclude(school__isnull=True).first()
                    
                if django_degree:
                    django_degree_exists_update_total += 1
                    # if the django degree exists, django would have the updated information! update iMIS.
                    print("degree exists in django - updating graduation date and degree complete information to iMIS")
                else:
                    print("new degree object being created in Django.")
                    not_django_degree_exists_update_total += 1
                    django_degree, created = EducationalDegree.objects.get_or_create(seqn=x.seqn, contact=contact, school=school)
            
                    if django_degree:
                        django_degree.graduation_date = degree_date
                        django_degree.is_planning = x.degree_planning
                        django_degree.complete = x.degree_complete
                        django_degree.level = x.degree_level

                        if x.school_seqn:
                            x.degree_program = ""
                            x.accredited_program = accred_school_program_dict[x.school_seqn]
                        else:
                            x.accredited_program = ""

                        # means the record was created AFTER the rollout. clear out degree program and accredited program fields
                        if created:
                            x.degree_program = ""

                            if x.school_seqn == 0:
                                x.accredited_program = ""
                        
                        if school_id in accred_school_dict:
                            django_degree.school = school
                            django_degree.other_school = accred_school_dict[school_id]
                            x.school_other = accred_school_dict[school_id]
                            x.school_id = school_id

                        elif school_id in all_school_dict:
                            x.school_other = all_school_dict[school_id]
                            x.school_id = ""
                            django_degree.school = None
                            django_degree.school_other = all_school_dict[school_id]

                        else:
                            django_degree.other_school = x.school_other
                            django_degree.school = None
                            x.school_id = ""
                    
                if django_degree:
                    django_degree.save()
                
                x.save()
            elif contact is None:
                print("no contact...odd")
                no_contact += 1

            else:
                print("django degree exists! skipping.")
                degree_seqn_exists += 1

        except Exception as e:
            print(e)
            print(x.id + " user name")
            error_logs[x.id] = str(e)
            continue
    print("--------------------------------------")
    print("ERRORS: " + str(error_logs))
    print("--------------------------------------")
    print(" django degree exists - required update total: " + str(django_degree_exists_update_total))
    print("django degree did not exist. new degree created total: " + str(not_django_degree_exists_update_total))
    print("invalid seqn: " + str(invalid_seqn))
    print("degree exists. skipped import: " + str(degree_seqn_exists))
    print("no contact: " + str(no_contact))

def archive_convert_records():
    # creates archive records for the converted students and new members
    # run this AFTER degree information has been synced across django and iMIS!!!

    # Counts might not match... converted students who should have been dropped
    # NOTE: Chapter counts might not match (international students no chapter)
    # NOTE: Schools might not match (converted student did not have a school record)

    converted_date = datetime.datetime(year=2017, month=7, day=9, tzinfo=pytz.utc)
    student_id_list = IndDemographics.objects.filter(student_start_date=converted_date).values_list("id", flat=True)
    nm_id_list = IndDemographics.objects.filter(new_member_start_date=converted_date).values_list("id", flat=True)
    students = Name.objects.filter(id__in=student_id_list).exclude(category='NM1')
    new_members = Name.objects.filter(id__in=nm_id_list)
    
    students_count = students.count()
    new_members_count = new_members.count()

    program_year = 1
    previously_student = True

    student_no_chapter_count = 0
    student_no_school_count = 0
    new_member_no_chapter_count = 0

    student_errors = {}
    new_member_errors = {}

    for index, name in enumerate(students):
        try:
            print("archiving student {0} of {1}".format(str(index), str(students_count)))

            imis_chapter_product_code = ""

            if name.chapter and name.chapter != "":
                imis_chapter_product_code = "CHAPT/" + name.chapter
            else:
                student_no_chapter_count += 1

            # archive dues / division / chapter
            subscriptions = Subscriptions.objects.filter(Q(id=name.id), Q(status="A"), Q(paid_thru__gte=datetime.datetime.now()), Q(product_code__in=["APA",imis_chapter_product_code]) | Q(prod_type='SEC'))
            for subscription in subscriptions:
                if subscription.product_code == "APA":
                    activity_type = ImisActivity.get_activity_type(record_type="RENEW", name=name, program_type="student_new_members")
                else:
                    activity_type = ImisActivity.get_activity_type(record_type=subscription.prod_type, name=name, program_type="student_new_members")

                subscription.create_activity(activity_type = activity_type, name=name, program_year=program_year, previously_student=previously_student)

            # if student does not have a primary chapter subscription, add no chapter archive record
            # if imis_chapter_product_code == "":
            #   activity_type = "STU_CHAPT"
            #   Activity.objects.create(id=name.id, activity_type=activity_type, member_type=n.member_type, other_code='STU', product_code="NO_CHAPTER", thru_date=datetime.datetime.now(), uf_4=program_year, description="Student subscription in join/renew")

            # archive advocacy
            advocacy, created = Advocacy.objects.get_or_create(id=name.id)
            activity_type_pan = ImisActivity.get_activity_type(name=name, record_type="PAN", program_type="student_new_members")
            advocacy_action_code = "ADD"
            
            if not advocacy.grassrootsmember:
                advocacy_action_code = "DROP"

            advocacy.create_activity(activity_type = activity_type_pan, name=name, program_year=program_year, previously_student=previously_student, action_codes=advocacy_action_code)
        
            # archive school - get the last created school record
            custom_degree = CustomDegree.objects.filter(id=name.id).last()

            if custom_degree:
                activity_type = ImisActivity.get_activity_type(record_type="SCH", name=name, program_type="student_new_members")
                custom_degree.create_activity(activity_type = activity_type, name=name, program_year=program_year, previously_student=previously_student, program_type="student_new_members")
            else:
                student_no_school_count += 1

        except Exception as e:
            print("ERRROR" + str(e))
            student_errors[name.id] = str(e)
            continue

    # for index, name in enumerate(new_members):
    #     try:
    #         print("archiving new member {0} of {1}".format(str(index), str(new_members_count)))
                    
    #         imis_chapter_product_code = ""
            
    #         # only primary chapter is archived
    #         if name.chapter and name.chapter != "":
    #             imis_chapter_product_code = "CHAPT/" + name.chapter
    #         else:
    #             new_member_no_chapter_count += 1

    #         # archive APA, primary chapter, and all division subscriptions
    #         subscriptions = Subscriptions.objects.filter(Q(id=name.id), Q(status="A"), Q(paid_thru__gte=datetime.datetime.now()), Q(product_code__in=["APA",imis_chapter_product_code]) | Q(prod_type='SEC'))

    #         for subscription in subscriptions:
    #             if subscription.product_code == "APA":
    #                 activity_type = ImisActivity.get_activity_type(record_type="RENEW", name=name, program_type="student_new_members")
    #             else:
    #                 activity_type = ImisActivity.get_activity_type(record_type=subscription.prod_type, name=name, program_type="student_new_members")

    #             subscription.create_activity(activity_type = activity_type, name=name, program_year=program_year, previously_student=previously_student)

    #         # archive advocacy
    #         advocacy, created = Advocacy.objects.get_or_create(id=name.id)
    #         activity_type_pan = ImisActivity.get_activity_type(name=name, record_type="PAN", program_type="student_new_members")
    #         advocacy_action_code = "ADD"
            
    #         if not advocacy.grassrootsmember:
    #             advocacy_action_code = "DROP"

    #         advocacy.create_activity(activity_type = activity_type_pan, name=name, program_year=program_year, previously_student=previously_student, action_codes=advocacy_action_code)
        
    #     except Exception as e:
    #         print("ERRROR" + str(e))
    #         new_member_errors[name.id] = str(e)
            continue

    print("student errors")
    print(str(student_errors))
    print("-------------------")
    # print("new member errors")
    # print(str(new_member_errors))
    print("--------------------")
    print("stats")
    print("students imported: {0}".format(str(students_count)))
    # print("new members imported: {0}".format(str(new_members_count)))
    print("students without chapters archived: {0}".format(str(student_no_chapter_count)))
    print("students without schools archived: {0}".format(str(student_no_school_count)))
    # print("new member without chapters archived: {0}".format(str(new_member_no_chapter_count)))


def create_drop_data():
    """
    creates dummy drop data that we can use to test reporting
    """

    names = Name.objects.filter(id__in=['158658','181714','223799','231988','234008','238220','247971','248024','251741','258147'])
    
    for name in names:
        print("creating drop data for: " + str(name.id))
        
        ind_demographics = IndDemographics.objects.get(id=name.id)       
        program_year = 1

        current_date_utc = datetime.datetime(year=datetime.datetime.now().year, month=datetime.datetime.now().month, day=datetime.datetime.now().day, tzinfo=pytz.utc)
        if name.member_type == "STU":
            ind_demographics.is_current_student = 1

            # begin student start date if none exist
            program_year = ind_demographics.student_program_year = ind_demographics.student_program_year + 1

            if program_year == 1:
                ind_demographics.student_start_date = current_date_utc
        else:
            ind_demographics.is_current_student = 0

            if name.category == "NM1":
                # reset the student_program_year counter when a student has moved to new member
                ind_demographics.student_program_year = 0
                ind_demographics.new_member_start_date = current_date_utc

            elif name.category == "NM2":
                program_year = 2

        ind_demographics.save()

        previously_student = True if ind_demographics.student_start_date else False

        # we only want the membership, primary chapter, and division subscription products
        imis_chapter_product_code = "CHAPT/" + name.chapter
        # purchase_subscriptions = list(Purchase.objects.filter(Q(order=self), Q(product__imis_code__in=["APA", imis_chapter_product_code]) | Q(product__product_type="DIVISION")).values_list("product__imis_code", flat=True))

        imis_subscriptions = Subscriptions.objects.filter(id=name.id)

        for subscription in imis_subscriptions:
            try:
                if subscription.product_code == "APA":
                    activity_type = ImisActivity.get_activity_type(record_type="RENEW", name=name, program_type="student_new_members")
                else:
                    activity_type = ImisActivity.get_activity_type(record_type=subscription.prod_type, name=name, program_type="student_new_members")
                
                subscription.create_activity(activity_type = activity_type, name=name, program_year=program_year, previously_student=previously_student)
            except Exception as e:
                print(str(e))
                continue

        try:
            custom_degree = CustomDegree.objects.filter(id=name.id).first()

            if custom_degree:
                activity_type = ImisActivity.get_activity_type(record_type="SCH", name=name, program_type="student_new_members")
                custom_degree.create_activity(activity_type = activity_type, name=name, program_year=program_year, previously_student=previously_student, program_type="student_new_members")
        except Exception as e:
            print(str(e))

        try:
            advocacy, created = Advocacy.objects.get_or_create(id=name.id)
            activity_type_pan = ImisActivity.get_activity_type(name=name, record_type="PAN", program_type="student_new_members")
            advocacy_action_codes = "ADD"

            if not advocacy.grassrootsmember:
                advocacy_action_codes = "DROP"

            advocacy.create_activity(activity_type = activity_type_pan, name=name, program_year=program_year, previously_student=previously_student, action_codes=advocacy_action_codes)
        
        except Exception as e:
            print(str(e))