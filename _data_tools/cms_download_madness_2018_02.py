import django
django.setup()

from django.db.models.fields.files import ImageFieldFile
import content, publications, media

PUBLICATION_IDS = (
# 9117463,
# 9117463,
# 9117471,
# 9117474,
# 9117478,
# 9117479,
# 9113630,
# 9113630,
# 9112800,
# 9112800,
# 9137981,
# 9137980,
# 9137982,
# 9134625,
# 9112509,
# 9112508,
# 9112508,
# 9102204,
# 9022831,
# 9115067,
# 9026050,
# 9022839,
# 9026011,
# 9144551,
# 9139484,
# 9139480,
# 9139479,
# 9139478,
# 9139474,
# 9139471,
# 9139469,
# 9139466,
# 9139463,
# 9139461,
# 9139458,
# 9138839,
# 9138026,
# 9138025,
# 9138024,
# 9138023,
# 9123956,
# 9114853,
# 9104071,
# 9131305,
# 9127204,
# 9119420,
# 9119763,
# 9144669,
# 9141726,
# 9120657,
# 9144651,
# 9142461,
# 9140343,
# 9138591,
# 9134459,
# 9132858,
# 9130756,
# 9129118,
# 9125782,
# 9123985,
# 9122032,
# 9119713,
# 9119261,
# 9117398,
# 9115657,
# 9114456,
# 9112643,
# 9110015,
# 9106851, 
# ADDITIONAL IDS 2018-04-11:
9144703,
9144702,
9144700,
9133706,
9133704,
9133702,
9115119,
9110743,
9110109,
9107834,
9107777,
9101585,
)

def media_to_convert():
    # returns queryset of the downloads to convert
    # include any media document with a product template:
    media_product_qs = media.models.Document.objects.filter(template="store/newtheme/product/details.html")
    # any others?
    media_qs = media_product_qs | media.models.Document.objects.filter(master__id__in=PUBLICATION_IDS)
    return media_qs

def convert_to_publication(media_obj):
    publication_document = publications.models.PublicationDocument(content_ptr_id=media_obj.pk)
    publication_document.__dict__.update(media_obj.__dict__)
    publication_document.template = "publications/newtheme/publication-document.html"
    publication_document.publication_download = media_obj.uploaded_file
    # publication_document.thumbnail = media_obj.image_thumbnail # NOTE THIS DOESN'T WORK... meeting with content team to determine rules for thumbnails
    publication_document.save()
    return publication_document

def test_single_record():
    m = media_to_convert()
    m0 = m[0]
    other_publish_stats = "DRAFT" if m0.publish_status == "PUBLISHED" else "PUBLISHED"
    m1 = media.models.Document.objects.get(publish_status=other_publish_stats, master__id=m0.master.id)
    d0 = convert_to_publication(m0)
    d1 = convert_to_publication(m1)
    published_d = d0.publish()
    published_d.solr_publish()
    return d0, d1

def convert_media_to_publications():
    converted_list = []
    for media_obj in media_to_convert():
        converted_list.append( convert_to_publication(media_obj) )
    for publication_document in converted_list:
        if publication_document.publish_status == "DRAFT":
            published_document = publication_document.publish()
            published_document.solr_publish()
            print(publication_document.title)
