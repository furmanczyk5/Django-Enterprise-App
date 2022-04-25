import re
import sys

from bs4 import BeautifulSoup

from content.models import Content, MenuItem

def fix_index_htm_links():
    """
    Looks through text field on Content records and removes the index.htm (or html) from internal links
    """

    FILTER_BY = '/index.htm'
    MATCH_PATTERN = r'(/index\.html{0,1})' # matches "/index.htm" or "/index.html"

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

            if not href.startswith("http"):
                new_href = re.sub(MATCH_PATTERN, "/", href)

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


def fix_content_urls():
    """
    updates Content url fields so that they don't use /index.htm (or .html)
    """

    FILTER_BY = '/index.htm'
    MATCH_PATTERN = r'(/index\.html{0,1})' # matches "/index.htm" or "/index.html"

    print("Querying for all Content records containing text: '%s'" % FILTER_BY)

    content = Content.objects.filter(url__contains=FILTER_BY)
    TOTAL = content.count()
    count = 0

    print("%s total records" % TOTAL)

    for c in content:

        count += 1

        print(c)
        print(c.url)
        print()

        if not c.url.startswith("http"):
            new_url = re.sub(MATCH_PATTERN, "/", c.url)

            print("    old: %s" % c.url )
            print("    new: %s" % new_url )
            print()

            c.url = new_url
            c.save()
            percent_complete = float(count/TOTAL)*float(100.0)
            print("  SAVED: %.2f%% complete" % percent_complete )
            
        print("----")
        print()
            
    print("Complete!")


def fix_menuitem_urls():
    """
    updates MenuItem url fields so that they don't use /index.htm (or .html)
    """

    FILTER_BY = '/index.htm'
    MATCH_PATTERN = r'(/index\.html{0,1})' # matches "/index.htm" or "/index.html"

    print("Querying for all MenuItem records containing text: '%s'" % FILTER_BY)

    menu_items = MenuItem.objects.filter(url__contains=FILTER_BY)
    TOTAL = menu_items.count()
    count = 0

    print("%s total records" % TOTAL)

    for mi in menu_items:

        count += 1

        print(mi)
        print(mi.url)
        print()

        if not mi.url.startswith("http"):
            new_url = re.sub(MATCH_PATTERN, "/", mi.url)

            print("    old: %s" % mi.url )
            print("    new: %s" % new_url )
            print()

            mi.url = new_url
            mi.save()
            percent_complete = float(count/TOTAL)*float(100.0)
            print("  SAVED: %.2f%% complete" % percent_complete )
            
        print("----")
        print()
            
    print("Complete!")






