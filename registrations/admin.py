# from collections import OrderedDict
# from datetime import date

# import pdfkit
# import pickle
# import csv
# import uuid
# import pytz

# from django import forms
# from django.shortcuts import render
# from django.contrib import admin
# from django.template.loader import render_to_string
# from django.http import HttpResponse, JsonResponse
# from django.db.models import Prefetch, Q
# from django.conf import settings
# from django.utils import timezone

# from ui.utils import get_css_path_from_less_path
# from myapa.utils import individual_fullname
# from content.models import ContentTagType
# from events.models import NATIONAL_CONFERENCES, NATIONAL_CONFERENCE_ADMIN, EventMulti
# from store.models import Order, Purchase
# from conference.models import NationalConferenceActivity #, NationalConferenceAttendee

# # from .models import Attendee, ATTENDEE_STATUSES

# from .tasks import create_attendee_tickets_pdf, create_attendee_address_labels_pdf
# from .tickets import ConferenceKioskTicketGenerator

# # FOR MASS PRINTING
# ALPHA_REGEX_GROUPINGS = {
#     "last_name_alpha_6":(
#         ("[a-d]", "A-D"),
#         ("[e-j]", "E-J"),
#         ("[k-o]", "K-O"),
#         ("[p-s]", "P-S"),
#         ("[t-z]", "T-Z"),
#         ("[^a-z]", "_OTHER")
#     ), 
#     "last_name_alpha_21":(
#         ("a", "A"),
#         ("b", "B"),
#         ("c", "C"),
#         ("d", "D"),
#         ("e", "E"),
#         ("f", "F"),
#         ("g", "G"),
#         ("h", "H"),
#         ("[i-j]", "I-J"),
#         ("k", "K"),
#         ("l", "L"),
#         ("m", "M"),
#         ("[n-o]", "N-O"),
#         ("[p-q]", "P-Q"),
#         ("r", "R"),
#         ("s", "S"),
#         ("t", "T"),
#         ("[u-v]", "U-V"),
#         ("w", "W"),
#         ("[x-z]", "X-Z"),
#         ("[^a-z]", "_OTHER")
#     ), 
#     "last_name_alpha_30":(
#         ("a", "A"),
#         ("b[^m-z]", "Ba-Bl"),
#         ("b[m-z]", "Bm-Bz"),
#         ("c[^m-z]", "Ca-Cl"),
#         ("c[m-z]", "Cm-Cz"),
#         ("d", "D"),
#         ("e", "E"),
#         ("f", "F"),
#         ("g[^m-z]", "Ga-Gl"),
#         ("g[m-z]", "Gm-Gz"),
#         ("h[^i-z]", "Ha-Hh"),
#         ("h[i-z]", "Hi-Hz"),
#         ("[i-j]", "I-J"),
#         ("k", "K"),
#         ("l", "L"),
#         ("m[^i-z]", "Ma-Mh"),
#         ("m[i-z]", "Mi-Mz"),
#         ("[n-o]", "N-O"),
#         ("p[^l-z]", "Pa-Pk"),
#         ("((p[l-z])|(q))","Pl-Q"),
#         ("r[^i-z]", "Ra-Rh"),
#         ("r[i-z]", "Ri-Rz"),
#         ("s[^i-z]", "Sa-Sh"),
#         ("s[i-z]", "Si-Sz"),
#         ("t", "T"),
#         ("[u-v]", "U-V"),
#         ("w[^i-z]", "Wa-Wh"),
#         ("w[i-z]", "Wi-Wz"),
#         ("[x-z]", "X-Z"),
#         ("[^a-z]", "_OTHER")
#     ), 
# }


# class DefaultActiveStatusFilter(admin.SimpleListFilter):

#     title = 'Status'
#     parameter_name = 'status'

