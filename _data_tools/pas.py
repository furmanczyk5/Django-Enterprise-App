from decimal import Decimal

from django.contrib.auth.models import Group
from django.db.models import Q

from media.models import Media, Document
from publications.models import Publication
from pages.models import Page
from store.models import Product, ProductPrice

# SHOULD THIS BE JUST PUBLISHED OR ALL?
# should we copy on draft and publish/solr_publish?
def add_group(obj, grp):
    obj.permission_groups.add(grp)
    obj.publish()
    obj.solr_publish()

# Publish the object (content) in order to publish product and prices
def change_pas_book_prices_groups(queryset=None):
    mem_grp = Group.objects.get(name='member')
    pas_grp = Group.objects.get(name='PAS')
    if not queryset:
        queryset = Book.objects.filter(title__contains='PAS', publish_status='DRAFT')
    for obj in queryset:
        for product_price in obj.product.prices.all():
            if product_price.title == "List Price":
                product_price.price = Decimal('25.00')
                product_price.save()
                obj.publish()
                obj.solr_publish()
            elif product_price.title == 'PAS subscriber':
                product_price.title = 'APA member & PAS subscriber'
                product_price.price = Decimal('0.00')
                current_groups = product_price.required_groups.all()
                if not mem_grp in current_groups:
                    product_price.required_groups.add(mem_grp)
                if not pas_grp in current_groups:
                    product_price.required_groups.add(pas_grp)
                product_price.save()
                obj.publish()
                obj.solr_publish()

# to change EIP document prices:
# get the group of about 35 eip documents that do not have eip in the title
# filenames that contain "EIP" (with titles that don't) and/or associated product codes that have "EIP_E_IP"

# split this in two functions?
# 1) create a new APA member & PAS subscriber product price and add it to the eip product
# associated with the eip document (set price to 0) add PAS and member groups
# 2) update any List Price that is not 30 to 30

def change_eip_document_prices_groups(queryset=None):
    mem_grp = Group.objects.get(name='member')
    pas_grp = Group.objects.get(name='PAS')
    if not queryset:
        queryset = Document.objects.filter(product__code__contains='EIP_E_IP', publish_status='DRAFT').exclude(master__id='9026630')
    for obj in queryset:
        print(obj.title)
        print(obj.master.id)
        # create a product price for members/suscribers -- how?
        # no -- the products already exist!
        pp, pp_created = ProductPrice.objects.get_or_create(
                title = 'APA member & PAS subscriber',
                product=obj.product, price=0.00, priority=0)

        current_groups = pp.required_groups.all()
        if mem_grp not in current_groups:
            pp.required_groups.add(mem_grp)
        if pas_grp not in current_groups:
            pp.required_groups.add(pas_grp)

        for product_price in obj.product.prices.all():
            if product_price.title == "List Price" and product_price.price != Decimal('30.00'):
                product_price.price = Decimal('30.00')
        pp.save()
        obj.publish()
        obj.solr_publish()

# error: OSError: File does not exist: document/Zoning-Practice-2008-02.png
def copy_description_to_text(docs=None):
    if not docs:
        docs = Document.objects.filter(publish_status='DRAFT')
    for doc in docs:
        description = doc.description
        if description and not doc.text:
            doc.text = description
            doc.save()
            doc.publish()
            doc.solr_publish()

def add_member_to_eip(pages=None):
    mem_grp = Group.objects.get(name='member')
    pas_grp = Group.objects.get(name='PAS')
    if not pages:
        pages = Page.objects.filter(url__contains='/pas/infopackets', publish_status='DRAFT')
    for page in pages:
        current_groups = page.permission_groups.all()
        # also, only put this on the non-public pages (those that already have PAS)
        if pas_grp in current_groups and not mem_grp in current_groups:
            add_group(page, mem_grp)
        # not this because some pages may be public ?
        # if not pas_grp in page.permission_groups.all():
        #     add_group(page, pas_grp)

def add_member_to_memo(queryset=None):
    mem_grp = Group.objects.get(name='member')
    if not queryset:
        queryset = Page.objects.filter(url__regex=r'^/pas/memo/2[0-9]', publish_status='DRAFT')
    for obj in queryset:
        if not mem_grp in obj.permission_groups.all():
            add_group(obj, mem_grp)

def unpublish_you_asked(pages=None):
    if not pages:
        pages = Page.objects.filter(url__contains='/pas/youasked', publish_status='DRAFT')
    for page in pages:
        if page.status == 'A':
            page.status = 'I'
            page.save()
            page.publish()
            page.solr_publish()

# is this the right queryset?
def add_member_pas_to_books(queryset=None):
    mem_grp = Group.objects.get(name='member')
    pas_grp = Group.objects.get(name='PAS')
    if not queryset:
        queryset = Book.objects.filter(title__contains='PAS', publish_status='DRAFT')
    for obj in queryset:
        current_groups = obj.permission_groups.all()
        if not mem_grp in current_groups:
            add_group(obj, mem_grp)
        if not pas_grp in current_groups:
            add_group(obj, pas_grp)

def add_member_pas_to_eip_documents(queryset=None):
    mem_grp = Group.objects.get(name='member')
    pas_grp = Group.objects.get(name='PAS')
    if not queryset:
        # these have no products:
        # queryset = Document.objects.filter(title__contains='EIP', publish_status='DRAFT')
        queryset = Document.objects.filter(product__code__contains='EIP_E_IP', publish_status='DRAFT').exclude(master__id='9026630')
    # add both -- ticket says only member, but all should have both unless exception that has none
    for obj in queryset:
        print(obj.title)
        print(obj.master.id)
        if not mem_grp in obj.permission_groups.all():
            add_group(obj, mem_grp)
        if not pas_grp in obj.permission_groups.all():
            add_group(obj, pas_grp)

