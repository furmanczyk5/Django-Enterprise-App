from imis.models import NameAddress

from django import forms


class NameAddressForm(forms.models.ModelForm):

    class Meta:
        model = NameAddress
        fields = ('address_1', 'address_2', 'city', 'state_province', 'zip', 'country')
