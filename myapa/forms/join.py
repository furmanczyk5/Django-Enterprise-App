import datetime

from django import forms
from django.contrib.auth.models import Group, User
from django.utils import timezone

from content.forms import AddFormControlClassMixin
from content.widgets import YearMonthDaySelectorWidget, SelectFacade
from imis.models import CustomSchoolaccredited
from myapa.forms.account import AddressesFormMixin, PersonalInformationForm, CreateAccountForm, UpdateAccountForm
from myapa.models.constants import DEGREE_TYPE_CHOICES
from myapa.models.contact import Contact
from myapa.models.educational_degree import EducationalDegree
from myapa.models.proxies import School
from myapa.permissions import utils as permissions_utils
from myapa.utils import get_primary_chapter_code_from_zip_code
from store.models import ProductCart, Purchase
from ui.utils import get_selectable_options_tuple_list


class ValidateChapterAddressFormMixin(object):

    def clean(self):
        # for all forms we should validate the zip code as being in iMIS before letting them save.

        # ! MAKE SURE THIS IS FIVE DIGITS? OR TRUNCATE TO FIVE DIGITS BEFORE CHECKING? !

        cleaned_data = super().clean()

        zip_code = self.cleaned_data['zip_code']
        country = self.cleaned_data['country']

        if country == 'United States':

            chapter = get_primary_chapter_code_from_zip_code(zip_code=zip_code)

            if not chapter:
                self.add_error("zip_code",
                               """A valid APA Chapter could not be found with the zip code entered.
                               Please verify the zip code and try again.
                               If you continue to experience issues please contact APA at customerservice@planning.org.""")

        return cleaned_data

class NonMemberCreateAccountForm(AddressesFormMixin, CreateAccountForm):

    def __init__(self, *args, **kwargs):
        is_individual = kwargs.pop("is_individual")
        super().__init__(*args, **kwargs)
        self.init_address_fields(is_individual)
        self.add_form_control_class()

    def clean(self):
        cleaned_data = super().clean()
        additional_address1 = cleaned_data.get("additional_address1", None)
        has_additional_address = bool(additional_address1)

        mailing_preferences = cleaned_data.get("mailing_preferences", None)
        billing_preferences = cleaned_data.get("billing_preferences", None)

        if mailing_preferences == 'Work Address' and not has_additional_address:
            self.add_error("mailing_preferences", "Cannot set mailing preferences on a nonexistent work address")

        if billing_preferences == 'Work Address' and not has_additional_address:
            self.add_error("billing_preferences", "Cannot set billing preferences on a nonexistent work address")

        return cleaned_data

    class Meta:
        model = Contact
        fields = [
            "prefix_name", "first_name", "middle_name", "last_name", "suffix_name", "email",
            "secondary_email", "phone", "secondary_phone", "cell_phone", "birth_date",
            "user_address_num", "address1", "address2", "country", "state", "city", "zip_code",
            "company"
        ]   # add informal_name after migrations are done


class JoinCreateAccountForm(AddressesFormMixin, ValidateChapterAddressFormMixin, CreateAccountForm):
    """ View for creating an new account to start the join process """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_address_fields()
        self.add_form_control_class()

    def clean(self):
        cleaned_data = super().clean()
        additional_address1 = cleaned_data.get("additional_address1", None)
        has_additional_address = bool(additional_address1)

        mailing_preferences = cleaned_data.get("mailing_preferences", None)
        billing_preferences = cleaned_data.get("billing_preferences", None)

        if mailing_preferences == 'Work Address' and not has_additional_address:
            self.add_error("mailing_preferences", "Cannot set mailing preferences on a nonexistent work address")

        if billing_preferences == 'Work Address' and not has_additional_address:
            self.add_error("billing_preferences", "Cannot set billing preferences on a nonexistent work address")

        return cleaned_data

    class Meta:
        model = Contact
        fields = [
            "prefix_name", "first_name", "middle_name", "last_name", "suffix_name", "email",
            "secondary_email", "phone", "secondary_phone", "cell_phone", "birth_date",
            "user_address_num", "address1", "address2", "country", "state", "city", "zip_code",
            "company"
        ]   # add informal_name after migrations are done


