from django.contrib.auth.models import Group

from content.models import *
from content.solr_search import SolrSearch
from content.utils import force_solr_date_format
from events.models import *
from myapa.models import *
from myapa.tests.factories.contact import ContactFactoryIndividual
from pages.models import LandingPage
from planning.global_test_case import GlobalTestCase


class EventPublishTestCase(GlobalTestCase):

    @classmethod
    def setUpTestData(cls):

        super(EventPublishTestCase, cls).setUpTestData()

        cls.user_contact = ContactFactoryIndividual()
        cls.mem_grp, cls.mg = Group.objects.get_or_create(name='member')

    def setUp(self):
        """
        :meth:`events.models.Event.save` sets a default parent landing page
        which will cause errors here if it doesn't exist (i.e. in a fresh test database)
        TODO: replace with events.tests.NPCTestCase
        """

        event_landing_page, event_landing_page_exists = LandingPage.objects.get_or_create(
            title='Test Page for Conferences & Meetings'
        )
        if not event_landing_page_exists:
            event_landing_page.publish()
        self.parent_landing_master_id = event_landing_page.master_id

        self.ttt, _ = TaxoTopicTag.objects.get_or_create(
            title="Environmental Protection Wetlands Standards"
        )

    def test_publish_event_single(self):
        # test_user, user_created = User.objects.get_or_create(username="000007", password="norman_pass")
        # user_contact, uc = Contact.objects.get_or_create(user=test_user)
        # create draft record                                                                                                                                                         
        act, act_created = EventSingle.objects.get_or_create(
            title='New Single Event',
            publish_status='DRAFT',
            parent_landing_master_id=self.parent_landing_master_id
        )
        # set draft values 
        cr, cr_created = ContactRole.objects.get_or_create(content=act, contact=self.user_contact)

        yesterday = timezone.now() - timedelta(days=1)
        # pytz.utc.localize(yesterday)
        act.begin_time = yesterday
        in_six_days = timezone.now() + timedelta(days=6)
        # pytz.utc.localize(in_six_days)
        act.end_time = in_six_days
        act.cm_status = 'A'
        act.cm_approved = 1.00
        act.is_free = True
        # sec, s = Section.objects.get_or_create(title='New Section')
        # act.section=sec
        act.text = '<h3>A Single Event&nbsp;</h3>\r\n\r\n<p>Test publishing a single event.</p>\r\n'
        tag_type1, tt1 = TagType.objects.get_or_create(title='Region', id=34, code='CENSUS_REGION')
        tag1, t1 = Tag.objects.get_or_create(title='Pacific', tag_type_id=tag_type1.id, code='PACIFIC')
        tag_type1.tags.add(tag1)
        tag_type1.save()
        add_tag = ContentTagType(content=act, tag_type=tag_type1)
        add_tag.save()
        # do we need to attach the ContentTagType to the content?
        act.contenttagtype.add(add_tag)
        add_tag.tags.add(tag1)
        add_tag.save()

        act.taxo_topics.add(self.ttt)
        mem_grp, mg = Group.objects.get_or_create(name='member')
        act.permission_groups.add(mem_grp)
        act.save()
        act_published = act.publish()
        # solr code solr_base='http://192.241.167.78:8983'
        resp_code = act.solr_publish()
        self.assertEqual(resp_code, 200)
        solr_act_rec = SolrSearch(custom_q='id:CONTENT.%s' % act.master_id)
        res = solr_act_rec.get_results()
        vals_dict = res["response"]["docs"][0]

        act_published.save()
        dr = act
        pu = act_published
        self.assertEqual(dr.title, pu.title)
        self.assertEqual(dr.master, pu.master)
        self.assertEqual(dr.content_type, pu.content_type)
        # self.assertEqual(dr.section, pu.section)
        self.assertEqual(dr.text, pu.text)

        # dbt = force_utc_datetime(dr.begin_time)
        # pbt = force_utc_datetime(pu.begin_time)
        # det = force_utc_datetime(dr.end_time)
        # pet = force_utc_datetime(pu.end_time)
        dbt = dr.begin_time
        pbt = pu.begin_time
        det = dr.end_time
        pet = pu.end_time

        self.assertEqual(dbt, pbt)
        self.assertEqual(det, pet)
        self.assertEqual(dr.cm_status, pu.cm_status)
        self.assertEqual(dr.cm_approved, pu.cm_approved)
        self.assertEqual(dr.is_free, pu.is_free)
        self.assertEqual(dr.has_started(), True)
        self.assertEqual(pu.has_started(), True)
        dcr = dr.contactrole.order_by('contact')[0]
        self.assertTrue(isinstance(dcr, ContactRole))
        pcr = pu.contactrole.order_by('contact')[0]
        self.assertTrue(isinstance(pcr, ContactRole))
        # Don't think you can assertEqual on objects?
        # self.assertEqual(dcr, pcr)
        self.assertEqual(dcr.contact.first_name, pcr.contact.first_name)
        self.assertEqual(dcr.contact.last_name, pcr.contact.last_name)

        # solr tests
        self.assertEqual(vals_dict["title"], "New Single Event")
        self.assertEqual(vals_dict["content_type"], "EVENT")
        self.assertEqual(vals_dict["event_type"], "EVENT_SINGLE")

        self.assertEqual(vals_dict["begin_time"], force_solr_date_format(pbt, False))
        self.assertEqual(vals_dict["end_time"], force_solr_date_format(pet, False))
        self.assertEqual(vals_dict["cm_status"], "A")
        self.assertEqual(vals_dict["cm_approved"], 1.00)
        self.assertEqual(vals_dict["is_free"], True)

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

    def test_publish_activity(self):
        act, act_created = Activity.objects.get_or_create(
            title='New Activity',
            publish_status='DRAFT',
            parent_landing_master_id=self.parent_landing_master_id
        )
        cr, cr_created = ContactRole.objects.get_or_create(content=act, contact=self.user_contact)

        yesterday = timezone.now() - timedelta(days=1)
        # pytz.utc.localize(yesterday)
        act.begin_time = yesterday
        in_six_days = timezone.now() + timedelta(days=6)
        # pytz.utc.localize(in_six_days)
        act.end_time = in_six_days
        act.cm_status = 'A'
        act.cm_approved = 1.00
        act.is_free = True
        # sec, s = Section.objects.get_or_create(title='New Section')
        # act.section=sec
        # act.text='<h3>An Activity&nbsp;</h3>\r\n\r\n<p>Test publishing an activity.</p>\r\n'
        tag_type1, tt1 = TagType.objects.get_or_create(title='Region', id=34, code='CENSUS_REGION')
        tag1, t1 = Tag.objects.get_or_create(title='Pacific', tag_type_id=tag_type1.id, code='PACIFIC')
        tag_type1.tags.add(tag1)
        tag_type1.save()
        add_tag = ContentTagType(content=act, tag_type=tag_type1)
        add_tag.save()
        act.contenttagtype.add(add_tag)
        add_tag.tags.add(tag1)
        add_tag.save()

        act.taxo_topics.add(self.ttt)
        mem_grp, mg = Group.objects.get_or_create(name='member')
        act.permission_groups.add(mem_grp)
        act.save()
        act_published = act.publish()
        resp_code = act.solr_publish()
        self.assertEqual(resp_code, 200)
        solr_act_rec = SolrSearch(custom_q='id:CONTENT.%s' % act.master_id)
        res = solr_act_rec.get_results()
        vals_dict = res["response"]["docs"][0]

        act_published.save()
        dr = act
        pu = act_published
        self.assertEqual(dr.title, pu.title)
        self.assertEqual(dr.master, pu.master)
        self.assertEqual(dr.content_type, pu.content_type)
        # self.assertEqual(dr.section, pu.section)
        self.assertEqual(dr.text, pu.text)

        dbt = dr.begin_time
        pbt = pu.begin_time
        det = dr.end_time
        pet = pu.end_time

        self.assertEqual(dbt, pbt)
        self.assertEqual(det, pet)
        self.assertEqual(dr.cm_status, pu.cm_status)
        self.assertEqual(dr.cm_approved, pu.cm_approved)
        self.assertEqual(dr.is_free, pu.is_free)
        self.assertTrue(dr.has_started())
        self.assertTrue(pu.has_started())
        dcr = dr.contactrole.order_by('contact')[0]
        self.assertTrue(isinstance(dcr, ContactRole))
        pcr = pu.contactrole.order_by('contact')[0]
        self.assertTrue(isinstance(pcr, ContactRole))
        # Don't think you can assertEqual on objects?
        # self.assertEqual(dcr, pcr)
        self.assertEqual(dcr.contact.first_name, pcr.contact.first_name)
        self.assertEqual(dcr.contact.last_name, pcr.contact.last_name)

        # solr tests
        self.assertEqual(vals_dict["title"], "New Activity")
        self.assertEqual(vals_dict["content_type"], "EVENT")
        self.assertEqual(vals_dict["event_type"], "ACTIVITY")

        self.assertEqual(vals_dict["begin_time"], force_solr_date_format(pbt, False))
        self.assertEqual(vals_dict["end_time"], force_solr_date_format(pet, False))
        self.assertEqual(vals_dict["cm_status"], "A")
        self.assertEqual(vals_dict["cm_approved"], 1.00)
        self.assertEqual(vals_dict["is_free"], True)

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

    def test_publish_course(self):
        course, course_created = Course.objects.get_or_create(
            title='New Course',
            publish_status='DRAFT',
            parent_landing_master_id=self.parent_landing_master_id
        )
        cr, cr_created = ContactRole.objects.get_or_create(content=course, contact=self.user_contact)

        yesterday = timezone.now() - timedelta(days=1)
        # pytz.utc.localize(yesterday)
        course.begin_time = yesterday
        in_six_days = timezone.now() + timedelta(days=6)
        # pytz.utc.localize(in_six_days)
        course.end_time = in_six_days
        course.cm_status = 'A'
        course.cm_approved = 1.00
        course.is_free = True
        # sec, s = Section.objects.get_or_create(title='New Section')
        # course.section=sec
        course.text = '<h3>A Course&nbsp;</h3>\r\n\r\n<p>Test publishing a course.</p>\r\n'
        tag_type1, tt1 = TagType.objects.get_or_create(title='Region', id=34, code='CENSUS_REGION')
        tag1, t1 = Tag.objects.get_or_create(title='Pacific', tag_type_id=tag_type1.id, code='PACIFIC')
        tag_type1.tags.add(tag1)
        tag_type1.save()
        add_tag = ContentTagType(content=course, tag_type=tag_type1)
        add_tag.save()
        course.contenttagtype.add(add_tag)
        add_tag.tags.add(tag1)
        add_tag.save()

        course.taxo_topics.add(self.ttt)
        mem_grp, mg = Group.objects.get_or_create(name='member')
        course.permission_groups.add(mem_grp)
        course.save()
        course_published = course.publish()
        resp_code = course.solr_publish()
        self.assertEqual(resp_code, 200)
        solr_course_rec = SolrSearch(custom_q='id:CONTENT.%s' % course.master_id)
        res = solr_course_rec.get_results()
        vals_dict = res["response"]["docs"][0]

        course_published.save()
        dr = course
        pu = course_published
        self.assertEqual(dr.title, pu.title)
        self.assertEqual(dr.master, pu.master)
        self.assertEqual(dr.content_type, pu.content_type)
        # self.assertEqual(dr.section, pu.section)
        self.assertEqual(dr.text, pu.text)

        dbt = dr.begin_time
        pbt = pu.begin_time
        det = dr.end_time
        pet = pu.end_time

        self.assertEqual(dbt, pbt)
        self.assertEqual(det, pet)
        self.assertEqual(dr.cm_status, pu.cm_status)
        self.assertEqual(dr.cm_approved, pu.cm_approved)
        self.assertEqual(dr.is_free, pu.is_free)
        self.assertEqual(dr.has_started(), True)
        self.assertEqual(pu.has_started(), True)
        dcr = dr.contactrole.order_by('contact')[0]
        self.assertTrue(isinstance(dcr, ContactRole))
        pcr = pu.contactrole.order_by('contact')[0]
        self.assertTrue(isinstance(pcr, ContactRole))
        # Don't think you can assertEqual on objects?
        # self.assertEqual(dcr, pcr)
        self.assertEqual(dcr.contact.first_name, pcr.contact.first_name)
        self.assertEqual(dcr.contact.last_name, pcr.contact.last_name)

        # solr tests
        self.assertEqual(vals_dict["title"], "New Course")
        self.assertEqual(vals_dict["content_type"], "EVENT")
        self.assertEqual(vals_dict["event_type"], "COURSE")

        self.assertEqual(vals_dict["begin_time"], force_solr_date_format(pbt, False))
        self.assertEqual(vals_dict["end_time"], force_solr_date_format(pet, False))
        self.assertEqual(vals_dict["cm_status"], "A")
        self.assertEqual(vals_dict["cm_approved"], 1.00)
        self.assertEqual(vals_dict["is_free"], True)

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

    def test_publish_event_multi(self):
        org_contact, oc = Organization.objects.get_or_create(company='new planning co.')
        ev_mult, ev_mult_created = EventMulti.objects.get_or_create(
            title='New Multi Event',
            publish_status='SUBMISSION',
            parent_landing_master_id=self.parent_landing_master_id
        )
        cr, cr_created = ContactRole.objects.get_or_create(content=ev_mult, contact=self.user_contact,
                                                           role_type='PROVIDER')
        ev_act, ev_act_created = Activity.objects.get_or_create(
            title='New Event Activity',
            publish_status='SUBMISSION',
            parent=ev_mult.master,
            parent_landing_master_id=self.parent_landing_master_id
        )
        cr2, cr2c = ContactRole.objects.get_or_create(content=ev_act, contact=org_contact, role_type='PROVIDER',
                                                      publish_status='SUBMISSION')
        ev_mult.submitted_time = timezone.now()
        ev_act.submitted_time = timezone.now()

        yesterday = timezone.now() - timedelta(days=1)
        # pytz.utc.localize(yesterday)
        ev_mult.begin_time = yesterday
        in_six_days = timezone.now() + timedelta(days=6)
        # pytz.utc.localize(in_six_days)
        ev_mult.end_time = in_six_days
        ev_mult.cm_status = 'A'
        ev_mult.cm_approved = 1.00
        ev_mult.is_free = True
        # sec, s = Section.objects.get_or_create(title='New Section')
        # ev_mult.section=sec
        ev_mult.text = '<h3>A Multi Event&nbsp;</h3>\r\n\r\n<p>Test publishing a multi event.</p>\r\n'
        tag_type1, tt1 = TagType.objects.get_or_create(title='Region', id=34, code='CENSUS_REGION')
        tag1, t1 = Tag.objects.get_or_create(title='Pacific', tag_type_id=tag_type1.id, code='PACIFIC')
        tag_type1.tags.add(tag1)
        tag_type1.save()
        add_tag = ContentTagType(content=ev_mult, tag_type=tag_type1)
        add_tag.save()
        ev_mult.contenttagtype.add(add_tag)
        add_tag.tags.add(tag1)
        add_tag.save()

        ev_mult.taxo_topics.add(self.ttt)
        mem_grp, mg = Group.objects.get_or_create(name='member')
        ev_mult.permission_groups.add(mem_grp)

        ev_mult.save()
        ev_act.save()
        ev_mult_draft = ev_mult.publish(publish_type="DRAFT")
        ev_act_draft = ev_act.publish(publish_type="DRAFT")

        ev_mult_published = ev_mult_draft.publish()
        ev_act_published = ev_act_draft.publish()

        resp_code = ev_mult_draft.solr_publish()
        self.assertEqual(resp_code, 200)
        solr_ev_mult_rec = SolrSearch(custom_q='id:CONTENT.%s' % ev_mult_draft.master_id)
        res = solr_ev_mult_rec.get_results()
        vals_dict = res["response"]["docs"][0]
        resp_code = ev_act_draft.solr_publish()
        self.assertEqual(resp_code, 200)
        solr_ev_act_rec = SolrSearch(custom_q='id:CONTENT.%s' % ev_act_draft.master_id)
        res = solr_ev_act_rec.get_results()
        vals_dict_act = res["response"]["docs"][0]

        ev_mult_published.save()
        ev_act_published.save()

        dr = ev_mult_draft
        pu = ev_mult_published
        adr = ev_act_draft
        apu = ev_act_published

        self.assertEqual(dr.title, pu.title)
        self.assertEqual(dr.master, pu.master)
        self.assertEqual(dr.content_type, pu.content_type)
        # self.assertEqual(dr.section, pu.section)
        self.assertEqual(dr.text, pu.text)

        self.assertEqual(adr.title, apu.title)

        dbt = dr.begin_time
        pbt = pu.begin_time
        det = dr.end_time
        pet = pu.end_time

        self.assertEqual(dbt, pbt)
        self.assertEqual(det, pet)
        self.assertEqual(dr.cm_status, pu.cm_status)
        self.assertEqual(dr.cm_approved, pu.cm_approved)
        self.assertEqual(dr.is_free, pu.is_free)
        self.assertEqual(dr.has_started(), True)
        self.assertEqual(pu.has_started(), True)
        dcr = dr.contactrole.order_by('contact')[0]
        self.assertTrue(isinstance(dcr, ContactRole))
        pcr = pu.contactrole.order_by('contact')[0]
        self.assertTrue(isinstance(pcr, ContactRole))
        self.assertEqual(dcr.contact.first_name, pcr.contact.first_name)
        self.assertEqual(dcr.contact.last_name, pcr.contact.last_name)

        # solr tests
        self.assertEqual(vals_dict["title"], "New Multi Event")
        self.assertEqual(vals_dict["content_type"], "EVENT")
        self.assertEqual(vals_dict["event_type"], "EVENT_MULTI")

        self.assertEqual(vals_dict["begin_time"], force_solr_date_format(pbt, False))
        self.assertEqual(vals_dict["end_time"], force_solr_date_format(pet, False))
        self.assertEqual(vals_dict["cm_status"], "A")
        self.assertEqual(vals_dict["cm_approved"], 1.00)
        self.assertEqual(vals_dict["is_free"], True)
        # check that the parent_id on the Activity in solr is the same as the master_id on the event
        self.assertEqual(vals_dict_act["parent"], str(ev_mult_draft.master_id))

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

        self.assertEqual(dr.publish_status, 'DRAFT')
        self.assertEqual(pu.publish_status, 'PUBLISHED')
