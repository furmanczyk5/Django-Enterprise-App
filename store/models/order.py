import datetime
import traceback

import pyodbc
import pytz
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models
from django.db.models import Q
from django.utils import timezone
from sentry_sdk import capture_exception

from content.mail import Mail
from cm.credly_api_utils import CredlyAPICaller
from imis.models import Name, IndDemographics, Subscriptions, Activity as ImisActivity, Advocacy, CustomDegree
from learn.utils.wcw_api_utils import WCWContactSync
from myapa.models import Contact, ContactRelationship
from planning.settings import STORE_STAFF
from store.models import Payment
from store.utils import PurchaseInfo
from .purchase import Purchase
from .settings import PAYMENT_METHODS, ORDER_STATUS, PRODUCT_TYPE_PRIORITY


class Order(models.Model):
    """
    represents an order that a user submitted through the store checkout process
    """

    # NOTE.. in general ALL orders require a user...
    # however we still need to keep historical data around even if user records merged/deleted, so making this optional

    legacy_id = models.IntegerField(null=True, blank=True)

    user = models.ForeignKey(User, related_name="orders", null=True, blank=True, on_delete=models.SET_NULL)
    expected_payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS, blank=True, null=True)
    # TO DO ... foreign key to contact INSTEAD of user...

    # we also store the user's iMIS id here for historical record keeping (in case user record is merged/deleted).
    # This is the same as as the user.username at the time of the order submission
    submitted_user_id = models.CharField(max_length=10, help_text="Contact's Imis Id")

    # set as true of order submitted by an admin (as opposed to the user)
    is_manual = models.BooleanField(default=False, verbose_name="Is Manual Order")

    submitted_time = models.DateTimeField()
    # more attribute/field definitions needed...?

    # default to NOT_SUBMITTED
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS, null=False, blank=False, default='NOT_SUBMITTED')

    # imis fields to be populated once line item is synced with iMIS:
    imis_trans_number = models.IntegerField(null=True, blank=True)
    imis_batch = models.CharField(max_length=50, null=True, blank=True)
    imis_batch_time = models.DateField(null=True, blank=True)

    def add_from_cart(self, user):
        """
        ties all cart purchases/payments to this order also processes them
        """

        company = ContactRelationship.get_company_contact(user=user)
        if company:
            purchases = Purchase.objects.filter(Q(user = user) | Q(contact = company), order__isnull=True)
        else:
            purchases = Purchase.objects.filter(user = user, order__isnull=True)

        for purchase in purchases:

            purchase.order = self
            purchase.save()

    def get_purchases(self):
        """
        returns all purchases for the order
        """

        purchases = sorted(Purchase.objects.filter(order = self), key = lambda p: PRODUCT_TYPE_PRIORITY.index(p.product.product_type))

        return purchases

    def process(self, submit_to_imis=True):
        """
        processes all purchases and payments tied to this order
        """
        batch_source_code = "CART"

        # self.add_comped_purchases()

        self.order_status="SUBMITTED"
        if not self.submitted_time:
            self.submitted_time=timezone.now()
        self.save()


        # Django admin order. Special batches assigned for these orders
        # ONLY 1 PAYMENT PER ORDER
        if self.is_manual:
            submitter = Contact.objects.get(user__username=self.submitted_user_id)
            if submitter.member_type == "STF":
                if self.payment_set.all()[0].amount >= 0:
                    batch_source_code = "STAFF"
                else:
                    batch_source_code = "STAFF_REFUND"
            else:
                batch_source_code = "CHAPTER_ADMIN"

        # TO DO... shouldn't repeat this here and in in the sync util
        # ... refactor
        purchases = self.purchase_set.all()

        from exam.open_water_api_utils import OPEN_WATER_DETAILS_TO_PRODUCT_CODE
        if settings.ENVIRONMENT_NAME != 'PROD':
            test_dict = OPEN_WATER_DETAILS_TO_PRODUCT_CODE.get('test_instance') or {}
            open_water_product_codes = list(test_dict.values())
        else:
            aicp_dict = OPEN_WATER_DETAILS_TO_PRODUCT_CODE.get('aicp_instance') or {}
            # FOR AWARDS LAUNCH WE WILL NEED TO INCORPORATE THE OW AWARDS INSTANCE HERE AS WELL
            # awards_dict = OPEN_WATER_DETAILS_TO_PRODUCT_CODE.get('awards_instance') or {}
            open_water_product_codes = list(aicp_dict.values())# + list(awards_dict.values())

        open_water_purchases = [p for p in purchases if p.product.imis_code in open_water_product_codes]
        if open_water_purchases:
            batch_source_code = "OPEN_WATER"

        # SENDS ORDER TO iMIS VIA PYODBC
        if submit_to_imis:
            self.submit_to_imis(batch_source_code=batch_source_code)

        learn_purchases = [p for p in purchases if p.product.product_type=="LEARN_COURSE"]

        try:
            if learn_purchases:
                wcw_contact_sync = WCWContactSync(self.user.contact)
                wcw_contact_sync.post_order_to_wcw(self)

                for p in learn_purchases:
                    if p.product.content.event.digital_product_url:
                        setattr(p, "url", p.product.content.event.digital_product_url)
                    else:
                        setattr(p, "url", "https://%s/local/catalog/view/product.php?globalid=%s" % (settings.LEARN_DOMAIN, p.product.code))

                mail_context = dict(
                    contact=self.user.contact,
                    order=self,
                    learn_purchases = learn_purchases
                )

                Mail.send(mail_code="LEARN_ORDER_INFO", mail_to=self.user.contact.email, mail_context=mail_context)

        except Exception as e:
            capture_exception(e)
            stack_trace = traceback.format_exc()
            try:
                subject = "THERE WAS ERROR WRITING APA LEARN ORDER TO WCW - app: store | model: purchase | method: process.  user id: {0} | order id: {1}".format(self.user.username, self.id)
                mail_body = "There was an error running purchase.process() <br/><br/>"
                mail_body += "user id: {0} | order id: {1} ".format(self.user.username, self.id)
                mail_body +="<br/><br/>"
                mail_body += "<br/>Exception: <br/>"
                mail_body += str(e)
                mail_body +="<br/><br/>"
                mail_body += stack_trace
            except:
                subject="STORE CHECKOUT ERROR"
                mail_body = str(e)
                mail_body +="<br/><br/>"
                mail_body += stack_trace
                print(str(stack_trace))
            send_mail(subject, mail_body, 'store@planning.org', ["rwest@planning.org","akrakos@planning.org", "bmissaggia@planning.org"], fail_silently=True, html_message=mail_body)

        if self.order_status != "SUBMITTED_FAILED":
            credly_purchases = [p for p in purchases if p.product.imis_code=="AICP_PRORATE"]
            try:
                if credly_purchases:
                    cr = CredlyAPICaller()
                    cr.credly_initial_dues_sync(self.user.username)
            except Exception as e:
                capture_exception(e)
                stack_trace = traceback.format_exc()
                try:
                    subject = "THERE WAS ERROR SYNCING DESIGNATION TO CREDLY - app: store | model: purchase | method: process.  user id: {0} | order id: {1}".format(self.user.username, self.id)
                    mail_body = "There was an error running purchase.process() <br/><br/>"
                    mail_body += "user id: {0} | order id: {1} ".format(self.user.username, self.id)
                    mail_body +="<br/><br/>"
                    mail_body += "<br/>Exception: <br/>"
                    mail_body += str(e)
                    mail_body +="<br/><br/>"
                    mail_body += stack_trace
                except:
                    subject="STORE CHECKOUT ERROR"
                    mail_body = str(e)
                    mail_body +="<br/><br/>"
                    mail_body += stack_trace
                    print(str(stack_trace))
                send_mail(subject, mail_body, 'store@planning.org', ["tjohnson@planning.org","akrakos@planning.org"], fail_silently=True, html_message=mail_body)

    def purchase_total(self):
        # just sum up the purchase amounts...
        ret_total = 0
        for purchase in self.purchase_set.all():
            ret_total += (purchase.submitted_product_price_amount * purchase.quantity)
        return float("{0:.2f}".format(ret_total))

    def payment_total(self):
        ret_total = 0
        for payment in self.payment_set.all():
            #if payment.status == "A":
            if payment.method in ('CHECK_REFUND','CC_REFUND'):
                ret_total -= (payment.amount)
            else:
                ret_total += (payment.amount)
        return float("{0:.2f}".format(ret_total))

    def purchase_pending_total(self):
        # just sum up the purchase amounts...
        ret_total = 0
        for purchase in self.purchase_set.filter(status="P"):
            ret_total += (purchase.submitted_product_price_amount * purchase.quantity)
        return float("{0:.2f}".format(ret_total))

    def payment_pending_total(self):
        ret_total = 0
        for payment in self.payment_set.filter(status="P"):
            ret_total += (payment.amount)
        return float("{0:.2f}".format(ret_total))

    def purchase_active_total(self):
        ret_total = 0
        for purchase in self.purchase_set.filter(status="A"):
            ret_total += (purchase.submitted_product_price_amount * purchase.quantity)
        return float("{0:.2f}".format(ret_total))

    def balance(self):
        return self.payment_total() - self.purchase_total()

    def get_payment(self):
        return Payment.objects.filter(order=self)

    def send_confirmation(self, recurring=False):
        # order mail confirmation sent for all store orders
        try:
            mail_context = {'order': self, 'payment': "{0:.2f}".format(self.payment_total()), 'recurring': recurring}

            Mail.send(mail_code="STORE_CONFIRMATION", mail_to=self.user.email, mail_context=mail_context)
        except Exception as e:
            capture_exception(e)


    def send_admin_confirmation(self, email=None):
        # emails a different order confirmation used by conf. chapter admins
        mail_context = {}
        mail_context["order"] = self
        mail_context["purchase_total"] = "{0:.2f}".format(self.purchase_active_total())
        mail_context["purchases"] = self.purchase_set.filter(status__in=("A","R","C"))
        mail_context["payments"] = self.payment_set.all().exclude(method="NONE")
        mail_context["balance"] = "{0:.2f}".format(abs(self.purchase_active_total() - self.payment_total()))
        mail_context["payment_total"] = "{0:.2f}".format(self.payment_total())
        if not email:
            email = self.user.email

        Mail.send(mail_code="STORE_ADMIN_ORDER_CONFIRMATION", mail_to=email, mail_context=mail_context)

    def __str__(self):
       return str(str(self.user) + ' | ' + 'Order Number: ' + str(self.id))

    @staticmethod
    def autocomplete_search_fields():
        return ("user__username__iexact",)


    def submit_to_imis(self, batch_source_code):
        """
        SUBMIT DJANGO ORDER TO IMIS
        NOTE: TABLE VALUED PARAMETERS DON'T APPEAR TO BE SUPPORTED YET, SO WE DECLARE A TABLE AND BUILD IT MANUALLY
        https://github.com/mkleehammer/pyodbc/issues/290
        """

        # PYODBC CONNECTION
        mssql = getattr(settings, "DATABASES").get("MSSQL")
        connection_string = ('DRIVER={0};SERVER={1};PORT={2};DATABASE=imis_live;UID={3};PWD={4};TDS_Version=7.4').format("{FreeTDS}",mssql.get("HOST"),mssql.get("PORT"),mssql.get("USER"), mssql.get("PASSWORD"))
        cnxn = pyodbc.connect(connection_string, autocommit=True)
        # DECLARE TABLE TYPE
        sql_query = "SET NOCOUNT ON; DECLARE @ImisResponse VARCHAR(200); DECLARE @DjangoPurchases AS DjangoPurchasesTable; INSERT INTO @DjangoPurchases(ProductCode, ProductOption, RegistrantClass, Quantity, Price, AgreementResponse1, AgreementResponse2, AgreementResponse3) VALUES "

        django_purchases = []

        # LOOP THROUGH PURCHASES TO POPULATE THE TABLE WITH VALUES
        for x in self.get_purchases():

            # NOT SURE HOW TO USE OPTIONS IN IMIS FOR EVENT REGISTRATIONS. MIGHT NEED TO ALSO PASS IN REG CLASS

            # POSSIBLY: REMOVE OPTION FROM BEING PASSED TO THE STORED PROCEDURE

            imis_code = "" if x.product.imis_code is None else x.product.imis_code

            option = ""

            # WILL COMBINE PRODUCT IMIS CODE + OPTION CODE TO GET IMIS CODE FOR EVEN REGISTRATIONS
            if x.product.product_type == "EVENT_REGISTRATION":
                if x.option:
                    imis_code = x.product.imis_code + "/" + x.option.code

            imis_reg_class = '' if not x.product_price.imis_reg_class else x.product_price.imis_reg_class

            django_purchases.append((imis_code, option, imis_reg_class, str(x.quantity), str(x.submitted_product_price_amount), x.agreement_response_1 * 1, x.agreement_response_2 * 1, x.agreement_response_3 * 1))


        # ADD PURCHASES TO SQL QUERY
        for purchase in django_purchases[:-1]:
            sql_query += str(purchase) + ","
        else:
            sql_query += str(django_purchases[-1]) + ";"


        # get payment for pn_ref and payment method
        payment = self.payment_set.all()[0]
        payment_method = payment.method

        # change the payment method for refunds
        # note: I don't believe we do this anymore. could probably get rid fo this
        if payment_method == "CC_REFUND":
            payment_method = "CC"
        elif payment_method in  ("CHECK","CHECK_REFUND"):
            payment_method = "[CHECK]"

        # NOTE: IS CHAPTER ADMIN IS NOT BEING CHECKED! ADD LATER.
        sql_query += "EXEC django_cart_submit @WebUserID={0}, @PaymentMethod={1}, @PaymentAmount={2}, @PNRef={3}, @BatchSourceCode={4}, @DjangoPurchases=@DjangoPurchases".format(self.user.username, payment_method, self.payment_total(), payment.pn_ref, batch_source_code)

        print("sql_query: " + sql_query)

        cursor = cnxn.cursor()

        # ATTEMPT TO WRITE TO IMIS
        try:
            # imis_response could be trans numbers if we want to link transactions
            imis_response = cursor.execute(sql_query).fetchall()

            # response returns list of purchases
            # example: [('FR', 'COMMUNITY', 3090995, '_WB190724', datetime.datetime(2019, 7, 24, 12, 52, 37, 113000))]

            for x in imis_response:

                # only write the iMIS transaction information if 5 items are returned, and the values returned are valid
                if len(x) == 5 and isinstance(x[0], str) and isinstance(x[1], str) and isinstance(x[2],int) and isinstance(x[3], str) and isinstance(x[4], datetime.datetime):

                    # get the purchase id of the first imis code in the list
                    purchase = self.purchase_set.filter(product__imis_code=x[1]).first()

                    # if no purchase found that matches the iMIS code, assume this is an event registration since this is the only case where the iMIS code will not match
                    if purchase is None and x[0] == "MEETING":
                        option_code = x[1].split("/",1)[1]
                        imis_code = x[1].split("/",1)[0]
                        purchase = self.purchase_set.filter(product__imis_code=imis_code, option__code=option_code).first()

                    if purchase:
                        purchase_id = purchase.id

                        # update django to write trans number, batch, and batch date
                        Purchase.objects.filter(id=purchase_id).update(imis_trans_number=x[2], imis_batch=x[3], imis_batch_date=x[4])


                # FAILED TO WRITE TO IMIS. PROCESS IN DJANGO AS NORMAL, BUT ALERT STAFF OF THE ERROR.
        except Exception as e:

            # NEW ORDER STATUS TO MEMBERSHIP CAN QUICKLY FIND FAILED ORDERS
            self.order_status="SUBMITTED_FAILED"
            self.save()

            # EMAIL MEMBERSHIP
            subject = "({}) Order failed writing to iMIS. Django order number: ".format(
                settings.ENVIRONMENT_NAME,
                self.id
            )
            mail_body = """<br/>Order Number: {0} <br/>
                            <br/>WebUserID: {1}<br/>
                            <br/>Error Message: {2}<br/>
                            <br/>SQL query: {3}<br />
            """.format(str(self.id), self.user.username, str(e), sql_query)
            send_mail(subject, mail_body, 'it@planning.org', STORE_STAFF, fail_silently=True, html_message=mail_body)


        cursor.close()
        del cursor
        cnxn.close()
