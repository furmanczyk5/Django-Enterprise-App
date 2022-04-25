from django.contrib.auth.models import Group

from content.models.tagging import ContentTagType, Tag, TagType, TaxoTopicTag
from content.solr_search import SolrSearch
from pages.models import Page, LandingPage
from planning.global_test_case import GlobalTestCase


class PagePublishTestCase(GlobalTestCase):

    @classmethod
    def setUpTestData(cls):

        super(PagePublishTestCase, cls).setUpTestData()

        cls.ttt, _ = TaxoTopicTag.objects.get_or_create(
            title="Environmental Protection Wetlands Standards"
        )

    def test_publish_page(self):
        # create draft record
        page, page_created = Page.objects.get_or_create(title='New Page', publish_status='DRAFT')

        # set draft values 
        page.content_area = 'RESEARCH'
        page.text = '<h3>A Web Page&nbsp;</h3>\r\n\r\n<p>Test publishing a web page. &quot;Text in quotes.&quot; More text.</p>\r\n'

        tag_type1, tt1 = TagType.objects.get_or_create(title='Region', id=34, code='CENSUS_REGION')
        tag1, t1 = Tag.objects.get_or_create(title='Pacific', tag_type_id=tag_type1.id, code='PACIFIC')
        tag_type1.tags.add(tag1)
        tag_type1.save()
        add_tag = ContentTagType(content=page, tag_type=tag_type1)

        # do we need to attach the ContentTagType to the content?
        add_tag.save()
        page.contenttagtype.add(add_tag)
        add_tag.tags.add(tag1)
        add_tag.save()

        page.taxo_topics.add(self.ttt)

        mem_grp, mg = Group.objects.get_or_create(name='member')
        page.permission_groups.add(mem_grp)
        page.save()
        page_published = page.publish()

        resp_code = page.solr_publish()
        self.assertEqual(resp_code, 200)
        solr_page_rec = SolrSearch(custom_q='id:CONTENT.%s' % page.master_id)
        res = solr_page_rec.get_results()
        vals_dict = res["response"]["docs"][0]

        page_published.save()
        dr = page
        pu = page_published
        self.assertEqual(dr.title, pu.title)
        self.assertEqual(dr.master, pu.master)
        self.assertEqual(dr.content_type, pu.content_type)
        self.assertEqual(dr.content_area, pu.content_area)
        self.assertEqual(dr.text, pu.text)

        # solr tests
        self.assertEqual(vals_dict["title"], "New Page")
        self.assertEqual(vals_dict["content_type"], "PAGE")
        # list of tag types:
        tt_title_list = [tt.split('.')[2] for tt in vals_dict["tag_types"]]
        # list of tag type codes:
        tt_code_list = [tt.split('.')[1] for tt in vals_dict["tag_types"]]
        # list of tag type ids:
        tt_id_list = [tt.split('.')[0] for tt in vals_dict["tag_types"]]

        # equivalence routine for tag_types and associated tags
        # this tests taxo topics in solr already:
        for index, (tt1, tt2) in enumerate(zip(dr.contenttagtype.order_by('tag_type__title').all(),
                                               pu.contenttagtype.order_by('tag_type__title').all())):
            self.assertEqual(tt1.tag_type.title, tt2.tag_type.title)
            self.assertEqual(tt2.tag_type.title in tt_title_list, True)
            tag_title_list = [t.split('.')[2] for t in vals_dict["tags_%s" % tt2.tag_type.code]]
            for index2, (t1, t2) in enumerate(
                    zip(tt1.tags.order_by('tag__title').all(), tt2.tags.order_by('tag__title').all())):
                self.assertEqual(t1.title, t2.title)
                self.assertEqual(t2.title in tag_title_list, True)

        # equivalence routine for taxo_topics                                                                                                                        
        for index, (val1, val2) in enumerate(zip(dr.taxo_topics.all(), pu.taxo_topics.all())):
            self.assertEqual(val1.title, val2.title)

        groups_list = vals_dict["permission_groups"]

        # equivalence routine for groups:                                                                                                                                    
        for index, (val1, val2) in enumerate(zip(dr.permission_groups.all(), pu.permission_groups.all())):
            self.assertEqual(val1.name, val2.name)
            self.assertEqual(val2.name in groups_list, True)

        self.assertEqual(dr.published_time, None)
        # id, published_time, (django: _state), updated_time                                                                                                                          
        self.assertEqual(dr.publish_status, 'DRAFT')
        self.assertEqual(pu.publish_status, 'PUBLISHED')
        self.assertEqual(dr.id + 1, pu.id)

    def test_publish_landing_page(self):
        # create draft record
        lpage, lpage_created = LandingPage.objects.get_or_create(title='New Landing Page', publish_status='DRAFT')
        # set draft values 
        # sec, s = Section.objects.get_or_create(title='New Section')
        # lpage.section=sec
        lpage.text = '<h3>A Web Page&nbsp;</h3>\r\n\r\n<p>Test publishing a web landing page.</p>\r\n'
        tag_type1, tt1 = TagType.objects.get_or_create(title='Region', id=34, code='CENSUS_REGION')
        tag1, t1 = Tag.objects.get_or_create(title='Pacific', tag_type_id=tag_type1.id, code='PACIFIC')
        tag_type1.tags.add(tag1)
        tag_type1.save()
        add_tag = ContentTagType(content=lpage, tag_type=tag_type1)
        # do we need to attach the ContentTagType to the content?
        add_tag.save()
        lpage.contenttagtype.add(add_tag)
        add_tag.tags.add(tag1)
        add_tag.save()

        lpage.taxo_topics.add(self.ttt)
        mem_grp, mg = Group.objects.get_or_create(name='member')
        lpage.permission_groups.add(mem_grp)
        lpage.save()
        lpage_published = lpage.publish()
        resp_code = lpage.solr_publish()
        self.assertEqual(resp_code, 200)
        solr_page_rec = SolrSearch(custom_q='id:CONTENT.%s' % lpage.master_id)
        res = solr_page_rec.get_results()
        vals_dict = res["response"]["docs"][0]

        lpage_published.save()
        dr = lpage
        pu = lpage_published
        self.assertEqual(dr.title, pu.title)
        self.assertEqual(dr.master, pu.master)
        self.assertEqual(dr.content_type, pu.content_type)
        self.assertEqual(dr.content_area, pu.content_area)
        # self.assertEqual(dr.section, pu.section)
        self.assertEqual(dr.text, pu.text)

        # solr tests
        self.assertEqual(vals_dict["title"], "New Landing Page")
        self.assertEqual(vals_dict["content_type"], "PAGE")
        # list of tag types:
        tt_title_list = [tt.split('.')[2] for tt in vals_dict["tag_types"]]
        # list of tag type codes:
        tt_code_list = [tt.split('.')[1] for tt in vals_dict["tag_types"]]
        # list of tag type ids:
        tt_id_list = [tt.split('.')[0] for tt in vals_dict["tag_types"]]

        # equivalence routine for tag_types and associated tags
        # this tests taxo topics in solr already:
        for index, (tt1, tt2) in enumerate(zip(dr.contenttagtype.order_by('tag_type__title').all(),
                                               pu.contenttagtype.order_by('tag_type__title').all())):
            self.assertEqual(tt1.tag_type.title, tt2.tag_type.title)
            self.assertEqual(tt2.tag_type.title in tt_title_list, True)
            tag_title_list = [t.split('.')[2] for t in vals_dict["tags_%s" % tt2.tag_type.code]]
            for index2, (t1, t2) in enumerate(
                    zip(tt1.tags.order_by('tag__title').all(), tt2.tags.order_by('tag__title').all())):
                self.assertEqual(t1.title, t2.title)
                self.assertEqual(t2.title in tag_title_list, True)

        # equivalence routine for taxo_topics                                                                                                                        
        for index, (val1, val2) in enumerate(zip(dr.taxo_topics.all(), pu.taxo_topics.all())):
            self.assertEqual(val1.title, val2.title)

        groups_list = vals_dict["permission_groups"]

        # equivalence routine for groups:                                                                                                                                    
        for index, (val1, val2) in enumerate(zip(dr.permission_groups.all(), pu.permission_groups.all())):
            self.assertEqual(val1.name, val2.name)
            self.assertEqual(val2.name in groups_list, True)

        self.assertEqual(dr.published_time, None)
        # id, published_time, (django: _state), updated_time                                                                                                                          
        self.assertEqual(dr.publish_status, 'DRAFT')
        self.assertEqual(pu.publish_status, 'PUBLISHED')
        self.assertEqual(dr.id + 1, pu.id)
