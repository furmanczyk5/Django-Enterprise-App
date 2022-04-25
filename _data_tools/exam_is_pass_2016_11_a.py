import django
django.setup()
import json, urllib
import requests
from myapa.models import *
from exam.models import *

node_url = "http://localhost:8081/dataimport/"



def import_is_pass():
    exam_codes = [
    '2000MAY',
    '2001MAY',
    '2002MAY',
    '2003MAY',
    '2004MAY', '2004NOV', 
    '2005MAY', '2005NOV', 
    '2006MAY', '2006NOV', 
    '2007MAY', '2007NOV', 
    '2008MAY', '2008NOV',
    '2009MAY', '2009NOV', 
    '2010MAY', '2010NOV', 
    '2011MAY', '2011NOV', '2011ASC', 
    '2012MAY', '2012NOV', '2012ASC',
    '2013NOV', '2013MAY', '2013ASC',
    '2014MAY', '2014NOV', '2014ASC', 
    '2015MAY', '2015NOV', '2015ASC', 
    '2016ASC', '2016MAY', '2016NOV', 
    ]
    # exam_codes = ['2016MAY']

    for exam_code in exam_codes:
        exam = Exam.objects.get(code=exam_code)

        url = node_url + 'examregistration/results/' + exam_code

        r = requests.get(url)

        exam_registrations = r.json()['data']
        
        for exam_registration_import in exam_registrations:
            try:
                user_id = exam_registration_import.get('ID')
                pass_value = exam_registration_import.get('PASS')
                
                contact = Contact.objects.get(user__username=user_id)
                reg = ExamRegistration.objects.filter(exam=exam, contact=contact)

                if pass_value == 1:
                    reg.update(is_pass=True)
                else:
                    reg.update(is_pass=False)

                print("Updated reg pass/fail for: " + str(contact))
            except Exception as e:
                print("error importing pass/fail record: " + str(e))
