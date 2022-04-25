from imis.models import *
from imis.models import Activity as ImisActivity

def converted_student_metrics_fix():
    """
    This method is intended to scan and correct any converted student activity records
    FSTU_CNVRT was created on launch. these are confirmed good.
    STU_CNVRT needs to be checked.
    """
    converted_students = Activity.objects.filter(id='318410', activity_type__in=['FSTU_CNVRT','STU_CNVRT']).values_list('id',flat=True)

    transaction_date = datetime.datetime(year=2017, month=7, day=9, tzinfo=pytz.utc)
    current_date_utc = datetime.datetime(year=datetime.datetime.now().year, month=datetime.datetime.now().month, day=datetime.datetime.now().day, tzinfo=pytz.utc)
    program_year = 1
    previously_student = True
    print("{0} students will be updated".format(str(len(converted_students))))

    for student_id in converted_students:
        
        print("updating student id: {0}".format(student_id))

        name = Name.objects.get(id=student_id)
        ind_demographics = IndDemographics.objects.get(id=student_id)
        activities = Activity.objects.filter(id=student_id, activity_type__in=['STU_RENEW','STU_CHAPT','STU_SEC','STU_PAN'])
        subscriptions = Subscriptions.objects.filter(id=student_id, status='A', prod_type__in=['DUES','SEC','CHAPT'])

        # only update the name. verify demographics information is correct
        if name.member_type == 'STU':
            ind_demographics.student_program_year = 1
            ind_demographics.student_start_date = transaction_date
            ind_demographics.new_member_start_date = None
            ind_demographics.is_current_student = 1
            ind_demographics.save()
            
            # remove and re-add activity records to match renew date. DO NOT ADD SCHOOL AS THESE ARE INCOMPLETE.
            if activities:
                activities.delete()

            for subscription in subscriptions:
                if subscription.product_code == "APA":
                    activity_type = ImisActivity.get_activity_type(record_type="RENEW", name=name, program_type="student_new_members")
                else:
                    activity_type = ImisActivity.get_activity_type(record_type=subscription.prod_type, name=name, program_type="student_new_members")
                
                subscription.create_activity(activity_type = activity_type, name=name, program_year=program_year, previously_student=previously_student, transaction_date=transaction_date) 

            # re-create advocacy record
            advocacy, created = Advocacy.objects.get_or_create(id=name.id)
            activity_type_pan = ImisActivity.get_activity_type(name=name, record_type="PAN", program_type="student_new_members")
            advocacy_action_codes = "ADD"

            if not advocacy.grassrootsmember:
                advocacy_action_codes = "DROP"

            advocacy.create_activity(activity_type = activity_type_pan, name=name, program_year=program_year, previously_student=previously_student, action_codes=advocacy_action_codes, transaction_date=transaction_date)
            
            new_activities = Activity.objects.filter(id=student_id, activity_type__in=['STU_RENEW','STU_CHAPT','STU_SEC','STU_SCH','STU_PAN'])

            for activity in new_activities:
                activity.transaction_date = transaction_date
                activity.effective_date = transaction_date
                activity.save()

        # this is not a student. should be safe to remove any activity records 
        else:
            if activities:
                activities.delete()

def converted_np_metrics_fix():
    """
    This method will scan and correct any converted new professional activity records
    """
    pass

def student_metrics_fix():
    """
    This method is intended to scan and correct any new student activity records
    """
    pass

def np_metrics_fix():
    """
    This method will scan and correct any new new professional activity records
    """
    pass


