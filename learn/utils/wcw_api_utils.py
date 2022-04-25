import datetime
import decimal
import json
import logging

from django.utils.html import strip_tags

from api.clients.base import ExternalService
from learn.models import GroupLicense
from learn.models.learn_course import LearnCourse
from learn.models.learn_course_info import LearnCourseInfo
from learn.models.learn_evaluation import LearnCourseEvaluation
from myapa.models import Contact, ContactRole
from planning.settings import LEARN_API_TOKEN, LEARN_DOMAIN, ENVIRONMENT_NAME

logger = logging.getLogger(__name__)

DEBUG_MODE = False

WCW_COURSE_CATEGORY_ID = "NPC21"

CM_HTML = """<span class="apa-blue-bold">CM</span><span class="apa-blue-narrow">|</span><span class="apa-red-bold">{0}</span>"""
CM_LAW_HTML = """<p><span><span style="color: rgb(54, 87, 140);"><b><span class="apa-blue-bold" style="">CM&nbsp;</span><span class="apa-blue-narrow" style="">I</span></b></span></span><span class="apa-red-bold"><b>&nbsp;<span style="color: rgb(190, 58, 52);">1.50&nbsp;</span></b></span><span style="color:rgb(54, 87, 140);">({0} Law)</span></p>"""
CM_ETHICS_HTML = """<p><span><span style="color: rgb(54, 87, 140);"><b><span class="apa-blue-bold" style="">CM&nbsp;</span><span class="apa-blue-narrow" style="">I</span></b></span></span><span class="apa-red-bold"><b>&nbsp;<span style="color: rgb(190, 58, 52);">1.50&nbsp;</span></b></span><span style="color:rgb(54, 87, 140);">({0} Ethics)</span></p>"""
CM_EQUITY_HTML = """<p><span><span style="color: rgb(54, 87, 140);"><b><span class="apa-blue-bold" style="">CM&nbsp;</span><span class="apa-blue-narrow" style="">I</span></b></span></span><span class="apa-red-bold"><b>&nbsp;<span style="color: rgb(190, 58, 52);">1.00&nbsp;</span></b></span><span style="color:rgb(54, 87, 140);">({0} Equity)</span></p>"""
CM_SUSTAINABILITY_HTML = """<p><span><span style="color: rgb(54, 87, 140);"><b><span class="apa-blue-bold" style="">CM&nbsp;</span><span class="apa-blue-narrow" style="">I</span></b></span></span><span class="apa-red-bold"><b>&nbsp;<span style="color: rgb(190, 58, 52);">1.00&nbsp;</span></b></span><span style="color:rgb(54, 87, 140);">({0} Sustainability & Resilience)</span></p>"""
GROUP_PRICING_HTML = """Interested in Group Pricing? <a href="https://learn.planning.org/mod/page/view.php?id=5236">Learn More</a>."""

STAGING_COURSE_URL = "https://apa.staging.coursestage.com/course/view.php?id="
PROD_COURSE_URL = "https://learn.planning.org/course/view.php?id="
STAGING_PRODUCT_URL = "https://apa.staging.coursestage.com/local/catalog/view/product.php?productid="
PROD_PRODUCT_URL = "https://learn.planning.org/local/catalog/view/product.php?productid="

LEARN_MORE_VALS = ("Yes", "No", "Undecided")

LMS_TEMPLATE_ID_STAGING = 11
LMS_TEMPLATE_ID_PROD = 26

MULTI_EVENT_CODE = "21CONF"

CONFERENCE_PREFIX = "NPC"
TWO_DIGIT_YEAR = "21"
LEARN_SESSION_DIGIT = "1"
COURSE_CREATE_PREFIX = CONFERENCE_PREFIX + TWO_DIGIT_YEAR + LEARN_SESSION_DIGIT
LEARN_COURSE_PREFIX = "LRN_" + COURSE_CREATE_PREFIX

RUN_TIME_CM = decimal.Decimal('0.75')
RUN_TIME = datetime.timedelta(0,45*60)


