import requests
import base64
import xml.etree.ElementTree as ET

from django.core.mail import send_mail

from planning.settings import PROMETRIC_USERNAME, PROMETRIC_PASSWORD, \
    AICP_TEAM_EMAILS

class Prometric(object):
    """
    all prometric calls are made here
    """
    auth_token = None

    def __init__(self):
        self.auth_token = self.get_auth_token()

    def get_auth_token(self):
        """
        creates a token needed for submitting XELIG data
        NOTE: put these Prometric methods soemwhere else once working
        """
        url="https://gee.prometric.com/GEEWEBSR/geesr.asmx"
        headers = {'content-type':'text/xml; charset=utf-8',
                'SOAPAction': 'https://gee.prometric.com/GetToken'}
        body = """<?xml version="1.0" encoding="utf-8"?>
                <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema- instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                <soap:Body>
                <GetToken xmlns="https://gee.prometric.com/">
                <strSystemID>"""+PROMETRIC_USERNAME+ """</strSystemID>
                <strPassword>"""+PROMETRIC_PASSWORD+ """</strPassword> </GetToken>
              </soap:Body>
            </soap:Envelope>"""

        response = requests.post(url,data=body,headers=headers)
        response_string = response.content.decode("utf-8")
        response_et = ET.fromstring(response_string)

        return response_et.find('.//{https://gee.prometric.com/}GetTokenResult').text

    def create_xelig(self, exam_registration):
        """
        returns xml formatted for the prometric call
        """
        form_code_id = exam_registration.get_form_code_id()
        exam_id = exam_registration.get_exam_id()
        exam_code = exam_registration.exam.code

        # grab the birth date because eric r. says so
        contact_dict = exam_registration.contact.get_imis_contact_legacy()["data"]
        company = contact_dict.get("company", '')
        if company == '':
            company = 'none'

        root = ET.Element('XELIG', attrib={'version':'2.00',})

        client_child = ET.SubElement(root, 'client')
        client_child.text='AICP'
        eligibility = ET.SubElement(root, 'eligibility')
        action = ET.SubElement(eligibility, 'action')
        action.text="add"
        demographics = ET.SubElement(eligibility, 'demographics')
        demographics_first_name = ET.SubElement(demographics, 'firstname')
        demographics_first_name.text = contact_dict.get('first_name', '')[:45]
        demographics_last_name = ET.SubElement(demographics, 'lastname')
        demographics_last_name.text = contact_dict.get('last_name', '')[:45]
        demographics_dateofbirth = ET.SubElement(demographics, 'dateofbirth')
        demographics_dateofbirth.text = contact_dict.get('birth_date', '')
        ids = ET.SubElement(demographics, 'ids')
        ssn = ET.SubElement(ids, 'ssn')
        # Prometric's "candidate" designation has nothing to do with AICP Candidate
        candidateid1 = ET.SubElement(ids, 'candidateid1')
        candidateid1.text = exam_registration.contact.user.username
        candidateid2 = ET.SubElement(ids, 'candidateid2')
        if exam_registration.registration_type in ["CAND_ENR_A", "CAND_T_0", "CAND_T_100"]:
            candidateid2.text="AICP_CAND"
        else:
            candidateid2.text="REGULAR"
        # ssn.text = exam_registration.contact.user.username
        address = ET.SubElement(demographics, 'address')
        demographics_address1 = ET.SubElement(address, 'address1')
        demographics_address1.text = company[:45]
        demographics_address2 = ET.SubElement(address, 'address2')
        demographics_address2.text = contact_dict.get('address1', '')[:45]

        demographics_address3 = ET.SubElement(address, 'address3')
        demographics_address3.text = contact_dict.get('address2', '')[:45]
        demographics_city = ET.SubElement(address, 'city')
        demographics_city.text = contact_dict.get('city')[:30]
        demographics_province = ET.SubElement(address, 'province')
        demographics_province.text = contact_dict.get('state_province', '')[:25]
        demographics_postal_code = ET.SubElement(address, 'postalcode')
        demographics_postal_code.text = contact_dict.get('zip_code', '')[:12]
        phones = ET.SubElement(demographics, 'phones')
        # phones_work = SubElement(phones, 'work')
        # phones_work.text = '' # self.contact.work_phone we don't have this yet
        phones_home = ET.SubElement(phones, 'home')
        phones_home.text = contact_dict.get('home_phone', '')[:20]
        demographics_email = ET.SubElement(demographics, 'emailaddress')
        demographics_email.text = contact_dict.get('email', '')[:50]
        events = ET.SubElement(eligibility, 'events')
        event = ET.SubElement(events, 'event')
        event_exam = ET.SubElement(event, 'exam', 
            attrib={"programid":"AICP","examsessions":'1',"examid":exam_id,"examtype":exam_code})
        sessions = ET.SubElement(event, 'sessions')
        sessions_session = ET.SubElement(sessions, 'session', attrib={'sequence':'1','examform': str(exam_registration.exam.generate_prometric_exam_code(form_code_id))})

        if exam_registration.ada_requirement == 'TIME AND A HALF':
            sessions_session.set('sessionduration','150')
        elif exam_registration.ada_requirement == 'DOUBLE TIME':
            sessions_session.set('sessionduration','200')
        else:
            sessions_session.set('sessionduration','100')

        event_eligibilityid1 = ET.SubElement(event, 'eligibilityid1')
        event_eligibilityid1.text = "E" + exam_registration.contact.user.username + str(exam_registration.id)
        restrictions = ET.SubElement(event, 'restrictions')
        restrictions_startdate = ET.SubElement(restrictions, 'startdate')
        restrictions_startdate.text = exam_registration.exam.start_time.strftime('%Y-%m-%d')
        restrictions_enddate = ET.SubElement(restrictions, 'enddate')
        restrictions_enddate.text = exam_registration.exam.end_time.strftime('%Y-%m-%d')
        event_specialconditions = ET.SubElement(event, 'specialconditions')
        specialconditions_specialcondition = ET.SubElement(event_specialconditions, 'specialcondition')
        
        if exam_registration.ada_requirement in ('READER REQUIRED', 'SEPARATE ROOM'):
            specialconditions_specialcondition.text = exam_registration.ada_requirement

        return base64.b64encode(ET.tostring(root, encoding="utf-8")).decode("utf-8")

    def submit_xelig(self, exam_registration):
        """
        submit an AICP exam registration to prometric for testing
        1 = successful submission
        anything else - there was an error
        """

        url="https://gee.prometric.com/GEEWEBSR/geesr.asmx"
        headers = {'content-type':'text/xml; charset=utf-8',
                'SOAPAction': 'https://gee.prometric.com/SubmitXELIG'}
        body = """<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema- instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><SubmitXELIG xmlns="https://gee.prometric.com/"><strToken>""" + self.auth_token + "</strToken>" + "<strXELIG>" +  str(self.create_xelig(exam_registration)) + "</strXELIG>" + """</SubmitXELIG></soap:Body></soap:Envelope>"""

        response = requests.post(url,data=body,headers=headers)
        response_string = response.content.decode("utf-8")
        response_et = ET.fromstring(response_string)

        # add email alert here for failed prometric exam submissions? 
        response_code = ET.fromstring(response_et.find('.//{https://gee.prometric.com/}SubmitXELIGResult').text).get('result')
        if response_code == "1":
            exam_registration.gee_eligibility_id = "E" + exam_registration.contact.user.username + str(exam_registration.id)
            exam_registration.save()
        else:
            # add email alert here for failed prometric exam submissions? 
            mail_subject = "Error submitting eligiblity id to Prometric. User ID: {0}".format(exam_registration.contact.user.username)

            prometric_error_response = ET.fromstring(response_et.find('.//{https://gee.prometric.com/}SubmitXELIGResult').text).text
            mail_body = """ There was an error submitting prometric data for the user listed below. 
                            <br/><br/>User ID: """+exam_registration.contact.user.username+"""
                            <br/>Exam Code: """+ exam_registration.exam.code+"""
                            <br/>Response Code: """+ str(response_code)+"""
                            <br/>Prometric Response: """+ prometric_error_response
            send_mail(mail_subject, prometric_error_response, 'django@planning.org', AICP_TEAM_EMAILS, fail_silently=False, html_message=mail_body)
        return response_code
        
