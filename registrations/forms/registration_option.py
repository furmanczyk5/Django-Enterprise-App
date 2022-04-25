from django import forms
from django.utils.safestring import mark_safe

from imis.models import CustomEventRegistration
from myapa.models.constants import RACE_CHOICES, HISPANIC_ORIGIN_CHOICES, GENDER_CHOICES
from myapa.permissions import utils as permissions_utils
from store.models import Purchase, ProductOption
from . import format_field, ModelChoiceField_w_LabelDictionary
from ..imis import get_questions, create_response_key, insert_response_value, Badge
from ..imis.xml_parser import required, visible

QUESTION_RESPONSE = 'question_response_'

class RegistrationOptionForm(forms.ModelForm):

    race = forms.MultipleChoiceField(
        label="Race",
        required=True,
        help_text="Please complete the sections for Hispanic Origin and Race. APA uses this data to better understand the diversity of our members. The information we collect correlates with U.S. Census Bureau reports.",
        choices=list(RACE_CHOICES) + [("NO_ANSWER", "I prefer not to answer")],
        widget=forms.CheckboxSelectMultiple()
    )

    hispanic_origin = forms.ChoiceField(
        label="Hispanic Origin",
        required=True,
        help_text="Please select one below",
        choices=list(HISPANIC_ORIGIN_CHOICES),
        widget=forms.RadioSelect()
    )

    gender = forms.ChoiceField(
        label="Gender",
        required=True,
        choices=[(None, "- select -")] + list(GENDER_CHOICES),
        widget=forms.Select(attrs={"style": "width:auto"}),
    )

    gender_other = forms.CharField(label="How You Self-Describe", required=False, max_length=25)

    ai_an = forms.CharField(required=False)
    asian_pacific = forms.CharField(required=False)
    other = forms.CharField(required=False)
    span_hisp_latino = forms.CharField(required=False)

    race_option_other = {
        "E003": "ai_an",
        "E100": "asian_pacific",
        "E999": "other"
    }
    hispanic_origin_option_other = {
        "O999": "span_hisp_latino"
    }

    def __init__(self, *args, **kwargs):
        self.fields = {}
        self.event = kwargs.pop("event", None)
        self.product = kwargs.pop("product", None)
        self.user = kwargs.pop("user", None)

        if self.user is not None:
            permissions_utils.update_user_groups(self.user)

        self.questions = get_questions(self.event.product.imis_code)
        self.code = kwargs.pop("code", None) # used in final save
        super().__init__(*args, **kwargs)

        self.init_registration_options()
        self.init_question_fields()

    def init_registration_options(self):

        option_choices = {}
        valid_option_ids = []
        for option in self.product.options.all():
            product_price = self.product.get_price(
                contact=self.user.contact,
                option=option,
                code=self.code
            )
            sorted_prices = sorted(
                (p for p in self.product.prices.all() if option.code == p.option_code),
                key=lambda p: (p.priority is None, p.priority, p.title))
            if product_price:
                prices_html = ""
                for price in sorted_prices:
                    if price.status == "A" or price == product_price:
                        if price == product_price:
                            prices_html += "<div class='key-value-pair bold-text'>"
                        else:
                            prices_html += "<div class='key-value-pair'>"

                        prices_html += """
                            <div class="key">{0}</div>
                            <div class="value">${1}</div>
                        </div>""".format(price.title, price.price)

                option_choices[option.id] = mark_safe("""
                    {0} - ${1}<br/> <div style='padding-bottom:10px;'><em>{2}</em></div><div style='padding:0px 0px 12px 12px;'>{3}</div>
                """.format(option.title, product_price.price, option.description or "", prices_html))
                valid_option_ids.append( option.id )

        self.fields["option"] = ModelChoiceField_w_LabelDictionary(
            widget=forms.RadioSelect,
            empty_label=None,
            queryset=ProductOption.objects.filter(id__in=valid_option_ids).order_by('sort_number'),
            label_dict=option_choices,
            label="Registration"
        )

    def init_question_fields(self):
        visible_field_keys = filter(
            lambda key: visible(self.questions[key]['xml']),
            self.questions.keys())

        for key in sorted(visible_field_keys):
            question_key = '{}{}'.format(QUESTION_RESPONSE, (key + 1))
            self.fields[question_key] = format_field(self.questions[key])

    def is_valid(self):
        return super().is_valid()

    def clean(self):
        for key, value in self.cleaned_data.items():
            if QUESTION_RESPONSE in key:
                self.check_for_required_error(key, value)

        return super().clean()

    def check_for_required_error(self, key, value):
        question_key = self.convert_to_numeric_key(key)
        question = self.questions[question_key]
        is_required = required(question['xml'])
        if is_required and value == '':
            self._errors[key] = self.error_class([u'This field is required.'])

    def save(self):
        self.save_question_responses(self.data)
        self.instance = purchase = super().save(commit=False)

        self.save_registration()

        self.instance = purchase = super().save(commit=False)
        contact = self.user.contact
        contact_purchases = list(contact.purchase_set.all())

        self.product.add_to_cart(contact=self.user.contact, option=purchase.option, code=self.code,  purchases=contact_purchases)

        return purchase

    def save_question_responses(self, data):
        responses = {}

        for key, value in data.items():
            if QUESTION_RESPONSE in key:
                responses[self.convert_to_numeric_key(key)] = value

        response_key = self.get_response_key(responses)

        for key, value in responses.items():
            associated_question = self.questions[key]
            field_key = associated_question['field_key']
            response_type = associated_question['type']
            value = self.adjust_value_for_imis(value, response_type)
            insert_response_value(
                response_key,
                field_key,
                response_type,
                value)

    def adjust_value_for_imis(self, value, response_type):
        if response_type == 'Boolean':
            return 1 if 'on' else 0

        if value == '':
            return None

        return value

    def save_registration(self):
        badge = Badge().get(self.user.username)
        CustomEventRegistration.objects.create(
            id=self.user.username,
            meeting=self.event.product.imis_code,
            **badge
        )

    def get_response_key(self, responses):
        if responses:
            return create_response_key(self.get_form_key(), self.user.username)

    def get_form_key(self):
        return self.questions[0]['form_key']

    def convert_to_numeric_key(self, key):
        return int(key.replace(QUESTION_RESPONSE, '')) - 1

    class Meta:
        model = Purchase
        fields = ["option"]
