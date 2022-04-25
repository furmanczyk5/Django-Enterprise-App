
# from django.contrib.auth.models import Permission, User
from content.models import Content
from publications.models import Publication, Book, EBook, Report
from events.models import Course
from media.models import Document
from store.models import Product
from _data_tools import permissions


import django
django.setup()

def update_all():
    update_reports()
    update_templates()
    update_permissions()

def update_reports():
    pas_reports_books = Publication.objects.filter(resource_type="BOOK", title__contains="PAS", publication_format="DOWNLOAD_PDF")
    pas_reports_books.update(resource_type="REPORT")
    pas_reports_ebooks = Publication.objects.filter(resource_type="EBOOK", title__contains="PAS", publication_format="DOWNLOAD_PDF")
    pas_reports_ebooks.update(resource_type="REPORT")
    
    products_reports = Product.objects.filter(content__resource_type="REPORT")
    products_reports.update(product_type="DIGITAL_PUBLICATION")

    reports_published = Report.objects.filter(publish_status="PUBLISHED")

    for r in reports_published:
        r.solr_publish()
        print(r.title)

def update_templates():
    books = Book.objects.all()
    ebooks = EBook.objects.all()
    books.update(template="store/newtheme/product/details.html")
    ebooks.update(template="store/newtheme/product/details.html")
    ondemands = Course.objects.filter(product__isnull=False)
    ondemands.update(template="store/newtheme/product/details.html")
    documents = Document.objects.filter(product__isnull=False)
    documents.update(template="store/newtheme/product/details.html", show_content_without_groups=True)
    reports = Report.objects.all()
    reports.update(template="store/newtheme/product/details.html", show_content_without_groups=True)


def update_permissions():
    permissions.proxy_perm_create()
    permissions.assign_app_perm("publications",
        ("change","add"),
        ("staff-editor","staff-marketing","staff-publications","staff-communications") )

