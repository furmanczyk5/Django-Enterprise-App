from datetime import timedelta

from django.contrib.auth.models import Group
from django.utils import timezone

from blog.models import BlogPost
from content.models import *
from content.solr_search import SolrSearch
from content.utils import force_utc_datetime, force_solr_date_format
from planning.global_test_case import GlobalTestCase


class BlogPublishTestCase(GlobalTestCase):

    def setUp(self):
        self.ttt, _ = TaxoTopicTag.objects.get_or_create(
            title="Environmental Protection Wetlands Standards"
        )

    def test_publish_blog_post(self):
        # create draft record
        bpost, bpost_created = BlogPost.objects.get_or_create(title='New Blog Post', publish_status='DRAFT')
        # set draft values 
        bpost.content_area = 'RESEARCH'
        # sec, s = Section.objects.get_or_create(title='New Section')
        # bpost.section=sec
        bpost.text = '<h3>A Web Page&nbsp;</h3>\r\n\r\n<p>&quot;Test publishing a blog post.&quot;</p>\r\n'
        tag_type1, tt1 = TagType.objects.get_or_create(title='Region', id=34, code='CENSUS_REGION')
        tag1, t1 = Tag.objects.get_or_create(title='Pacific', tag_type_id=tag_type1.id, code='PACIFIC')
        tag_type1.tags.add(tag1)
        add_tag = ContentTagType(content=bpost, tag_type=tag_type1)
        # do we need to attach the ContentTagType to the content?
        add_tag.save()
        bpost.contenttagtype.add(add_tag)
        add_tag.tags.add(tag1)
        add_tag.save()

        bpost.taxo_topics.add(self.ttt)
        mem_grp, mg = Group.objects.get_or_create(name='member')
        bpost.permission_groups.add(mem_grp)

        today = timezone.now().date()
        bpost.save()
        bpost.publish()
        bpost_all = BlogPost.objects.filter(title='New Blog Post')
        bpost_draft = BlogPost.objects.get(title='New Blog Post', publish_status='DRAFT')
        bpost_published = BlogPost.objects.get(title='New Blog Post', publish_status='PUBLISHED')

        resp_code = bpost_draft.solr_publish()
        self.assertEqual(resp_code, 200)
        solr_bpost_draft_rec = SolrSearch(custom_q='id:CONTENT.%s' % bpost_draft.master_id)
        res = solr_bpost_draft_rec.get_results()
        vals_dict = res["response"]["docs"][0]

        bpost_draft.save()
        bpost_published.save()
        dr = bpost_draft
        pu = bpost_published
        self.assertEqual(dr.title, pu.title)
        self.assertEqual(dr.master, pu.master)
        self.assertEqual(dr.content_type, pu.content_type)
        self.assertEqual(dr.content_area, pu.content_area)
        # self.assertEqual(dr.section, pu.section)
        self.assertEqual(dr.text, pu.text)
        self.assertEqual(dr.resource_published_date, today)
        self.assertEqual(pu.resource_published_date, today)

        # special case of dealing with solr date format with a blog
        now = timezone.now()
        cut_time = timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)
        now_zero = now - cut_time
        nowu = force_utc_datetime(now_zero)
        nowu_str = str(nowu)
        today_solr = force_solr_date_format(nowu_str, True)

        # solr tests
        self.assertEqual(vals_dict["title"], "New Blog Post")
        self.assertEqual(vals_dict["content_type"], "BLOG")
        self.assertEqual(vals_dict["begin_time"], today_solr)

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
        print("end of test_publish_blog_post")
