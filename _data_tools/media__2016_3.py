import re
import sys

from bs4 import BeautifulSoup

from content.models import Content
from media.models import Document, Media

def fix_document_links():

    UPLOAD_STORAGE_ROOT = 'planning-org-uploaded-media.s3.amazonaws.com'
    MATCH_PATTERN = r'planning-org-uploaded-media\.s3\.amazonaws\.com.*(document.*)'

    content = Content.objects.filter(text__contains=UPLOAD_STORAGE_ROOT)

    print("Querying for all Content records containing text: '%s'" % UPLOAD_STORAGE_ROOT)

    stats = {
        "TOTAL":content.count(),
        "SAVED":[],
        "NOTHING":[],
        "FAILED":[],
        "FAILED_LINKS":[]
    }

    print("%s total records" % stats["TOTAL"])

    count = 0

    for c in content:

        count += 1 

        soup = BeautifulSoup(c.text)
        is_success = True
        is_changed = False # assume no change

        for link in soup.select('a[href*=%s]' % UPLOAD_STORAGE_ROOT):

            href = link['href']
            print("    %s" % href )
            match = re.search(MATCH_PATTERN, href)

            if match:
                try:
                    filename = match.groups()[0]
                    document = Document.objects.get(uploaded_file=filename, publish_status="PUBLISHED")
                    new_href = "/media/document/%s/" % document.master_id
                    link['href'] = new_href
                    is_changed = True
                    print("        %s" % "match" )
                except:
                    stats["FAILED_LINKS"].append(href)
                    is_success = False
            else:
                pass

        if not is_success:
            stats["FAILED"].append(c)
            print("FAILED: %.2f%% complete" % (float(count/stats["TOTAL"])*100.0,) )

        if is_changed:
            c.text = str(soup)
            c.save()
            stats["SAVED"].append(c)
            print("SAVED: %.2f%% complete" % (float(count/stats["TOTAL"])*100.0,) )
        else:
            stats["NOTHING"].append(c)
            print("NOTHING: %.2f%% complete" % (float(count/stats["TOTAL"])*100.0,) )
            

    print("Complete!")  

    return stats

def reset_media_templates():
    """
    script to assign template for all existing media records
    """
    Media.objects.update(template="media/newtheme/details.html")
    print("assigned template for all existing media records")


def create_draft_media_from_published():
    """
    script to create draft copies of all media with live copies but no draft copy,
    uses the publish function
    """
    print("Querying for published media that need draft copies...")
    live_media = Media.objects.filter(
        publish_status="PUBLISHED",
        master__content_draft__isnull=True
    )

    TOTAL = live_media.count()
    count = 0
    failures = []

    for m in live_media:
        count += 1

        try:
            m.__class__ = m.get_media_proxy_class()
            m.publish(publish_type="DRAFT")
            print("%s : (%s/%s) %.2f%% complete" % (m.title, count, TOTAL, float(count/TOTAL)*100.0) )
        except:
            s = sys.exc_info()
            failures.append((m.id, s[1]))
            print("FAILED (id=%s): %s" % (m.master, s[1]) )


    if not failures:
        print("Flawless Victory!")
    else:
        print("Complete with %s Failed" % len(failures))
        for x in failures:
            print("    %s: %s" % (x[0], x[1]))


def fix_external_urls():
    """
    Looks through text field on Content records and removes the index.htm (or html) from internal links
    """

    FILTER_BY = "planning-org-uploaded-media.s3.amazonaws.com"
    MATCH_PATTERN = r"planning-org-uploaded-media\.s3\.amazonaws\.com.*(http.*)"

    content = Content.objects.filter(text__contains=FILTER_BY)

    print("Querying for all Content records containing text: '%s'" % FILTER_BY)

    TOTAL = content.count()

    print("%s total records" % TOTAL)

    count = 0

    for c in content:

        print(c)
        print(c.url or " - No Url - ")
        print()

        count += 1 
        soup = BeautifulSoup(c.text)
        changed = False

        links = soup.select('a[href*=%s]' % FILTER_BY)

        for link in links:

            href = link['href']
            match = re.search(MATCH_PATTERN, href)

            if match:
                new_href = match.groups()[0]

                print("    old: %s" % href )
                print("    new: %s" % new_href )
                print()

                link['href'] = new_href

                changed = True

        if changed:
            c.text = str(soup)
            c.save()
            percent_complete = float(count/TOTAL)*float(100.0)
            print("  SAVED: %.2f%% complete" % percent_complete )

        print("----")
        print()
            
    print("Complete!")