def add_missing_activity_records():

    converted_students = Activity.objects.filter(activity_type__in=['FSTU_CNVRT','STU_CNVRT']).values_list('id',flat=True)
    renew_students = Activity.objects.filter(activity_type='STU_RENEW').values_list('id',flat=True)
    student_records = Name.objects.filter(member_type='STU').values_list('id',flat=True)

    # for the converted students, if there is not a renew students record...

    for x in converted_students:
        if x not in renew_students and x in student_records:
            print("adding activity records for id {0}".format(str(x)))

            name = Name.objects.get(id=x)
            ind_demographics = IndDemographics.objects.get(id=x)       

            program_year = 1
            ind_demographics.is_current_student = 1
            ind_demographics.student_program_year = 1
            ind_demographics.student_start_date = '2017-07-09'
            ind_demographics.save()

            previously_student = True if ind_demographics.student_start_date else False

            # we only want the membership, primary chapter, and division subscription products
            imis_chapter_product_code = "CHAPT/" + name.chapter
            imis_subscriptions = Subscriptions.objects.filter(id=name.id, status='A')

            transaction_date = datetime.datetime(year=2017, month=7, day=9, tzinfo=pytz.utc)
            todays_date = datetime.datetime(year=datetime.datetime.now().year, month=datetime.datetime.now().month, day=datetime.datetime.now().day, tzinfo=pytz.utc)
          
            for subscription in imis_subscriptions:
                try:
                    if subscription.product_code == "APA":
                        activity_type = ImisActivity.get_activity_type(record_type="RENEW", name=name, program_type="student_new_members")
                    else:
                        activity_type = ImisActivity.get_activity_type(record_type=subscription.prod_type, name=name, program_type="student_new_members")
                    
                    subscription.create_activity(activity_type = activity_type, name=name, program_year=program_year, previously_student=previously_student, transaction_date=transaction_date)
                except Exception as e:
                    print(str(e))
                    continue

            try:
                custom_degree = CustomDegree.objects.filter(id=name.id, is_current=True).first()

                if custom_degree:
                    activity_type = ImisActivity.get_activity_type(record_type="SCH", name=name, program_type="student_new_members")
                    custom_degree.create_activity(activity_type = activity_type, name=name, program_year=program_year, previously_student=previously_student, program_type="student_new_members", transaction_date=transaction_date)
            except Exception as e:
                print(str(e))

            try:
                advocacy, created = Advocacy.objects.get_or_create(id=name.id)
                activity_type_pan = ImisActivity.get_activity_type(name=name, record_type="PAN", program_type="student_new_members")
                advocacy_action_codes = "ADD"

                if not advocacy.grassrootsmember:
                    advocacy_action_codes = "DROP"

                advocacy.create_activity(activity_type = activity_type_pan, name=name, program_year=program_year, previously_student=previously_student, action_codes=advocacy_action_codes, transaction_date=transaction_date)
            
                new_activities = Activity.objects.filter(id=x, activity_type__in=['STU_RENEW','STU_CHAPT','STU_SEC','STU_SCH','STU_PAN'], transaction_date=todays_date)

                for activity in new_activities:
                    activity.transaction_date = transaction_date
                    activity.effective_date = transaction_date
                    activity.save()

            except Exception as e:
                print(str(e))


def add_missing_student_activity_records():

    renew_students = Activity.objects.filter(activity_type='STU_RENEW').values_list('id',flat=True)
    student_records = Name.objects.filter(member_type='STU').values_list('id',flat=True)

    # for the converted students, if there is not a renew students record...

    for x in student_records:
        if x not in renew_students:
            print("adding activity records for id {0}".format(str(x)))

            name = Name.objects.get(id=x)
            join_date = name.join_date
            ind_demographics = IndDemographics.objects.get(id=x)       

            program_year = 1
            ind_demographics.is_current_student = 1
            ind_demographics.student_program_year = 1
            ind_demographics.student_start_date = join_date
            ind_demographics.save()

            previously_student = True if ind_demographics.student_start_date else False

            # we only want the membership, primary chapter, and division subscription products
            imis_chapter_product_code = "CHAPT/" + name.chapter
            imis_subscriptions = Subscriptions.objects.filter(id=name.id, status='A')

            transaction_date = join_date
            todays_date = datetime.datetime(year=datetime.datetime.now().year, month=datetime.datetime.now().month, day=datetime.datetime.now().day, tzinfo=pytz.utc)
          
            for subscription in imis_subscriptions:
                try:
                    if subscription.product_code == "APA":
                        activity_type = ImisActivity.get_activity_type(record_type="RENEW", name=name, program_type="student_new_members")
                    else:
                        activity_type = ImisActivity.get_activity_type(record_type=subscription.prod_type, name=name, program_type="student_new_members")
                    
                    subscription.create_activity(activity_type = activity_type, name=name, program_year=program_year, previously_student=previously_student, transaction_date=transaction_date)
                except Exception as e:
                    print(str(e))
                    continue

            try:
                custom_degree = CustomDegree.objects.filter(id=name.id, is_current=True).first()

                if custom_degree:
                    activity_type = ImisActivity.get_activity_type(record_type="SCH", name=name, program_type="student_new_members")
                    custom_degree.create_activity(activity_type = activity_type, name=name, program_year=program_year, previously_student=previously_student, program_type="student_new_members", transaction_date=transaction_date)
            except Exception as e:
                print(str(e))

            try:
                advocacy, created = Advocacy.objects.get_or_create(id=name.id)
                activity_type_pan = ImisActivity.get_activity_type(name=name, record_type="PAN", program_type="student_new_members")
                advocacy_action_codes = "ADD"

                if not advocacy.grassrootsmember:
                    advocacy_action_codes = "DROP"

                advocacy.create_activity(activity_type = activity_type_pan, name=name, program_year=program_year, previously_student=previously_student, action_codes=advocacy_action_codes, transaction_date=transaction_date)
            
                new_activities = Activity.objects.filter(id=x, activity_type__in=['STU_RENEW','STU_CHAPT','STU_SEC','STU_SCH','STU_PAN'], transaction_date=todays_date)

                for activity in new_activities:
                    activity.transaction_date = transaction_date
                    activity.effective_date = transaction_date
                    activity.save()

            except Exception as e:
                print(str(e))

