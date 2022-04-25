import datetime

from django.contrib.auth.models import User
from django.utils import timezone

from content.models import Content, TagType, TaxoTopicTag
from planning.global_test_case import GlobalTestCase


# ----------------------------------------------------------
# some dummy setup stuff here

# TESTS TO CREATE:

# -------------------------------------------------------------------------------------------

# SAVING/PUBLISHING:

# - after creating/saving new (draft) record:
# DONE - - - master content record is created, with master's content_draft = new record's id AND draft content's master = new master ID
# DONE - - - draft record's is_published returns false
# DONE - - - draft record's is_up_do_date returns false

# - after saving existing draft record:
# - - - master content record remains the same
# - - - draft record's is_up_do_date returns false

# - after publishing a record: 
# - - - master content record's content_live should point to a record with publish_status=PUBLISHED 
# - - - on the published record, all fields other than publish_status equal those on the draft record (how to test this?)
# - - - draft record's is_published returns true
# - - - draft record's is_up_do_date returns true

# -------------------------------------------------------------------


class BaseContentTests(GlobalTestCase):
    """
    tests base content info abstract class methods
    """

    @classmethod
    def setUpTestData(cls):
        super(BaseContentTests, cls).setUpTestData()
        cls.test_user, user_created = User.objects.get_or_create(username="000007", password="norman_pass")

    def test_title_save_time(self):

        yesterday_time = timezone.now() - datetime.timedelta(days=1)

        # testing on an instance of TagType, since this is a simple model that inherits from BaseContent, with none of its own methods:
        tag_type = TagType(code="TEST_TAG_TYPE") 
        # tag_type.updated_by = user
        # tag_type.created_by = user
        
        self.assertEqual(str(tag_type), "[no title]")
        tag_type.title = "My new title!"
        self.assertEqual(str(tag_type), "My new title!")

        # now save, for testing updated and created times
        tag_type.save()
        # for the new instance, make sure that created and updated times set, and greater than yesterday
        self.assertTrue(tag_type.updated_time > yesterday_time)
        self.assertTrue(tag_type.created_time > yesterday_time)

        # now assume that tag type was created yesterday, and save... updated_time should be reset, but created_time should remain as is
        tag_type.created_time = yesterday_time
        tag_type.updated_time = yesterday_time
        tag_type.save()
        self.assertTrue(tag_type.updated_time > yesterday_time)
        self.assertEqual(tag_type.created_time, yesterday_time)


class TaxoTopicTagTests(GlobalTestCase):
    """
    tests taxo topic tag save ... and queryset filter?
    """

    @classmethod
    def setUpTestData(cls):
        super(TaxoTopicTagTests, cls).setUpTestData()
        cls.test_user, user_created = User.objects.get_or_create(username="000007", password="norman_pass")

    def setUp(self):
        self.taxo_topic_tag_type, created = TagType.objects.get_or_create(code="TAXO_MASTERTOPIC")

    def test_save(self):
        taxo_topic_tag = TaxoTopicTag(code="NEW_TOPIC_TAG")
        taxo_topic_tag.save()
        # the type foreign key for the new tag should automatically be set to the TAXO_MATERTOPIC tag type on save: 
        self.assertEqual(taxo_topic_tag.tag_type, self.taxo_topic_tag_type)

    # TBD... test for the queryset filter?


# next up.... MasterContent tests


class ContentTests(GlobalTestCase):
    """
    tests for content records
    """
    @classmethod
    def setUpTestData(cls):
        super(ContentTests, cls).setUpTestData()
        cls.test_user, user_created = User.objects.get_or_create(username="000007", password="norman_pass")

    def setUp(self):
        new_content = Content(title="Test Content", code="TEST_DRAFT_CONTENT")
        new_content.created_by = self.test_user
        new_content.save()

    def test_master_record_created(self):
        """
        when new (draft) content record is saved, master record should also be created, such that...
        new content's master attribute should = foreign key reference to the master record
        master record's content_draft attribute should = foreign key reference to the new content
        """
        new_content = Content.objects.get(code="TEST_DRAFT_CONTENT")
        self.assertIsNotNone(new_content.master) # master must exist
        self.assertIsNotNone(new_content.master.content_draft) # the master content_draft attribute must be set
        self.assertEqual(new_content.id, new_content.master.content_draft.id) # the master content_draft id must be the id of the content

    def test_is_not_published_and_is_not_up_to_date(self):
        """
        when new (draft) content record is saved, it should be marked as not up-to-date and not published
        """
        new_content = Content.objects.get(code="TEST_DRAFT_CONTENT")
        self.assertFalse(new_content.is_published())
        self.assertFalse(new_content.is_up_to_date())


