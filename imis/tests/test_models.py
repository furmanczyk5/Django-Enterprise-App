from unittest import mock

from planning.global_test_case import GlobalTestCase
from ..models import CustomEventSchedule, EventFunction


class MockQuerySet:
    def __init__(self, query_set):
        self.query_set = query_set

    def count(self):
        return len(self.query_set)


class EventFunctionTest(GlobalTestCase):
    def setUp(self):
        self.function = EventFunction(
            event_id='19CONF',
            event_function_id='19CONF/NPC123',
            capacity='3',
            max_quantity_per_registrant='2'
        )

        self.ticket_123 = CustomEventSchedule(
            id='123',
            meeting='19CONF',
            product_code='19CONF/NPC123',
            status='A'
        )
        
        self.ticket_456 = CustomEventSchedule(
            id='456',
            meeting='19CONF',
            product_code='19CONF/NPC123',
            status='A'
        )   

        self.query_set = [self.ticket_123, self.ticket_456]

    @mock.patch('imis.models.CustomEventSchedule.objects')
    def test_returns_total_active_tickets_as_tickets_sold(self, mock_tickets):
        mock_tickets.filter.return_value = MockQuerySet(self.query_set)
        self.assertEqual(2, self.function.tickets_sold())

    @mock.patch('imis.models.CustomEventSchedule.objects')
    def test_returns_soldout_status_when_ticket_available(self, mock_tickets):
        mock_tickets.filter.return_value = MockQuerySet(self.query_set)
        self.assertFalse(self.function.soldout())

    @mock.patch('imis.models.CustomEventSchedule.objects')
    def test_returns_soldout_status_when_tickets_soldout(self, mock_tickets):
        query_set = self.query_set + [
            CustomEventSchedule(
                id='789',
                meeting='19CONF',
                product_code='19CONF/NPC123',
                status='A'
            )  
        ]
        mock_tickets.filter.return_value = MockQuerySet(query_set)
        self.assertTrue(self.function.soldout())

    @mock.patch('imis.models.CustomEventSchedule.objects')
    def test_returns_tickets_user_may_purchase_when_no_purchases(self, mock_tickets):
        mock_tickets.filter.return_value = MockQuerySet([])
        self.assertEqual(2, self.function.remaining_tickets_for_user('123'))

    @mock.patch('imis.models.CustomEventSchedule.objects')
    def test_returns_tickets_user_may_purchase_when_some_purchased(self, mock_tickets):
        mock_tickets.filter.return_value = MockQuerySet([self.ticket_123])
        self.assertEqual(1, self.function.remaining_tickets_for_user('123'))

    @mock.patch('imis.models.CustomEventSchedule.objects')
    def test_adjusts_tickets_user_may_purchase_when_fewer_total_tickets(self, mock_tickets):
        mock_tickets.filter.side_effect = [
            MockQuerySet([self.ticket_456, self.ticket_456]),
            MockQuerySet([])
        ]
        self.assertEqual(1, self.function.remaining_tickets_for_user('123'))
