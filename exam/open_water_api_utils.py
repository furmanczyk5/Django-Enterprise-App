import datetime
from decimal import Decimal
import json
import pytz
from sentry_sdk import add_breadcrumb, capture_exception
from time import sleep

from django.conf import settings
from django.utils import timezone

from myapa.models.contact import Contact
from myapa.permissions.utils import update_user_groups
from store.models import Product, ProductPrice, ProductCart, Payment, Order

from api.clients.base import ExternalService
from exam.settings import OPEN_WATER_API_URL
from exam.models import AICPCredentialData
from store.models import Purchase

import logging
logger = logging.getLogger(__name__)
DEBUG_MODE = False

# TO SET UP THE ACTUAL AWARDS FEES FOR THE AWARDS LAUNCH:
# CREATE INDIVIDUAL IMIS PRODUCTS FOR EACH FEE
# CREATE DJANGO PRODUCT/PRICE FOR EACH FEE
# THEN UPDATE THIS DICT WITH THE ACTUAL IMIS PRODUCT CODES

OPEN_WATER_COUPON_CODE = 'aicpcode'

OPEN_WATER_DETAILS_TO_PRODUCT_CODE = {
    'awards_instance': {
        'Nomination Fee - APA Member, Coupon': 'OW_AWARDS_MEMBER', # placeholder product code
        'Nomination Fee - Non Member, Coupon': 'OW_AWARDS_NONMEMBER', # placeholder product code
    },
    'aicp_instance': {
        # CANDIDATE PATH
        'Enrollment': 'OW_AICP_CAN_ENR',
        'Certification Application': 'OW_AICP_CERT_AP',
        'Expedited Certification Application': 'OW_EX_CERT_AP',
        # CANDIDATE SCHOLARSHIP
        'Certification Application (Scholarship)': 'OW_AICP_CES_SCH',
        'Expedited Certification Application (Scholarship)': 'OW_AICP_CXESSCH',
        # TRADITIONAL PATH
        'Application Fee': 'OW_AICP_APP_FEE',
        'Essay': 'OW_AICP_REG_ESS',
        'Expedited Essay Review': 'OW_AICP_EX_ESSY',
        # TRADITIONAL SCHOLARSHIP
        'Essay (Scholarship)': 'OW_AICP_ES_SCHL',
        'Expedited Essay Review (Scholarship)': 'OW_AICP_XES_SCH',
        # REGISTRATION
        'Exam Fee - Candidate': 'OW_AICP_CAN_EX',
        'Exam Fee - Standard': 'OW_AICP_EXAM_ST',
        'Exam Transfer Fee': 'OW_AICP_TRANSFR',
        # NOT SET UP IN OW AICP YET... NEED TO VERIFY:
        'Candidate Transfer Fee': 'OW_AICP_CANDTRX',
        # REGISTRATION SCHOLARSHIP
        'Exam Fee - Candidate (Scholarship)': 'OW_AICP_CEX_SCH',
        'Exam Fee - Standard (Scholarship)': 'OW_AICP_EX_SCHL',
        # CHANGE TO CORRECT FEE NAME AFTER IT'S SET UP IN OPEN WATER:
        'Appeal submission fee': 'OW_AICP_APPEAL'
    },
    'test_instance': {
        # CANDIDATE PATH
        'Enrollment': 'OW_AICP_CAN_ENR',
        'Certification Application': 'OW_AICP_CERT_AP',
        'Expedited Certification Application': 'OW_EX_CERT_AP',
        # CANDIDATE SCHOLARSHIP
        'Certification Application (Scholarship)': 'OW_AICP_CES_SCH',
        'Expedited Certification Application (Scholarship)': 'OW_AICP_CXESSCH',
        # TRADITIONAL PATH
        'Application Fee': 'OW_AICP_APP_FEE',
        'Essay': 'OW_AICP_REG_ESS',
        'Expedited Essay Review': 'OW_AICP_EX_ESSY',
        # TRADITIONAL SCHOLARSHIP
        'Essay (Scholarship)': 'OW_AICP_ES_SCHL',
        'Expedited Essay Review (Scholarship)': 'OW_AICP_XES_SCH',
        # REGISTRATION
        'Exam Fee - Candidate': 'OW_AICP_CAN_EX',
        'Exam Fee - Standard': 'OW_AICP_EXAM_ST',
        'Exam Transfer Fee': 'OW_AICP_TRANSFR',
        # NOT SET UP IN OW TEST YET... NEED TO VERIFY:
        'Candidate Transfer Fee': 'OW_AICP_CANDTRX',
        # REGISTRATION SCHOLARSHIP
        'Exam Fee - Candidate (Scholarship)': 'OW_AICP_CEX_SCH',
        'Exam Fee - Standard (Scholarship)': 'OW_AICP_EX_SCHL',
        # CHANGE TO CORRECT FEE NAME AFTER IT'S SET UP IN OPEN WATER:
        'Appeal submission fee': 'OW_AICP_APPEAL'
    }
}