#     def lookups(self, request, model_admin):
#         lookup_list = list(ATTENDEE_STATUSES)
#         active_choice_index = next(i for i, choice in enumerate(lookup_list) if choice[0] == "A")
#         lookup_list[active_choice_index] = (None, "Active")
#         lookup_list.insert(0, ("ANY", "Any"))
#         return lookup_list

#     def choices(self, cl):
#         for lookup, title in self.lookup_choices:
#             yield {
#                 'selected': self.value() == lookup,
#                 'query_string': cl.get_query_string({
#                     self.parameter_name: lookup,
#                 }, []),
#                 'display': title,
#             }

#     def queryset(self, request, queryset):
#         if self.value() is None: # default only active
#             return queryset.filter(status="A")
#         elif self.value() == "ANY":
#             return queryset
#         else:
#             return queryset.filter(status=self.value())


# class PrintBadgesAndTicketsOptionsForm(forms.Form):
#     _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
#     select_across = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=0)

#     paper_size = forms.ChoiceField(label="Paper Size", required=True, choices=(
#         ("letter", "Letter (8.5x11in, 6 items per page"),
#         ("sato", "Sato (4x4in, 1 item per page)"),
#         ("letter_time_correction", "Letter (Time Correction)")), initial="sato")

#     query_mode = forms.ChoiceField(label="What are you printing?", required=True, choices=(
#         ("conference_full", "Complete Badge and Ticket Orders for a conference"),
#         ("conference_activities", "ONLY ACTIVITY tickets for a conference"),
#         ("badge_only", "ONLY BADGES for a conference")))

#     separate_documents = forms.ChoiceField(
#         choices=(
#             ("None", "No"), 
#             ("last_name_alpha_6", "Last Name Alpha (<= 6 pdfs)"),
#             ("last_name_alpha_21", "Last Name Alpha (<= 21 pdfs)"),
#             ("last_name_alpha_30", "Last Name Alpha (<= 30 pdfs)")),
#         label="Print In Groups",
#         help_text="Use a grouping when printing a large number of badges and tickets, especially if tickets include images. This is most useful when printing for NPC.")

#     badge_include_twitter = forms.BooleanField(label="Include Twitter Handle", required=False)
#     badge_include_twitter_attribute = forms.ChoiceField(label="Twitter Handle Registration Question", required=False, choices=[(None, ""), ("question_response_1", "Question 1"), ("question_response_2", "Question 2"), ("question_response_3", "Question 3")])
#     badge_margin_top = forms.FloatField(label="Badge Top Margin", required=False, help_text="units are in inches", initial=0.00)

#     ticket_margin_top = forms.FloatField(label="Ticket Top Margin", required=False, help_text="units are in inches", initial=0.00)

#     page_margin_top = forms.FloatField(label="Page Top Margin", required=False, help_text="units are in inches", initial=0.25)
#     page_margin_bottom = forms.FloatField(label="Page Bottom Margin", required=False, help_text="units are in inches", initial=1.75)
#     page_margin_left = forms.FloatField(label="Page Left Margin", required=False, help_text="units are in inches", initial=0.1875)
#     page_margin_right = forms.FloatField(label="Page Right Margin", required=False, help_text="units are in inches", initial=0.1875)

#     num_receipts = forms.TypedChoiceField(label="Number of Receipts", required=False, choices=[(0, 0), (1, 1), (2, 2)], coerce=int, initial=2)

#     def clean(self):
#         cleaned_data = super().clean()
#         if cleaned_data.get("badge_include_twitter") and not cleaned_data.get("badge_include_twitter_attribute"):
#             self.add_error('badge_include_twitter_attribute', "To print twitter handles, you must specify which registration question was for twitter handles")
#         return cleaned_data


# class AttendeeAdmin(admin.ModelAdmin):

#     # SHOULD WE PREVENT CREATING NEW ATTENDEES ???

