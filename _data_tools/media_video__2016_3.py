import re

from media.models import Video

def fix_youtube_resource_urls():
    """
    updates MenuItem url fields so that they don't use /index.htm (or .html)
    """

    FILTER_BY = 'youtu.be'
    MATCH_PATTERN = r'https{0,1}://youtu\.be/(.*)' # matches "/index.htm" or "/index.html"

    print("Querying for all Video records containing text: '%s'" % FILTER_BY)

    videos = Video.objects.filter(url_source="YOUTUBE", resource_url__contains=FILTER_BY)
    TOTAL = videos.count()
    count = 0

    print("%s total records" % TOTAL)

    for v in videos:

        count += 1

        print(v)
        print(v.resource_url)
        print()

        match = re.match(MATCH_PATTERN,  v.resource_url)

        if match:
            youtube_id = match.groups()[0]
            new_url = "https://www.youtube.com/embed/%s" % youtube_id

            print("    old: %s" % v.resource_url )
            print("    new: %s" % new_url )
            print()

            v.resource_url = new_url
            v.save()

            percent_complete = float(count/TOTAL)*float(100.0)
            print("  SAVED: %.2f%% complete" % percent_complete )
            
        print("----")
        print()
            
    print("Complete!")






