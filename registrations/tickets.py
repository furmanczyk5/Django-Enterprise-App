import pdfkit

from functools import reduce

from django.template.loader import render_to_string
from django.db.models import Prefetch, Q, Count, F
from django.conf import settings

from ui.utils import get_css_path_from_less_path
from content.models import ContentTagType
from store.models import Order, Purchase
from events.models import Event

from .models import Attendee
from .utils import get_complex_receipt_sort

default_page_options = {
    "sato": {
        "page_margin_top":0.0785,
        "page_margin_bottom":0.0785,
        "page_margin_left":0.0785,
        "page_margin_right":0.0785
    },
    "letter": {
        "page_margin_top":0.25,
        "page_margin_bottom":1.75,
        "page_margin_left":0.1875,
        "page_margin_right":0.1875
    },
    "letter_time_correction": {
        "page_margin_top":0.25,
        "page_margin_bottom":0.75,
        "page_margin_left":0.1875,
        "page_margin_right":0.1875
    }
}

class AddressLabelGenerator(object):

    output_type = "string"  # 'string' or 'file'

    def __init__(self, *args, **kwargs):
        self.output_type = kwargs.pop("output_type", None)
        self.output_file_path = kwargs.pop("output_file_path", None)
        self.pdf_output = self.output_file_path if self.output_type == "file" else False
        super().__init__(*args, **kwargs)

    def generate_address_labels(self, queryset):

        attendees = queryset.select_related(
            "contact__user", "purchase__option"
        ).order_by(
            "contact__last_name", "contact__first_name", "contact__user__username"
        ).filter(
            status__in=["A", "H"]  # also allowing hidden attendees (using for speakers)
        )

        html = render_to_string(
            "registrations/tickets/conference-address-labels.html",
            dict(attendees=attendees))

        return self.get_response(html)

    def get_pdfkit_options(self):
        options = {
            "page-width": "3.0in",
            "page-height": "2.0in",
            "margin-top": "0.0in",
            "margin-right": "0.0in",
            "margin-bottom": "0.0in",
            "margin-left": "0.0in"
        }
        return options

    def get_response(self, html):
        css = get_css_path_from_less_path([
            "/static/content/css/style.less",
            "/static/registrations/css/tickets.less"])
        config = pdfkit.configuration(wkhtmltopdf=settings.WKHTMLTOPDF_PATH)
        result = pdfkit.from_string(html, self.pdf_output, css=css, options=self.get_pdfkit_options(), configuration=config)
        return self.pdf_output or result

        # response = HttpResponse(the_pdf, content_type='application/pdf')
        # response['Content-Disposition'] = 'attachment; filename="conference-address-labels.pdf"'