# Open Water Program Names
TRADITIONAL_CERTIFICATION_PROGRAM = 'American Institute of Certified Planners - Certification Application - Traditional Path'
CANDIDATE_CERTIFICATION_PROGRAM = 'American Institute of Certified Planners - Certification Application - Candidate Path'
EXAM_REGISTRATION_PROGRAM = 'American Institute of Certified Planners - Exam Registration'
# Open Water Round Names
TRAD_APP_SUBMISSION_ROUND = "Application Submission"
TRAD_ESSAY_SUBMISSION_ROUND_1_ROUND = "Essay Submission (Round 1)"
TRAD_ESSAY_SUBMISSION_ROUND_4_ROUND = "Essay Resubmit (Round 4)"
CAND_APP_SUBMISSION_ROUND = "Candidate Enrollment"
CAND_ESSAY_SUBMISSION_ROUND_1_ROUND = "Essay Submission (Round 1)"
CAND_ESSAY_SUBMISSION_ROUND_4_ROUND = "Essay Resubmit (Round 4)"
EXAM_REGISTRATION_ROUND = "Exam Registration"

OW_MYAPA_PROGRAMS = (
    TRADITIONAL_CERTIFICATION_PROGRAM,
    CANDIDATE_CERTIFICATION_PROGRAM,
    EXAM_REGISTRATION_PROGRAM
)
OW_MYAPA_ROUNDS = (
    TRAD_APP_SUBMISSION_ROUND,
    TRAD_ESSAY_SUBMISSION_ROUND_1_ROUND,
    TRAD_ESSAY_SUBMISSION_ROUND_4_ROUND,
    CAND_APP_SUBMISSION_ROUND,
    CAND_ESSAY_SUBMISSION_ROUND_1_ROUND,
    CAND_ESSAY_SUBMISSION_ROUND_4_ROUND,
    EXAM_REGISTRATION_ROUND
)