#     list_display = ["id", "get_event_master_id", "get_event_code", "event", "get_event_begin_time", "get_username", "contact", "get_single_purchase_amount", "status","get_purchase_submitted_time","get_member_type", "get_last_name", "get_first_name", "is_standby"]
#     search_fields = ["=id", "=contact__user__username", "contact__title", "event__title", "=event__id", "=event__code", "=event__master__id", "=event__parent__content_live__code"] # "event__product__code", "event__product__code"]

#     list_filter = ["event__event_type", DefaultActiveStatusFilter, "is_standby", "purchase__submitted_time"]

#     fieldsets = [
#         (None, {
#             "fields":(
#                 ("status", "is_standby"), 
#                 "contact", "badge_name", 
#                 ("badge_company", "badge_location"), 
#                 "purchase", "get_purchase_submitted_time", "added_time", "event", 
#                 ("cancel", "transfer_attendance"),
#                 ("ready_to_print", "print_count", "last_printed_time"),
#                 #("get_order_overview"), 
#                 ("credit_card_refund_options"),
#                 ("check_refund_options"),
#                 ("adjustment_options"),
#                 )
#         }),
#         ("Address", {
#             "fields":(
#                 ("address1", "address2"),
#                 ("city", "state"),
#                 ("country", "zip_code")
#             )
#         })
#     ]

#     readonly_fields = ["get_purchase_submitted_time", "added_time", "transfer_attendance", "cancel","check_refund_options","credit_card_refund_options","adjustment_options"]

#     raw_id_fields = ["contact", "purchase", "event"]
#     autocomplete_lookup_fields = {"fk": ["contact", "purchase", "event"]}

#     actions = ["print_tickets_W_options", "get_csv_report"]

#     def get_queryset(self, request):

#         # TO DO... we need to create this "product-admin" login group... we're checking for for that instead of staff (because chapter admins will also be marked as is_staff)
#         qs = super().get_queryset(request).select_related("event", "contact__user", "purchase__product", "purchase__user")
#         if request.user.groups.filter(name__in=["staff-store-admin", "onsite-conference-admin"]).exists() or request.user.is_superuser:
#             return qs
#         else:
#             # organization = Organization.objects.get(user__username='050501')
#             admin_relationship = request.user.contact.contactrelationship_as_target.all().filter(relationship_type="ADMINISTRATOR").first()
#             if admin_relationship:
#                 organization = admin_relationship.source
#                 return qs.filter(
#                     Q(purchase__product__content__contactrole__contact=organization) | 
#                     Q(purchase__product__content__parent__content_live__contactrole__contact=organization)).distinct()
#             else:
#                 return qs.none()

#     def get_event_code(self, obj):
#         return obj.event.code
#     get_event_code.short_description = "Event Code"
#     get_event_code.admin_order_field = "event__code"

#     def get_username(self, obj):
#         return obj.contact.user.username
#     get_username.short_description = "Imis ID"
#     get_username.admin_order_field = "contact__user__username"

#     def get_member_type(self, obj):
#         return obj.contact.member_type
#     get_member_type.short_description = "Member Type"
#     get_member_type.admin_order_field = "contact__member_type"

#     # def get_order_overview(self, obj):
#     #     order_overview = obj.order_overview()
#     #     return ( "Purchases: $" + str(order_overview[0]) + "<br/>Payments: $" + str(order_overview[1]) + "<br/>Balance: $" + str(order_overview[2]) )
#     # get_order_overview.short_description = "Conference order overview from all related orders"
#     # get_order_overview.allow_tags = True
    
#     def credit_card_refund_options(self, obj):
#         if obj.status=="R":
#             purchase = Purchase.objects.filter(product=obj.purchase.product, contact=obj.contact, quantity__lt=0).exclude(order__isnull=True).last()
#             purchase_date = purchase.submitted_time.strftime("%B %d, %Y")

