from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError
from django.forms import NumberInput
from django.forms.widgets import RadioSelect
from django.utils.translation import ugettext_lazy as _

from content.forms import StateCountryModelFormMixin, AddFormControlClassMixin
from myapa.models.contact import Contact
from myapa.models.proxies import Organization
from store.models import ProductOption, ProductCart, Purchase


class ModelChoiceField_w_LabelDictionary(forms.ModelChoiceField):
    """
    ModelChoiceField with extra kwarg "label_dict" (id keys matching to label values)
    """
    def __init__(self, *args, **kwargs):
        self.label_dict= kwargs.pop("label_dict",{})
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        return self.label_dict.get(obj.id, None) or super().label_from_instance()


class RegistrationOptionForm(forms.Form):

    def __init__(self, choices, *args, **kwargs):
        super(RegistrationOptionForm, self).__init__(*args, **kwargs)
        self.fields['registration_option'] = forms.ChoiceField(
            widget=RadioSelect,
            choices=choices
        )


class EventQuestionsForm(forms.Form):

    def __init__(self, product, *args, **kwargs):
        super(EventQuestionsForm, self).__init__(*args, **kwargs)

        if product.question_1 != '':
            self.fields['question_1'] = forms.CharField(label=product.question_1, required=False)

        if product.question_2 != '':
            self.fields['question_2'] = forms.CharField(label=product.question_2, required=False)

        if product.question_3 != '':
            self.fields['question_3'] = forms.CharField(label=product.question_3, required=False)

        if product.agreement_statement_1 != '':
            self.fields['agreement_statement_1'] = forms.BooleanField(label=product.agreement_statement_1, required=False)

        if product.agreement_statement_2 != '':
            self.fields['agreement_statement_2'] = forms.BooleanField(label=product.agreement_statement_2, required=False)

        if product.agreement_statement_3 != '':
            self.fields['agreement_statement_3'] = forms.BooleanField(label=product.agreement_statement_3, required=False)


class EventSessionsForm(forms.Form):

    def __init__(self, user, event, option, *args, **kwargs):
        super().__init__(*args, label_suffix="", **kwargs)
        for activity in event.master.children.filter(
            event__event_type='ACTIVITY').order_by('event__begin_time'):
            # Create an IntegerField with the field name in the form of "session_x"
            # Where x is the id of the ProductPrice object

            # What happens if every activity does not have a product?
            # Can an activity with no product be accidentally be created in the admin?

            # What variables correspond to the the fields in the product price view?

            try:
                price = activity.product.get_price(user, option)
            except ObjectDoesNotExist:
                price = None

            if price is not None:
                product_price = activity.product.get_price(user,option)
                if product_price.price > 0:
                    max_qty = 1000
                    max_qty_1 = 1000
                    max_qty_2 = 1000
                    if product_price.product.max_quantity_per_person is not None:
                        max_qty_1 = product_price.product.max_quantity_per_person
                    if product_price.product.max_quantity is not None:
                        max_qty_2 = product_price.product.max_quantity - product_price.product.current_quantity_taken
                        if max_qty_2 < 0:
                            max_qty_2 = 0
                    max_qty = min(max_qty_1, max_qty_2)

                    err_message = {
                            'max_value': 'Ticket Qty must be less than or equal to ' + str(int(max_qty))
                    }

                    self.fields['session_%s' % activity.product.get_price(user, option).id] = forms.IntegerField(
                        label=activity.title,
                        initial=0,
                        min_value=0,
                        max_value=int(max_qty),
                        error_messages=err_message
                    )
                else:
                    self.fields['session_%s' % activity.product.get_price(user, option).id] = forms.IntegerField(
                        label=activity.title,
                        widget=NumberInput(attrs={'readonly': 'readonly'}),
                        initial=1,
                        min_value=1,
                        max_value=1,
                    )


