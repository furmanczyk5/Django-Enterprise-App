import csv
from pages.models import AudioPage

def iterate_csv(filename):
    with open(filename, 'r') as csvfile:
        fieldnames = ['id', 'title', 'url', 'description']
        csvlist = csv.reader(csvfile)

        for line in csvlist:
            create_pod_page(line)

def create_pod_page(listPod, update=False):
    pod_url = build_pod_url(listPod[2])
    newPage, created = AudioPage.objects.get_or_create(url=pod_url)
    if update or created:
        newPage.title = newPage.og_title = build_pod_title(listPod[1])
        print(newPage.title, created)
        newPage.overline = build_pod_overline(listPod[1])
        newPage.text = build_pod_html(listPod)
        #default for pods
        newPage.template="pages/newtheme/media.html"
        newPage.status = 'A'
        newPage.og_url = build_Og_Url(listPod[2])

        newPage.save()


def build_pod_url(scraped_url):
    return scraped_url.replace('apa_planning', 'podcast')+'/'

def build_pod_html(listPod):
    podID = listPod[0]
    podDesc = listPod[3]
    iframe = """<p><iframe allow="autoplay" frameborder="no" height="166" scrolling="no" src="https://w.soundcloud.com/player/?url=https%3A//api.soundcloud.com/tracks/{}%3Fsecret_token%3Ds-ThJv1&amp;color=%23ff5500&amp;auto_play=false&amp;hide_related=false&amp;show_comments=true&amp;show_user=true&amp;show_reposts=false&amp;show_teaser=true" width="100%"></iframe></p>
    """.format(podID)
    tail = """
    <div class="layout-tracery slab-gray">
	<div class="layout-column">
		<div class="section-get-the-planning-app">
			<div class="row">
				<div class="col-sm-8 col-md-6">
					<h3>Other Ways to Listen</h3>
					<p>Find us on iTunes and Stitcher&nbsp;&mdash; or wherever you get your podcasts.</p></div>
				<div class="col-sm-4 col-md-6">
					<div class="app-badges-container"><a class="app-badge app-badge-apple" href="ttps://itunes.apple.com/us/podcast/american-planning-association/id194167978" target="_blank"><img src="https://planning-org-uploaded-media.s3.amazonaws.com/image/app-badge-itunes.png" /> </a><a class="app-badge app-badge-google" href="https://www.stitcher.com/podcast/american-planning-association-podcasts/" target="_blank"> <img src="https://planning-org-uploaded-media.s3.amazonaws.com/image/app-badge-stitcher.png" /> </a><!--<a class="app-badge app-badge-amazon" href="http://www.amazon.com/gp/mas/dl/android?p=com.Planning.Planning"> <img src="/static/newtheme/image/app-badge-amazon.png" /> </a>--></div></div></div></div></div></div>
					"""

    return iframe + podDesc + tail

def build_pod_overline(scraped_title):
    return "Podcast : " + scraped_title.split(':')[1]

def build_pod_title(scraped_title):
    return scraped_title.split(':')[-1].replace(' by APA_Planning','')

def build_Og_Url(url):
    return "https://www.planning.org" + url





