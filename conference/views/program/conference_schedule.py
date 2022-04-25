import copy

# TO DO: import ProductCart instead of Product and refactor based on new pricing logic
from .conference_search import MicrositeConferenceSearchView
from conference.views.program.microsite_search import get_master_ids_for_scheduled_events
from events.models import Activity
from store.models import Product
from imis.models import CustomEventSchedule
from imis.db_accessor import DbAccessor
from imis.event_tickets import save_activity_to_schedule


class ConferenceScheduleView(MicrositeConferenceSearchView):
    """
    User's "My Schedule" for NPC
    """
    content_url = "/conference/schedule/" # not used... remove?

    rows = 100
    title = "My Schedule"
    template_name = "conference/newtheme/program/schedule-from-search.html"
    prompt_login = True
    pdf_filename = "NPC20-myschedule.pdf"

    def get(self, request, *args, **kwargs):
        if self.microsite.url_path_stem and self.microsite.url_path_stem != 'conference':
            self.content_url = "/conference/{}/schedule/".format(self.microsite.url_path_stem)
        self.user = self.request.user
        self.contact = self.user.contact
        return super().get(request, *args, **kwargs)

    def get_queries(self, *args, **kwargs):
        staff_registered_from_waitlist_codes = self.get_ordered_codes()
        self.update_schedule(staff_registered_from_waitlist_codes)
        query = super().get_queries(*args, **kwargs)
        self.waitlist_product_codes = self.get_waitlist_codes()
        product_codes = [t[0] for t in self.get_waitlist_codes()]
        self.waitlist_session_master_ids = get_master_ids_for_scheduled_events(None, product_codes)
        self.scheduled_solr_ids = self.scheduled_solr_ids + ['CONTENT.' + str(i) for i in self.waitlist_session_master_ids]
        query.append('id:(0 %s)' % ' '.join(self.scheduled_solr_ids) )
        return query

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_schedule'] = True
        context['contact'] = self.contact
        context['results']['response']['docs'] = self.add_ticket_quantity_to_events(context, self.scheduled)
        context["title"] = "My Schedule"
        context["waitlisted_master_ids"] = self.waitlist_session_master_ids
        return context

    def add_ticket_quantity_to_events(self, context, scheduled_events):
        # TEMP REMOVE FOR LOCAL TESTING REMOTELY
        events = context['results']['response']['docs']
        # events = []

        for event in events:
            if event.get('prices', None):
                event['quantity'] = self.get_quantity(event, scheduled_events)

        return events

    def has_regular_ticket(self, code, scheduled_codes):
        return code in scheduled_codes

    def update_data_for_waitlist(self, event):
        event = copy.deepcopy(event)
        return self.replace_data_for_waitlist(event)

    def replace_data_for_waitlist(self, event):
        event['title'] = self.create_waitlist_title(event)
        return event

    def get_product_codes(self, events):
        products = Product.objects.filter(
            code__in=map(lambda event: event['code'], events)
        )
        current_codes = set(map(lambda product: product.imis_code, products))
        return list(current_codes)

    def split_product_code(self, code):
        return code.split('/')[-1]

    # THIS IS NOT BEING CALLED FROM /conference/schedule/
    def get_scheduled_events(self, events, contact):
        return list(CustomEventSchedule.objects.filter(
            id=contact.user.username,
            product_code__in=self.get_product_codes(events),
            status='A'
        ))

    def get_scheduled_codes(self, scheduled_events):
        return set([
            event.product_code
            for event in scheduled_events
        ])

    def get_waitlist_codes(self):
        query = """
                SELECT OL.PRODUCT_CODE, P.TITLE, PF.BEGIN_DATE_TIME, PF.END_DATE_TIME, OL.DESCRIPTION
                FROM Order_Lines as OL 
                INNER JOIN Orders as O
                ON OL.ORDER_NUMBER = O.ORDER_NUMBER
                INNER JOIN Product as P 
                ON P.PRODUCT_CODE = OL.PRODUCT_CODE
                INNER JOIN Product_Function as PF
                ON OL.PRODUCT_CODE = PF.PRODUCT_CODE
                WHERE O.BT_ID=? --AND OL.PRODUCT_CODE IN ?
                  AND OL.ADDED_TO_WAIT_LIST IS NOT NULL
                    AND OL.QUANTITY_BACKORDERED > 0--AND ORDER_DATE=?        """
        rows = DbAccessor().get_rows(
            query,
            [
                self.user.username,
            ]
        )
        return rows

    def create_waitlist_title(self, event):
        return 'WAITLIST: {}'.format(event['title'])

    def get_quantity(self, event, scheduled_events):
        return len(
            [
                event
                for scheduled_event in scheduled_events
                if self.split_product_code(scheduled_event.product_code) == event['code']
            ]
        )

    def get_ordered_codes(self):
        """
        Here 'ordered' means staff registered user from waitlist in imis
        :param scheduled_codes:
        :return:
        """
        query = """
                SELECT OL.PRODUCT_CODE
                FROM Order_Lines as OL
                INNER JOIN Orders as O
                ON OL.ORDER_NUMBER = O.ORDER_NUMBER
                WHERE O.BT_ID=?
                  AND OL.ADDED_TO_WAIT_LIST IS NOT NULL
                    AND OL.QUANTITY_ORDERED > 0"""
        rows = DbAccessor().get_rows(query, [self.user.username])
        return rows


    def update_schedule(self, ordered_codes):
        ordered_codes = [o[0] for o in ordered_codes if len(o) > 0]
        activities = Activity.objects.filter(
            product__imis_code__in=ordered_codes,
            publish_status="DRAFT"
        )
        username = self.user.username
        for activity in activities:
            save_activity_to_schedule(activity, username, api=False)