def add_missing_activity_records(username):

    # NOTE: THIS WILL ONLY WORK FOR FIRST YEAR STUDENTS / NEW MEMBERS!
    x = username
    print("adding activity records for id {0}".format(str(x)))

    name = Name.objects.get(id=x)
    join_date = Subscriptions.objects.get(id=x, product_code='APA', status='A').payment_date
    ind_demographics = IndDemographics.objects.get(id=x)       


    program_year = 1
    # Assume student (no one should be in program year 2)
    if name.member_type == 'STU':
        ind_demographics.is_current_student = 1
        ind_demographics.student_program_year = 1
        # assumes the student start date is the payment date
        ind_demographics.student_start_date = join_date


    else:
        ind_demographics.is_current_student = 0
        ind_demographics.student_program_year = 0
        # assume the new member start date is the payment date
        ind_demographics.new_member_start_date = join_date
    ind_demographics.save()

    previously_student = True if ind_demographics.student_start_date else False

    # we only want the membership, primary chapter, and division subscription products
    imis_chapter_product_code = "CHAPT/" + name.chapter
    imis_subscriptions = Subscriptions.objects.filter(id=name.id, status='A')
    transaction_date = join_date

    todays_date = datetime.datetime(year=datetime.datetime.now().year, month=datetime.datetime.now().month, day=datetime.datetime.now().day, tzinfo=pytz.utc)
  
    for subscription in imis_subscriptions:
        try:
            if subscription.product_code == "APA":
                activity_type = ImisActivity.get_activity_type(record_type="RENEW", name=name, program_type="student_new_members")
            else:
                activity_type = ImisActivity.get_activity_type(record_type=subscription.prod_type, name=name, program_type="student_new_members")
            
            subscription.create_activity(activity_type = activity_type, name=name, program_year=program_year, previously_student=previously_student, transaction_date=transaction_date)
        except Exception as e:
            print(str(e))
            continue

    try:
        custom_degree = CustomDegree.objects.filter(id=name.id, is_current=True).first()

        if custom_degree:
            activity_type = ImisActivity.get_activity_type(record_type="SCH", name=name, program_type="student_new_members")
            custom_degree.create_activity(activity_type = activity_type, name=name, program_year=program_year, previously_student=previously_student, program_type="student_new_members", transaction_date=transaction_date)
    except Exception as e:
        print(str(e))

    try:
        advocacy, created = Advocacy.objects.get_or_create(id=name.id)
        activity_type_pan = ImisActivity.get_activity_type(name=name, record_type="PAN", program_type="student_new_members")
        advocacy_action_codes = "ADD"

        if not advocacy.grassrootsmember:
            advocacy_action_codes = "DROP"

        advocacy.create_activity(activity_type = activity_type_pan, name=name, program_year=program_year, previously_student=previously_student, action_codes=advocacy_action_codes, transaction_date=transaction_date)
    
        new_activities = Activity.objects.filter(id=x, activity_type__in=['STU_RENEW','STU_CHAPT','STU_SEC','STU_SCH','STU_PAN'], transaction_date=todays_date)

        for activity in new_activities:
            activity.transaction_date = transaction_date
            activity.effective_date = transaction_date
            activity.save()

    except Exception as e:
        print(str(e))