#             return ("<div>This attendee record has been refunded. The most recent refund for this user was processed on {0}. <br/> <a href='/admin/store/order/{1}/change' target='_blank'>View order ID: {2}</a></div>".format(purchase_date, str(purchase.order.id), str(purchase.order.id)))
#         elif not obj.purchase:
#             return ("<div>There is not a purchase associated with this record. You can only refund purchased activities.</div>")
#         elif obj.event.event_type in ("EVENT_SINGLE","EVENT_MULTI"):
#             return ("<div style='width:1500px'><a href='/registrations/admin/attendee/" + str(obj.id) + "/?refund_type=CC_REFUND'" +  """ onClick="return confirm('Submit credit card refund for NPC & all activities?')" """ + """ style='color: #cc0000;' >NPC & all activities</a>"""
#             + 
#                 "<a href='/registrations/admin/attendee/" + str(obj.id) + "/?refund_type=CC_REFUND&cancellation_fee=1" + """' style='color: #cc0000; margin-left:80px' """ +  """ onClick="return confirm('Submit credit card refund for NPC & activities with cancellation fee?')" """ + ">NPC & all activities with cancellation fee</a></div>")
#         elif obj.event.event_type == "ACTIVITY":
#             return ("<a href='/registrations/admin/attendee/" + str(obj.id) + "/?refund_type=CC_REFUND'" +  """ onClick="return confirm('Submit credit card refund?')" """ + "style='color: #cc0000' >Full Credit Card Refund</a>")

#     credit_card_refund_options.short_description = "Credit Card Refund Options"
#     credit_card_refund_options.allow_tags = True

#     def check_refund_options(self, obj):
#         if obj.status=="R":
#             return ("")
#         elif not obj.purchase:
#             return ("")
#         elif obj.event.event_type in ("EVENT_SINGLE","EVENT_MULTI"):
#             return ("<div style='width:800px'><a href='/registrations/admin/attendee/" + str(obj.id) + "/?refund_type=CHECK_REFUND'" +  """ onClick="return confirm('Submit check refund for NPC & all activities?')" """ + " style='color: #cc0000;' >NPC & all activities</a>"
#             + 
#                 "<a href='/registrations/admin/attendee/" + str(obj.id) + "/?refund_type=CHECK_REFUND&cancellation_fee=1'" +  """ onClick="return confirm('Submit check refund for NPC & all activities with a cancellation fee?')" """ + " style='color: #cc0000; margin-left:80px' >NPC & all activities with cancellation fee</a></div>")
#         elif obj.event.event_type == "ACTIVITY":
#             return ("<a href='/registrations/admin/attendee/" + str(obj.id) + "/?refund_type=CHECK_REFUND'" +  """ onClick="return confirm('Submit check refund?')" """ + " style='color: #cc0000' >Full Check Refund</a>")

#     check_refund_options.short_description = "Check Refund Options"
#     check_refund_options.allow_tags = True

#     def adjustment_options(self, obj):
#         if obj.status=="R" or not obj.purchase:
#             return ("")
#         else:
#             return ("<a href='/registrations/admin/attendee/" + str(obj.id) + "/?adjustment=1'" +  """ onClick="return confirm('Cancel purchase for adjustment?')" """ + " style='color: #cc0000' >Cancel purchase for adjustment</a>")

#     adjustment_options.short_description = "Adjustments (cancels purchase without refund payment)"
#     adjustment_options.allow_tags = True


#     def get_single_purchase_amount(self, obj):
#         if obj.purchase:
#             return "$" + str(obj.purchase.amount / obj.purchase.quantity)
#         else:
#             return "--"
#     get_single_purchase_amount.short_description = "Price"

#     def get_event_begin_time(self, obj):
#         return obj.event.begin_time
#     get_event_begin_time.short_description = "Begin Time"
#     get_event_begin_time.admin_order_field = "event__begin_time"

#     def get_event_master_id(self, obj):
#         return obj.event.master_id
#     get_event_master_id.short_description = "Master"
#     get_event_master_id.admin_order_field = "event__master_id"