def add_member_to_memo_documents(queryset=None):
    mem_grp = Group.objects.get(name='member')
    pas_grp = Group.objects.get(name='PAS')
    if not queryset:
        queryset = Document.objects.filter(title__contains='PAS Memo', publish_status='DRAFT')
    for obj in queryset:
        current_groups = obj.permission_groups.all()
        if pas_grp in current_groups and not mem_grp in current_groups:
            add_group(obj, mem_grp)

def add_member_to_quicknotes(queryset=None):
    mem_grp = Group.objects.get(name='member')
    pas_grp = Group.objects.get(name='PAS')
    if not queryset:
        queryset = Document.objects.filter(title__contains='PAS Quick', publish_status='DRAFT')
    for obj in queryset:
        current_groups = obj.permission_groups.all()
        if pas_grp in current_groups and not mem_grp in current_groups:
            add_group(obj, mem_grp)

# THERE IS ALSO CODE UPDATING PAS CODES IN on_demand.py
# 5872-Django-product-codes-for-PAS-Reports-need-to-be-changed-to-match-iMIS-codes
# updpas = update pas reports
def updpas(qs=None):
    # update/add code into content.code, product.code and product.imis_code
    if not qs:
        qs = Publication.objects.filter(resource_type="REPORT")
    for pub in qs:
        try:
            code = pub.code or pub.product.code or pub.product.imis_code
            print("original code is ", code)
        except:
            code = None
            print("Could not get a code")
        if code:
            if code.find("BOOK_P") == 0:
                code = code.replace("BOOK_P", "PAS_")
                if code.endswith("P1"):
                    code = code[:-2]
                set_all_codes(pub, code)
            elif code == ("BOOK_AE1757"):
                code = "PAS_561"
                set_all_codes(pub, code)
            # this case doesn't exist on pas reports so commenting out
            # elif code.find("PAS_") == 0:
            #     # correct code already on something
            #     set_all_codes(pub, code)
        else:
            print("NO CODE FOUND ANYWHERE -- STAFF NEED TO CREATE")
            print(pub)
            print()

def updmem(qs=None):
    # update/add code into content.code, product.code and product.imis_code
    if not qs:
        qs = mems=Publication.objects.filter(subtitle__contains="PAS Memo")
    for pub in qs:
        try:
            code = pub.code or pub.product.code or pub.product.imis_code
            print("original code is ", code)
        except:
            code = None
            print("Could not get a code")
        if code:
            if code.find("PAS_M_") == 0:
                code = code.replace("_", "-")
                code = code.replace("PAS-M", "PAS_M")
                set_all_codes(pub, code)
            elif code.find("PASM_E_I_") == 0:
                code = code.replace("PASM_E_I_", "PAS_M_")
                code = code.replace("_", "-")
                code = code.replace("PAS-M", "PAS_M")
                set_all_codes(pub, code)
            elif code.find("PAS_M-") == 0:
                # correct code already on something
                set_all_codes(pub, code)
        else:
            print("NO CODE FOUND ANYWHERE -- STAFF NEED TO CREATE")
            print(pub)
            print()

# PAS QuickNotes or Zoning Practice
def updqz(qs=None):
    # update/add code into content.code, product.code and product.imis_code
    if not qs:
        qs = Publication.objects.filter(
            Q(subtitle__contains="PAS QuickNotes") |
            Q(subtitle__contains="Zoning Practice"))
    for pub in qs:
        try:
            code = pub.code or pub.product.code or pub.product.imis_code
            print("original code is ", code)
        except:
            code = None
            print("Could not get a code")
        if code:
            if code.find("ZP_E_") == 0 or code.find("PAS_Q_E_") == 0:
                # correct code already on something
                set_all_codes(pub, code)
            else:
                print("code that no match is ", code)
                print(pub)
                print()
        else:
            print("NO CODE FOUND ANYWHERE -- STAFF NEED TO CREATE")
            print(pub)
            print()

def set_all_codes(pub, code):
    pub.code = code
    pub.save()
    try:
        p = Product.objects.get(content=pub)
    except Exception:
        p = None
    if p:
        p.code = code
        p.imis_code = code
        p.save()
        print("product is ", p.title)
    print("publication is ", pub)
    print("publication code is ", pub.code)
    print()


# FOR TESTING LOGIC IN THE SHELL
def foo():
    code = "BOOK_AE1757"
    if code.find("BOOK_P") == 0:
        code = code.replace("BOOK_P", "PAS_")
        if code.endswith("P1"):
            code = code[:-2]
        # process_codes(pub, code)
        print(code)
    elif code == ("BOOK_AE1757"):
        code = "PAS_561"
        # process_codes(pub, code)
        print(code)

def foo2():
    code = "PAS_M-20XX-XX"
    if code:
        # PAS_M-20XX-XX from both PAS_M_20XX_XX and PASM_E_I_20XX_XX
        if code.find("PAS_M_") == 0:
            code = code.replace("_", "-")
            code = code.replace("PAS-M", "PAS_M")
            # set_all_codes(pub, code)
            print(code)
        elif code.find("PASM_E_I_") == 0:
            code = code.replace("PASM_E_I_", "PAS_M_")
            code = code.replace("_", "-")
            code = code.replace("PAS-M", "PAS_M")
            # set_all_codes(pub, code)
            print(code)
        elif code.find("PAS_M-") == 0:
            # correct code already on something
            # set_all_codes(pub, code)
            print(code)
    else:
        # else if no code we need to pull from subtitle and build it
        # no if there is no code anywhere it will have to be created by staff
        print("NO CODE FOUND ANYWHERE")
        print(pub)
        print()
