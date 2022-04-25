import datetime, pytz

from decimal import Decimal

from store.models import ContentProduct, Product, ProductPrice
from events.models import Event
from submissions.models import Period
from cm.models import Period as CMPeriod
from exam.models import ApplicationCategory, Exam
"""
Script to create instances for new:
 - categories
 - periods
 - questions? (not sure)
 - products
 - prices

this should already be handled by normal exam process:
 - exam categories
 - exams
"""

# Chapter Jobs Price DAta:
ENROLL_price_title_stem="AICP Candidate Enrollment"

REG_price_title_stem="AICP Exam Registration"
NEW_REG_price_title_stem="AICP Candidate Exam Registration"

CERT_price_title_stem="AICP Exam Application"

ENROLL_price_codes="""CAND_ENR"""

REG_price_codes="""CAND_ENR_A
CAND_T_100
CAND_T_0"""

CERT_price_codes="""CAND_CERT
CAND_RESUB"""

ENROLL_prices = [
    Decimal('20.00'), 
    ]

REG_prices = [
    Decimal('100.00'), Decimal('100.00'), Decimal('0.00'), 
    ]

CERT_prices = [
    Decimal('375.00'), Decimal('0.00'),
    ]

aicp_product_gl_account_num = "440100-AU6200"
cand_reg_gl_account_num = "440100-AU6200-TEST"

REG_PRODUCT_CODE = "EXAM_REGISTRATION_AICP"
CERT_PRODUCT_CODE = "EXAMAPPLICATION_AICP"

ENROLL_PRODUCT_TYPE = 'AICP_CANDIDATE_ENROLLMENT'
REG_PRODUCT_TYPE = 'AICP_CANDIDATE_REGISTRATION'

"""
NEW price on NEW candidate enrollment product?
•	Candidate Application Fee: $20

NEW price on preexisting exam reg product?
•	Candidate Exam Registration Fee: $100 (payable each time member registers for exam)

NEW price on preexisting exam reg product?
•	Candidate Transfer Fee: $100

NEW price on preexisting exam applicaiton product?
•	Candidate AICP Application Fee: $375

nothing new? (application product/price already set up?)
•	Early Bird Resubmission Fee: $70

"""

# all codes same, except for product price code
# content product: title=title, description=title, code=code
# product: code=code, product_type='JOB_AD', imis_code=code, gl_account=gl, max_quantity=Decimal('1.00')
# product price: title, price, priority, code // for now just query for preexisting product prices for jobs


# reg product gl account #: 440100-AU6202
# app product gl account #: 440100-AU6202
# *** will also have to be published ***

# ADD EMAIL TEMPLATE
# MAKE STORE CHANGES AND OTHER MIGRATIONS ON SEPARATE BRANCH AND PUSH TO STAGING/PROD
# THEN PUSH THIS SCRIPT TO STAGING AND RUN THERE FOR TESTING


def create_candidate_product(title_stem, codes_raw, prices):
    codes=codes_raw.split('\n')
    titles = []
    for code in codes:
        titles.append(title_stem + " " + code)
    gls = aicp_product_gl_account_num
    price_tuples = []
    for i in range(0, len(titles)):
        price_tuples.append((titles[i], codes[i], prices[i]))

    for i in range(0, len(codes)):
        print("i is ", i)
        cand_enroll_cp, cand_enroll_cp_created = ContentProduct.objects.get_or_create(
            title=ENROLL_price_title_stem, description=ENROLL_price_title_stem, code=codes[i], publish_status="DRAFT")
        cand_enroll_p, cand_enroll_p_created = Product.objects.get_or_create(
            code=codes[i], content=cand_enroll_cp, product_type='AICP_CANDIDATE_ENROLLMENT', 
            imis_code="AICP_"+codes[i], gl_account=gls, max_quantity=Decimal('1.00'), publish_status="DRAFT")

        for i, toop in enumerate(price_tuples):
            prod_price, prod_price_created = ProductPrice.objects.get_or_create(
                title=toop[0], code=toop[1], price=toop[2], product=cand_enroll_p, priority=i, publish_status="DRAFT")
        cand_enroll_cp.publish()

