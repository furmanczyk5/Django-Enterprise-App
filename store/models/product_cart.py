import logging

from django.db import models
from django.db.models import Q
from django.utils import timezone

from store.utils.prevent_delete_purchases_queryset import PreventDeletePurchasesQuerySet

from myapa.models import Contact
from store.models.product import Product, Purchase
from store.models.product_price import ProductPrice

logger = logging.getLogger(__name__)

class ProductCartManager(models.Manager):
    """
    manager for querying products for purposes of displaying
    in cart / store / search
    """
    def get_queryset(self):
        return super().get_queryset().filter(
                status__in=("A","H"),
                publish_status="PUBLISHED",
            ).select_related("content").prefetch_related(
                models.Prefetch(
                    "prices",
                    queryset=ProductPrice.objects.filter(status__in=("A","H")).order_by("priority").prefetch_related("exclude_groups", "required_groups")
                    )
            ).prefetch_related("options")

class ProductCart(Product):

    objects = ProductCartManager.from_queryset(PreventDeletePurchasesQuerySet)()

    def get_prices(self,
        contact=None,
        option=None,
        code=None,
        purchases = [], # all purchases for this contact
        stop_when_applies = False
        ):

        return_prices = list(self.prices.all())
        user = contact.user if contact else None
        current_time = timezone.now()
        this_purchase = next( (p for p in purchases if p.product == self ), None )

        for price in return_prices:
            # print("----------------------------------------------")
            # print(price)

            # assume guilty until proven innocent
            setattr(price, "applies", False)
            setattr(price, "applies_except_group", False)

            if price.begin_time and price.begin_time > current_time:
                # print("bad begin time")
                continue

            if price.end_time and price.end_time < current_time:
                # print("bad end time")
                continue

            # check if the option (if specified) applies to this price:
            if option and price.option_code and option.code != price.option_code:
                # print("bad option")
                continue

            # check if the an purchase for other required product exists (if specified):
            if price.other_required_product_code:

                # set special filter kwargs for checking if purchase must be in cart (order is None)
                # or if specific option must have been selected for the other required product
                matching_purchases = [p for p in purchases if p.product.code==price.other_required_product_code and p.status in ("A","P")]
                if not matching_purchases:
                    print("bad required product")
                    continue

                if price.other_required_product_must_be_in_cart:
                    if not next( (True for p in matching_purchases if p.order is None), False ):
                        print("bad required product in cart")
                        continue

                if price.other_required_option_code:
                    if not next( (True for p in matching_purchases if p.option.code==price.other_required_option_code), False ):
                        print("bad required product option")
                        continue

            if price.min_quantity and this_purchase and this_purchase.quantity < price.min_quantity:
                # print("bad min quantity")
                continue

            if price.max_quantity and this_purchase and this_purchase.quantity > price.max_quantity:
                # print("bad max quantity")
                continue

            if price.code:

                if (
                    self.code == "MEMBERSHIP_STU"
                    or self.product_type in ("PUBLICATION_SUBSCRIPTION", "CHAPTER", "DIVISION")
                    ):
                    if not contact or price.code != contact.salary_range:
                        # print("bad membership salary code ... students / new mem pubs / chapter / division", price.code, contact.salary_range)
                        continue

                elif self.code in ("MEMBERSHIP_MEM", "MEMBERSHIP_AICP"):
                    if not contact or (contact.country in ("United States", '', None) and price.code != contact.salary_range):
                        # print("bad membership salary code, regular / aicp", price.code, contact.salary_range)
                        continue

                    elif not contact or (contact.country not in ("United States", '', None) and price.code != contact.get_country_type_code()):
                        # print("bad membership country code")
                        continue

                elif self.product_type in ("CHAPTER","DIVISION") and (not contact or price.code != contact.salary_range):
                    continue

                # these chapters have salary based dues, so check for matching contact salary:
                elif self.code in ( "CHAPT_CO", "CHAPT_IL", "CHAPT_UT", "CHAPT_NNE", "CHAPT_WA", "CHAPT_NE",
                    "CHAPT_OH", "CHAPT_FL", "CHAPT_PA", "CHAPT_CT", "CHAPT_NJ", "CHAPT_IN", "CHAPT_VA", "CHAPT_NATC",
                    "CHAPT_FL", "CHAPT_NM", "CHAPT_AL", "CHAPT_AZ", "CHAPT_MI", "CHAPT_NV",
                    "CHAPT_TN",
                    ):
                    if not contact or price.code != contact.salary_range:
                        continue

                else:
                    if price.code != code:
                        # print("bad price code")
                        continue

            price.prices_applies_except_group = True

            if price.required_groups.all():
                has_required_group = False
                if user:
                    has_required_group = next( (True for g in price.required_groups.all() if g in user.groups.all()), False)
                if not has_required_group:
                    cart_products = [p.product for p in purchases if p.order is None]
                    all_future_groups = []
                    for cp in cart_products:
                        all_future_groups.extend(cp.future_groups.all())
                    has_required_group = next( (True for g in price.required_groups.all() if g in all_future_groups), False )
                if not has_required_group:
                    # print("bad user does not have required group")
                    continue

            if price.exclude_groups.all():
                if user and next( (True for g in price.exclude_groups.all() if g in user.groups.all()), False):
                    # print("bad user has excluded group")
                    continue

            # YAY! all restrictions passed with flying colors, so this price applies
            price.applies = True

            if stop_when_applies:

                break

            # elif self.product_type == "PUBLICATION_SUBSCRIPTION" and price.code:
            #     # hacky, but its the best way to give special pricing to "newmembers" (L)
            #     if next((True for sc in SALARY_CHOICES_ALL if price.code == sc[0]), False):
            #         price.applies = price.code == contact.salary_range

            # NOTE: TO DO... need to uncomment this once we fix login group issues on chapter records (meeting with Karl)
            #if contact.member_type in ("RET","LIFE") or self.code:
            # return self.code == contact.salary_range


        return return_prices


    def get_price(self, **kwargs):
        return next( (price for price in self.get_prices(stop_when_applies=True, **kwargs) if price.applies), None)

    def add_to_cart(self, contact, **kwargs):
        """
        method to add product to user's cart
        returns the created purchase record
        """
        option = kwargs.get("option", None)
        quantity = kwargs.get("quantity", 1)
        company_contact_id = kwargs.get("company_contact_id", None)
        code = kwargs.get("code", None)
        content_master = kwargs.get("content_master", None)
        provider = kwargs.get("provider", None)
        user = contact.user
        purchases = list(kwargs.get("purchases", []))

        # TODO: Remove when shopping cart refactor done
        # https://americanplanning.atlassian.net/browse/DEV-2134?focusedCommentId=19072&page=com.atlassian.jira.plugin.system.issuetabpanels:comment-tabpanel#comment-19072
        amount = kwargs.get("amount", None)
        submitted_product_price_amount = kwargs.get('submitted_product_price_amount', None)

        if company_contact_id:

            product_price = kwargs.get("product_price", self.get_price(
                contact=contact, option=option, code=code, purchases=purchases))

            # TO DO: sort out this company nonsense!!!!!!!!!
            contact = Contact.objects.get(user__username=company_contact_id)

        else:
            contact = kwargs.get("contact", Contact.objects.get(user__username=user.username))

            product_price = kwargs.get("product_price", self.get_price(
                contact=contact, option=option, code=code, purchases=purchases) )

        Purchase.objects.filter(user=contact.user,product=self,order=None).delete()

        if product_price and product_price.price is not None:
            purchase = Purchase.objects.create(
                user=user,
                contact=contact,
                content_master=content_master,
                product=self,
                option=option,
                quantity=quantity,
                product_price=product_price,
                submitted_product_price_amount=submitted_product_price_amount if submitted_product_price_amount is not None else product_price.price,
                amount=amount if amount is not None else float(product_price.price) * float(quantity), # TO DO... double check is this the best way to convert float/decimal for currency data?
                order=None,
                code=code,
                contact_recipient=provider,
                for_someone_else=kwargs.get("for_someone_else", False),
            )

            purchases.append(purchase)
            self.add_comped_purchases(contact, purchase, purchases)

        else:
            return None
        return purchase

    def add_comped_purchases(self, contact, purchase, purchases):

        comped_products = ProductCart.objects.filter(
            prices__other_required_product_code=self.code,
            prices__comped=True,
            ).filter(
                Q(prices__other_required_option_code__isnull=True) | Q(prices__other_required_option_code="") | Q(prices__other_required_option_code=purchase.option.code if purchase.option else None)
            ).distinct()

        for cp in comped_products:
            cp.add_to_cart(contact=contact, purchases=purchases)

    class Meta:
        proxy = True
