from django.contrib.auth.models import Group

from content.models import *
from content.solr_search import SolrSearch
from knowledgebase.models import *
from planning.global_test_case import GlobalTestCase


class KnowledgePublishTestCase(GlobalTestCase):

    def setUp(self):
        self.ttt, _ = TaxoTopicTag.objects.get_or_create(
            title="Environmental Protection Wetlands Standards",
            tag_type=self.mastertopic_tt
        )

    def test_publish_resource(self):
        # create draft record                                                                                                                                                         
        rsrc, rsrc_created = Resource.objects.get_or_create(title='New Resource', publish_status='DRAFT')
        # for some reason content_type is defaulting to 'EVENT' ?? so set it:
        rsrc.content_type = 'KNOWLEDGEBASE'
        # set draft values 
        rsrc.content_area = 'RESEARCH'
        # sec, s = Section.objects.get_or_create(title='New Section')
        # rsrc.section=sec
        rsrc.text='<h3>A Resource Publication&nbsp;</h3>\r\n\r\n<p>Test publishing a Resource</p>\r\n'
        tag_type1, tt1 = TagType.objects.get_or_create(title='Region', id=34, code='CENSUS_REGION')
        tag1, t1 = Tag.objects.get_or_create(title='Pacific', tag_type_id=tag_type1.id, code='PACIFIC')
        tag_type1.tags.add(tag1)
        tag_type1.save()
        add_tag=ContentTagType(content=rsrc, tag_type=tag_type1)
        # do we need to attach the ContentTagType to the content?
        add_tag.save()
        rsrc.contenttagtype.add(add_tag)
        add_tag.tags.add(tag1)
        add_tag.save()
        rsrc.taxo_topics.add(self.ttt)
        mem_grp, mg = Group.objects.get_or_create(name='member')
        rsrc.permission_groups.add(mem_grp)
        rsrc.save()
        rsrc_published = rsrc.publish()

        resp_code = rsrc.solr_publish()
        self.assertEqual(resp_code, 200)
        solr_rsrc_rec = SolrSearch(custom_q='id:CONTENT.%s' %rsrc.master_id)
        res=solr_rsrc_rec.get_results()
        vals_dict=res["response"]["docs"][0]

        rsrc_published.save()
        dr = rsrc
        pu = rsrc_published
        self.assertEqual(dr.title, pu.title)
        self.assertEqual(dr.master, pu.master)
        self.assertEqual(dr.content_type, pu.content_type)
        self.assertEqual(dr.content_area, pu.content_area)
        # self.assertEqual(dr.section, pu.section)
        self.assertEqual(dr.text, pu.text)

        # solr tests
        self.assertEqual(vals_dict["title"], "New Resource")
        self.assertEqual(vals_dict["content_type"], "KNOWLEDGEBASE")
        # list of tag types:
        tt_title_list = [tt.split('.')[2] for tt in vals_dict["tag_types"]]
        # list of tag type codes:
        tt_code_list = [tt.split('.')[1] for tt in vals_dict["tag_types"]]
        # list of tag type ids:
        tt_id_list = [tt.split('.')[0] for tt in vals_dict["tag_types"]]

        # equivalence routine for tag_types and associated tags
        # this tests taxo topics in solr already:
        for index, (tt1, tt2) in enumerate(zip(dr.contenttagtype.order_by('tag_type__title').all(), pu.contenttagtype.order_by('tag_type__title').all())):
          self.assertEqual(tt1.tag_type.title, tt2.tag_type.title)
          self.assertEqual(tt2.tag_type.title in tt_title_list, True)
          tag_title_list = [t.split('.')[2] for t in vals_dict["tags_%s" %tt2.tag_type.code]]
          for index2, (t1, t2) in enumerate(zip(tt1.tags.order_by('tag__title').all(), tt2.tags.order_by('tag__title').all())):
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

        self.assertEqual(dr.published_time , None)
        # id, published_time, (django: _state), updated_time                                                                                                                          
        self.assertEqual(dr.publish_status , 'DRAFT')
        self.assertEqual(pu.publish_status , 'PUBLISHED')
        self.assertEqual(dr.id + 1 , pu.id)

    def test_publish_collection(self):
        # create draft record
        coll, coll_created = Collection.objects.get_or_create(title='New Collection', publish_status='DRAFT')
        # set draft values 
        coll.content_type = 'KNOWLEDGEBASE_COLLECTION'
        coll.content_area = 'RESEARCH'
        # sec, s = Section.objects.get_or_create(title='New Section')
        # coll.section=sec
        coll.text='<h3>A Collection Publication&nbsp;</h3>\r\n\r\n<p>Test publishing a Collection.</p>\r\n'
        tag_type1, tt1 = TagType.objects.get_or_create(title='Region', id=34, code='CENSUS_REGION')
        tag1, t1 = Tag.objects.get_or_create(title='Pacific', tag_type_id=tag_type1.id, code='PACIFIC')
        tag_type1.tags.add(tag1)
        tag_type1.save()
        add_tag=ContentTagType(content=coll, tag_type=tag_type1)
        add_tag.save()
        # do we need to attach the ContentTagType to the content?
        coll.contenttagtype.add(add_tag)
        add_tag.tags.add(tag1)
        add_tag.save()
        coll.taxo_topics.add(self.ttt)
        mem_grp, mg = Group.objects.get_or_create(name='member')
        coll.permission_groups.add(mem_grp)
        coll.save()
        coll_published = coll.publish()
        resp_code = coll.solr_publish()
        self.assertEqual(resp_code, 200)
        solr_page_rec = SolrSearch(custom_q='id:CONTENT.%s' %coll.master_id)
        res=solr_page_rec.get_results()
        vals_dict=res["response"]["docs"][0]

        coll_published.save()
        dr = coll
        pu = coll_published
        self.assertEqual(dr.title, pu.title)
        self.assertEqual(dr.master, pu.master)
        self.assertEqual(dr.content_type, pu.content_type)
        self.assertEqual(dr.content_area, pu.content_area)
        # self.assertEqual(dr.section, pu.section)
        self.assertEqual(dr.text, pu.text)

        # solr tests
        self.assertEqual(vals_dict["title"], "New Collection")
        self.assertEqual(vals_dict["content_type"], "KNOWLEDGEBASE_COLLECTION")
        # list of tag types:
        tt_title_list = [tt.split('.')[2] for tt in vals_dict["tag_types"]]
        # list of tag type codes:
        tt_code_list = [tt.split('.')[1] for tt in vals_dict["tag_types"]]
        # list of tag type ids:
        tt_id_list = [tt.split('.')[0] for tt in vals_dict["tag_types"]]

        # equivalence routine for tag_types and associated tags
        # this tests taxo topics in solr already:
        for index, (tt1, tt2) in enumerate(zip(dr.contenttagtype.order_by('tag_type__title').all(), pu.contenttagtype.order_by('tag_type__title').all())):
          self.assertEqual(tt1.tag_type.title, tt2.tag_type.title)
          self.assertEqual(tt2.tag_type.title in tt_title_list, True)
          tag_title_list = [t.split('.')[2] for t in vals_dict["tags_%s" %tt2.tag_type.code]]
          for index2, (t1, t2) in enumerate(zip(tt1.tags.order_by('tag__title').all(), tt2.tags.order_by('tag__title').all())):
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

        self.assertEqual(dr.published_time , None)
        # id, published_time, (django: _state), updated_time                                                                                                                          
        self.assertEqual(dr.publish_status , 'DRAFT')
        self.assertEqual(pu.publish_status , 'PUBLISHED')
        self.assertEqual(dr.id + 1 , pu.id)
