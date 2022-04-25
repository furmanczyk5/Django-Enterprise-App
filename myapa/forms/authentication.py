from django import forms

from django.contrib.auth import password_validation
from django.contrib.auth.forms import SetPasswordForm
from django.utils.translation import ugettext_lazy as _

class PasswordResetSendEmailForm(forms.Form):
    email = forms.EmailField(
        label="Email Address", 
        required=True, 
        widget=forms.EmailInput(attrs={"class":"form-control"}))


class MyapaSetPasswordForm(SetPasswordForm):

    error_messages = {
        "password_mismatch": _("The two passwords entered are not identical. Please try again."),
        "password_min_length": _("Your password has fewer than eight characters. Please try again.")
    }

    new_password1 = forms.CharField(
        label=_("New Password"),
        widget=forms.PasswordInput(attrs={"class":"form-control"}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_("Confirm New Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"class":"form-control"}),
    )

    def clean_new_password1(self):
        password1 = self.cleaned_data.get('new_password1')
        if len(password1) < 8:

            raise forms.ValidationError(
                self.error_messages['password_min_length'],
                code='password_min_length',
            )
        return password1