class PaymentCallbackForm(forms.Form):

    PNREF = forms.CharField(required=True)

    AMT = forms.CharField(required=True)
    RESULT = forms.CharField(required=True)
    AUTHCODE = forms.CharField(required=False)
    RESPMSG = forms.CharField(required=False)
    AVSDATA = forms.CharField(required=False)
    INVOICE = forms.CharField(required=False)
    TAX = forms.CharField(required=False)
    TYPE = forms.CharField(required=False)
    DESCRIPTION = forms.CharField(required=False)
    CUSTID = forms.CharField(required=False)
    NAME = forms.CharField(required=False)
    ADDRESS = forms.CharField(required=False)
    CITY = forms.CharField(required=False)
    STATE = forms.CharField(required=False)
    ZIP = forms.CharField(required=False)
    COUNTRY = forms.CharField(required=False)
    PHONE = forms.CharField(required=False)
    EMAIL = forms.CharField(required=False)
    USER1 = forms.CharField(required=True)
    USER2 = forms.CharField(required=False)
    USER3 = forms.CharField(required=False)
    USER4 = forms.CharField(required=False)
    USER5 = forms.CharField(required=False)
    USER6 = forms.CharField(required=False)
    USER7 = forms.CharField(required=False)
    USER8 = forms.CharField(required=False)
    USER9 = forms.CharField(required=False)
    USER10 = forms.CharField(required=False)
    COMMENT2 = forms.CharField(required=False)

    # For debugging
    # must include VERBOSITY=HIGH in request
    # https://developer.paypal.com/docs/classic/payflow/integration-guide/?mark=RESULT%20Values%20for%20Transaction%20Declines%20or%20Errors#transaction-responses
    HOSTCODE = forms.CharField(required=False)
    RESPTEXT = forms.CharField(required=False)


RECORD_TYPES = (
        ("AGC", "Agency - Use for cities, counties, other municipalities/jurisdictions, all their internal departments and agency libraries. Not for universities, public libraries, non-profit or for-profit associations and organizations."),
        ("LIB", "Library - Use for public and University libraries. Not for private or agency libraries."),
        ("PRI", "Private Firm - Use for privately-owned businesses, private libraries, non-profit/for-profit organizations, press/media outlets, etc. Not for subscription companies, exchange subscribers, universities or public libraries."),
        ("SCH", "School - Use for universities, colleges or institutions for teaching."),
        ("SUB", "Subscription Company - Use for companies subscribing to APA publications for another company or individual."),
    )


# class RadioFieldWithoutULRenderer(RadioFieldRenderer):

#     def render(self):
#         return format_html_join(
#             '\n',
#             '<p>{0}</p>',
#             [(force_text(w), ) for w in self],
#         )

class RadioSelectWithoutUL(RadioSelect):
    template_name = 'forms/widgets/radio.html'

class SubscribeOrganizationLinkForm(StateCountryModelFormMixin, AddFormControlClassMixin, forms.ModelForm):
    fax_number = forms.CharField(label="Fax Number",required=False)
    record_type = forms.ChoiceField(
        label="Organizational Record Type",
        help_text="Please select one",
        required=True,
        choices= list(RECORD_TYPES),
        widget=RadioSelectWithoutUL()
    )

    def __init__(self, *args, **kwargs):
        super(SubscribeOrganizationLinkForm, self).__init__(*args, **kwargs)
        self.fields['company'].required = True
        self.fields['address1'].required = True
        self.fields['city'].required = True

        self.init_state_country_fields()
        self.add_form_control_class()

    class Meta:
        model = Organization
        fields = ["company", "address1", "address2", "country", "city", "state", "zip_code", "phone"]
        labels = { "company": "Organization Name","address1":"Address Line 1", "address2":"Address Line 2",
            "zip_code": "Zip/Postal Code", "phone":"Phone Number"}
        help_texts = {
            "address1": "Street Address, P.O. Box, c/o",
            "address2": "Apartment, suite, unit, building, floor, etc.",
        }