#     def get_last_name(self, obj):
#         return obj.contact.last_name
#     get_last_name.short_description = "Last Name"
#     get_last_name.admin_order_field = "contact__last_name"

#     def get_first_name(self, obj):
#         return obj.contact.first_name
#     get_first_name.short_description = "First Name"
#     get_first_name.admin_order_field = "contact__first_name"

#     def get_purchase_submitted_time(self, obj):
#         if obj.purchase:
#             return obj.purchase.submitted_time
#     get_purchase_submitted_time.short_description = "Submitted Time"
#     get_purchase_submitted_time.admin_order_field = "purchase__submitted_time"

#     def cancel(self, obj):
#         return ("<a href='/registrations/admin/cancel/" + str(obj.id) + "/" + str(obj.event.id) + "/'>CANCEL</a>")
#     cancel.short_description = ""
#     cancel.allow_tags = True

#     def transfer_attendance(self, obj):
#         return ("<a href='/registrations/admin/transfer_attendance/" + str(obj.id) + "/" + str(obj.event.id) + "/'>Transfer Attendance</a>")
#     transfer_attendance.short_description = ""
#     transfer_attendance.allow_tags = True

#     def get_csv_report(self, request, queryset):

#         fieldnames = OrderedDict([
#             ("id", "Ticket ID"),
#             ("contact__user__username", "User ID"),
#             ("contact__title", "Full Name"),
#             ("contact__first_name", "First"),
#             ("contact__middle_name", "Middle"),
#             ("contact__last_name", "Last"),
#             ("contact__suffix_name", "Suffix"),
#             ("contact__designation", "Designation"),
#             ("contact__email", "Email"),
#             ("badge_name", "Badge Name"),
#             ("badge_company", "Badge Company"),
#             ("badge_location", "Badge Location"),
#             ("purchase__submitted_time", "Submitted Time"),
#             ("address1", "Address 1"),
#             ("address2", "Address 2"),
#             ("city", "City"),
#             ("state", "State"),
#             ("zip_code", "Zip"),
#             ("country", "Country")
#         ])

#         response = HttpResponse(content_type='text/csv')
#         response['Content-Disposition'] = 'attachment; filename="badge-report.csv"'

#         writer = csv.DictWriter(response, fieldnames=fieldnames)
#         writer.writerow(fieldnames)
#         for attendee in queryset.values(*fieldnames):
#             attendee["contact__title"] = individual_fullname(
#                 firstname=attendee["contact__first_name"],
#                 lastname=attendee["contact__last_name"],
#                 middle_initial=attendee["contact__middle_name"],
#                 suffix=attendee["contact__suffix_name"],
#                 designation=attendee["contact__designation"])
#             writer.writerow(attendee)

#         return response
#     get_csv_report.short_description = "Badge/Ticket Report"

#     def print_tickets_W_options(self, request, queryset):

#         form = None
#         attendee_list = queryset.select_related("contact")

#         if "apply" in request.POST:

#             form = PrintBadgesAndTicketsOptionsForm(request.POST)
#             if form.is_valid():
    
#                 task_options = dict(form.cleaned_data)
#                 separate_documents_code = task_options.get("separate_documents", "")
#                 task_results = []

#                 if separate_documents_code in ["last_name_alpha_6", "last_name_alpha_21", "last_name_alpha_30"]:

#                     now = timezone.now().astimezone(pytz.timezone("US/Central"))
#                     task_options["file_subpath"] = "alpha-{0}/".format(now.strftime('%Y-%m-%d_%H:%M:%S'))
#                     alpha_expressions = ALPHA_REGEX_GROUPINGS[separate_documents_code] 
                    
#                     for exp in alpha_expressions:

