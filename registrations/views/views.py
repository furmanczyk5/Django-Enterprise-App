import json

from celery.result import AsyncResult
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, TemplateView, View

from conference.models import Microsite
from content.models import MenuItem
from events.models import Event, EventMulti, Activity, NATIONAL_CONFERENCES
from imis.models import CustomEventRegistration

from myapa.viewmixins import AuthenticateLoginMixin, AuthenticateWebUserGroupMixin
from planning.s3utils import read_string_from_s3_file
# TO DO: shouldn't have to import Product once refactor complete
from store.models import Order, ProductCart, Purchase, Payment
from ..forms import CustomTicketPrintingForm
from ..models import Attendee
from ..tickets import ConferenceKioskTicketGenerator, ConferenceCustomTicketGenerator, \
    TicketPdfGenerator, default_page_options
from ..utils import poll_task_progress


def registration_redirect(request, **kwargs):
    event = Event.objects.get(pk=kwargs['event_id'])
    event_master_id = event.master_id
    return redirect("/events/eventsingle/" + str(event_master_id) + "/")


class RedirectOldRegistrationLinksView(View):

    def get(self, request, *args, **kwargs):
        event_id = kwargs.get("event_id")
        event = Event.objects.get(id=event_id)
        model_name = event.get_proxymodel_class()._meta.model_name
        master_id = event.master_id

        return redirect("/events/{0}/{1}/".format(model_name, master_id))


class AdminCancelAttendeeView(AuthenticateLoginMixin, View):

    def get(self, request, *args, **kwargs):

        if request.user.is_staff:
            attendee_id = kwargs['attendee_id']
            event_id = kwargs['event_id']
            attendee = Attendee.objects.get(id=attendee_id)

            event_attendee_qset = Attendee.objects.filter(id=attendee_id, event__id=event_id)
            if event_attendee_qset:
                event_attendee = event_attendee_qset[0]
                event_attendee.status = "CA"
                event_attendee.save()
                activity_attendance_qset = event_attendee.activity_attendance().filter(purchase__isnull=False)
                activity_attendance_qset.update(status="CA")

                event_purchase_qset = Purchase.objects.filter(contact__user_id=attendee.contact.user_id,
                                                              product__content__id=event_id)

                event_purchase_qset.update(status="CA")

                user = event_attendee.contact.user

                order = Order.objects.create(user=user, is_manual=True, submitted_user_id=request.user.username,
                                             submitted_time=timezone.now())
                order.process()
                for activity_attendee in activity_attendance_qset:
                    activity_price = activity_attendee.purchase.product_price
                    activity_quantity = activity_attendee.purchase.quantity * -1
                    event_purchase = Purchase.objects.create(user=user, contact=event_attendee.contact, order=order,
                                                             product=activity_attendee.purchase.product,
                                                             product_price=activity_price,
                                                             quantity=activity_quantity, amount=activity_price.price,
                                                             submitted_product_price_amount=activity_price.price)
                    event_purchase.process()

                event_cancel_fee = ProductCart.objects.get(code="EVENT_NATIONAL_CANCELLATION_FEE")
                event_cancel_fee_purcahse = Purchase.objects.create(user=user, contact=event_attendee.contact,
                                                                    order=order, product=event_cancel_fee,
                                                                    product_price=event_cancel_fee.get_price(),
                                                                    amount=event_cancel_fee.get_price().price,
                                                                    submitted_product_price_amount=event_cancel_fee.get_price().price)
                event_cancel_fee_purcahse.process()

                event_attendee.save()

                messages.success(request, 'Attendee status successfully changed to CANCELLED')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            else:
                messages.error(request, 'Attendee status could not be CANCELLED')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class RefundCancelAttendeeView(AuthenticateLoginMixin, View):

    def get(self, request, *args, **kwargs):
        event_id = kwargs.get('event_id')
        attendee_id = kwargs.get('attendee_id')

        attendee = Attendee.objects.get(event__id=event_id, id=attendee_id)
        if attendee:
            attendee.status = 'CA'
            user = User.objects.get(username=attendee.contact.user.username)

            order = Order.objects.create(user=user, is_manual=True, submitted_user_id=request.user.username,
                                         submitted_time=timezone.now())
            refund_price = attendee.purchase.product_price
            refund_purchase = Purchase.objects.create(user=user, order=order, product=attendee.purchase.product,
                                                      product_price=refund_price,
                                                      quantity=-1, amount=refund_price.price,
                                                      submitted_product_price_amount=refund_price.price)
            refund_purchase.process()
            attendee.save()

            # TO DO.. Automatically process the refund

            messages.success(request,
                             'Attendee status for the specific Event/Activity is successfully changed to CANCELLED')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    def render_template(self, request):
        return render(request, self.template_name, self.context)


