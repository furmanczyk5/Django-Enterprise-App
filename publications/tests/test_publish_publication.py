from django.contrib.auth.models import Group

from django.core.files import File

from content.models import *
from publications.models import *
from content.utils import html_to_text
from content.solr_search import SolrSearch
from planning.global_test_case import GlobalTestCase


class PublicationPublishTestCase(GlobalTestCase):

    @classmethod
    def setUpTestData(cls):

        super(PublicationPublishTestCase, cls).setUpTestData()

        cls.ttt, _ = TaxoTopicTag.objects.get_or_create(
            title="Environmental Protection Wetlands Standards"
        )

# HOW TO UPLOAD AN IMAGE TO DATABASE?
    def test_publish_publication(self):
        # create draft record
        format_tag_type, is_created = TagType.objects.get_or_create(code="FORMAT", title="Format")
        format_tag, is_created = Tag.objects.get_or_create(
            tag_type=format_tag_type,
            code="FORMAT_ARTICLE",
            title='Article'
        )
        
        with open('publications/tests/samp.pdf', 'rb') as pdf:
            pub_down = File(pdf)
            art, art_created = Article.objects.get_or_create(
                publication_download=pub_down,
                title='New Article',
                publish_status='DRAFT'
            )

        # format_contenttagtype, is_created = ContentTagType.objects.get_or_create(content=art, tag_type=format_tag_type)

        art.page_count = 1
        art.publication_format = 'PDF'
        art.text = '<h3>An Article&nbsp;</h3>\r\n\r\n<p>Test publishing an article.</p>\r\n'
        solr_text = html_to_text(art.text)
        tag_type1, tt1 = TagType.objects.get_or_create(title='Region', id=34, code='CENSUS_REGION')
        tag1, t1 = Tag.objects.get_or_create(title='Pacific', tag_type_id=tag_type1.id, code='PACIFIC')
        tag_type1.tags.add(tag1)
        tag_type1.save()
        add_tag=ContentTagType(content=art, tag_type=tag_type1)
        add_tag.save()
        # do we need to attach the ContentTagType to the content?
        art.contenttagtype.add(add_tag)
        add_tag.tags.add(tag1)
        add_tag.save()

        art.taxo_topics.add(self.ttt)
        mem_grp, mg = Group.objects.get_or_create(name='member')
        art.permission_groups.add(mem_grp)
        art.save()
        art_published = art.publish()
        resp_code = art.solr_publish()
        self.assertEqual(resp_code, 200)
        solr_art_rec = SolrSearch(custom_q='id:CONTENT.%s' % art.master_id)
        res=solr_art_rec.get_results()
        vals_dict=res["response"]["docs"][0]

        art_published.save()
        dr = art
        pu = art_published
        self.assertEqual(dr.title, pu.title)
        self.assertEqual(dr.master_id, pu.master_id)
        self.assertEqual(dr.content_type, pu.content_type)
        self.assertEqual(dr.content_area, pu.content_area)
        self.assertEqual(dr.resource_type, pu.resource_type)
        self.assertEqual(dr.text, pu.text)
        self.assertEqual(dr.publication_download, pu.publication_download)

        self.assertEqual(pu.title, "New Article")
        self.assertEqual(pu.text, '<h3>An Article&nbsp;</h3>\r\n\r\n<p>Test publishing an article.</p>\r\n')
        self.assertEqual(pu.page_count, 1)
        self.assertEqual(pu.publication_format, "PDF")
        self.assertEqual(pu.content_type, "PUBLICATION")
        self.assertEqual(pu.content_area, "KNOWLEDGE_CENTER")
        self.assertEqual(pu.resource_type, "ARTICLE")

        # solr tests
        self.assertEqual(vals_dict["title"], "New Article")
        self.assertEqual(vals_dict["content_type"], "PUBLICATION")
        self.assertEqual(vals_dict["resource_type"], "ARTICLE")
        # not in solr?
        # self.assertEqual(vals_dict["text"], solr_text)

        # list of tag types:
        tt_title_list = [tt.split('.')[2] for tt in vals_dict["tag_types"]]
        # print("tt_title_list is ............................ ", tt_title_list)
        # list of tag type codes:
        tt_code_list = [tt.split('.')[1] for tt in vals_dict["tag_types"]]
        # print("tt_code_list is ............................. ", tt_code_list)
        # list of tag type ids:
        tt_id_list = [tt.split('.')[0] for tt in vals_dict["tag_types"]]
        # print("tt_id_list is ................................. ", tt_id_list)
        # print()

        # equivalence routine for tag_types and associated tags
        # this tests taxo topics in solr already:
        # print("dr.contenttagtype.order_by('tag_type__title').all() is .... ", dr.contenttagtype.order_by('tag_type__title').all())
        # print("pu.contenttagtype.order_by('tag_type__title').all()) is .... ", pu.contenttagtype.order_by('tag_type__title').all())
        # print()
        for index, (tt1, tt2) in enumerate(zip(dr.contenttagtype.order_by('tag_type__title').all(), pu.contenttagtype.order_by('tag_type__title').all())):
          self.assertEqual(tt1.tag_type.title, tt2.tag_type.title)

          self.assertEqual(tt2.tag_type.title in tt_title_list, True)
          # solr_tag_types_list = vals_dict["tag_types"]
          tag_title_list = [t.split('.')[2] for t in vals_dict["tags_%s" % tt2.tag_type.code]]

          # print("vals_dict is ..................................... ", vals_dict)
          # print("tag_title_list is ................................", tag_title_list)
          # print("tt1.tags.all() is ...............................", tt1.tags.all())
          # print("tt2.tags.all() is ................................", tt2.tags.all())
          # print()
          for index2, (t1, t2) in enumerate(zip(tt1.tags.order_by('tag__title').all(), tt2.tags.order_by('tag__title').all())):
            self.assertEqual(t1.title, t2.title)
            # print("t1.title is ......... ", t1.title)
            # print("t2.title is .......... ", t2.title)
            # print()
            self.assertEqual(t2.title in tag_title_list, True)

        # equivalence routine for taxo_topics                                                                                                                        
        for index, (val1, val2) in enumerate(zip(dr.taxo_topics.all(), pu.taxo_topics.all())):
          self.assertEqual(val1.title, val2.title)

        groups_list = vals_dict["permission_groups"]

        # equivalence routine for groups:                                                                                                                                    
        for index, (val1, val2) in enumerate(zip(dr.permission_groups.all(), pu.permission_groups.all())):
          self.assertEqual(val1.name, val2.name)
          self.assertEqual(val2.name in groups_list, True)

        self.assertEqual(dr.published_time , None)
        # id, published_time, (django: _state), updated_time                                                                                                                          
        self.assertEqual(dr.publish_status , 'DRAFT')
        self.assertEqual(pu.publish_status , 'PUBLISHED')
        self.assertEqual(dr.id + 1 , pu.id)