class SubscribeOrganizationProfileForm(AddFormControlClassMixin, forms.ModelForm):

    # product_code = forms.CharField(widget=forms.HiddenInput())

    roster_emails = forms.CharField(widget = forms.Textarea(attrs={'class':'form-control'}),
        required=False,
        label = "Subscriber Email Addresses",
        help_text="Enter a unique email address for everyone you want to include in your subscription.\
        (Important! Make sure each email address appears only once. Separate the email addresses by commas.) \
        APA will email everyone on your list to let them know about the subscription and give them instructions for confirming their inclusion. \
        Everyone who confirms will get full access. \
        Questions? Contact subscriptions@planning.org.")
    employee_verify = forms.BooleanField(label="I verify that the employees listed above work at the subscriber’s office.",
        required=True, initial=False)

    def __init__(self, *args, **kwargs):

        self.product_id = kwargs.pop("product_id", None)
        super().__init__(*args, **kwargs)
        if self.product_id:
            product = ProductCart.objects.get(id=self.product_id)
            if product.code == "SUB_PAS":
                self.fields['pas_type'].required = True
                self.fields['pas_type'].label = "Choose Organization Type"
            else:
                del self.fields["pas_type"]
                del self.fields["employee_verify"]

        self.add_form_control_class()

    class Meta:
        model = Organization
        fields = ["pas_type"]


class ProductOptionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop("product", None)
        self.user = kwargs.pop("user", None)
        self.code = kwargs.pop("code", None)
        self.content = kwargs.pop("content", None)
        super().__init__(*args, **kwargs)

        self.init_product_options()

        for field_name in self.fields:
            field = self.fields[field_name]
            if not field.required:
                field.widget.attrs.update({"placeholder":"Optional"})

    def init_product_options(self):

        if self.product:
            option_choices = {}
            valid_option_ids = []
            for option in self.product.options.all():
                product_price = self.product.get_price(user=self.user, option=option, code=self.code)
                # product_price = option.get_price(product=self.product, user=self.user, code=self.code)
                if product_price:
                    option_choices[option.id] = "{0} - ${1}".format(option.title, product_price.price)
                    valid_option_ids.append( option.id )
            self.fields["option"] = ModelChoiceField_w_LabelDictionary(widget=forms.RadioSelect, empty_label=None, queryset=ProductOption.objects.filter(id__in=valid_option_ids), label_dict=option_choices, label="Product")

    def save(self):
        self.instance = purchase = super().save(commit=False)
        # User add to cart method on product model instead?
        purchase.product = self.product
        purchase.product_price = self.product.get_price(user=self.user, option=purchase.option, code=self.code)
        purchase.code = self.code
        purchase.user = self.user
        purchase.contact = Contact.objects.get(user__username=self.user.username)

        purchase.quantity = 1
        purchase.amount = purchase.product_price.price * purchase.quantity
        purchase.submitted_product_price_amount = purchase.product_price.price
        purchase.save()

        return purchase

    class Meta:
        model = Purchase
        fields = ["id", "option"]


class CartForm(forms.Form):

    purchase_agreement = forms.BooleanField(required=False, label="I have read and agree to the following license agreement for DIGITAL PRODUCTS.")
    purchase_agreement_required = forms.BooleanField(required=False)

    def clean(self):
        cleaned_data = super(CartForm, self).clean()

        purchase_agreement = cleaned_data.get("purchase_agreement", False)
        purchase_agreement_required = cleaned_data.get("purchase_agreement_required", False)

        if purchase_agreement_required and not purchase_agreement:
            self.add_error("purchase_agreement", "Please read and agree to the Digital Products License Agreement before continuing.")

        return cleaned_data


# ###################### #
# FOUNDATION FORM STUFFS #
# ###################### #


class USDollarField(forms.DecimalField):

    default_error_messages = {
        'invalid': _("Value must be a US Dollar amount."),
    }

    def to_python(self, value):
        altered_value = value.replace(",", "") if value is not None else value
        return super().to_python(altered_value)

    def validate(self, value):
        super().validate(value)

        if value and value < 0:
            raise ValidationError("Please enter a positive amount")