class RefundAttendeeView(AuthenticateLoginMixin, View):
    """
    This is used for the 2018 APA National Conference
    """

    def get(self, request, *args, **kwargs):

        attendee_id = kwargs.get("attendee_id")
        cancellation_fee = request.GET.get("cancellation_fee", None)
        refund_type = request.GET.get("refund_type", None)
        adjustment = request.GET.get("adjustment", None)

        event_type = None
        attendee = Attendee.objects.get(id=attendee_id)

        order_overview = attendee.order_overview()
        total_purchases = order_overview[0]
        total_payments = order_overview[1]

        member_type = attendee.contact.member_type

        if attendee.purchase:

            attendee.status = "R"

            attendee.save()
            event_type = attendee.event.event_type

            order = Order.objects.create(user=attendee.contact.user, is_manual=True,
                                         submitted_user_id=request.user.username, submitted_time=timezone.now(),
                                         order_status="SUBMITTED")

            # get all activities associated with the event about to be refunded. we will need to cancel them
            if event_type in ("EVENT_SINGLE", "EVENT_MULTI") and not adjustment:
                all_event_related_purchases = Attendee.objects.filter(contact=attendee.contact,
                                                                      event__parent=attendee.event.master)

                for attendee_activity in all_event_related_purchases:
                    purchase = attendee_activity.purchase

                    if purchase and purchase.status == "A":
                        refund_price = attendee_activity.purchase.product_price
                        refund_amount = (attendee_activity.purchase.amount / attendee_activity.purchase.quantity)
                        refund_purchase = Purchase.objects.create(status="A", user=attendee.contact.user,
                                                                  contact=attendee.contact, order=order,
                                                                  product=attendee_activity.purchase.product,
                                                                  product_price=refund_price,
                                                                  quantity=-1, amount=refund_amount,
                                                                  submitted_product_price_amount=refund_amount,
                                                                  submitted_time=timezone.now())
                        refund_purchase.update_attendees()

                    else:
                        # delete purchases in the user's shopping cart
                        if attendee_activity.purchase:
                            attendee_activity.purchase.delete()

                        # delete items in the user's schedule
                        else:
                            attendee_activity.delete()

            elif event_type == "ACTIVITY":
                purchase = attendee.purchase
                if purchase:
                    total_payments = attendee.purchase.submitted_product_price_amount

            # refunds the event or activity

            if attendee.purchase:
                refund_price = attendee.purchase.product_price
                refund_amount = (attendee.purchase.amount / attendee.purchase.quantity)
                refund_purchase = Purchase.objects.create(status="A", user=attendee.contact.user,
                                                          contact=attendee.contact, order=order,
                                                          product=attendee.purchase.product, product_price=refund_price,
                                                          option=attendee.purchase.option,
                                                          quantity=-1, amount=refund_amount,
                                                          submitted_product_price_amount=refund_amount,
                                                          submitted_time=timezone.now())

            # hard coded for NPC cancellations. We should use the code in product for the main event to find cancellation / process fees!!
            ##############################################################################################################################
            if cancellation_fee:
                # TO DO: WTF hard-coded product code for NPC18!!!
                cancellation_product = ProductCart.objects.get(imis_code="18CONF/NPC185556", status="A")

                if member_type == "STU":
                    cancellation_amount = 35
                else:
                    cancellation_amount = cancellation_product.prices.all()[0].price

                cancel_purchase = Purchase.objects.create(status="A", user=attendee.contact.user, order=order,
                                                          product=cancellation_product,
                                                          product_price=cancellation_product.prices.all()[0],
                                                          quantity=1, amount=cancellation_amount,
                                                          submitted_product_price_amount=cancellation_amount)

                # remove cancellation fee from the payments calculated
                total_payments -= cancellation_amount
            ###############################################################################################################################

            if not adjustment:
                Payment.objects.create(status="A", user=attendee.contact.user, order=order, amount=total_payments,
                                       contact=attendee.contact, submitted_time=timezone.now(), method=refund_type)

        else:
            pass
        messages.success(request, 'Event or activity registration(s) have been refunded or cancelled.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    def render_template(self, request):
        return render(request, self.template_name, self.context)


class KioskTicketPrintingView(AuthenticateWebUserGroupMixin, TemplateView):
    """
    Class based view for printing tickets as they are purchased
    """
    template_name = "registrations/kiosk/admin/ticket-printing.html"
    authenticate_groups = ["staff", "onsite-conference-admin", "reg-temp"]

    def get(self, request, *args, **kwargs):

        self.master_id = kwargs.get("master_id")

        self.ticket_purchases = Purchase.objects.select_related(
            'product',
            'product__content',
            'user',
            'user__contact',
            'order'
        ).filter(
            Q(product__content__parent__id=self.master_id)
            | Q(product__content__master_id=self.master_id),
            product__product_type__in=("ACTIVITY_TICKET", "EVENT_REGISTRATION"),
            status='A',
            order__isnull=False,
        ).order_by(
            '-order__submitted_time'
        )

        return super().get(request, *args, **kwargs)

    def attendee_set_print_type(self, attendee):

        if not attendee["is_reprint"] and attendee["orders"]:

            payments = attendee["orders"][0].payment_set.all()

            if payments and payments[0].method == "CHECK":
                attendee["check_payment"] = attendee["orders"][0].purchase_total()
            else:
                attendee["check_payment"] = None
            # except:
            #     attendee["check_payment"] = None

        if attendee["registration"]:
            print_type = "FULL"
        else:
            print_type = "TICS"
        attendee["print_type"] = print_type
        return print_type

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["master_id"] = self.master_id
        context["ticket_purchases"] = self.ticket_purchases
        context["event_code"] = "21CONF"  # FIXME Hardcoding
        context["imis_staff_site"] = getattr(settings, "IMIS_STAFF_SITE", "https://staffdev.planning.org")
        return context


class KioskTicketPrintingAttendeesRefreshView(KioskTicketPrintingView):
    template_name = "registrations/kiosk/admin/ticket-printing-attendees.html"


class kioskAdminDismissAttendees(AuthenticateWebUserGroupMixin, View):
    authenticate_groups = ["staff", "onsite-conference-admin"]

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        attendee_codes = request.POST.getlist("print_code")
        attendee_ids = [a.split(".")[1] for a_list in attendee_codes for a in a_list.split(",")]

        Attendee.objects.filter(contact__attending__id__in=attendee_ids).update(ready_to_print=False)

        return HttpResponse(json.dumps({"got_it": True}, cls=DjangoJSONEncoder), content_type='application/json')


class KioskAdminPrintTickets(AuthenticateWebUserGroupMixin, View):
    authenticate_groups = ["staff", "onsite-conference-admin"]

    def get(self, request, *args, **kwargs):
        attendee_codes = request.GET.getlist("print_code")

        full_attendee_ids = [a.split(".")[1] for a in attendee_codes if a.startswith("FULL.")]
        tickets_attendee_ids = [a.split(".")[1] for a_list in attendee_codes for a in a_list.split(",") if
                                a_list.startswith("TICS.")]

        pdf_output = ConferenceKioskTicketGenerator().generate_tickets(
            full_attendee_ids=full_attendee_ids,
            ticketonly_attendee_ids=tickets_attendee_ids,
            conference_master_id=kwargs.get("master_id", None))

        response = HttpResponse(pdf_output, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="conference-tickets.pdf"'

        return response


class CustomTicketPrintingFormView(AuthenticateWebUserGroupMixin, FormView):
    """
    Staff Admin view for printing adhoc tickets on the fly at NPC
    """
    template_name = "admin/registrations/attendee/print-custom-ticket.html"
    form_class = CustomTicketPrintingForm
    authenticate_groups = ["onsite-conference-admin", "staff-store-admin"]

    def get_badge_context(self, data):
        return {
            "ticket_template": data.get("ticket_template"),
            "attendee": {
                "badge_name": data.get("badge_name"),
                "badge_company": data.get("badge_company"),
                "badge_location": data.get("badge_location"),
                "get_member_type_friendly": data.get("badge_membertype"),
                "contact": {
                    "full_title": data.get("badge_fullname"),
                    "company": data.get("badge_company"),
                    "user": {
                        "username": data.get("badge_userid")
                    }
                }
            },
            "purchase": {
                "product_price": {
                    "imis_reg_class": data.get("badge_regclass")
                }
            }
        }

    def get_session_context(self, data):
        context = {
            "ticket_template": data.get("ticket_template"),
            "attendee": {
                "is_standby": data.get("session_standby"),
            },
            "event": {
                "code": data.get("session_code"),
                "title": data.get("session_title"),
                "begin_time": data.get("session_begintime"),
                "contenttagtype_room": [{
                    "tags": {
                        "all": [{
                            "title": data.get("session_location")
                        }]
                    }
                }]
            },
            "purchase": {
                "product_price": {
                    "price": data.get("session_price")
                },
                "product": {
                    "description": data.get("session_description")
                }
            }
        }
        context.update(self.get_nonbadge_context(data))
        return context

    def get_nonbadge_context(self, data):
        return {
            "ticket_template": data.get("ticket_template"),
            "multipart_attendee": {
                "contact": {
                    "full_title": data.get("nonbadge_fullname"),
                    "member_type": data.get("nonbadge_membertype"),
                    "user": {
                        "username": data.get("nonbadge_userid"),
                    }
                },
                "purchase": {
                    "product_price": {
                        "imis_reg_class": data.get("nonbadge_regclass")
                    }
                }
            }
        }

    def form_valid(self, form):

        data = form.cleaned_data

        if data.get("ticket_template") == "registrations/tickets/layouts/CONFERENCE-BADGE.html":
            ticket_context = self.get_badge_context(data)
        elif data.get("ticket_template") == "registrations/tickets/layouts/CONFERENCE-ACTIVITY.html":
            ticket_context = self.get_session_context(data)
        else:
            ticket_context = self.get_nonbadge_context(data)

        pdf_output = ConferenceCustomTicketGenerator().generate_tickets(
            custom_tickets=[ticket_context]
        )

        response = HttpResponse(pdf_output, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="conference-tickets.pdf"'

        return response


class PollTaskProgressView(AuthenticateWebUserGroupMixin, View):
    authenticate_groups = ["staff-store-admin"]

    def get(self, request, *args, **kwargs):
        task_id = request.GET.get("task_id", None)
        context = poll_task_progress(task_id)
        return JsonResponse(context)


class RevokeTaskView(AuthenticateWebUserGroupMixin, View):
    authenticate_groups = ["staff-store-admin"]

    def get(self, request, *args, **kwargs):
        task_id = request.GET.get("task_id")
        task = AsyncResult(task_id)
        task.revoke(terminate=True)
        context = dict(success=True, task_id=task_id)
        return JsonResponse(context)


class GetTaskPdfResult(AuthenticateWebUserGroupMixin, View):
    """ returns the pdf result, from amazon s3, for the given task """

    authenticate_groups = ["staff-store-admin"]

    def get(self, request, *args, **kwargs):
        task_id = request.GET.get("task_id")
        task = AsyncResult(task_id)  # terminate=True will cancel already running tasks

        ticket_pdf = read_string_from_s3_file(task.result)
        response = HttpResponse(ticket_pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="conference-tickets.pdf"'
        return response


class GetTaskResult(AuthenticateWebUserGroupMixin, View):
    """Returns the result of the given celery task"""

    authenticate_groups = ["staff-store-admin"]

    def get(self, request, *args, **kwargs):
        task_id = request.GET.get("task_id")
        task = AsyncResult(task_id)  # terminate=True will cancel already running tasks
        context = dict(task_id=task_id, result=task.result)
        return JsonResponse(context)


class PreviewMyBadgeAndTicketsView(AuthenticateLoginMixin, View):

    def get(self, request, *args, **kwargs):
        master_id = kwargs.get("master_id")
        paper_size = kwargs.get("paper_size", "sato")
        default_options = default_page_options.get(paper_size, {})
        queryset = Attendee.objects.filter(
            status__in=["A", "H"],
            contact=request.user.contact,
            event__master_id=master_id)

        if not queryset.exists():
            raise Http404

        pdf_output = TicketPdfGenerator(
            paper_size=paper_size,
            num_receipts=1,
            page_margin_top=default_options.get("page_margin_top", 0.0),
            page_margin_bottom=default_options.get("page_margin_bottom", 0.0),
            page_margin_left=default_options.get("page_margin_left", 0.0),
            page_margin_right=default_options.get("page_margin_right", 0.0)
        ).generate_tickets(query=queryset)

        response = HttpResponse(pdf_output, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="conference-tickets.pdf"'

        return response


def event_registration_sync(request):
    """
    Syncs registration information for a given user id and event code.
    """

    user_id = request.GET.get("UserID")

    # issue passing static event code with iMIS. Hard coding for now.
    event_code = "21CONF"

    CustomEventRegistration.sync_registration(user_id, event_code)

    messages.success(request, "{0} registration has been synced for user id: {1}".format(event_code, user_id))

    return redirect('/admin/')