class OpenWaterCallHelper(ExternalService):
    """
    Creates callable objects that make get/post calls to Open Water's Invoices API.
    """

    def __init__(self,
                 method_name,  # the Open Water API method name (incorporated in URL, e.g. /Invoices/{id}
                 http_method="get",
                 **kwargs
                 ):
        self.method_name = method_name
        self.http_method = http_method
        self.response = None
        self.success = None
        self.json = None
        self.headers = None
        self.instance = kwargs.pop("instance", None)
        self.__dict__.update(kwargs)
        super().__init__(timeout=30)


    @property
    def endpoint(self):
        """
        The endpoint url for making the call to Open Water's server.
        """
        api_url = 'https://api.secure-platform.com/v2/'

        return api_url

    def log_error(self, log_method="error"):
        """
        Logs to logger (Sentry) as either as an error or exception
        """
        msg = 'Open Water API Error Calling "%s"' % self.method_name
        getattr(logger, log_method)(msg, exc_info=True, extra={
            "data": {
                "endpoint": OPEN_WATER_API_URL,
                "response": self.response.text if self.response else None
            },
        })

    def __call__(self, fail_silently=True, log_soft_fails=True, **kwargs):
        """
        Makes the call, passing in kwargs as parameters, and returns the response as JSON.
        """
    # put try back in after testing??
    # try:
        self.success = False
        client_key = settings.OPEN_WATER_CLIENT_KEYS[self.instance]
        api_key = settings.OPEN_WATER_API_KEYS[self.instance]
        self.headers = {'accept': 'application/json', 'X-ClientKey': client_key,
                    'X-ApiKey': api_key, 'X-SuppressEmails': 'true'}

        if self.http_method == 'get':
            self.response = self.make_request(self.endpoint + self.method_name,
                                                method=self.http_method,
                                                params=kwargs,
                                              headers=self.headers)
        elif self.http_method == 'post':
            params_dict = {'APIKey': kwargs.pop("APIKey"), 'Method': kwargs.pop("Method")}
            d = json.dumps(kwargs)
            post_body_json = [json.loads(d)]
            self.response = self.make_request(self.endpoint + self.method_name,
                                              method=self.http_method,
                                              json=post_body_json,
                                              params=params_dict,
                                                headers=self.headers)

        if self.response:
            print("request headers is ", self.response.request.headers)
            print("request method is ", self.response.request.method)
            print("request url is ", self.response.request.url)
            print("request body is ", self.response.request.body, "\n")
            self.json = self.response.json()

            if len(self.json) > 0:
                self.success = True
            else:
                self.success = False

            if not self.success:
                if not fail_silently:
                    raise Exception("Open Water response had an error or was explicitly unsuccessful, raising exception since fail_silently=False")
                elif log_soft_fails:
                    self.log_error("error")

            if DEBUG_MODE:
                print(self.response.url)
                print(self.json)
                print("-------")

        return self.json
    # put back in after testing?
    # except Exception as e:
    #     self.log_error("exception")
    #
    #     if not fail_silently:
    #         raise e