class BaseDonationForm(forms.Form):

    amount = forms.ChoiceField(
        label="",
        # label="Gift Amount",
        required=True,
        widget=forms.RadioSelect())

    other_amount = USDollarField(
        label="Other Amount",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "input-other-amount",
                "style": "display:inline-block;width:auto;"}))

    product_id = forms.TypedChoiceField(
        label="Direct Your Gift",
        required=True,
        coerce=int,
        # widget=forms.RadioSelect()
        )

    name = forms.CharField(
        label="Person or Organization Making this Gift",
        required=False,
        widget=forms.TextInput(attrs={"class":"form-control"}) )


    FOUNDATION_GIFT_CHOICES = None
    FOUNDATION_GIFT_INITIAL = None

    def clean(self):
        cleaned_data = super().clean()

        amount = cleaned_data.get("amount", "")
        other_amount = cleaned_data.get("other_amount", "")
        # is_anonymous = cleaned_data.get("is_anonymous", "")
        name = cleaned_data.get("name", "")

        if amount == "OTHER" and not self.errors.get("other_amount"):
            if not other_amount:
                self.add_error("other_amount", "Please specify an other amount.")
            elif other_amount >= 10000.00:
                raise forms.ValidationError("""Thank you for your generosity. APA
                    wants to handle your gift—and all gifts of $10,000 or
                    more—with special care. Please contact APA Chief Executive
                    Officer <a href='mailto:jdrinan@planning.org'>James Drinan
                    </a> at your earliest convenience to finalize
                    your gift.""")

        # if not is_anonymous and not name:
        if not name:
            # self.add_error("name", "Please tell us how you want your name to appear on the Donors Recognition page, or if you prefer your gift to remain anonymous.")
            self.add_error("name", "Please tell us how you want your name to appear on the Donors Recognition page.")

        return cleaned_data

    def __init__(self, *args, **kwargs):
        self.products = kwargs.pop("products")
        super().__init__(*args, **kwargs)
        self.fields["product_id"].choices = ((p.content.master_id, p.title) for p in self.products)
        self.fields["amount"].choices = self.FOUNDATION_GIFT_CHOICES
        self.fields["amount"].initial = self.FOUNDATION_GIFT_INITIAL


class FoundationDonationForm(BaseDonationForm):

    is_tribute = forms.BooleanField(
        label="Is your gift in recognition of an individual or organization?",
        required=False,
        widget=forms.CheckboxInput(attrs={
            "class": "form-control",
            "style": "display:inline-block;width:auto;vertical-align:middle;"}))

    tribute_honoree = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class":"form-control",
            "placeholder": "Individual or Organization",
            "style":"display:inline-block;width:auto;vertical-align:middle;min-width:250px;"}))

    tribute_email = forms.EmailField(
        label="If you would like APA to notify someone, a person or organization, of this donation, please provide the email address",
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control"}))

    FOUNDATION_GIFT_CHOICES = (
        ("100", "$100"),
        ("250", "$250"),
        ("500", "$500"),
        ("1000", "$1000"),
        ("OTHER", "OTHER")
    )

    FOUNDATION_GIFT_INITIAL = "100"

    def clean(self):
        cleaned_data = super().clean()
        is_tribute = cleaned_data.get("is_tribute", None)
        tribute_honoree = cleaned_data.get("tribute_honoree", None)
        if is_tribute and not tribute_honoree:
            self.add_error("is_tribute", "Please enter the name of the individual or organization you want to recognize, or uncheck the box.")
        return cleaned_data


class FoundationDonationCartForm(BaseDonationForm):

    FOUNDATION_GIFT_CHOICES = (
        ("10", "$10"),
        ("25", "$25"),
        ("50", "$50"),
        ("75", "$75"),
        ("100", "$100"),
        ("250", "$250"),
        ("500", "$500"),
        ("1000", "$1000"),
    )
    FOUNDATION_GIFT_INITIAL = "10"

    def __init__(self, *args, **kwargs):
        self.base_fields["amount"].widget = forms.Select(attrs={
            "class":"form-control"})
        self.base_fields["product_id"].widget = forms.Select(
            attrs={"class":"form-control"})
        super().__init__(*args, **kwargs)
        self.fields["amount"].label = "Gift Amount"