class JoinUpdateAccountForm(AddressesFormMixin, ValidateChapterAddressFormMixin, UpdateAccountForm):
    """ form for editing an account to start the join process"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_address_fields()
        self.add_form_control_class()

    def clean(self):
        cleaned_data = super().clean()
        additional_address1 = cleaned_data.get("additional_address1", None)
        has_additional_address = bool(additional_address1)

        mailing_preferences = cleaned_data.get("mailing_preferences", None)
        billing_preferences = cleaned_data.get("billing_preferences", None)

        if mailing_preferences == 'Work Address' and not has_additional_address:
            self.add_error("mailing_preferences", "Cannot set mailing preferences on a nonexistent work address")

        if billing_preferences == 'Work Address' and not has_additional_address:
            self.add_error("billing_preferences", "Cannot set billing preferences on a nonexistent work address")

        return cleaned_data

    class Meta:
        model = Contact
        fields = [
            "email", "secondary_email", "birth_date", "phone", "secondary_phone",
            "cell_phone", "user_address_num", "address1", "address2", "country", "state",
            "city", "zip_code", "company"
        ]   # add informal_name after migrations are done


class JoinPersonalInformationForm(PersonalInformationForm):
    """
    Form View for entering personal information, within the join process
    """
    pass


class JoinEnhanceMembershipForm(forms.Form):
    product_type_division = "DIVISION"
    product_type_chapter = "CHAPTER"
    product_type_subscription = "PUBLICATION_SUBSCRIPTION"
    available_product_type_codes = [product_type_division, product_type_chapter, product_type_subscription]

    exclude_planning_print = forms.BooleanField(
        label="I would like to receive only the digital edition of Planning. I do not want to receive the print edition.",
        required=False
    )

    planners_advocacy = forms.BooleanField(
        label="I want to join APA's Planners' Advocacy Network.",
        required=False,
        initial=False
    )

    def __init__(self, *args, **kwargs):

        self.active_subscriptions = kwargs.pop("subscriptions", [])
        self.cart_products = kwargs.pop("cart_products", [])
        self.primary_chapter_product = kwargs.pop("primary_chapter_product", None)
        self.contact = kwargs.pop("contact", None)
        self.available_products = []
        self.add_divisions = []
        self.add_chapters = []
        self.add_subscriptions = []
        self.renew_divisions = []
        self.renew_chapters = []
        self.renew_subscriptions = []
        self.all_products = []

        super().__init__(*args, **kwargs)

        # so that get_price can access groups w/o queries
        if self.contact:
            # Give the user the new-member login group for pricing
            # self.is_new_membership_qualified is supposed to be set once on JoinRenewMixin,
            # but seems to not persist for some yet-to-be-determined reasons. It's a fairly expensive
            # operation, but it's better than people getting the wrong price.
            permissions_utils.update_user_groups(self.contact.user)
            if self.contact.is_new_membership_qualified:
                self.contact.user.groups.add(Group.objects.get(name='new-member'))

            self.user = User.objects.filter(
                username=self.contact.user.username
            ).prefetch_related(
                "groups"
            ).first()

        else:
            self.user = None

        self.init_optional_product_fields()

    def init_optional_product_fields(self):
        """ Initializes optional division, chapter, and subscription fields.
            Each product is a separate field in the form."""
        self.set_available_products()

        active_subscription_product_codes = [
            "DIVISION_%s" % s.product_code
            if s.prod_type == "SEC"
            else s.product_code
            for s in self.active_subscriptions
        ]

        contact = self.user.contact
        contact_purchases = contact.purchase_set.all()

        for p in self.available_products:

            in_cart = p in self.cart_products
            price = p.get_price(contact=self.user.contact, purchases=contact_purchases)

            fieldname = "product_%s" % p.id
            product_dict = {"field_name": fieldname, "price": price, "product": p}

            is_active = p.code in active_subscription_product_codes

            if p.product_type in self.available_product_type_codes:
                self.fields[fieldname] = forms.BooleanField(
                    label=p.content.title,
                    initial=is_active or in_cart,
                    required=False
                )

                self.add_or_renew_products(is_active, p, product_dict)

        # this makes this easier to process later
        self.all_products = self.add_divisions \
                            + self.add_subscriptions \
                            + self.renew_divisions \
                            + self.renew_subscriptions \
                            + self.add_chapters \
                            + self.renew_chapters

    def set_available_products(self):

        self.available_products = ProductCart.objects.filter(
            product_type__in=self.available_product_type_codes
        ).exclude(
            code__in=['SUB_PLANNING', 'EDU_SUB']  # Planning Magazine is complimentary with membership
        ).order_by(
            'content__title'
        )
        if self.primary_chapter_product:
            # this condition is needed because international joiners will not have a primary chapter
            self.available_products = self.available_products.exclude(id=self.primary_chapter_product.id)

    def add_or_renew_products(self, is_active, product, product_dict):
        if product.product_type == self.product_type_division:
            if is_active:
                self.renew_divisions.append(product_dict)
            else:
                self.add_divisions.append(product_dict)
        elif product.product_type == self.product_type_chapter:
            if is_active:
                self.renew_chapters.append(product_dict)
            else:
                self.add_chapters.append(product_dict)
        elif product.product_type == self.product_type_subscription \
                and product_dict['price'] is not None \
                and product.code != "SUB_PAS":
            if is_active:
                self.renew_subscriptions.append(product_dict)
            else:
                self.add_subscriptions.append(product_dict)

    def save(self):

        # remove all existing division and subscription products from the cart
        Purchase.cart_items(
            user=self.user
        ).filter(
            product_id__in=[p.id for p in self.available_products]
        ).exclude(
            product=self.primary_chapter_product
        ).delete()

        # always create new purchase to add to cart
        for p_dict in self.all_products:
            # Later need to be more specific about pricing and option (like for students)
            if self.data.get("product_%s" % p_dict["product"].id, None):
                p_dict["product"].add_to_cart(contact=self.contact)


class StudentJoinEnhanceMembershipForm(JoinEnhanceMembershipForm):
    exclude_planning_print = None
    max_free_divisions = 5

    def init_optional_product_fields(self):

        # get choices from products
        self.available_products = self.get_available_products()

        self.division_products = [p for p in self.available_products]
        active_subscription_products = [p for p in self.available_products
                                        if p.code in [
                                            "DIVISION_%s" % s.product_code
                                            for s in self.active_subscriptions
                                            if s.prod_type == "SEC"
                                            ]
                                        ]

        initial_division_products = [p for p in self.cart_products if
                                     p.product_type == "DIVISION"] or active_subscription_products

        self.fields["divisions"] = forms.MultipleChoiceField(
            choices=[(p.id, p.content.title) for p in self.division_products],
            initial=[p.id for p in initial_division_products],
            widget=forms.CheckboxSelectMultiple(),
            required=False)

    def get_available_products(self):
        return ProductCart.objects.filter(
            product_type=self.product_type_division
        ).order_by(
            "content__title"
        )

    def clean_divisions(self):
        divisions = self.cleaned_data.get("divisions")
        max_free_divisions = self.get_max_free_divisions()
        if len(divisions) > max_free_divisions:
            self.add_error(
                "divisions",
                "Please select {0} or fewer free divisions to include with your student membership.".format(
                    max_free_divisions
                )
            )
        return divisions

    def get_max_free_divisions(self):
        return self.max_free_divisions

    def save(self):
        # remove all existing division and subscription products from the cart
        Purchase.cart_items(
            user=self.user
        ).filter(
            product_id__in=[p.id for p in self.available_products]
        ).exclude(
            product=self.primary_chapter_product
        ).delete()

        # add primary chapter to cart HERE? or already in cart...

        # always create new purchase to add to cart
        selected_division_product_ids = self.cleaned_data.get("divisions")
        for p in self.division_products:
            if str(p.id) in selected_division_product_ids:
                p.add_to_cart(contact=self.contact)


class StudentAddFreeDivisionsForm(forms.Form):
    """ Form to allow students to add up to 5 free divisions outside of the join process"""
    max_free_divisions = 5

    def __init__(self, *args, **kwargs):
        self.active_division_products = kwargs.pop("active_division_products")
        self.available_division_products = kwargs.pop("available_division_products")
        self.contact = kwargs.pop("contact")
        super().__init__(*args, **kwargs)
        self.init_optional_product_fields()

    def init_optional_product_fields(self):

        self.fields["divisions"] = forms.MultipleChoiceField(
            choices=[(p.id, p.content.title) for p in self.available_division_products],
            initial=[],
            widget=forms.CheckboxSelectMultiple(),
            required=False)

    def clean_divisions(self):
        divisions = self.cleaned_data.get("divisions")
        max_additional_free_divisions = self.get_max_free_divisions()

        if len(self.active_division_products) >= self.max_free_divisions:
            self.add_error("divisions", "You already have the maximum number of divisions for student membership.")
        elif len(divisions) > max_additional_free_divisions:
            self.add_error("divisions",
                           "You can only have up to {0} free divisions. You may only select {1} additional divisions".format(
                               self.max_free_divisions, max_additional_free_divisions))
        return divisions

    def get_max_free_divisions(self):
        return max(self.max_free_divisions - len(self.active_division_products), 0)

    def save(self):
        purchases = []
        selected_division_product_ids = self.cleaned_data.get("divisions")
        for p in self.available_division_products:
            if str(p.id) in selected_division_product_ids:
                purchase = p.add_to_cart(
                    contact=self.contact,
                    amount=0,
                    submitted_product_price_amount=0
                )
                purchases.append(purchase)
        return purchases


class StudentJoinSchoolInformationForm(AddFormControlClassMixin, forms.ModelForm):
    """
    Form for the first step of the student join process... verifification, etc.
    """

    verify = forms.BooleanField(
        label="I confirm that I am a current student actively enrolled in a college or university degree program.",
        required=True)

    school = forms.ChoiceField(
        label="School",
        required=True,
        choices=[("OTHER", "Other")])

    other_school = forms.CharField(
        label="Other school if yours is not listed above",
        required=False)

    degree_program = forms.ChoiceField(
        label="Program",
        choices=[(None, "")],
        help_text="(Optional if School is 'Other')",
        required=False
    )

    degree_type_choice = forms.ChoiceField(
        label="Degree Type",
        choices=DEGREE_TYPE_CHOICES + (("OTHER", "Other"),))

    degree_type_other = forms.CharField(
        label="Other Degree Type",
        required=False)

    level = forms.ChoiceField(
        label="Degree Level",
        required=True,
        choices=(
            ("B", "Undergraduate"),
            ("M", "Graduate"),
            ("P", "Post-Graduate (PhD, J.D., etc.)"),
            ("N", "Other")
        ))

    level_other = forms.CharField(
        label="Other Degree Level",
        required=False)

    graduation_date = forms.DateField(
        label="Expected Graduation Date",
        required=True,
        widget=YearMonthDaySelectorWidget(
            year_sort="asc",
            max_year=datetime.datetime.today().year + 20,
            min_year=datetime.datetime.today().year,
            include_day=False,
            attrs={"style": "width:auto;display:inline-block"}))

    student_id = forms.CharField(
        label="Student ID",
        required=True)

    # override this to prevent init of visible school field widget
    hide_school = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_school_and_degree_fields(*args, **kwargs)
        self.add_form_control_class()

    def clean(self):

        school = self.cleaned_data.get("school")
        other_school = self.cleaned_data.get("other_school")
        degree_program = self.cleaned_data.get("degree_program")
        degree_type_choice = self.cleaned_data.get("degree_type_choice")
        degree_type_other = self.cleaned_data.get("degree_type_other")
        level = self.cleaned_data.get("level")
        level_other = self.cleaned_data.get("level_other")

        if school == "OTHER":
            if not other_school:
                self.add_error("other_school", "Please provide an other value")
        else:
            self.cleaned_data["other_school"] = next((s[1] for s in self.fields["school"].choices if s[0] == school),
                                                     None)

            if not degree_program:
                self.add_error("degree_program", "This field is required")
            elif degree_program == "OTHER":
                if not degree_type_choice:
                    self.add_error("degree_type_choice", "This field is required")
                elif degree_type_choice == "OTHER" and not degree_type_other:
                    self.add_error("degree_type_other", "Please provide an other value")

        if level == "N":
            if not level_other:
                self.add_error("level_other", "Please provide an other value")
        else:
            self.cleaned_data["level_other"] = None

        return self.cleaned_data

    def clean_graduation_date(self):
        graduation_date = self.cleaned_data.get("graduation_date", None)
        now = timezone.now()
        if graduation_date and (graduation_date.year < now.year or (
                graduation_date.year == now.year and graduation_date.month < now.month)):
            self.add_error("graduation_date",
                           "To qualify for student membership, this date must be in the future. Please update your graduation date or join APA as a regular member.")
        return graduation_date

    def save(self, commit=True):

        degree = super().save(commit=False)

        school = self.cleaned_data.get("school")
        degree_program = self.cleaned_data.get("degree_program")
        degree_type_choice = self.cleaned_data.get("degree_type_choice")
        degree_type_other = self.cleaned_data.get("degree_type_other")

        if school != "OTHER":
            # choices are usernames so we need to query for actual record
            degree.school = School.objects.only("id").get(user__username=school)
        else:
            degree.school = None

        if school == "OTHER" or degree_program == "OTHER":
            degree.school_seqn = None
            degree.program = degree_type_choice if degree_type_choice != "OTHER" else degree_type_other
        else:
            imis_school = CustomSchoolaccredited.objects.get(id=school, seqn=degree_program)
            degree.school_seqn = degree_program
            degree.program = imis_school.degree_program
            degree.level = imis_school.degree_level
            degree.level_other = None
            degree.is_planning = True

        degree.is_current = True
        degree.complete = False

        if commit:
            degree.save()

        return degree

    def get_school_choices(self, *args, **kwargs):
        return [(None, ""), ("OTHER", "Other")] + CustomSchoolaccredited.get_current_schools()

    def init_school_and_degree_fields(self, *args, **kwargs):
        prefix = kwargs.get("prefix", "") or ""
        form_prefix = self.prefix or ""
        if form_prefix:
            combo_prefix = form_prefix + "-" + prefix
        else:
            combo_prefix = prefix

        school = self.data.get("%sschool" % combo_prefix, None) or self.initial.get("%sschool" % prefix, None) or None
        degree_program_choices = [(None, "")] + get_selectable_options_tuple_list(mode="current_programs_from_school",
                                                                                  value=school)

        if not self.hide_school:
            self.fields["%sschool" % prefix].widget = SelectFacade(attrs={
                "class": "selectchain",
                "data-selectchain-mode": "current_programs_from_school",
                "data-selectchain-target": "#%sdegree-program-select" % combo_prefix})
        self.fields["%sschool" % prefix].choices = self.get_school_choices()

        self.fields["%sdegree_program" % prefix].widget = SelectFacade(
            attrs={"id": "%sdegree-program-select" % combo_prefix})
        self.fields["%sdegree_program" % prefix].choices = degree_program_choices

    class Meta:
        model = EducationalDegree
        fields = ["other_school", "level", "level_other", "graduation_date", "student_id"]