#                         name = exp[1]
#                         alpha_query = queryset.filter(contact__last_name__iregex="^{0}".format(exp[0]))
#                         if alpha_query.exists():
#                             pickled_query = pickle.dumps(alpha_query.query, 0).decode()
#                             task_options["filename_prefix"] = name + "-"
#                             task_result = create_attendee_tickets_pdf.apply_async(kwargs=dict(
#                                 pickled_query=pickled_query,
#                                 options=task_options))
#                             task_results.append(dict(name=name, task_id=task_result.task_id))
                        
#                 else:
#                     pickled_query = pickle.dumps(queryset.query, 0).decode()
#                     task_result = create_attendee_tickets_pdf.apply_async(kwargs=dict(
#                             pickled_query=pickled_query,
#                             options=task_options))
#                     task_results.append(dict(name="all", task_id=task_result.task_id))

#                 context = dict(success=True, tasks=task_results)
#                 return JsonResponse(context)
#             else:
#                 context = dict(success=False, errors=form.errors)
#                 return JsonResponse(context)

#         if not form:
#             form = PrintBadgesAndTicketsOptionsForm(initial={
#                 '_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME),
#                 "select_across": request.POST.get("select_across", 0) })

#         return render(request, 'admin/registrations/attendee/print-badges-and-sessions-with-options.html', dict(attendees=[a.contact for a in attendee_list], form=form))

#     print_tickets_W_options.short_description = "Print Badge and Tickets with options"

#     # NEED TO MOVE THIS INTO TICKET PRINTING GENERATOR CLASS
#     # def print_tickets(modeladmin, request, queryset, include_sessions=True):

#     #     attendees = queryset if include_sessions else queryset.filter(event__event_type="EVENT_MULTI")

#     #     attendees = attendees.select_related(
#     #         "contact__user", "event", "purchase", "purchase__product_price"
#     #     ).order_by(
#     #         "contact__last_name", "contact__first_name", "contact__user__username", "-event__event_type", "event__begin_time", "event__end_time", "event__title"
#     #     )

#     #     # separate into groups of 6
#     #     last_contact_id = None
#     #     grouped_attendees = []
#     #     group_count = 0
#     #     for i, attendee in enumerate(attendees):
#     #         if group_count % 6 == 0 or (include_sessions and not attendee.contact_id == last_contact_id): # new page for new contact, except for badge only
#     #             group_count = 0
#     #             last_contact_id = attendee.contact_id
#     #             grouped_attendees.append([])
#     #         grouped_attendees[-1].append(attendee)
#     #         group_count += 1

#     #     the_css = get_css_path_from_less_path(["/static/content/css/style.less","/static/registrations/css/tickets.less"])
#     #     the_html = render_to_string("registrations/tickets/chapter-registrations.html", {"grouped_attendees":grouped_attendees})
        
#     #     the_options = {
#     #         "page-size": "Letter",
#     #         "margin-top": "0.0in",
#     #         "margin-right": "0.0in",
#     #         "margin-bottom": "0.0in",
#     #         "margin-left": "0.0in"
#     #     }
#     #     config = pdfkit.configuration(wkhtmltopdf=settings.WKHTMLTOPDF_PATH)
#     #     the_pdf = pdfkit.from_string(the_html, False, css=the_css, options=the_options, configuration=config)

#     #     response = HttpResponse(the_pdf, content_type='application/pdf')
#     #     response['Content-Disposition'] = 'attachment; filename="tickets.pdf"'

#     #     return response
#     # print_tickets.short_description = "Print Tickets"


# # THESE FILTERS ARE REPEATED A FEW TIMES, USE ONE CLASS, OR inherit
# class NationalConferenceAttendeeFilter(admin.SimpleListFilter):

#     title = 'National Conference Year'
#     parameter_name = 'conference_year'
#     default_choice = NATIONAL_CONFERENCE_ADMIN

