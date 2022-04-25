from decimal import *
from unittest import mock, skip

from django.contrib.auth.models import Group

from content.models import Content, MasterContent
from planning.global_test_case import GlobalTestCase
from store.models import Product, ProductPrice, Purchase


@skip
class BookProductPriceTestCase(GlobalTestCase):

    @classmethod
    def setUpTestData(cls):

        super(BookProductPriceTestCase, cls).setUpTestData()

        cls.mem_grp = Group.objects.get_or_create(name='member')

    def setUp(self):
        # Set up a dummy product with member and nonmember prices
        pc, pc_created = Content.objects.get_or_create(
            title='product_content',
            content_type='PUBLICATION'
        )
        tp, tp_created = Product.objects.get_or_create(
            title='test_product',
            code='BOOK_Z00000',
            content=pc
        )

        lp, lp_created = ProductPrice.objects.get_or_create(
            title='list_price',
            product=tp,
            price=34.95,
            priority=2
        )

        mp, mp_created = ProductPrice.objects.get_or_create(
            title='apa_member_price',
            product=tp,
            price=24.95,
            priority=1
        )

        mp.required_groups.add(self.mem_grp)
        mp.save()
        self.test_product = tp
        # just use one user and one product and reset all the values each time
        # each test will set all the values and just run one test

        # make a product with product_type = 'DUES' AND code="MEMBERSHIP_AICP"

        # make a product with product_type = 'DUES' AND code="MEMBERSHIP_STU"

    # SET PRIORITY EXPLICITLY FOR EACH PRODUCT PRICE
    # or instead of creating the price (saved to database)
    # just instantiate it inside of each function - so it goes away?
    def test_list_price(self):
        self.purchase = self.test_product.add_to_cart(user=self.non_mem_user)
        self.assertEqual(self.purchase.product_price.price, Decimal('34.95'))

    def test_member_price(self):
        self.purchase = self.test_product.add_to_cart(user=self.test_user)
        self.assertEqual(self.purchase.product_price.price, Decimal('24.95'))
        self.test_user.groups.remove(self.mem_grp)


@skip
class PurchaseTest(GlobalTestCase):
    def setUp(self):
        self.mock_events_patcher = mock.patch('events.models.Event')
        self.mock_events = self.mock_events_patcher.start()
        self.mock_events.objects.filter().first().get_meeting_code.return_value = '19CONF'

        self.mock_delete_patcher = mock.patch('store.models.delete_event_tickets')
        self.mock_delete = self.mock_delete_patcher.start()

        self.content = Content.objects.create(
            title='product_content',
            content_type='PUBLICATION'
        )
        self.product = Product.objects.create(
            title='test_product',
            code='NPC12345',
            content=self.content,
            product_type='ACTIVITY_TICKET'
        )
        self.product_price = ProductPrice.objects.create(
            title='list_price',
            product=self.product,
            price=34.95,
            priority=2,
            imis_reg_class='CCONF'
        )
        self.master_content = MasterContent.objects.get(
            id=self.content.master_id
        )
        self.attributes = {
            'user': self.test_user,
            'contact': self.test_user.contact,
            'product': self.product,
            'content_master': self.master_content,
            'product_price': self.product_price,
            'amount': 1.00,
            'submitted_product_price_amount': self.product_price.price,
            'quantity': 1
        }
        self.expected_attributes = {
            'id': self.test_user.username,
            'seqn': 1,
            'meeting': '19CONF',
            'registrant_class': self.product_price.imis_reg_class,
            'product_code': self.product.imis_code,
            'status': 'I',
            'unit_price': self.product_price.price
        }

    def tearDown(self):
        self.mock_events_patcher.stop()
        self.mock_delete_patcher.stop()

    @mock.patch('store.models.CustomEventTickets')
    def test_creating_conference_purchase_saves_ticket_to_imis(self, mock_tickets):
        mock_tickets.objects.filter.return_value = []
        Purchase.objects.create(**self.attributes)
        mock_tickets.objects.create.assert_called_with(
            **sort_attributes(self.expected_attributes)
        )

    @mock.patch('store.models.CustomEventTickets')
    def test_increments_seqn_for_tickets_with_same_user(self, mock_tickets):
        mock_tickets.objects.filter.return_value = MockQuerySet()
        self.attributes['quantity'] = 1
        Purchase.objects.create(**self.attributes)
        self.expected_attributes['seqn'] = 2
        mock_tickets.objects.create.assert_called_with(
            **sort_attributes(self.expected_attributes)
        )

    @mock.patch('store.models.CustomEventTickets')
    def test_creates_tickets_equal_to_purchase_quantity(self, mock_tickets):
        mock_tickets.objects.filter.return_value = MockQuerySet()
        self.attributes['quantity'] = 3
        Purchase.objects.create(**self.attributes)
        self.assertEqual(3, mock_tickets.objects.create.call_count)

    @mock.patch('store.models.CustomEventTickets')
    def test_deletes_tickets_from_imis(self, mock_tickets):
        mock_tickets.objects.filter.return_value = MockQuerySet()
        purchase = Purchase.objects.create(**self.attributes)
        purchase.delete()
        self.assertTrue(self.mock_delete.called)


class MockQuerySet():
    def __iter__(self):
        return iter([MockTicket()])

    def __len__(self):
        return 1

    def latest(self, field):
        return MockTicket()


class MockTicket:
    seqn = 1


def sort_attributes(attributes):
    sorted_dict = {}

    for key in sorted(attributes.keys()):
        sorted_dict[key] = attributes[key]

    return sorted_dict