def run_create_candidate_product():
    create_candidate_product(ENROLL_price_title_stem, ENROLL_price_codes, ENROLL_prices)

def delete_candidate_product(codes_raw):
    codes = codes=codes_raw.split('\n')
    print("codes is ", codes)
    print("len codes is ", len(codes))

    for i in range(0, len(codes)):
        queryset = ContentProduct.objects.filter(code=codes[i])
        print("i is ", i)
        print("queryset is ", queryset)
        # num_objs_deleted, num_deletions_per_obj_dict = queryset.delete()
        queryset.delete()
        print("code is ", codes[i])
        # print("num_objs_deleted is ", num_objs_deleted)
        # print("num_deletions_per_obj_dict is ", num_deletions_per_obj_dict)
        print()

def run_delete_candidate_product():
    delete_candidate_product(ENROLL_price_codes)

# CREATE REG PRODUCT -- NOPE JUST KEEP SAME REG PRODUCT
def create_candidate_reg_product(title_stem, codes_raw, prices):
    codes=codes_raw.split('\n')
    titles = []
    for code in codes:
        titles.append(title_stem + " " + code)
    gls = cand_reg_gl_account_num
    price_tuples = []
    for i in range(0, len(titles)):
        price_tuples.append((titles[i], codes[i], prices[i]))

    cand_reg_cp, cand_reg_cp_created = ContentProduct.objects.get_or_create(
        title=NEW_REG_price_title_stem, description=NEW_REG_price_title_stem, code=codes[i], publish_status="DRAFT")
    cand_reg_p, cand_reg_p_created = Product.objects.get_or_create(
        code=codes[i], content=cand_reg_cp, product_type=REG_PRODUCT_TYPE, 
        imis_code="AICP_"+codes[i], gl_account=gls, max_quantity=Decimal('1.00'), publish_status="DRAFT")

    for i, toop in enumerate(price_tuples):
        prod_price, prod_price_created = ProductPrice.objects.get_or_create(
            title=toop[0], code=toop[1], price=toop[2], product=cand_reg_p, priority=i, publish_status="DRAFT")
    cand_reg_cp.publish()

def run_create_candidate_reg_product():
    create_candidate_reg_product(NEW_REG_price_title_stem, REG_price_codes, REG_prices)

def delete_candidate_reg_product(codes_raw):
    codes = codes=codes_raw.split('\n')
    print("codes is ", codes)
    print("len codes is ", len(codes))

    for i in range(0, len(codes)):
        queryset = ContentProduct.objects.filter(code=codes[i])
        print("i is ", i)
        print("queryset is ", queryset)
        # num_objs_deleted, num_deletions_per_obj_dict = queryset.delete()
        queryset.delete()
        print("code is ", codes[i])
        # print("num_objs_deleted is ", num_objs_deleted)
        # print("num_deletions_per_obj_dict is ", num_deletions_per_obj_dict)
        print()

def run_delete_candidate_reg_product():
    delete_candidate_reg_product(REG_price_codes)

# ALSO HAVE TO CREATE THE SUBMISSION CATEGORIES AND PERIODS FOR EVERY CHAPTER JOB PRODUCT

# create new prices on application/registration products
def update_related_products(title_stem, codes_raw, prices, product_code):
    codes=codes_raw.split('\n')
    titles = []
    for code in codes:
        titles.append(title_stem + " " + code)
    price_tuples = []
    for i in range(0, len(titles)):
        price_tuples.append((titles[i], codes[i], prices[i]))
    print("codes is ", codes)
    print("titles is ", titles)
    print("price tuples is ", price_tuples)
    product = Product.objects.get(code=product_code, publish_status="DRAFT")
    print("product is ", product)
    base_priority = product.prices.count()

    for i, toop in enumerate(price_tuples):
        prod_price, prod_price_created = ProductPrice.objects.get_or_create(
            title=toop[0], code=toop[1], price=toop[2], product=product, priority=base_priority+i, publish_status="DRAFT")
        print("product price is ", prod_price)
    product.content.publish()

