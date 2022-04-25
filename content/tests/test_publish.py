from django.contrib.auth.models import User, Group

from content.models import *
from planning.global_test_case import GlobalTestCase


class ContentPublishTestCase(GlobalTestCase):
    """
    This is a general content test case (with no solr elements).
    """

    @classmethod
    def setUpTestData(cls):

        super(ContentPublishTestCase, cls).setUpTestData()

        cls.test_user, user_created = User.objects.get_or_create(username="000007", password="norman_pass")
        cls.mem_grp, mg = Group.objects.get_or_create(name='member')
        cls.ttt, _ = TaxoTopicTag.objects.get_or_create(
            title="Environmental Protection Wetlands Standards"
        )

    def test_publish_content(self):
        # create draft record
        wp, wp_created =Content.objects.get_or_create(title='Testing Publishing', content_type='PAGE', publish_status='DRAFT')
        # set draft values
        wp.content_area = 'RESEARCH'
        wp.text='<h3>H3 Heading&nbsp;</h3>\r\n\r\n<p>Paragraph Text. &quot;Text in quotes.&quot; More text.</p>\r\n'
        tag_type1, tt1 = TagType.objects.get_or_create(title='Region', id=16, code='CENSUS_REGION')
        tag1, t1 = Tag.objects.get_or_create(title='Pacific', tag_type_id=16, code='PACIFIC')
        tag_type1.tags.add(tag1)
        tag_type1.save()
        add_tag=ContentTagType(content=wp, tag_type=tag_type1)
        add_tag.save()

        wp.taxo_topics.add(self.ttt)
        mem_grp, mg = Group.objects.get_or_create(name='member')
        wp.permission_groups.add(mem_grp)
        wp.save()
        wp_published = wp.publish()
        wp_published.save()
        dr = wp
        pu = wp_published
        self.assertEqual(dr.title, pu.title)
        self.assertEqual(dr.master, pu.master)
        self.assertEqual(dr.content_type, pu.content_type)
        self.assertEqual(dr.content_area, pu.content_area)
        self.assertEqual(dr.text, pu.text)
        # equivalence routine for tag_types and associated tags
        for index, (tt1, tt2) in enumerate(zip(dr.tag_types.all(), pu.tag_types.all())):
          self.assertEqual(tt1.title, tt2.title)
          for index2, (t1, t2) in enumerate(zip(tt1.tags.all(), tt2.tags.all())):
            self.assertEqual(t1.title, t2.title)
        # equivalence routine for taxo_topics
        for index, (val1, val2) in enumerate(zip(dr.taxo_topics.all(), pu.taxo_topics.all())):
          self.assertEqual(val1.title, val2.title)
        # equivalence routine for groups:
        for index, (val1, val2) in enumerate(zip(dr.permission_groups.all(), pu.permission_groups.all())):
          self.assertEqual(val1.name, val2.name)

        self.assertEqual(dr.published_time , None)
        # id, published_time, (django: _state), updated_time
        self.assertEqual(dr.publish_status , 'DRAFT')
        self.assertEqual(pu.publish_status , 'PUBLISHED')
        self.assertEqual(dr.id + 1 , pu.id)


class MessageTextPublishTestCase(GlobalTestCase):
    """
    MessageText does not inherit from Content (only BaseContent) so tests have to be altered. Also
    not on solr.
    """

    def test_publish_message_text(self):
        # create draft record
        mtext, mtext_created = MessageText.objects.get_or_create(title='New MessageText', publish_status='DRAFT')
        # set draft values
        mtext.text='<h3>A MessageText Record&nbsp;</h3>\r\n\r\n<p>Test publishing a MessageText record.</p>\r\n'
        mtext.save()
        mtext_published = mtext.publish()
        mtext_published.save()
        dr = mtext
        pu = mtext_published
        self.assertEqual(dr.title, pu.title)
        self.assertEqual(dr.text, pu.text)

        self.assertEqual(dr.published_time , None)
        # id, published_time, (django: _state), updated_time
        self.assertEqual(dr.publish_status , 'DRAFT')
        self.assertEqual(pu.publish_status , 'PUBLISHED')
        self.assertEqual(dr.id + 1 , pu.id)