class TicketPdfGenerator(object):

    paper_size = "letter" # letter, sato, letter_time_correction

    query_mode = "conference_full"
        # "conference_full": badge and tickets oriented toward printing for a single conference
        # "badge_only": only prints multipart event tickets
        # "conference_activities": optimized for printing only activities from the selected attendees

    badge_margin_top = 0
    badge_include_twitter = False
    badge_include_twitter_attribute = None

    ticket_margin_top = 0
    num_receipts = 0
    page_margin_top = 0
    page_margin_bottom = 0
    page_margin_left = 0
    page_margin_right = 0
    conference_master_id = None
    on_update_progress = None

    def __init__(self, *args, **kwargs):
        self.paper_size = kwargs.pop("paper_size", self.paper_size)
        self.query_mode = kwargs.pop("query_mode", self.paper_size)
        self.badge_margin_top = kwargs.pop("badge_margin_top", self.badge_margin_top)
        self.badge_include_twitter = kwargs.pop("badge_include_twitter", self.badge_include_twitter)
        self.badge_include_twitter_attribute = kwargs.pop("badge_include_twitter_attribute", self.badge_include_twitter_attribute)
        self.ticket_margin_top = kwargs.pop("ticket_margin_top", self.ticket_margin_top)
        self.num_receipts = kwargs.pop("num_receipts", self.num_receipts)
        self.page_margin_top = kwargs.pop("page_margin_top", self.page_margin_top)
        self.page_margin_bottom = kwargs.pop("page_margin_bottom", self.page_margin_bottom)
        self.page_margin_left = kwargs.pop("page_margin_left", self.page_margin_left)
        self.page_margin_right = kwargs.pop("page_margin_right", self.page_margin_right)
        self.conference_master_id = kwargs.pop("conference_master_id", self.conference_master_id)
        self.on_update_progress = kwargs.pop("on_update_progress", self.on_update_progress)

        self.page_style = "padding:{0}in {1}in {2}in {3}in".format(self.page_margin_top, self.page_margin_right, self.page_margin_bottom, self.page_margin_left)
        self.badge_only = self.query_mode == "badge_only"

    def generate_tickets(self, *args, **kwargs):

        self.progress_complete = 0
        self.TOTAL_PROGRESS = 100  # arbitrary, reset in filter_query

        self.update_progress(self.progress_complete, 'Collecting attendee records')
        grouped_tickets = self.get_grouped_tickets(*args, **kwargs)

        self.update_progress(self.progress_complete + 10, 'Generating Tickets')
        html = self.get_html(grouped_tickets)

        self.update_progress(self.progress_complete + 70, 'Saving PDF')
        output_response = self.get_response(html)

        self.update_progress(self.progress_complete + 20, 'Saving PDF')
        return output_response

    def update_progress(self, new_progress_complete, message):
        self.progress_complete = new_progress_complete
        if self.on_update_progress:
            self.on_update_progress(self.progress_complete, self.TOTAL_PROGRESS, message)

    def get_conference_activity_tickets_prefetch(self):
        prefetch_query = Attendee.objects.exclude(
            event__product__isnull=True
        ).filter(
            event__parent_id=self.conference_master_id,
            event__product__status__in=["A", "H"],
            status="A"
        ).select_related(
            "contact__user", "event", "purchase__product", "purchase__product_price"
        ).prefetch_related(
            self.get_conference_location_prefetch()
        ).order_by("event__begin_time", "event__end_time", "event__title")

        return Prefetch("contact__attending", queryset=prefetch_query, to_attr="conference_tickets")

    def get_conference_receipt_prefetch(self):
        prefetch_query = Order.objects.prefetch_related(
            "purchase_set__product__content__event", "purchase_set__product_price", "payment_set",
        ).filter(
            Q(purchase__product__content__master_id=self.conference_master_id) |
            Q(purchase__product__content__parent_id=self.conference_master_id)
        ).distinct("id")

        return Prefetch("contact__user__orders", queryset=prefetch_query, to_attr="conference_orders")

    def get_conference_location_prefetch(self):
        prefetch_query = ContentTagType.objects.prefetch_related("tags").filter(tag_type__code="ROOM")
        return Prefetch("event__contenttagtype", queryset=prefetch_query, to_attr="contenttagtype_room" )

    def get_conference_receipt(self, attendee, orders):
        conference_receipt = dict(
            ticket_template="registrations/tickets/layouts/CONFERENCE-RECEIPT.html",
            purchases=[],
            purchase_total=0.00,
            payment_total=0.00,
            multipart_attendee=attendee
        )

        for order in orders:
            for purchase in order.purchase_set.all():
                if purchase.product.status != "H":
                    conference_receipt["purchases"].append(purchase)
                conference_receipt["purchase_total"] += float(purchase.quantity * purchase.amount)
            for payment in order.payment_set.all():
                conference_receipt["payment_total"] += float(payment.get_payment_amount())

        # some receipt cleanup
        conference_receipt["purchases"].sort(key=get_complex_receipt_sort(first_master_ids=[self.conference_master_id]))  # purchases sort order
        conference_receipt["purchases_not_visible"] = len(conference_receipt["purchases"][20:])  # to show how many purchases are not included
        conference_receipt["purchases"] = conference_receipt["purchases"][:20]  # only show up to 20 purchases (to prevent wasting paper)

        return conference_receipt

    def get_multipart_full_attendees_queryset(self, query):

        filtered_attendees = query.filter(event__event_type="EVENT_MULTI", status__in=["A", "H"])  # also allowing hidden attendees (using for speakers)
        self.TOTAL_PROGRESS += filtered_attendees.count()

        if not self.conference_master_id:
            # if not specified...
            multi_event_ids = filtered_attendees.order_by("event__master_id").distinct("event__master_id").values_list("event__master_id", flat=True) # Should only ever be one

            if len(multi_event_ids) > 1:
                raise Exception("You may only use this tool to print tickets from one conference at a time.")
            elif not multi_event_ids:
                raise Exception("Please select an attendee record for at least one mulipart event")

            self.conference_master_id = multi_event_ids[0]

        prefetches = [self.get_conference_location_prefetch()]

        if not self.badge_only:
            prefetches.append(self.get_conference_activity_tickets_prefetch())

            if self.num_receipts > 0:
                prefetches.append(self.get_conference_receipt_prefetch())

        attendees = filtered_attendees.prefetch_related(
            *prefetches
        ).select_related(
            "contact__user", "event", "purchase__product_price"
        ).order_by(
            "contact__last_name", "contact__first_name", "contact__user__username"
        )

        return attendees

    def get_multipart_full_attendees(self, query):

        attendees = self.get_multipart_full_attendees_queryset(query)

        grouped_tickets = []
        for i, conf_attendee in enumerate(attendees):

            users_attendees = [conf_attendee]
            if not self.badge_only:
                users_attendees += conf_attendee.contact.conference_tickets

            tickets = []
            for a in users_attendees:
                tickets.append(dict(
                    ticket_template=a.event.ticket_template,
                    attendee=a,
                    purchase=a.purchase,
                    event=a.event,
                    multipart_attendee=conf_attendee
                    # is_standby
                    # description
                    # ticket number (for unsold tickets)
                ))

            if not self.badge_only and self.num_receipts > 0:
                conference_receipt = self.get_conference_receipt(
                    conf_attendee,
                    conf_attendee.contact.user.conference_orders)

                for k in range(0, self.num_receipts):
                    tickets.append(conference_receipt)

            if self.paper_size == "sato":
                grouped_tickets.append(tickets)
            elif self.badge_only:
                if i % 6 == 0:
                    grouped_tickets.append([])
                grouped_tickets[-1].append(tickets[0])
            else:
                for j, ticket in enumerate(tickets):
                    if j % 6 == 0:
                        grouped_tickets.append([])
                    grouped_tickets[-1].append(ticket)

            self.update_progress(self.progress_complete + 1, 'Collecting attendee records')

        return grouped_tickets

    def get_multipart_tickets_only_attendees(self, query):

        if not getattr(self, "conference_master_id"):
            multi_event_ids = query.order_by("event__parent_id").distinct("event__parent_id").values_list("event__parent_id", flat=True) # Should only ever be one

            if len(multi_event_ids) > 1:
                raise Exception("You may only use this tool to print tickets from one conference at a time.")
            elif not multi_event_ids:
                raise Exception("Please select an attendee record for at least one mulipart event")

            self.conference_master_id = multi_event_ids[0]

        if not getattr(self, "ticketonly_attendee_ids", None):
            self.ticketonly_attendee_ids = [a.id for a in query]

        ticket_attendees = query.select_related(
            "contact__user", "event", "purchase__product", "purchase__product_price",
        ).prefetch_related(
            self.get_conference_location_prefetch()
        ).order_by("contact")

        reg_attendees = Attendee.objects.filter(
            contact_id__in=set([a.contact_id for a in ticket_attendees]),
            event__master_id=self.conference_master_id,
        ).select_related(
            "contact__user", "event", "purchase__product_price", "purchase__option"
        ).distinct("contact")

        orders = Order.objects.filter(purchase__attendees__in=self.ticketonly_attendee_ids).prefetch_related(
            "purchase_set__product__content__event", "purchase_set__product_price", "payment_set", "user__contact"
        ).order_by("id").distinct("id")
        orders = sorted(list(orders), key=lambda x: x.user.contact.id)

        grouped_tickets = []

        self.TOTAL_PROGRESS += reg_attendees.count()

        for i, r in enumerate(sorted(reg_attendees, key=lambda a: (a.contact.last_name, a.contact.first_name, a.contact.user.username))):
            r.conference_tickets = [t for t in ticket_attendees if t.contact_id == r.contact_id]
            r.conference_orders = [o for o in orders if o.user.contact.id == r.contact_id]

            tickets = []

            for a in r.conference_tickets:
                tickets.append(dict(
                    ticket_template=a.event.ticket_template,
                    attendee=a,
                    purchase=a.purchase,
                    event=a.event,
                    multipart_attendee=r
                    # is_standby
                    # description
                    # ticket number (for unsold tickets)
                ))

            conference_receipt = self.get_conference_receipt(r, r.conference_orders)
            for k in range(0, self.num_receipts):
                tickets.append(conference_receipt)

            grouped_tickets.append(tickets)  # need conditional filtering for this to work with page_size = letter

            self.update_progress(self.progress_complete + 1, 'Collecting attendee records')

        return grouped_tickets

    def get_grouped_tickets(self, *args, **kwargs):
        query = kwargs.get("query")
        if self.query_mode == "conference_activities":
            return self.get_multipart_tickets_only_attendees(query)
        else:
            return self.get_multipart_full_attendees(query)

    def get_html(self, grouped_tickets):

        html = render_to_string(
            self.get_template(),
            dict(
                grouped_tickets=grouped_tickets,
                paper_size=self.paper_size,
                badge_include_twitter=self.badge_include_twitter,
                badge_include_twitter_attribute=self.badge_include_twitter_attribute,
                badge_margin_top=self.badge_margin_top,
                ticket_margin_top=self.ticket_margin_top,
                page_style=self.page_style
            )
        )
        return html

    def get_template(self):
        if self.paper_size == "sato":
            return "registrations/tickets/tickets-sato.html"
        elif self.paper_size == "letter_time_correction":
            return "registrations/tickets/tickets-letter-urgent.html"
        else:
            return "registrations/tickets/tickets-letter.html"

    def get_pdfkit_options(self):
        options = {
            "margin-top": "0.0in",
            "margin-right": "0.0in",
            "margin-bottom": "0.0in",
            "margin-left": "0.0in"
        }
        if self.paper_size == "sato":
            options.update({"page-width": "4in", "page-height": "4in"})
        else:
            options.update({"page-size": "Letter"})
        return options

    def get_response(self, html):
        css = get_css_path_from_less_path((
            "/static/content/css/style.less",
            "/static/registrations/css/tickets.less"))
        config = pdfkit.configuration(wkhtmltopdf=settings.WKHTMLTOPDF_PATH)
        output = pdfkit.from_string(html, None, css=css, options=self.get_pdfkit_options(), configuration=config)
        return output