class OpenWaterAPICaller():

    def __init__(self, **kwargs):
        self.instance = kwargs.pop("instance", None)
        self.instance_details_dict = OPEN_WATER_DETAILS_TO_PRODUCT_CODE.get(self.instance, None)
        self.__dict__.update(kwargs)

    def get_invoices_summary(self, program_id, is_paid=True, most_recent_transaction_since_utc=None, page_index=0, page_size=10):
        method_name = 'Invoices'
        response = OpenWaterCallHelper(method_name, http_method='get', instance=self.instance)(
            programId=program_id,
            isPaid=is_paid,
            mostRecentTransactionSinceUtc=most_recent_transaction_since_utc,
            pageIndex=page_index,
            pageSize=page_size
        )
        return response or {}

    def get_invoice(self, invoice_id):
        method_name = 'Invoices/{}'.format(invoice_id)
        response = OpenWaterCallHelper(method_name, http_method='get', instance=self.instance)()
        return response or {}

    def get_billing_line_items(self):
        method_name = 'Invoices/BillingLineItems'
        response = OpenWaterCallHelper(method_name, http_method='get', instance=self.instance)()
        return response or {}

    def get_payments(self):
        method_name = 'Invoices/Payments'
        response = OpenWaterCallHelper(method_name, http_method='get', instance=self.instance)()
        return response or {}

    def get_refunds(self):
        method_name = 'Invoices/Refunds'
        response = OpenWaterCallHelper(method_name, http_method='get', instance=self.instance)()
        return response or {}

    def write_invoice(self, ow_invoice):
        process_order = False

        if ow_invoice:
            username = ow_invoice['thirdPartyCorporateId']

            if username:
                try:
                    missing = 6 - len(username)
                    username = "0" * missing + username
                    contact = Contact.objects.get(user__username=username)
                except Exception as e:
                    contact = None
                    print("Exception Contact query failed: ", e)

                if contact:
                    user = contact.user
                    couponCode = ow_invoice.get('couponCode', '')

                    for bli in ow_invoice['billingLineItems']:
                        full_fee_name = bli['details']
                        instance_details_dict = self.instance_details_dict
                        tokens = full_fee_name.split(',')
                        fee_name = tokens[0] if tokens else None
                        price_title = tokens[0] + ', Coupon' if len(tokens) > 1 else fee_name

                        if fee_name in instance_details_dict.keys():
                            invoice_amount = self.ow_to_django_payment_amount(bli['amount'])

                            if Decimal(invoice_amount) != 0 or couponCode == OPEN_WATER_COUPON_CODE:
                                print("fee name is ", fee_name)
                                django_product_code = instance_details_dict.get(fee_name, 'NO_OW_FEE_TO_DJANGO_PRODUCT_MATCH_EXISTS')

                                try:
                                    content_live_product = Product.objects.get(publish_status="PUBLISHED",
                                        code=django_product_code)
                                    product = ProductCart.objects.get(id=content_live_product.id)
                                    print("django product code is ", django_product_code)
                                    print("content live product is ", content_live_product)
                                    print("content live product id is ", content_live_product.id)

                                    if settings.ENVIRONMENT_NAME != "PROD":
                                        product_price = ProductPrice.objects.get(product=content_live_product,
                                                                                 # price=invoice_amount,
                                                                                 title=price_title)
                                    else:
                                        product_price = ProductPrice.objects.get(product=content_live_product,
                                                                                 price=invoice_amount,
                                                                                 title=price_title)
                                except Exception as e:
                                    print("EXCEPTION GETTING PRODUCT OR PRICE: ", e)
                                    content_live_product = None
                                    product = None
                                    product_price = None

                                price_code = product_price.code if product_price else None
                                order_created_date = ow_invoice['createdAtUtc']
                                print("PRICE CODE IS ", price_code)
                                print("Price title is --------------------- ", price_title)
                                print("ORDER CREATED DATE IS -------------------- ", order_created_date)

                                # FOR TESTING WITHOUT WRITING COMMENT THIS BLOCK OUT // START:
                                if product and product_price and (ow_invoice['payments'] or couponCode == OPEN_WATER_COUPON_CODE):
                                    print("IN CREATE ORDER BLOCK FROM PAYMENT OR COUPON CODE")
                                    order, order_created = Order.objects.get_or_create(
                                        user=user,
                                        submitted_user_id=user.username,
                                        submitted_time=order_created_date,
                                        order_status="SUBMITTED")
                                    print("ORDER IS ", order, order_created)

                                    if order_created:
                                        cart_purchases = Purchase.objects.filter(order__isnull=True, user=user).exclude(status='A')
                                        print("Deleting all %s purchases " % cart_purchases.count())
                                        cart_purchases.delete()
                                        purchase = product.add_to_cart(
                                            contact=contact,
                                            quantity=1,
                                            code=price_code
                                        )
                                        print("PURCHASE IS ", purchase)

                                        if purchase:
                                            process_order = True
                                        else:
                                            log_method = 'error'
                                            msg = 'Open Water Invoice Failed to Add Purchase to Cart'
                                            getattr(logger, log_method)(msg, exc_info=True, extra={
                                                "data": {
                                                    "contact": contact,
                                                    "invoice": ow_invoice,
                                                    "order": order,
                                                    "purchase": purchase,
                                                    "fee_name": fee_name,
                                                    "product": product,
                                                    "product price": product_price,
                                                    "price_title": price_title,
                                                    "price_code": price_code,
                                                    "couponCode": couponCode
                                                },
                                            })
                                        print("process_order is ", process_order)
                                # FOR TESTING WITHOUT WRITING ANYTHING COMMENT THIS BLOCK OUT // END
                            break

                    if process_order:
                        print("START PROCESS ORDER ----- ", order)
                        order.add_from_cart(user)

                        for pay in ow_invoice['payments']:
                            method = self.ow_to_django_payment_method(pay['method'])
                            amount = self.ow_to_django_payment_amount(pay['amount'])
                            pn_ref = pay['externalPaymentTransactionData']
                            payment, created = Payment.objects.get_or_create(
                                method=method,
                                order=order,
                                user=user,
                                submitted_time=order_created_date,
                                amount=amount,
                                # in imis pn_ref (paypal transaction id) is written to Orders.gateway_ref ?
                                pn_ref=pn_ref)
                            payment.process()

                        if not ow_invoice['payments'] and couponCode == OPEN_WATER_COUPON_CODE:
                            method = self.ow_to_django_payment_method('CreditCard')
                            amount = self.ow_to_django_payment_amount(0.00)
                            pn_ref = None
                            payment, created = Payment.objects.get_or_create(
                                method=method,
                                order=order,
                                user=user,
                                submitted_time=order_created_date,
                                amount=amount,
                                pn_ref=pn_ref)
                            payment.process()

                        # TO TEST WRITING ALL DJANGO, BUT NO IMIS COMMENT THIS OUT (then delete payment, purchase, order):
                        order.process()
                        print("END PROCESS ORDER ---- ", order)
                        log_method = 'debug'
                        msg = 'Open Water Invoice Writing Summary - DEBUG'
                        getattr(logger, log_method)(msg, exc_info=True, extra={
                            "data": {
                                "contact": contact,
                                "invoice": ow_invoice,
                                "order": order,
                                "purchase": purchase,
                                "fee_name": fee_name,
                                "product": product,
                                "product price": product_price,
                                "price_title": price_title,
                                "price_code": price_code,
                                "couponCode": couponCode
                            },
                        })

                        try:
                            update_user_groups(user)
                        except Exception as exc:
                            log_method = 'error'
                            msg = 'Exception Calling update_user_groups() During Open Water Invoice Writing'
                            getattr(logger, log_method)(msg, exc_info=True, extra={
                                "data": {
                                    "user": user,
                                },
                            })

    # *** REMEMBER FULL DEPLOY TO RESTART CELERY ***
    def pull_open_water_invoices(self, window_in_hours=.5):
        psum = self.get_programs_summary()
        pagingInfo=psum.get('pagingInfo',{})
        num_programs = pagingInfo.get('totalCount',0)
        programs = psum.get('items',[])
        program_ids = [p.get('id') for p in programs]
        now = timezone.now()
        launch_date = now.replace(year=2021, month=1, day=5, hour=6, minute=0, second=0)
        format_string_no_micro = "%Y-%m-%dT%H:%M:%S"
        utc = pytz.timezone("UTC")

        for p in program_ids:
            now = timezone.now()
            some_hours = datetime.timedelta(hours=window_in_hours)
            some_hours_prior = now - some_hours
            # like this: '2020-07-21T14:42:57.5629977Z'
            format_string = "%Y-%m-%dT%H:%M:%S.%fZ"
            some_hours_prior_formatted = some_hours_prior.strftime(format_string)
            # put 100 ms delay here and before every http request (OW has 10 requests/sec limit)
            sleep(.33)
            invoice_ids = []
            invs=self.get_invoices_summary(p, True, some_hours_prior_formatted, 0, 1000)
            # ONLY TEMPORARY:
            # invs=self.get_invoices_summary(p, True, launch_date, 0, 1000)
            pagingInfo = invs.get('pagingInfo',{})
            numberOfPages = pagingInfo.get('numberOfPages') if pagingInfo else 0
            print("program id is ++++++++ ", p)
            print("numberOfPages is +++++++++ ", numberOfPages)
            # num_invoices = pagingInfo.get('totalCount', 0) if pagingInfo else 0
            invoices = invs.get('items',[])
            print("num_invoices is +++++++++ ", len(invoices))

            page = 1
            while numberOfPages > 0 and page <= numberOfPages:
                for inv_dict in invoices:
                    createdAtUtc = inv_dict.get('createdAtUtc', None)
                    tokens = createdAtUtc.split('.')
                    created_date_no_micro = tokens[0] if tokens else None
                    created_at_date_object = datetime.datetime.strptime(created_date_no_micro, format_string_no_micro)
                    created_at_utc = utc.localize(created_at_date_object)
                    # print("CREATED AT UTC IS ++++++++++++++++ ", created_at_utc)
                    if created_at_utc >= launch_date:
                        invoice_ids.append(inv_dict.get('id'))

                if page < numberOfPages:
                    # BRING THIS BACK AFTER 500 ERROR FIXED:
                    invs=self.get_invoices_summary(p, True, some_hours_prior_formatted, page, 1000)
                    # temporary, see above -- REPLACE AFTER 500 ERROR FIXED AND
                    # invs=self.get_invoices_summary(p, True, launch_date, page, 1000)
                    invoices = invs.get('items',[])
                    print("for page %s num invoices is %s" % (page, len(invoices)))
                    print("INSIDE invoice_ids is ++++ ", invoice_ids)
                page += 1
            invoice_ids = set(invoice_ids)
            invoice_ids = list(invoice_ids)
            print("FINAL LIST OF INVOICE IDS ---------------------------------------------")
            print(invoice_ids)

            for i in invoice_ids:
                sleep(.33)
                inv=self.get_invoice(i)
                # BETTER NOT TO WRITE ANYTHING FROM LOCAL (comment out for local testing)
                print("invoice being written: ")
                print(i)
                print(inv)
                self.write_invoice(inv)

    def ow_to_django_payment_method(self, ow_payment_method):
        case_switch = {
            'CreditCard':'CC',
            'Check': 'CHECK'
        }
        return case_switch.get(ow_payment_method, None)

    def ow_to_django_payment_amount(self, ow_payment_amount):
        return Decimal("%.2f" % (ow_payment_amount))

    def get_ow_instance_details(self):
        if self.instance is 'awards_instance':
            return OPEN_WATER_DETAILS_TO_PRODUCT_CODE.get(self.instance)
        if self.instance is 'aicp_instance':
            return OPEN_WATER_DETAILS_TO_PRODUCT_CODE.get(self.instance)
        if self.instance is 'test_instance':
            return OPEN_WATER_DETAILS_TO_PRODUCT_CODE.get(self.instance)

    # an Open Water "program" is an initiative like "Essay Submission" or "Exam Registration"
    def get_programs_summary(self):
        method_name = 'Programs'
        response = OpenWaterCallHelper(method_name, http_method='get', instance=self.instance)()
        return response

    def get_program(self, program_id):
        method_name = 'Programs/{}'.format(program_id)
        response = OpenWaterCallHelper(method_name, http_method='get', instance=self.instance)()
        return response

    def get_applications_summary(self, program_id=None, user_id=None, code=None, lastModifiedSinceUtc=None,
        page_index=0, page_size=1000):
        method_name = 'Applications'
        response = OpenWaterCallHelper(method_name, http_method='get', instance=self.instance)(
            programId=program_id,
            userId=user_id,
            # code=code,
            # lastModifiedSinceUtc=lastModifiedSinceUtc,
            pageIndex=page_index,
            pageSize=page_size
        )
        return response

    def get_application(self, application_id):
        method_name = 'Applications/{}'.format(application_id)
        response = OpenWaterCallHelper(method_name, http_method='get', instance=self.instance)()
        return response

    def get_filtered_users(self, thirdPartyId=None):
        method_name = 'Users'
        response = OpenWaterCallHelper(method_name, http_method='get', instance=self.instance)(
            thirdPartyId=thirdPartyId,
        )
        return response

    def get_ow_aicp_info(self, thirdPartyId=None, info_dict={}):
        OWPR = OPEN_WATER_PROGRAMS_AND_ROUNDS = self.build_program_summary_dict()
        trad_cert = OWPR[TRADITIONAL_CERTIFICATION_PROGRAM]
        cand_cert = OWPR[CANDIDATE_CERTIFICATION_PROGRAM]
        exam_reg = OWPR[EXAM_REGISTRATION_PROGRAM]
        ow_users = self.get_filtered_users(thirdPartyId=thirdPartyId).get("items", [])
        ow_user_id_dict = ow_users[0] if len(ow_users) == 1 else {}
        ow_user_id = ow_user_id_dict.get("id", None)
        cc_app_sub_max = cc_ess_sub_r1_max = cc_ess_sub_r4_max = -1
        tc_app_sub_max = tc_ess_sub_r1_max = tc_ess_sub_r4_max = ex_reg_max = -1
        # if you hit get_applications_summary with a None or "" user_id it returns all apps, all users
        if ow_user_id:
            for k, v in OPEN_WATER_PROGRAMS_AND_ROUNDS.items():
                program_id = v.get("id")
                app_dict = self.get_applications_summary(
                    program_id=program_id, user_id=ow_user_id) or {}#{} if program_id else {}
                app_list = app_dict.get("items",[]) if app_dict else []

                for app in app_list:
                    if app['userId'] == ow_user_id:
                        app_id = app.get("id")
                        full_app = self.get_application(app_id)

                        if full_app:
                            full_app_id = full_app.get("id", -2)
                            round_submissions_list = full_app.get("roundSubmissions", [])
                        else:
                            full_app_id = ""
                            round_submissions_list = []

                        for ow_round in round_submissions_list:
                            round_id = ow_round.get("roundId")
                            date = ow_round.get("updatedAtUtc", None)
                            date = None if date == '' else date
                            status = ow_round.get("status", None)
                            status = None if status == '' else status

                            if round_id == cand_cert[CAND_APP_SUBMISSION_ROUND]:
                                if full_app_id > cc_app_sub_max:
                                    info_dict["cand_cert_sub_date"] = date
                                    info_dict["cand_cert_status"] = status
                                    cc_app_sub_max = full_app_id
                            elif round_id == cand_cert[CAND_ESSAY_SUBMISSION_ROUND_1_ROUND]:
                                if full_app_id > cc_ess_sub_r1_max:
                                    info_dict["cand_essay_sub_date"] = date
                                    info_dict["cand_essay_status"] = status
                                    cc_ess_sub_r1_max = full_app_id
                            elif round_id == cand_cert[CAND_ESSAY_SUBMISSION_ROUND_4_ROUND]:
                                if full_app_id > cc_ess_sub_r4_max:
                                    info_dict["cand_essay_sub_date"] = date if date else info_dict["cand_essay_sub_date"]
                                    info_dict["cand_essay_status"] = status if status else info_dict["cand_essay_status"]
                                    cc_ess_sub_r4_max = full_app_id
                            elif round_id == trad_cert[TRAD_APP_SUBMISSION_ROUND]:
                                if full_app_id > tc_app_sub_max:
                                    info_dict["trad_cert_sub_date"] = date
                                    info_dict["trad_cert_status"] = status
                                    tc_app_sub_max = full_app_id
                            elif round_id == trad_cert[TRAD_ESSAY_SUBMISSION_ROUND_1_ROUND]:
                                if full_app_id > tc_ess_sub_r1_max:
                                    info_dict["trad_essay_sub_date"] = date
                                    info_dict["trad_essay_status"] = status
                                    tc_ess_sub_r1_max = full_app_id
                            elif round_id == trad_cert[TRAD_ESSAY_SUBMISSION_ROUND_4_ROUND]:
                                if full_app_id > tc_ess_sub_r4_max:
                                    info_dict["trad_essay_sub_date"] = date if date else info_dict["trad_essay_sub_date"]
                                    info_dict["trad_essay_status"] = status if status else info_dict["trad_essay_status"]
                                    tc_ess_sub_r4_max = full_app_id
                            elif round_id == exam_reg[EXAM_REGISTRATION_ROUND]:
                                if full_app_id > ex_reg_max:
                                    program = self.get_program(program_id)
                                    rounds = program.get("rounds",[]) if program else []
                                    reg_round_list = [d for d in rounds if d.get("id") == round_id]
                                    reg_round = reg_round_list[0] if reg_round_list else {}
                                    info_dict["exam_reg_sub_date"] = date
                                    info_dict["exam_reg_eligibility_id"] = full_app_id
                                    info_dict["exam_reg_exam_window_open"] = reg_round.get("judgingStartDateUtc", "")
                                    info_dict["exam_reg_exam_window_close"] = reg_round.get("judgingEndDateUtc", "")
                                    ex_reg_max = full_app_id
            if ow_user_id and thirdPartyId:
                ow_myapa_data, created = AICPCredentialData.objects.get_or_create(
                    imis_id=thirdPartyId,
                    open_water_user_id=ow_user_id)
            else:
                ow_myapa_data = None

            if ow_myapa_data:
                ow_myapa_data.candidate_application_submission_date = info_dict.get("cand_cert_sub_date", None)
                ow_myapa_data.candidate_application_status = info_dict.get("cand_cert_status", None)

                ow_myapa_data.candidate_essays_submission_date = info_dict.get("cand_essay_sub_date", None)
                ow_myapa_data.candidate_essays_status = info_dict.get("cand_essay_status", None)

                ow_myapa_data.traditional_application_submission_date = info_dict.get("trad_cert_sub_date", None)
                ow_myapa_data.traditional_application_status = info_dict.get("trad_cert_status", None)

                ow_myapa_data.traditional_essays_submission_date = info_dict.get("trad_essay_sub_date", None)
                ow_myapa_data.traditional_essays_status = info_dict.get("trad_essay_status", None)

                ow_myapa_data.exam_registration_submission_date = info_dict.get("exam_reg_sub_date", None)
                ow_myapa_data.exam_registration_eligibility_id = info_dict.get("exam_reg_eligibility_id", None)
                ow_myapa_data.exam_registration_exam_window_open = info_dict.get("exam_reg_exam_window_open", None)
                ow_myapa_data.exam_registration_exam_window_close = info_dict.get("exam_reg_exam_window_close", None)
                ow_myapa_data.save()
        return info_dict

    def build_program_summary_dict(self):
        owpr = open_water_program_summary = {}
        ps = self.get_programs_summary()
        items = ps["items"]
        for program in items:
            if program["name"] in OW_MYAPA_PROGRAMS:
                owpr[program["name"]] = {"id": program["id"]}
                rounds = program["rounds"]
                for round in rounds:
                    if round["name"] in OW_MYAPA_ROUNDS:
                        owpr[program["name"]][round["name"]] = round["id"]
        return owpr

    def show_ow_program_summary(self):
        ret1 = self.get_programs_summary()
        print("get programs returns:")
        print(ret1)
        items = ret1["items"]
        for li in items:
            print("NEW PROGRAM --------------------")
            print("program id: ", li["id"])
            print("program name: ", li["name"])
            rounds = li["rounds"]
            for rli in rounds:
                print("round id: ", rli["id"])
                print("round name: ", rli["name"])
            print("END PROGRAM ---------------------\n")
        print("")

    def show_ow_app_rounds(self, application_id):
        app = self.get_application(application_id)
        print("\n---------------------- GET APP RETURNS THIS -------------------------------------")
        print(app)
        print("app id: ", app["id"])
        print("app program id: ", app["programId"])
        roundSubmissions = app.get("roundSubmissions",[])
        print("Here are the app round submissions:")
        for rsli in roundSubmissions:
            print("in app round submissions, round id is: ", rsli.get("roundId"))
            print("in app round submissions, round name is ", rsli.get("roundName"))
            print("in app round submissions, date submitted is ", rsli.get("finalizedAtUtc"))
            print("in app round submissions, status is ", rsli.get("status"))
        print("")

    def get_programs_summary(self):
        method_name = 'Programs'
        response = OpenWaterCallHelper(method_name, http_method='get', instance=self.instance)()
        return response or {}

    def sync_open_water_to_myapa(self):
        '''
        Nightly sync of MyAPA data for those users who have records in the database.
        '''
        none_dict = dict(
            # from open water:
            cand_cert_sub_date=None,
            cand_cert_status=None,
            cand_essay_sub_date=None,
            cand_essay_status=None,
            trad_cert_sub_date=None,
            trad_cert_status=None,
            trad_essay_sub_date=None,
            trad_essay_status=None,
            exam_reg_sub_date=None,
            exam_reg_eligibility_id=None,
            exam_reg_exam_window_open=None,
            exam_reg_exam_window_close=None,
        )

        for acd in AICPCredentialData.objects.all():
            exam_dict = self.get_ow_aicp_info(
                thirdPartyId=acd.imis_id,
                info_dict=none_dict)