class WCWCallHelper(ExternalService):
    """
    A helper class to create callable objects that make get/post calls to WCW's api when called.
    """

    def __init__(self,
                 method_name,  # the WCW API method name, such as "AmsUpdateUser"
                 http_method="get"  # "get" or "post" in lowercase
                 ):
        self.method_name = method_name
        self.http_method = http_method
        self.response = None
        self.success = None
        self.json = None
        super().__init__(timeout=30)

    @property
    def endpoint(self):
        """
        The endpoint url for making the call to WCW's server.
        """
        return "https://%s/webservice/restv2/server/%s/%s/" % (LEARN_DOMAIN, LEARN_API_TOKEN, self.method_name)

    def log_error(self, log_method="error"):
        """
        Logs to logger (Sentry) as either as an error or exception
        """
        msg = 'WCW Sync Error Calling "%s"' % self.method_name
        getattr(logger, log_method)(msg, exc_info=True, extra={
            "data": {
                "endpoint": "https://%s/webservice/restv2/server/%s/%s/" % (
                LEARN_DOMAIN, "[LEARN_API_TOKEN]", self.method_name),
                "response": self.response.text if self.response else None
            },
        })

    def __call__(self, fail_silently=True, log_soft_fails=True, **kwargs):
        """
        Makes the call, passing in kwargs as parameters, and returns the response as JSON.
        """

        try:
            self.success = False  # assume guilty until proven innocent

            # self.response = getattr(requests, self.http_method)(self.endpoint, kwargs)

            if self.http_method == 'get':
                self.response = self.make_request(self.endpoint, method=self.http_method, params=kwargs)
            elif self.http_method == 'post':
                d = json.dumps(kwargs)
                post_body_json = json.loads(d)
                self.response = self.make_request(self.endpoint, method=self.http_method, json=post_body_json)
            self.json = self.response.json()
            self.success = self.json.get("success", False)

            if not self.success:
                if not fail_silently:
                    raise Exception("WCW response did not contain success, raising exception since fail_silently=False")
                elif log_soft_fails:
                    self.log_error("error")

            if DEBUG_MODE:
                print(self.response.url)
                print(self.json)
                print("-------")

            return self.json

        except Exception as e:
            self.log_error("exception")

            if not fail_silently:
                raise e