def delete_related_updates(codes_raw):
    codes=codes_raw.split('\n')
    print("codes is ", codes)

    for i, code in enumerate(codes):
        print("i is ", i)
        queryset = ProductPrice.objects.filter(code=code)
        print("i is ", i)
        # print("queryset is ", queryset)
        queryset.delete()
        # num_objs_deleted, num_deletions_per_obj_dict = queryset.delete()
        print("code is ", code)
        # print("num_objs_deleted is ", num_objs_deleted)
        # print("num_deletions_per_obj_dict is ", num_deletions_per_obj_dict)
        print()

def run_update_related_products():
	update_related_products(REG_price_title_stem, REG_price_codes, REG_prices, REG_PRODUCT_CODE)
	update_related_products(CERT_price_title_stem, CERT_price_codes, CERT_prices, CERT_PRODUCT_CODE)

def run_delete_related_updates():
	delete_related_updates(REG_price_codes)
	delete_related_updates(CERT_price_codes)

def create_candidate_categories(codes_raw):
    codes = codes_raw.split('\n')
    related_products = Product.objects.filter(
        publish_status='PUBLISHED', code__in=codes)
    for prod in related_products:
        new_cat, created = ApplicationCategory.objects.get_or_create(
            code=prod.code,
            title=prod.content.title,
            product_master=prod.content.master,
            description=prod.content.title,
            )
        tz = pytz.timezone("US/Central")
        nov_1_2017 = tz.localize(datetime.datetime(year=2017, month=11, day=1))
        oct_31_2018 = tz.localize(datetime.datetime(year=2018, month=10, day=31))
        new_per, created = Period.objects.get_or_create(
            title=prod.content.title,
            content_type='EXAM',	
            begin_time=nov_1_2017,
            end_time=oct_31_2018,
            category=new_cat
            )
        print("category, created: ", new_cat, created)
        print("period, created: ", new_per, created)

def delete_candidate_categories(codes_raw):
    codes = codes_raw.split('\n')
    related_products = Product.objects.filter(
        publish_status='PUBLISHED', code__in=codes)
    for prod in related_products:
        queryset = ApplicationCategory.objects.filter(
            code=prod.code,
            )
        queryset.delete()
        print("product related to ApplicationCategory deleted is: ", prod)

def run_create_candidate_categories():
	create_candidate_categories(ENROLL_price_codes)

def run_delete_candidate_categories():
    delete_candidate_categories(ENROLL_price_codes)

# NEXT: CREATE A DUMMY EXAM, and category, period to go with it. ALREADY HAVE THE CATEGORY, PERIOD ABOVE?? same for product, exam_app and exam??
        # YOU MUST SUPPLY AN EXAM TO AN ExamApplication record -- IT CANNOT BE NULL -- NEED A SPECIAL DUMMY CANDIDATE EXAM --
        # WITH A CATEGORY/PERIOD THAT ARE ALWAYS VALID - UNTIL 2099