#     def lookups(self, request, model_admin):
#         lookup_list = sorted(NATIONAL_CONFERENCES, reverse=True)
#         index_of_default = [y[0] for y in lookup_list].index(self.default_choice[0])
#         lookup_list[index_of_default] = (None, self.default_choice[1])
#         return lookup_list

#     def choices(self, cl):
#         for lookup, title in self.lookup_choices:
#             yield {
#                 'selected': self.value() == lookup,
#                 'query_string': cl.get_query_string({
#                     self.parameter_name: lookup,
#                 }, []),
#                 'display': title,
#             }

#     def queryset(self, request, queryset):
#         if self.value() is None: # default to most recent conference
#             return queryset.filter(event__code=self.default_choice[0])
#         else:
#             return queryset.filter(event__code=self.value())

# # THESE FILTERS ARE REPEATED A FEW TIMES, USE ONE CLASS, OR inherit
# class NationalConferenceAttendeeClassFilter(admin.SimpleListFilter):

#     title = 'Attendee Registrant Class'
#     parameter_name = 'registrant_class'
#     default_choice = 'ALL'

#     def lookups(self, request, model_admin):
#         return [
#             ('ALL', 'All Registrations'),
#             ('ALL-BSPKR', 'All except BSPKR'),
#             ('BSPKR', 'BSPKR Only'),
#             ]

#     def choices(self, cl):
#         for lookup, title in self.lookup_choices:
#             yield {
#                 'selected': self.value() == lookup,
#                 'query_string': cl.get_query_string({
#                     self.parameter_name: lookup,
#                 }, []),
#                 'display': title,
#             }

#     def queryset(self, request, queryset):
#         if self.value() == "ALL-BSPKR":
#             return queryset.exclude(purchase__product_price__imis_reg_class="BSPKR")
#         elif self.value() == "BSPKR":
#             return queryset.filter(purchase__product_price__imis_reg_class="BSPKR")
#         else:
#             return queryset # default to most recent conference

# class NationalConferenceAttendeeAdmin(AttendeeAdmin):

#     list_display = ["id", "get_event_master_id", "get_event_code", "event", "get_event_begin_time", "get_username", "contact", "get_single_purchase_amount", "status","get_purchase_submitted_time","get_member_type", "get_last_name", "get_first_name"]
#     list_filter = [DefaultActiveStatusFilter, NationalConferenceAttendeeFilter, NationalConferenceAttendeeClassFilter, "purchase__submitted_time"]

#     list_per_page = 200

#     actions = ["print_tickets", "print_address_labels"]
#     ordering = ("contact__last_name", "contact__first_name")

#     def print_tickets(self, request, queryset):
#         """
#         NOTE: ticket printing only works for the current conference. If for some odd reason we try to print tickets from previous conferences,
#         (or if we have future conferences included in the NATIONAL_CONFERENCES variable), then activity tickets will not print
#         """
#         pdf_output = ConferenceKioskTicketGenerator().generate_tickets(
#             full_attendee_ids=[a.id for a in queryset],
#             conference_master_id=EventMulti.objects.get(code=NATIONAL_CONFERENCE_ADMIN[0], publish_status="PUBLISHED").master_id)

#         response = HttpResponse(pdf_output, content_type='application/pdf')
#         response['Content-Disposition'] = 'attachment; filename="conference-tickets.pdf"'

#         return response
#     print_tickets.short_description = "Quick Print"

#     def print_address_labels(self, request, queryset):
#         pickled_query = pickle.dumps(queryset.query, 0).decode()
#         task_result = create_attendee_address_labels_pdf.apply_async(kwargs=dict(
#             pickled_query=pickled_query))
#         context = dict(success=True, task_id=task_result.task_id)
#         return JsonResponse(context)

#     class Media:
#         js = (
#             "//ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js",
#             "/static/registrations/js/admin.js"
#         )


# admin.site.register(Attendee, AttendeeAdmin)
# admin.site.register(NationalConferenceAttendee, NationalConferenceAttendeeAdmin)