def add_nm_records():

    # NOTE: THIS WILL ONLY WORK FOR FIRST YEAR STUDENTS / NEW MEMBERS!

    nm = Name.objects.filter(category='NM1', member_type='MEM').values_list('id', flat=True)
    current_date_utc = datetime.datetime(year=datetime.datetime.now().year, month=datetime.datetime.now().month, day=datetime.datetime.now().day, tzinfo=pytz.utc)

    active_apa_subscriptions = Subscriptions.objects.filter(product_code='APA', status='A', paid_thru__gte=current_date_utc).values_list('id', flat=True)

    nm_activity_records = Activity.objects.filter(activity_type='NM_RENEW').values_list('id', flat=True)
    missing_counter = 0
    for x in nm:
        if x in active_apa_subscriptions:
            if x not in nm_activity_records:

                print("adding activity records for id {0}".format(str(x)))

                name = Name.objects.get(id=x)
                transaction_date = Subscriptions.objects.get(id=x, product_code='APA', status='A').payment_date
                ind_demographics = IndDemographics.objects.get(id=x)       


                program_year = 1
                # Assume student (no one should be in program year 2)
                if name.member_type == 'STU':
                    ind_demographics.is_current_student = 1
                    ind_demographics.student_program_year = 1
                    # assumes the student start date is the payment date
                    ind_demographics.student_start_date = transaction_date


                elif name.category == 'NM1':
                    ind_demographics.is_current_student = 0
                    ind_demographics.student_program_year = 0
                    # assume the new member start date is the payment date
                    ind_demographics.new_member_start_date = transaction_date
                ind_demographics.save()

                previously_student = True if ind_demographics.student_start_date else False

                # we only want the membership, primary chapter, and division subscription products
                imis_chapter_product_code = "CHAPT/" + name.chapter
                imis_subscriptions = Subscriptions.objects.filter(id=name.id, status='A', paid_thru__gte=current_date_utc)
                
                todays_date = datetime.datetime(year=datetime.datetime.now().year, month=datetime.datetime.now().month, day=datetime.datetime.now().day, tzinfo=pytz.utc)
              
                for subscription in imis_subscriptions:
                    try:
                        if subscription.product_code == "APA":
                            activity_type = ImisActivity.get_activity_type(record_type="RENEW", name=name, program_type="student_new_members")
                        else:
                            activity_type = ImisActivity.get_activity_type(record_type=subscription.prod_type, name=name, program_type="student_new_members")
                        
                        subscription.create_activity(activity_type = activity_type, name=name, program_year=program_year, previously_student=previously_student, transaction_date=transaction_date)
                    except Exception as e:
                        print(str(e))
                        continue

                try:
                    custom_degree = CustomDegree.objects.filter(id=name.id, is_current=True).first()

                    if custom_degree:
                        activity_type = ImisActivity.get_activity_type(record_type="SCH", name=name, program_type="student_new_members")
                        custom_degree.create_activity(activity_type = activity_type, name=name, program_year=program_year, previously_student=previously_student, program_type="student_new_members", transaction_date=transaction_date)
                except Exception as e:
                    print(str(e))

                try:
                    advocacy, created = Advocacy.objects.get_or_create(id=name.id)
                    activity_type_pan = ImisActivity.get_activity_type(name=name, record_type="PAN", program_type="student_new_members")
                    advocacy_action_codes = "ADD"

                    if not advocacy.grassrootsmember:
                        advocacy_action_codes = "DROP"

                    advocacy.create_activity(activity_type = activity_type_pan, name=name, program_year=program_year, previously_student=previously_student, action_codes=advocacy_action_codes, transaction_date=transaction_date)
                
                    new_activities = Activity.objects.filter(id=x, activity_type__in=['STU_RENEW','STU_CHAPT','STU_SEC','STU_SCH','STU_PAN','NM_RENEW','NM_CHAPT','NM_SEC','NM_PAN','MEM_RENEW','MEM_CHAPT','MEM_SEC','MEM_PAN'], transaction_date=current_date_utc)

                    for activity in new_activities:
                        activity.transaction_date = transaction_date
                        activity.effective_date = transaction_date
                        activity.save()

                except Exception as e:
                    print(str(e))