class ConferenceKioskTicketGenerator(TicketPdfGenerator):

    paper_size = "sato"
    num_receipts = 2
    page_margin_top = 0.0785
    page_margin_bottom = 0.0785
    page_margin_left = 0.0785
    page_margin_right = 0.0785

    def generate_tickets(self, *args, **kwargs):
        self.full_attendee_ids = kwargs.get("full_attendee_ids", [])
        self.ticketonly_attendee_ids = kwargs.get("ticketonly_attendee_ids", [])
        self.conference_master_id = kwargs.get("conference_master_id", None)
        return super().generate_tickets(*args, **kwargs)

    def get_grouped_tickets(self, *args, **kwargs):
        full_attendees = Attendee.objects.filter(id__in=self.full_attendee_ids)
        ticketonly_attendees = Attendee.objects.filter(id__in=self.ticketonly_attendee_ids)

        grouped_tickets = []
        grouped_tickets += self.get_multipart_full_attendees(full_attendees)
        grouped_tickets += self.get_multipart_tickets_only_attendees(ticketonly_attendees)

        return grouped_tickets


class ConferenceCustomTicketGenerator(TicketPdfGenerator):

    paper_size = "sato"
    num_receipts = 0
    page_margin_top = 0.0785
    page_margin_bottom = 0.0785
    page_margin_left = 0.0785
    page_margin_right = 0.0785

    def generate_tickets(self, *args, **kwargs):
        self.custom_tickets = kwargs.get("custom_tickets", [])
        return super().generate_tickets(*args, **kwargs)

    def get_grouped_tickets(self, *args, **kwargs):
        return [self.custom_tickets]


class TicketPdfFileGenerator(TicketPdfGenerator):

    def __init__(self, *args, **kwargs):
        self.output_file_path = kwargs.pop("output_file_path", None)
        super().__init__(*args, **kwargs)

    def get_response(self, html):
        css = get_css_path_from_less_path((
            "/static/content/css/style.less",
            "/static/registrations/css/tickets.less"))
        config = pdfkit.configuration(wkhtmltopdf=settings.WKHTMLTOPDF_PATH)
        pdfkit.from_string(html, self.output_file_path, css=css, options=self.get_pdfkit_options(), configuration=config)
        return self.output_file_path