class WCWContactSync():

    def __init__(self, contact):
        self.contact = contact

    def get_user_kwargs(self):
        return dict(
            amsid=self.contact.user.username,
            firstname=self.contact.first_name,
            lastname=self.contact.last_name,
            email=self.contact.email,
            # country = self.contact.country, # TO DO: country codes
            city=self.contact.city,
            state=self.contact.state,
            # institution = self.contact.company, # TO DO: passing institution appears to raise invalid param exception
            # TO DO consider... custom fields for chapter?
        )

    def create_contact_on_wcw(self, **kwargs):
        return WCWCallHelper("AmsCreateUser")(**self.get_user_kwargs(), **kwargs)

    def update_contact_on_wcw(self, **kwargs):
        return WCWCallHelper("AmsUpdateUser")(**self.get_user_kwargs(), **kwargs)

    def post_order_to_wcw(self, order):
        """
        posts order to WCW if including learn courses purchased
        """
        purchases = order.purchase_set.all()

        # TO DO: confirm whether this creates new query counts
        learn_purchases = [p for p in purchases if p.product.product_type == "LEARN_COURSE"]

        if learn_purchases:
            # We're attempting to create user here just in case user has not already
            # synced to WCW. Most likely, will return an error response, with "user already exists",
            # which is fine
            self.create_contact_on_wcw(log_soft_fails=False)

            for p in learn_purchases:
                if p.quantity > 1 or p.for_someone_else == True:
                    existing_licenses = GroupLicense.objects.filter(purchase__product=p.product,
                                                                    purchase__user=self.contact.user)[:]
                    WCWCallHelper("SignupCodeCreate")(
                        amsid=self.contact.user.username,
                        productid=p.product.code,
                        quantity=int(p.quantity),
                        fail_silently=False
                    )
                    singup_code_query_helper = WCWCallHelper("SignupCodeQuery")
                    singup_code_query_helper(
                        creatoramsid=self.contact.user.username,
                        productid=p.product.code,
                        fail_silently=False
                    )
                    # TO DO TO DO... check that success is there when querying codes!!!
                    if singup_code_query_helper.success:
                        codes = singup_code_query_helper.json["codes"]
                        for c in codes:
                            if c["code"] not in [l.license_code for l in existing_licenses]:
                                GroupLicense.objects.create(purchase=p, license_code=c["code"])
                else:
                    WCWCallHelper("AmsPostOrder")(
                        amsid=self.contact.user.username,
                        productid=p.product.code,
                        orderid=order.id,
                        fail_silently=False
                    )

    def pull_licenses_redeemed_from_wcw(self, order):
        purchases = order.purchase_set.all()

        # TO DO: refactor / clean up to minimize queries
        learn_purchases = [p for p in purchases if p.product.product_type == "LEARN_COURSE"]
        for p in learn_purchases:
            if p.quantity > 1 or p.for_someone_else == True:
                singup_code_query_helper = WCWCallHelper("SignupCodeQuery")
                singup_code_query_helper(
                    creatoramsid=self.contact.user.username,
                    productid=p.product.code,
                )
                if singup_code_query_helper.success:
                    codes = singup_code_query_helper.json["codes"]
                    existing_licenses = GroupLicense.objects.filter(purchase__product=p.product,
                                                                    purchase__user=self.contact.user)[:]
                    for l in existing_licenses:
                        this_code = next((c for c in codes if c["code"] == l.license_code), None)

                        if this_code and this_code["amsid"] is not None and l.redemption_contact is None:
                            if this_code["dateconsumed"]:
                                l.redemption_date = datetime.datetime.strptime(this_code["dateconsumed"],
                                                                               "%Y-%m-%dT%H:%M:%SZ")
                            redemption_contact = Contact.objects.filter(user__username=this_code["amsid"]).first()
                            if redemption_contact is not None:
                                l.redemption_contact = redemption_contact
                            l.save()

    def star_rating_to_integer(self, star_rating):
        if star_rating and type(star_rating) == str and star_rating.find("Star") >= 0:
            tokens = star_rating.split("(")
            return int(tokens[1][0])
        else:
            return None

    def clean_wcw_integer(self, datum):
        if datum:
            star_rating = self.star_rating_to_integer(datum)
            if not star_rating:
                try:
                    integer = int(datum)
                    return 4 - integer + 1
                except:
                    return None
            else:
                return star_rating

    def clean_wcw_speaker_integer(self, datum):
        if datum:
            star_rating = self.star_rating_to_integer(datum)
            if not star_rating:
                try:
                    integer = int(datum)
                    if integer == 5:
                        return 0
                    else:
                        return 5 - integer
                except:
                    return None
            else:
                return star_rating

    def clean_wcw_boolean(self, datum):
        if datum and (datum == 'Agree' or datum == 'Yes' or datum == True):
            return True
        else:
            return False

    def clean_wcw_string(self, datum):
        if datum and type(datum) == str:
            return datum
        else:
            return None

    def clean_wcw_learn_more(self, datum):
        if datum and type(datum) == str and datum in LEARN_MORE_VALS:
            return datum.upper()
        else:
            return None

    def pull_course_completions_from_wcw(self):

        apa_logging_helper = WCWCallHelper("ApaLogging")
        apa_logging_helper(amsid=self.contact.user.username)

        if apa_logging_helper.success:

            courses = apa_logging_helper.json.get("courses", [])
            for c in courses:
                product_code = c.get("productid", None)
                try:
                    course = LearnCourse.objects.filter(code=product_code, publish_status="PUBLISHED", status__in=("A","H")).first()

                    try:
                        lce, lce_created = LearnCourseEvaluation.objects.get_or_create(
                            content=course,
                            contact=self.contact)
                        # FOR TESTING ONLY:
                        # if True:
                        if lce_created:
                            # Integer
                            lce.objective_rating = self.clean_wcw_integer(c.get("objective", None))
                            lce.knowledge_rating = self.clean_wcw_integer(c.get("knowledge", None))
                            lce.practice_rating = self.clean_wcw_integer(c.get("practice", None))
                            lce.speaker_rating = self.clean_wcw_speaker_integer(c.get("speaker", None))
                            lce.value_rating = self.clean_wcw_integer(c.get("value", None))
                            # Text
                            lce.commentary_suggestions = strip_tags(self.clean_wcw_string(c.get("suggestions", None)))
                            lce.learn_more_choice = self.clean_wcw_learn_more(c.get("learn", None))
                            # Boolean
                            lce.publish = self.clean_wcw_boolean(c.get("publish", None))
                            lce.save()
                    except Exception as e:
                        logger.error('Error getting or creating LearnCourseEvaluation: {}'.format(e.__str__()))
                except LearnCourse.DoesNotExist:
                    pass


    def push_courses_to_wcw(self, learn_courses=None):
        """
        Create/Update speakers/courses/products in APA Learn from data in Django/postgres
        :return: response message
        """
        print("TOP OF PUSH COURSES METHOD ++++++++++++++++++++++++++++++++++++++")
        print("learn_courses is ", learn_courses)
        if not learn_courses:
            learn_courses = LearnCourse.objects.filter(
                code__contains=LEARN_COURSE_PREFIX,
                status__in=["A","H"],
                publish_status="DRAFT")
        print("AFTER IF learn_courses is ", learn_courses)

        for lc in learn_courses:
            print("GOT IN *******************************************")

            # 1. Create/update speaker pages
            speaker_pages = ""

            speaker_roles = ContactRole.objects.filter(
                content=lc,
                role_type__in=("SPEAKER", "ORGANIZER", "PROPOSER", "ORGANIZER&SPEAKER", "MOBILEWORKSHOPGUIDE",
                               "MODERATOR", "ORGANIZER&MODERATOR", "LEADPOSTERPRESENTER", "POSTERPRESENTER",
                               "MOBILEWORKSHOPCOORDINATOR", "LEADMOBILEWORKSHOPCOORDINATOR", "AUTHOR"),
            ).order_by("contact__last_name")

            for sr in speaker_roles:
                c = sr.contact
                if c:
                    f = c.first_name or ""
                    m = c.middle_name or ""
                    l = c.last_name or ""
                    un = c.user.username
                    name = c.full_title() or ""
                    try:
                        uniqueid = f + m + l + un
                    except Exception as e:
                        uniqueid = "BAD_SPEAKER_DATA"
                        print("Exception creating unique id for speaker page: ", e)
                    print("\nSTART OF GET CUSTOM PAGE--------")
                    wcw_get_helper = WCWCallHelper("GetCustomPage")(
                        uniqueid=uniqueid
                    )
                    print("wcw_get_helper is ", wcw_get_helper)

                    exception = wcw_get_helper.get('exception', None)
                    success = wcw_get_helper.get('success', None)
                    if exception or success == False:
                        method = "CreateCustomPage"
                    else:
                        method = "UpdateCustomPage"

                    print("START OF CREATE/UPDATE CUSTOM PAGE")
                    wcw_post_response = WCWCallHelper(method, http_method='post')(
                        name=name,
                        uniqueid=uniqueid,
                        visible=0,
                        content=c.bio
                    )
                    print("wcw_post_response is ", wcw_post_response)
                    print("END OF CUSTOM PAGE-----------------------\n")
                    fhtm = '<ul><li><a href=\"'
                    mhtm = '\">'
                    bhtm = '</a></li></ul>'
                    url = wcw_post_response.get("url","")
                    speaker_html = fhtm + url + mhtm + name + bhtm
                    speaker_pages = speaker_pages + speaker_html
                    sr.external_bio_url = url
                    sr.save()

            # 2. Create/update course
            print("START OF GET COURSE -----------------------")
            wcw_get_helper = WCWCallHelper("GetCourse")(
                productcode=lc.code
            )
            print("wcw_get_helper is ", wcw_get_helper)
            print("START OF CREATE/UPDATE COURSE ------------------")
            exception = wcw_get_helper.get('exception', None)
            success = wcw_get_helper.get('success', None)
            if exception or success == False:
                method = "CreateCourse"
            else:
                method = "UpdateCourse"
            if ENVIRONMENT_NAME == 'LOCAL' or ENVIRONMENT_NAME == 'STAGING':
                templateid = LMS_TEMPLATE_ID_STAGING
                course_url_stem = STAGING_COURSE_URL
                product_url_stem = STAGING_PRODUCT_URL
            elif ENVIRONMENT_NAME == 'PROD':
                templateid = LMS_TEMPLATE_ID_PROD
                course_url_stem = PROD_COURSE_URL
                product_url_stem = PROD_PRODUCT_URL

            tags = [t.title for t in lc.taxo_topics.all()]
            tags_string = ", ".join(tags) or "No_Tags"

            if method == "CreateCourse":
                wcw_post_response = WCWCallHelper(method, http_method='post')(
                    templateid=templateid,
                    category=WCW_COURSE_CATEGORY_ID,
                    productcode=lc.code,
                    shortname=lc.title,
                    fullname=lc.title,
                    summary=lc.description,
                    # startdate=lc.begin_time.replace(month=5,day=7).timestamp(),
                    startdate=lc.begin_time.timestamp(),
                    enddate=lc.end_time.timestamp(),
                    tags=tags_string,
                    visible=0
                    # customfields={"somefield": "somevalue"}
                )
                print("wcw_post_response is ", wcw_post_response)
            else:
                wcw_post_response = WCWCallHelper(method, http_method='post')(
                    productcode=lc.code,
                    shortname=lc.title,
                    fullname=lc.title,
                    summary=lc.description,
                    # startdate=lc.begin_time.replace(month=5,day=7).timestamp(),
                    startdate=lc.begin_time.timestamp(),
                    enddate=lc.end_time.timestamp(),
                    tags=tags_string,
                    visible=0
                    # customfields={"somefield": "somevalue"}
                )
                print("wcw_post_response is ", wcw_post_response)
            page_id = wcw_post_response.get("id", None)
            url = course_url_stem + str(page_id)
            lc.digital_product_url = url
            print("END OF COURSE -------------------------\n")

            # 3. Create/update product
            print("START OF GET PRODUCT --------------------")
            wcw_get_helper = WCWCallHelper("GetCatalogProduct")(
                productid=lc.code,
                # name=lc.title
            )
            print("wcw_get_helper is ", wcw_get_helper)
            print("START OF CREATE/UPDATE PRODUCT ---------------")
            exception = wcw_get_helper.get('exception', None)
            success = wcw_get_helper.get('success', None)
            if exception or success == False:
                method = "CreateCatalogProduct"
            else:
                method = "UpdateCatalogProduct"

            # tags = [t.title for t in lc.taxo_topics.all()]

            base_price = lc.product.prices.filter(
                option_code="INDIVIDUAL",
                required_groups__isnull=True
            ).first()

            base_member_price = lc.product.prices.filter(
                option_code="INDIVIDUAL",
                required_groups__name="member"
            ).first()

            credit_types = ""
            credit_html_blurb = ""
            credit_amount = decimal.Decimal("0.0")

            if lc.cm_targeted_credits:
                credit_types = credit_types + ", Sustainability & Resilience" if credit_types else "Sustainability & Resilience"
                credit_html_blurb = CM_SUSTAINABILITY_HTML.format(lc.cm_targeted_credits)
            elif lc.cm_equity_credits:
                credit_types = credit_types + ", Equity" if credit_types else "Equity"
                credit_html_blurb = CM_EQUITY_HTML.format(lc.cm_equity_credits)
            elif lc.cm_ethics_approved:
                credit_types = credit_types + ", Ethics" if credit_types else "Ethics"
                credit_html_blurb = CM_ETHICS_HTML.format(lc.cm_ethics_approved)
            elif lc.cm_law_approved:
                credit_types = credit_types + ", Law" if credit_types else "Law"
                credit_html_blurb = CM_LAW_HTML.format(lc.cm_law_approved)
            elif lc.cm_approved:
                credit_amount = lc.cm_approved
                credit_types+="CM"
                credit_html_blurb = CM_HTML.format(credit_amount)

            lci = LearnCourseInfo.objects.filter(
                learncourse=lc
            ).first()

            duration = round(lci.run_time.seconds / 60.) if lci else None
            raw_description = (lc.text or "") + (lc.learning_objectives or "")
            wcw_description = raw_description.replace("</body></html>", "") + "</body></html>"

            if method == "UpdateCatalogProduct":
                wcw_post_response = WCWCallHelper(method, http_method='post')(
                    productid=lc.code,
                    name=lc.title,
                    shortdescription=lc.description or "",
                    description=wcw_description,
                    # startdate=int(lc.begin_time.replace(month=5,day=7).timestamp()),
                    startdate=int(lc.begin_time.timestamp()),
                    enddate=int(lc.end_time.timestamp()),
                    tags=tags_string,
                    visible=0,
                    customfields={
                        # "group_price": "<a href=\"https://learn.planning.org/mod/page/view.php?id=5236\">Learn More=>",
                        "group_price": GROUP_PRICING_HTML,
                        "speakers": speaker_pages,
                        "price_member": base_member_price.price.to_eng_string() if base_member_price else None,
                        "price": base_price.price.to_eng_string() if base_price else None,
                        "coursecredits": credit_html_blurb,
                        "credit_type": credit_types,
                        "credit_amount": credit_amount.to_eng_string(),
                        "duration": duration
                    }
                )
            else:
                wcw_post_response = WCWCallHelper(method, http_method='post')(
                    type="Course",
                    productid=lc.code,
                    name=lc.title,
                    shortdescription=lc.description or "",
                    description=wcw_description,
                    # startdate=int(lc.begin_time.replace(month=5,day=7).timestamp()),
                    startdate=int(lc.begin_time.timestamp()),
                    enddate=int(lc.end_time.timestamp()),
                    tags=tags_string,
                    visible=0,
                    customfields={
                        # "group_price": "<a href=\"https://learn.planning.org/mod/page/view.php?id=5236\">Learn More=>",
                        "group_price": GROUP_PRICING_HTML,
                        "speakers": speaker_pages,
                        "price_member": float(base_member_price.price) if base_member_price else None,
                        "price": float(base_price.price) if base_price else None,
                        "coursecredits": credit_html_blurb,
                        "credit_type": credit_types,
                        "credit_amount": float(credit_amount),
                        "duration": duration
                    }
                )
            print("wcw_post_response is ", wcw_post_response)
            if lci:
                page_id = wcw_post_response.get("id", None)
                url = product_url_stem + str(page_id)
                lci.lms_product_page_url = url
                lci.save()
            lc.save()
            lc.publish()
            lc.solr_publish()
            print("END OF PRODUCT -----------------------------------\n\n\n")

    def delete_courses_from_wcw(self, learn_courses=None):
        """
        Delete WCW courses
        :param learn_courses:
        :return: None
        """
        # Removing this so user must specify queryset, instead of
        # defaulting to delete all:
        # if not learn_courses:
        #     learn_courses = LearnCourse.objects.filter(
        #         code__contains="NPC20")

        for lc in learn_courses:

            # 1. Create/update speaker pages
            speaker_roles = ContactRole.objects.filter(
                content=lc,
                role_type__in=("SPEAKER", "ORGANIZER", "PROPOSER", "ORGANIZER&SPEAKER", "MOBILEWORKSHOPGUIDE",
                               "MODERATOR", "ORGANIZER&MODERATOR", "LEADPOSTERPRESENTER", "POSTERPRESENTER",
                               "MOBILEWORKSHOPCOORDINATOR", "LEADMOBILEWORKSHOPCOORDINATOR", "AUTHOR"),
            ).order_by("last_name")

            # 1. Delete Custom Pages (Speakers)
            for sr in speaker_roles:
                c = sr.contact
                if c:
                    f = c.first_name or ""
                    m = c.middle_name or ""
                    l = c.last_name or ""
                    un = c.user.username
                    try:
                        uniqueid = f + m + l + un
                    except Exception as e:
                        uniqueid = "BAD_SPEAKER_DATA"
                    #     print("Exception creating unique id for speaker page: ", e)
                    # print("\nSTART OF DELETE CUSTOM PAGE--------")
                    wcw_delete_helper = WCWCallHelper("DeleteCustomPage")(
                        uniqueid=uniqueid
                    )
                    # print("wcw_delete_helper for CUSTOM PAGE is ", wcw_delete_helper)

            # 2. Delete Courses
            wcw_delete_helper = WCWCallHelper("DeleteCourse")(
                productcode=lc.code
            )
            # print("wcw_delete_helper FOR COURSE is ", wcw_delete_helper)

            # 3. Delete Products
            wcw_delete_helper = WCWCallHelper("DeleteCatalogProduct")(
                productid=lc.code
            )
            # print("wcw_delete_helper FOR PRODUCT is ", wcw_delete_helper)
