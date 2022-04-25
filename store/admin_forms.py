from django import forms
from .models import ProductOption, ProductPrice, Purchase, Product


class OrderConfirmationAdminEmailForm(forms.Form):
    email = forms.CharField(label="Email Address", required=True, widget=forms.TextInput())


class PaymentAdminForm(forms.ModelForm):
    PAYMENT_METHOD_CHOICES = (
        ("CHECK", "Check"),
        ("CASH", "Cash")
        )
    method = forms.ChoiceField(choices=PAYMENT_METHOD_CHOICES)


class PurchaseInlineAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
    
        instance = kwargs.pop("instance",None)

        super().__init__(*args, **kwargs)
        product = instance.product
        option = instance.option

        self.fields["option"] = forms.ChoiceField(
        choices=[(None,""),("TEST","TEST")]+[(x.code,x.title) for x in ProductOption.objects.filter(product=product)], widget=forms.Select(attrs={"class":"selectchain","data-selectchain-target":"product_price","data-selectchain-isformset":True,"data-selectchain-mode":"productprice_from_productoption"}))


        self.fields["product_price"] = forms.ChoiceField(
        choices=[(None,"")]+[(x.code,x.title) for x in ProductPrice.objects.filter(product=product, required_product_options=option)])

        self.fields["product"] = forms.ChoiceField(widget=forms.Select(attrs={"class":"selectchain","data-selectchain-target":"option","data-selectchain-isformset":True,"data-selectchain-mode":"productoption_from_product"}))

    class Meta:
        model = Purchase
        exclude = []
        widgets = {
            "product":forms.Select(attrs={"class":"selectchain","data-selectchain-target":"option","data-selectchain-isformset":True,"data-selectchain-mode":"productoption_from_product"}),
            "option":forms.Select(attrs={"class":"selectchain","data-selectchain-target":"product_price","data-selectchain-isformset":True,"data-selectchain-mode":"productprice_from_productoption"}),
            "product_price":forms.Select(),
        }


class ProductInlineAdminForm(forms.ModelForm):

    class Meta:
        model = Product
        exclude = []
        widgets = {
            "confirmation_text":forms.Textarea(attrs={"class":"ckeditor"}),
            "reviews":forms.Textarea(attrs={"class":"ckeditor"}),
        }