# WILL NOT NEED THESE -- WILL ALWAYS BE PUTTING "CURRENT" EXAM ON ANY APP OR REG RECORD
def create_dummy_candidate_exam():
    """
    A placeholder exam on the enroll app until they try to register, at which point this 
    gets overwritten with a real exam. then if they pass exam and apply for certification,
    they will have the same exam record tied to all three records (enroll app, reg, cert app)
    """
    # nov_1_2017 = datetime.datetime(year=2017, month=11, day=1)
    # oct_31_2031 = datetime.datetime(year=2031, month=10, day=31)
    e, created = Exam.objects.get_or_create(
        code='CAND', title='AICP Candidate Placeholder Exam',
        description='AICP Candidate Placeholder Exam -- will be overwritten by real exam when candidate registers to take exam.',
        # TRY WITHOUT THESE FOR NOW -- BETTER IF THIS EXAM IS TECHNICALLY NOT OPEN
        # start_time=nov_1_2017,
        # end_time=oct_31_2031,
    # ASSUME THESE ALL UNNECESSARY:
    # registration_start_time = models.DateTimeField(blank=True, null=True) 
    # registration_end_time = models.DateTimeField(blank=True, null=True)
    # application_start_time = models.DateTimeField(blank=True, null=True)
    # application_end_time = models.DateTimeField(blank=True, null=True)
    # application_early_end_time = models.DateTimeField(blank=True, null=True)
    # previous_exams = models.ManyToManyField("Exam", blank=True)
    # product = models.ForeignKey("store.Product", blank=True, null=True)
    )
    print("exam is ", e)
    print("exam created is ", created)
    print()

def delete_dummy_candidate_exam():
    queryset = Exam.objects.filter(code='CAND')
    print("dummy candidate exam queryset is ", queryset)
    queryset.delete()

def run_create_dummy_candidate_exam():
    create_dummy_candidate_exam()

def run_delete_dummy_candidate_exam():
    delete_dummy_candidate_exam()

def create_dummy_mentee_event():
    """
    A placeholder event to put on the Mentee when it is created if enrollee chooses
    to sign up for mentor program
    """
    e, created = Event.objects.get_or_create(
        code='CAND', title='AICP Candidate Placeholder Event',
        description='AICP Candidate Placeholder Event.',
    )
    print("event is ", e)
    print("event created is ", created)
    print()

def delete_dummy_mentee_event():
    queryset = Event.objects.filter(code='CAND')
    print("dummy mentee event queryset is ", queryset)
    queryset.delete()

def run_create_dummy_mentee_event():
    create_dummy_mentee_event()

def run_delete_dummy_mentee_event():
    delete_dummy_mentee_event()

# NEXT: CREATE/DELETE "CAND" CM PERIOD

def create_candidate_cm_period():
    # what attributes do we set?
    tz = pytz.timezone("US/Central")
    nov_1_2017 = tz.localize(datetime.datetime(year=2017, month=11, day=1))
    nov_1_2047 = tz.localize(datetime.datetime(year=2047, month=11, day=1))
    four_months = datetime.timedelta(days=120)
    cm_period, created = CMPeriod.objects.get_or_create(code="CAND")
    if created:
        cm_period.status='A'
        cm_period.begin_time = nov_1_2017
        cm_period.end_time = nov_1_2047
        cm_period.description = "A special CM period for AICP enrollees that is always open."
        cm_period.grace_end_time = nov_1_2047 + four_months
        cm_period.title = "AICP Enrollee CM Period"
        cm_period.save()

def delete_candidate_cm_period():
    period = CMPeriod.objects.get(code="CAND")
    period.delete()

def run_create_candidate_cm_period():
    create_candidate_cm_period()

def run_delete_candidate_cm_period():
    delete_candidate_cm_period()

# WHAT ABOUT CAND APP EMAIL TEMPLATES?
# EMAILS generated WHEN
# 1. enrolled - triggered by staff action in admin
# 2. approved - cleared to register - triggered by staff action in admin

def create_all():
    run_create_candidate_product()
    run_update_related_products()
    run_create_candidate_categories()
    # run_create_dummy_candidate_exam()
    # run_create_dummy_mentee_event()
    run_create_candidate_cm_period()

def delete_all():
    run_delete_candidate_product()
    run_delete_related_updates()
    run_delete_candidate_categories()
    # run_delete_dummy_candidate_exam()
    # run_delete_dummy_mentee_event()
    run_delete_candidate_cm_period()



